"""TestAnalyst factory and reusable defaults."""

from __future__ import annotations

from typing import Any

from .base import AgentDefinition, build_agent, merge_with_yaml

TEST_ANALYST_PROMPT_STYLE = (
    "- Output test points in structured form.\n"
    "- Do not fabricate missing requirement details.\n"
    "- If requirement granularity is insufficient, ask explicit clarification questions.\n"
    "- Ensure each point is executable and its expected check is verifiable."
)

DEFAULT_TEST_ANALYST = AgentDefinition(
    key="test_analyst",
    role="TestAnalyst",
    goal=(
        "Generate comprehensive test points covering functional, API, permission, boundary, "
        "exception, compatibility, performance, security, stability, and DFX dimensions."
    ),
    backstory=(
        "You specialize in risk-driven test analysis for integrated hardware-software systems "
        "and ensure broad yet traceable coverage across quality dimensions."
    ),
    prompt_style=TEST_ANALYST_PROMPT_STYLE,
    recommended_tool_names=["knowledge_retriever", "coverage_builder"],
    verbose=True,
    allow_delegation=False,
)


def get_test_analyst_definition(config_path: str | None = None) -> AgentDefinition:
    """Return YAML-aware TestAnalyst definition."""
    return merge_with_yaml(DEFAULT_TEST_ANALYST, config_path=config_path)


def build_test_analyst(
    tools: list[Any] | None = None,
    llm: Any | None = None,
    verbose: bool | None = None,
    allow_delegation: bool | None = None,
    config_path: str | None = None,
):
    """Build CrewAI TestAnalyst agent."""
    definition = get_test_analyst_definition(config_path=config_path)
    return build_agent(
        definition=definition,
        tools=tools,
        llm=llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
    )
