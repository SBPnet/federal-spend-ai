"""Engine scheduler and pipeline tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from federalspendai.config import Settings
from federalspendai.engine.pipeline import run_cycle
from federalspendai.engine.state import read_state
from federalspendai.plugins.registry import ensure_plugins_config, load_plugins


def test_load_default_plugins(tmp_path: Path):
    settings = Settings(data_dir=tmp_path)
    ensure_plugins_config(settings)
    plugins = load_plugins(settings)
    assert len(plugins) == 1
    assert plugins[0].name == "federal-spend-ai"


@patch("federalspendai.engine.pipeline.detect_anomalies_tool")
@patch("federalspendai.engine.pipeline.build_embedding_index")
@patch("federalspendai.engine.pipeline.ingest_all")
def test_run_cycle(mock_ingest, mock_embed, mock_anomaly, tmp_path: Path):
    settings = Settings(data_dir=tmp_path)
    mock_ingest.return_value = [{"dataset": "awards", "rows": 2, "skipped": False}]
    mock_embed.return_value = {"indexed": 2, "skipped": 0, "model": "test-model"}
    mock_anomaly.return_value = {
        "data": {"total": 1, "department_anomalies": [{"id": "a1"}], "vendor_anomalies": []}
    }

    summary = run_cycle(settings=settings, incremental=True, emit_events=True)

    assert summary["datasets_changed"] == 1
    assert summary["embed"]["indexed"] == 2
    assert summary["anomalies"]["total"] == 1
    mock_ingest.assert_called_once()
    mock_embed.assert_called_once()
    assert (tmp_path / "events").exists()


def test_incremental_ingest_skips_unchanged_checksum(tmp_path: Path):
    from federalspendai.data.ingest import ingest_dataset
    from federalspendai.data.store import DataStore

    settings = Settings(data_dir=tmp_path)
    store = DataStore(settings)
    store.record_ingest_run("awards", "https://example.com/awards.csv", "abc123", 10, "success")

    with patch("federalspendai.data.ingest.resolve_csv_urls", return_value=["https://example.com/awards.csv"]), patch(
        "federalspendai.data.ingest.download_file",
        return_value="abc123",
    ), patch("federalspendai.data.ingest.ingest_csv_path") as mock_ingest:
        result = ingest_dataset("awards", settings=settings, incremental=True)

    assert result.get("skipped") is True
    mock_ingest.assert_not_called()
