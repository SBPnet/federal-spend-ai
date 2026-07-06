"""Register core FederalSpendAI MCP tools on a FastMCP instance."""

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
from federalspendai.tools import anomaly as anomaly_tools
from federalspendai.tools import graph as graph_tools
from federalspendai.tools import nlp as nlp_tools
from federalspendai.tools import public_accounts as pa_tools
from federalspendai.tools import search_semantic as search_tools


def register_core_tools(mcp: FastMCP) -> None:
    """Attach all built-in FederalSpendAI tools to the given MCP server."""

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

    @mcp.tool()
    def search_public_accounts_tool(
        payee: str | None = None,
        department: str | None = None,
        fiscal_year: str | None = None,
        min_amount: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Search Public Accounts payee payments."""
        return pa_tools.search_public_accounts(
            payee=payee,
            department=department,
            fiscal_year=fiscal_year,
            min_amount=min_amount,
            limit=limit,
            offset=offset,
        )

    @mcp.tool()
    def semantic_search_contracts_tool(query: str, limit: int = 20) -> dict:
        """Semantic search over contract embeddings."""
        return search_tools.semantic_search_contracts(query=query, limit=limit)

    @mcp.tool()
    def hybrid_search_tool(query: str, limit: int = 20) -> dict:
        """Hybrid keyword + semantic contract search."""
        return search_tools.hybrid_search_contracts(query=query, limit=limit)

    @mcp.tool()
    def build_embeddings_index_tool(limit: int = 0, emit_events: bool = False) -> dict:
        """Build or refresh the contract embedding index. limit=0 means all contracts."""
        return search_tools.build_embeddings_index(
            limit=None if limit == 0 else limit,
            emit_events=emit_events,
        )

    @mcp.tool()
    def detect_anomalies_tool(
        department: str | None = None,
        include_vendors: bool = True,
        z_threshold: float = 2.5,
        emit_events: bool = False,
    ) -> dict:
        """Detect unusual department or vendor spending patterns."""
        return anomaly_tools.detect_anomalies_tool(
            department=department,
            include_vendors=include_vendors,
            z_threshold=z_threshold,
            emit_events=emit_events,
        )

    @mcp.tool()
    def investigate_anomaly_tool(
        anomaly_id: str | None = None,
        department: str | None = None,
        vendor: str | None = None,
        force: bool = False,
    ) -> dict:
        """Investigate a spending anomaly with contract and Public Accounts evidence."""
        return anomaly_tools.investigate_anomaly_tool(
            anomaly_id=anomaly_id,
            department=department,
            vendor=vendor,
            force=force,
        )

    @mcp.tool()
    def list_stored_anomalies_tool(
        anomaly_status: str = "open",
        investigation_status: str | None = None,
        limit: int = 50,
    ) -> dict:
        """List persisted spending anomalies and investigation status."""
        return anomaly_tools.list_stored_anomalies_tool(
            anomaly_status=anomaly_status,
            investigation_status=investigation_status,
            limit=limit,
        )

    @mcp.tool()
    def correlate_effects_tool(department: str | None = None, vendor: str | None = None) -> dict:
        """Correlate contract spend with Public Accounts payee totals."""
        return anomaly_tools.correlate_effects_tool(department=department, vendor=vendor)

    @mcp.tool()
    def build_money_flow_graph_tool(
        department: str | None = None,
        vendor: str | None = None,
        min_amount: float | None = None,
        limit: int = 500,
    ) -> dict:
        """Build a vendor-to-department money-flow graph summary."""
        return graph_tools.build_money_flow_graph_tool(
            department=department,
            vendor=vendor,
            min_amount=min_amount,
            limit=limit,
        )

    @mcp.tool()
    def trace_money_flow_tool(vendor: str, department: str | None = None) -> dict:
        """Trace money flow from vendor contracts to Public Accounts payees."""
        return graph_tools.trace_money_flow_tool(vendor=vendor, department=department)

    @mcp.tool()
    def export_graph_tool(
        department: str | None = None,
        vendor: str | None = None,
        emit_events: bool = False,
    ) -> dict:
        """Export money-flow graph as JSON for Cognitive Substrate ingestion."""
        return graph_tools.export_graph_tool(
            department=department,
            vendor=vendor,
            emit_events=emit_events,
        )

    @mcp.tool()
    def engine_status_tool() -> dict:
        """Engine scheduler status, plugin list, and last analysis cycle."""
        from federalspendai.tools.status import engine_status

        return engine_status()
