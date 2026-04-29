"""
utils/news_retrieval.py — DuckDuckGo news fetcher (FR-004).

Fetches the top N news articles for a given ticker.
Returns a list of NewsArticle schema objects ready for the API response.
"""

import logging
from typing import List

from duckduckgo_search import DDGS

from app.models.schemas import NewsArticle

logger = logging.getLogger(__name__)

# Maximum articles to retrieve per request
MAX_ARTICLES = 5
# Truncation length for snippets to keep API responses lean
SNIPPET_MAX_CHARS = 180


def fetch_news(ticker: str) -> List[NewsArticle]:
    """
    Retrieves up to MAX_ARTICLES recent news articles for `ticker`
    using the DuckDuckGo search API.

    Args:
        ticker: Stock/crypto ticker symbol (e.g. "AAPL", "BTC-USD").

    Returns:
        List of NewsArticle objects with title, snippet, and source.

    Raises:
        Exception: Propagated to caller; handled with graceful degradation.
    """
    query = f"{ticker} stock news latest"
    logger.info("Fetching news | ticker=%s | query='%s'", ticker, query)

    articles: List[NewsArticle] = []

    try:
        with DDGS() as ddgs:
            results = ddgs.news(query, max_results=MAX_ARTICLES)

            for item in results:
                snippet = _truncate(item.get("body", ""), SNIPPET_MAX_CHARS)
                articles.append(
                    NewsArticle(
                        title=item.get("title", "Untitled"),
                        snippet=snippet,
                        source=item.get("source", None),
                        url=item.get("url", "")
                    )
                )
    except Exception as e:
        logger.warning("DuckDuckGo search failed (possibly rate limited): %s", e)

    logger.info("Fetched %d articles | ticker=%s", len(articles), ticker)
    return articles


# ── Private helpers ───────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int) -> str:
    """Safely truncates a string to max_chars, appending ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
