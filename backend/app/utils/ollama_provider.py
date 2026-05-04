"""
utils/ollama_provider.py — Local Ollama LLM provider.

Calls a locally running Ollama instance (default: http://localhost:11434)
using the /api/chat endpoint. Designed for development use only.
Uses the same standardised interface as gemini_provider.py.

Model default: llama3.2:3b
"""

import json
import logging
import os
import re
from typing import List

import httpx

from app.models.schemas import NewsArticle
from app.utils.prompt_builder import build_analysis_prompt, SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
TIMEOUT_SECONDS = 60.0  # Local models are slower; give them more time


# ── Public interface ──────────────────────────────────────────────────────────

async def analyze(ticker: str, trend: str, news: List[NewsArticle]) -> dict:
    """
    Calls local Ollama to assess news sentiment AND alignment with the ML trend.

    Returns a standardised dict:
        sentiment  : "POSITIVE" | "NEGATIVE" | "NEUTRAL"
        verdict    : "ALIGNED"  | "CONFLICTING" | "UNCERTAIN"
        reasoning  : str
        confidence : float  (0.0 – 1.0)
    """
    if not news:
        return _fallback("No news articles found to analyze.")

    prompt = build_analysis_prompt(ticker=ticker, trend=trend, news=news)

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user",   "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        raw_content = data["message"]["content"]

        # Extract JSON — local models sometimes wrap it in ```json fences
        result = _parse_json(raw_content)

        return {
            "sentiment":  _validate_sentiment(result.get("sentiment", "NEUTRAL")),
            "verdict":    _validate_verdict(result.get("verdict", "UNCERTAIN")),
            "reasoning":  result.get("reasoning", "Local LLM analysis complete."),
            "confidence": float(result.get("confidence", 0.5)),
        }

    except httpx.ConnectError:
        logger.error(
            "Ollama is not reachable at %s. Is it running?", OLLAMA_BASE_URL
        )
        raise  # Let llm_factory handle the fallback

    except httpx.TimeoutException:
        logger.error("Ollama timed out after %ss for %s", TIMEOUT_SECONDS, ticker)
        raise

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("Ollama returned unparseable response for %s: %s", ticker, exc)
        raise

    except Exception as exc:
        logger.error("Ollama analysis failed for %s: %s", ticker, exc)
        raise


# ── Private helpers ───────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    """Attempts to parse JSON, stripping markdown code fences if present."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    return json.loads(text)


def _validate_sentiment(value: str) -> str:
    valid = {"POSITIVE", "NEGATIVE", "NEUTRAL"}
    return value.upper() if value.upper() in valid else "NEUTRAL"


def _validate_verdict(value: str) -> str:
    valid = {"ALIGNED", "CONFLICTING", "UNCERTAIN"}
    return value.upper() if value.upper() in valid else "UNCERTAIN"


def _fallback(reason: str) -> dict:
    return {
        "sentiment":  "NEUTRAL",
        "verdict":    "UNCERTAIN",
        "reasoning":  reason,
        "confidence": 0.0,
    }
