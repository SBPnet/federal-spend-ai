"""MCP host that mounts engine plugins on a shared FastMCP server."""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from federalspendai.config import Settings, get_settings
from federalspendai.engine.runner import EngineRunner
from federalspendai.plugins.registry import ensure_plugins_config, load_plugins

logger = logging.getLogger(__name__)


def create_engine_mcp(settings: Settings | None = None) -> tuple[FastMCP, list]:
    """Build the engine MCP host with all enabled plugins registered."""
    settings = settings or get_settings()
    ensure_plugins_config(settings)
    plugins = load_plugins(settings)

    mcp = FastMCP(
        name="federalspend-engine",
        instructions=(
            "FederalSpendAI engine host. Core spending tools come from the "
            "federal-spend-ai plugin; additional MCP servers are mounted as "
            "namespaced plugins. Data is refreshed automatically on a schedule."
        ),
    )

    for plugin in plugins:
        logger.info("Registering MCP plugin: %s (%s)", plugin.name, plugin.plugin_type)
        plugin.register(mcp)

    return mcp, plugins


def run_engine(
    *,
    transport: str = "sse",
    port: int = 8000,
    settings: Settings | None = None,
) -> None:
    """Start the background engine scheduler and MCP plugin host."""
    settings = settings or get_settings()
    mcp, plugins = create_engine_mcp(settings)
    runner = EngineRunner(settings=settings, plugins=plugins)

    if settings.engine_enabled:
        runner.start()
    else:
        logger.warning("Engine scheduler disabled (FEDERALSPEND_ENGINE_ENABLED=false)")

    try:
        if transport == "stdio":
            mcp.run()
        elif transport == "sse":
            mcp.run(transport="sse", port=port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")
    finally:
        runner.stop()
