"""MCP tools for semantic and hybrid search."""

from __future__ import annotations

from typing import Any

from federalspendai.config import get_settings
from federalspendai.embeddings.hybrid import hybrid_search
from federalspendai.embeddings.index import build_embedding_index, semantic_search
from federalspendai.mcp.envelope import make_error, make_response
from federalspendai.substrate.events import emit_embedding_indexed


def semantic_search_contracts(query: str, limit: int = 20) -> dict[str, Any]:
    if not query.strip():
        return make_error("EMPTY_QUERY", "Provide a non-empty search query.")
    settings = get_settings()
    rows = semantic_search(query, settings=settings, limit=limit)
    return make_response({"query": query, "results": rows, "count": len(rows)})


def hybrid_search_contracts(query: str, limit: int = 20) -> dict[str, Any]:
    if not query.strip():
        return make_error("EMPTY_QUERY", "Provide a non-empty search query.")
    settings = get_settings()
    rows = hybrid_search(query, settings=settings, limit=limit)
    return make_response({"query": query, "results": rows, "count": len(rows)})


def build_embeddings_index(limit: int | None = None, emit_events: bool = False) -> dict[str, Any]:
    settings = get_settings()
    summary = build_embedding_index(settings=settings, limit=limit)
    if emit_events:
        emit_embedding_indexed(summary, settings=settings)
    return make_response(summary)
