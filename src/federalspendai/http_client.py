"""Shared HTTP client defaults for open-government downloads."""

from __future__ import annotations

DEFAULT_USER_AGENT = (
    "FederalSpendAI/0.3.0 (+https://github.com/SBPnet/federal-spend-ai; open research)"
)


def default_headers() -> dict[str, str]:
    return {"User-Agent": DEFAULT_USER_AGENT}
