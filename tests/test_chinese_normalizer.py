"""Tests for Chinese wording normalizer."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.schemas import (  # noqa: E402
    ClarificationQuestion,
    CrewExecutionResult,
    EntryExitCriteriaSet,
    GateCriterion,
    RequirementSummary,
    ReviewComment,
    ReviewResult,
    TestCase,
    TestPoint,
)
from test_case_writing_crew.tools import (  # noqa: E402
    normalize_execution_result,
    normalize_expected_result,
    normalize_test_case_title,
    normalize_test_point_title,
    normalize_test_steps,
)


class ChineseNormalizerTest(unittest.TestCase):
    def test_english_title_to_chinese_style(self) -> None:
        title = normalize_test_case_title("device startup success", module="device")
        self.assertTrue(title.startswith("【设备控制】验证"))
        self.assertIn("设备启动成功", title)

    def test_short_title_gets_validation_pattern(self) -> None:
        title = normalize_test_point_title("参数保存", module="control")
        self.assertTrue(title.startswith("【控制管理】验证"))

    def test_steps_normalized_to_chinese_numbering(self) -> None:
        steps = normalize_test_steps(["1）准备环境", "2）执行操作", "3）检查结果"])
        self.assertEqual(len(steps), 3)
        self.assertTrue(steps[0].startswith("1）"))
        self.assertEqual(steps[0], "1）准备环境")

    def test_expected_result_becomes_observable(self) -> None:
        result = normalize_expected_result("成功")
        self.assertIn("可通过页面状态、设备状态或日志记录进行验证", result)

    def test_protected_tokens_not_rewritten(self) -> None:
        result = normalize_expected_result("调用 POST /device/start，返回错误码 TIMEOUT_ERROR，校验字段 device_id")
        self.assertIn("POST /device/start", result)
        self.assertIn("TIMEOUT_ERROR", result)
        self.assertIn("device_id", result)

    def test_normalize_execution_result_scope(self) -> None:
        execution = CrewExecutionResult(
            requirement_summary=RequirementSummary(product_name="Demo"),
            test_points=[
                TestPoint(
                    test_point_id="TP-001",
                    module="device",
                    sub_module="core",
                    requirement_id="REQ-001",
                    test_dimension="functional",
                    title="device startup success",
                    description="check startup behavior",
                )
            ],
            test_cases=[
                TestCase(
                    case_id="TC-001",
                    module="device",
                    sub_module="core",
                    test_point_id="TP-001",
                    requirement_id="REQ-001",
                    title="startup test",
                    preconditions=["system ready"],
                    steps=["Open page", "Click save"],
                    expected_result="成功",
                )
            ],
            review_result=ReviewResult(
                overall_status="needs_revision",
                comments=[
                    ReviewComment(
                        target_type="test_case",
                        target_id="TC-001",
                        severity="high",
                        comment="Expected result is empty.",
                        suggestion="Add measurable expected result.",
                    )
                ],
            ),
            quality_gates=EntryExitCriteriaSet(
                entry_criteria=[
                    GateCriterion(
                        criterion_id="GC-E-001",
                        criterion_type="entry",
                        category="functional",
                        description="All high-priority requirements mapped to test points",
                        threshold="100%",
                    )
                ],
            ),
        )

        normalized = normalize_execution_result(execution)
        self.assertTrue(normalized.test_points[0].title.startswith("【设备控制】验证"))
        self.assertTrue(normalized.test_cases[0].title.startswith("【设备控制】验证"))
        self.assertTrue(normalized.test_cases[0].steps[0].startswith("1）"))
        self.assertIn("可通过页面状态、设备状态或日志记录进行验证", normalized.test_cases[0].expected_result)
        self.assertIn("预期结果为空", normalized.review_result.comments[0].comment)

    def test_limit_counts(self) -> None:
        execution = CrewExecutionResult(
            requirement_summary=RequirementSummary(product_name="Demo"),
            clarification_questions=[],
            test_points=[],
            test_cases=[],
            review_result=ReviewResult(overall_status="needs_revision", comments=[]),
            quality_gates=EntryExitCriteriaSet(entry_criteria=[], exit_criteria=[]),
        )
        for i in range(12):
            execution.clarification_questions.append(
                ClarificationQuestion(
                    id=f"CQ-{i:03d}",
                    category="api",
                    question=f"q{i}",
                    impact="high",
                    required=True,
                )
            )
        for i in range(25):
            execution.test_points.append(
                TestPoint(
                    test_point_id=f"TP-{i:03d}",
                    module="device",
                    sub_module="core",
                    requirement_id=f"REQ-{i:03d}",
                    test_dimension="functional",
                    title=f"title{i}",
                    description="desc",
                )
            )
            execution.test_cases.append(
                TestCase(
                    case_id=f"TC-{i:03d}",
                    module="device",
                    sub_module="core",
                    test_point_id=f"TP-{i:03d}",
                    requirement_id=f"REQ-{i:03d}",
                    title="title",
                    preconditions=["p"],
                    steps=["1）a", "2）b", "3）c", "4）d", "5）e", "6）f", "7）g"],
                    expected_result="ok",
                )
            )
        for i in range(12):
            execution.review_result.comments.append(
                ReviewComment(
                    target_type="test_case",
                    target_id=f"TC-{i:03d}",
                    severity="medium",
                    comment="c",
                    suggestion="s",
                )
            )
            execution.quality_gates.entry_criteria.append(
                GateCriterion(
                    criterion_id=f"GC-E-{i:03d}",
                    criterion_type="entry",
                    category="functional",
                    description="d",
                    threshold="t",
                )
            )
            execution.quality_gates.exit_criteria.append(
                GateCriterion(
                    criterion_id=f"GC-X-{i:03d}",
                    criterion_type="exit",
                    category="functional",
                    description="d",
                    threshold="t",
                )
            )

        normalized = normalize_execution_result(execution)
        self.assertLessEqual(len(normalized.clarification_questions), 8)
        self.assertLessEqual(len(normalized.test_points), 20)
        self.assertLessEqual(len(normalized.test_cases), 20)
        self.assertLessEqual(len(normalized.review_result.comments), 8)
        self.assertLessEqual(len(normalized.quality_gates.entry_criteria), 8)
        self.assertLessEqual(len(normalized.quality_gates.exit_criteria), 8)
        self.assertLessEqual(len(normalized.test_cases[0].steps), 6)


if __name__ == "__main__":
    unittest.main()
