"""Event emitter for Cognitive Substrate integration."""

from __future__ import annotations

import json
import os
from typing import Any

from federalspendai.config import Settings, get_settings
from federalspendai.substrate.schemas import SubstrateEvent


def emit_event(event_type: str, payload: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    """Emit a structured event to file, stdout, or webhook."""
    settings = settings or get_settings()
    event = SubstrateEvent(event_type=event_type, payload=payload)
    data = event.model_dump()

    event_dir = settings.data_dir / "events"
    event_dir.mkdir(parents=True, exist_ok=True)
    event_file = event_dir / f"{event.timestamp.replace(':', '-')}_{event_type}.json"
    event_file.write_text(json.dumps(data, indent=2, default=str))

    webhook = os.environ.get("FEDERALSPEND_SUBSTRATE_EVENT_URL")
    if webhook:
        try:
            import httpx

            httpx.post(webhook, json=data, timeout=10.0)
        except Exception:
            pass

    return event


def emit_flow_graph_exported(export_payload: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    return emit_event("FlowGraphExported", export_payload, settings=settings)


def emit_anomaly_flagged(anomaly: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    return emit_event("AnomalyFlagged", anomaly, settings=settings)


def emit_embedding_indexed(summary: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    return emit_event("EmbeddingIndexed", summary, settings=settings)


def emit_ingest_completed(result: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    return emit_event("IngestCompleted", result, settings=settings)


def emit_engine_cycle_completed(summary: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    return emit_event("EngineCycleCompleted", summary, settings=settings)
