"""NLP utilities for contract text."""

from federalspendai.nlp.blackstone_ner import blackstone_available
from federalspendai.nlp.embed import embeddings_available
from federalspendai.nlp.models import ContractNLPResult, EntitySpan, RiskFlag
from federalspendai.nlp.normalize import normalize_text
from federalspendai.nlp.pipeline import analyze_contract, analyze_text, batch_analyze_contracts

__all__ = [
    "analyze_contract",
    "analyze_text",
    "batch_analyze_contracts",
    "blackstone_available",
    "embeddings_available",
    "normalize_text",
    "ContractNLPResult",
    "EntitySpan",
    "RiskFlag",
]
