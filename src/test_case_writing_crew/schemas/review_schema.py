"""Review schemas for testcase artifacts and quality feedback."""

from dataclasses import dataclass, field

from .validators import (
    ensure_dataclass_list,
    ensure_dict,
    ensure_in_set,
    ensure_non_empty_str,
    ensure_str_list,
)

TARGET_TYPES = {"requirement", "test_point", "test_case", "gate", "other"}
SEVERITY_LEVELS = {"low", "medium", "high", "critical"}
REVIEW_STATUS = {"pass", "needs_revision", "fail", "blocked"}


@dataclass
class ReviewComment:
    """Single review issue raised for a target artifact."""

    target_type: str = field(
        default="test_case",
        metadata={"description": "Target artifact type under review."},
    )
    target_id: str = field(
        default="UNKNOWN",
        metadata={"description": "Target artifact identifier."},
    )
    severity: str = field(
        default="medium",
        metadata={"description": "Issue severity level."},
    )
    comment: str = field(
        default="No comment provided.",
        metadata={"description": "Observed problem or concern."},
    )
    suggestion: str = field(
        default="",
        metadata={"description": "Suggested fix or improvement."},
    )

    def __post_init__(self) -> None:
        self.target_type = ensure_in_set(self.target_type, "target_type", TARGET_TYPES)
        self.target_id = ensure_non_empty_str(self.target_id, "target_id")
        self.severity = ensure_in_set(self.severity, "severity", SEVERITY_LEVELS)
        self.comment = ensure_non_empty_str(self.comment, "comment")
        if not isinstance(self.suggestion, str):
            raise TypeError("suggestion must be str")
        self.suggestion = self.suggestion.strip()


@dataclass
class ReviewResult:
    """Aggregated review output for generated test points and test cases."""

    overall_status: str = field(
        default="needs_revision",
        metadata={"description": "Overall review result status."},
    )
    comments: list[ReviewComment] = field(
        default_factory=list,
        metadata={"description": "Detailed review comments."},
    )
    coverage_gaps: list[str] = field(
        default_factory=list,
        metadata={"description": "Detected coverage gaps."},
    )
    duplicates: list[str] = field(
        default_factory=list,
        metadata={"description": "Potential duplicate items or cases."},
    )
    statistics: dict = field(
        default_factory=dict,
        metadata={"description": "Summary statistics, e.g., total/passed/failed counts."},
    )

    def __post_init__(self) -> None:
        self.overall_status = ensure_in_set(
            self.overall_status,
            "overall_status",
            REVIEW_STATUS,
        )
        self.comments = ensure_dataclass_list(self.comments, "comments", ReviewComment)
        self.coverage_gaps = ensure_str_list(self.coverage_gaps, "coverage_gaps")
        self.duplicates = ensure_str_list(self.duplicates, "duplicates")
        self.statistics = ensure_dict(self.statistics, "statistics")
