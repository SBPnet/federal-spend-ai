"""Money-flow graph builder using NetworkX."""

from __future__ import annotations

from typing import Any

import networkx as nx

from federalspendai.data.store import DataStore


def build_money_flow_graph(
    *,
    department: str | None = None,
    vendor: str | None = None,
    min_amount: float | None = None,
    limit: int = 500,
    store: DataStore | None = None,
) -> nx.DiGraph:
    """Build vendor -> department flow graph from contract awards."""
    store = store or DataStore()
    contracts = store.search_contracts(
        department=department,
        vendor=vendor,
        min_amount=min_amount,
        limit=limit,
    )

    graph = nx.DiGraph()
    for row in contracts:
        vend = row.get("vendor") or "Unknown Vendor"
        dept = row.get("department") or "Unknown Department"
        amount = float(row.get("contract_amount") or 0)
        ref = row.get("reference_number")

        if not graph.has_edge(vend, dept):
            graph.add_edge(vend, dept, total_amount=0.0, contracts=[])
        graph[vend][dept]["total_amount"] += amount
        graph[vend][dept]["contracts"].append(ref)

    return graph


def graph_summary(graph: nx.DiGraph) -> dict[str, Any]:
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "top_edges": sorted(
            [
                {
                    "vendor": u,
                    "department": v,
                    "total_amount": data.get("total_amount", 0),
                    "contract_count": len(data.get("contracts", [])),
                }
                for u, v, data in graph.edges(data=True)
            ],
            key=lambda item: item["total_amount"],
            reverse=True,
        )[:20],
    }
