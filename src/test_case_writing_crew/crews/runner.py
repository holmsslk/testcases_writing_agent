"""Stable Python runner interface for TestDesignCrew."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import time
from typing import Any

from test_case_writing_crew.crews.test_design_crew import TestDesignCrew
from test_case_writing_crew.schemas import CrewExecutionResult


@dataclass
class TestDesignCrewInput:
    """Structured input contract for crew execution."""

    source_documents: list[dict[str, Any]] = field(default_factory=list)
    knowledge_context: dict[str, Any] = field(default_factory=dict)
    clarified_context: dict[str, Any] = field(default_factory=dict)
    project_metadata: dict[str, Any] = field(default_factory=dict)


class TestDesignCrewRunner:
    """Stable wrapper for invoking core crew from Flow or Python services."""

    def __init__(self, crew: TestDesignCrew | None = None) -> None:
        self._crew = crew or TestDesignCrew()

    def run(self, crew_input: TestDesignCrewInput) -> CrewExecutionResult:
        """Run core crew and return structured result."""
        started_at = time.monotonic()
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [STAGE] start: TestDesignCrewRunner.run",
            flush=True,
        )
        payload = {
            "documents": crew_input.source_documents,
            "knowledge_context": crew_input.knowledge_context,
            "clarified_context": crew_input.clarified_context,
            "project_metadata": crew_input.project_metadata,
        }
        result = self._crew.run(inputs=payload)
        duration = time.monotonic() - started_at
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [STAGE] end: TestDesignCrewRunner.run "
            f"(duration={duration:.2f}s)",
            flush=True,
        )
        return result

    def run_text(self, crew_input: TestDesignCrewInput):
        """Optional text-first execution path for compatibility."""
        payload = {
            "documents": crew_input.source_documents,
            "knowledge_context": crew_input.knowledge_context,
            "clarified_context": crew_input.clarified_context,
            "project_metadata": crew_input.project_metadata,
        }
        return self._crew.run_text(inputs=payload)


def run_test_design_crew(crew_input: TestDesignCrewInput) -> CrewExecutionResult:
    """Convenience function for one-off structured execution."""
    return TestDesignCrewRunner().run(crew_input)
