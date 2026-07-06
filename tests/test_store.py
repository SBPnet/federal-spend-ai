"""Tests for DuckDB ingest and queries."""

from pathlib import Path

import pytest

from federalspendai.config import Settings
from federalspendai.data.ingest import ingest_dataset
from federalspendai.data.store import DataStore
from federalspendai.tools.search import contract_details, search_contracts
from federalspendai.tools.status import federalspend_status, list_departments
from federalspendai.tools.aggregates import top_vendors, spending_by_department

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def temp_store(tmp_path: Path) -> DataStore:
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "test.duckdb")
    store = DataStore(settings)
    store.init_schema()
    ingest_dataset("awards", settings=settings, fixture_path=FIXTURES / "awards.csv")
    return store


def test_ingest_fixture_loads_rows(temp_store: DataStore):
    counts = temp_store.table_counts()
    assert counts["awards"] >= 1


def test_search_contracts_by_vendor(temp_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.search._store", lambda: temp_store)
    result = search_contracts(vendor="Irving")
    assert result["data"]["count"] >= 1


def test_contract_details(temp_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.search._store", lambda: temp_store)
    rows = temp_store.search_contracts(limit=1)
    ref = rows[0]["reference_number"]
    result = contract_details(reference_number=ref)
    assert result["data"]["reference_number"] == ref


def test_top_vendors(temp_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.aggregates._store", lambda: temp_store)
    result = top_vendors(limit=5)
    assert len(result["data"]["results"]) >= 1


def test_spending_by_department(temp_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.aggregates._store", lambda: temp_store)
    result = spending_by_department(limit=5)
    assert len(result["data"]["results"]) >= 1


def test_list_departments(temp_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.status._store", lambda: temp_store)
    result = list_departments(limit=5)
    assert len(result["data"]["results"]) >= 1


def test_federalspend_status(temp_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.status._store", lambda: temp_store)
    result = federalspend_status()
    assert result["data"]["row_counts"]["awards"] >= 1
