#!/usr/bin/env python3
"""Manual verification script for unified Flow -> Crew integration."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from test_case_writing_crew.flows import TestcaseGenerationFlow  # noqa: E402


def main() -> int:
    input_files = [
        str(PROJECT_ROOT / "examples" / "sample_prd.md"),
        str(PROJECT_ROOT / "examples" / "sample_api.yaml"),
        str(PROJECT_ROOT / "examples" / "sample_requirement_table.csv"),
    ]
    outputs_interim = PROJECT_ROOT / "outputs" / "interim"
    outputs_final = PROJECT_ROOT / "outputs" / "final"

    flow = TestcaseGenerationFlow(
        review_mode="file",
        human_review_dir=PROJECT_ROOT / "examples" / "human_reviews",
        outputs_interim_dir=outputs_interim,
        outputs_final_dir=outputs_final,
    )
    state = flow.kickoff(input_files=input_files)

    checks: list[tuple[str, bool]] = [
        ("crew_result_cache_exists", flow._crew_result_cache is not None),
        ("requirement_summary_exists", state.requirement_summary is not None),
        ("test_points_exists", len(state.test_points) > 0),
        ("test_cases_exists", len(state.test_cases) > 0),
        ("quality_gates_exists", state.quality_gates is not None),
        ("export_test_points_csv", Path(state.export_paths.get("test_points", "")).exists()),
        ("export_test_cases_csv", Path(state.export_paths.get("test_cases", "")).exists()),
        ("export_quality_gates_csv", Path(state.export_paths.get("quality_gates", "")).exists()),
        ("final_flow_state_json", (outputs_final / "flow_state.json").exists()),
    ]

    failed = [name for name, ok in checks if not ok]
    summary = {
        "release_decision": state.release_decision,
        "checks": [{"name": name, "ok": ok} for name, ok in checks],
        "export_paths": state.export_paths,
        "counts": {
            "test_points": len(state.test_points),
            "test_cases": len(state.test_cases),
            "entry_gates": len(state.quality_gates.entry_criteria) if state.quality_gates else 0,
            "exit_gates": len(state.quality_gates.exit_criteria) if state.quality_gates else 0,
        },
        "state_preview": {
            "requirement_summary": asdict(state.requirement_summary)
            if state.requirement_summary
            else None,
        },
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failed:
        print(f"\nverification failed: {', '.join(failed)}")
        return 1
    print("\nverification passed: Flow -> Crew integrated path is runnable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

