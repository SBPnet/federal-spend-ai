"""Load engine MCP plugins from config and entry points."""

from __future__ import annotations

import json
import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

from federalspendai.config import Settings, get_settings
from federalspendai.plugins.base import EnginePlugin
from federalspendai.plugins.builtin import BuiltinFederalSpendPlugin
from federalspendai.plugins.mcp_proxy import McpProxyPlugin

logger = logging.getLogger(__name__)

DEFAULT_PLUGINS_CONFIG = {
    "plugins": [
        {
            "name": "federal-spend-ai",
            "type": "builtin",
            "enabled": True,
        }
    ]
}


def default_plugins_config_path(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.data_dir / "plugins.json"


def ensure_plugins_config(settings: Settings | None = None) -> Path:
    """Write default plugins.json into the data dir if missing."""
    settings = settings or get_settings()
    path = default_plugins_config_path(settings)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_PLUGINS_CONFIG, indent=2))
    return path


def _load_python_plugin(spec: dict[str, Any]) -> EnginePlugin:
    entry_name = spec.get("entry_point") or spec["name"]
    group = entry_points().select(group="federalspendai.plugins")
    for entry in group:
        if entry.name == entry_name:
            plugin = entry.load()()
            if not isinstance(plugin, EnginePlugin):
                raise TypeError(f"Plugin {entry_name} does not implement EnginePlugin")
            return plugin
    raise ValueError(f"Unknown python plugin entry point: {entry_name}")


def _load_plugin(spec: dict[str, Any]) -> EnginePlugin:
    plugin_type = spec.get("type", "builtin")
    if plugin_type == "builtin":
        return BuiltinFederalSpendPlugin()
    if plugin_type == "mcp":
        return McpProxyPlugin(spec)
    if plugin_type == "python":
        return _load_python_plugin(spec)
    raise ValueError(f"Unsupported plugin type: {plugin_type}")


def load_plugins(settings: Settings | None = None) -> list[EnginePlugin]:
    """Load enabled plugins from plugins.json."""
    settings = settings or get_settings()
    path = ensure_plugins_config(settings)
    raw = json.loads(path.read_text())
    plugins: list[EnginePlugin] = []
    seen: set[str] = set()

    for spec in raw.get("plugins", []):
        if not spec.get("enabled", True):
            continue
        name = spec.get("name")
        if not name:
            continue
        if name in seen:
            logger.warning("Duplicate plugin name skipped: %s", name)
            continue
        try:
            plugin = _load_plugin(spec)
            plugins.append(plugin)
            seen.add(name)
        except Exception:
            logger.exception("Failed to load plugin %s", name)

    if not plugins:
        plugins.append(BuiltinFederalSpendPlugin())
    return plugins
