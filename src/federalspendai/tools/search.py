"""Contract search and detail MCP tools."""

from __future__ import annotations

from datetime import date
from typing import Any

from federalspendai.config import get_settings
from federalspendai.data.store import DataStore
from federalspendai.mcp.envelope import make_error, make_response


def _store() -> DataStore:
    return DataStore(get_settings())


def _clamp_limit(limit: int) -> int:
    settings = get_settings()
    return max(1, min(limit, settings.max_limit))


def search_contracts(
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
) -> dict[str, Any]:
    parsed_from = date.fromisoformat(award_date_from) if award_date_from else None
    parsed_to = date.fromisoformat(award_date_to) if award_date_to else None
    rows = _store().search_contracts(
        vendor=vendor,
        department=department,
        keyword=keyword,
        status=status,
        min_amount=min_amount,
        max_amount=max_amount,
        award_date_from=parsed_from,
        award_date_to=parsed_to,
        limit=_clamp_limit(limit),
        offset=offset,
    )
    return make_response({"results": rows, "count": len(rows), "offset": offset})


def contract_details(
    reference_number: str | None = None,
    contract_number: str | None = None,
) -> dict[str, Any]:
    if not reference_number and not contract_number:
        return make_error(
            "MISSING_IDENTIFIER",
            "Provide reference_number or contract_number.",
            suggestions=["contract_details(reference_number='MX-123')"],
        )
    row = _store().contract_details(
        reference_number=reference_number,
        contract_number=contract_number,
    )
    if not row:
        return make_error("NOT_FOUND", "No contract matched the identifier provided.")
    return make_response(row)
