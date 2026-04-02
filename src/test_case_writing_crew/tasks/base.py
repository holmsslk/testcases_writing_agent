"""Shared task definition and builder utilities for MVP task chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

TASKS_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "tasks.yaml"


@dataclass
class TaskDefinition:
    """Reusable definition object for one CrewAI task."""

    key: str
    description: str
    expected_output: str
    agent: str
    context_sources: list[str] = field(default_factory=list)
    context_task_keys: list[str] = field(default_factory=list)


def _read_tasks_yaml(config_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Read tasks YAML config, returning empty mapping when file missing."""
    path = Path(config_path) if config_path else TASKS_YAML_PATH
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"tasks config must be a mapping, got {type(data).__name__}")
    return data


def merge_with_yaml(
    definition: TaskDefinition,
    config_path: str | Path | None = None,
) -> TaskDefinition:
    """Merge task defaults with YAML overrides when present."""
    all_config = _read_tasks_yaml(config_path=config_path)
    item = all_config.get(definition.key, {})
    if not isinstance(item, dict):
        raise ValueError(f"task config for '{definition.key}' must be a mapping")

    return TaskDefinition(
        key=definition.key,
        description=str(item.get("description", definition.description)),
        expected_output=str(item.get("expected_output", definition.expected_output)),
        agent=str(item.get("agent", definition.agent)),
        context_sources=list(item.get("context_sources", definition.context_sources)),
        context_task_keys=list(item.get("context_task_keys", definition.context_task_keys)),
    )


def build_task(
    definition: TaskDefinition,
    agent_obj: Any,
    context_tasks: list[Any] | None = None,
):
    """Instantiate CrewAI Task lazily with context dependencies."""
    try:
        from crewai import Task
    except ImportError as exc:
        raise ImportError(
            "crewai is required to instantiate tasks. Run in an environment with crewai installed."
        ) from exc

    description = (
        f"{definition.description}\n\n"
        f"Input context sources: {', '.join(definition.context_sources) or 'none'}"
    )
    kwargs: dict[str, Any] = {
        "description": description,
        "expected_output": definition.expected_output,
        "agent": agent_obj,
    }
    if context_tasks:
        kwargs["context"] = context_tasks
    return Task(**kwargs)
