"""Frontend-facing queries over the processed weather dataset."""

from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from .aggregations import get_rainfall_trend, get_season_summary_metrics, get_temperature_trend
except ImportError:
    from aggregations import get_rainfall_trend, get_season_summary_metrics, get_temperature_trend

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "weather_processed_final.csv"

@st.cache_data(ttl=3600, show_spinner="Loading processed weather data...")
def load_processed_data(path: Path = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Load the processed dataset and normalize its date column."""
    if not path.exists():
        raise FileNotFoundError(f"Processed weather data not found: {path}")

    data = pd.read_csv(path, parse_dates=["date"])
    if data.empty:
        raise ValueError("Processed weather data is empty")
    return data.sort_values("date").reset_index(drop=True)


def filter_historical_weather(
    data: pd.DataFrame,
    start_date: str | None = None,
    end_date: str | None = None,
    season: str | None = None,
) -> pd.DataFrame:
    """Filter weather records by inclusive dates and optionally by season."""
    filtered = data.copy()
    filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")
    if filtered["date"].isna().any():
        raise ValueError("Invalid date values found in weather data")

    if start_date:
        start = pd.to_datetime(start_date, errors="coerce")
        if pd.isna(start):
            raise ValueError(f"Invalid start_date: {start_date}")
        filtered = filtered[filtered["date"] >= start]

    if end_date:
        end = pd.to_datetime(end_date, errors="coerce")
        if pd.isna(end):
            raise ValueError(f"Invalid end_date: {end_date}")
        filtered = filtered[filtered["date"] <= end]

    if start_date and end_date and start > end:
        raise ValueError("start_date must be on or before end_date")

    if season:
        filtered = filtered[filtered["noongar_season"] == season]

    return filtered.reset_index(drop=True)


def get_current_weather(data: pd.DataFrame) -> dict:
    """Return the most recent processed weather record as a JSON-friendly dict."""
    if data.empty:
        raise ValueError("Weather data is empty")
    
    # Strictly drop rows with missing temperatures FIRST
    valid_data = data.dropna(subset=["temp_max", "temp_min"]).copy()
    if valid_data.empty:
        valid_data = data
        
    latest = valid_data.sort_values("date").iloc[-1].copy()
    latest["date"] = pd.Timestamp(latest["date"]).date().isoformat()
    return latest.to_dict()
