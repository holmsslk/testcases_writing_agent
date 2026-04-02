"""Shared agent factory helpers for MVP agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

AGENTS_YAML_PATH = Path(__file__).resolve().parents[1] / "config" / "agents.yaml"


@dataclass
class AgentDefinition:
    """Reusable definition object for one CrewAI agent."""

    key: str
    role: str
    goal: str
    backstory: str
    prompt_style: str
    recommended_tool_names: list[str] = field(default_factory=list)
    verbose: bool = True
    allow_delegation: bool = False


def _read_agents_yaml(config_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Read agents YAML config, returning an empty map if file is missing."""
    path = Path(config_path) if config_path else AGENTS_YAML_PATH
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"agents config must be a mapping, got: {type(data).__name__}")
    return data


def merge_with_yaml(
    definition: AgentDefinition,
    config_path: str | Path | None = None,
) -> AgentDefinition:
    """Merge default definition with YAML overrides when present."""
    all_config = _read_agents_yaml(config_path=config_path)
    item = all_config.get(definition.key, {})
    if not isinstance(item, dict):
        raise ValueError(f"agent config for '{definition.key}' must be a mapping")

    return AgentDefinition(
        key=definition.key,
        role=str(item.get("role", definition.role)),
        goal=str(item.get("goal", definition.goal)),
        backstory=str(item.get("backstory", definition.backstory)),
        prompt_style=str(item.get("prompt_style", definition.prompt_style)),
        recommended_tool_names=list(
            item.get("recommended_tool_names", definition.recommended_tool_names)
        ),
        verbose=bool(item.get("verbose", definition.verbose)),
        allow_delegation=bool(item.get("allow_delegation", definition.allow_delegation)),
    )


def build_agent(
    definition: AgentDefinition,
    tools: list[Any] | None = None,
    llm: Any | None = None,
    verbose: bool | None = None,
    allow_delegation: bool | None = None,
):
    """Instantiate CrewAI Agent lazily to avoid hard dependency at import time."""
    try:
        from crewai import Agent
    except ImportError as exc:
        raise ImportError(
            "crewai is required to instantiate agents. Run in an environment with crewai installed."
        ) from exc

    merged_backstory = (
        f"{definition.backstory}\n\n"
        f"Prompt style guidance:\n{definition.prompt_style}\n\n"
        f"Recommended tools: {', '.join(definition.recommended_tool_names) or 'none'}"
    )
    kwargs: dict[str, Any] = {
        "role": definition.role,
        "goal": definition.goal,
        "backstory": merged_backstory,
        "verbose": definition.verbose if verbose is None else verbose,
        "allow_delegation": (
            definition.allow_delegation
            if allow_delegation is None
            else allow_delegation
        ),
        "tools": tools or [],
    }
    if llm is not None:
        kwargs["llm"] = llm

    return Agent(**kwargs)
