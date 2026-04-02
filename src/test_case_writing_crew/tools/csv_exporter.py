"""CSV exporters for MVP artifacts."""

from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from test_case_writing_crew.schemas import GateCriterion, TestCase, TestPoint


def _obj_to_dict(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj):
        return _normalize_row(asdict(obj))
    if isinstance(obj, Mapping):
        return _normalize_row(dict(obj))
    raise TypeError(f"unsupported row object type: {type(obj).__name__}")


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            normalized[key] = value
        elif isinstance(value, (list, dict, tuple, set)):
            normalized[key] = json.dumps(value, ensure_ascii=False)
        else:
            normalized[key] = str(value)
    return normalized


def export_list_to_csv(
    rows: Iterable[object],
    output_path: str | Path,
    field_order: list[str] | None = None,
) -> Path:
    """Export a list of dataclass/mapping rows to one CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    row_dicts = [_obj_to_dict(row) for row in rows]
    if not row_dicts:
        raise ValueError("rows must not be empty")

    headers = field_order or list(row_dicts[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(row_dicts)
    return path


def export_mvp_csv_bundle(
    test_points: Iterable[TestPoint],
    test_cases: Iterable[TestCase],
    gate_criteria: Iterable[GateCriterion],
    output_dir: str | Path,
    prefix: str = "mvp_export",
) -> dict[str, Path]:
    """Export test points, test cases, and quality gates to separate CSV files."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tp_path = export_list_to_csv(test_points, out_dir / f"{prefix}_testpoints.csv")
    tc_path = export_list_to_csv(test_cases, out_dir / f"{prefix}_testcases.csv")
    gate_path = export_list_to_csv(gate_criteria, out_dir / f"{prefix}_qualitygates.csv")
    return {
        "test_points": tp_path,
        "test_cases": tc_path,
        "quality_gates": gate_path,
    }
