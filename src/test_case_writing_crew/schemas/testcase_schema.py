"""Testcase schema definitions for testcase generation MVP."""

from dataclasses import dataclass, field

from .validators import ensure_bool, ensure_in_set, ensure_non_empty_str, ensure_str_list

CASE_TYPES = {
    "functional",
    "api",
    "permission",
    "boundary",
    "exception",
    "compatibility",
    "performance",
    "security",
    "stability",
    "dfx",
    "regression",
    "other",
}
PRIORITY_LEVELS = {"p0", "p1", "p2", "p3"}
RISK_LEVELS = {"low", "medium", "high", "critical"}


@dataclass
class TestCase:
    """Detailed executable test case generated from one test point."""

    case_id: str = field(
        default="TC-001",
        metadata={"description": "Unique test case identifier."},
    )
    module: str = field(
        default="general",
        metadata={"description": "Product module under test."},
    )
    sub_module: str = field(
        default="default",
        metadata={"description": "Sub-module under test."},
    )
    test_point_id: str = field(
        default="TP-001",
        metadata={"description": "Linked test point identifier."},
    )
    requirement_id: str = field(
        default="REQ-UNKNOWN",
        metadata={"description": "Linked requirement identifier."},
    )
    title: str = field(
        default="Untitled test case",
        metadata={"description": "Short title of the test case."},
    )
    preconditions: list[str] = field(
        default_factory=list,
        metadata={"description": "Preconditions that must be satisfied before execution."},
    )
    steps: list[str] = field(
        default_factory=list,
        metadata={"description": "Execution steps in order."},
    )
    expected_result: str = field(
        default="Expected behavior is met.",
        metadata={"description": "Expected result after performing steps."},
    )
    priority: str = field(
        default="p2",
        metadata={"description": "Priority level: p0/p1/p2/p3."},
    )
    case_type: str = field(
        default="functional",
        metadata={"description": "Case type category."},
    )
    automation_candidate: bool = field(
        default=False,
        metadata={"description": "Whether the case is a candidate for automation."},
    )
    risk_level: str = field(
        default="medium",
        metadata={"description": "Risk level: low/medium/high/critical."},
    )
    environment: str = field(
        default="integration",
        metadata={"description": "Target execution environment."},
    )
    remarks: str = field(
        default="",
        metadata={"description": "Additional notes for execution/maintenance."},
    )

    def __post_init__(self) -> None:
        self.case_id = ensure_non_empty_str(self.case_id, "case_id")
        self.module = ensure_non_empty_str(self.module, "module")
        self.sub_module = ensure_non_empty_str(self.sub_module, "sub_module")
        self.test_point_id = ensure_non_empty_str(self.test_point_id, "test_point_id")
        self.requirement_id = ensure_non_empty_str(self.requirement_id, "requirement_id")
        self.title = ensure_non_empty_str(self.title, "title")
        self.preconditions = ensure_str_list(self.preconditions, "preconditions")
        self.steps = ensure_str_list(self.steps, "steps")
        self.expected_result = ensure_non_empty_str(
            self.expected_result,
            "expected_result",
        )
        self.priority = ensure_in_set(self.priority, "priority", PRIORITY_LEVELS)
        self.case_type = ensure_in_set(self.case_type, "case_type", CASE_TYPES)
        self.automation_candidate = ensure_bool(
            self.automation_candidate,
            "automation_candidate",
        )
        self.risk_level = ensure_in_set(self.risk_level, "risk_level", RISK_LEVELS)
        self.environment = ensure_non_empty_str(self.environment, "environment")
        if not isinstance(self.remarks, str):
            raise TypeError("remarks must be str")
        self.remarks = self.remarks.strip()
