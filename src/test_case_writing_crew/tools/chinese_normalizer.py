"""Chinese-style wording normalizer for test design artifacts."""

from __future__ import annotations

import copy
import re

from test_case_writing_crew.schemas import (
    CrewExecutionResult,
    ReviewComment,
)

MODULE_CN_MAP = {
    "auth": "权限管理",
    "device": "设备控制",
    "control": "控制管理",
    "telemetry": "通信管理",
    "alert": "告警管理",
    "api": "接口管理",
}

DIMENSION_CN_MAP = {
    "functional": "功能",
    "api": "接口",
    "permission": "权限",
    "boundary": "边界",
    "exception": "异常",
    "compatibility": "兼容",
    "performance": "性能",
    "security": "安全",
    "stability": "稳定",
    "dfx": "DFX",
}

_PROTECTED_PATTERNS = [
    re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+/[^\s]+"),
    re.compile(r"/[A-Za-z0-9_\-/{}/]+"),
    re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b"),
    re.compile(r"\b[a-z]+_[a-z0-9_]+\b"),
]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _is_mostly_ascii(text: str) -> bool:
    clean = _normalize_text(text)
    if not clean:
        return False
    ascii_count = sum(1 for c in clean if ord(c) < 128)
    return ascii_count / max(len(clean), 1) > 0.75


def _has_protected_token(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PROTECTED_PATTERNS)


def _module_label(module: str) -> str:
    m = _normalize_text(module).lower()
    if not m:
        return "通用模块"
    return MODULE_CN_MAP.get(m, module if any("\u4e00" <= c <= "\u9fff" for c in module) else f"{module}")


def _normalize_sentence(text: str) -> str:
    s = _normalize_text(text)
    if not s:
        return s
    if s[-1] not in "。！？":
        s += "。"
    return s


def _rewrite_english_title(title: str) -> str:
    lower = title.lower()
    if "startup" in lower or ("start" in lower and "device" in lower):
        return "验证设备启动成功"
    if "parameter" in lower and ("save" in lower or "saved" in lower):
        return "验证参数可成功保存"
    if "network" in lower and ("reconnect" in lower or "retry" in lower):
        return "验证网络异常后系统能够自动重连"
    if "timeout" in lower:
        return "验证通信超时场景下系统处理行为"
    return "验证功能在指定条件下的表现"


def normalize_test_point_title(title: str, module: str, description: str = "") -> str:
    raw = _normalize_text(title)
    module_label = _module_label(module)
    if not raw:
        raw = _normalize_text(description) or "验证功能在指定条件下的表现"

    if _is_mostly_ascii(raw):
        if _has_protected_token(raw):
            core = f"验证场景行为符合预期（{raw}）"
        else:
            core = _rewrite_english_title(raw)
    else:
        core = re.sub(r"^[【\[].*?[】\]]\s*", "", raw)
        core = re.sub(r"^(测试|用例)\s*", "", core)
        if len(core) <= 4:
            core = f"验证{core}在指定条件下的表现"
        elif not core.startswith("验证"):
            core = f"验证{core}"

    for en, cn in DIMENSION_CN_MAP.items():
        core = re.sub(fr"\b{en}\b", cn, core, flags=re.IGNORECASE)
    core = core.replace("  ", " ").strip("。")
    return f"【{module_label}】{core}"


def normalize_test_case_title(title: str, module: str, test_point_title: str = "") -> str:
    base = _normalize_text(title) or _normalize_text(test_point_title)
    return normalize_test_point_title(base, module, description=test_point_title)


def normalize_test_steps(steps: list[str]) -> list[str]:
    normalized: list[str] = []
    for index, step in enumerate(steps[:6], start=1):
        text = _normalize_text(step)
        text = re.sub(r"^\d+\s*[)\.、）]\s*", "", text)
        text = re.sub(r"^[)\.、）\s]+", "", text)
        if _is_mostly_ascii(text):
            text = f"执行以下操作：{text}"
        elif not re.match(r"^(启动|进入|输入|点击|选择|执行|检查|确认|断开|恢复|观察|记录|调用|发送|接收|校验|设置|查看|提交|等待|重启|登录|退出|准备)", text):
            text = f"执行操作：{text}"
        normalized.append(f"{index}）{text}")
    return normalized


def normalize_expected_result(expected_result: str) -> str:
    text = _normalize_text(expected_result)
    if not text:
        return "系统行为符合预期，并可通过页面状态、设备状态或日志记录进行验证。"

    vague_patterns = {"正常", "成功", "没有问题", "通过", "ok", "OK", "pass"}
    if text in vague_patterns:
        return "系统行为符合预期，并可通过页面状态、设备状态或日志记录进行验证。"

    if _is_mostly_ascii(text) and not _has_protected_token(text):
        text = f"系统返回结果符合预期：{text}"

    observable_keywords = ["提示", "显示", "状态", "日志", "告警", "返回", "错误码", "保存", "记录"]
    if not any(keyword in text for keyword in observable_keywords):
        text = f"{text}，并可通过页面状态、设备状态或日志记录进行验证"
    return _normalize_sentence(text)


def normalize_review_comment(comment: ReviewComment) -> ReviewComment:
    comment.comment = _normalize_sentence(
        _normalize_text(comment.comment).replace("Expected result is empty", "预期结果为空，无法执行判定")
    )
    suggestion = _normalize_text(comment.suggestion)
    if suggestion:
        if _is_mostly_ascii(suggestion) and not _has_protected_token(suggestion):
            suggestion = f"建议：{suggestion}"
        comment.suggestion = _normalize_sentence(suggestion)
    return comment


def normalize_quality_gate_text(text: str) -> str:
    s = _normalize_text(text)
    if not s:
        return s
    if _is_mostly_ascii(s) and not _has_protected_token(s):
        s = f"校验要求：{s}"
    return _normalize_sentence(s)


def normalize_execution_result(result: CrewExecutionResult) -> CrewExecutionResult:
    normalized = copy.deepcopy(result)

    normalized.clarification_questions = normalized.clarification_questions[:8]
    normalized.test_points = normalized.test_points[:20]
    normalized.test_cases = normalized.test_cases[:20]

    for test_point in normalized.test_points:
        test_point.title = normalize_test_point_title(
            title=test_point.title,
            module=test_point.module,
            description=test_point.description,
        )
        test_point.description = normalize_quality_gate_text(test_point.description)
        if test_point.remarks:
            test_point.remarks = normalize_quality_gate_text(test_point.remarks)

    point_title_map = {point.test_point_id: point.title for point in normalized.test_points}
    for case in normalized.test_cases:
        case.title = normalize_test_case_title(
            title=case.title,
            module=case.module,
            test_point_title=point_title_map.get(case.test_point_id, ""),
        )
        case.steps = normalize_test_steps(case.steps)
        case.expected_result = normalize_expected_result(case.expected_result)
        case.preconditions = [normalize_quality_gate_text(item) for item in case.preconditions]
        if case.remarks:
            case.remarks = normalize_quality_gate_text(case.remarks)

    if normalized.review_result is not None:
        normalized.review_result.comments = [
            normalize_review_comment(item) for item in normalized.review_result.comments
        ][:8]
        normalized.review_result.coverage_gaps = [
            normalize_quality_gate_text(item) for item in normalized.review_result.coverage_gaps
        ]

    if normalized.quality_gates is not None:
        normalized.quality_gates.entry_criteria = normalized.quality_gates.entry_criteria[:8]
        normalized.quality_gates.exit_criteria = normalized.quality_gates.exit_criteria[:8]
        for criterion in normalized.quality_gates.entry_criteria + normalized.quality_gates.exit_criteria:
            criterion.description = normalize_quality_gate_text(criterion.description)
            criterion.threshold = _normalize_text(criterion.threshold)
            if criterion.remarks:
                criterion.remarks = normalize_quality_gate_text(criterion.remarks)
        normalized.quality_gates.project_specific_notes = [
            normalize_quality_gate_text(item) for item in normalized.quality_gates.project_specific_notes
        ]

    if normalized.requirement_summary is not None:
        normalized.requirement_summary.scope = [
            normalize_quality_gate_text(item) for item in normalized.requirement_summary.scope
        ]
        normalized.requirement_summary.business_rules = [
            normalize_quality_gate_text(item) for item in normalized.requirement_summary.business_rules
        ]
    return normalized


__all__ = [
    "normalize_test_point_title",
    "normalize_test_case_title",
    "normalize_test_steps",
    "normalize_expected_result",
    "normalize_review_comment",
    "normalize_quality_gate_text",
    "normalize_execution_result",
]
