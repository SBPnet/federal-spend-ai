"""Optional Blackstone legal NER backend."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from federalspendai.nlp.models import EntitySpan

BLACKSTONE_MODEL = "en_blackstone_proto"


@lru_cache(maxsize=1)
def blackstone_available() -> bool:
    try:
        import spacy  # noqa: F401

        _load_blackstone()
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def _load_blackstone() -> Any:
    import spacy

    return spacy.load(BLACKSTONE_MODEL)


def extract_entities_blackstone(text: str) -> list[EntitySpan]:
    """Extract legal entities using Blackstone when installed."""
    if not text.strip():
        return []
    nlp = _load_blackstone()
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
