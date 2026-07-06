"""Persist engine scheduler state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from federalspendai.config import Settings, get_settings


def _state_path(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.data_dir / "engine_state.json"


def read_state(settings: Settings | None = None) -> dict[str, Any]:
    path = _state_path(settings)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_state(state: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    path = _state_path(settings)
    path.write_text(json.dumps(state, indent=2, default=str))
    return state


def mark_cycle_started(settings: Settings | None = None) -> dict[str, Any]:
    state = read_state(settings)
    state["status"] = "running"
    state["last_cycle_started_at"] = datetime.now(timezone.utc).isoformat()
    return write_state(state, settings)


def mark_cycle_finished(summary: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    state = read_state(settings)
    state["status"] = "idle"
    state["last_cycle_finished_at"] = datetime.now(timezone.utc).isoformat()
    state["last_cycle"] = summary
    return write_state(state, settings)


def mark_cycle_failed(error: str, settings: Settings | None = None) -> dict[str, Any]:
    state = read_state(settings)
    state["status"] = "error"
    state["last_error"] = error
    state["last_error_at"] = datetime.now(timezone.utc).isoformat()
    return write_state(state, settings)
