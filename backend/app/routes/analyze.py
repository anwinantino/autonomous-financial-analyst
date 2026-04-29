"""
routes/analyze.py — GET /analyze endpoint (FR-008).

Fetches news, runs Gemini sentiment analysis, and returns
an alignment verdict comparing the forecast trend to news sentiment.
Response time target: 3–6 seconds (FR-008).
"""

import logging
import re

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import AnalyzeResponse
from app.utils.news_retrieval import fetch_news
from app.utils.gemini_llm import analyze_sentiment
from app.utils.comparator import compute_verdict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analyze"])

TICKER_PATTERN = re.compile(r"^[A-Z0-9\-]{1,12}$")


@router.get("/analyze", response_model=AnalyzeResponse)
async def analyze(
    ticker: str = Query(..., description="Stock or crypto ticker, e.g. AAPL or BTC-USD"),
    trend: str = Query("NEUTRAL", description="Forecast trend from /predict: UP, DOWN, or NEUTRAL"),
):
    """
    Fetches top 5 news articles for the ticker, sends them to Gemini for
    sentiment analysis, then computes an alignment verdict against the
    provided forecast trend. Gracefully degrades if Gemini is unavailable.
    """
    ticker = ticker.upper().strip()
    trend = trend.upper().strip()

    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=422,
            detail="Invalid ticker format. Use alphanumeric characters and hyphens only.",
        )
    if trend not in {"UP", "DOWN", "NEUTRAL"}:
        raise HTTPException(
            status_code=422,
            detail="Trend must be one of: UP, DOWN, NEUTRAL.",
        )

    logger.info("Received /analyze request | ticker=%s | trend=%s", ticker, trend)

    # Step 1: Fetch news articles
    try:
        news_articles = fetch_news(ticker=ticker)
    except Exception as exc:
        logger.error("News retrieval failed | ticker=%s | error=%s", ticker, exc, exc_info=True)
        raise HTTPException(status_code=502, detail="News retrieval failed. Please try again.")

    # Step 2: Gemini LLM sentiment analysis (graceful degradation)
    try:
        llm_result = await analyze_sentiment(ticker=ticker, trend=trend, news=news_articles)
        sentiment = llm_result["sentiment"]
        reasoning = llm_result["reasoning"]
    except Exception as exc:
        # If Gemini fails, return UNCERTAIN with a clear explanation
        logger.warning("Gemini analysis failed, degrading gracefully | error=%s", exc)
        sentiment = "NEUTRAL"
        reasoning = "AI analysis is temporarily unavailable. Showing news without sentiment verdict."

    # Step 3: Compute alignment verdict
    verdict_result = compute_verdict(
        trend=trend, 
        sentiment=sentiment, 
        llm_confidence=llm_result.get("confidence", 0.5) if "llm_result" in locals() else 0.5
    )

    logger.info(
        "Analysis complete | ticker=%s | sentiment=%s | verdict=%s",
        ticker, sentiment, verdict_result["verdict"],
    )

    return AnalyzeResponse(
        news=news_articles,
        sentiment=sentiment,
        verdict=verdict_result["verdict"],
        confidence=verdict_result["confidence"],
        reasoning=reasoning,
    )
