import pandas as pd
from pathlib import Path

#The purpose of this app within the backend pipeline is to process raw weather data from the Bureau of Meteorology (BoM) and prepare it for frontend visualization.
#Within the backend chain, this app ensures that the data is cleaned, merged, and enriched with Noongar seasonal information, making it suitable for analysis and display in the frontend application.
#This block attempts to import the apply_noongar_seasons function from the season_mapper module.
try:
    from .season_mapper import apply_noongar_seasons
except ImportError:
    from season_mapper import apply_noongar_seasons

# Define relative paths so the script works anywhere.
#This is important because the script may be run from different working directories, and we want to ensure that the data files are always found correctly.
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

#This function will load a raw BoM CSV file, extract the date and a specific weather metric, and return a cleaned DataFrame.
def load_bom_csv(filepath: Path, value_col_name: str, new_col_name: str) -> pd.DataFrame:
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

#This run pipeline function will execute the entire data processing workflow, from loading raw datasets to exporting the final processed CSV.
#It is designed to be run as a standalone script, ensuring that all steps are completed in sequence and that the final output is ready for frontend use.
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

    print("4. Applying Noongar seasons mapping...")
    df_final = apply_noongar_seasons(df_merged, date_column="date")
    
    # Calculate daily average for frontend graphing
    df_final["temp_avg"] = df_final[["temp_max", "temp_min"]].mean(axis=1).round(1)
    df_final = df_final.sort_values("date").reset_index(drop=True)

    print("5. Exporting processed data...")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "weather_processed_final.csv"
    df_final.to_csv(output_path, index=False)
    
    print(f"Pipeline complete! {len(df_final)} records saved to {output_path}")

#this function will execute the run_pipeline function if the script is run directly, allowing for easy testing and execution of the data processing workflow within VSCODE.
if __name__ == "__main__":
    run_pipeline()