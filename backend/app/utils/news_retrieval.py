"""
utils/news_retrieval.py — Multi-source news fetcher (FR-004).

Primary source: Yahoo Finance via yfinance (.news property)
  - Same library already used for price data, no new dependencies.
  - Works reliably in Docker / datacenter environments.

Fallback source: DuckDuckGo
  - Used if yfinance returns 0 articles.
  - Up to 3 retries with exponential backoff.
  - Multiple query strategies.
"""

import logging
import time
from typing import List

import yfinance as yf
from app.models.schemas import NewsArticle

logger = logging.getLogger(__name__)

MAX_ARTICLES = 5
SNIPPET_MAX_CHARS = 180

# DDG fallback retry config
MAX_RETRIES = 2
RETRY_BACKOFF = [1.0, 2.0]

TICKER_TO_COMPANY: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google Alphabet",
    "GOOG": "Google",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "META": "Meta Facebook",
    "NFLX": "Netflix",
    "BABA": "Alibaba",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "BNB-USD": "Binance",
    "SOL-USD": "Solana",
    "DOGE-USD": "Dogecoin",
}


def fetch_news(ticker: str) -> List[NewsArticle]:
    """
    Fetches up to MAX_ARTICLES news articles for the ticker.

    Tries Yahoo Finance first (via yfinance), falls back to DuckDuckGo.
    Returns [] only if both sources fail.
    """
    ticker_upper = ticker.upper()

    # ── Primary: Yahoo Finance ────────────────────────────────────────────
    articles = _fetch_from_yfinance(ticker_upper)
    if articles:
        logger.info("Fetched %d articles from Yahoo Finance | ticker=%s", len(articles), ticker_upper)
        return articles

    logger.warning("Yahoo Finance returned no news | ticker=%s | trying DDG fallback", ticker_upper)

    # ── Fallback: DuckDuckGo ──────────────────────────────────────────────
    articles = _fetch_from_ddg(ticker_upper)
    if articles:
        logger.info("Fetched %d articles from DuckDuckGo | ticker=%s", len(articles), ticker_upper)
        return articles

    logger.warning("All news sources exhausted | ticker=%s", ticker_upper)
    return []


# ── Yahoo Finance source ──────────────────────────────────────────────────────

def _fetch_from_yfinance(ticker: str) -> List[NewsArticle]:
    """
    Retrieves news from Yahoo Finance using yfinance's Ticker.news property.
    Returns [] on any failure.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        raw_news = ticker_obj.news or []

        articles: List[NewsArticle] = []
        for item in raw_news[:MAX_ARTICLES]:
            # yfinance news structure: {title, link, publisher, providerPublishTime, thumbnail, relatedTickers}
            # Content is in nested 'content' dict in newer yfinance versions
            content = item.get("content", item)
            title = (
                content.get("title")
                or item.get("title")
                or "Untitled"
            )
            snippet = _truncate(
                content.get("summary")
                or item.get("summary", ""),
                SNIPPET_MAX_CHARS
            )
            source = (
                content.get("provider", {}).get("displayName")
                or item.get("publisher")
                or None
            )

            if not title or title == "Untitled":
                continue

            articles.append(NewsArticle(title=title, snippet=snippet, source=source))

        return articles

    except Exception as exc:
        logger.warning("yfinance news fetch failed | ticker=%s | error=%s", ticker, exc)
        return []


# ── DuckDuckGo fallback source ────────────────────────────────────────────────

def _fetch_from_ddg(ticker: str) -> List[NewsArticle]:
    """
    Tries multiple DDG query strategies with retries.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    company = TICKER_TO_COMPANY.get(ticker, ticker)
    queries = [
        f"{company} stock news",
        f"{ticker} stock market news",
        f"{company} financial results",
    ]

    for query in queries:
        for attempt in range(MAX_RETRIES):
            try:
                articles = _ddg_execute(query)
                if articles:
                    return articles
            except Exception as exc:
                logger.debug("DDG attempt %d failed | query='%s' | %s", attempt + 1, query, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])

    return []


def _ddg_execute(query: str) -> List[NewsArticle]:
    from duckduckgo_search import DDGS
    articles: List[NewsArticle] = []
    with DDGS() as ddgs:
        results = ddgs.news(query, max_results=MAX_ARTICLES)
        for item in results:
            snippet = _truncate(item.get("body", ""), SNIPPET_MAX_CHARS)
            articles.append(NewsArticle(
                title=item.get("title", "Untitled"),
                snippet=snippet,
                source=item.get("source") or item.get("publisher") or None,
            ))
    return articles


# ── Helpers ───────────────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
