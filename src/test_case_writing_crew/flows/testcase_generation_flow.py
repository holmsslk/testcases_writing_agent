"""MVP flow orchestration for testcase generation with human review checkpoints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any

import yaml

from test_case_writing_crew.schemas import (
    ClarificationQuestion,
    CrewExecutionResult,
    EntryExitCriteriaSet,
    RequirementSummary,
    ReviewResult,
    TestCase,
    TestPoint,
)
from test_case_writing_crew.crews import TestDesignCrewInput, TestDesignCrewRunner
from test_case_writing_crew.tools import (
    export_mvp_csv_bundle,
    export_mvp_excel,
    load_documents,
    normalize_execution_result,
)


@dataclass
class TestcaseGenerationState:
    """State container for the end-to-end MVP flow."""

    input_files: list[str] = field(default_factory=list)
    requirement_summary: RequirementSummary | None = None
    clarification_questions: list[ClarificationQuestion] = field(default_factory=list)
    clarified_context: dict[str, Any] = field(default_factory=dict)
    test_points: list[TestPoint] = field(default_factory=list)
    test_cases: list[TestCase] = field(default_factory=list)
    review_result: ReviewResult | None = None
    quality_gates: EntryExitCriteriaSet | None = None
    export_paths: dict[str, str] = field(default_factory=dict)
    release_decision: str = "pending"


class TestcaseGenerationFlow:
    """Local MVP flow with file/CLI human review checkpoints."""

    def __init__(
        self,
        review_mode: str = "file",
        human_review_dir: str | Path | None = None,
        outputs_interim_dir: str | Path = "outputs/interim",
        outputs_final_dir: str | Path = "outputs/final",
    ) -> None:
        self.review_mode = review_mode
        self.human_review_dir = (
            Path(human_review_dir)
            if human_review_dir is not None
            else Path("examples/human_reviews")
        )
        self.outputs_interim_dir = Path(outputs_interim_dir)
        self.outputs_final_dir = Path(outputs_final_dir)
        self.state = TestcaseGenerationState()
        # Flow depends on stable runner interface instead of crew internals.
        self.crew_runner = TestDesignCrewRunner()
        self._crew_result_cache: CrewExecutionResult | None = None
        self._documents_cache: list[dict[str, Any]] | None = None
        self._crew_kickoff_count: int = 0
        self._rerun_required_after_review: bool = False

    @staticmethod
    def _has_material_generation_change(clarified_context: dict[str, Any]) -> bool:
        """Return True only when review updates can materially affect generation."""
        material_keys = {
            "version",
            "modules",
            "user_roles",
            "business_rules",
            "external_dependencies",
            "non_functional_requirements",
            "risks",
            "assumptions",
            "priority_rules",
            "scope",
            "out_of_scope",
            "constraints",
        }
        return any(key in material_keys and clarified_context.get(key) for key in clarified_context)

    def _stage_start(self, name: str) -> float:
        started_at = time.monotonic()
        print(f"{datetime.now().isoformat(timespec='seconds')} [STAGE] start: {name}", flush=True)
        return started_at

    def _stage_end(self, name: str, started_at: float, warn_after_s: float | None = None) -> float:
        duration = time.monotonic() - started_at
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [STAGE] end: {name} "
            f"(duration={duration:.2f}s)",
            flush=True,
        )
        if warn_after_s is not None and duration > warn_after_s:
            print(
                f"{datetime.now().isoformat(timespec='seconds')} [WARN] stage_slow: {name} "
                f"exceeded {warn_after_s:.0f}s (actual={duration:.2f}s) ; "
                "possible cause: long LLM call, review wait, or I/O bottleneck.",
                flush=True,
            )
        return duration

    def _build_crew_input(
        self,
        documents: list[dict[str, Any]],
        regeneration_round: int = 0,
    ) -> TestDesignCrewInput:
        return TestDesignCrewInput(
            source_documents=documents,
            knowledge_context={"base_dir": "knowledge"},
            clarified_context=dict(self.state.clarified_context),
            project_metadata={
                "flow": "testcase_generation_flow",
                "regeneration_round": regeneration_round,
            },
        )

    def _run_crew(
        self,
        docs: list[dict[str, Any]],
        regeneration_round: int = 0,
        force: bool = False,
    ) -> CrewExecutionResult:
        stage = f"flow._run_crew(force={force}, regeneration_round={regeneration_round})"
        started = self._stage_start(stage)
        cache_miss = self._crew_result_cache is None or force
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [FLOW] crew_cache: "
            f"{'miss' if cache_miss else 'hit'}",
            flush=True,
        )
        if cache_miss:
            self._crew_kickoff_count += 1
            self._crew_result_cache = self.crew_runner.run(
                self._build_crew_input(docs, regeneration_round=regeneration_round)
            )
        result = self._crew_result_cache
        self._stage_end(stage, started, warn_after_s=180)
        if result is None:
            raise RuntimeError("crew result cache is unexpectedly empty")
        return result

    def _get_ingested_documents(self) -> list[dict[str, Any]]:
        if self._documents_cache is None:
            self._documents_cache = self.ingest_documents()
        return self._documents_cache

    def _sync_state_from_crew_result(
        self,
        crew_result: CrewExecutionResult,
        persist_interim: bool = True,
    ) -> None:
        """Synchronize Flow state from Crew structured output.

        Deprecated local generators are intentionally not called anymore.
        Core generation is now owned by Crew and distributed to Flow state here.
        """
        started = self._stage_start("flow._sync_state_from_crew_result")
        self.state.requirement_summary = crew_result.requirement_summary
        self.state.clarification_questions = crew_result.clarification_questions
        self.state.test_points = crew_result.test_points
        self.state.test_cases = crew_result.test_cases
        self.state.review_result = crew_result.review_result
        self.state.quality_gates = crew_result.quality_gates

        if persist_interim:
            self._save_interim_json(
                "02_requirement_analysis",
                {
                    "requirement_summary": asdict(crew_result.requirement_summary),
                    "clarification_questions": [asdict(q) for q in crew_result.clarification_questions],
                },
            )
            self._save_interim_json("04_test_points", [asdict(tp) for tp in crew_result.test_points])
            self._save_interim_json("05_test_cases", [asdict(tc) for tc in crew_result.test_cases])
            if crew_result.review_result is not None:
                self._save_interim_json("06_review_result", asdict(crew_result.review_result))
            if crew_result.quality_gates is not None:
                self._save_interim_json("07_quality_gates", asdict(crew_result.quality_gates))
        self._stage_end("flow._sync_state_from_crew_result", started, warn_after_s=20)

    def _ensure_dirs(self) -> None:
        self.outputs_interim_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_final_dir.mkdir(parents=True, exist_ok=True)

    def _save_interim_json(self, name: str, payload: Any) -> None:
        output_path = self.outputs_interim_dir / f"{name}.json"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _serialize_state(self) -> dict[str, Any]:
        """Return one canonical, JSON-serializable state payload."""
        return {
            "input_files": list(self.state.input_files),
            "requirement_summary": (
                asdict(self.state.requirement_summary)
                if self.state.requirement_summary is not None
                else None
            ),
            "clarification_questions": [asdict(item) for item in self.state.clarification_questions],
            "clarified_context": dict(self.state.clarified_context),
            "test_points": [asdict(item) for item in self.state.test_points],
            "test_cases": [asdict(item) for item in self.state.test_cases],
            "review_result": asdict(self.state.review_result) if self.state.review_result else None,
            "quality_gates": asdict(self.state.quality_gates) if self.state.quality_gates else None,
            "export_paths": dict(self.state.export_paths),
            "release_decision": self.state.release_decision,
        }

    def _save_state_snapshot(self, stage: str) -> None:
        """Persist canonical state snapshot for auditing/debugging per stage."""
        self._save_interim_json(f"{stage}_state", self._serialize_state())

    def _load_human_review_file(self, file_name: str) -> dict[str, Any]:
        path = self.human_review_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"human review file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text) or {}
        else:
            data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"human review file must contain a mapping: {path}")
        return data

    def _human_review_payload(self, stage: str, file_name: str) -> dict[str, Any]:
        if self.review_mode == "file":
            return self._load_human_review_file(file_name)
        if self.review_mode == "cli":
            if stage == "human_release_review":
                decision = input(
                    f"[{stage}] decision (approve/rework/reject): "
                ).strip().lower()
                notes = input(f"[{stage}] notes: ").strip()
                return {"decision": decision, "notes": notes}
            approved = input(f"[{stage}] approved? (y/n): ").strip().lower() in {"y", "yes"}
            notes = input(f"[{stage}] notes: ").strip()
            return {"approved": approved, "notes": notes}
        raise ValueError("review_mode must be 'file' or 'cli'")

    # 1) ingest_documents
    # Input: state.input_files
    # Output: loaded document dict list persisted to interim
    def ingest_documents(self) -> list[dict[str, Any]]:
        started = self._stage_start("ingest_documents")
        docs = load_documents(self.state.input_files)
        payload = [
            {
                "source_name": d.source_name,
                "source_type": d.source_type,
                "raw_text": d.raw_text,
                "metadata": d.metadata,
            }
            for d in docs
        ]
        self._documents_cache = payload
        self._save_interim_json("01_ingested_documents", payload)
        self._stage_end("ingest_documents", started, warn_after_s=20)
        return payload

    # 2) analyze_requirements
    # Input: ingested docs + clarified_context
    # Output: RequirementSummary + ClarificationQuestion list
    def analyze_requirements(self, docs: list[dict[str, Any]]) -> None:
        started = self._stage_start("analyze_requirements")
        crew_result = self._run_crew(docs, force=True)
        # Crew-owned core generation (summary/questions/points/cases/review/gates).
        self._sync_state_from_crew_result(crew_result)
        self._save_state_snapshot("02_requirement_analysis")
        self._stage_end("analyze_requirements", started, warn_after_s=180)

    # 3) human_review_requirements
    # Input: requirement_summary + clarification_questions
    # Output: approval decision + clarified_context updates
    def human_review_requirements(self) -> bool:
        started = self._stage_start("human_review_requirements")
        payload = self._human_review_payload(
            stage="human_review_requirements",
            file_name="requirements_review.json",
        )
        approved = bool(payload.get("approved", False))
        requires_regeneration = bool(payload.get("requires_regeneration", False))
        clarified_context = payload.get("clarified_context", {})
        if isinstance(clarified_context, dict):
            before_context = dict(self.state.clarified_context)
            self.state.clarified_context.update(clarified_context)
            context_changed = self.state.clarified_context != before_context
            material_change = self._has_material_generation_change(clarified_context)
            should_rerun = requires_regeneration and context_changed and material_change
            self._rerun_required_after_review = should_rerun
            if should_rerun:
                print(
                    f"{datetime.now().isoformat(timespec='seconds')} [FLOW] requirements_review: "
                    "requires_regeneration=true -> invalidate cache and rerun crew",
                    flush=True,
                )
                self._crew_result_cache = None
            else:
                print(
                    f"{datetime.now().isoformat(timespec='seconds')} [FLOW] requirements_review: "
                    "requires_regeneration=false -> reuse first crew result",
                    flush=True,
                )
                print(
                    f"{datetime.now().isoformat(timespec='seconds')} [FLOW] review_regeneration_check: "
                    f"requires_regeneration={requires_regeneration}, context_changed={context_changed}, "
                    f"material_change={material_change}",
                    flush=True,
                )
        else:
            # keep previous context when payload format is invalid
            self._rerun_required_after_review = False
            print(
                f"{datetime.now().isoformat(timespec='seconds')} [FLOW] requirements_review: "
                "clarified_context invalid format -> reuse first crew result",
                flush=True,
            )
        self._save_interim_json("03_human_review_requirements", payload)
        self._save_state_snapshot("03_human_review_requirements")
        self._stage_end("human_review_requirements", started, warn_after_s=60)
        return approved

    # 4) generate_test_points
    # Input: requirement_summary + clarified_context
    # Output: list[TestPoint]
    def generate_test_points(self) -> None:
        started = self._stage_start("generate_test_points")
        summary = self.state.requirement_summary
        if summary is None:
            raise RuntimeError("requirement_summary is required before generating test points")
        docs = self._get_ingested_documents()
        # Deprecated fallback: previous local test-point generator lives in Crew internals.
        crew_result = self._run_crew(docs)
        self.state.test_points = crew_result.test_points
        self._save_interim_json("04_test_points", [asdict(tp) for tp in self.state.test_points])
        self._save_state_snapshot("04_test_points")
        self._stage_end("generate_test_points", started, warn_after_s=120)

    # 5) generate_test_cases
    # Input: list[TestPoint]
    # Output: list[TestCase]
    def generate_test_cases(self, regeneration_round: int = 0) -> None:
        started = self._stage_start(f"generate_test_cases(round={regeneration_round})")
        if not self.state.test_points:
            raise RuntimeError("test_points must be generated before test cases")
        docs = self._get_ingested_documents()
        crew_result = self._run_crew(
            docs,
            regeneration_round=regeneration_round,
            force=regeneration_round > 0,
        )
        # When regeneration occurs, refresh all Crew-owned artifacts together.
        self._sync_state_from_crew_result(crew_result)
        self._save_state_snapshot("05_test_cases")
        self._stage_end(
            f"generate_test_cases(round={regeneration_round})",
            started,
            warn_after_s=180,
        )

    # 6) review_test_assets
    # Input: list[TestPoint] + list[TestCase]
    # Output: ReviewResult
    def review_test_assets(self) -> None:
        started = self._stage_start("review_test_assets")
        points = self.state.test_points
        cases = self.state.test_cases
        if not points or not cases:
            raise RuntimeError("test points and test cases are required for review")
        docs = self._get_ingested_documents()
        crew_result = self._run_crew(docs)
        self.state.review_result = crew_result.review_result
        if self.state.review_result is None:
            raise RuntimeError("crew result missing review_result")
        self._save_interim_json("06_review_result", asdict(self.state.review_result))
        self._save_state_snapshot("06_review_result")
        self._stage_end("review_test_assets", started, warn_after_s=120)

    # 7) generate_quality_gates
    # Input: ReviewResult + requirement context
    # Output: EntryExitCriteriaSet
    def generate_quality_gates(self) -> None:
        started = self._stage_start("generate_quality_gates")
        review = self.state.review_result
        if review is None:
            raise RuntimeError("review_result is required before generating quality gates")
        docs = self._get_ingested_documents()
        crew_result = self._run_crew(docs)
        self.state.quality_gates = crew_result.quality_gates
        if self.state.quality_gates is None:
            raise RuntimeError("crew result missing quality_gates")
        self._save_interim_json("07_quality_gates", asdict(self.state.quality_gates))
        self._save_state_snapshot("07_quality_gates")
        self._stage_end("generate_quality_gates", started, warn_after_s=120)

    # 8) human_release_review
    # Input: review_result + quality_gates
    # Output: release_decision
    def human_release_review(self) -> str:
        started = self._stage_start("human_release_review")
        payload = self._human_review_payload(
            stage="human_release_review",
            file_name="release_review.json",
        )
        decision = str(payload.get("decision", "reject")).strip().lower()
        if decision not in {"approve", "rework", "reject"}:
            raise ValueError("release decision must be one of: approve, rework, reject")
        self.state.release_decision = decision
        self._save_interim_json("08_human_release_review", payload)
        self._save_state_snapshot("08_human_release_review")
        self._stage_end("human_release_review", started, warn_after_s=60)
        return decision

    # 9) export_outputs
    # Input: test_points + test_cases + quality_gates
    # Output: export_paths
    def export_outputs(self) -> None:
        started = self._stage_start("export_outputs")
        if self.state.quality_gates is None:
            raise RuntimeError("quality_gates required before export")
        if self.state.requirement_summary is None:
            raise RuntimeError("requirement_summary required before export")

        # Final normalization before export:
        # keep schema shape unchanged while unifying Chinese wording style.
        normalized = normalize_execution_result(
            CrewExecutionResult(
                requirement_summary=self.state.requirement_summary,
                clarification_questions=self.state.clarification_questions,
                test_points=self.state.test_points,
                test_cases=self.state.test_cases,
                review_result=self.state.review_result,
                quality_gates=self.state.quality_gates,
                interim_artifacts={},
            )
        )
        self.state.requirement_summary = normalized.requirement_summary
        self.state.clarification_questions = normalized.clarification_questions
        self.state.test_points = normalized.test_points
        self.state.test_cases = normalized.test_cases
        self.state.review_result = normalized.review_result
        self.state.quality_gates = normalized.quality_gates

        self.outputs_final_dir.mkdir(parents=True, exist_ok=True)

        csv_started = self._stage_start("export_outputs.csv")
        csv_paths = export_mvp_csv_bundle(
            test_points=self.state.test_points,
            test_cases=self.state.test_cases,
            gate_criteria=self.state.quality_gates.entry_criteria + self.state.quality_gates.exit_criteria,
            output_dir=self.outputs_final_dir,
            prefix="testcase_mvp",
        )
        self._stage_end("export_outputs.csv", csv_started, warn_after_s=20)
        export_paths = {k: str(v) for k, v in csv_paths.items()}

        excel_path = self.outputs_final_dir / "testcase_mvp.xlsx"
        excel_started = self._stage_start("export_outputs.excel")
        try:
            path = export_mvp_excel(
                test_points=self.state.test_points,
                test_cases=self.state.test_cases,
                gate_criteria=self.state.quality_gates.entry_criteria + self.state.quality_gates.exit_criteria,
                output_path=excel_path,
            )
            export_paths["excel"] = str(path)
        except ImportError as exc:
            export_paths["excel_error"] = str(exc)
        self._stage_end("export_outputs.excel", excel_started, warn_after_s=20)

        self.state.export_paths = export_paths
        self._save_state_snapshot("09_export_outputs")
        final_state_path = self.outputs_final_dir / "flow_state.json"
        write_started = self._stage_start("export_outputs.final_state_write")
        final_state_path.write_text(json.dumps(self._serialize_state(), ensure_ascii=False, indent=2), encoding="utf-8")
        self._stage_end("export_outputs.final_state_write", write_started, warn_after_s=10)
        self._stage_end("export_outputs", started, warn_after_s=20)

    def kickoff(
        self,
        input_files: list[str] | None = None,
        max_requirement_loops: int = 2,
        max_rework_loops: int = 2,
    ) -> TestcaseGenerationState:
        """Run the full MVP flow with loopbacks at review checkpoints."""
        flow_started = self._stage_start("flow.kickoff")
        self._ensure_dirs()
        self.state = TestcaseGenerationState(
            input_files=input_files or ["examples/sample_prd.md"]
        )
        self._documents_cache = None
        self._crew_result_cache = None
        self._crew_kickoff_count = 0
        self._rerun_required_after_review = False

        requirement_attempt = 0
        while requirement_attempt < max_requirement_loops:
            requirement_attempt += 1
            print(
                f"{datetime.now().isoformat(timespec='seconds')} [FLOW] requirement_loop: {requirement_attempt}/{max_requirement_loops}",
                flush=True,
            )
            docs = self._get_ingested_documents()
            self.analyze_requirements(docs)
            if self.human_review_requirements():
                break
        else:
            self.state.release_decision = "reject"
            print(
                f"{datetime.now().isoformat(timespec='seconds')} [FLOW] kickoff_count={self._crew_kickoff_count} "
                "(result=rejected_before_generation)",
                flush=True,
            )
            self._stage_end("flow.kickoff", flow_started, warn_after_s=300)
            return self.state

        self.generate_test_points()

        regeneration_round = 0
        while True:
            print(
                f"{datetime.now().isoformat(timespec='seconds')} [FLOW] testcase_regeneration_round: {regeneration_round}",
                flush=True,
            )
            self.generate_test_cases(regeneration_round=regeneration_round)
            self.review_test_assets()
            if self.state.review_result and self.state.review_result.overall_status == "pass":
                break
            regeneration_round += 1
            if regeneration_round > max_rework_loops:
                self.state.release_decision = "reject"
                print(
                    f"{datetime.now().isoformat(timespec='seconds')} [FLOW] kickoff_count={self._crew_kickoff_count} "
                    "(result=rejected_after_rework_limit)",
                    flush=True,
                )
                self._stage_end("flow.kickoff", flow_started, warn_after_s=300)
                return self.state

        self.generate_quality_gates()

        release_round = 0
        while release_round <= max_rework_loops:
            print(
                f"{datetime.now().isoformat(timespec='seconds')} [FLOW] release_review_round: {release_round}",
                flush=True,
            )
            decision = self.human_release_review()
            if decision == "approve":
                self.export_outputs()
                mode_label = "single_kickoff" if self._crew_kickoff_count == 1 else "double_or_more_kickoff"
                print(
                    f"{datetime.now().isoformat(timespec='seconds')} [FLOW] kickoff_count={self._crew_kickoff_count} "
                    f"(run_mode={mode_label}, rerun_required_after_review={self._rerun_required_after_review})",
                    flush=True,
                )
                self._stage_end("flow.kickoff", flow_started, warn_after_s=300)
                return self.state
            if decision == "reject":
                self.state.release_decision = "reject"
                mode_label = "single_kickoff" if self._crew_kickoff_count == 1 else "double_or_more_kickoff"
                print(
                    f"{datetime.now().isoformat(timespec='seconds')} [FLOW] kickoff_count={self._crew_kickoff_count} "
                    f"(run_mode={mode_label}, rerun_required_after_review={self._rerun_required_after_review})",
                    flush=True,
                )
                self._stage_end("flow.kickoff", flow_started, warn_after_s=300)
                return self.state

            # decision == rework: return to testcase generation stage.
            release_round += 1
            regeneration_round += 1
            self.generate_test_cases(regeneration_round=regeneration_round)
            self.review_test_assets()
            self.generate_quality_gates()

        self.state.release_decision = "reject"
        mode_label = "single_kickoff" if self._crew_kickoff_count == 1 else "double_or_more_kickoff"
        print(
            f"{datetime.now().isoformat(timespec='seconds')} [FLOW] kickoff_count={self._crew_kickoff_count} "
            f"(run_mode={mode_label}, rerun_required_after_review={self._rerun_required_after_review})",
            flush=True,
        )
        self._stage_end("flow.kickoff", flow_started, warn_after_s=300)
        return self.state
