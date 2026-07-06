"""Embedding index for semantic contract search."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

import numpy as np

from federalspendai.config import Settings, get_settings
from federalspendai.data.store import DataStore

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model(model_name: str = DEFAULT_MODEL):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def contract_text(row: dict[str, Any]) -> str:
    parts = [
        row.get("title_eng"),
        row.get("description_eng"),
        row.get("vendor"),
        row.get("department"),
    ]
    return " ".join(part for part in parts if part)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def embed_texts(texts: list[str], model_name: str = DEFAULT_MODEL) -> np.ndarray:
    model = _load_model(model_name)
    vectors = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)


def build_embedding_index(
    *,
    settings: Settings | None = None,
    model_name: str = DEFAULT_MODEL,
    limit: int | None = None,
    incremental: bool = False,
) -> dict[str, Any]:
    """Embed ingested contracts and store vectors in DuckDB."""
    settings = settings or get_settings()
    store = DataStore(settings)
    rows = store.list_awards_for_embedding(limit=limit)
    if not rows:
        return {"indexed": 0, "skipped": 0, "model": model_name}

    existing_hashes = store.get_embedding_text_hashes(model_name) if incremental else {}
    pending: list[tuple[dict[str, Any], str, str]] = []
    skipped = 0

    for row in rows:
        text = contract_text(row)
        text_hash = _text_hash(text)
        ref = row["reference_number"]
        if incremental and existing_hashes.get(ref) == text_hash:
            skipped += 1
            continue
        pending.append((row, text, text_hash))

    if not pending:
        return {"indexed": 0, "skipped": skipped, "model": model_name}

    texts = [text for _, text, _ in pending]
    vectors = embed_texts(texts, model_name=model_name)
    for (row, text, text_hash), vector in zip(pending, vectors, strict=True):
        store.upsert_embedding(
            row["reference_number"],
            model_name,
            vector.tolist(),
            text_hash,
        )
    return {"indexed": len(pending), "skipped": skipped, "model": model_name}


def semantic_search(
    query: str,
    *,
    settings: Settings | None = None,
    model_name: str = DEFAULT_MODEL,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Cosine similarity search over stored embeddings."""
    settings = settings or get_settings()
    store = DataStore(settings)
    stored = store.get_embeddings(model=model_name)
    if not stored:
        return []

    query_vec = embed_texts([query], model_name=model_name)[0]
    scored: list[tuple[str, float]] = []
    for row in stored:
        vec = np.asarray(row["embedding"], dtype=np.float32)
        score = float(np.dot(query_vec, vec))
        scored.append((row["reference_number"], score))

    scored.sort(key=lambda item: item[1], reverse=True)
    top_refs = [ref for ref, _ in scored[:limit]]
    results: list[dict[str, Any]] = []
    for ref, score in scored[:limit]:
        details = store.contract_details(reference_number=ref) or {}
        details["similarity_score"] = round(score, 4)
        results.append(details)
    if not results and top_refs:
        pass
    return results
