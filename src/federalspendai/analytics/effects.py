"""Basic effect correlation between spend and contextual indicators."""

from __future__ import annotations

from typing import Any

from federalspendai.data.store import DataStore


def correlate_effects(
    *,
    department: str | None = None,
    vendor: str | None = None,
    store: DataStore | None = None,
) -> dict[str, Any]:
    """Correlate contract spend with related public accounts payee totals."""
    store = store or DataStore()
    contracts = store.search_contracts(department=department, vendor=vendor, limit=100)
    contract_total = sum(float(row.get("contract_amount") or 0) for row in contracts)

    payee_name = vendor
    if not payee_name and contracts:
        payee_name = contracts[0].get("vendor")

    public_rows = store.search_public_accounts(payee=payee_name, department=department, limit=50) if payee_name else []
    public_total = sum(float(row.get("amount") or 0) for row in public_rows)

    ratio = None
    if contract_total > 0 and public_total > 0:
        ratio = round(public_total / contract_total, 3)

    return {
        "department": department,
        "vendor": payee_name,
        "contract_count": len(contracts),
        "contract_total": contract_total,
        "public_accounts_count": len(public_rows),
        "public_accounts_total": public_total,
        "public_to_contract_ratio": ratio,
        "note": (
            "Ratio compares Public Accounts payee totals to CanadaBuys contract totals. "
            "Fuzzy name matching may affect accuracy."
        ),
        "public_accounts_sample": public_rows[:5],
        "contract_sample": contracts[:5],
    }
