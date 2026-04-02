"""Local knowledge retrieval utilities for MVP.

This module provides:
- loading local knowledge files under a configurable knowledge directory
- category filtering
- simple keyword matching without vector database dependencies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .document_loader import DocumentObject, load_documents

KNOWLEDGE_CATEGORIES = {
    "defect_patterns",
    "testcase_templates",
    "domain_rules",
    "quality_gates",
}

SUPPORTED_KNOWLEDGE_SUFFIXES = {".md", ".markdown", ".txt", ".csv", ".yaml", ".yml", ".json"}


@dataclass
class KnowledgeMatch:
    """Single keyword retrieval hit."""

    category: str
    source_name: str
    matched_keywords: list[str] = field(default_factory=list)
    score: int = 0
    snippet: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _normalize_category(category: str) -> str:
    normalized = category.strip().lower()
    if normalized not in KNOWLEDGE_CATEGORIES:
        raise ValueError(
            f"unsupported category '{category}', allowed: {sorted(KNOWLEDGE_CATEGORIES)}"
        )
    return normalized


def _category_from_path(path: Path, base_dir: Path) -> str:
    """Infer category from immediate child directory or file name fallback."""
    try:
        relative = path.relative_to(base_dir)
    except ValueError:
        relative = path

    parts = relative.parts
    if parts:
        first = parts[0].lower()
        if first in KNOWLEDGE_CATEGORIES:
            return first

    name_lower = path.name.lower()
    for category in KNOWLEDGE_CATEGORIES:
        if category in name_lower:
            return category
    return "domain_rules"


def _iter_knowledge_files(base_dir: Path) -> list[Path]:
    """Collect supported knowledge files recursively."""
    if not base_dir.exists():
        raise FileNotFoundError(f"knowledge directory does not exist: {base_dir}")
    if not base_dir.is_dir():
        raise ValueError(f"knowledge path is not a directory: {base_dir}")

    return sorted(
        p
        for p in base_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_KNOWLEDGE_SUFFIXES
    )


def load_knowledge_documents(
    base_dir: str | Path,
    category: str | None = None,
) -> list[DocumentObject]:
    """Load local knowledge documents with optional category filtering."""
    root = Path(base_dir)
    category_filter = _normalize_category(category) if category else None

    files = _iter_knowledge_files(root)
    if category_filter:
        files = [f for f in files if _category_from_path(f, root) == category_filter]

    documents = load_documents(files)
    for doc, file_path in zip(documents, files):
        doc.metadata["knowledge_category"] = _category_from_path(file_path, root)
    return documents


def _extract_keywords(query: str | Iterable[str]) -> list[str]:
    if isinstance(query, str):
        tokens = [t.strip().lower() for t in query.split() if t.strip()]
    else:
        tokens = [str(t).strip().lower() for t in query if str(t).strip()]
    if not tokens:
        raise ValueError("query keywords must not be empty")
    return tokens


def _build_snippet(content: str, keyword: str, radius: int = 60) -> str:
    idx = content.lower().find(keyword.lower())
    if idx < 0:
        return content[: min(2 * radius, len(content))]
    start = max(0, idx - radius)
    end = min(len(content), idx + len(keyword) + radius)
    return content[start:end].replace("\n", " ").strip()


def retrieve_knowledge(
    query: str | Iterable[str],
    base_dir: str | Path = "knowledge",
    category: str | None = None,
    top_k: int = 10,
) -> list[KnowledgeMatch]:
    """Retrieve local knowledge using simple keyword scoring."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    keywords = _extract_keywords(query)
    documents = load_knowledge_documents(base_dir=base_dir, category=category)
    matches: list[KnowledgeMatch] = []

    for doc in documents:
        lower_content = doc.raw_text.lower()
        matched = [kw for kw in keywords if kw in lower_content]
        if not matched:
            continue
        snippet = _build_snippet(doc.raw_text, matched[0])
        matches.append(
            KnowledgeMatch(
                category=str(doc.metadata.get("knowledge_category", "domain_rules")),
                source_name=doc.source_name,
                matched_keywords=matched,
                score=len(matched),
                snippet=snippet,
                metadata=doc.metadata,
            )
        )

    return sorted(matches, key=lambda x: x.score, reverse=True)[:top_k]
