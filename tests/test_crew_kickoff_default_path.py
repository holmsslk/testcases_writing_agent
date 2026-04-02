"""Tests for kickoff-first behavior in TestDesignCrew.run()."""

from __future__ import annotations

from pathlib import Path
import types
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.crews import TestDesignCrew  # noqa: E402
from test_case_writing_crew.schemas import CrewExecutionResult, RequirementSummary  # noqa: E402


class _FakeTaskOutput:
    def __init__(self, raw: str) -> None:
        self.raw = raw


class _FakeKickoffResult:
    def __init__(self, raw_items: list[str]) -> None:
        self.tasks_output = [_FakeTaskOutput(text) for text in raw_items]
        self.raw = raw_items[-1] if raw_items else ""


class CrewKickoffDefaultPathTest(unittest.TestCase):
    def test_run_uses_kickoff_by_default(self) -> None:
        crew = TestDesignCrew()
        calls = {"kickoff": 0, "fallback": 0}

        kickoff_payloads = [
            '{"requirement_summary": {"product_name":"Demo","version":"1.0.0","scope":["s"],'
            '"out_of_scope":[],"modules":["m1"],"user_roles":["r"],"business_rules":["b"],'
            '"external_dependencies":[],"non_functional_requirements":[],"risks":[],"assumptions":[]}}',
            '{"clarification_questions":[{"id":"CQ-1","category":"api","question":"q","impact":"high","required":true}]}',
            '{"test_points":[{"test_point_id":"TP-1","module":"m1","sub_module":"s1","requirement_id":"REQ-1",'
            '"test_dimension":"functional","title":"t","description":"d","priority":"p1","risk_level":"medium","dfx_tags":[],"remarks":""}]}',
            '{"test_cases":[{"case_id":"TC-1","module":"m1","sub_module":"s1","test_point_id":"TP-1","requirement_id":"REQ-1",'
            '"title":"tc","preconditions":["p"],"steps":["s"],"expected_result":"ok","priority":"p1","case_type":"functional",'
            '"automation_candidate":true,"risk_level":"medium","environment":"lab","remarks":""}]}',
            '{"review_result":{"overall_status":"pass","comments":[],"coverage_gaps":[],"duplicates":[],"statistics":{"n":1}}}',
            '{"quality_gates":{"entry_criteria":[],"exit_criteria":[],"project_specific_notes":["n"]}}',
            '{"export":"ok"}',
        ]

        class _FakeCrew:
            def kickoff(self, inputs):  # noqa: ANN001
                _ = inputs
                calls["kickoff"] += 1
                return _FakeKickoffResult(kickoff_payloads)

        crew.crew = types.MethodType(lambda self: _FakeCrew(), crew)

        def _unexpected_fallback(self, inputs):  # noqa: ANN001
            _ = inputs
            calls["fallback"] += 1
            raise AssertionError("fallback should not be used when kickoff parse succeeds")

        crew.execute_pipeline_structured = types.MethodType(_unexpected_fallback, crew)

        result = crew.run(inputs={"documents": []})
        self.assertIsInstance(result, CrewExecutionResult)
        self.assertEqual(calls["kickoff"], 1)
        self.assertEqual(calls["fallback"], 0)
        self.assertEqual(result.requirement_summary.product_name, "Demo")
        self.assertEqual(len(result.test_points), 1)
        self.assertEqual(len(result.test_cases), 1)
        self.assertIsNotNone(result.quality_gates)

    def test_run_fallback_only_when_kickoff_fails(self) -> None:
        crew = TestDesignCrew()

        class _FailingCrew:
            def kickoff(self, inputs):  # noqa: ANN001
                _ = inputs
                raise RuntimeError("simulated kickoff failure")

        crew.crew = types.MethodType(lambda self: _FailingCrew(), crew)

        fallback_result = CrewExecutionResult(requirement_summary=RequirementSummary(product_name="Fallback"))

        crew.execute_pipeline_structured = types.MethodType(
            lambda self, inputs: fallback_result,  # noqa: ANN001
            crew,
        )

        result = crew.run(inputs={"documents": []})
        self.assertIs(result, fallback_result)
        self.assertEqual(result.requirement_summary.product_name, "Fallback")
        self.assertEqual(
            result.interim_artifacts.get("fallback_used"),
            "execute_pipeline_structured",
        )
        self.assertIn("kickoff failed:", str(result.interim_artifacts.get("fallback_reason")))


if __name__ == "__main__":
    unittest.main()
