"""Public Accounts of Canada CSV parser."""

from __future__ import annotations

import hashlib
from typing import Any

import polars as pl

from federalspendai.data.schema import PUBLIC_ACCOUNTS_COLUMN_MAP


def _strip_bom(name: str) -> str:
    return name.lstrip("\ufeff").strip('"')


def normalize_public_accounts_columns(df: pl.DataFrame) -> pl.DataFrame:
    rename_map: dict[str, str] = {}
    for column in df.columns:
        clean = _strip_bom(column)
        if clean in PUBLIC_ACCOUNTS_COLUMN_MAP:
            rename_map[column] = PUBLIC_ACCOUNTS_COLUMN_MAP[clean]
    return df.rename(rename_map)


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def public_accounts_frame_to_records(
    df: pl.DataFrame,
    source_url: str,
) -> pl.DataFrame:
    normalized = normalize_public_accounts_columns(df)
    rows: list[dict[str, Any]] = []

    for record in normalized.to_dicts():
        payee = (record.get("payee") or "").strip()
        aggregate = _parse_float(record.get("aggregate_payment"))
        current = _parse_float(record.get("expenditure_current_year"))

        # Payee-level rows use aggregate_payment; skip empty payee summary rows
        if not payee:
            continue
        amount = aggregate if aggregate and aggregate > 0 else current
        if not amount or amount <= 0:
            continue

        fiscal_year = record.get("fiscal_year")
        department = record.get("department")
        service_class = record.get("service_class")
        row_id = hashlib.sha256(
            f"{fiscal_year}|{department}|{payee}|{amount}|{service_class}".encode()
        ).hexdigest()[:32]

        rows.append(
            {
                "id": row_id,
                "fiscal_year": fiscal_year,
                "department": department,
                "service_class": service_class,
                "payee": payee,
                "amount": amount,
                "source_url": source_url,
            }
        )

    return pl.DataFrame(rows)
