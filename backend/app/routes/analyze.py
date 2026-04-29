"""
routes/analyze.py — GET /analyze endpoint (FR-008, FR-013).

Fetches news, runs Gemini sentiment analysis, and returns
an alignment verdict comparing the forecast trend to news sentiment.
Response time target: 3–6 seconds (FR-008).

FR-013: `trend` is now optional (defaults to NEUTRAL).
This allows the frontend to fire /predict and /analyze in parallel
without waiting for the forecast result to determine the trend.
If trend is not provided, the endpoint resolves it gracefully.
"""

import logging
import re

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.schemas import AnalyzeResponse
from app.utils.news_retrieval import fetch_news
from app.utils.gemini_llm import analyze_sentiment
from app.utils.comparator import compute_verdict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analyze"])

TICKER_PATTERN = re.compile(r"^[A-Z0-9\-]{1,12}$")
VALID_TRENDS = {"UP", "DOWN", "NEUTRAL"}


@router.get("/analyze", response_model=AnalyzeResponse)
async def analyze(
    ticker: str = Query(..., description="Stock or crypto ticker, e.g. AAPL or BTC-USD"),
    trend: Optional[str] = Query(
        None,
        description="Forecast trend: UP, DOWN, or NEUTRAL. "
                    "If omitted, defaults to NEUTRAL (enables parallel calls with /predict).",
    ),
):
    """
    Fetches top 5 news articles for the ticker, sends them to Gemini for
    sentiment analysis, then computes an alignment verdict against the
    provided forecast trend.

    Gracefully degrades if Gemini is unavailable.
    `trend` is optional — omit it to allow true parallel frontend calls (FR-013).
    """
    ticker = ticker.upper().strip()

    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=422,
            detail="Invalid ticker format. Use alphanumeric characters and hyphens only.",
        )

    # Resolve trend — default to NEUTRAL if not provided (FR-013 parallel support)
    if trend is None:
        resolved_trend = "NEUTRAL"
        logger.info(
            "No trend provided for /analyze | ticker=%s | defaulting to NEUTRAL", ticker
        )
    else:
        resolved_trend = trend.upper().strip()
        if resolved_trend not in VALID_TRENDS:
            raise HTTPException(
                status_code=422,
                detail="Trend must be one of: UP, DOWN, NEUTRAL.",
            )

    logger.info(
        "Received /analyze request | ticker=%s | trend=%s", ticker, resolved_trend
    )

    # Step 1: Fetch news articles
    try:
        news_articles = fetch_news(ticker=ticker)
    except Exception as exc:
        logger.error(
            "News retrieval failed | ticker=%s | error=%s", ticker, exc, exc_info=True
        )
        raise HTTPException(
            status_code=502, detail="News retrieval failed. Please try again."
        )

    # Step 2: Gemini LLM sentiment analysis (graceful degradation)
    llm_result = None
    try:
        llm_result = await analyze_sentiment(
            ticker=ticker, trend=resolved_trend, news=news_articles
        )
        sentiment = llm_result["sentiment"]
        reasoning = llm_result["reasoning"]
    except Exception as exc:
        logger.warning("Gemini analysis failed, degrading gracefully | error=%s", exc)
        sentiment = "NEUTRAL"
        reasoning = (
            "AI analysis is temporarily unavailable. "
            "Showing news without sentiment verdict."
        )

    # Step 3: Compute alignment verdict
    verdict_result = compute_verdict(
        trend=resolved_trend,
        sentiment=sentiment,
        llm_confidence=llm_result.get("confidence", 0.5) if llm_result else 0.5,
    )

    logger.info(
        "Analysis complete | ticker=%s | sentiment=%s | verdict=%s",
        ticker,
        sentiment,
        verdict_result["verdict"],
    )

    return AnalyzeResponse(
        news=news_articles,
        sentiment=sentiment,
        verdict=verdict_result["verdict"],
        confidence=verdict_result["confidence"],
        reasoning=reasoning,
    )
