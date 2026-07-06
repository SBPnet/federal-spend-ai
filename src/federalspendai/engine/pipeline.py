"""Ingest → embed → analyze pipeline for the engine."""

from __future__ import annotations

import logging
from typing import Any

from federalspendai.config import Settings, get_settings
from federalspendai.data.ingest import ingest_all
from federalspendai.embeddings.index import build_embedding_index
from federalspendai.substrate.events import (
    emit_anomaly_flagged,
    emit_embedding_indexed,
    emit_engine_cycle_completed,
    emit_ingest_completed,
)
from federalspendai.tools.anomaly import detect_anomalies_tool

logger = logging.getLogger(__name__)


def run_cycle(
    *,
    settings: Settings | None = None,
    incremental: bool = True,
    emit_events: bool = True,
) -> dict[str, Any]:
    """Pull open data, refresh embeddings, and run anomaly analysis."""
    settings = settings or get_settings()
    datasets = settings.engine_datasets_list()

    logger.info("Engine cycle starting for datasets: %s", datasets)
    ingest_results = ingest_all(
        datasets,
        settings=settings,
        incremental=incremental,
    )

    changed_datasets = [item for item in ingest_results if not item.get("skipped")]
    if emit_events:
        for item in ingest_results:
            emit_ingest_completed(item, settings=settings)

    embed_summary = build_embedding_index(
        settings=settings,
        incremental=incremental,
    )
    if emit_events and embed_summary.get("indexed", 0) > 0:
        emit_embedding_indexed(embed_summary, settings=settings)

    anomaly_payload = detect_anomalies_tool(emit_events=emit_events)
    anomaly_data = anomaly_payload.get("data", {})
    if emit_events:
        for anomaly in anomaly_data.get("department_anomalies", []):
            emit_anomaly_flagged(anomaly, settings=settings)
        for anomaly in anomaly_data.get("vendor_anomalies", []):
            emit_anomaly_flagged(anomaly, settings=settings)

    summary = {
        "datasets": datasets,
        "ingest": ingest_results,
        "datasets_changed": len(changed_datasets),
        "embed": embed_summary,
        "anomalies": {
            "total": anomaly_data.get("total", 0),
            "department_count": len(anomaly_data.get("department_anomalies", [])),
            "vendor_count": len(anomaly_data.get("vendor_anomalies", [])),
        },
        "incremental": incremental,
    }

    if emit_events:
        emit_engine_cycle_completed(summary, settings=settings)

    logger.info(
        "Engine cycle finished: changed=%s embedded=%s anomalies=%s",
        len(changed_datasets),
        embed_summary.get("indexed", 0),
        summary["anomalies"]["total"],
    )
    return summary
