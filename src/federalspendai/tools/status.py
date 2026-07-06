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


def engine_status() -> dict[str, Any]:
    from federalspendai.engine.state import read_state
    from federalspendai.plugins.registry import ensure_plugins_config, load_plugins

    settings = get_settings()
    ensure_plugins_config(settings)
    plugins = load_plugins(settings)
    state = read_state(settings)
    return make_response(
        {
            "enabled": settings.engine_enabled,
            "poll_interval_seconds": settings.engine_poll_interval_seconds,
            "datasets": settings.engine_datasets_list(),
            "plugins": [{"name": plugin.name, "type": plugin.plugin_type} for plugin in plugins],
            "plugins_config": str(settings.data_dir / "plugins.json"),
            "state_file": str(settings.data_dir / "engine_state.json"),
            **state,
        }
    )


def list_departments(limit: int = 100) -> dict[str, Any]:
    settings = get_settings()
    limit = max(1, min(limit, settings.max_limit))
    rows = _store().list_departments(limit=limit)
    return make_response({"results": rows})
