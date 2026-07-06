"""Aggregation MCP tools."""

from __future__ import annotations

from typing import Any

from federalspendai.config import get_settings
from federalspendai.data.store import DataStore
from federalspendai.mcp.envelope import make_response


def _store() -> DataStore:
    return DataStore(get_settings())


def _clamp_limit(limit: int) -> int:
    settings = get_settings()
    return max(1, min(limit, settings.max_limit))


def contract_count(group_by: str = "department") -> dict[str, Any]:
    rows = _store().contract_count(group_by=group_by)
    return make_response({"group_by": group_by, "results": rows})


def top_vendors(
    department: str | None = None,
    min_amount: float | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    rows = _store().top_vendors(
        department=department,
        min_amount=min_amount,
        limit=_clamp_limit(limit),
    )
    return make_response({"results": rows})


def spending_by_department(limit: int = 50) -> dict[str, Any]:
    rows = _store().spending_by_department(limit=_clamp_limit(limit))
    return make_response({"results": rows})


def spending_by_category(limit: int = 50) -> dict[str, Any]:
    rows = _store().spending_by_category(limit=_clamp_limit(limit))
    return make_response({"results": rows})
