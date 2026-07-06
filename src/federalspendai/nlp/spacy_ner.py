"""spaCy NER backend with lazy model loading."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from federalspendai.nlp.models import EntitySpan


@lru_cache(maxsize=1)
def _load_spacy_model(model_name: str) -> Any:
    import spacy

    try:
        return spacy.load(model_name)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{model_name}' is not installed. "
            f"Run: python -m spacy download {model_name}"
        ) from exc


def extract_entities_spacy(text: str, model_name: str = "en_core_web_sm") -> list[EntitySpan]:
    """Extract named entities using spaCy."""
    if not text.strip():
        return []
    nlp = _load_spacy_model(model_name)
    doc = nlp(text)
    return [
        EntitySpan(
            text=ent.text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
            confidence=None,
        )
        for ent in doc.ents
    ]
