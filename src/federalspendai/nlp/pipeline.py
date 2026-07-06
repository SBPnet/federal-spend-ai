"""Contract NLP analysis pipeline."""

from __future__ import annotations

from federalspendai.config import Settings, get_settings
from federalspendai.data.store import DataStore
from federalspendai.nlp.blackstone_ner import blackstone_available, extract_entities_blackstone
from federalspendai.nlp.models import ContractNLPResult, EntitySpan
from federalspendai.nlp.normalize import normalize_text
from federalspendai.nlp.risk import assess_procurement_risk
from federalspendai.nlp.spacy_ner import extract_entities_spacy


def _summarize(text: str, max_chars: int = 240) -> str:
    cleaned = normalize_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def _extract_entities(text: str, backend: str, spacy_model: str) -> tuple[list[EntitySpan], str]:
    if backend == "blackstone" and blackstone_available():
        return extract_entities_blackstone(text), "blackstone"
    return extract_entities_spacy(text, model_name=spacy_model), spacy_model


def analyze_text(
    text: str,
    *,
    reference_number: str | None = None,
    contract_amount: float | None = None,
    procurement_method: str | None = None,
    backend: str = "auto",
    spacy_model: str = "en_core_web_sm",
    lang: str = "en",
) -> ContractNLPResult:
    """Run NER, risk heuristics, and summarization on contract text."""
    normalized = normalize_text(text)
    chosen_backend = backend
    if backend == "auto":
        chosen_backend = "blackstone" if blackstone_available() else "spacy"

    entities, model_name = _extract_entities(normalized, chosen_backend, spacy_model)
    risk_flags = assess_procurement_risk(
        normalized,
        contract_amount=contract_amount,
        procurement_method=procurement_method,
    )
    return ContractNLPResult(
        reference_number=reference_number,
        text_analyzed=normalized,
        entities=entities,
        risk_flags=risk_flags,
        summary=_summarize(normalized),
        model=model_name,
        lang=lang,
    )


def analyze_contract(
    reference_number: str,
    *,
    settings: Settings | None = None,
    backend: str = "auto",
) -> ContractNLPResult:
    """Analyze one ingested contract by reference number."""
    settings = settings or get_settings()
    store = DataStore(settings)
    row = store.contract_details(reference_number=reference_number)
    if not row:
        raise ValueError(f"Contract not found: {reference_number}")

    parts = [
        row.get("title_eng"),
        row.get("description_eng"),
        row.get("unspsc_description_eng"),
        row.get("procurement_method"),
    ]
    text = " ".join(part for part in parts if part)
    return analyze_text(
        text,
        reference_number=reference_number,
        contract_amount=row.get("contract_amount"),
        procurement_method=row.get("procurement_method"),
        backend=backend,
        lang=settings.lang,
    )


def batch_analyze_contracts(
    reference_numbers: list[str],
    *,
    settings: Settings | None = None,
    backend: str = "auto",
) -> list[ContractNLPResult]:
    """Analyze multiple contracts."""
    return [
        analyze_contract(ref, settings=settings, backend=backend)
        for ref in reference_numbers
    ]
