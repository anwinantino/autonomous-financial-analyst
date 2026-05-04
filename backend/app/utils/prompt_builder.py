"""
utils/prompt_builder.py — Shared LLM prompt templates.

Single source of truth for all LLM prompts used across providers
(Gemini, Ollama, or any future provider).

Both gemini_provider.py and ollama_provider.py import from here,
ensuring the analysis logic and output schema stay consistent
regardless of which LLM is active.
"""

from typing import List
from app.models.schemas import NewsArticle


# ── Constants ─────────────────────────────────────────────────────────────────

VALID_SENTIMENTS = {"POSITIVE", "NEGATIVE", "NEUTRAL"}
VALID_VERDICTS   = {"ALIGNED", "CONFLICTING", "UNCERTAIN"}

# System-level instruction used across all providers that support it
SYSTEM_INSTRUCTION = (
    "You are a senior financial analyst. "
    "You MUST respond ONLY with a single valid JSON object. "
    "Do NOT include any explanation, markdown, or text outside the JSON."
)


# ── Public builders ───────────────────────────────────────────────────────────

def build_analysis_prompt(
    ticker: str,
    trend: str,
    news: List[NewsArticle],
) -> str:
    """
    Builds the core analysis prompt shared by all LLM providers.

    The prompt instructs the LLM to:
      1. Assess overall news sentiment (POSITIVE / NEGATIVE / NEUTRAL).
      2. Compare that sentiment against the ML model's 30-day price trend.
      3. Return a dynamic confidence score (not fixed) based on signal clarity.
      4. Provide a 2-3 sentence reasoning that references BOTH news AND the trend.

    Args:
        ticker : Stock / crypto ticker (e.g. "TSLA").
        trend  : ML forecast direction — "UP", "DOWN", or "NEUTRAL".
        news   : List of NewsArticle objects to be analysed.

    Returns:
        A formatted prompt string ready to be sent to any LLM.
    """
    news_text = "\n\n".join(
        [f"Headline: {a.title}\nSnippet: {a.snippet}" for a in news]
    )

    return f"""You are a senior financial analyst. Perform a two-part analysis for the stock ticker {ticker}.

--- PART 1: News Sentiment ---
Read the latest news articles below and determine the overall sentiment:
- POSITIVE  → News reflects optimism, growth, or bullish signals
- NEGATIVE  → News reflects pessimism, risk, or bearish signals
- NEUTRAL   → News is mixed, ambiguous, or not financially meaningful

--- PART 2: Alignment with ML Prediction ---
A machine learning model has predicted the 30-day price trend for {ticker} will be: {trend.upper()}

Determine if the news sentiment ALIGNS or CONFLICTS with this ML prediction:
- ALIGNED      → Sentiment supports the ML trend (e.g. POSITIVE news + UP trend)
- CONFLICTING  → Sentiment contradicts the ML trend (e.g. POSITIVE news + DOWN trend)
- UNCERTAIN    → News is too ambiguous or mixed to support either verdict

--- Confidence Score (MUST be dynamic — do NOT always return 0.4 or 0.5) ---
Rate your confidence from 0.0 to 1.0 based on signal clarity:
- 0.85–1.00 : Very clear, unanimous signal strongly aligned with or against the trend
- 0.65–0.84 : Mostly clear with only minor ambiguity
- 0.45–0.64 : Mixed signals, moderate certainty
- 0.20–0.44 : Very ambiguous, sparse, or contradictory news

--- News Articles for {ticker} ---
{news_text}

--- Required Output ---
Return ONLY a valid JSON object with NO markdown, NO code fences, NO extra text:
{{
    "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
    "verdict": "ALIGNED" | "CONFLICTING" | "UNCERTAIN",
    "reasoning": "2-3 sentences referencing specific news AND the ML trend of {trend.upper()}",
    "confidence": <float between 0.0 and 1.0>
}}"""
