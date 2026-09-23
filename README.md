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
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

They will receive `weather_processed_final.csv`, the aggregation functions,
the service layer, and the `.gitignore` rules. They can import the service
functions from `src.weather_service` while building the Streamlit UI.

## Frontend development brief

The frontend should be built as a Streamlit app. Start it from the repository
root with:

```bash
streamlit run app.py
```

Create `app.py` as the main entry point. Import the backend with:

```python
from src.weather_service import (
	 filter_historical_weather,
	 get_current_weather,
	 get_season_dashboard,
	 load_processed_data,
)
```

### Screens and navigation

Use a clear sidebar or top navigation control with these views:

1. **Home**: show the latest available weather record, current Noongar season,
	temperature cards, rainfall, and a short seasonal description.
2. **Past Data**: let users select a start date, end date, and Noongar season.
	Display the filtered records alongside rainfall and temperature charts.
3. **Info**: explain the six Noongar seasons, their month ranges, and the
	environmental characteristics associated with each season. Keep cultural
	information respectful and cite the source used for the descriptions.
4. **Unsure?**: provide a simple guided selector or search box that helps a
	user find a season from a date, weather condition, or question.

Use buttons for clear actions such as `Apply filters`, `Reset`, and `Back to
home`. Use dropdowns for season choices and date inputs for date ranges. Show
an empty-state message when a filter returns no records, and validate that the
start date is not later than the end date.

### Cards and graphs

- Keep weather cards compact and consistent: date, season, maximum temperature,
  minimum temperature, average temperature, and rainfall.
- Use Plotly for the historical views. Use a line chart for yearly minimum and
  maximum temperatures and a bar chart for total rainfall by year.
- Label axes with units: `Temperature (C)` and `Total Rainfall (mm)`.
- Include tooltips, readable legends, and a visible selected-season label.
- Avoid showing raw technical column names to users.

### Season visual system

Use the selected season as the visual accent for the page, cards, buttons, and
chart highlights. These are interface palette suggestions rather than official
cultural colour definitions:

| Season | Months | Suggested accent |
| --- | --- | --- |
| Birak | December-January | warm red and ochre |
| Bunuru | February-March | golden yellow and turquoise |
| Djeran | April-May | muted coral and soft green |
| Makuru | June-July | deep blue and cool grey |
| Djilba | August-September | fresh green and blue |
| Kambarang | October-November | bright yellow and orange |

Keep text contrast accessible, use a neutral background, and do not rely on
colour alone to communicate the season. Include the season name and an icon or
text label beside coloured accents. Keep layouts responsive so cards and charts
stack cleanly on smaller screens.

### Suggested frontend workflow

1. Load the processed data once near the top of `app.py`.
2. Build navigation and the Home view first.
3. Add Past Data controls using `filter_historical_weather()`.
4. Add charts using `get_season_dashboard()` and Plotly.
5. Add the Info and Unsure? views with sourced seasonal content.
6. Test every screen with all six seasons, an empty filter result, and a mobile
	width before merging.
