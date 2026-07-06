"""FederalSpendAI command-line interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from federalspendai.config import get_settings
from federalspendai.data.ingest import ingest_all
from federalspendai.mcp.server import run_server


@click.group()
@click.version_option(package_name="federalspendai")
def cli() -> None:
    """Open-source Canadian federal spending analysis with MCP."""


@cli.command("ingest")
@click.option(
    "--datasets",
    default="awards",
    show_default=True,
    help="Comma-separated datasets: awards, contract_history, proactive, public_accounts",
)
@click.option("--full", is_flag=True, help="Re-download and reload all selected datasets.")
@click.option("--incremental", is_flag=True, help="Alias for default ingest behavior.")
@click.option("--dry-run", is_flag=True, help="Show planned downloads without writing to the database.")
@click.option("--fixture-dir", type=click.Path(path_type=Path), help="Load CSV fixtures instead of downloading.")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def ingest_cmd(
    datasets: str,
    full: bool,
    incremental: bool,
    dry_run: bool,
    fixture_dir: Path | None,
    as_json: bool,
) -> None:
    """Download open CanadaBuys CSVs and load them into the local DuckDB store.

    Examples:

      federalspendai ingest --dry-run

      federalspendai ingest --datasets awards --fixture-dir tests/fixtures

      federalspendai ingest --datasets awards,contract_history
    """
    _ = full, incremental
    selected = [item.strip() for item in datasets.split(",") if item.strip()]
    if not selected:
        click.echo(
            "Error: No datasets specified.\n"
            "  federalspendai ingest --datasets awards\n"
            "  Available: awards, contract_history, proactive, public_accounts",
            err=True,
        )
        raise SystemExit(1)

    settings = get_settings()
    results = ingest_all(
        selected,
        settings=settings,
        dry_run=dry_run,
        fixture_dir=fixture_dir,
    )
    if as_json:
        click.echo(json.dumps(results, indent=2, default=str))
    else:
        for item in results:
            if item.get("dry_run"):
                click.echo(f"[dry-run] {item['dataset']}: {item.get('source_url') or item.get('fixture_path')}")
            else:
                click.echo(
                    f"ingested {item['dataset']}: {item.get('rows', 0)} rows from {item.get('source') or item.get('source_url')}"
                )


@cli.command("serve")
@click.option("--transport", type=click.Choice(["stdio", "sse"]), default="stdio", show_default=True)
@click.option("--port", default=8000, show_default=True, help="Port for SSE transport.")
def serve_cmd(transport: str, port: int) -> None:
    """Run the FederalSpendAI MCP server.

    Examples:

      federalspendai serve

      federalspendai serve --transport sse --port 8000
    """
    run_server(transport=transport, port=port)


@cli.command("analyze")
@click.option("--reference-number", help="Analyze one ingested contract by reference number.")
@click.option("--text", help="Analyze raw contract text instead of a stored contract.")
@click.option(
    "--backend",
    default="auto",
    show_default=True,
    type=click.Choice(["auto", "spacy", "blackstone"]),
    help="NER backend: auto prefers Blackstone when installed.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def analyze_cmd(
    reference_number: str | None,
    text: str | None,
    backend: str,
    as_json: bool,
) -> None:
    """Run contract NLP analysis: entities, risk flags, and summary.

    Examples:

      federalspendai analyze --reference-number MX-444028039551

      federalspendai analyze --text "Sole source IT consulting contract" --json
    """
    from federalspendai.tools.nlp import analyze_contract_text

    if not reference_number and not text:
        click.echo(
            "Error: Provide --reference-number or --text.\n"
            "  federalspendai analyze --reference-number MX-444028039551\n"
            "  federalspendai analyze --text \"Sole source consulting services\"",
            err=True,
        )
        raise SystemExit(1)

    payload = analyze_contract_text(
        text=text,
        reference_number=reference_number,
        backend=backend,
    )
    if "error" in payload:
        click.echo(payload["error"]["message"], err=True)
        raise SystemExit(1)

    if as_json:
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        data = payload["data"]
        click.echo(f"model: {data.get('model')}")
        click.echo(f"summary: {data.get('summary')}")
        if data.get("risk_flags"):
            click.echo("risk_flags:")
            for flag in data["risk_flags"]:
                click.echo(f"  - [{flag['severity']}] {flag['code']}: {flag['message']}")
        if data.get("entities"):
            click.echo(f"entities: {len(data['entities'])} found")


@cli.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
def status_cmd(as_json: bool) -> None:
    """Show local database status without starting the MCP server."""
    from federalspendai.tools.status import federalspend_status

    payload = federalspend_status()
    if as_json:
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        data = payload["data"]
        click.echo(f"database: {data['database_path']}")
        click.echo(f"awards: {data['row_counts'].get('awards', 0)}")
        click.echo(f"public_accounts: {data['row_counts'].get('public_accounts', 0)}")
        click.echo(f"embeddings: {data['row_counts'].get('contract_embeddings', 0)}")
        if data.get("last_ingest"):
            click.echo(f"last ingest: {data['last_ingest']}")


@cli.command("embed")
@click.option("--limit", default=0, show_default=True, help="Max contracts to embed (0 = all).")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON output.")
@click.option("--emit-events", is_flag=True, help="Emit Cognitive Substrate EmbeddingIndexed event.")
def embed_cmd(limit: int, as_json: bool, emit_events: bool) -> None:
    """Build contract embedding index for semantic search."""
    from federalspendai.tools.search_semantic import build_embeddings_index

    payload = build_embeddings_index(limit=None if limit == 0 else limit, emit_events=emit_events)
    if as_json:
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        data = payload["data"]
        click.echo(f"indexed: {data.get('indexed', 0)} contracts with model {data.get('model')}")


@cli.command("detect-anomalies")
@click.option("--department", default=None, help="Filter anomalies to one department.")
@click.option("--z-threshold", default=2.5, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def detect_anomalies_cmd(department: str | None, z_threshold: float, as_json: bool) -> None:
    """Detect spending anomalies in ingested contract data."""
    from federalspendai.tools.anomaly import detect_anomalies_tool

    payload = detect_anomalies_tool(department=department, z_threshold=z_threshold)
    if as_json:
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        data = payload["data"]
        click.echo(f"anomalies found: {data.get('total', 0)}")


@cli.command("trace")
@click.argument("vendor")
@click.option("--department", default=None)
@click.option("--json", "as_json", is_flag=True)
def trace_cmd(vendor: str, department: str | None, as_json: bool) -> None:
    """Trace money flow for a vendor across contracts and Public Accounts."""
    from federalspendai.tools.graph import trace_money_flow_tool

    payload = trace_money_flow_tool(vendor=vendor, department=department)
    if as_json:
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        data = payload["data"]
        click.echo(f"vendor: {data.get('vendor')}")
        click.echo(f"contract_total: {data.get('contract_total')}")
        click.echo(f"public_account_links: {len(data.get('public_account_links', []))}")


def main() -> None:
    try:
        cli(standalone_mode=True)
    except click.ClickException as exc:
        click.echo(str(exc), err=True)
        sys.exit(exc.exit_code)


if __name__ == "__main__":
    main()
