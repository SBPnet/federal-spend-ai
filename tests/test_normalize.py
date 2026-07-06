"""Tests for bilingual CSV normalization."""

from pathlib import Path

import polars as pl

from federalspendai.data.normalize import awards_frame_to_records, normalize_award_columns

FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture() -> pl.DataFrame:
    return pl.read_csv(
        FIXTURES / "awards.csv",
        infer_schema_length=1000,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )


def test_normalize_award_columns_renames_bilingual_headers():
    df = _read_fixture()
    normalized = normalize_award_columns(df)
    assert "title_eng" in normalized.columns
    assert "vendor" in normalized.columns
    assert "department" in normalized.columns


def test_awards_frame_to_records_parses_amounts_and_dates():
    df = _read_fixture()
    prepared = awards_frame_to_records(df, "awards", "fixture://awards.csv")
    assert prepared.height >= 1
    row = prepared.row(0, named=True)
    assert row["reference_number"]
    assert row["contract_amount"] == 2000000.0
