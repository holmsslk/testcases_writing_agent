"""Core Crew for test analysis and testcase design MVP."""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import re
import time
from typing import Any

from test_case_writing_crew.agents import (
    build_quality_gate_specialist,
    build_quality_reviewer,
    build_requirement_analyst,
    build_test_analyst,
    build_testcase_designer,
)
from test_case_writing_crew.tasks import (
    TASK_CHAIN_ORDER,
    get_clarification_task_definition,
    get_export_task_definition,
    get_quality_gate_task_definition,
    get_requirement_analysis_task_definition,
    get_review_task_definition,
    get_test_case_generation_task_definition,
    get_test_point_generation_task_definition,
)
from test_case_writing_crew.schemas import (
    ClarificationQuestion,
    CrewExecutionResult,
    EntryExitCriteriaSet,
    GateCriterion,
    RequirementSummary,
    ReviewComment,
    ReviewResult,
    TestCase,
    TestPoint,
)

try:
    from crewai import Crew, Process, Task
    from crewai.events import BaseEventListener, TaskCompletedEvent, TaskFailedEvent, TaskStartedEvent
    from crewai.project import CrewBase, after_kickoff, agent, before_kickoff, crew, task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


def _ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _stage_start(name: str) -> float:
    started_at = time.monotonic()
    print(f"{_ts()} [STAGE] start: {name}", flush=True)
    return started_at


def _stage_end(name: str, started_at: float, warn_after_s: float | None = None) -> float:
    duration = time.monotonic() - started_at
    print(f"{_ts()} [STAGE] end: {name} (duration={duration:.2f}s)", flush=True)
    if warn_after_s is not None and duration > warn_after_s:
        print(
            f"{_ts()} [WARN] stage_slow: {name} exceeded {warn_after_s:.0f}s "
            f"(actual={duration:.2f}s) ; possible cause: long LLM call or waiting stage.",
            flush=True,
        )
    return duration


_TASK_TIMER_REGISTERED = False


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _interim_dir() -> Path:
    return _project_root() / "outputs" / "interim"


def _final_dir() -> Path:
    return _project_root() / "outputs" / "final"


def _config_dir() -> Path:
    return _project_root() / "src" / "test_case_writing_crew" / "config"


MANDATORY_DIMENSIONS = [
    "functional",
    "api",
    "permission",
    "boundary",
    "exception",
    "compatibility",
    "performance",
    "security",
    "stability",
    "dfx",
]

INTEGRATED_SCENARIOS = [
    "上位机与设备交互",
    "指令下发与回执确认",
    "通信超时与重试",
    "状态同步一致性",
    "断电与重启恢复",
    "升级与回滚",
    "日志、告警与可诊断性",
]


class _StructuredCrewMixin:
    """Structured stage executors reused by Flow to avoid duplicated logic."""

    def execute_requirement_analysis(
        self,
        documents: list[dict[str, Any]],
        clarified_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        merged_text = "\n".join(item.get("raw_text", "") for item in documents)
        first_line = (
            merged_text.splitlines()[0].strip()
            if merged_text.splitlines()
            else "Integrated System"
        )
        product_name = first_line.lstrip("#").strip() or "Integrated System"

        context = clarified_context or {}
        modules = ["auth", "device", "control", "telemetry", "alert"]
        if context.get("modules"):
            modules = [str(x).strip() for x in context["modules"] if str(x).strip()]

        summary = RequirementSummary(
            product_name=product_name,
            version=str(context.get("version", "0.1.0")),
            scope=[
                "用户认证与授权",
                "设备指令控制与遥测",
                "监控与告警流程",
            ],
            out_of_scope=["物理硬件极限压测"],
            modules=modules,
            user_roles=["管理员", "操作员", "维护人员"],
            business_rules=[
                "关键指令必须有回执并记录审计日志",
                "操作权限必须受角色矩阵约束",
            ],
            external_dependencies=["设备固件", "消息中间件", "时钟同步服务"],
            non_functional_requirements=[
                "必须具备通信超时与重试机制",
                "必须保证状态同步一致性",
                "系统需具备断电重启后的恢复能力",
            ],
            risks=[
                "设备通信链路间歇性异常",
                "指令回执与执行状态不一致",
            ],
            assumptions=[
                "测试环境固件版本与目标发布版本一致",
                "可获取可用的回滚安装包",
            ],
        )
        clarification_questions = [
            ClarificationQuestion(
                id="CQ-001",
                category="api",
                question="不同指令类型的超时时间与最大重试次数分别是多少？",
                impact="high",
                required=True,
            ),
            ClarificationQuestion(
                id="CQ-002",
                category="stability",
                question="设备重启后，在接受新指令前必须恢复哪些关键状态字段？",
                impact="high",
                required=True,
            ),
        ]
        return {
            "requirement_summary": summary,
            "clarification_questions": clarification_questions,
        }

    def execute_test_point_generation(
        self,
        requirement_summary: RequirementSummary,
        clarified_context: dict[str, Any] | None = None,
    ) -> list[TestPoint]:
        _ = clarified_context
        test_points: list[TestPoint] = []
        for idx, dimension in enumerate(MANDATORY_DIMENSIONS, start=1):
            scenario = INTEGRATED_SCENARIOS[(idx - 1) % len(INTEGRATED_SCENARIOS)]
            test_points.append(
                TestPoint(
                    test_point_id=f"TP-{idx:03d}",
                    module=requirement_summary.modules[(idx - 1) % len(requirement_summary.modules)],
                    sub_module="core",
                    requirement_id=f"REQ-{idx:03d}",
                    test_dimension=dimension,
                    title=f"【{requirement_summary.modules[(idx - 1) % len(requirement_summary.modules)]}】验证{scenario}场景下的{dimension}能力",
                    description=f"验证{scenario}场景下与{dimension}维度相关的行为是否符合需求与门禁要求。",
                    priority="p1" if dimension in {"functional", "api", "stability"} else "p2",
                    risk_level="high" if dimension in {"security", "stability"} else "medium",
                    dfx_tags=["testability", "diagnosability"] if dimension == "dfx" else [],
                    remarks="由 TestDesignCrew 自动生成",
                )
            )
        return test_points

    def execute_test_case_generation(
        self,
        test_points: list[TestPoint],
        regeneration_round: int = 0,
    ) -> list[TestCase]:
        test_cases: list[TestCase] = []
        for idx, point in enumerate(test_points, start=1):
            test_cases.append(
                TestCase(
                    case_id=f"TC-{idx:03d}-R{regeneration_round}",
                    module=point.module,
                    sub_module=point.sub_module,
                    test_point_id=point.test_point_id,
                    requirement_id=point.requirement_id,
                    title=point.title,
                    preconditions=[
                        "系统已启动并与目标设备建立通信连接",
                        "具备对应权限的测试账号已登录",
                    ],
                    steps=[
                        "1）准备测试环境并设置目标设备初始状态",
                        "2）执行目标操作并采集接口响应与设备遥测数据",
                        "3）校验指令回执、状态同步、日志与告警结果",
                    ],
                    expected_result=(
                        "操作结果、回执状态、设备状态、日志记录与告警行为均符合需求定义。"
                    ),
                    priority=point.priority,
                    case_type=point.test_dimension,
                    automation_candidate=point.test_dimension
                    in {"api", "functional", "stability"},
                    risk_level=point.risk_level,
                    environment="集成测试环境",
                    remarks=f"第 {regeneration_round} 轮生成",
                )
            )
        return test_cases

    def execute_review(
        self,
        test_points: list[TestPoint],
        test_cases: list[TestCase],
    ) -> ReviewResult:
        comments: list[ReviewComment] = []
        duplicates: list[str] = []
        seen_titles: set[str] = set()
        for case in test_cases:
            if case.title in seen_titles:
                duplicates.append(case.case_id)
            seen_titles.add(case.title)
            if not case.expected_result.strip():
                comments.append(
                    ReviewComment(
                        target_type="test_case",
                        target_id=case.case_id,
                        severity="high",
                        comment="预期结果为空，无法用于执行判定。",
                        suggestion="补充可观察、可验证的预期结果。",
                    )
                )

        dim_covered = {p.test_dimension for p in test_points}
        coverage_gaps = [d for d in MANDATORY_DIMENSIONS if d not in dim_covered]
        overall_status = "pass"
        if coverage_gaps or comments or duplicates:
            overall_status = "needs_revision"

        return ReviewResult(
            overall_status=overall_status,
            comments=comments,
            coverage_gaps=coverage_gaps,
            duplicates=duplicates,
            statistics={
                "test_point_count": len(test_points),
                "test_case_count": len(test_cases),
                "duplicate_count": len(duplicates),
                "coverage_gap_count": len(coverage_gaps),
            },
        )

    def execute_quality_gate_generation(
        self,
        review_result: ReviewResult,
    ) -> EntryExitCriteriaSet:
        entry = [
            GateCriterion(
                criterion_id="GC-E-001",
                criterion_type="entry",
                category="functional",
                description="所有高优先级需求均已映射到测试点。",
                threshold="100%",
                mandatory=True,
            ),
            GateCriterion(
                criterion_id="GC-E-002",
                criterion_type="entry",
                category="stability",
                description="通信超时/重试与重启恢复策略已明确并评审通过。",
                threshold="文档化并评审通过",
                mandatory=True,
            ),
        ]
        exit_criteria = [
            GateCriterion(
                criterion_id="GC-X-001",
                criterion_type="exit",
                category="stability",
                description="发布范围内不存在未关闭的严重级别评审问题。",
                threshold="严重问题遗留数=0",
                mandatory=True,
            ),
            GateCriterion(
                criterion_id="GC-X-002",
                criterion_type="exit",
                category="dfx",
                description="日志与告警信息足以支持故障定位与回滚验证。",
                threshold="关键诊断信息完整",
                mandatory=True,
            ),
        ]
        notes = [
            "软硬件一体专项门禁：指令下发与回执一致性",
            "软硬件一体专项门禁：重启后状态同步一致性",
            f"门禁生成时评审状态：{review_result.overall_status}",
        ]
        return EntryExitCriteriaSet(
            entry_criteria=entry,
            exit_criteria=exit_criteria,
            project_specific_notes=notes,
        )

    def _write_stage_markdown(self, file_name: str, title: str, data: Any) -> str:
        """Persist markdown stage artifact while keeping structured output primary."""
        _interim_dir().mkdir(parents=True, exist_ok=True)
        path = _interim_dir() / file_name
        if is_dataclass(data):
            body = json.dumps(asdict(data), ensure_ascii=False, indent=2)
        elif isinstance(data, list):
            body = json.dumps(
                [asdict(item) if is_dataclass(item) else item for item in data],
                ensure_ascii=False,
                indent=2,
            )
        else:
            body = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        content = f"# {title}\n\n```json\n{body}\n```\n"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _write_final_markdown(self, result: CrewExecutionResult) -> str:
        """Persist final markdown summary for compatibility with existing outputs."""
        _final_dir().mkdir(parents=True, exist_ok=True)
        path = _final_dir() / "final_output.md"
        payload = {
            "requirement_summary": asdict(result.requirement_summary),
            "clarification_questions": [asdict(q) for q in result.clarification_questions],
            "test_points_count": len(result.test_points),
            "test_cases_count": len(result.test_cases),
            "review_result": asdict(result.review_result) if result.review_result else None,
            "quality_gates": asdict(result.quality_gates) if result.quality_gates else None,
        }
        path.write_text(
            "# Crew Structured Execution Result\n\n```json\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n```\n",
            encoding="utf-8",
        )
        return str(path)

    def _standardize_from_raw_task_texts(
        self,
        raw_texts: list[str],
        fallback_result: CrewExecutionResult,
    ) -> CrewExecutionResult:
        """Normalize possibly-unstructured task text into structured result.

        MVP strategy:
        - keep schema-safe fallback as source of truth
        - attach raw texts to interim_artifacts for traceability
        - avoid strict JSON dependency from LLM output
        """
        artifacts = dict(fallback_result.interim_artifacts)
        artifacts["raw_task_texts"] = raw_texts
        fallback_result.interim_artifacts = artifacts
        return fallback_result

    def _extract_json_payload(self, text: str) -> Any | None:
        """Best-effort JSON extraction from task output text."""
        candidates: list[str] = []
        stripped = text.strip()
        if stripped:
            candidates.append(stripped)

        fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        candidates.extend(chunk.strip() for chunk in fenced if chunk.strip())

        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            candidates.append(brace_match.group(0).strip())

        list_match = re.search(r"\[[\s\S]*\]", text)
        if list_match:
            candidates.append(list_match.group(0).strip())

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    def _coerce_dataclass(self, cls: Any, payload: Any) -> Any | None:
        if not isinstance(payload, dict):
            return None
        allowed = {item.name for item in fields(cls)}
        data = {key: payload[key] for key in allowed if key in payload}
        if not data:
            return None
        try:
            return cls(**data)
        except Exception:
            return None

    def _coerce_dataclass_list(self, cls: Any, payload: Any) -> list[Any] | None:
        if not isinstance(payload, list):
            return None
        result: list[Any] = []
        for item in payload:
            obj = self._coerce_dataclass(cls, item)
            if obj is not None:
                result.append(obj)
        return result if result else None

    def _fallback_result(self, inputs: dict[str, Any], reason: str) -> CrewExecutionResult:
        logging.warning("TestDesignCrew.run fallback to execute_pipeline_structured: %s", reason)
        fallback = self.execute_pipeline_structured(inputs=inputs)
        fallback.interim_artifacts["fallback_used"] = "execute_pipeline_structured"
        fallback.interim_artifacts["fallback_reason"] = reason
        return fallback

    def parse_kickoff_result_to_execution_result(
        self,
        kickoff_result: Any,
        inputs: dict[str, Any],
    ) -> CrewExecutionResult:
        """Parse CrewAI kickoff output into CrewExecutionResult."""
        tasks_output = getattr(kickoff_result, "tasks_output", []) or []
        task_raw_by_key: dict[str, str] = {}
        raw_task_texts: list[str] = []
        for idx, task_output in enumerate(tasks_output):
            key = TASK_CHAIN_ORDER[idx] if idx < len(TASK_CHAIN_ORDER) else f"task_{idx+1}"
            text = str(getattr(task_output, "raw", str(task_output)))
            task_raw_by_key[key] = text
            raw_task_texts.append(text)

        # Use structured fallback only if kickoff misses critical structured content.
        fallback_cache: CrewExecutionResult | None = None

        def fallback() -> CrewExecutionResult:
            nonlocal fallback_cache
            if fallback_cache is None:
                fallback_cache = self._fallback_result(
                    inputs=inputs,
                    reason="kickoff output could not be fully standardized",
                )
            return fallback_cache

        requirement_summary: RequirementSummary | None = None
        clarification_questions: list[ClarificationQuestion] | None = None
        test_points: list[TestPoint] | None = None
        test_cases: list[TestCase] | None = None
        review_result: ReviewResult | None = None
        quality_gates: EntryExitCriteriaSet | None = None

        req_payload = self._extract_json_payload(task_raw_by_key.get("requirement_analysis_task", ""))
        if isinstance(req_payload, dict):
            requirement_summary = self._coerce_dataclass(
                RequirementSummary,
                req_payload.get("requirement_summary", req_payload),
            )
            clarification_questions = self._coerce_dataclass_list(
                ClarificationQuestion,
                req_payload.get("clarification_questions", []),
            )

        clar_payload = self._extract_json_payload(task_raw_by_key.get("clarification_task", ""))
        if clarification_questions is None:
            if isinstance(clar_payload, dict):
                clarification_questions = self._coerce_dataclass_list(
                    ClarificationQuestion,
                    clar_payload.get("clarification_questions", []),
                )
            else:
                clarification_questions = self._coerce_dataclass_list(
                    ClarificationQuestion,
                    clar_payload,
                )

        points_payload = self._extract_json_payload(task_raw_by_key.get("test_point_generation_task", ""))
        test_points = self._coerce_dataclass_list(
            TestPoint,
            points_payload.get("test_points", points_payload)
            if isinstance(points_payload, dict)
            else points_payload,
        )

        cases_payload = self._extract_json_payload(task_raw_by_key.get("test_case_generation_task", ""))
        test_cases = self._coerce_dataclass_list(
            TestCase,
            cases_payload.get("test_cases", cases_payload)
            if isinstance(cases_payload, dict)
            else cases_payload,
        )

        review_payload = self._extract_json_payload(task_raw_by_key.get("review_task", ""))
        if isinstance(review_payload, dict):
            review_result = self._coerce_dataclass(
                ReviewResult,
                review_payload.get("review_result", review_payload),
            )

        gate_payload = self._extract_json_payload(task_raw_by_key.get("quality_gate_task", ""))
        if isinstance(gate_payload, dict):
            quality_gates = self._coerce_dataclass(
                EntryExitCriteriaSet,
                gate_payload.get("quality_gates", gate_payload),
            )

        if requirement_summary is None:
            requirement_summary = fallback().requirement_summary
        if clarification_questions is None:
            clarification_questions = fallback().clarification_questions
        if test_points is None:
            test_points = fallback().test_points
        if test_cases is None:
            test_cases = fallback().test_cases
        if review_result is None:
            review_result = fallback().review_result
        if quality_gates is None:
            quality_gates = fallback().quality_gates

        interim_artifacts: dict[str, Any] = {}
        for idx, task_key in enumerate(TASK_CHAIN_ORDER, start=1):
            md_path = _interim_dir() / f"{idx:02d}_{task_key}.md"
            if md_path.exists():
                interim_artifacts[task_key] = str(md_path)
        final_md = _final_dir() / "final_output.md"
        if final_md.exists():
            interim_artifacts["final_output"] = str(final_md)
        interim_artifacts["raw_task_texts"] = raw_task_texts

        result = CrewExecutionResult(
            requirement_summary=requirement_summary,
            clarification_questions=clarification_questions,
            test_points=test_points,
            test_cases=test_cases,
            review_result=review_result,
            quality_gates=quality_gates,
            interim_artifacts=interim_artifacts,
        )
        if fallback_cache is not None:
            result.interim_artifacts["fallback_used"] = "execute_pipeline_structured"
            result.interim_artifacts["fallback_reason"] = (
                "partial kickoff parse; merged with structured fallback"
            )
        return result

    def execute_pipeline_structured(self, inputs: dict[str, Any]) -> CrewExecutionResult:
        """Run structured multi-stage execution and return unified result object."""
        documents = list(inputs.get("documents", []))
        clarified_context = dict(inputs.get("clarified_context", {}))

        requirement_pack = self.execute_requirement_analysis(
            documents=documents,
            clarified_context=clarified_context,
        )
        requirement_summary = requirement_pack["requirement_summary"]
        clarification_questions = requirement_pack["clarification_questions"]
        test_points = self.execute_test_point_generation(
            requirement_summary=requirement_summary,
            clarified_context=clarified_context,
        )
        test_cases = self.execute_test_case_generation(test_points=test_points, regeneration_round=0)
        review_result = self.execute_review(test_points=test_points, test_cases=test_cases)
        quality_gates = self.execute_quality_gate_generation(review_result=review_result)

        interim_artifacts = {
            "requirement_analysis_task": self._write_stage_markdown(
                "01_requirement_analysis_task.md",
                "Requirement Analysis",
                {
                    "requirement_summary": asdict(requirement_summary),
                    "clarification_questions": [asdict(q) for q in clarification_questions],
                },
            ),
            "test_point_generation_task": self._write_stage_markdown(
                "03_test_point_generation_task.md",
                "Test Point Generation",
                test_points,
            ),
            "test_case_generation_task": self._write_stage_markdown(
                "04_test_case_generation_task.md",
                "Test Case Generation",
                test_cases,
            ),
            "review_task": self._write_stage_markdown(
                "05_review_task.md",
                "Review Result",
                review_result,
            ),
            "quality_gate_task": self._write_stage_markdown(
                "06_quality_gate_task.md",
                "Quality Gates",
                quality_gates,
            ),
        }

        result = CrewExecutionResult(
            requirement_summary=requirement_summary,
            clarification_questions=clarification_questions,
            test_points=test_points,
            test_cases=test_cases,
            review_result=review_result,
            quality_gates=quality_gates,
            interim_artifacts=interim_artifacts,
        )
        result.interim_artifacts["final_output"] = self._write_final_markdown(result)
        return result


if CREWAI_AVAILABLE:
    class _CrewTaskTimingListener(BaseEventListener):
        """Per-task timing diagnostics for Crew execution."""

        def __init__(self) -> None:
            self._task_started: dict[str, float] = {}
            super().__init__()

        def setup_listeners(self, crewai_event_bus) -> None:
            def _task_label(event: Any) -> str:
                if getattr(event, "task_name", None):
                    return str(event.task_name)
                task_obj = getattr(event, "task", None)
                if task_obj is not None and getattr(task_obj, "name", None):
                    return str(task_obj.name)
                if task_obj is not None and getattr(task_obj, "description", None):
                    first_line = str(task_obj.description).strip().splitlines()[0]
                    return first_line[:80]
                if getattr(event, "task_id", None):
                    return str(event.task_id)
                return "unknown_task"

            @crewai_event_bus.on(TaskStartedEvent)
            def _on_task_started(source, event: TaskStartedEvent) -> None:
                key = event.task_id or event.task_name or "unknown_task"
                self._task_started[key] = time.monotonic()
                task_label = _task_label(event)
                print(
                    f"{_ts()} [TASK] start: {task_label} "
                    f"(task_id={event.task_id or 'n/a'})",
                    flush=True,
                )

            @crewai_event_bus.on(TaskCompletedEvent)
            def _on_task_completed(source, event: TaskCompletedEvent) -> None:
                key = event.task_id or event.task_name or "unknown_task"
                task_label = _task_label(event)
                started_at = self._task_started.pop(key, None)
                if started_at is None:
                    print(
                        f"{_ts()} [TASK] end: {task_label} "
                        f"(task_id={event.task_id or 'n/a'}, duration=unknown)",
                        flush=True,
                    )
                    return

                duration = time.monotonic() - started_at
                print(
                    f"{_ts()} [TASK] end: {task_label} "
                    f"(task_id={event.task_id or 'n/a'}, duration={duration:.2f}s)",
                    flush=True,
                )
                if duration > 60:
                    print(
                        f"{_ts()} [WARN] task_slow: {task_label} exceeded 60s "
                        f"(actual={duration:.2f}s) ; possible cause: long LLM generation.",
                        flush=True,
                    )

            @crewai_event_bus.on(TaskFailedEvent)
            def _on_task_failed(source, event: TaskFailedEvent) -> None:
                key = event.task_id or event.task_name or "unknown_task"
                task_label = _task_label(event)
                started_at = self._task_started.pop(key, None)
                duration_text = (
                    "unknown" if started_at is None else f"{(time.monotonic() - started_at):.2f}s"
                )
                print(
                    f"{_ts()} [TASK] fail: {task_label} "
                    f"(task_id={event.task_id or 'n/a'}, duration={duration_text}, error={event.error})",
                    flush=True,
                )

    if not _TASK_TIMER_REGISTERED:
        _CrewTaskTimingListener()
        _TASK_TIMER_REGISTERED = True

    @CrewBase
    class TestDesignCrew(_StructuredCrewMixin):
        """MVP crew that performs requirement->case->review->gate->export chain."""

        agents_config = str(_config_dir() / "agents.yaml")
        tasks_config = str(_config_dir() / "tasks.yaml")
        agents_config_path = str(_config_dir() / "agents.yaml")
        tasks_config_path = str(_config_dir() / "tasks.yaml")

        def _build_task(
            self,
            definition,
            assigned_agent: Any,
            output_path: Path | None = None,
            context_tasks: list[Any] | None = None,
        ) -> Task:
            kwargs: dict[str, Any] = {
                "description": (
                    f"{definition.description}\n\n"
                    f"Input context sources: {', '.join(definition.context_sources) or 'none'}"
                ),
                "expected_output": definition.expected_output,
                "agent": assigned_agent,
            }
            if output_path is not None:
                kwargs["output_file"] = str(output_path)
            if context_tasks:
                kwargs["context"] = context_tasks
            return Task(**kwargs)

        @before_kickoff
        def _prepare_io(self, inputs: dict[str, Any]) -> dict[str, Any]:
            """Create output folders and persist kickoff inputs."""
            interim = _interim_dir()
            final = _final_dir()
            interim.mkdir(parents=True, exist_ok=True)
            final.mkdir(parents=True, exist_ok=True)
            (interim / "input_payload.json").write_text(
                json.dumps(inputs, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return inputs

        @after_kickoff
        def _persist_outputs(self, result: Any) -> Any:
            """Persist per-task and final outputs for easy inspection."""
            interim = _interim_dir()
            final = _final_dir()
            interim.mkdir(parents=True, exist_ok=True)
            final.mkdir(parents=True, exist_ok=True)

            tasks_output = getattr(result, "tasks_output", []) or []
            for idx, task_output in enumerate(tasks_output):
                task_key = TASK_CHAIN_ORDER[idx] if idx < len(TASK_CHAIN_ORDER) else f"task_{idx+1}"
                output_path = interim / f"{idx+1:02d}_{task_key}.md"
                text = getattr(task_output, "raw", None)
                if text is None:
                    if is_dataclass(task_output):
                        text = json.dumps(asdict(task_output), ensure_ascii=False, indent=2)
                    else:
                        text = str(task_output)
                output_path.write_text(str(text), encoding="utf-8")

            final_text = getattr(result, "raw", None)
            if final_text is None:
                final_text = str(result)
            (final / "final_output.md").write_text(str(final_text), encoding="utf-8")
            return result

        @agent
        def requirement_analyst(self):
            return build_requirement_analyst(config_path=self.agents_config_path)

        @agent
        def test_analyst(self):
            return build_test_analyst(config_path=self.agents_config_path)

        @agent
        def testcase_designer(self):
            return build_testcase_designer(config_path=self.agents_config_path)

        @agent
        def quality_reviewer(self):
            return build_quality_reviewer(config_path=self.agents_config_path)

        @agent
        def quality_gate_specialist(self):
            return build_quality_gate_specialist(config_path=self.agents_config_path)

        @task
        def requirement_analysis_task(self):
            definition = get_requirement_analysis_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.requirement_analyst(),
                _interim_dir() / "01_requirement_analysis_task.md",
            )

        @task
        def clarification_task(self):
            definition = get_clarification_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.requirement_analyst(),
                _interim_dir() / "02_clarification_task.md",
                [self.requirement_analysis_task()],
            )

        @task
        def test_point_generation_task(self):
            definition = get_test_point_generation_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.test_analyst(),
                _interim_dir() / "03_test_point_generation_task.md",
                [self.clarification_task()],
            )

        @task
        def test_case_generation_task(self):
            definition = get_test_case_generation_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.testcase_designer(),
                _interim_dir() / "04_test_case_generation_task.md",
                [self.test_point_generation_task()],
            )

        @task
        def review_task(self):
            definition = get_review_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.quality_reviewer(),
                _interim_dir() / "05_review_task.md",
                [self.test_case_generation_task()],
            )

        @task
        def quality_gate_task(self):
            definition = get_quality_gate_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.quality_gate_specialist(),
                _interim_dir() / "06_quality_gate_task.md",
                [self.review_task()],
            )

        @task
        def export_task(self):
            definition = get_export_task_definition(config_path=self.tasks_config_path)
            return self._build_task(
                definition,
                self.testcase_designer(),
                _final_dir() / "07_export_task.md",
                [self.quality_gate_task()],
            )

        @crew
        def crew(self) -> Crew:
            """Create the core MVP crew.

            We use Process.sequential because this MVP has strict upstream/downstream
            dependency between tasks and prioritizes deterministic traceability.
            """

            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
            )

        def run(self, inputs: dict[str, Any]):
            """Primary execution entrance: CrewAI kickoff -> standardization -> structured result."""
            run_started = _stage_start("crew.run")
            try:
                kickoff_started = _stage_start("crew.kickoff")
                kickoff_result = self.crew().kickoff(inputs=inputs)
                _stage_end("crew.kickoff", kickoff_started, warn_after_s=180)
            except Exception as exc:
                _stage_end("crew.run", run_started, warn_after_s=180)
                return self._fallback_result(inputs=inputs, reason=f"kickoff failed: {exc}")
            try:
                standardize_started = _stage_start("kickoff.standardize")
                result = self.parse_kickoff_result_to_execution_result(
                    kickoff_result=kickoff_result,
                    inputs=inputs,
                )
                _stage_end("kickoff.standardize", standardize_started, warn_after_s=30)
                _stage_end("crew.run", run_started, warn_after_s=180)
                return result
            except Exception as exc:
                _stage_end("crew.run", run_started, warn_after_s=180)
                return self._fallback_result(inputs=inputs, reason=f"standardization failed: {exc}")

        def run_text(self, inputs: dict[str, Any]):
            """Optional legacy execution preserving CrewAI text-first output."""
            return self.crew().kickoff(inputs=inputs)

        def run_with_standardization(self, inputs: dict[str, Any]) -> CrewExecutionResult:
            """Compatibility alias of structured run (kickoff-driven)."""
            return self.run(inputs=inputs)

else:

    class TestDesignCrew(_StructuredCrewMixin):  # pragma: no cover - only used when crewai missing
        """Fallback class when crewai is unavailable in current Python environment."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            _ = args, kwargs

        def crew(self):
            raise ImportError("crewai is not installed in this Python runtime.")

        def run(self, inputs: dict[str, Any]):
            """Structured run remains available without crewai dependency."""
            return self.execute_pipeline_structured(inputs=inputs)

        def run_text(self, inputs: dict[str, Any]):
            raise ImportError("crewai is not installed in this Python runtime.")

        def run_with_standardization(self, inputs: dict[str, Any]) -> CrewExecutionResult:
            return self.run(inputs=inputs)
