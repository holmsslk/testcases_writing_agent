"""RequirementAnalyst factory and reusable defaults."""

from __future__ import annotations

from typing import Any

from .base import AgentDefinition, build_agent, merge_with_yaml

REQUIREMENT_ANALYST_PROMPT_STYLE = (
    "- Output must be structured and schema-aligned.\n"
    "- Do not invent requirements or interfaces.\n"
    "- If information is missing, explicitly list clarification questions.\n"
    "- Generated analysis must be executable and verifiable by QA."
)

DEFAULT_REQUIREMENT_ANALYST = AgentDefinition(
    key="requirement_analyst",
    role="RequirementAnalyst",
    goal=(
        "Parse PRD, API docs, and requirement tables; produce a RequirementSummary and "
        "ClarificationQuestion list for unresolved gaps."
    ),
    backstory=(
        "You are a senior requirement analyst for integrated hardware-software systems. "
        "You extract concrete scope, dependencies, and risks while preserving traceability."
    ),
    prompt_style=REQUIREMENT_ANALYST_PROMPT_STYLE,
    recommended_tool_names=["document_loader", "knowledge_retriever"],
    verbose=True,
    allow_delegation=True,
)


def get_requirement_analyst_definition(
    config_path: str | None = None,
) -> AgentDefinition:
    """Return YAML-aware RequirementAnalyst definition."""
    return merge_with_yaml(DEFAULT_REQUIREMENT_ANALYST, config_path=config_path)


def build_requirement_analyst(
    tools: list[Any] | None = None,
    llm: Any | None = None,
    verbose: bool | None = None,
    allow_delegation: bool | None = None,
    config_path: str | None = None,
):
    """Build CrewAI RequirementAnalyst agent."""
    definition = get_requirement_analyst_definition(config_path=config_path)
    return build_agent(
        definition=definition,
        tools=tools,
        llm=llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
    )
