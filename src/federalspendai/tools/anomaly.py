"""MCP tools for anomaly detection and investigation."""

from __future__ import annotations

from typing import Any

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.analytics.effects import correlate_effects
from federalspendai.analytics.investigation import investigate_anomaly
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
    )
    if emit_events:
        for item in result["department_anomalies"] + result["vendor_anomalies"]:
            emit_anomaly_flagged(item)
    return make_response(result)


def investigate_anomaly_tool(
    anomaly_id: str | None = None,
    department: str | None = None,
    vendor: str | None = None,
) -> dict[str, Any]:
    result = investigate_anomaly(
        anomaly_id=anomaly_id,
        department=department,
        vendor=vendor,
    )
    return make_response(result)


def correlate_effects_tool(
    department: str | None = None,
    vendor: str | None = None,
) -> dict[str, Any]:
    result = correlate_effects(department=department, vendor=vendor)
    return make_response(result)
