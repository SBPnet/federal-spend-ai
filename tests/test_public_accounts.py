"""Tests for Public Accounts ingest and search."""

from pathlib import Path

import pytest

from federalspendai.config import Settings
from federalspendai.data.ingest import ingest_dataset
from federalspendai.data.store import DataStore
from federalspendai.tools.public_accounts import search_public_accounts

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def pa_store(tmp_path: Path) -> DataStore:
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "pa.duckdb")
    ingest_dataset("awards", settings=settings, fixture_path=FIXTURES / "awards.csv")
    ingest_dataset("public_accounts", settings=settings, fixture_path=FIXTURES / "public_accounts.csv")
    return DataStore(settings)


def test_public_accounts_ingest(pa_store: DataStore):
    counts = pa_store.table_counts()
    assert counts["public_accounts"] >= 3


def test_search_public_accounts(pa_store: DataStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("federalspendai.tools.public_accounts._store", lambda: pa_store)
    result = search_public_accounts(payee="Acme")
    assert result["data"]["count"] >= 1
