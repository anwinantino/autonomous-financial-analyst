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

# Base ticker: alphanumeric + hyphen only (no suffix yet — suffix is added by market logic)
TICKER_PATTERN = re.compile(r"^[A-Z0-9\-]{1,12}$")
VALID_MARKETS = {"US", "NSE", "BSE"}


def _resolve_ticker(ticker: str, market: str) -> str:
    """
    Formats the ticker for the target market.

    - US  : returns unchanged; rejects if ticker already has .NS / .BO suffix.
    - NSE : appends .NS if not already present.
    - BSE : appends .BO if not already present.
    """
    if market == "US":
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            raise HTTPException(
                status_code=422,
                detail="Invalid ticker for US market. Remove the .NS/.BO suffix or switch market.",
            )
        return ticker

    if market == "NSE":
        return ticker if ticker.endswith(".NS") else f"{ticker}.NS"

    if market == "BSE":
        return ticker if ticker.endswith(".BO") else f"{ticker}.BO"

    return ticker  # fallback (should never reach here due to Query validation)


@router.get("/predict", response_model=PredictResponse)
async def predict(
    ticker: str = Query(..., description="Stock or crypto ticker, e.g. AAPL, RELIANCE"),
    days: int = Query(30, ge=7, le=90, description="Forecast horizon in days"),
    market: str = Query("US", description="Market: US, NSE, or BSE"),
):
    """
    Fetches historical price data via yfinance, trains a Prophet model,
    and returns the forecast with trend direction and confidence intervals.
    Response time target: < 2 seconds (FR-007).

    market param (optional, default=US):
      - US  : standard US / crypto ticker (e.g. AAPL, BTC-USD)
      - NSE : Indian NSE ticker — .NS suffix applied automatically (e.g. RELIANCE)
      - BSE : Indian BSE ticker — .BO suffix applied automatically (e.g. RELIANCE)
    """
    ticker = ticker.upper().strip()

    # Validate market value
    market = market.upper().strip()
    if market not in VALID_MARKETS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid market '{market}'. Must be one of: US, NSE, BSE.",
        )

    # Validate raw ticker format before suffix is applied
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=422,
            detail="Invalid ticker format. Use alphanumeric characters and hyphens only (e.g. AAPL, BTC-USD).",
        )

    # Apply market-specific suffix / validation
    formatted_ticker = _resolve_ticker(ticker, market)

    logger.info(
        "Received /predict request | ticker=%s | formatted=%s | market=%s | days=%d",
        ticker, formatted_ticker, market, days,
    )

    try:
        result = generate_forecast(ticker=formatted_ticker, forecast_days=days)
        logger.info("Forecast generated successfully | ticker=%s", formatted_ticker)
        return result
    except ValueError as exc:
        logger.warning("Invalid ticker: %s | error=%s", formatted_ticker, exc)
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' not found or not supported in the {market} market.",
        )
    except Exception as exc:
        logger.error("Forecast error | ticker=%s | error=%s", formatted_ticker, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Forecast generation failed. Please try again.")
