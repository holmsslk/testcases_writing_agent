"""Quality gate task definitions."""

from __future__ import annotations

from .base import TaskDefinition, merge_with_yaml

DEFAULT_QUALITY_GATE_TASK = TaskDefinition(
    key="quality_gate_task",
    description=(
        "Generate measurable entry/exit criteria and project-specific quality gates for "
        "integrated hardware-software systems. Criteria should explicitly cover host-device "
        "interaction, command dispatch/ack, communication timeout/retry, state synchronization, "
        "power-off/reboot recovery, upgrade/rollback, and logging/alerting/diagnosability."
    ),
    expected_output='JSON object: {"quality_gates": EntryExitCriteriaSet}',
    agent="quality_gate_specialist",
    context_sources=["ReviewResult from review_task"],
    context_task_keys=["review_task"],
)


def get_quality_gate_task_definition(config_path: str | None = None) -> TaskDefinition:
    """Return YAML-aware quality_gate_task definition."""
    return merge_with_yaml(DEFAULT_QUALITY_GATE_TASK, config_path=config_path)


def build_gate_tasks(config_path: str | None = None) -> list[TaskDefinition]:
    """Return gate stage task definitions."""
    return [get_quality_gate_task_definition(config_path=config_path)]
