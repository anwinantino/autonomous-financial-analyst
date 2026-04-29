"""
utils/comparator.py — Forecast ↔ Sentiment alignment logic (FR-006).

Maps forecast trend and news sentiment to one of three verdicts:
  ALIGNED     — trend and sentiment agree
  CONFLICTING — trend and sentiment contradict each other
  UNCERTAIN   — one or both sides are neutral, or data is missing

Confidence scores reflect how strongly the alignment was determined.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Mapping from trend/sentiment to a unified direction signal
_DIRECTION_MAP = {
    "UP": "BULLISH",
    "DOWN": "BEARISH",
    "NEUTRAL": "NEUTRAL",
    "POSITIVE": "BULLISH",
    "NEGATIVE": "BEARISH",
}

# Confidence scores by verdict type
_CONFIDENCE = {
    "ALIGNED": 0.85,
    "CONFLICTING": 0.80,
    "UNCERTAIN": 0.40,
}


def compute_verdict(trend: str, sentiment: str, llm_confidence: float = 0.5) -> Dict[str, Any]:
    """
    Computes the alignment verdict between a price forecast trend
    and a news sentiment classification.

    Args:
        trend: "UP" | "DOWN" | "NEUTRAL" (from Prophet forecast)
        sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL" (from Gemini)
        llm_confidence: float between 0.0 and 1.0 from the LLM

    Returns:
        Dict with:
          - verdict: "ALIGNED" | "CONFLICTING" | "UNCERTAIN"
          - confidence: float between 0.0 and 1.0
    """
    trend_direction = _DIRECTION_MAP.get(trend.upper(), "NEUTRAL")
    sentiment_direction = _DIRECTION_MAP.get(sentiment.upper(), "NEUTRAL")

    logger.debug(
        "Computing verdict | trend=%s (%s) | sentiment=%s (%s) | llm_conf=%.2f",
        trend, trend_direction, sentiment, sentiment_direction, llm_confidence
    )

    verdict = _determine_verdict(trend_direction, sentiment_direction)
    
    # Calculate a dynamic confidence score based on the base verdict confidence
    # and the LLM's reported confidence.
    base_confidence = _CONFIDENCE[verdict]
    
    # For UNCERTAIN, we keep it low. For others, we blend it with the LLM's confidence.
    if verdict == "UNCERTAIN":
        confidence = base_confidence
    else:
        # A simple weighted average: 60% base logic, 40% LLM confidence
        confidence = (base_confidence * 0.6) + (llm_confidence * 0.4)

    logger.info("Verdict computed | verdict=%s | confidence=%.2f", verdict, confidence)
    return {"verdict": verdict, "confidence": round(confidence, 2)}


# ── Private helpers ───────────────────────────────────────────────────────────

def _determine_verdict(trend_direction: str, sentiment_direction: str) -> str:
    """
    Core rule-based logic to map two directions to a verdict.

    Rules:
    - Both NEUTRAL → UNCERTAIN
    - Either is NEUTRAL (but not both) → UNCERTAIN
    - Both match (BULLISH/BULLISH or BEARISH/BEARISH) → ALIGNED
    - They differ (BULLISH/BEARISH or BEARISH/BULLISH) → CONFLICTING
    """
    if trend_direction == "NEUTRAL" or sentiment_direction == "NEUTRAL":
        return "UNCERTAIN"
    if trend_direction == sentiment_direction:
        return "ALIGNED"
    return "CONFLICTING"
