"""Excel exporter for MVP artifacts using openpyxl."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

from test_case_writing_crew.schemas import GateCriterion, TestCase, TestPoint

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - handled by runtime checks
    Workbook = None  # type: ignore[assignment]


def _sheet_from_objects(workbook: Workbook, sheet_name: str, rows: list[dict]) -> None:
    """Create one sheet and write header + rows."""
    ws = workbook.create_sheet(title=sheet_name)
    if not rows:
        ws.append(["note"])
        ws.append(["No data"])
        return

    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([_to_excel_cell(row.get(h, "")) for h in headers])


def _to_excel_cell(value: object) -> object:
    """Convert non-scalar values to strings for openpyxl compatibility."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, dict, tuple, set)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def export_mvp_excel(
    test_points: Iterable[TestPoint],
    test_cases: Iterable[TestCase],
    gate_criteria: Iterable[GateCriterion],
    output_path: str | Path,
) -> Path:
    """Export artifacts to an Excel workbook with three sheets."""
    if Workbook is None:
        raise ImportError(
            "openpyxl is required for Excel export. Install with: uv add openpyxl"
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    # Remove default sheet created by openpyxl for a cleaner workbook.
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    test_point_rows = [asdict(tp) for tp in test_points]
    test_case_rows = [asdict(tc) for tc in test_cases]
    gate_rows = [asdict(gc) for gc in gate_criteria]

    _sheet_from_objects(workbook, "TestPoints", test_point_rows)
    _sheet_from_objects(workbook, "TestCases", test_case_rows)
    _sheet_from_objects(workbook, "QualityGates", gate_rows)

    workbook.save(path)
    return path
