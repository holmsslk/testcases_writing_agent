"""Test-point and coverage schemas for testcase generation MVP."""

from dataclasses import dataclass, field

from .validators import ensure_in_set, ensure_non_empty_str, ensure_str_list

TEST_DIMENSIONS = {
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
}

PRIORITY_LEVELS = {"p0", "p1", "p2", "p3"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
COVERAGE_STATUS = {"not_covered", "partial", "covered", "blocked", "not_applicable"}


@dataclass
class TestPoint:
    """Atomic test objective mapped to requirement and coverage dimension."""

    test_point_id: str = field(
        default="TP-001",
        metadata={"description": "Unique test point identifier."},
    )
    module: str = field(
        default="general",
        metadata={"description": "Product module for the test point."},
    )
    sub_module: str = field(
        default="default",
        metadata={"description": "Sub-module within the product module."},
    )
    requirement_id: str = field(
        default="REQ-UNKNOWN",
        metadata={"description": "Linked requirement identifier."},
    )
    test_dimension: str = field(
        default="functional",
        metadata={"description": "Coverage dimension (functional/api/security/etc.)."},
    )
    title: str = field(
        default="Untitled test point",
        metadata={"description": "Short title of this test point."},
    )
    description: str = field(
        default="No description provided.",
        metadata={"description": "Detailed test intent and check focus."},
    )
    priority: str = field(
        default="p2",
        metadata={"description": "Priority level: p0/p1/p2/p3."},
    )
    risk_level: str = field(
        default="medium",
        metadata={"description": "Risk level: low/medium/high/critical."},
    )
    dfx_tags: list[str] = field(
        default_factory=list,
        metadata={"description": "DFX-related tags such as maintainability/diagnosability."},
    )
    remarks: str = field(
        default="",
        metadata={"description": "Additional remarks and context."},
    )

    def __post_init__(self) -> None:
        self.test_point_id = ensure_non_empty_str(self.test_point_id, "test_point_id")
        self.module = ensure_non_empty_str(self.module, "module")
        self.sub_module = ensure_non_empty_str(self.sub_module, "sub_module")
        self.requirement_id = ensure_non_empty_str(self.requirement_id, "requirement_id")
        self.test_dimension = ensure_in_set(
            self.test_dimension,
            "test_dimension",
            TEST_DIMENSIONS,
        )
        self.title = ensure_non_empty_str(self.title, "title")
        self.description = ensure_non_empty_str(self.description, "description")
        self.priority = ensure_in_set(self.priority, "priority", PRIORITY_LEVELS)
        self.risk_level = ensure_in_set(self.risk_level, "risk_level", RISK_LEVELS)
        self.dfx_tags = ensure_str_list(self.dfx_tags, "dfx_tags")
        if not isinstance(self.remarks, str):
            raise TypeError("remarks must be str")
        self.remarks = self.remarks.strip()


@dataclass
class CoverageMatrixItem:
    """Requirement-to-test artifact coverage mapping row."""

    requirement_id: str = field(
        default="REQ-UNKNOWN",
        metadata={"description": "Requirement identifier."},
    )
    requirement_desc: str = field(
        default="No requirement description provided.",
        metadata={"description": "Requirement text summary."},
    )
    linked_test_points: list[str] = field(
        default_factory=list,
        metadata={"description": "List of linked test point IDs."},
    )
    linked_test_cases: list[str] = field(
        default_factory=list,
        metadata={"description": "List of linked test case IDs."},
    )
    coverage_status: str = field(
        default="not_covered",
        metadata={"description": "Coverage status (not_covered/partial/covered/etc.)."},
    )

    def __post_init__(self) -> None:
        self.requirement_id = ensure_non_empty_str(self.requirement_id, "requirement_id")
        self.requirement_desc = ensure_non_empty_str(
            self.requirement_desc,
            "requirement_desc",
        )
        self.linked_test_points = ensure_str_list(
            self.linked_test_points,
            "linked_test_points",
        )
        self.linked_test_cases = ensure_str_list(
            self.linked_test_cases,
            "linked_test_cases",
        )
        self.coverage_status = ensure_in_set(
            self.coverage_status,
            "coverage_status",
            COVERAGE_STATUS,
        )
