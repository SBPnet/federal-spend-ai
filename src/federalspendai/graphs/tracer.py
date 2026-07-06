"""Money-flow tracing across contracts and public accounts."""

from __future__ import annotations

import difflib
from typing import Any

from federalspendai.data.store import DataStore
from federalspendai.graphs.builder import build_money_flow_graph


def _link_confidence(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def trace_money_flow(
    vendor: str,
    *,
    department: str | None = None,
    store: DataStore | None = None,
    link_threshold: float = 0.6,
) -> dict[str, Any]:
    """Trace vendor contract flows and link to Public Accounts payees."""
    store = store or DataStore()
    graph = build_money_flow_graph(vendor=vendor, department=department, store=store)
    contracts = store.search_contracts(vendor=vendor, department=department, limit=100)

    payee_candidates = store.search_public_accounts(payee=vendor, department=department, limit=20)
    if not payee_candidates:
        # Fuzzy link against all payees containing first token
        token = vendor.split()[0] if vendor.split() else vendor
        payee_candidates = store.search_public_accounts(payee=token, limit=50)

    links: list[dict[str, Any]] = []
    for row in payee_candidates:
        payee = row.get("payee") or ""
        confidence = _link_confidence(vendor, payee)
        if confidence >= link_threshold:
            store.upsert_vendor_link(vendor, payee, confidence, "fuzzy_name")
            links.append(
                {
                    "vendor": vendor,
                    "payee": payee,
                    "link_confidence": round(confidence, 3),
                    "public_accounts_amount": row.get("amount"),
                    "department": row.get("department"),
                    "fiscal_year": row.get("fiscal_year"),
                }
            )

    contract_total = sum(float(c.get("contract_amount") or 0) for c in contracts)
    public_total = sum(float(link.get("public_accounts_amount") or 0) for link in links)

    return {
        "vendor": vendor,
        "department_filter": department,
        "contract_count": len(contracts),
        "contract_total": contract_total,
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "public_account_links": links,
        "public_accounts_total": public_total,
        "contracts": contracts[:10],
    }
