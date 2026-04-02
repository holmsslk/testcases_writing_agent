"""Task-chain exports for testcase generation MVP."""

from __future__ import annotations

from typing import Any

from .analysis_tasks import get_test_point_generation_task_definition
from .base import TaskDefinition, build_task
from .gate_tasks import get_quality_gate_task_definition
from .requirement_tasks import (
    get_clarification_task_definition,
    get_requirement_analysis_task_definition,
)
from .review_tasks import get_review_task_definition
from .testcase_tasks import (
    get_export_task_definition,
    get_test_case_generation_task_definition,
)

TASK_CHAIN_ORDER = [
    "requirement_analysis_task",
    "clarification_task",
    "test_point_generation_task",
    "test_case_generation_task",
    "review_task",
    "quality_gate_task",
    "export_task",
]


def get_task_chain_definitions(config_path: str | None = None) -> list[TaskDefinition]:
    """Return all seven task definitions in dependency order."""
    return [
        get_requirement_analysis_task_definition(config_path=config_path),
        get_clarification_task_definition(config_path=config_path),
        get_test_point_generation_task_definition(config_path=config_path),
        get_test_case_generation_task_definition(config_path=config_path),
        get_review_task_definition(config_path=config_path),
        get_quality_gate_task_definition(config_path=config_path),
        get_export_task_definition(config_path=config_path),
    ]


def build_task_chain_from_agents(
    agent_objects: dict[str, Any],
    config_path: str | None = None,
) -> list[Any]:
    """Build CrewAI Task objects from agent mapping keyed by agent config names."""
    definitions = get_task_chain_definitions(config_path=config_path)
    task_by_key: dict[str, Any] = {}
    built_tasks: list[Any] = []

    for definition in definitions:
        if definition.agent not in agent_objects:
            raise KeyError(f"missing agent object for '{definition.agent}'")
        context_tasks = [task_by_key[key] for key in definition.context_task_keys if key in task_by_key]
        task_obj = build_task(
            definition=definition,
            agent_obj=agent_objects[definition.agent],
            context_tasks=context_tasks,
        )
        task_by_key[definition.key] = task_obj
        built_tasks.append(task_obj)
    return built_tasks


__all__ = [
    "TaskDefinition",
    "TASK_CHAIN_ORDER",
    "get_requirement_analysis_task_definition",
    "get_clarification_task_definition",
    "get_test_point_generation_task_definition",
    "get_test_case_generation_task_definition",
    "get_review_task_definition",
    "get_quality_gate_task_definition",
    "get_export_task_definition",
    "get_task_chain_definitions",
    "build_task_chain_from_agents",
]
