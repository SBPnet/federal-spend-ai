"""MCP tools for anomaly detection and investigation."""

from __future__ import annotations

from typing import Any

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.analytics.effects import correlate_effects
from federalspendai.analytics.investigation import investigate_anomaly
from federalspendai.config import get_settings
from federalspendai.data.store import DataStore
from federalspendai.mcp.envelope import make_response
from federalspendai.substrate.events import emit_anomaly_flagged


def detect_anomalies_tool(
    department: str | None = None,
    include_vendors: bool = True,
    z_threshold: float = 2.5,
    emit_events: bool = False,
) -> dict[str, Any]:
    result = detect_anomalies(
        department=department,
        include_vendors=include_vendors,
        z_threshold=z_threshold,
        persist=True,
    )
    if emit_events:
        for item in result.get("emitted", []):
            emit_anomaly_flagged(item)
    return make_response(result)


def investigate_anomaly_tool(
    anomaly_id: str | None = None,
    department: str | None = None,
    vendor: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    result = investigate_anomaly(
        anomaly_id=anomaly_id,
        department=department,
        vendor=vendor,
        force=force,
    )
    return make_response(result)


def list_stored_anomalies_tool(
    anomaly_status: str = "open",
    investigation_status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    store = DataStore(get_settings())
    rows = store.list_spending_anomalies(
        anomaly_status=anomaly_status,
        investigation_status=investigation_status,
        limit=limit,
    )
    return make_response({"results": rows, "count": len(rows)})


def correlate_effects_tool(
    department: str | None = None,
    vendor: str | None = None,
) -> dict[str, Any]:
    result = correlate_effects(department=department, vendor=vendor)
    return make_response(result)
