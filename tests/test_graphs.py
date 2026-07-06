"""Tests for money-flow graphs."""

from pathlib import Path

import pytest

from federalspendai.config import Settings
from federalspendai.data.ingest import ingest_dataset
from federalspendai.data.store import DataStore
from federalspendai.graphs.builder import build_money_flow_graph, graph_summary
from federalspendai.graphs.export import export_graph_json
from federalspendai.graphs.tracer import trace_money_flow

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def graph_store(tmp_path: Path) -> DataStore:
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "graph.duckdb")
    ingest_dataset("awards", settings=settings, fixture_path=FIXTURES / "awards.csv")
    ingest_dataset("public_accounts", settings=settings, fixture_path=FIXTURES / "public_accounts.csv")
    return DataStore(settings)


def test_build_money_flow_graph(graph_store: DataStore):
    graph = build_money_flow_graph(store=graph_store)
    summary = graph_summary(graph)
    assert summary["node_count"] >= 2
    assert summary["edge_count"] >= 1


def test_trace_money_flow(graph_store: DataStore):
    result = trace_money_flow("Irving Oil", store=graph_store)
    assert result["contract_count"] >= 1
    assert result["vendor"] == "Irving Oil"


def test_export_graph_json(graph_store: DataStore):
    graph = build_money_flow_graph(store=graph_store)
    exported = export_graph_json(graph)
    assert exported["nodes"]
    assert exported["edges"]
