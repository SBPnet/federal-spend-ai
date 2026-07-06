"""Proxy tools from an external MCP server subprocess."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastmcp import FastMCP
from fastmcp.client.client import Client

logger = logging.getLogger(__name__)


class McpProxyPlugin:
    """Attach tools from an external MCP server as namespaced engine plugins."""

    def __init__(self, spec: dict[str, Any]) -> None:
        self.name = str(spec["name"])
        self.command = str(spec["command"])
        self.args = [str(arg) for arg in spec.get("args", [])]
        self._client: Client | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def plugin_type(self) -> str:
        return "mcp"

    def register(self, mcp: FastMCP) -> None:
        self._loop = asyncio.new_event_loop()
        try:
            self._loop.run_until_complete(self._register_async(mcp))
        except Exception:
            logger.exception("Failed to load MCP plugin %s", self.name)
            raise

    async def _register_async(self, mcp: FastMCP) -> None:
        config = {
            "mcpServers": {
                self.name: {
                    "command": self.command,
                    "args": self.args,
                }
            }
        }
        client = Client(config)
        await client.__aenter__()
        self._client = client

        tools = await client.list_tools()
        for tool in tools:
            remote_name = tool.name
            exposed_name = f"{self.name}__{remote_name}"
            description = tool.description or f"Proxied from MCP plugin {self.name}"

            async def handler(*, _remote: str = remote_name, **kwargs: Any) -> Any:
                assert self._client is not None
                return await self._client.call_tool(_remote, kwargs)

            mcp.add_tool(handler, name=exposed_name, description=description)

    def on_cycle_complete(self, context: dict[str, Any]) -> None:
        return None

    def shutdown(self) -> None:
        if self._client is not None and self._loop is not None:
            try:
                self._loop.run_until_complete(self._client.__aexit__(None, None, None))
            except Exception:
                logger.exception("Error shutting down MCP plugin %s", self.name)
            finally:
                self._client = None
                self._loop.close()
                self._loop = None
