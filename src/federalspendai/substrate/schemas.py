"""Cognitive Substrate event payload schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SubstrateEvent(BaseModel):
    event_type: str
    source: str = "federalspendai"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict[str, Any]
