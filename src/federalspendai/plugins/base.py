"""Plugin protocol for the FederalSpendAI engine."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from fastmcp import FastMCP


@runtime_checkable
class EnginePlugin(Protocol):
    """MCP plugin loaded by the engine host."""

    name: str

    @property
    def plugin_type(self) -> str:
        """Plugin kind: builtin, mcp, or python."""

    def register(self, mcp: FastMCP) -> None:
        """Register MCP tools on the shared engine host."""

    def on_cycle_complete(self, context: dict[str, Any]) -> None:
        """Called after each ingest/analyze cycle."""

    def shutdown(self) -> None:
        """Release subprocesses or connections."""
