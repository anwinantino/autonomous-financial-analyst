"""
utils/prophet_ml.py — Prophet time-series forecasting utility (FR-003).

Responsibilities:
  1. Fetch historical OHLCV data via yfinance (FR-002).
  2. Reformat data to Prophet's {ds, y} convention.
  3. Train a Prophet model and generate a N-day forecast.
  4. Extract trend direction and confidence intervals.

This module is intentionally stateless — no caching lives here.
Caching (5-min TTL) will be added as middleware or a cache layer in a later sprint.
"""

import logging
from typing import Dict, Any

import yfinance as yf
import pandas as pd
from prophet import Prophet

from app.models.schemas import PredictResponse

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_forecast(ticker: str, forecast_days: int = 30) -> PredictResponse:
    """
    Fetches historical data for `ticker` and returns a Prophet forecast.

    Args:
        ticker: Valid yfinance ticker symbol (e.g. "AAPL", "BTC-USD").
        forecast_days: Number of days to forecast ahead (7–90).

    Returns:
        PredictResponse with dates, prices, bounds, trend, and current price.

    Raises:
        ValueError: If the ticker is not found or has insufficient data.
    """
    raw_df = _fetch_historical_data(ticker)
    prophet_df = _to_prophet_format(raw_df)
    model, forecast = _train_and_forecast(prophet_df, forecast_days)
    return _build_response(prophet_df, forecast)


# ── Private helpers ───────────────────────────────────────────────────────────

def _fetch_historical_data(ticker: str) -> pd.DataFrame:
    """
    Downloads at least 2 years of daily closing prices from yfinance.
    More historical data improves Prophet's trend/seasonality detection.

    Raises:
        ValueError: If ticker is invalid or returns an empty DataFrame.
    """
    logger.info("Downloading historical data | ticker=%s", ticker)

    # Use 2y to give Prophet enough data for yearly seasonality
    df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)

    if df.empty:
        raise ValueError(f"Ticker '{ticker}' not found or returned no data. Check the spelling.")

    logger.info("Downloaded %d rows for ticker=%s", len(df), ticker)
    return df


def _to_prophet_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a yfinance DataFrame to Prophet's expected {ds, y} format.
    Uses the adjusted closing price as the target variable.
    """
    prophet_df = df[["Close"]].copy()
    prophet_df = prophet_df.reset_index()
    prophet_df.columns = ["ds", "y"]

    # yfinance may return tz-aware timestamps; Prophet requires tz-naive
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
    prophet_df = prophet_df.dropna()

    return prophet_df


def _train_and_forecast(df: pd.DataFrame, forecast_days: int):
    """
    Trains a Prophet model and generates a forward-looking forecast.

    Prophet is configured with:
    - yearly_seasonality: ON  (captures annual stock cycles)
    - weekly_seasonality: ON  (captures Mon–Fri trading patterns)
    - daily_seasonality: OFF  (daily data has no intra-day pattern)
    """
    logger.info("Training Prophet model | rows=%d | horizon=%d days", len(df), forecast_days)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)

    logger.info("Prophet forecast complete | forecast_rows=%d", len(forecast))
    return model, forecast


def _determine_trend(forecast: pd.DataFrame) -> str:
    """
    Compares the last historical close to the final forecasted price
    to determine an UP / DOWN / NEUTRAL trend direction.
    """
    last_historical = forecast["yhat"].iloc[-(30 + 1)]  # last known point
    last_forecast = forecast["yhat"].iloc[-1]            # end of forecast window
    delta_pct = (last_forecast - last_historical) / last_historical * 100

    if delta_pct > 1.5:
        return "UP"
    elif delta_pct < -1.5:
        return "DOWN"
    else:
        return "NEUTRAL"


def _build_response(historical_df: pd.DataFrame, forecast: pd.DataFrame) -> PredictResponse:
    """
    Assembles the PredictResponse from Prophet's forecast DataFrame.
    Only returns the forecast window (future rows), not historical.
    """
    # Keep only the forecast portion (future rows beyond historical data)
    forecast_only = forecast.tail(30).copy()

    dates = forecast_only["ds"].dt.strftime("%Y-%m-%d").tolist()
    prices = forecast_only["yhat"].round(2).tolist()
    lower_bound = forecast_only["yhat_lower"].round(2).tolist()
    upper_bound = forecast_only["yhat_upper"].round(2).tolist()

    trend = _determine_trend(forecast)
    current_price = round(float(historical_df["y"].iloc[-1]), 2)

    return PredictResponse(
        dates=dates,
        prices=prices,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        trend=trend,
        current_price=current_price,
    )
