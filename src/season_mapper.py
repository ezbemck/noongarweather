import pandas as pd

def get_noongar_season(month: int) -> str:
    """Returns the Noongar season based on the calendar month."""
    seasons = {
        1: "Birak", 2: "Bunuru", 3: "Bunuru", 4: "Djeran", 5: "Djeran",
        6: "Makuru", 7: "Makuru", 8: "Djilba", 9: "Djilba",
        10: "Kambarang", 11: "Kambarang", 12: "Birak",
    }
    return seasons.get(month, "Unknown")

def apply_noongar_seasons(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """Appends a 'noongar_season' column to the DataFrame."""
    df_processed = df.copy()
    
    # Ensure the column is a datetime object to safely extract the month
    if date_column not in df_processed.columns:
        raise ValueError(f"Missing date column: {date_column}")

    if not pd.api.types.is_datetime64_any_dtype(df_processed[date_column]):
        df_processed[date_column] = pd.to_datetime(
            df_processed[date_column], errors="coerce"
        )
    if df_processed[date_column].isna().any():
        raise ValueError(f"Invalid date values found in {date_column}")
        
    # Extract the month from the datetime column and apply the mapping
    df_processed["noongar_season"] = df_processed[date_column].dt.month.apply(get_noongar_season)
    
    return df_processed