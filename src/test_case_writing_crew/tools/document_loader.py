"""Document loading utilities for MVP input ingestion.

Supported file types:
- markdown: .md, .markdown
- text: .txt
- csv: .csv
- yaml: .yaml, .yml
- json: .json
"""

from __future__ import annotations

from dataclasses import dataclass, field
import csv
import json
from pathlib import Path
from typing import Any, Iterable

SUPPORTED_SUFFIXES = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "text",
    ".csv": "csv",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
}


@dataclass
class DocumentObject:
    """Unified in-memory document representation for downstream tools."""

    source_name: str
    source_type: str
    raw_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _read_text(path: Path, encoding: str = "utf-8") -> str:
    """Read UTF-8 text file with fallback errors handling."""
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError as exc:
        raise ValueError(f"failed to decode file as {encoding}: {path}") from exc
    except OSError as exc:
        raise OSError(f"failed to read file: {path}") from exc


def _build_metadata(path: Path, source_type: str, content: str) -> dict[str, Any]:
    """Build lightweight metadata for a loaded document."""
    metadata: dict[str, Any] = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "line_count": len(content.splitlines()),
    }

    if source_type == "csv":
        rows = list(csv.reader(content.splitlines()))
        metadata["row_count"] = max(0, len(rows) - 1 if rows else 0)
        metadata["headers"] = rows[0] if rows else []
    elif source_type == "json":
        try:
            parsed = json.loads(content)
            metadata["json_type"] = type(parsed).__name__
        except json.JSONDecodeError:
            metadata["json_parse_error"] = True
    elif source_type == "yaml":
        metadata["yaml_candidate"] = True

    return metadata


def _load_single_document(path: Path, encoding: str = "utf-8") -> DocumentObject:
    """Load one supported document file into a unified object."""
    if not path.exists():
        raise FileNotFoundError(f"document path does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"document path is not a file: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"unsupported file type: {path}. supported: {sorted(SUPPORTED_SUFFIXES)}"
        )

    source_type = SUPPORTED_SUFFIXES[suffix]
    content = _read_text(path, encoding=encoding)
    metadata = _build_metadata(path, source_type, content)
    return DocumentObject(
        source_name=path.name,
        source_type=source_type,
        raw_text=content,
        metadata=metadata,
    )


def load_documents(paths: Iterable[str | Path], encoding: str = "utf-8") -> list[DocumentObject]:
    """Load multiple files and return a list of unified document objects."""
    documents: list[DocumentObject] = []
    for raw_path in paths:
        path = Path(raw_path)
        documents.append(_load_single_document(path, encoding=encoding))
    return documents
