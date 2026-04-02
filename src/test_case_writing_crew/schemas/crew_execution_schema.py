"""Structured output schema for crew execution results."""

from dataclasses import dataclass, field
from typing import Any

from .gate_schema import EntryExitCriteriaSet
from .requirement_schema import ClarificationQuestion, RequirementSummary
from .review_schema import ReviewResult
from .testcase_schema import TestCase
from .testpoint_schema import TestPoint
from .validators import ensure_dataclass_list, ensure_dict


@dataclass
class CrewExecutionResult:
    """Unified structured result returned by the core crew."""

    requirement_summary: RequirementSummary
    clarification_questions: list[ClarificationQuestion] = field(default_factory=list)
    test_points: list[TestPoint] = field(default_factory=list)
    test_cases: list[TestCase] = field(default_factory=list)
    review_result: ReviewResult | None = None
    quality_gates: EntryExitCriteriaSet | None = None
    interim_artifacts: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.requirement_summary, RequirementSummary):
            raise TypeError("requirement_summary must be RequirementSummary")
        self.clarification_questions = ensure_dataclass_list(
            self.clarification_questions,
            "clarification_questions",
            ClarificationQuestion,
        )
        self.test_points = ensure_dataclass_list(self.test_points, "test_points", TestPoint)
        self.test_cases = ensure_dataclass_list(self.test_cases, "test_cases", TestCase)
        if self.review_result is not None and not isinstance(self.review_result, ReviewResult):
            raise TypeError("review_result must be ReviewResult | None")
        if self.quality_gates is not None and not isinstance(
            self.quality_gates, EntryExitCriteriaSet
        ):
            raise TypeError("quality_gates must be EntryExitCriteriaSet | None")
        self.interim_artifacts = ensure_dict(self.interim_artifacts, "interim_artifacts")
