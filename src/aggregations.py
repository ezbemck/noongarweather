import pandas as pd

VALID_SEASONS = {"Birak", "Bunuru", "Djeran", "Makuru", "Djilba", "Kambarang"}


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"date", "noongar_season", "temp_min", "temp_max", "rainfall_mm"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    prepared = df.copy()
    prepared["date"] = pd.to_datetime(prepared["date"], errors="coerce")
    if prepared["date"].isna().any():
        raise ValueError("Invalid date values found in weather data")
    return prepared


def _season_dataframe(df: pd.DataFrame, season: str) -> pd.DataFrame:
    if season not in VALID_SEASONS:
        raise ValueError(f"Unknown Noongar season: {season}")
    prepared = _prepare_dataframe(df)
    return prepared[prepared["noongar_season"] == season].copy()

def get_rainfall_trend(df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Calculates total rainfall per year for a specific Noongar season.
    Prepares a clean DataFrame for a Plotly bar chart.
    """
    # 1. Filter to the requested season
    season_df = _season_dataframe(df, season)
    
    # 2. Extract the year from the date column for grouping
    season_df["year"] = pd.to_datetime(season_df["date"]).dt.year
    
    # 3. Group by year and sum the rainfall
    yearly_rain = season_df.groupby("year")["rainfall_mm"].sum().reset_index()
    
    # 4. Rename columns so Plotly automatically labels the axes
    yearly_rain.rename(columns={
        "year": "Year", 
        "rainfall_mm": "Total Rainfall (mm)"
    }, inplace=True)
    
    return yearly_rain

def get_temperature_trend(df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Calculates average min and max temperatures per year for a specific season.
    Melts the DataFrame into a 'long format' for a Plotly multi-line chart.
    """
    season_df = _season_dataframe(df, season)
    season_df["year"] = pd.to_datetime(season_df["date"]).dt.year
    
    # Get average min and max temp per year
    yearly_temp = season_df.groupby("year")[["temp_min", "temp_max"]].mean().reset_index()
    
    # 'Melt' the data: compresses min and max into a single column so Plotly can color-code them
    melted_df = pd.melt(
        yearly_temp, 
        id_vars=["year"], 
        value_vars=["temp_min", "temp_max"],
        var_name="Measurement", 
        value_name="Temperature (°C)"
    )
    
    # Clean up the labels for the frontend legend
    melted_df["Measurement"] = melted_df["Measurement"].map({
        "temp_min": "Minimum Temp", 
        "temp_max": "Maximum Temp"
    })
    melted_df.rename(columns={"year": "Year"}, inplace=True)
    
    # Sort chronologically so the line chart draws left-to-right correctly
    melted_df.sort_values("Year", inplace=True)
    
    return melted_df

def get_season_summary_metrics(df: pd.DataFrame, season: str) -> dict:
    """
    Calculates quick summary statistics for the frontend metric cards.
    """
    season_df = _season_dataframe(df, season)
    if season_df.empty:
        raise ValueError(f"No weather records found for season: {season}")
    
    return {
        "avg_max_temp": round(season_df["temp_max"].mean(), 1),
        "avg_min_temp": round(season_df["temp_min"].mean(), 1),
        # Total rainfall divided by number of unique years to get average seasonal rainfall
        "avg_seasonal_rain": round(season_df["rainfall_mm"].sum() / season_df["date"].dt.year.nunique(), 1)
    }


def get_period_extremes(df: pd.DataFrame) -> dict:
    """Summarize hottest/wettest days and mean diurnal range for a period."""
    period_df = _prepare_dataframe(df)
    if period_df.empty:
        raise ValueError("No weather records found for this period")

    period_df["temp_max"] = pd.to_numeric(period_df["temp_max"], errors="coerce")
    period_df["temp_min"] = pd.to_numeric(period_df["temp_min"], errors="coerce")
    period_df["rainfall_mm"] = pd.to_numeric(period_df["rainfall_mm"], errors="coerce")

    valid_temperature = period_df.dropna(subset=["temp_max", "temp_min"])
    valid_rainfall = period_df.dropna(subset=["rainfall_mm"])
    if valid_temperature.empty or valid_rainfall.empty:
        raise ValueError("Weather data is missing temperature or rainfall values")

    hottest = valid_temperature.loc[valid_temperature["temp_max"].idxmax()]
    wettest = valid_rainfall.loc[valid_rainfall["rainfall_mm"].idxmax()]
    daily_range = valid_temperature["temp_max"] - valid_temperature["temp_min"]

    return {
        "hottest_day_date": hottest["date"].strftime("%Y-%m-%d"),
        "hottest_day_temp_max": round(float(hottest["temp_max"]), 1),
        "wettest_day_date": wettest["date"].strftime("%Y-%m-%d"),
        "wettest_day_rainfall_mm": round(float(wettest["rainfall_mm"]), 1),
        "avg_diurnal_range": round(float(daily_range.mean()), 1),
    }