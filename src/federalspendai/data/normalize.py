"""Bilingual CSV normalization utilities."""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl

from federalspendai.data.schema import AWARD_COLUMN_MAP


def _strip_bom(name: str) -> str:
  return name.lstrip("\ufeff").strip('"')


def normalize_award_columns(df: pl.DataFrame) -> pl.DataFrame:
  """Rename bilingual CanadaBuys headers to canonical column names."""
  rename_map: dict[str, str] = {}
  for column in df.columns:
    clean = _strip_bom(column)
    if clean in AWARD_COLUMN_MAP:
      rename_map[column] = AWARD_COLUMN_MAP[clean]
  return df.rename(rename_map)


def _parse_date(value: Any) -> date | None:
  if value is None:
    return None
  text = str(value).strip()
  if not text:
    return None
  try:
    return date.fromisoformat(text[:10])
  except ValueError:
    return None


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


def awards_frame_to_records(df: pl.DataFrame, source_dataset: str, source_url: str) -> pl.DataFrame:
  """Coerce types and ensure required columns for DuckDB ingest."""
  normalized = normalize_award_columns(df)
  columns = set(normalized.columns)

  def col(name: str, default: str | None = None) -> pl.Expr:
    if name in columns:
      return pl.col(name)
    return pl.lit(default).alias(name)

  out = normalized.select(
    col("reference_number").cast(pl.Utf8).alias("reference_number"),
    col("title_eng").cast(pl.Utf8).alias("title_eng"),
    col("title_fra").cast(pl.Utf8).alias("title_fra"),
    col("contract_number").cast(pl.Utf8).alias("contract_number"),
    col("solicitation_number").cast(pl.Utf8).alias("solicitation_number"),
    col("vendor").cast(pl.Utf8).alias("vendor"),
    col("department").cast(pl.Utf8).alias("department"),
    col("contract_amount").cast(pl.Utf8).alias("contract_amount_raw"),
    col("total_contract_value").cast(pl.Utf8).alias("total_contract_value_raw"),
    col("contract_currency").cast(pl.Utf8).alias("contract_currency"),
    col("publication_date").cast(pl.Utf8).alias("publication_date_raw"),
    col("contract_award_date").cast(pl.Utf8).alias("contract_award_date_raw"),
    col("contract_start_date").cast(pl.Utf8).alias("contract_start_date_raw"),
    col("contract_end_date").cast(pl.Utf8).alias("contract_end_date_raw"),
    col("award_status").cast(pl.Utf8).alias("award_status"),
    col("unspsc").cast(pl.Utf8).alias("unspsc"),
    col("unspsc_description_eng").cast(pl.Utf8).alias("unspsc_description_eng"),
    col("procurement_category").cast(pl.Utf8).alias("procurement_category"),
    col("procurement_method").cast(pl.Utf8).alias("procurement_method"),
    col("description_eng").cast(pl.Utf8).alias("description_eng"),
    pl.lit(source_dataset).alias("source_dataset"),
    pl.lit(source_url).alias("source_url"),
  )

  rows = out.to_dicts()
  cleaned: list[dict[str, Any]] = []
  for row in rows:
    ref = row.get("reference_number")
    if not ref:
      continue
    cleaned.append(
      {
        "reference_number": ref,
        "title_eng": row.get("title_eng"),
        "title_fra": row.get("title_fra"),
        "contract_number": row.get("contract_number"),
        "solicitation_number": row.get("solicitation_number"),
        "vendor": row.get("vendor"),
        "department": row.get("department"),
        "contract_amount": _parse_float(row.get("contract_amount_raw")),
        "total_contract_value": _parse_float(row.get("total_contract_value_raw")),
        "contract_currency": row.get("contract_currency"),
        "publication_date": _parse_date(row.get("publication_date_raw")),
        "contract_award_date": _parse_date(row.get("contract_award_date_raw")),
        "contract_start_date": _parse_date(row.get("contract_start_date_raw")),
        "contract_end_date": _parse_date(row.get("contract_end_date_raw")),
        "award_status": row.get("award_status"),
        "unspsc": row.get("unspsc"),
        "unspsc_description_eng": row.get("unspsc_description_eng"),
        "procurement_category": row.get("procurement_category"),
        "procurement_method": row.get("procurement_method"),
        "description_eng": row.get("description_eng"),
        "source_dataset": source_dataset,
        "source_url": source_url,
      }
    )
  return pl.DataFrame(cleaned)
