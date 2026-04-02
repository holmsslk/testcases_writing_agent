"""Requirement and clarification task definitions."""

from __future__ import annotations

from .base import TaskDefinition, merge_with_yaml

DEFAULT_REQUIREMENT_ANALYSIS_TASK = TaskDefinition(
    key="requirement_analysis_task",
    description=(
        "Parse PRD/API docs/requirement table into a normalized requirement summary; "
        "identify scope, out-of-scope, module boundaries, role permissions, "
        "external dependencies, non-functional constraints, and key risks for an "
        "integrated hardware-software system."
    ),
    expected_output=(
        'JSON object: {"requirement_summary": RequirementSummary} with '
        "product_name/version/scope/out_of_scope/modules/user_roles/business_rules/"
        "external_dependencies/non_functional_requirements/risks/assumptions."
    ),
    agent="requirement_analyst",
    context_sources=["PRD document", "API specification", "requirement table"],
    context_task_keys=[],
)

DEFAULT_CLARIFICATION_TASK = TaskDefinition(
    key="clarification_task",
    description=(
        "Based on requirement analysis, produce explicit clarification questions for missing "
        "or ambiguous details. Must highlight hardware-software integration concerns: "
        "host-device interaction, command dispatch/ack, communication timeout/retry, "
        "state synchronization, power-off/reboot recovery, upgrade/rollback, "
        "logging/alerting/diagnosability."
    ),
    expected_output='JSON object: {"clarification_questions": list[ClarificationQuestion]}',
    agent="requirement_analyst",
    context_sources=["RequirementSummary from requirement_analysis_task"],
    context_task_keys=["requirement_analysis_task"],
)


def get_requirement_analysis_task_definition(
    config_path: str | None = None,
) -> TaskDefinition:
    """Return YAML-aware requirement_analysis_task definition."""
    return merge_with_yaml(DEFAULT_REQUIREMENT_ANALYSIS_TASK, config_path=config_path)


def get_clarification_task_definition(config_path: str | None = None) -> TaskDefinition:
    """Return YAML-aware clarification_task definition."""
    return merge_with_yaml(DEFAULT_CLARIFICATION_TASK, config_path=config_path)


def build_requirement_tasks(config_path: str | None = None) -> list[TaskDefinition]:
    """Return requirement stage task definitions."""
    return [
        get_requirement_analysis_task_definition(config_path=config_path),
        get_clarification_task_definition(config_path=config_path),
    ]
