"""
utils/gemini_provider.py — Google Gemini LLM provider.

Wraps the Gemini API call into a standardised async interface
consumed by llm_factory.py. Includes an improved prompt that asks
the model to explicitly compare news snippets against the ML trend
verdict and return a dynamic confidence score.
"""

import asyncio
import json
import logging
import os

import google.generativeai as genai
from typing import List

from app.models.schemas import NewsArticle
from app.utils.prompt_builder import build_analysis_prompt, SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.0-flash"
TIMEOUT_SECONDS = 10.0

if _API_KEY:
    genai.configure(api_key=_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. Gemini provider will fail.")


# ── Public interface ──────────────────────────────────────────────────────────

async def analyze(ticker: str, trend: str, news: List[NewsArticle]) -> dict:
    """
    Calls Gemini to assess news sentiment AND alignment with the ML trend.

    Returns a standardised dict:
        sentiment  : "POSITIVE" | "NEGATIVE" | "NEUTRAL"
        verdict    : "ALIGNED"  | "CONFLICTING" | "UNCERTAIN"
        reasoning  : str
        confidence : float  (0.0 – 1.0, dynamic based on news strength)
    """
    if not _API_KEY:
        logger.error("Skipping Gemini analysis: GEMINI_API_KEY not set.")
        return _fallback("API key missing.")

    if not news:
        return _fallback("No news articles found to analyze.")

    prompt = build_analysis_prompt(ticker=ticker, trend=trend, news=news)

    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=TIMEOUT_SECONDS,
        )

        result = json.loads(response.text)
        return {
            "sentiment":  result.get("sentiment", "NEUTRAL"),
            "verdict":    result.get("verdict", "UNCERTAIN"),
            "reasoning":  result.get("reasoning", "Analysis complete."),
            "confidence": float(result.get("confidence", 0.5)),
        }

    except asyncio.TimeoutError:
        logger.error("Gemini timed out after %ss for %s", TIMEOUT_SECONDS, ticker)
        return _fallback("LLM analysis timed out.")
    except json.JSONDecodeError:
        logger.error("Gemini returned malformed JSON for %s", ticker)
        return _fallback("LLM returned malformed response.")
    except Exception as exc:
        logger.error("Gemini analysis failed for %s: %s", ticker, exc)
        return _fallback(f"LLM analysis failed: {exc}")


# ── Private helpers ───────────────────────────────────────────────────────────

def _fallback(reason: str) -> dict:
    """Safe fallback when Gemini is unavailable."""
    return {
        "sentiment":  "NEUTRAL",
        "verdict":    "UNCERTAIN",
        "reasoning":  reason,
        "confidence": 0.0,
    }
