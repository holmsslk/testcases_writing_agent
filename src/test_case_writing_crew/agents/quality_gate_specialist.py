"""QualityGateSpecialist factory and reusable defaults."""

from __future__ import annotations

from typing import Any

from .base import AgentDefinition, build_agent, merge_with_yaml

QUALITY_GATE_SPECIALIST_PROMPT_STYLE = (
    "- Output structured entry/exit criteria and gate rationale.\n"
    "- Do not invent compliance constraints not supported by inputs.\n"
    "- If policy or environment details are missing, explicitly request clarification.\n"
    "- Gate criteria must be measurable, executable, and objectively verifiable."
)

DEFAULT_QUALITY_GATE_SPECIALIST = AgentDefinition(
    key="quality_gate_specialist",
    role="QualityGateSpecialist",
    goal=(
        "Generate entry/exit quality gate criteria tailored for integrated hardware-software "
        "systems, including stability, security, and environment-dependent checks."
    ),
    backstory=(
        "You design release gate standards for complex systems where hardware, firmware, "
        "and software quality risks must be managed together."
    ),
    prompt_style=QUALITY_GATE_SPECIALIST_PROMPT_STYLE,
    recommended_tool_names=["knowledge_retriever"],
    verbose=True,
    allow_delegation=False,
)


def get_quality_gate_specialist_definition(
    config_path: str | None = None,
) -> AgentDefinition:
    """Return YAML-aware QualityGateSpecialist definition."""
    return merge_with_yaml(DEFAULT_QUALITY_GATE_SPECIALIST, config_path=config_path)


def build_quality_gate_specialist(
    tools: list[Any] | None = None,
    llm: Any | None = None,
    verbose: bool | None = None,
    allow_delegation: bool | None = None,
    config_path: str | None = None,
):
    """Build CrewAI QualityGateSpecialist agent."""
    definition = get_quality_gate_specialist_definition(config_path=config_path)
    return build_agent(
        definition=definition,
        tools=tools,
        llm=llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
    )
