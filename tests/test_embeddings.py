"""Tests for embeddings with mocked model."""

from pathlib import Path
from unittest.mock import patch

import numpy as np

from federalspendai.config import Settings
from federalspendai.data.ingest import ingest_dataset
from federalspendai.embeddings.index import build_embedding_index, semantic_search

FIXTURES = Path(__file__).parent / "fixtures"


@patch("federalspendai.embeddings.index.embed_texts")
def test_build_and_search_embeddings(mock_embed, tmp_path: Path):
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "embed.duckdb")
    ingest_dataset("awards", settings=settings, fixture_path=FIXTURES / "awards.csv")

    def fake_embed(texts, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        return np.ones((len(texts), 8), dtype=np.float32)

    mock_embed.side_effect = fake_embed

    summary = build_embedding_index(settings=settings)
    assert summary["indexed"] >= 1

    results = semantic_search("diesel fuel", settings=settings)
    assert len(results) >= 1
    assert "similarity_score" in results[0]
