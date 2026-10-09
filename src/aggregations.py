import pandas as pd

#This app is separated from the other backend pipelines to allow for more complex data processing and analysis of the weather data, which is necessary for the frontend visualizations and seasonal insights.


VALID_SEASONS = {"Birak", "Bunuru", "Djeran", "Makuru", "Djilba", "Kambarang"}

#This function checks if the required columns are present in the DataFrame and prepares it for further analysis. 
# It converts the 'date' column to datetime format and raises an error if any required columns are missing or if there are invalid date values.
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

#This function filters the DataFrame to include only the rows corresponding to the specified Noongar season.
def _season_dataframe(df: pd.DataFrame, season: str) -> pd.DataFrame:
    if season not in VALID_SEASONS:
        raise ValueError(f"Unknown Noongar season: {season}")
    prepared = _prepare_dataframe(df)
    return prepared[prepared["noongar_season"] == season].copy()

#This function calculates the total rainfall for each year within a specific Noongar season.
#Then prepares a clean DataFrame for a Plotly bar chart.
def get_rainfall_trend(df: pd.DataFrame, season: str) -> pd.DataFrame:
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

#This function calculates the average minimum and maximum temperatures for each year within a specific Noongar season.
#It melts the DataFrame into a 'long format' for a Plotly multi-line chart.
def get_temperature_trend(df: pd.DataFrame, season: str) -> pd.DataFrame:
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

#This function calculates quick summary statistics for the frontend metric cards.
def get_season_summary_metrics(df: pd.DataFrame, season: str) -> dict:
    season_df = _season_dataframe(df, season)
    if season_df.empty:
        raise ValueError(f"No weather records found for season: {season}")
    
    # Shift January back by 1 year so Dec/Jan group together as one "season year"
    season_years = season_df["date"].dt.year
    is_january = season_df["date"].dt.month == 1
    season_years = season_years.where(~is_january, season_years - 1)
    
    unique_cycles = season_years.nunique()
    
    return {
        "avg_max_temp": round(season_df["temp_max"].mean(), 1),
        "avg_min_temp": round(season_df["temp_min"].mean(), 1),
        "avg_seasonal_rain": round(season_df["rainfall_mm"].sum() / unique_cycles, 1) if unique_cycles else 0
    }

#This function summarizes hottest/wettest days and mean diurnal range for a period.
#Diurnal range is the difference between the daily maximum and minimum temperatures.
#We use the unrounded mean diurnal range for more accurate calculations, but round the other metrics for display.
def get_period_extremes(df: pd.DataFrame) -> dict:
    period_df = _prepare_dataframe(df)
    if period_df.empty:
        raise ValueError("No weather records found for this period")

    period_df["temp_max"] = pd.to_numeric(period_df["temp_max"], errors="coerce")
    period_df["temp_min"] = pd.to_numeric(period_df["temp_min"], errors="coerce")
    period_df["rainfall_mm"] = pd.to_numeric(period_df["rainfall_mm"], errors="coerce")
    
    # Calculate unrounded average diurnal range
    avg_range = float((period_df["temp_max"] - period_df["temp_min"]).mean())
    
    valid_temperature = period_df.dropna(subset=["temp_max", "temp_min"])
    valid_rainfall = period_df.dropna(subset=["rainfall_mm"])
    if valid_temperature.empty or valid_rainfall.empty:
        raise ValueError("Weather data is missing temperature or rainfall values")

    # Find hottest day
    hottest_idx = valid_temperature["temp_max"].idxmax()
    hottest_row = valid_temperature.loc[hottest_idx]
    hottest_date = pd.Timestamp(hottest_row["date"]).date().isoformat()
    hottest_max = float(hottest_row["temp_max"])

    # Find wettest day
    wettest_idx = valid_rainfall["rainfall_mm"].idxmax()
    wettest_row = valid_rainfall.loc[wettest_idx]
    wettest_date = pd.Timestamp(wettest_row["date"]).date().isoformat()
    wettest_rain = float(wettest_row["rainfall_mm"])

    return {
        "hottest_day_date": hottest_date,
        "hottest_day_temp_max": hottest_max,
        "wettest_day_date": wettest_date,
        "wettest_day_rainfall_mm": wettest_rain,
        "avg_diurnal_range": avg_range,
    }