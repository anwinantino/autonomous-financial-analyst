import os
import json
import logging
import asyncio
import google.generativeai as genai
from typing import List
from app.models.schemas import NewsArticle

logger = logging.getLogger(__name__)

# Initialize Gemini
API_KEY = os.getenv("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. Gemini integration will fail.")

# We use Gemini 2.0 Flash for speed
MODEL_NAME = "gemini-2.0-flash"
TIMEOUT_SECONDS = 5.0

async def analyze_sentiment(ticker: str, trend: str, news: List[NewsArticle]) -> dict:
    """
    Analyzes news sentiment using Gemini and compares it to the ML trend.
    Returns a dict matching AnalyzeResponse schema components.
    
    Includes a hard 5-second timeout and graceful degradation if the API fails.
    """
    if not API_KEY:
        logger.error("Skipping Gemini analysis: GEMINI_API_KEY not set.")
        return _fallback_response("API key missing.")

    if not news:
        return _fallback_response("No news articles found to analyze.")

    news_text = "\n\n".join(
        [f"Headline: {n.title}\nSnippet: {n.snippet}" for n in news]
    )

    prompt = f"""
    You are an expert financial analyst. A machine learning model has predicted that the price trend for {ticker} over the next 30 days will be {trend}.
    
    Here are the latest news snippets for {ticker}:
    {news_text}
    
    Based ONLY on the provided news, determine if the current sentiment is ALIGNED, CONFLICTING, or UNCERTAIN with the ML prediction trend ({trend}).
    
    Return your response STRICTLY as a JSON object (do not include markdown formatting):
    {{
        "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
        "verdict": "ALIGNED" | "CONFLICTING" | "UNCERTAIN",
        "summary": "1-2 sentence summary of the news",
        "reasoning": "1-2 sentence explanation of your verdict",
        "confidence": 0.85
    }}
    """
    
    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        # Run synchronous generate_content in a thread to allow asyncio timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=TIMEOUT_SECONDS
        )
        
        # Parse response
        result = json.loads(response.text)
        
        # Ensure schema fields exist
        return {
            "sentiment": result.get("sentiment", "NEUTRAL"),
            "verdict": result.get("verdict", "UNCERTAIN"),
            "summary": result.get("summary", "Analysis complete."),
            "reasoning": result.get("reasoning", "LLM processed successfully."),
            "confidence": float(result.get("confidence", 0.5))
        }
        
    except asyncio.TimeoutError:
        logger.error("Gemini analysis timed out after %s seconds for %s", TIMEOUT_SECONDS, ticker)
        return _fallback_response("LLM analysis timed out.")
    except json.JSONDecodeError:
        logger.error("Failed to parse Gemini response as JSON for %s", ticker)
        return _fallback_response("LLM returned malformed response.")
    except Exception as e:
        logger.error("Gemini analysis failed for %s: %s", ticker, e)
        return _fallback_response(f"LLM analysis failed: {str(e)}")

def _fallback_response(reason: str) -> dict:
    """Returns a safe fallback response if Gemini fails or times out."""
    return {
        "sentiment": "NEUTRAL",
        "verdict": "UNCERTAIN",
        "summary": "News analysis is currently unavailable.",
        "reasoning": reason,
        "confidence": 0.0
    }
