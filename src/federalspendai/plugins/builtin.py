"""Built-in FederalSpendAI MCP plugin."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from federalspendai.mcp.tools_registry import register_core_tools


class BuiltinFederalSpendPlugin:
    """Core spending analysis tools — always available on the engine host."""

    name = "federal-spend-ai"

    @property
    def plugin_type(self) -> str:
        return "builtin"

    def register(self, mcp: FastMCP) -> None:
        register_core_tools(mcp)

    def on_cycle_complete(self, context: dict[str, Any]) -> None:
        return None

    def shutdown(self) -> None:
        return None
