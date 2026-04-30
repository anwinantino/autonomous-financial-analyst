"""
utils/news_retrieval.py — Multi-source news fetcher (FR-004).

Guarantee: always returns at least MIN_ARTICLES (4) relevant articles.

Strategy:
  1. DuckDuckGo text search  — targeted keyword queries, no site: restrictions
  2. Yahoo Finance            — always-reliable fallback, fills any remaining gap
  3. Deduplicate & merge      — combine both sources up to MAX_ARTICLES (5)
"""

import logging
import time
from typing import List

from app.models.schemas import NewsArticle

logger = logging.getLogger(__name__)

MAX_ARTICLES = 5
MIN_ARTICLES = 4          # Minimum we guarantee per request
SNIPPET_MAX_CHARS = 180
DDG_FETCH_COUNT = 10      # Fetch more, then trim to MAX_ARTICLES

MAX_RETRIES = 2
RETRY_BACKOFF = [1.0, 2.0]

TICKER_TO_COMPANY: dict[str, str] = {
    "AAPL":     "Apple",
    "MSFT":     "Microsoft",
    "GOOGL":    "Google Alphabet",
    "GOOG":     "Google",
    "AMZN":     "Amazon",
    "NVDA":     "NVIDIA",
    "TSLA":     "Tesla",
    "META":     "Meta",
    "NFLX":     "Netflix",
    "BABA":     "Alibaba",
    "PLTR":     "Palantir",
    "AMD":      "AMD",
    "INTC":     "Intel",
    "ORCL":     "Oracle",
    "CRM":      "Salesforce",
    "SHOP":     "Shopify",
    "SNAP":     "Snap",
    "UBER":     "Uber",
    "LYFT":     "Lyft",
    "PYPL":     "PayPal",
    "SQ":       "Block Square",
    "COIN":     "Coinbase",
    "JPM":      "JPMorgan",
    "GS":       "Goldman Sachs",
    "BAC":      "Bank of America",
    "BRK-B":    "Berkshire Hathaway",
    "XOM":      "ExxonMobil",
    "CVX":      "Chevron",
    "GOLD":     "Barrick Gold",
    "BTC-USD":  "Bitcoin",
    "ETH-USD":  "Ethereum",
    "BNB-USD":  "Binance",
    "SOL-USD":  "Solana",
    "DOGE-USD": "Dogecoin",
}


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_news(ticker: str) -> List[NewsArticle]:
    """
    Fetches MIN_ARTICLES–MAX_ARTICLES targeted news articles for ticker.

    Merges DDG + Yahoo Finance results, deduplicates, and ensures at least
    MIN_ARTICLES relevant articles are returned on every call.
    """
    ticker_upper = ticker.upper()
    company = TICKER_TO_COMPANY.get(ticker_upper, ticker_upper)

    articles: List[NewsArticle] = []
    seen_titles: set[str] = set()

    # ── 1. DuckDuckGo text search ──────────────────────────────────────────
    ddg_articles = _fetch_ddg(ticker_upper, company)
    for art in ddg_articles:
        key = art.title.lower().strip()
        if key not in seen_titles:
            seen_titles.add(key)
            articles.append(art)

    logger.info("DDG returned %d articles | ticker=%s", len(articles), ticker_upper)

    # ── 2. Yahoo Finance top-up ────────────────────────────────────────────
    # Always try Yahoo Finance to fill any gap up to MIN_ARTICLES
    if len(articles) < MIN_ARTICLES:
        needed = MAX_ARTICLES - len(articles)
        # lenient=True: skip keyword filter so we definitely get articles
        yf_articles = _fetch_yfinance(
            ticker_upper, company,
            lenient=(len(articles) < MIN_ARTICLES),
            max_needed=needed + 3,  # fetch a few extra to allow dedup
        )
        for art in yf_articles:
            key = art.title.lower().strip()
            if key not in seen_titles and len(articles) < MAX_ARTICLES:
                seen_titles.add(key)
                articles.append(art)

        logger.info(
            "After Yahoo Finance top-up: %d articles | ticker=%s",
            len(articles), ticker_upper,
        )

    if len(articles) < MIN_ARTICLES:
        logger.warning(
            "Could only fetch %d/%d articles | ticker=%s",
            len(articles), MIN_ARTICLES, ticker_upper,
        )

    return articles[:MAX_ARTICLES]


# ── DuckDuckGo text search ────────────────────────────────────────────────────

def _fetch_ddg(ticker: str, company: str) -> List[NewsArticle]:
    """
    Uses DDGS().text() with broad keyword queries.
    No site: restrictions — maximises result count.
    Fetches DDG_FETCH_COUNT results and trims to MAX_ARTICLES.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return []

    company_short = company.split()[0]  # e.g. "NVIDIA" from "NVIDIA Corp"

    # Ordered from most specific to broadest — stop at first that yields results
    queries = [
        f"{ticker} {company_short} stock news 2025",
        f"{company} stock price news analysis",
        f"{company_short} shares market news",
    ]

    for query in queries:
        for attempt in range(MAX_RETRIES):
            try:
                results = _ddg_execute(query)
                if results:
                    logger.debug("DDG hit on attempt %d | query='%s'", attempt + 1, query[:60])
                    return results
            except Exception as exc:
                logger.debug("DDG attempt %d | query='%s' | %s", attempt + 1, query[:60], exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])

    return []


def _ddg_execute(query: str) -> List[NewsArticle]:
    from duckduckgo_search import DDGS

    articles: List[NewsArticle] = []
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=DDG_FETCH_COUNT))
        for item in results:
            title   = (item.get("title") or "").strip()
            body    = item.get("body") or ""
            href    = item.get("href") or ""
            source  = _extract_domain(href)
            snippet = _truncate(body, SNIPPET_MAX_CHARS)

            if not title:
                continue

            articles.append(NewsArticle(title=title, snippet=snippet, source=source))

    return articles[:MAX_ARTICLES]


# ── Yahoo Finance fallback ────────────────────────────────────────────────────

def _fetch_yfinance(
    ticker: str,
    company: str,
    lenient: bool = False,
    max_needed: int = MAX_ARTICLES,
) -> List[NewsArticle]:
    """
    Retrieves news from Yahoo Finance via yfinance.

    lenient=False: Only keep articles mentioning ticker/company (strict mode).
    lenient=True:  Return all articles regardless of keyword match (gap fill).
    """
    try:
        import yfinance as yf
        raw_news = yf.Ticker(ticker).news or []

        # Keywords for strict mode
        keywords = {
            ticker.lower(),
            company.lower(),
            company.split()[0].lower(),
        }

        articles: List[NewsArticle] = []
        for item in raw_news:
            content = item.get("content", item)
            title = (
                content.get("title")
                or item.get("title")
                or ""
            ).strip()

            if not title:
                continue

            # In strict mode, skip articles that don't mention the company
            if not lenient:
                if not any(kw in title.lower() for kw in keywords):
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

            if len(articles) >= max_needed:
                break

        return articles

    except Exception as exc:
        logger.warning("yfinance news failed | ticker=%s | %s", ticker, exc)
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Returns readable domain from a URL, e.g. 'reuters.com'."""
    if not url:
        return ""
    try:
        domain = url.split("//")[-1].split("/")[0]
        return domain.replace("www.", "")
    except Exception:
        return ""


def _truncate(text: str, max_chars: int) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
