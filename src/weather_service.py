"""Frontend-facing queries over the processed weather dataset."""

from pathlib import Path

import pandas as pd

try:
    from .aggregations import get_rainfall_trend, get_season_summary_metrics, get_temperature_trend
except ImportError:
    from aggregations import get_rainfall_trend, get_season_summary_metrics, get_temperature_trend

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "weather_processed_final.csv"


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
    latest = data.sort_values("date").iloc[-1].copy()
    latest["date"] = pd.Timestamp(latest["date"]).date().isoformat()
    return latest.to_dict()


def get_season_dashboard(data: pd.DataFrame, season: str) -> dict:
    """Return metrics and chart data needed for a season comparison view."""
    return {
        "season": season,
        "summary": get_season_summary_metrics(data, season),
        "rainfall_trend": get_rainfall_trend(data, season).to_dict("records"),
        "temperature_trend": get_temperature_trend(data, season).to_dict("records"),
    }