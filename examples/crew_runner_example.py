"""Minimal example for calling the stable TestDesignCrewRunner interface."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.crews import TestDesignCrewInput, TestDesignCrewRunner  # noqa: E402
from test_case_writing_crew.tools import load_documents  # noqa: E402


def main() -> None:
    files = [
        PROJECT_ROOT / "examples" / "sample_prd.md",
        PROJECT_ROOT / "examples" / "sample_api.yaml",
    ]
    docs = load_documents(files)
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
        clarified_context={"version": "0.1.0"},
        project_metadata={"demo": "crew_runner_example"},
    )
    result = TestDesignCrewRunner().run(crew_input=crew_input)
    print("test_points:", len(result.test_points))
    print("test_cases:", len(result.test_cases))
    print("quality_gates(exit):", len(result.quality_gates.exit_criteria) if result.quality_gates else 0)


if __name__ == "__main__":
    main()
