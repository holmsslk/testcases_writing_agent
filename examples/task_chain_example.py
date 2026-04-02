"""Minimal task-chain example without requiring full Flow integration."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.tasks import get_task_chain_definitions  # noqa: E402


def main() -> None:
    definitions = get_task_chain_definitions()
    for idx, item in enumerate(definitions, start=1):
        print(f"{idx}. {item.key}")
        print(f"   agent: {item.agent}")
        print(f"   expected_output: {item.expected_output}")
        print(f"   context_task_keys: {item.context_task_keys}")
        print(f"   context_sources: {item.context_sources}")


if __name__ == "__main__":
    main()
