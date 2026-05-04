"""
utils/llm_factory.py — Unified LLM service entry point.

Routing policy:
  APP_ENV=production  → always uses GeminiProvider (Ollama is blocked)
  APP_ENV=local       → uses provider specified by LLM_PROVIDER env var
                         "gemini" (default) | "ollama"

Fallback policy (local only):
  If Ollama fails (connection error, timeout, parse error)
  → automatically retries with Gemini and logs a warning.

Usage:
    from app.utils.llm_factory import get_analysis

    result = await get_analysis(ticker="TSLA", trend="UP", news=articles)
    # result keys: sentiment, verdict, reasoning, confidence
"""

import logging
import os
from typing import List

from app.models.schemas import NewsArticle

logger = logging.getLogger(__name__)

# ── Environment config ────────────────────────────────────────────────────────

APP_ENV      = os.getenv("APP_ENV", "production").lower().strip()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower().strip()


# ── Public interface ──────────────────────────────────────────────────────────

async def get_analysis(ticker: str, trend: str, news: List[NewsArticle]) -> dict:
    """
    Routes the LLM analysis request to the appropriate provider.

    Args:
        ticker: Stock/crypto ticker symbol (e.g. "TSLA").
        trend:  ML forecast trend — "UP", "DOWN", or "NEUTRAL".
        news:   List of NewsArticle objects to analyse.

    Returns:
        dict with keys: sentiment, verdict, reasoning, confidence
    """
    provider = _resolve_provider()
    logger.info(
        "LLM routing | app_env=%s | requested_provider=%s | resolved=%s | ticker=%s",
        APP_ENV, LLM_PROVIDER, provider, ticker,
    )

    if provider == "ollama":
        return await _run_with_ollama_fallback(ticker, trend, news)

    return await _run_gemini(ticker, trend, news)


# ── Routing helpers ───────────────────────────────────────────────────────────

def _resolve_provider() -> str:
    """
    Determines the effective provider.

    Production always returns "gemini" regardless of LLM_PROVIDER.
    Local respects LLM_PROVIDER, defaulting to "gemini".
    """
    if APP_ENV == "production":
        if LLM_PROVIDER == "ollama":
            logger.warning(
                "LLM_PROVIDER=ollama is NOT allowed in production. "
                "Forcing Gemini."
            )
        return "gemini"

    # Local / dev environment
    if LLM_PROVIDER == "ollama":
        return "ollama"

    return "gemini"


async def _run_gemini(ticker: str, trend: str, news: List[NewsArticle]) -> dict:
    """Calls the Gemini provider. Returns fallback dict on error."""
    from app.utils import gemini_provider
    try:
        return await gemini_provider.analyze(ticker=ticker, trend=trend, news=news)
    except Exception as exc:
        logger.error("Gemini provider failed for %s: %s", ticker, exc)
        return _hard_fallback(f"Gemini failed: {exc}")


async def _run_with_ollama_fallback(
    ticker: str, trend: str, news: List[NewsArticle]
) -> dict:
    """
    Tries Ollama first. On any exception, falls back to Gemini.
    Only reachable when APP_ENV=local.
    """
    from app.utils import ollama_provider
    try:
        result = await ollama_provider.analyze(ticker=ticker, trend=trend, news=news)
        logger.info("Ollama analysis succeeded for %s", ticker)
        return result
    except Exception as exc:
        logger.warning(
            "Ollama failed for %s (%s). Falling back to Gemini.", ticker, exc
        )
        return await _run_gemini(ticker, trend, news)


def _hard_fallback(reason: str) -> dict:
    """Last-resort fallback when both providers fail."""
    return {
        "sentiment":  "NEUTRAL",
        "verdict":    "UNCERTAIN",
        "reasoning":  reason,
        "confidence": 0.0,
    }
