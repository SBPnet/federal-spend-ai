"""MCP tools for money-flow graphs."""

from __future__ import annotations

from typing import Any

from federalspendai.graphs.builder import build_money_flow_graph, graph_summary
from federalspendai.graphs.export import export_graph_json
from federalspendai.graphs.tracer import trace_money_flow
from federalspendai.mcp.envelope import make_error, make_response
from federalspendai.substrate.events import emit_flow_graph_exported


def build_money_flow_graph_tool(
    department: str | None = None,
    vendor: str | None = None,
    min_amount: float | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    graph = build_money_flow_graph(
        department=department,
        vendor=vendor,
        min_amount=min_amount,
        limit=limit,
    )
    return make_response(graph_summary(graph))


def trace_money_flow_tool(
    vendor: str,
    department: str | None = None,
) -> dict[str, Any]:
    if not vendor.strip():
        return make_error("MISSING_VENDOR", "Provide a vendor name to trace.")
    result = trace_money_flow(vendor=vendor, department=department)
    return make_response(result)


def export_graph_tool(
    department: str | None = None,
    vendor: str | None = None,
    emit_events: bool = False,
) -> dict[str, Any]:
    graph = build_money_flow_graph(department=department, vendor=vendor)
    payload = export_graph_json(graph)
    if emit_events:
        emit_flow_graph_exported(payload)
    return make_response(payload)
