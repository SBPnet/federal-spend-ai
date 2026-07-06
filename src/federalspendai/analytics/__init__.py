"""Analytics package."""

from federalspendai.analytics.anomaly import detect_anomalies
from federalspendai.analytics.effects import correlate_effects
from federalspendai.analytics.investigation import investigate_anomaly

__all__ = ["detect_anomalies", "investigate_anomaly", "correlate_effects"]
