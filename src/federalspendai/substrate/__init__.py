"""Cognitive Substrate integration hooks."""

from federalspendai.substrate.events import (
    emit_anomaly_flagged,
    emit_embedding_indexed,
    emit_event,
    emit_flow_graph_exported,
)
from federalspendai.substrate.schemas import SubstrateEvent

__all__ = [
    "SubstrateEvent",
    "emit_event",
    "emit_anomaly_flagged",
    "emit_embedding_indexed",
    "emit_flow_graph_exported",
]
