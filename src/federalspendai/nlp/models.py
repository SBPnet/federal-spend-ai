"""Structured NLP output models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EntitySpan(BaseModel):
    """Named entity with source offsets."""

    text: str
    label: str
    start: int
    end: int
    confidence: float | None = None


class RiskFlag(BaseModel):
    """Heuristic or model-derived risk indicator."""

    code: str
    message: str
    severity: str = "info"
    confidence: float = 1.0


class ContractNLPResult(BaseModel):
    """Full NLP analysis for one contract or text snippet."""

    reference_number: str | None = None
    text_analyzed: str
    entities: list[EntitySpan] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    summary: str = ""
    model: str = "spacy"
    lang: str = "en"
