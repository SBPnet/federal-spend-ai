"""FastMCP server for FederalSpendAI."""

from __future__ import annotations

from fastmcp import FastMCP

from federalspendai.mcp.tools_registry import register_core_tools


def _standalone_mcp() -> FastMCP:
    mcp = FastMCP(
        name="federal-spend-ai",
        instructions=(
            "Canadian federal government contract and spending analysis over open "
            "CanadaBuys and Proactive Disclosure datasets ingested locally."
        ),
    )
    register_core_tools(mcp)
    return mcp


# Backward-compatible module-level instance for imports/tests.
mcp = _standalone_mcp()


def run_server(transport: str = "stdio", port: int = 8000) -> None:
    """Run the standalone FederalSpendAI MCP server (no background engine)."""
    if transport == "stdio":
        mcp.run()
    elif transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        raise ValueError(f"Unsupported transport: {transport}")
