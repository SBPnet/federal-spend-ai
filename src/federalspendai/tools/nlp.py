"""MCP tools for contract NLP analysis."""

from __future__ import annotations

from typing import Any

from federalspendai.mcp.envelope import make_error, make_response
from federalspendai.nlp.blackstone_ner import blackstone_available
from federalspendai.nlp.pipeline import analyze_contract, analyze_text


def extract_legal_entities(
    text: str,
    backend: str = "auto",
) -> dict[str, Any]:
    """Extract named entities from contract or legal text."""
    if not text.strip():
        return make_error("EMPTY_TEXT", "Provide non-empty contract text to analyze.")
    result = analyze_text(text, backend=backend)
    return make_response(
        {
            "entities": [entity.model_dump() for entity in result.entities],
            "model": result.model,
            "blackstone_available": blackstone_available(),
        }
    )


def analyze_contract_text(
    text: str | None = None,
    reference_number: str | None = None,
    backend: str = "auto",
) -> dict[str, Any]:
    """Run full NLP analysis: entities, risk flags, and summary."""
    try:
        if reference_number:
            result = analyze_contract(reference_number, backend=backend)
        elif text and text.strip():
            result = analyze_text(text, backend=backend)
        else:
            return make_error(
                "MISSING_INPUT",
                "Provide text or reference_number.",
                suggestions=["analyze_contract_text(reference_number='MX-123')"],
            )
    except ValueError as exc:
        return make_error("NOT_FOUND", str(exc))
    return make_response(result.model_dump())


def batch_nlp(
    reference_numbers: list[str],
    backend: str = "auto",
) -> dict[str, Any]:
    """Batch NLP analysis for multiple contract reference numbers."""
    if not reference_numbers:
        return make_error("EMPTY_BATCH", "Provide at least one reference_number.")
    results = []
    errors = []
    for ref in reference_numbers:
        try:
            results.append(analyze_contract(ref, backend=backend).model_dump())
        except ValueError as exc:
            errors.append({"reference_number": ref, "error": str(exc)})
    return make_response({"results": results, "errors": errors, "count": len(results)})
