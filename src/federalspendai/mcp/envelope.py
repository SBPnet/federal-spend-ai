"""MCP response envelope utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_response(
    data: Any,
    *,
    source: str = "federalspendai",
    lang: str = "en",
    cached: bool = False,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "source": source,
        "lang": lang,
        "cached": cached,
        "timestamp": utc_now(),
    }
    if extra_meta:
        meta.update(extra_meta)
    return {"_meta": meta, "data": data}


def make_error(
    code: str,
    message: str,
    *,
    suggestions: list[str] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if suggestions:
        error["suggestions"] = suggestions
    return {"error": error, "_meta": {"timestamp": utc_now()}}
