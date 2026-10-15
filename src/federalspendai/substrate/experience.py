"""Map FederalSpendAI events to Cognitive Substrate ExperienceEvent records."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

EXPERIENCE_EVENT_TYPES: dict[str, str] = {
    "FlowGraphExported": "money_flow_export",
    "AnomalyFlagged": "spending_anomaly",
    "EmbeddingIndexed": "embedding_index",
    "IngestCompleted": "data_ingest",
    "EngineCycleCompleted": "engine_cycle",
}


class ExperienceContext(BaseModel):
    sessionId: str
    traceId: str


class ExperienceInput(BaseModel):
    text: str
    embedding: list[float] = Field(default_factory=list)


class ExperienceInternalState(BaseModel):
    confidence: float = 0.75
    activePlan: str = "Analyze Canadian federal spending signals for publication."


class ExperienceAction(BaseModel):
    tool: str
    reasoning: str


class ExperienceResult(BaseModel):
    output: str
    success: bool = True
    latencyMs: int | None = None


class ExperienceEvaluation(BaseModel):
    rewardScore: float = 0.7
    selfAssessedQuality: float = 0.7


class ExperienceEvent(BaseModel):
    """Cognitive Substrate experience.raw compatible event."""

    eventId: str
    timestamp: str
    type: str
    context: ExperienceContext
    input: ExperienceInput
    internalState: ExperienceInternalState
    action: ExperienceAction
    result: ExperienceResult
    evaluation: ExperienceEvaluation
    importanceScore: float = 0.0
    tags: list[str] = Field(default_factory=list)
    sourcePayload: dict[str, Any] = Field(default_factory=dict)


def _summary_text(event_type: str, payload: dict[str, Any]) -> str:
    if event_type == "FlowGraphExported":
        summary = payload.get("summary", {})
        return (
            f"Exported money-flow graph with {summary.get('node_count', 0)} nodes "
            f"and {summary.get('edge_count', 0)} edges."
        )
    if event_type == "AnomalyFlagged":
        return (
            f"Spending anomaly flagged for {payload.get('vendor') or payload.get('department')} "
            f"in {payload.get('month')} (z={payload.get('z_score')})."
        )
    if event_type == "EmbeddingIndexed":
        return f"Indexed {payload.get('indexed', 0)} contract embeddings ({payload.get('model')})."
    if event_type == "IngestCompleted":
        return (
            f"Ingested dataset {payload.get('dataset')} with {payload.get('rows', 0)} rows "
            f"from {payload.get('source_url') or payload.get('source')}."
        )
    if event_type == "EngineCycleCompleted":
        anomalies = payload.get("anomalies", {})
        return (
            f"Engine cycle completed: {payload.get('datasets_changed', 0)} datasets changed, "
            f"{anomalies.get('total', 0)} anomalies open."
        )
    return f"FederalSpendAI event: {event_type}"


def _importance_score(event_type: str, payload: dict[str, Any]) -> float:
    if event_type == "AnomalyFlagged":
        z = abs(float(payload.get("z_score") or 0))
        return min(1.0, round(0.5 + min(z, 5.0) * 0.1, 3))
    if event_type == "FlowGraphExported":
        return 0.65
    if event_type == "EngineCycleCompleted":
        return 0.55
    return 0.45


def deterministic_event_id(event_type: str, timestamp: str, payload: dict[str, Any]) -> str:
    material = json.dumps(
        {"event_type": event_type, "timestamp": timestamp, "payload": payload},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(material.encode()).hexdigest()[:32]


def to_experience_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    event_id: str | None = None,
    timestamp: str | None = None,
    trace_id: str | None = None,
) -> ExperienceEvent:
    """Convert a FederalSpendAI substrate event into an ExperienceEvent."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    eid = event_id or deterministic_event_id(event_type, ts, payload)
    trace = trace_id or f"federalspendai-{uuid.uuid4().hex[:12]}"
    summary = _summary_text(event_type, payload)
    exp_type = EXPERIENCE_EVENT_TYPES.get(event_type, "system_event")
    success = payload.get("status", "success") != "failed"

    return ExperienceEvent(
        eventId=eid,
        timestamp=ts,
        type=exp_type,
        context=ExperienceContext(sessionId="federalspendai", traceId=trace),
        input=ExperienceInput(text=summary),
        internalState=ExperienceInternalState(
            activePlan=f"Handle FederalSpendAI {event_type} for Cognitive Substrate ingestion.",
        ),
        action=ExperienceAction(
            tool=event_type,
            reasoning="Emit structured spending analysis as a durable experience event.",
        ),
        result=ExperienceResult(output=summary, success=success),
        evaluation=ExperienceEvaluation(
            rewardScore=_importance_score(event_type, payload),
            selfAssessedQuality=0.8 if success else 0.3,
        ),
        importanceScore=_importance_score(event_type, payload),
        tags=["federalspendai", "open-canada", event_type.lower()],
        sourcePayload=payload,
    )
