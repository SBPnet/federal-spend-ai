#!/usr/bin/env python3
"""BigPines.net companion demo for FederalSpendAI.

Runs an offline, reproducible end-to-end pipeline on bundled fixtures and
writes artifacts under ./runnable/out/ with checked invariants.

Usage:
  python examples/bigpines_companion_demo.py
  python examples/bigpines_companion_demo.py --skip-embed
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
OUT_DIR = REPO_ROOT / "runnable" / "out"


def _check(condition: bool, message: str, results: list[str]) -> None:
    status = "PASS" if condition else "FAIL"
    results.append(f"[{status}] {message}")
    if not condition:
        raise AssertionError(message)


def run_demo(*, skip_embed: bool = False) -> dict:
    from federalspendai.analytics.anomaly import detect_anomalies
    from federalspendai.config import Settings
    from federalspendai.data.ingest import ingest_all
    from federalspendai.data.store import DataStore
    from federalspendai.embeddings.index import build_embedding_index
    from federalspendai.graphs.builder import build_money_flow_graph
    from federalspendai.graphs.export import export_graph_json
    from federalspendai.graphs.tracer import trace_money_flow
    from federalspendai.substrate.events import emit_flow_graph_exported

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data_dir = Path(tempfile.mkdtemp(prefix="federalspendai-demo-"))
    settings = Settings(data_dir=data_dir)
    checks: list[str] = []

    store = DataStore(settings)
    ingest_results = ingest_all(
        ["awards", "public_accounts"],
        settings=settings,
        fixture_dir=FIXTURES,
    )
    _check(len(ingest_results) == 2, "ingested awards and public_accounts fixtures", checks)
    _check(
        sum(item.get("rows", 0) for item in ingest_results) >= 12,
        "fixture ingest loaded multi-month award history",
        checks,
    )

    embed_summary = {"indexed": 0, "skipped": 0, "model": "skipped"}
    if not skip_embed:
        embed_summary = build_embedding_index(settings=settings, incremental=False)
        _check(embed_summary.get("indexed", 0) > 0, "built contract embedding index", checks)

    anomalies = detect_anomalies(store=store)
    _check(anomalies.get("total", 0) > 0, "detected at least one spending anomaly", checks)

    trace = trace_money_flow("Irving Oil Limited", store=store)
    _check(trace.get("contract_count", 0) >= 3, "traced Irving Oil contract history", checks)
    _check(len(trace.get("public_account_links", [])) >= 1, "linked vendor to Public Accounts payee", checks)

    graph = build_money_flow_graph(vendor="Irving Oil Limited", store=store)
    export_payload = export_graph_json(graph)
    emit_flow_graph_exported(export_payload, settings=settings)
    _check(export_payload["summary"]["edge_count"] >= 1, "exported money-flow graph", checks)

    legacy_events = list((settings.data_dir / "events").glob("*.json"))
    experience_events = list((settings.data_dir / "events" / "experience").glob("*.json"))
    _check(len(legacy_events) >= 1, "wrote legacy substrate event files", checks)
    _check(len(experience_events) >= 1, "wrote ExperienceEvent-compatible files", checks)

    experience = json.loads(experience_events[0].read_text())
    required_fields = {
        "eventId",
        "timestamp",
        "type",
        "context",
        "input",
        "action",
        "result",
        "evaluation",
        "tags",
    }
    _check(required_fields.issubset(experience.keys()), "experience event has required fields", checks)

    summary = {
        "demo": "federalspendai-bigpines-companion",
        "fixture_note": (
            "Synthetic illustrative fixtures for reproducible demos. "
            "Not verified live government records."
        ),
        "checks": checks,
        "ingest": ingest_results,
        "embed": embed_summary,
        "anomalies_total": anomalies.get("total"),
        "trace_vendor": trace.get("vendor"),
        "graph_summary": export_payload.get("summary"),
        "events": {
            "legacy": [path.name for path in legacy_events],
            "experience": [path.name for path in experience_events],
        },
    }

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (OUT_DIR / "trace.json").write_text(json.dumps(trace, indent=2, default=str))
    (OUT_DIR / "graph.json").write_text(json.dumps(export_payload, indent=2, default=str))
    shutil.copytree(settings.data_dir / "events", OUT_DIR / "events")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="FederalSpendAI BigPines companion demo")
    parser.add_argument("--skip-embed", action="store_true", help="Skip sentence-transformers embed step")
    args = parser.parse_args()

    try:
        summary = run_demo(skip_embed=args.skip_embed)
    except Exception as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, default=str))
    print(f"\nArtifacts written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
