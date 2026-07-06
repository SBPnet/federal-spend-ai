"""Tests for procurement risk heuristics."""

from federalspendai.nlp.risk import assess_procurement_risk


def test_high_value_flag():
    flags = assess_procurement_risk(
        "Enterprise consulting services",
        contract_amount=2_500_000,
    )
    codes = {flag.code for flag in flags}
    assert "HIGH_VALUE_CONTRACT" in codes


def test_limited_competition_flag():
    flags = assess_procurement_risk("This is a sole source procurement for IT support.")
    codes = {flag.code for flag in flags}
    assert "LIMITED_COMPETITION" in codes


def test_missing_description_flag():
    flags = assess_procurement_risk("")
    codes = {flag.code for flag in flags}
    assert "MISSING_DESCRIPTION" in codes
