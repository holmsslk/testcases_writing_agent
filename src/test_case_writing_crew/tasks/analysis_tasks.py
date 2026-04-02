"""Test-point analysis task definitions."""

from __future__ import annotations

from .base import TaskDefinition, merge_with_yaml

DEFAULT_TEST_POINT_GENERATION_TASK = TaskDefinition(
    key="test_point_generation_task",
    description=(
        "Generate structured test points from clarified requirements. Coverage must include "
        "functional, API, permission, boundary, exception, compatibility, performance, "
        "security, stability, and DFX dimensions. Explicitly include integrated-system "
        "scenarios: host-device interaction, command dispatch/ack, communication timeout/retry, "
        "state synchronization, power-off/reboot recovery, upgrade/rollback, "
        "and logging/alerting/diagnosability."
    ),
    expected_output='JSON object: {"test_points": list[TestPoint]}',
    agent="test_analyst",
    context_sources=[
        "RequirementSummary from requirement_analysis_task",
        "ClarificationQuestion list from clarification_task",
    ],
    context_task_keys=["clarification_task"],
)


def get_test_point_generation_task_definition(
    config_path: str | None = None,
) -> TaskDefinition:
    """Return YAML-aware test_point_generation_task definition."""
    return merge_with_yaml(DEFAULT_TEST_POINT_GENERATION_TASK, config_path=config_path)


def build_analysis_tasks(config_path: str | None = None) -> list[TaskDefinition]:
    """Return analysis stage task definitions."""
    return [get_test_point_generation_task_definition(config_path=config_path)]
