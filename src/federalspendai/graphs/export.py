"""Graph export for external systems and Cognitive Substrate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from federalspendai.graphs.builder import graph_summary


def export_graph_json(graph: nx.DiGraph) -> dict[str, Any]:
    nodes = [{"id": node, "label": node} for node in graph.nodes]
    edges = []
    for source, target, data in graph.edges(data=True):
        edges.append(
            {
                "source": source,
                "target": target,
                "total_amount": data.get("total_amount", 0),
                "contracts": data.get("contracts", []),
            }
        )
    return {"nodes": nodes, "edges": edges, "summary": graph_summary(graph)}


def export_graph_graphml(graph: nx.DiGraph, path: Path) -> str:
    # NetworkX graphml doesn't support list edge attrs; stringify contracts
    export_graph = nx.DiGraph()
    for node in graph.nodes:
        export_graph.add_node(node)
    for u, v, data in graph.edges(data=True):
        export_graph.add_edge(
            u,
            v,
            total_amount=data.get("total_amount", 0),
            contract_count=len(data.get("contracts", [])),
            contracts_json=json.dumps(data.get("contracts", [])),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(export_graph, path)
    return str(path)
