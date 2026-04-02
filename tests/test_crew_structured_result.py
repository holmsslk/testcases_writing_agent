"""Validation tests for structured crew execution output."""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.crews import TestDesignCrew  # noqa: E402
from test_case_writing_crew.schemas import CrewExecutionResult  # noqa: E402
from test_case_writing_crew.tools import load_documents  # noqa: E402


class CrewStructuredResultTest(unittest.TestCase):
    """Ensure crew returns structured result object for downstream consumers."""

    def test_run_returns_structured_result(self) -> None:
        sample_prd = PROJECT_ROOT / "examples" / "sample_prd.md"
        documents = load_documents([sample_prd])
        inputs = {
            "topic": "integrated_hardware_software_system",
            "documents": [
                {
                    "source_name": d.source_name,
                    "source_type": d.source_type,
                    "raw_text": d.raw_text,
                    "metadata": d.metadata,
                }
                for d in documents
            ],
        }

        result = TestDesignCrew().run(inputs=inputs)
        self.assertIsInstance(result, CrewExecutionResult)
        self.assertGreater(len(result.test_points), 0)
        self.assertGreater(len(result.test_cases), 0)
        self.assertIsNotNone(result.quality_gates)
        self.assertIn("final_output", result.interim_artifacts)


if __name__ == "__main__":
    unittest.main()
