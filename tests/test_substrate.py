"""Tests for Cognitive Substrate event emission."""

import json
from pathlib import Path

from federalspendai.config import Settings
from federalspendai.substrate.events import emit_anomaly_flagged, emit_embedding_indexed


def test_emit_event_writes_file(tmp_path: Path):
    settings = Settings(data_dir=tmp_path)
    event = emit_embedding_indexed({"indexed": 3, "model": "test"}, settings=settings)
    files = list((tmp_path / "events").glob("*.json"))
    assert files
    payload = json.loads(files[0].read_text())
    assert payload["event_type"] == "EmbeddingIndexed"
    assert event.payload["indexed"] == 3


def test_emit_anomaly_event(tmp_path: Path):
    settings = Settings(data_dir=tmp_path)
    event = emit_anomaly_flagged({"anomaly_id": "abc", "z_score": 3.1}, settings=settings)
    assert event.event_type == "AnomalyFlagged"
