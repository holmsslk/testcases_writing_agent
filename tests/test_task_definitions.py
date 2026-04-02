"""Tests for MVP task chain definitions and dependencies."""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.tasks import TASK_CHAIN_ORDER, get_task_chain_definitions  # noqa: E402


class TaskDefinitionTest(unittest.TestCase):
    """Validate seven-task chain and structured expected outputs."""

    def test_chain_order_and_dependencies(self) -> None:
        tasks = get_task_chain_definitions()
        self.assertEqual([t.key for t in tasks], TASK_CHAIN_ORDER)

        task_map = {t.key: t for t in tasks}
        self.assertEqual(task_map["clarification_task"].context_task_keys, ["requirement_analysis_task"])
        self.assertEqual(task_map["test_point_generation_task"].context_task_keys, ["clarification_task"])
        self.assertEqual(task_map["test_case_generation_task"].context_task_keys, ["test_point_generation_task"])
        self.assertEqual(task_map["review_task"].context_task_keys, ["test_case_generation_task"])
        self.assertEqual(task_map["quality_gate_task"].context_task_keys, ["review_task"])
        self.assertEqual(task_map["export_task"].context_task_keys, ["quality_gate_task"])

    def test_expected_output_is_structured(self) -> None:
        tasks = get_task_chain_definitions()
        expected = {
            "requirement_analysis_task": "requirement_summary",
            "clarification_task": "clarification_questions",
            "test_point_generation_task": "test_points",
            "test_case_generation_task": "test_cases",
            "review_task": "review_result",
            "quality_gate_task": "quality_gates",
        }
        task_map = {t.key: t for t in tasks}
        for task_key, output in expected.items():
            self.assertIn(output, task_map[task_key].expected_output)


if __name__ == "__main__":
    unittest.main()
