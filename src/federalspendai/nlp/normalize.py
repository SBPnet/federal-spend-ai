"""Text normalization helpers for contract NLP."""

from __future__ import annotations


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.split())
