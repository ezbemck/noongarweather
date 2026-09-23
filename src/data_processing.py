import pandas as pd
from pathlib import Path

try:
    from .season_mapper import apply_noongar_seasons
except ImportError:
    from season_mapper import apply_noongar_seasons

# Define relative paths so the script works anywhere
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

def load_bom_csv(filepath: Path, value_col_name: str, new_col_name: str) -> pd.DataFrame:
    """Extracts dates and specific weather metrics from a raw BoM CSV."""
    if not filepath.exists():
        raise FileNotFoundError(f"Missing file: {filepath}. Check if it is in data/raw/.")

    df = pd.read_csv(filepath)

    required_date_columns = {"Year", "Month", "Day"}
    missing_date_columns = required_date_columns.difference(df.columns)
    if missing_date_columns:
        raise ValueError(
            f"Missing date columns in {filepath.name}: {sorted(missing_date_columns)}"
        )

    # Combine BoM's split columns into one validated datetime column.
    date_parts = df[["Year", "Month", "Day"]].apply(pd.to_numeric, errors="coerce")
    df["date"] = pd.to_datetime(date_parts, errors="coerce")
    if df["date"].isna().any():
        raise ValueError(f"Invalid date values found in {filepath.name}")

    # Dynamically find the target metric column (ignoring BoM's varying metadata headers)
    target_cols = [col for col in df.columns if value_col_name.lower() in col.lower()]
    if not target_cols:
        raise ValueError(f"Could not find '{value_col_name}' in {filepath.name}")
    
    target_col = target_cols[0]

    # Filter down to just the date and the target metric, then rename for the frontend
    df_clean = df[["date", target_col]].copy()
    df_clean.rename(columns={target_col: new_col_name}, inplace=True)
    df_clean[new_col_name] = pd.to_numeric(df_clean[new_col_name], errors="coerce")
    df_clean = df_clean.drop_duplicates(subset="date", keep="last")
    
    return df_clean

def run_pipeline():
    print("1. Loading raw BoM datasets...")
    df_max = load_bom_csv(RAW_DIR / "max_temp.csv", "Maximum temperature", "temp_max")
    df_min = load_bom_csv(RAW_DIR / "min_temp.csv", "Minimum temperature", "temp_min")
    df_rain = load_bom_csv(RAW_DIR / "rainfall.csv", "Rainfall amount", "rainfall_mm")

    print("2. Merging datasets chronologically...")
    df_merged = pd.merge(df_max, df_min, on="date", how="outer")
    df_merged = pd.merge(df_merged, df_rain, on="date", how="outer")

    print("3. Cleaning missing values...")
    # BoM uses blank rainfall values for days with no recorded rainfall.
    df_merged["rainfall_mm"] = df_merged["rainfall_mm"].fillna(0.0)
    # Drop rows where temperature sensors failed entirely
    df_merged = df_merged.dropna(subset=["temp_max", "temp_min"])

    print("4. Applying Noongar seasons mapping...")
    df_final = apply_noongar_seasons(df_merged, date_column="date")
    
    # Calculate daily average for frontend graphing
    df_final["temp_avg"] = ((df_final["temp_max"] + df_final["temp_min"]) / 2).round(1)
    df_final = df_final.sort_values("date").reset_index(drop=True)

    print("5. Exporting processed data...")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "weather_processed_final.csv"
    df_final.to_csv(output_path, index=False)
    
    print(f"Pipeline complete! {len(df_final)} records saved to {output_path}")

if __name__ == "__main__":
    run_pipeline()