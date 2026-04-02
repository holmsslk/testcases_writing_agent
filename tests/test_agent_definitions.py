"""Tests for MVP agent definitions and YAML merge behavior."""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.agents import (  # noqa: E402
    get_quality_gate_specialist_definition,
    get_quality_reviewer_definition,
    get_requirement_analyst_definition,
    get_test_analyst_definition,
    get_testcase_designer_definition,
)


class AgentDefinitionTest(unittest.TestCase):
    """Ensure five MVP agent definitions are loaded and usable."""

    def test_all_agent_definitions_have_required_fields(self) -> None:
        definitions = [
            get_requirement_analyst_definition(),
            get_test_analyst_definition(),
            get_testcase_designer_definition(),
            get_quality_reviewer_definition(),
            get_quality_gate_specialist_definition(),
        ]
        self.assertEqual(len(definitions), 5)
        for definition in definitions:
            self.assertTrue(definition.role.strip())
            self.assertTrue(definition.goal.strip())
            self.assertTrue(definition.backstory.strip())
            self.assertTrue(definition.prompt_style.strip())
            self.assertIsInstance(definition.verbose, bool)
            self.assertIsInstance(definition.allow_delegation, bool)
            self.assertIsInstance(definition.recommended_tool_names, list)


if __name__ == "__main__":
    unittest.main()
