"""End-to-end integration test for Flow -> Crew unified pipeline."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.flows import TestcaseGenerationFlow  # noqa: E402


class FlowCrewIntegrationE2ETest(unittest.TestCase):
    """Validate the real integrated main path without mocking core generation."""

    def test_flow_calls_crew_and_exports_csv_with_examples(self) -> None:
        input_files = [
            str(PROJECT_ROOT / "examples" / "sample_prd.md"),
            str(PROJECT_ROOT / "examples" / "sample_api.yaml"),
            str(PROJECT_ROOT / "examples" / "sample_requirement_table.csv"),
        ]
        human_review_dir = PROJECT_ROOT / "examples" / "human_reviews"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            outputs_interim = tmp_root / "outputs" / "interim"
            outputs_final = tmp_root / "outputs" / "final"

            flow = TestcaseGenerationFlow(
                review_mode="file",
                human_review_dir=human_review_dir,
                outputs_interim_dir=outputs_interim,
                outputs_final_dir=outputs_final,
            )

            state = flow.kickoff(input_files=input_files)

            self.assertEqual(state.release_decision, "approve")
            self.assertIsNotNone(flow._crew_result_cache)
            self.assertIsNotNone(state.requirement_summary)
            self.assertTrue(state.test_points)
            self.assertTrue(state.test_cases)
            self.assertIsNotNone(state.quality_gates)
            self.assertIn("test_points", state.export_paths)
            self.assertIn("test_cases", state.export_paths)
            self.assertIn("quality_gates", state.export_paths)

            for key in ("test_points", "test_cases", "quality_gates"):
                self.assertTrue(Path(state.export_paths[key]).exists())

            self.assertTrue((outputs_final / "flow_state.json").exists())


if __name__ == "__main__":
    unittest.main()

