"""Event emitter for Cognitive Substrate integration."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

from federalspendai.config import Settings, get_settings
from federalspendai.http_client import default_headers
from federalspendai.substrate.experience import to_experience_event
from federalspendai.substrate.schemas import SubstrateEvent

logger = logging.getLogger(__name__)


def _write_json(path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def _post_webhook(url: str, payload: dict[str, Any]) -> None:
    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=10.0,
            headers=default_headers(),
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Substrate webhook delivery failed: %s", exc)


def emit_event(event_type: str, payload: dict[str, Any], settings: Settings | None = None) -> SubstrateEvent:
    """Emit a structured event to file and optionally to a Cognitive Substrate webhook."""
    settings = settings or get_settings()
    event = SubstrateEvent(event_type=event_type, payload=payload)
    legacy = event.model_dump()
    experience = to_experience_event(
        event_type,
        payload,
        event_id=event.event_id,
        timestamp=event.timestamp,
    ).model_dump()

    event_dir = settings.data_dir / "events"
    safe_ts = event.timestamp.replace(":", "-")
    _write_json(event_dir / f"{safe_ts}_{event_type}.json", legacy)
    _write_json(event_dir / "experience" / f"{safe_ts}_{event_type}.json", experience)

    webhook = os.environ.get("FEDERALSPEND_SUBSTRATE_EVENT_URL")
    if webhook:
        event_format = os.environ.get("FEDERALSPEND_SUBSTRATE_EVENT_FORMAT", "both").lower()
        if event_format in {"legacy", "both"}:
            _post_webhook(webhook, legacy)
        if event_format in {"experience", "both"}:
            _post_webhook(webhook, experience)

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
