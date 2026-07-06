"""Hybrid keyword + semantic contract search."""

from __future__ import annotations

from typing import Any

from federalspendai.config import Settings, get_settings
from federalspendai.data.store import DataStore
from federalspendai.embeddings.index import DEFAULT_MODEL, semantic_search


def hybrid_search(
    query: str,
    *,
    settings: Settings | None = None,
    limit: int = 20,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> list[dict[str, Any]]:
    """Merge keyword SQL search with embedding similarity scores."""
    settings = settings or get_settings()
    store = DataStore(settings)

    keyword_hits = store.search_contracts(keyword=query, limit=limit * 2)
    keyword_scores = {
        row["reference_number"]: 1.0 - (index / max(len(keyword_hits), 1))
        for index, row in enumerate(keyword_hits)
    }

    semantic_hits = semantic_search(query, settings=settings, model_name=DEFAULT_MODEL, limit=limit * 2)
    semantic_scores = {row["reference_number"]: row.get("similarity_score", 0.0) for row in semantic_hits}

    all_refs = set(keyword_scores) | set(semantic_scores)
    merged: list[dict[str, Any]] = []
    for ref in all_refs:
        kw = keyword_scores.get(ref, 0.0)
        sem = semantic_scores.get(ref, 0.0)
        combined = keyword_weight * kw + semantic_weight * sem
        if combined <= 0:
            continue
        details = store.contract_details(reference_number=ref) or {}
        details["hybrid_score"] = round(combined, 4)
        details["keyword_score"] = round(kw, 4)
        details["semantic_score"] = round(sem, 4)
        merged.append(details)

    merged.sort(key=lambda row: row.get("hybrid_score", 0), reverse=True)
    return merged[:limit]
