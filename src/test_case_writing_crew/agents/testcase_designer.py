"""TestcaseDesigner factory and reusable defaults."""

from __future__ import annotations

from typing import Any

from .base import AgentDefinition, build_agent, merge_with_yaml

TESTCASE_DESIGNER_PROMPT_STYLE = (
    "- Output structured test cases directly mappable to Excel/CSV columns.\n"
    "- Do not infer undocumented behavior as facts.\n"
    "- If prerequisite data is missing, list explicit clarification items.\n"
    "- Every test case must be executable and expected results must be objectively verifiable."
)

DEFAULT_TESTCASE_DESIGNER = AgentDefinition(
    key="testcase_designer",
    role="TestcaseDesigner",
    goal=(
        "Transform approved test points into detailed, structured test cases suitable for "
        "CSV/Excel export and execution by QA teams."
    ),
    backstory=(
        "You are an expert in test case design for complex integrated systems, balancing "
        "coverage depth, execution clarity, and downstream automation readiness."
    ),
    prompt_style=TESTCASE_DESIGNER_PROMPT_STYLE,
    recommended_tool_names=["knowledge_retriever", "csv_exporter", "excel_exporter"],
    verbose=True,
    allow_delegation=False,
)


def get_testcase_designer_definition(
    config_path: str | None = None,
) -> AgentDefinition:
    """Return YAML-aware TestcaseDesigner definition."""
    return merge_with_yaml(DEFAULT_TESTCASE_DESIGNER, config_path=config_path)


def build_testcase_designer(
    tools: list[Any] | None = None,
    llm: Any | None = None,
    verbose: bool | None = None,
    allow_delegation: bool | None = None,
    config_path: str | None = None,
):
    """Build CrewAI TestcaseDesigner agent."""
    definition = get_testcase_designer_definition(config_path=config_path)
    return build_agent(
        definition=definition,
        tools=tools,
        llm=llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
    )
