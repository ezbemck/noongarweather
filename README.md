# Noongar Weather

Backend data pipeline for an interactive app mapping Perth weather with the six
Noongar seasons.

## Backend setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/data_processing.py
```

The pipeline reads the BoM files in `data/raw/` and writes the clean dataset to
`data/processed/weather_processed_final.csv`.

## Backend modules

- `src/data_processing.py` loads, validates, cleans, merges, and exports data.
- `src/season_mapper.py` assigns the six Noongar seasons by month.
- `src/aggregations.py` prepares rainfall, temperature, and summary metrics for Plotly.
- `src/weather_service.py` provides current-weather, historical-filter, and season-dashboard queries for the frontend.

## Frontend handoff

The backend is committed on `main`. Your teammate can now run:

```bash
git pull origin main
pip install -r requirements.txt
```

They will receive `weather_processed_final.csv`, the aggregation functions,
the service layer, and the `.gitignore` rules. They can import the service
functions from `src.weather_service` while building the Streamlit UI.
