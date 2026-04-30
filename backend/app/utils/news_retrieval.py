"""
utils/news_retrieval.py — Multi-source news fetcher (FR-004).

Strategy (ordered by preference):
  1. DuckDuckGo text search  — highly targeted, financial news sites only
  2. Yahoo Finance (.news)   — always works in Docker, less targeted (filtered)
"""

import logging
import time
from typing import List

from app.models.schemas import NewsArticle

logger = logging.getLogger(__name__)

MAX_ARTICLES = 5
SNIPPET_MAX_CHARS = 180

MAX_RETRIES = 2
RETRY_BACKOFF = [1.0, 2.0]

# Known financial news domains for DDG site-targeting
FINANCIAL_SITES = (
    "site:reuters.com OR site:cnbc.com OR site:bloomberg.com "
    "OR site:ft.com OR site:wsj.com OR site:marketwatch.com "
    "OR site:finance.yahoo.com OR site:investopedia.com "
    "OR site:fool.com OR site:seekingalpha.com"
)

TICKER_TO_COMPANY: dict[str, str] = {
    "AAPL":    "Apple",
    "MSFT":    "Microsoft",
    "GOOGL":   "Google Alphabet",
    "GOOG":    "Google",
    "AMZN":    "Amazon",
    "NVDA":    "NVIDIA",
    "TSLA":    "Tesla",
    "META":    "Meta",
    "NFLX":    "Netflix",
    "BABA":    "Alibaba",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "BNB-USD": "Binance",
    "SOL-USD": "Solana",
    "DOGE-USD":"Dogecoin",
}


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_news(ticker: str) -> List[NewsArticle]:
    """
    Fetches up to MAX_ARTICLES targeted news articles for the ticker.

    1. DuckDuckGo text search  (targeted: financial news sites only)
    2. Yahoo Finance fallback  (reliable but less specific — filtered)
    """
    ticker_upper = ticker.upper()
    company = TICKER_TO_COMPANY.get(ticker_upper, ticker_upper)

    # ── 1. DuckDuckGo text search ──────────────────────────────────────────
    articles = _fetch_ddg_text(ticker_upper, company)
    if articles:
        logger.info("DDG text: fetched %d articles | ticker=%s", len(articles), ticker_upper)
        return articles

    logger.warning("DDG returned nothing | ticker=%s | falling back to Yahoo Finance", ticker_upper)

    # ── 2. Yahoo Finance fallback ──────────────────────────────────────────
    articles = _fetch_yfinance(ticker_upper, company)
    if articles:
        logger.info("Yahoo Finance: fetched %d articles | ticker=%s", len(articles), ticker_upper)
        return articles

    logger.error("All news sources failed | ticker=%s", ticker_upper)
    return []


# ── DuckDuckGo text search (primary) ─────────────────────────────────────────

def _fetch_ddg_text(ticker: str, company: str) -> List[NewsArticle]:
    """
    Uses DDGS().text() instead of .news() — far more reliable in Docker/CI.
    Queries are targeted to financial news sites only.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    # Two query variants: specific ticker + broader company name
    queries = [
        f'"{company}" stock {ticker} {FINANCIAL_SITES}',
        f'"{ticker}" stock news latest {FINANCIAL_SITES}',
    ]

    for query in queries:
        for attempt in range(MAX_RETRIES):
            try:
                articles = _ddg_text_execute(query)
                if articles:
                    return articles
            except Exception as exc:
                logger.debug(
                    "DDG text attempt %d | query='%s' | %s",
                    attempt + 1, query[:60], exc,
                )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])

    return []


def _ddg_text_execute(query: str) -> List[NewsArticle]:
    from duckduckgo_search import DDGS

    articles: List[NewsArticle] = []
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=MAX_ARTICLES))
        for item in results:
            title   = item.get("title", "").strip()
            body    = item.get("body", "")
            source  = _extract_domain(item.get("href", ""))
            snippet = _truncate(body, SNIPPET_MAX_CHARS)

            if not title:
                continue

            articles.append(NewsArticle(title=title, snippet=snippet, source=source))

    return articles


def _extract_domain(url: str) -> str:
    """Returns just the readable domain from a URL, e.g. 'reuters.com'."""
    if not url:
        return ""
    try:
        # Remove protocol, then keep only up to first slash
        domain = url.split("//")[-1].split("/")[0]
        # Drop 'www.'
        return domain.replace("www.", "")
    except Exception:
        return ""


# ── Yahoo Finance fallback ────────────────────────────────────────────────────

def _fetch_yfinance(ticker: str, company: str) -> List[NewsArticle]:
    """
    Retrieves news from Yahoo Finance via yfinance.
    Filters to keep only articles that mention the ticker or company name
    in the title to avoid unrelated generic finance news.
    """
    try:
        import yfinance as yf
        ticker_obj = yf.Ticker(ticker)
        raw_news = ticker_obj.news or []

        keywords = {ticker.lower(), company.lower()}
        # Include first word of company name (e.g. "Tesla" from "Tesla Inc")
        keywords.add(company.split()[0].lower())

        articles: List[NewsArticle] = []
        for item in raw_news:
            content = item.get("content", item)
            title = (
                content.get("title")
                or item.get("title")
                or ""
            ).strip()

            # Filter: skip articles that don't mention the company/ticker
            title_lower = title.lower()
            if not any(kw in title_lower for kw in keywords):
                continue

            snippet = _truncate(
                content.get("summary") or item.get("summary", ""),
                SNIPPET_MAX_CHARS,
            )
            source = (
                content.get("provider", {}).get("displayName")
                or item.get("publisher")
                or None
            )

            articles.append(NewsArticle(title=title, snippet=snippet, source=source))

            if len(articles) >= MAX_ARTICLES:
                break

        return articles

    except Exception as exc:
        logger.warning("yfinance news failed | ticker=%s | %s", ticker, exc)
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _truncate(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
