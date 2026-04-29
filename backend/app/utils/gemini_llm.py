"""
utils/gemini_llm.py — Google Gemini LLM integration (FR-005).

Sends ticker, forecast trend, and news articles to Gemini and
returns structured sentiment + reasoning. Reads GEMINI_API_KEY
from environment variables only — never hardcoded.
"""

import json
import logging
import os
from typing import Dict, Any, List

import google.generativeai as genai
from dotenv import load_dotenv

from app.models.schemas import NewsArticle

load_dotenv(".env.local")  # Load secrets from local env file when running locally

logger = logging.getLogger(__name__)

# Gemini model to use — update if a newer model becomes available
GEMINI_MODEL = "gemini-1.5-flash"

# Timeout in seconds for Gemini API calls (FR-005: max 5 seconds)
REQUEST_TIMEOUT_SECONDS = 5


def _get_client() -> genai.GenerativeModel:
    """
    Initializes the Gemini client using the API key from environment.
    Raises a clear RuntimeError if the key is missing rather than leaking it.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env.local or the container environment."
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def analyze_sentiment(
    ticker: str,
    trend: str,
    articles: List[NewsArticle],
) -> Dict[str, Any]:
    """
    Sends a structured prompt to Gemini and returns sentiment + reasoning.

    Args:
        ticker: The stock/crypto ticker being analyzed.
        trend: Forecast trend direction — "UP", "DOWN", or "NEUTRAL".
        articles: List of NewsArticle objects from DuckDuckGo.

    Returns:
        Dict with keys:
          - sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL"
          - reasoning: natural-language explanation string

    Raises:
        Exception: Any Gemini API or parsing error; caller handles degradation.
    """
    model = _get_client()
    prompt = _build_prompt(ticker=ticker, trend=trend, articles=articles)

    logger.info("Sending prompt to Gemini | ticker=%s | model=%s", ticker, GEMINI_MODEL)

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3,  # Low temp for deterministic, factual responses
        ),
    )

    result = _parse_response(response.text)
    logger.info("Gemini response received | ticker=%s | sentiment=%s", ticker, result["sentiment"])
    return result


# ── Private helpers ───────────────────────────────────────────────────────────

def _build_prompt(ticker: str, trend: str, articles: List[NewsArticle]) -> str:
    """
    Constructs the structured prompt sent to Gemini.
    The prompt enforces a JSON response format to simplify parsing.
    """
    articles_text = "\n".join(
        f"- [{a.source or 'Unknown'}] {a.title}: {a.snippet}" for a in articles
    )

    return f"""You are a financial analyst assistant. Analyze the following news articles
about {ticker} and determine the overall market sentiment.

FORECAST CONTEXT:
- Ticker: {ticker}
- ML Forecast Trend: {trend} (based on 30-day Prophet model)

NEWS ARTICLES:
{articles_text}

TASK:
Based on the news articles above, respond with a JSON object containing:
1. "sentiment": one of "POSITIVE", "NEGATIVE", or "NEUTRAL"
2. "reasoning": a 2-3 sentence explanation of why you chose this sentiment,
   and whether the news supports or contradicts the forecast trend of {trend}.

Respond ONLY with valid JSON. Example format:
{{
  "sentiment": "POSITIVE",
  "reasoning": "Recent earnings beat and product launches signal strong growth..."
}}"""


def _parse_response(raw_text: str) -> Dict[str, Any]:
    """
    Parses Gemini's JSON response and validates required fields.
    Falls back to NEUTRAL sentiment if parsing fails.
    """
    try:
        data = json.loads(raw_text)
        sentiment = data.get("sentiment", "NEUTRAL").upper()
        reasoning = data.get("reasoning", "No reasoning provided.")

        # Validate sentiment is one of the expected values
        if sentiment not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            logger.warning("Unexpected sentiment value from Gemini: %s", sentiment)
            sentiment = "NEUTRAL"

        return {"sentiment": sentiment, "reasoning": reasoning}

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON response | error=%s | raw=%s", exc, raw_text[:200])
        return {
            "sentiment": "NEUTRAL",
            "reasoning": "Could not parse AI response. Defaulting to neutral sentiment.",
        }
