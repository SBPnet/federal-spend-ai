"""Tests for Cognitive Substrate ExperienceEvent adaptation."""

from __future__ import annotations

from federalspendai.substrate.experience import to_experience_event


def test_to_experience_event_maps_required_fields():
    payload = {
        "vendor": "Irving Oil Limited",
        "month": "2025-07",
        "z_score": 4.2,
    }
    event = to_experience_event("AnomalyFlagged", payload, event_id="evt-123")

    assert event.eventId == "evt-123"
    assert event.type == "spending_anomaly"
    assert event.context.sessionId == "federalspendai"
    assert event.input.text
    assert event.action.tool == "AnomalyFlagged"
    assert event.result.success is True
    assert "federalspendai" in event.tags
    assert event.sourcePayload == payload


def test_flow_graph_export_summary_text():
    payload = {"summary": {"node_count": 2, "edge_count": 1}}
    event = to_experience_event("FlowGraphExported", payload)
    assert "2 nodes" in event.input.text
    assert event.type == "money_flow_export"
