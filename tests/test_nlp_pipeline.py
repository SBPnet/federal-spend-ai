"""Tests for NLP pipeline with mocked spaCy backend."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from federalspendai.config import Settings
from federalspendai.data.ingest import ingest_dataset
from federalspendai.nlp.models import EntitySpan
from federalspendai.nlp.pipeline import analyze_contract, analyze_text

FIXTURES = Path(__file__).parent / "fixtures"

MOCK_ENTITIES = [
    EntitySpan(text="Acme Consulting Inc.", label="ORG", start=0, end=20),
]


@patch(
    "federalspendai.nlp.pipeline._extract_entities",
    return_value=(MOCK_ENTITIES, "spacy-test"),
)
@patch("federalspendai.nlp.pipeline.blackstone_available", return_value=False)
def test_analyze_text_returns_entities_and_risk(_blackstone, _extract):
    result = analyze_text(
        "Sole source contract awarded to Acme Consulting Inc.",
        contract_amount=1_500_000,
        backend="spacy",
    )
    assert result.entities[0].label == "ORG"
    assert any(flag.code == "LIMITED_COMPETITION" for flag in result.risk_flags)
    assert any(flag.code == "HIGH_VALUE_CONTRACT" for flag in result.risk_flags)
    assert result.summary


@patch(
    "federalspendai.nlp.pipeline._extract_entities",
    return_value=(MOCK_ENTITIES, "spacy-test"),
)
@patch("federalspendai.nlp.pipeline.blackstone_available", return_value=False)
def test_analyze_contract_from_store(_blackstone, _extract, tmp_path: Path):
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "nlp.duckdb")
    ingest_dataset("awards", settings=settings, fixture_path=FIXTURES / "awards.csv")
    result = analyze_contract("MX-444028039551", settings=settings, backend="spacy")
    assert result.reference_number == "MX-444028039551"
    assert "Diesel" in result.text_analyzed or "diesel" in result.text_analyzed.lower()


@patch(
    "federalspendai.nlp.pipeline._extract_entities",
    return_value=([], "spacy-test"),
)
@patch("federalspendai.nlp.pipeline.blackstone_available", return_value=False)
def test_analyze_contract_missing_raises(_blackstone, _extract, tmp_path: Path):
    settings = Settings(data_dir=tmp_path, db_path=tmp_path / "nlp.duckdb")
    with pytest.raises(ValueError, match="not found"):
        analyze_contract("DOES-NOT-EXIST", settings=settings)
