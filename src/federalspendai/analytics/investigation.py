"""Agentic anomaly investigation with evidence chaining."""

from __future__ import annotations

from typing import Any

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.data.store import DataStore
from federalspendai.nlp.pipeline import analyze_contract


def _public_anomaly_view(stored: dict[str, Any]) -> dict[str, Any]:
    return {
        key: stored.get(key)
        for key in (
            "anomaly_id",
            "type",
            "department",
            "vendor",
            "month",
            "observed_amount",
            "baseline_mean",
            "z_score",
            "contract_count",
            "sample_contracts",
            "anomaly_status",
            "investigation_status",
            "first_seen_at",
            "last_seen_at",
            "last_investigated_at",
        )
    }


def _build_investigation_report(target: dict[str, Any], store: DataStore) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    for sample in target.get("sample_contracts", []):
        ref = sample.get("reference_number")
        if not ref:
            continue
        contract = store.contract_details(reference_number=ref) or sample
        nlp = None
        try:
            nlp = analyze_contract(ref, settings=store.settings).model_dump()
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
        "anomaly": _public_anomaly_view(target),
        "evidence": evidence,
        "public_accounts_matches": public_accounts,
        "recommended_next_steps": [
            "Review sample contracts for procurement method and risk flags.",
            "Cross-check Public Accounts payee records for matching vendor names.",
            "Trace money flow with trace_money_flow for the vendor.",
        ],
    }


def _resolve_stored_anomaly(
    store: DataStore,
    *,
    anomaly_id: str | None = None,
    department: str | None = None,
    vendor: str | None = None,
) -> dict[str, Any] | None:
    if anomaly_id:
        return store.get_spending_anomaly(anomaly_id)
    if department or vendor:
        return store.find_spending_anomaly(department=department, vendor=vendor)
    open_rows = store.list_spending_anomalies(anomaly_status="open", limit=1)
    return open_rows[0] if open_rows else None


def investigate_anomaly(
    anomaly_id: str | None = None,
    *,
    department: str | None = None,
    vendor: str | None = None,
    force: bool = False,
    store: DataStore | None = None,
) -> dict[str, Any]:
    """Build or return a cached evidence report for a stored spending anomaly."""
    store = store or DataStore()
    target = _resolve_stored_anomaly(
        store,
        anomaly_id=anomaly_id,
        department=department,
        vendor=vendor,
    )

    if target is None:
        detect_anomalies(department=department, store=store, persist=True)
        target = _resolve_stored_anomaly(
            store,
            anomaly_id=anomaly_id,
            department=department,
            vendor=vendor,
        )

    if not target:
        return {
            "status": "not_found",
            "message": "No matching stored anomaly found. Run detect_anomalies first.",
            "available_count": len(store.list_spending_anomalies(anomaly_status="open")),
        }

    anomaly_key = target["anomaly_id"]
    evidence_fingerprint = target.get("evidence_fingerprint")
    investigation_status = target.get("investigation_status")
    investigation_fingerprint = target.get("investigation_fingerprint")

    if (
        not force
        and investigation_status == "completed"
        and investigation_fingerprint == evidence_fingerprint
    ):
        cached = store.get_anomaly_investigation_report(anomaly_key)
        if cached:
            cached = dict(cached)
            cached["status"] = "cached"
            cached["message"] = "Investigation is current; no new evidence since last run."
            cached["anomaly"] = _public_anomaly_view(target)
            return cached

    report = _build_investigation_report(target, store)
    store.save_anomaly_investigation(
        anomaly_key,
        report,
        evidence_fingerprint or "",
    )
    return report
