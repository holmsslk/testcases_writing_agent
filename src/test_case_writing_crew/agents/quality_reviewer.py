"""QualityReviewer factory and reusable defaults."""

from __future__ import annotations

from typing import Any

from .base import AgentDefinition, build_agent, merge_with_yaml

QUALITY_REVIEWER_PROMPT_STYLE = (
    "- Output structured review results with severity and actionable comments.\n"
    "- Do not fabricate evidence; base all findings on provided artifacts.\n"
    "- If critical information is missing, explicitly mark review as blocked and ask questions.\n"
    "- Validate executability, deduplication, and expected-result verifiability."
)

DEFAULT_QUALITY_REVIEWER = AgentDefinition(
    key="quality_reviewer",
    role="QualityReviewer",
    goal=(
        "Review test points and test cases for coverage completeness, executability, "
        "deduplication quality, and verifiable expected results."
    ),
    backstory=(
        "You are a strict but practical QA reviewer focused on release confidence for "
        "hardware-software integrated products."
    ),
    prompt_style=QUALITY_REVIEWER_PROMPT_STYLE,
    recommended_tool_names=["coverage_builder", "knowledge_retriever"],
    verbose=True,
    allow_delegation=False,
)


def get_quality_reviewer_definition(config_path: str | None = None) -> AgentDefinition:
    """Return YAML-aware QualityReviewer definition."""
    return merge_with_yaml(DEFAULT_QUALITY_REVIEWER, config_path=config_path)


def build_quality_reviewer(
    tools: list[Any] | None = None,
    llm: Any | None = None,
    verbose: bool | None = None,
    allow_delegation: bool | None = None,
    config_path: str | None = None,
):
    """Build CrewAI QualityReviewer agent."""
    definition = get_quality_reviewer_definition(config_path=config_path)
    return build_agent(
        definition=definition,
        tools=tools,
        llm=llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
    )
