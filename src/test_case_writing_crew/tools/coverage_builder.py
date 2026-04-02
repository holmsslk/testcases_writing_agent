"""Coverage matrix builder for requirement -> test point -> test case mapping."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from test_case_writing_crew.schemas import CoverageMatrixItem, TestCase, TestPoint


def _safe_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _parse_requirement_records(
    requirements: Sequence[Mapping[str, Any]] | None,
) -> dict[str, str]:
    """Parse requirement records into id -> description map."""
    result: dict[str, str] = {}
    if not requirements:
        return result

    for idx, item in enumerate(requirements):
        requirement_id = _safe_str(item.get("requirement_id", ""), f"requirements[{idx}].requirement_id")
        requirement_desc = _safe_str(
            item.get("requirement_desc", "No requirement description provided."),
            f"requirements[{idx}].requirement_desc",
        )
        result[requirement_id] = requirement_desc
    return result


def _status_for_links(test_points: list[str], test_cases: list[str]) -> str:
    if test_points and test_cases:
        return "covered"
    if test_points and not test_cases:
        return "partial"
    return "not_covered"


def build_coverage_matrix(
    test_points: Sequence[TestPoint],
    test_cases: Sequence[TestCase],
    requirements: Sequence[Mapping[str, Any]] | None = None,
) -> list[CoverageMatrixItem]:
    """Build coverage matrix from requirement/test-point/test-case relationships."""
    if not isinstance(test_points, Sequence):
        raise TypeError("test_points must be a sequence of TestPoint")
    if not isinstance(test_cases, Sequence):
        raise TypeError("test_cases must be a sequence of TestCase")

    req_desc_map = _parse_requirement_records(requirements)
    tp_by_req: dict[str, list[str]] = defaultdict(list)
    tc_by_req: dict[str, list[str]] = defaultdict(list)

    for tp in test_points:
        if not isinstance(tp, TestPoint):
            raise TypeError("all test_points items must be TestPoint")
        tp_by_req[tp.requirement_id].append(tp.test_point_id)
        req_desc_map.setdefault(tp.requirement_id, f"Inferred from test point {tp.test_point_id}")

    for tc in test_cases:
        if not isinstance(tc, TestCase):
            raise TypeError("all test_cases items must be TestCase")
        tc_by_req[tc.requirement_id].append(tc.case_id)
        req_desc_map.setdefault(tc.requirement_id, f"Inferred from test case {tc.case_id}")

    requirement_ids = sorted(set(req_desc_map.keys()) | set(tp_by_req.keys()) | set(tc_by_req.keys()))
    matrix: list[CoverageMatrixItem] = []
    for requirement_id in requirement_ids:
        linked_test_points = sorted(set(tp_by_req.get(requirement_id, [])))
        linked_test_cases = sorted(set(tc_by_req.get(requirement_id, [])))
        coverage_status = _status_for_links(linked_test_points, linked_test_cases)
        matrix.append(
            CoverageMatrixItem(
                requirement_id=requirement_id,
                requirement_desc=req_desc_map.get(
                    requirement_id,
                    "No requirement description provided.",
                ),
                linked_test_points=linked_test_points,
                linked_test_cases=linked_test_cases,
                coverage_status=coverage_status,
            )
        )
    return matrix
