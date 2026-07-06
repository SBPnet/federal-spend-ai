"""Tests for anomaly detection."""

from pathlib import Path

import pytest

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.analytics.effects import correlate_effects
from federalspendai.config import Settings
from federalspendai.data.ingest import ingest_dataset
from federalspendai.data.store import DataStore

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def full_store(tmp_path: Path) -> DataStore:
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "full.duckdb")
    ingest_dataset("awards", settings=settings, fixture_path=FIXTURES / "awards.csv")
    ingest_dataset("public_accounts", settings=settings, fixture_path=FIXTURES / "public_accounts.csv")
    return DataStore(settings)


def test_detect_anomalies_runs(full_store: DataStore):
    result = detect_anomalies(store=full_store)
    assert "department_anomalies" in result
    assert "vendor_anomalies" in result


def test_correlate_effects(full_store: DataStore):
    result = correlate_effects(vendor="Acme", store=full_store)
    assert result["contract_count"] >= 1
    assert result["public_accounts_count"] >= 0
