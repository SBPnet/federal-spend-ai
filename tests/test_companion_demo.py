"""Tests for the BigPines companion demo."""

from __future__ import annotations

from unittest.mock import patch

from examples.bigpines_companion_demo import OUT_DIR, run_demo


def test_companion_demo_runs_offline():
    with patch("federalspendai.embeddings.index.build_embedding_index") as mock_embed:
        mock_embed.return_value = {"indexed": 7, "skipped": 0, "model": "test-model"}
        summary = run_demo(skip_embed=True)

    assert summary["anomalies_total"] > 0
    assert OUT_DIR.exists()
    assert (OUT_DIR / "summary.json").exists()
    assert (OUT_DIR / "events" / "experience").exists()
