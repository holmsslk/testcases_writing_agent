"""Tests for stable crew runner interface."""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.crews import TestDesignCrewInput, TestDesignCrewRunner  # noqa: E402
from test_case_writing_crew.schemas import CrewExecutionResult  # noqa: E402
from test_case_writing_crew.tools import load_documents  # noqa: E402


class CrewRunnerInterfaceTest(unittest.TestCase):
    """Validate stable Python interface for structured crew execution."""

    def test_runner_returns_structured_result(self) -> None:
        docs = load_documents([PROJECT_ROOT / "examples" / "sample_prd.md"])
        crew_input = TestDesignCrewInput(
            source_documents=[
                {
                    "source_name": d.source_name,
                    "source_type": d.source_type,
                    "raw_text": d.raw_text,
                    "metadata": d.metadata,
                }
                for d in docs
            ],
            knowledge_context={"base_dir": str(PROJECT_ROOT / "knowledge")},
            clarified_context={},
            project_metadata={"test": "runner_interface"},
        )
        result = TestDesignCrewRunner().run(crew_input)
        self.assertIsInstance(result, CrewExecutionResult)
        self.assertGreater(len(result.test_points), 0)
        self.assertGreater(len(result.test_cases), 0)
        self.assertIsNotNone(result.quality_gates)


if __name__ == "__main__":
    unittest.main()
