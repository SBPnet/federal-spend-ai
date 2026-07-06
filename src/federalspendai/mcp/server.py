"""FastMCP server for FederalSpendAI."""

from __future__ import annotations

from fastmcp import FastMCP

from federalspendai.tools import (
    contract_count,
    contract_details,
    federalspend_status,
    list_departments,
    search_contracts,
    spending_by_category,
    spending_by_department,
    top_vendors,
)
from federalspendai.tools import nlp as nlp_tools

mcp = FastMCP(
    name="federal-spend-ai",
    instructions=(
        "Canadian federal government contract and spending analysis over open "
        "CanadaBuys and Proactive Disclosure datasets ingested locally."
    ),
)


@mcp.tool()
def federalspend_status_tool() -> dict:
    """Database freshness, row counts, and last ingest metadata."""
    return federalspend_status()


@mcp.tool()
def search_contracts_tool(
    vendor: str | None = None,
    department: str | None = None,
    keyword: str | None = None,
    status: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    award_date_from: str | None = None,
    award_date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Search federal contracts by vendor, department, keyword, dates, and amounts."""
    return search_contracts(
        vendor=vendor,
        department=department,
        keyword=keyword,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        award_date_from=award_date_from,
        award_date_to=award_date_to,
        limit=limit,
        offset=offset,
    )


@mcp.tool()
def contract_details_tool(
    reference_number: str | None = None,
    contract_number: str | None = None,
) -> dict:
    """Fetch one contract by reference number or contract number."""
    return contract_details(
        reference_number=reference_number,
        contract_number=contract_number,
    )


@mcp.tool()
def contract_count_tool(group_by: str = "department") -> dict:
    """Count contracts grouped by department, status, category, or vendor."""
    return contract_count(group_by=group_by)


@mcp.tool()
def top_vendors_tool(
    department: str | None = None,
    min_amount: float | None = None,
    limit: int = 20,
) -> dict:
    """Rank vendors by total awarded contract value."""
    return top_vendors(department=department, min_amount=min_amount, limit=limit)


@mcp.tool()
def spending_by_department_tool(limit: int = 50) -> dict:
    """Aggregate contract spending by federal contracting entity."""
    return spending_by_department(limit=limit)


@mcp.tool()
def spending_by_category_tool(limit: int = 50) -> dict:
    """Aggregate contract spending by UNSPSC or procurement category."""
    return spending_by_category(limit=limit)


@mcp.tool()
def list_departments_tool(limit: int = 100) -> dict:
    """List contracting departments with contract counts for disambiguation."""
    return list_departments(limit=limit)


@mcp.tool()
def extract_legal_entities_tool(text: str, backend: str = "auto") -> dict:
    """Extract named entities from contract or legal text using spaCy or Blackstone."""
    return nlp_tools.extract_legal_entities(text=text, backend=backend)


@mcp.tool()
def analyze_contract_text_tool(
    text: str | None = None,
    reference_number: str | None = None,
    backend: str = "auto",
) -> dict:
    """Analyze contract text or an ingested contract: entities, risk flags, summary."""
    return nlp_tools.analyze_contract_text(
        text=text,
        reference_number=reference_number,
        backend=backend,
    )


@mcp.tool()
def batch_nlp_tool(reference_numbers: list[str], backend: str = "auto") -> dict:
    """Run NLP analysis across multiple contract reference numbers."""
    return nlp_tools.batch_nlp(reference_numbers=reference_numbers, backend=backend)


def run_server(transport: str = "stdio", port: int = 8000) -> None:
    if transport == "stdio":
        mcp.run()
    elif transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        raise ValueError(f"Unsupported transport: {transport}")
