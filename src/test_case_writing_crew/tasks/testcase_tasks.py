"""Testcase generation and export task definitions."""

from __future__ import annotations

from .base import TaskDefinition, merge_with_yaml

DEFAULT_TEST_CASE_GENERATION_TASK = TaskDefinition(
    key="test_case_generation_task",
    description=(
        "Transform test points into executable and verifiable test cases with "
        "clear preconditions, ordered steps, expected_result, and export-oriented fields. "
        "Ensure coverage of integrated-system behavior including command/ack timing, "
        "state sync consistency, recovery after reboot/power loss, and upgrade/rollback checks."
    ),
    expected_output='JSON object: {"test_cases": list[TestCase]}',
    agent="testcase_designer",
    context_sources=["list[TestPoint] from test_point_generation_task"],
    context_task_keys=["test_point_generation_task"],
)

DEFAULT_EXPORT_TASK = TaskDefinition(
    key="export_task",
    description=(
        "Export reviewed artifacts into CSV/Excel deliverables. Ensure output tables are "
        "consistent with export schema and include TestPoints, TestCases, and QualityGates."
    ),
    expected_output=(
        "Export manifest containing generated file paths for CSV and/or Excel outputs."
    ),
    agent="testcase_designer",
    context_sources=[
        "list[TestCase] from test_case_generation_task",
        "ReviewResult from review_task",
        "EntryExitCriteriaSet from quality_gate_task",
    ],
    context_task_keys=["quality_gate_task"],
)


def get_test_case_generation_task_definition(
    config_path: str | None = None,
) -> TaskDefinition:
    """Return YAML-aware test_case_generation_task definition."""
    return merge_with_yaml(DEFAULT_TEST_CASE_GENERATION_TASK, config_path=config_path)


def get_export_task_definition(config_path: str | None = None) -> TaskDefinition:
    """Return YAML-aware export_task definition."""
    return merge_with_yaml(DEFAULT_EXPORT_TASK, config_path=config_path)


def build_testcase_tasks(config_path: str | None = None) -> list[TaskDefinition]:
    """Return testcase stage task definitions."""
    return [
        get_test_case_generation_task_definition(config_path=config_path),
        get_export_task_definition(config_path=config_path),
    ]
