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
    help="Comma-separated datasets: awards, contract_history, proactive",
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
            "  Available: awards, contract_history, proactive",
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
@click.option("--json", "as_json", is_flag=True, help="Reserved for future analytics output.")
def analyze_cmd(as_json: bool) -> None:
    """Run spending analysis workflows (anomaly detection — coming soon).

    Examples:

      federalspendai analyze
    """
    _ = as_json
    click.echo(
        "Analyze workflows (NLP, anomaly detection) are planned for a future release.\n"
        "Use MCP tools via `federalspendai serve` for current querying capabilities.",
        err=True,
    )
    raise SystemExit(0)


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
        if data.get("last_ingest"):
            click.echo(f"last ingest: {data['last_ingest']}")


def main() -> None:
    try:
        cli(standalone_mode=True)
    except click.ClickException as exc:
        click.echo(str(exc), err=True)
        sys.exit(exc.exit_code)


if __name__ == "__main__":
    main()
