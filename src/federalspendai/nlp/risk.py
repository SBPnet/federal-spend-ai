"""Rule-based procurement risk heuristics (OSS, no API keys)."""

from __future__ import annotations

import re

from federalspendai.nlp.models import RiskFlag

LIMITED_TENDERING_PATTERNS = [
    r"sole\s+source",
    r"limited\s+tender",
    r"non[- ]competitive",
    r"single\s+source",
    r"appel\s+d'offres\s+limit",
]

HIGH_VALUE_THRESHOLD = 1_000_000.0


def assess_procurement_risk(
    text: str,
    *,
    contract_amount: float | None = None,
    procurement_method: str | None = None,
) -> list[RiskFlag]:
    """Flag procurement patterns worth investigator follow-up."""
    flags: list[RiskFlag] = []
    combined = " ".join(filter(None, [text, procurement_method or ""])).lower()

    for pattern in LIMITED_TENDERING_PATTERNS:
        if re.search(pattern, combined, flags=re.IGNORECASE):
            flags.append(
                RiskFlag(
                    code="LIMITED_COMPETITION",
                    message="Text suggests limited or non-competitive procurement.",
                    severity="medium",
                    confidence=0.85,
                )
            )
            break

    if contract_amount is not None and contract_amount >= HIGH_VALUE_THRESHOLD:
        flags.append(
            RiskFlag(
                code="HIGH_VALUE_CONTRACT",
                message=f"Contract amount >= ${HIGH_VALUE_THRESHOLD:,.0f} CAD.",
                severity="info",
                confidence=1.0,
            )
        )

    if procurement_method and "non-competitive" in procurement_method.lower():
        flags.append(
            RiskFlag(
                code="NON_COMPETITIVE_METHOD",
                message=f"Procurement method: {procurement_method}",
                severity="medium",
                confidence=0.9,
            )
        )

    if not text.strip():
        flags.append(
            RiskFlag(
                code="MISSING_DESCRIPTION",
                message="No contract description text available for NLP review.",
                severity="low",
                confidence=1.0,
            )
        )

    return flags
