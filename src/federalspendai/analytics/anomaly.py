"""Spending anomaly detection."""

from __future__ import annotations

import statistics
from typing import Any

from federalspendai.analytics.anomaly_store import attach_stable_ids, sync_detected_anomalies
from federalspendai.data.store import DataStore


def _zscore(value: float, values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return 0.0
    return (value - mean) / stdev


def detect_spending_anomalies(
    *,
    department: str | None = None,
    z_threshold: float = 2.5,
    store: DataStore | None = None,
) -> list[dict[str, Any]]:
    """Flag department-month spend totals with unusual z-scores."""
    store = store or DataStore()
    monthly = store.monthly_department_spend()
    if department:
        monthly = [row for row in monthly if department.lower() in (row.get("department") or "").lower()]

    by_dept: dict[str, list[dict[str, Any]]] = {}
    for row in monthly:
        by_dept.setdefault(row["department"], []).append(row)

    anomalies: list[dict[str, Any]] = []
    for dept, rows in by_dept.items():
        amounts = [float(row["total_amount"]) for row in rows]
        for row in rows:
            amount = float(row["total_amount"])
            z = _zscore(amount, amounts)
            if z is not None and abs(z) >= z_threshold:
                anomalies.append(
                    {
                        "type": "department_monthly_spend",
                        "department": dept,
                        "month": row["month"],
                        "observed_amount": amount,
                        "baseline_mean": statistics.mean(amounts),
                        "z_score": round(z, 3),
                        "contract_count": row["contract_count"],
                        "sample_contracts": _sample_contracts(store, department=dept, limit=5),
                    }
                )
    anomalies.sort(key=lambda item: abs(item.get("z_score", 0)), reverse=True)
    return anomalies


def flag_vendor_anomalies(
    *,
    z_threshold: float = 2.5,
    store: DataStore | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Flag vendors with unusual monthly award spikes."""
    store = store or DataStore()
    monthly = store.vendor_monthly_spend()
    by_vendor: dict[str, list[dict[str, Any]]] = {}
    for row in monthly:
        by_vendor.setdefault(row["vendor"], []).append(row)

    anomalies: list[dict[str, Any]] = []
    for vendor, rows in by_vendor.items():
        amounts = [float(row["total_amount"]) for row in rows]
        if len(amounts) < 2:
            continue
        latest = max(rows, key=lambda row: row["month"])
        amount = float(latest["total_amount"])
        z = _zscore(amount, amounts)
        if z is not None and abs(z) >= z_threshold:
            anomalies.append(
                {
                    "type": "vendor_monthly_spike",
                    "vendor": vendor,
                    "month": latest["month"],
                    "observed_amount": amount,
                    "baseline_mean": statistics.mean(amounts),
                    "z_score": round(z, 3),
                    "sample_contracts": _sample_contracts(store, vendor=vendor, limit=5),
                }
            )
    anomalies.sort(key=lambda item: abs(item.get("z_score", 0)), reverse=True)
    return anomalies[:limit]


def detect_anomalies(
    *,
    department: str | None = None,
    include_vendors: bool = True,
    z_threshold: float = 2.5,
    store: DataStore | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Run all anomaly detectors and optionally persist results."""
    store = store or DataStore()
    dept_flags = detect_spending_anomalies(
        department=department,
        z_threshold=z_threshold,
        store=store,
    )
    vendor_flags = flag_vendor_anomalies(z_threshold=z_threshold, store=store) if include_vendors else []
    raw = {
        "department_anomalies": dept_flags,
        "vendor_anomalies": vendor_flags,
        "total": len(dept_flags) + len(vendor_flags),
    }
    if persist:
        return sync_detected_anomalies(raw, store=store)
    return attach_stable_ids(raw)


def _sample_contracts(
    store: DataStore,
    *,
    department: str | None = None,
    vendor: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    rows = store.search_contracts(department=department, vendor=vendor, limit=limit)
    return [
        {
            "reference_number": row.get("reference_number"),
            "title_eng": row.get("title_eng"),
            "contract_amount": row.get("contract_amount"),
            "vendor": row.get("vendor"),
            "department": row.get("department"),
        }
        for row in rows
    ]
