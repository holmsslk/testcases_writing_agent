"""Simple instantiation tests for MVP schemas."""

from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.schemas import (  # noqa: E402
    ClarificationQuestion,
    CoverageMatrixItem,
    EntryExitCriteriaSet,
    GateCriterion,
    RequirementSummary,
    ReviewComment,
    ReviewResult,
    TestCase,
    TestPoint,
)


class SchemaInstantiationTest(unittest.TestCase):
    """Validate that key schema classes can be instantiated."""

    def test_schema_instantiation(self) -> None:
        summary = RequirementSummary(
            product_name="Integrated Control System",
            version="1.2.3",
            scope=["login", "device status", "alerts"],
            modules=["auth", "device", "alert"],
            user_roles=["admin", "operator"],
            business_rules=["alerts must be acknowledged"],
            external_dependencies=["message broker", "device firmware"],
            non_functional_requirements=["response < 2s"],
            risks=["network jitter"],
            assumptions=["test environment has 30 devices"],
        )
        question = ClarificationQuestion(
            id="CQ-100",
            category="security",
            question="Should lockout trigger after 5 failed logins?",
            impact="high",
            required=True,
        )
        point = TestPoint(
            test_point_id="TP-100",
            module="auth",
            sub_module="login",
            requirement_id="REQ-100",
            test_dimension="functional",
            title="Role-based login validation",
            description="Verify different role login behavior and access boundary.",
            priority="p1",
            risk_level="high",
            dfx_tags=["testability", "reliability"],
            remarks="Core smoke coverage",
        )
        case = TestCase(
            case_id="TC-100",
            module="auth",
            sub_module="login",
            test_point_id="TP-100",
            requirement_id="REQ-100",
            title="Admin login with valid credentials",
            preconditions=["Admin account exists"],
            steps=["Open login page", "Input valid admin credentials", "Click login"],
            expected_result="Admin user enters dashboard successfully.",
            priority="p1",
            case_type="functional",
            automation_candidate=True,
            risk_level="medium",
            environment="staging",
            remarks="Can be automated in regression suite",
        )
        matrix_item = CoverageMatrixItem(
            requirement_id="REQ-100",
            requirement_desc="Role-based login must be supported",
            linked_test_points=["TP-100"],
            linked_test_cases=["TC-100"],
            coverage_status="covered",
        )
        comment = ReviewComment(
            target_type="test_case",
            target_id="TC-100",
            severity="medium",
            comment="Add a negative-login case for wrong password.",
            suggestion="Add at least one boundary + lockout case.",
        )
        review = ReviewResult(
            overall_status="needs_revision",
            comments=[comment],
            coverage_gaps=["Missing account lockout test"],
            duplicates=[],
            statistics={"total_cases": 1, "missing_cases": 1},
        )
        entry = GateCriterion(
            criterion_id="GC-E-01",
            criterion_type="entry",
            category="functional",
            description="All high-priority requirements are mapped to test points.",
            threshold="100%",
            mandatory=True,
            remarks="Required before design review",
        )
        exit_criterion = GateCriterion(
            criterion_id="GC-X-01",
            criterion_type="exit",
            category="stability",
            description="No critical open defects before release sign-off.",
            threshold="0 critical defects",
            mandatory=True,
            remarks="Release blocker",
        )
        criteria_set = EntryExitCriteriaSet(
            entry_criteria=[entry],
            exit_criteria=[exit_criterion],
            project_specific_notes=["Hardware firmware should be v3.2+"],
        )

        self.assertEqual(summary.product_name, "Integrated Control System")
        self.assertTrue(question.required)
        self.assertEqual(point.test_point_id, "TP-100")
        self.assertEqual(case.case_id, "TC-100")
        self.assertEqual(matrix_item.coverage_status, "covered")
        self.assertEqual(review.comments[0].target_id, "TC-100")
        self.assertEqual(criteria_set.exit_criteria[0].criterion_type, "exit")


if __name__ == "__main__":
    unittest.main()
