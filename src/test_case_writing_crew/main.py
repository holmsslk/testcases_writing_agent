#!/usr/bin/env python3
"""Unified runnable entry for testcase generation MVP.

Recommended primary entry: Flow (end-to-end with human review and export).
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import time

from test_case_writing_crew.crews import TestDesignCrewInput, TestDesignCrewRunner
from test_case_writing_crew.flows import TestcaseGenerationFlow
from test_case_writing_crew.tools import load_documents


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_input_files() -> list[str]:
    root = _project_root()
    return [
        str(root / "examples" / "sample_prd.md"),
        str(root / "examples" / "sample_api.yaml"),
        str(root / "examples" / "sample_requirement_table.csv"),
    ]


def _build_crew_input(input_files: list[str]) -> TestDesignCrewInput:
    """Load input files and build structured crew input."""
    documents = load_documents(input_files)
    return TestDesignCrewInput(
        source_documents=[
            {
                "source_name": d.source_name,
                "source_type": d.source_type,
                "raw_text": d.raw_text,
                "metadata": d.metadata,
            }
            for d in documents
        ],
        knowledge_context={"base_dir": str(_project_root() / "knowledge")},
        clarified_context={},
        project_metadata={"topic": "integrated_hardware_software_system"},
    )


def run_crew(input_files: list[str] | None = None) -> Any:
    """Run only core Crew with input files (debug entry)."""
    crew_input = _build_crew_input(input_files or _default_input_files())
    return TestDesignCrewRunner().run(crew_input=crew_input)


def run_flow(
    input_files: list[str] | None = None,
    review_mode: str = "file",
    human_review_dir: str | Path | None = None,
    outputs_interim_dir: str | Path | None = None,
    outputs_final_dir: str | Path | None = None,
    max_requirement_loops: int = 2,
    max_rework_loops: int = 2,
) -> Any:
    """Run the integrated Flow -> Crew -> review -> export pipeline."""
    root = _project_root()
    flow = TestcaseGenerationFlow(
        review_mode=review_mode,
        human_review_dir=human_review_dir or (root / "examples" / "human_reviews"),
        outputs_interim_dir=outputs_interim_dir or (root / "outputs" / "interim"),
        outputs_final_dir=outputs_final_dir or (root / "outputs" / "final"),
    )
    return flow.kickoff(
        input_files=input_files or _default_input_files(),
        max_requirement_loops=max_requirement_loops,
        max_rework_loops=max_rework_loops,
    )


def run(argv: list[str] | None = None) -> Any:
    """Recommended run target: integrated flow."""
    parser = argparse.ArgumentParser(
        description="Test case generation MVP entry (default: integrated flow)."
    )
    parser.add_argument(
        "--mode",
        choices=["flow", "crew-debug"],
        default="flow",
        help="Run mode. 'flow' is the recommended end-to-end entry.",
    )
    parser.add_argument(
        "--input",
        dest="input_files",
        action="append",
        help="Input file path. Repeat this option for multiple files.",
    )
    parser.add_argument(
        "--review-mode",
        choices=["file", "cli"],
        default="file",
        help="Human review mode for flow mode.",
    )
    parser.add_argument(
        "--human-review-dir",
        default=None,
        help="Directory of review files in file review mode.",
    )
    parser.add_argument(
        "--outputs-interim-dir",
        default=None,
        help="Interim output directory.",
    )
    parser.add_argument(
        "--outputs-final-dir",
        default=None,
        help="Final output directory.",
    )
    parser.add_argument(
        "--max-requirement-loops",
        type=int,
        default=2,
        help="Maximum loops for requirement human review.",
    )
    parser.add_argument(
        "--max-rework-loops",
        type=int,
        default=2,
        help="Maximum loops for testcase/release rework.",
    )
    args = parser.parse_args(argv)

    started_at = time.monotonic()
    print(
        f"{datetime.now().isoformat(timespec='seconds')} [STAGE] start: main.run(mode={args.mode})",
        flush=True,
    )
    if args.mode == "crew-debug":
        result = run_crew(input_files=args.input_files)
        duration = time.monotonic() - started_at
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [STAGE] end: main.run(mode={args.mode}) "
            f"(duration={duration:.2f}s)",
            flush=True,
        )
        return result

    result = run_flow(
        input_files=args.input_files,
        review_mode=args.review_mode,
        human_review_dir=args.human_review_dir,
        outputs_interim_dir=args.outputs_interim_dir,
        outputs_final_dir=args.outputs_final_dir,
        max_requirement_loops=args.max_requirement_loops,
        max_rework_loops=args.max_rework_loops,
    )
    duration = time.monotonic() - started_at
    print(
        f"{datetime.now().isoformat(timespec='seconds')} [STAGE] end: main.run(mode={args.mode}) "
        f"(duration={duration:.2f}s)",
        flush=True,
    )
    if duration > 300:
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [WARN] main.run exceeded 300s "
            f"(actual={duration:.2f}s) ; possible cause: slow Crew task or repeated rework loops.",
            flush=True,
        )
    return result


def kickoff() -> Any:
    """Compatibility alias for runtime conventions."""
    return run()


if __name__ == "__main__":
    result = run()
    print(
        f"{datetime.now().isoformat(timespec='seconds')} [STAGE] start: main.__main__.serialize_output",
        flush=True,
    )
    try:
        if is_dataclass(result):
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        else:
            print(getattr(result, "raw", json.dumps(result, ensure_ascii=False, indent=2)))
    except TypeError:
        print(str(result))
    print(
        f"{datetime.now().isoformat(timespec='seconds')} [STAGE] end: main.__main__.serialize_output",
        flush=True,
    )
    print(
        f"{datetime.now().isoformat(timespec='seconds')} [STAGE] end: process_exit_ready",
        flush=True,
    )
