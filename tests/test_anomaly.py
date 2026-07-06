"""Tests for anomaly detection and persistence."""

from pathlib import Path
from unittest.mock import patch

import pytest

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.analytics.anomaly_store import stable_anomaly_id
from federalspendai.analytics.effects import correlate_effects
from federalspendai.analytics.investigation import investigate_anomaly
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
    assert "sync" in result


def test_stable_anomaly_id_is_deterministic():
    first = stable_anomaly_id(
        "vendor_monthly_spike",
        vendor="Acme Corp",
        month="2024-01",
    )
    second = stable_anomaly_id(
        "vendor_monthly_spike",
        vendor="Acme Corp",
        month="2024-01",
    )
    assert first == second


def test_detect_anomalies_persists_stable_ids(full_store: DataStore):
    first = detect_anomalies(store=full_store, persist=True)
    if first["total"] == 0:
        pytest.skip("fixture data produced no anomalies")

    anomaly_id = first["vendor_anomalies"][0]["anomaly_id"]
    second = detect_anomalies(store=full_store, persist=True)
    same = next(row for row in second["vendor_anomalies"] if row["anomaly_id"] == anomaly_id)
    assert same["anomaly_id"] == anomaly_id
    assert second["sync"]["unchanged"] >= 1


@patch("federalspendai.analytics.investigation.analyze_contract")
def test_investigation_is_cached_without_new_evidence(mock_analyze, full_store: DataStore):
    mock_analyze.return_value = type(
        "Result",
        (),
        {"model_dump": lambda self: {"summary": "cached"}},
    )()
    detected = detect_anomalies(store=full_store, persist=True)
    if detected["total"] == 0:
        pytest.skip("fixture data produced no anomalies")

    target = detected["vendor_anomalies"][0]
    first = investigate_anomaly(anomaly_id=target["anomaly_id"], store=full_store)
    second = investigate_anomaly(anomaly_id=target["anomaly_id"], store=full_store)

    assert first["status"] == "ok"
    assert second["status"] == "cached"
    assert mock_analyze.call_count == len(target.get("sample_contracts", []))


@patch("federalspendai.analytics.investigation.analyze_contract")
def test_investigation_reruns_when_marked_stale(mock_analyze, full_store: DataStore):
    mock_analyze.return_value = type(
        "Result",
        (),
        {"model_dump": lambda self: {"summary": "fresh"}},
    )()
    detected = detect_anomalies(store=full_store, persist=True)
    if detected["total"] == 0:
        pytest.skip("fixture data produced no anomalies")

    target = detected["vendor_anomalies"][0]
    investigate_anomaly(anomaly_id=target["anomaly_id"], store=full_store)
    full_store.upsert_spending_anomaly(
        {
            **target,
            "observed_amount": float(target["observed_amount"]) * 2,
            "z_score": float(target["z_score"]) + 1,
        },
        "changed-fingerprint",
    )
    rerun = investigate_anomaly(anomaly_id=target["anomaly_id"], store=full_store)
    assert rerun["status"] == "ok"
    assert mock_analyze.call_count >= len(target.get("sample_contracts", []))


def test_correlate_effects(full_store: DataStore):
    result = correlate_effects(vendor="Acme", store=full_store)
    assert result["contract_count"] >= 1
    assert result["public_accounts_count"] >= 0
