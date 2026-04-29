"""
routes/predict.py — GET /predict endpoint (FR-007).

Returns a 30-day Prophet forecast for the given ticker.
The data pipeline and model logic live in app/utils/prophet_ml.py
to keep this router thin and single-responsibility.
"""

import logging
import re

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import PredictResponse
from app.utils.prophet_ml import generate_forecast

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Predict"])

# Ticker must be alphanumeric + hyphen only (e.g. AAPL, BTC-USD)
TICKER_PATTERN = re.compile(r"^[A-Z0-9\-]{1,12}$")


@router.get("/predict", response_model=PredictResponse)
async def predict(
    ticker: str = Query(..., description="Stock or crypto ticker, e.g. AAPL or BTC-USD"),
    days: int = Query(30, ge=7, le=90, description="Forecast horizon in days"),
):
    """
    Fetches historical price data via yfinance, trains a Prophet model,
    and returns the forecast with trend direction and confidence intervals.
    Response time target: < 2 seconds (FR-007).
    """
    # Sanitize ticker — reject anything that isn't uppercase alphanumeric + hyphen
    ticker = ticker.upper().strip()
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=422,
            detail="Invalid ticker format. Use alphanumeric characters and hyphens only (e.g. AAPL, BTC-USD).",
        )

    logger.info("Received /predict request | ticker=%s | days=%d", ticker, days)

    try:
        result = generate_forecast(ticker=ticker, forecast_days=days)
        logger.info("Forecast generated successfully | ticker=%s", ticker)
        return result
    except ValueError as exc:
        # Raised by prophet_ml when ticker is not found in yfinance
        logger.warning("Invalid ticker: %s | error=%s", ticker, exc)
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Forecast error | ticker=%s | error=%s", ticker, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Forecast generation failed. Please try again.")
