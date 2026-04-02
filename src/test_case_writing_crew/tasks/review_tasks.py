"""Quality review task definitions."""

from __future__ import annotations

from .base import TaskDefinition, merge_with_yaml

DEFAULT_REVIEW_TASK = TaskDefinition(
    key="review_task",
    description=(
        "Review generated test points and test cases for coverage completeness, "
        "executability, duplicate elimination, and expected-result verifiability. "
        "Highlight gaps in integrated hardware-software scenarios such as timeout/retry, "
        "state sync, recovery, and diagnosability."
    ),
    expected_output='JSON object: {"review_result": ReviewResult}',
    agent="quality_reviewer",
    context_sources=[
        "list[TestPoint] from test_point_generation_task",
        "list[TestCase] from test_case_generation_task",
    ],
    context_task_keys=["test_case_generation_task"],
)


def get_review_task_definition(config_path: str | None = None) -> TaskDefinition:
    """Return YAML-aware review_task definition."""
    return merge_with_yaml(DEFAULT_REVIEW_TASK, config_path=config_path)


def build_review_tasks(config_path: str | None = None) -> list[TaskDefinition]:
    """Return review stage task definitions."""
    return [get_review_task_definition(config_path=config_path)]
