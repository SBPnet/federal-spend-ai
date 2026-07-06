"""Agentic anomaly investigation with evidence chaining."""

from __future__ import annotations

from typing import Any

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.data.store import DataStore
from federalspendai.nlp.pipeline import analyze_contract


def investigate_anomaly(
    anomaly_id: str | None = None,
    *,
    department: str | None = None,
    vendor: str | None = None,
    store: DataStore | None = None,
) -> dict[str, Any]:
    """Build an evidence report for a spending anomaly."""
    store = store or DataStore()
    anomalies = detect_anomalies(department=department, store=store)
    all_flags = anomalies["department_anomalies"] + anomalies["vendor_anomalies"]

    target: dict[str, Any] | None = None
    if anomaly_id:
        target = next((item for item in all_flags if item["anomaly_id"] == anomaly_id), None)
    elif department or vendor:
        for item in all_flags:
            if department and item.get("department") and department.lower() in item["department"].lower():
                target = item
                break
            if vendor and item.get("vendor") and vendor.lower() in item["vendor"].lower():
                target = item
                break
    else:
        target = all_flags[0] if all_flags else None

    if not target:
        return {
            "status": "not_found",
            "message": "No matching anomaly found. Run detect_anomalies first.",
            "available_count": len(all_flags),
        }

    evidence: list[dict[str, Any]] = []
    for sample in target.get("sample_contracts", []):
        ref = sample.get("reference_number")
        if not ref:
            continue
        contract = store.contract_details(reference_number=ref) or sample
        nlp = None
        try:
            nlp = analyze_contract(ref).model_dump()
        except ValueError:
            pass
        evidence.append({"contract": contract, "nlp": nlp})

    public_accounts = []
    if target.get("vendor"):
        public_accounts = store.search_public_accounts(payee=target["vendor"], limit=10)
    elif evidence and evidence[0]["contract"].get("vendor"):
        public_accounts = store.search_public_accounts(
            payee=evidence[0]["contract"]["vendor"],
            limit=10,
        )

    return {
        "status": "ok",
        "anomaly": target,
        "evidence": evidence,
        "public_accounts_matches": public_accounts,
        "recommended_next_steps": [
            "Review sample contracts for procurement method and risk flags.",
            "Cross-check Public Accounts payee records for matching vendor names.",
            "Trace money flow with trace_money_flow for the vendor.",
        ],
    }
