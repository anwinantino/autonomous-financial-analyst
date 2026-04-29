"""
utils/prophet_ml.py — Prophet time-series forecasting utility (FR-003).

Responsibilities:
  1. Fetch historical OHLCV data via yfinance (FR-002).
  2. Reformat data to Prophet's {ds, y} convention.
  3. Load from cache or Train a Prophet model.
  4. Generate a N-day forecast.
  5. Extract trend direction, confidence intervals, and evaluate performance.
"""

import logging
import os
import json
import time
from typing import Dict, Any, Tuple

import yfinance as yf
import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json

from app.models.schemas import PredictResponse, ModelMetrics

logger = logging.getLogger(__name__)

# Cache directory for models
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Cache TTL (24 hours in seconds)
CACHE_TTL = 24 * 60 * 60


# ── Public API ────────────────────────────────────────────────────────────────

def generate_forecast(ticker: str, forecast_days: int = 30) -> PredictResponse:
    """
    Fetches historical data for `ticker` and returns a Prophet forecast.

    Args:
        ticker: Valid yfinance ticker symbol (e.g. "AAPL", "BTC-USD").
        forecast_days: Number of days to forecast ahead (7–90).

    Returns:
        PredictResponse with dates, prices, bounds, trend, current price, and metrics.

    Raises:
        ValueError: If the ticker is not found or has insufficient data.
    """
    raw_df = _fetch_historical_data(ticker)
    prophet_df = _to_prophet_format(raw_df)
    
    # Check cache
    cached_data = _load_cached_model(ticker)
    
    if cached_data:
        logger.info("Using cached model for ticker=%s", ticker)
        model = model_from_json(cached_data["prophet_model"])
        metrics = cached_data["metrics"]
    else:
        logger.info("Training new model for ticker=%s", ticker)
        # Calculate metrics on a holdout set
        metrics = _calculate_metrics(prophet_df)
        
        # Train final model on ALL data
        model = _train_model(prophet_df)
        
        # Save to cache
        _save_cached_model(ticker, model, metrics)

    # Forecast future
    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)
    
    return _build_response(prophet_df, forecast, forecast_days, metrics)


# ── Private helpers ───────────────────────────────────────────────────────────

def _fetch_historical_data(ticker: str) -> pd.DataFrame:
    """Downloads at least 2 years of daily closing prices from yfinance."""
    logger.info("Downloading historical data | ticker=%s", ticker)
    df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)

    if df.empty:
        raise ValueError(f"Ticker '{ticker}' not found or returned no data. Check the spelling.")

    logger.info("Downloaded %d rows for ticker=%s", len(df), ticker)
    return df


def _to_prophet_format(df: pd.DataFrame) -> pd.DataFrame:
    """Converts a yfinance DataFrame to Prophet's expected {ds, y} format."""
    prophet_df = df[["Close"]].copy()
    
    # Handle pandas multi-index which yfinance sometimes returns for single tickers in newer versions
    if isinstance(prophet_df.columns, pd.MultiIndex):
        prophet_df.columns = prophet_df.columns.get_level_values(0)
        
    prophet_df = prophet_df.reset_index()
    prophet_df.columns = ["ds", "y"]
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
    prophet_df = prophet_df.dropna()
    return prophet_df


def _train_model(df: pd.DataFrame) -> Prophet:
    """Trains a Prophet model."""
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(df)
    return model


def _calculate_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calculates MAPE, RMSE, and Directional Accuracy using a 30-day holdout."""
    if len(df) < 60:
        return {"mape": 0.0, "rmse": 0.0, "directional_accuracy": 0.0}
    
    train = df.iloc[:-30]
    test = df.iloc[-30:]
    
    model = _train_model(train)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    
    forecast_test = forecast.tail(30)
    
    y_true = test["y"].values
    y_pred = forecast_test["yhat"].values
    
    mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
    rmse = float(np.sqrt(np.mean((y_true - y_pred)**2)))
    
    # Directional accuracy
    true_diff = np.diff(y_true)
    pred_diff = np.diff(y_pred)
    
    correct_directions = np.sum(np.sign(true_diff) == np.sign(pred_diff))
    da = float(correct_directions / len(true_diff)) if len(true_diff) > 0 else 0.0
    
    return {
        "mape": round(mape, 2),
        "rmse": round(rmse, 2),
        "directional_accuracy": round(da, 2)
    }


def _save_cached_model(ticker: str, model: Prophet, metrics: Dict[str, float]):
    """Serializes the model and metrics to JSON."""
    path = os.path.join(MODELS_DIR, f"{ticker}.json")
    data = {
        "prophet_model": model_to_json(model),
        "metrics": metrics
    }
    try:
        with open(path, "w") as f:
            json.dump(data, f)
        logger.info("Saved cached model to %s", path)
    except Exception as e:
        logger.error("Failed to save model for %s: %s", ticker, e)


def _load_cached_model(ticker: str) -> Dict[str, Any] | None:
    """Loads a cached model if it exists and is less than CACHE_TTL seconds old."""
    path = os.path.join(MODELS_DIR, f"{ticker}.json")
    if not os.path.exists(path):
        return None
        
    file_age = time.time() - os.path.getmtime(path)
    if file_age > CACHE_TTL:
        logger.info("Cached model for %s is stale (age: %.1fh)", ticker, file_age / 3600)
        return None
        
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load cache for %s: %s", ticker, e)
        return None


def _determine_trend(forecast: pd.DataFrame, forecast_days: int) -> str:
    """Compares the last historical close to the final forecasted price."""
    last_historical = forecast["yhat"].iloc[-(forecast_days + 1)]
    last_forecast = forecast["yhat"].iloc[-1]
    delta_pct = (last_forecast - last_historical) / last_historical * 100

    if delta_pct > 1.5:
        return "UP"
    elif delta_pct < -1.5:
        return "DOWN"
    else:
        return "NEUTRAL"


def _build_response(
    historical_df: pd.DataFrame,
    forecast: pd.DataFrame,
    forecast_days: int,
    metrics_dict: Dict[str, float]
) -> PredictResponse:
    """Assembles the PredictResponse."""
    forecast_only = forecast.tail(forecast_days).copy()

    dates = forecast_only["ds"].dt.strftime("%Y-%m-%d").tolist()
    prices = forecast_only["yhat"].round(2).tolist()
    lower_bound = forecast_only["yhat_lower"].round(2).tolist()
    upper_bound = forecast_only["yhat_upper"].round(2).tolist()

    trend = _determine_trend(forecast, forecast_days)
    current_price = round(float(historical_df["y"].iloc[-1]), 2)
    
    metrics = ModelMetrics(
        mape=metrics_dict["mape"],
        rmse=metrics_dict["rmse"],
        directional_accuracy=metrics_dict["directional_accuracy"]
    )

    return PredictResponse(
        dates=dates,
        prices=prices,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        trend=trend,
        current_price=current_price,
        metrics=metrics,
    )
