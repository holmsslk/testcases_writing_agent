"""Minimal runnable tests for testcase generation flow MVP."""

from pathlib import Path
import tempfile
import unittest
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.flows import TestcaseGenerationFlow  # noqa: E402
from test_case_writing_crew.schemas import (  # noqa: E402
    CrewExecutionResult,
    EntryExitCriteriaSet,
    GateCriterion,
    RequirementSummary,
    ReviewResult,
    TestCase,
    TestPoint,
)


def _fake_crew_result() -> CrewExecutionResult:
    summary = RequirementSummary(
        product_name="Demo Product",
        version="0.1.0",
        scope=["核心流程"],
    )
    points = [
        TestPoint(
            test_point_id="TP-001",
            module="auth",
            sub_module="core",
            requirement_id="REQ-001",
            test_dimension="functional",
            title="【权限管理】验证登录流程",
            description="验证登录流程可正常执行。",
        )
    ]
    cases = [
        TestCase(
            case_id="TC-001",
            module="auth",
            sub_module="core",
            test_point_id="TP-001",
            requirement_id="REQ-001",
            title="【权限管理】验证登录成功",
            preconditions=["系统已启动。"],
            steps=["1）输入正确账号密码并提交。"],
            expected_result="系统提示登录成功并进入首页。",
        )
    ]
    review = ReviewResult(
        overall_status="pass",
        comments=[],
        coverage_gaps=[],
        duplicates=[],
        statistics={"test_point_count": 1, "test_case_count": 1},
    )
    gates = EntryExitCriteriaSet(
        entry_criteria=[
            GateCriterion(
                criterion_id="GC-E-001",
                criterion_type="entry",
                category="functional",
                description="已完成测试点映射。",
                threshold="100%",
            )
        ],
        exit_criteria=[
            GateCriterion(
                criterion_id="GC-X-001",
                criterion_type="exit",
                category="functional",
                description="关键问题为 0。",
                threshold="0",
            )
        ],
        project_specific_notes=[],
    )
    return CrewExecutionResult(
        requirement_summary=summary,
        clarification_questions=[],
        test_points=points,
        test_cases=cases,
        review_result=review,
        quality_gates=gates,
        interim_artifacts={},
    )


class FlowMVPTest(unittest.TestCase):
    """Flow-level smoke test with file-based human review."""

    def test_flow_runs_with_file_based_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            prd_path = tmp_root / "sample_prd.md"
            prd_path.write_text("# Demo Product\nNeed command ack and recovery.", encoding="utf-8")

            human_review_dir = tmp_root / "human_reviews"
            human_review_dir.mkdir(parents=True)
            (human_review_dir / "requirements_review.json").write_text(
                '{"approved": true, "clarified_context": {"version": "0.2.0"}}',
                encoding="utf-8",
            )
            (human_review_dir / "release_review.json").write_text(
                '{"decision": "approve"}',
                encoding="utf-8",
            )

            flow = TestcaseGenerationFlow(
                review_mode="file",
                human_review_dir=human_review_dir,
                outputs_interim_dir=tmp_root / "outputs" / "interim",
                outputs_final_dir=tmp_root / "outputs" / "final",
            )
            state = flow.kickoff(input_files=[str(prd_path)])
            self.assertEqual(state.release_decision, "approve")
            self.assertTrue(state.test_points)
            self.assertTrue(state.test_cases)
            self.assertIn("test_points", state.export_paths)
            self.assertTrue((tmp_root / "outputs" / "final" / "flow_state.json").exists())

    def test_flow_calls_crew_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            prd_path = tmp_root / "sample_prd.md"
            prd_path.write_text("# Demo Product\nNeed command ack and recovery.", encoding="utf-8")

            human_review_dir = tmp_root / "human_reviews"
            human_review_dir.mkdir(parents=True)
            (human_review_dir / "requirements_review.json").write_text(
                '{"approved": true, "clarified_context": {"version": "0.2.0"}}',
                encoding="utf-8",
            )
            (human_review_dir / "release_review.json").write_text(
                '{"decision": "approve"}',
                encoding="utf-8",
            )

            flow = TestcaseGenerationFlow(
                review_mode="file",
                human_review_dir=human_review_dir,
                outputs_interim_dir=tmp_root / "outputs" / "interim",
                outputs_final_dir=tmp_root / "outputs" / "final",
            )

            called = {"run": 0}
            original_run = flow.crew_runner.run

            def wrapped_run(*args, **kwargs):
                called["run"] += 1
                return original_run(*args, **kwargs)

            flow.crew_runner.run = wrapped_run

            state = flow.kickoff(input_files=[str(prd_path)])
            self.assertEqual(state.release_decision, "approve")
            self.assertGreaterEqual(called["run"], 1)

    def test_requirements_review_without_regeneration_triggers_single_kickoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            prd_path = tmp_root / "sample_prd.md"
            prd_path.write_text("# Demo Product\nNeed command ack and recovery.", encoding="utf-8")

            human_review_dir = tmp_root / "human_reviews"
            human_review_dir.mkdir(parents=True)
            (human_review_dir / "requirements_review.json").write_text(
                (
                    '{"approved": true, "requires_regeneration": false, '
                    '"clarified_context": {"version": "0.2.0", "modules": ["auth"]}}'
                ),
                encoding="utf-8",
            )
            (human_review_dir / "release_review.json").write_text(
                '{"decision": "approve"}',
                encoding="utf-8",
            )

            flow = TestcaseGenerationFlow(
                review_mode="file",
                human_review_dir=human_review_dir,
                outputs_interim_dir=tmp_root / "outputs" / "interim",
                outputs_final_dir=tmp_root / "outputs" / "final",
            )

            called = {"run": 0}

            def fake_run(*args, **kwargs):
                called["run"] += 1
                return _fake_crew_result()

            flow.crew_runner.run = fake_run

            state = flow.kickoff(input_files=[str(prd_path)])
            self.assertEqual(state.release_decision, "approve")
            self.assertEqual(called["run"], 1)
            self.assertFalse(flow._rerun_required_after_review)

    def test_requirements_review_with_regeneration_allows_second_kickoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            prd_path = tmp_root / "sample_prd.md"
            prd_path.write_text("# Demo Product\nNeed command ack and recovery.", encoding="utf-8")

            human_review_dir = tmp_root / "human_reviews"
            human_review_dir.mkdir(parents=True)
            (human_review_dir / "requirements_review.json").write_text(
                (
                    '{"approved": true, "requires_regeneration": true, '
                    '"clarified_context": {"modules": ["auth", "device"]}}'
                ),
                encoding="utf-8",
            )
            (human_review_dir / "release_review.json").write_text(
                '{"decision": "approve"}',
                encoding="utf-8",
            )

            flow = TestcaseGenerationFlow(
                review_mode="file",
                human_review_dir=human_review_dir,
                outputs_interim_dir=tmp_root / "outputs" / "interim",
                outputs_final_dir=tmp_root / "outputs" / "final",
            )

            called = {"run": 0}

            def fake_run(*args, **kwargs):
                called["run"] += 1
                return _fake_crew_result()

            flow.crew_runner.run = fake_run

            state = flow.kickoff(input_files=[str(prd_path)])
            self.assertEqual(state.release_decision, "approve")
            self.assertEqual(called["run"], 2)
            self.assertTrue(flow._rerun_required_after_review)


if __name__ == "__main__":
    unittest.main()
