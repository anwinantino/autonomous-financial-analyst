"""models/schemas.py — Pydantic response schemas for all API endpoints.

Defining schemas here keeps route handlers clean and enables
automatic OpenAPI documentation generation via FastAPI.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ModelMetrics(BaseModel):
    """Performance metrics for the forecasting model."""

    mape: float = Field(..., description="Mean Absolute Percentage Error.")
    rmse: float = Field(..., description="Root Mean Squared Error.")
    directional_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Percentage of correct daily trend predictions."
    )


# ── /predict ─────────────────────────────────────────────────────────────────

class PredictResponse(BaseModel):
    """Response schema for the /predict endpoint (FR-007)."""

    # ── Historical actuals (last 90 days) ─────────────────────────────────
    historical_dates: List[str] = Field(
        ..., description="ISO date strings for the last 90 days of actual closing prices."
    )
    historical_prices: List[float] = Field(
        ..., description="Actual historical closing prices aligned with historical_dates."
    )

    # ── 30-day forecast ───────────────────────────────────────────────────
    dates: List[str] = Field(
        ..., description="ISO date strings for the 30-day forecast window."
    )
    prices: List[float] = Field(
        ..., description="Prophet yhat (predicted closing prices) for forecast window."
    )
    lower_bound: List[float] = Field(
        ..., description="Prophet yhat_lower confidence interval for forecast window."
    )
    upper_bound: List[float] = Field(
        ..., description="Prophet yhat_upper confidence interval for forecast window."
    )

    trend: Literal["UP", "DOWN", "NEUTRAL"] = Field(
        ..., description="Overall 30-day price direction."
    )
    current_price: float = Field(
        ..., description="Most recent historical closing price."
    )
    metrics: ModelMetrics = Field(
        ..., description="Performance evaluation of the model."
    )


# ── /analyze ─────────────────────────────────────────────────────────────────

class NewsArticle(BaseModel):
    """A single news article from DuckDuckGo (FR-004)."""

    title: str
    snippet: str = Field(..., max_length=200)
    source: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Response schema for the /analyze endpoint (FR-008)."""

    news: List[NewsArticle] = Field(..., description="Top 5 relevant news articles.")
    sentiment: Literal["POSITIVE", "NEGATIVE", "NEUTRAL"] = Field(
        ..., description="Gemini-assessed overall news sentiment."
    )
    verdict: Literal["ALIGNED", "CONFLICTING", "UNCERTAIN"] = Field(
        ..., description="Alignment between forecast trend and news sentiment."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Comparator confidence score."
    )
    reasoning: str = Field(
        ..., description="Gemini's natural-language explanation of the verdict."
    )


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx/5xx responses."""

    detail: str
