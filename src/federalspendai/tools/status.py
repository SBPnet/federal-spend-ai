"""Status and discovery MCP tools."""

from __future__ import annotations

from typing import Any

from federalspendai.config import get_settings
from federalspendai.data.store import DataStore
from federalspendai.mcp.envelope import make_response


def _store() -> DataStore:
    return DataStore(get_settings())


def federalspend_status() -> dict[str, Any]:
    store = _store()
    counts = store.table_counts()
    last = store.last_ingest()
    return make_response(
        {
            "database_path": str(store.db_path),
            "row_counts": counts,
            "last_ingest": last,
            "datasets_supported": ["awards", "contract_history", "proactive", "public_accounts"],
        }
    )


def list_departments(limit: int = 100) -> dict[str, Any]:
    settings = get_settings()
    limit = max(1, min(limit, settings.max_limit))
    rows = _store().list_departments(limit=limit)
    return make_response({"results": rows})
