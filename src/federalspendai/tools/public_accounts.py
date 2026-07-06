"""MCP tools for Public Accounts data."""

from __future__ import annotations

from typing import Any

from federalspendai.config import get_settings
from federalspendai.data.store import DataStore
from federalspendai.mcp.envelope import make_response


def _store() -> DataStore:
    return DataStore(get_settings())


def search_public_accounts(
    payee: str | None = None,
    department: str | None = None,
    fiscal_year: str | None = None,
    min_amount: float | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    settings = get_settings()
    limit = max(1, min(limit, settings.max_limit))
    rows = _store().search_public_accounts(
        payee=payee,
        department=department,
        fiscal_year=fiscal_year,
        min_amount=min_amount,
        limit=limit,
        offset=offset,
    )
    return make_response({"results": rows, "count": len(rows), "offset": offset})
