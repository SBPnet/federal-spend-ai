"""Persist and sync detected spending anomalies."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from federalspendai.data.store import DataStore


def stable_anomaly_id(
    anomaly_type: str,
    *,
    department: str | None = None,
    vendor: str | None = None,
    month: str,
) -> str:
    """Deterministic ID for a department/vendor monthly spend anomaly."""
    if anomaly_type == "department_monthly_spend":
        material = f"{anomaly_type}|{department}|{month}"
    else:
        material = f"{anomaly_type}|{vendor}|{month}"
    return hashlib.sha256(material.encode()).hexdigest()[:32]


def anomaly_evidence_fingerprint(payload: dict[str, Any]) -> str:
    """Fingerprint anomaly metrics and sample contracts for change detection."""
    sample_refs = sorted(
        ref
        for ref in (
            row.get("reference_number")
            for row in payload.get("sample_contracts", [])
            if isinstance(row, dict)
        )
        if ref
    )
    material = {
        "observed_amount": round(float(payload.get("observed_amount") or 0), 4),
        "z_score": round(float(payload.get("z_score") or 0), 4),
        "baseline_mean": round(float(payload.get("baseline_mean") or 0), 4),
        "contract_count": payload.get("contract_count"),
        "sample_refs": sample_refs,
    }
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


def attach_stable_ids(detected: dict[str, Any]) -> dict[str, Any]:
    """Add stable anomaly_id values to freshly detected anomalies."""
    department: list[dict[str, Any]] = []
    for item in detected.get("department_anomalies", []):
        row = dict(item)
        row["anomaly_id"] = stable_anomaly_id(
            row["type"],
            department=row.get("department"),
            month=row["month"],
        )
        department.append(row)

    vendor: list[dict[str, Any]] = []
    for item in detected.get("vendor_anomalies", []):
        row = dict(item)
        row["anomaly_id"] = stable_anomaly_id(
            row["type"],
            vendor=row.get("vendor"),
            month=row["month"],
        )
        vendor.append(row)

    return {
        "department_anomalies": department,
        "vendor_anomalies": vendor,
        "total": len(department) + len(vendor),
    }


def sync_detected_anomalies(
    detected: dict[str, Any],
    *,
    store: DataStore | None = None,
) -> dict[str, Any]:
    """Persist detected anomalies and track new/updated/unchanged state."""
    store = store or DataStore()
    stamped = attach_stable_ids(detected)
    all_rows = stamped["department_anomalies"] + stamped["vendor_anomalies"]

    sync_stats = {"new": 0, "updated": 0, "unchanged": 0, "resolved": 0}
    seen_ids: list[str] = []
    emitted: list[dict[str, Any]] = []

    for item in all_rows:
        anomaly_id = item["anomaly_id"]
        fingerprint = anomaly_evidence_fingerprint(item)
        seen_ids.append(anomaly_id)
        outcome = store.upsert_spending_anomaly(item, fingerprint)
        sync_stats[outcome] += 1
        stored = store.get_spending_anomaly(anomaly_id)
        if stored and outcome in {"new", "updated"}:
            emitted.append(stored)

    sync_stats["resolved"] = store.resolve_spending_anomalies_not_seen(seen_ids)

    open_rows = store.list_spending_anomalies(anomaly_status="open")
    department_anomalies = [row for row in open_rows if row["type"] == "department_monthly_spend"]
    vendor_anomalies = [row for row in open_rows if row["type"] == "vendor_monthly_spike"]

    return {
        "department_anomalies": department_anomalies,
        "vendor_anomalies": vendor_anomalies,
        "total": len(open_rows),
        "sync": sync_stats,
        "emitted": emitted,
    }
