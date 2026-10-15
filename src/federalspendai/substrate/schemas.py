"""Cognitive Substrate event payload schemas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class SubstrateEvent(BaseModel):
    event_type: str
    source: str = "federalspendai"
    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict[str, Any]
