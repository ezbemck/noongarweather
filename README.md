# ☀️ Noongar Weather

An interactive, educational web application designed for primary school to tertiary level students to explore Perth's weather through the lens of the six Noongar seasons. 

**[This project is live - you can play with the live app here](https://noongarweather.streamlit.app/)**

## 📖 About the Project
This project bridges meteorological data with traditional Indigenous ecological knowledge. It uses over 30 years of daily weather observations to help students understand how temperature and rainfall align with the environmental indicators of the Noongar calendar: **Birak, Bunuru, Djeran, Makuru, Djilba, and Kambarang**.

### ✨ Key Features
*   **Live Perth Weather:** Real-time temperature and weather conditions fetched via the Open-Meteo API.
*   **Birthday Explorer:** Students can input their birthday to discover their Noongar season, the exact weather on the day they were born, and the native flower associated with that time of year.
*   **Interactive Climate Charts:** Custom Plotly bar and line charts allowing users to filter historical data (1993–2026) by year and season to compare temperatures and cumulative rainfall.
*   **Learn About the Seasons:** An interactive, animated season wheel that dynamically re-themes the page and displays curated, touch-friendly photo cards of seasonal flora and fauna.
*   **Cultural Context:** Integrated "Did you know?" facts, seasonal signs, and traditional food sources.

## 📊 Data & Cultural Sources
*   **Weather Data:** Historical daily maximum temperature, minimum temperature, and rainfall records (1993–2026) sourced from the **Bureau of Meteorology (BoM)** — Perth Metro Station (009225).
*   **Live Weather:** Current conditions provided by the **Open-Meteo API**.
*   **Cultural Knowledge:** Seasonal definitions, translations, and environmental indicators sourced from the **BoM Indigenous Weather Knowledge** portal, the **Noongar Boodjar Language Centre**, and the **South West Aboriginal Land and Sea Council (SWALSC)**.
*   **Images:** All plant and animal photography is sourced from **Wikimedia Commons** under Creative Commons licenses (full credits listed in the app's About tab).

## 🛠️ Tech Stack
*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **Data Processing & Aggregation:** Pandas, NumPy
*   **Data Visualization:** Plotly Graph Objects & Plotly Express
*   **Styling:** Custom CSS with fluid typography (Google Fonts: Fredoka, Baloo 2, Nunito)

## 🚀 Getting Started

To run this project locally on your own machine:

### 1. Clone the repository
```bash
git clone [https://github.com/ezbemck/noongarweather.git](https://github.com/ezbemck/noongarweather.git)
cd noongarweather

### 2. Set up a virtual environment (Optional but recommended)

python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Now run the app!

streamlit run app.py


Repository Structure

    app.py: The main Streamlit frontend application and view router.

    src/data_processing.py: Offline pipeline to merge, clean, and map raw BoM CSVs.

    src/season_mapper.py: Logic for mapping calendar months to Noongar seasons.

    src/weather_service.py: Cached data loading and external API fetching.

    src/aggregations.py: Statistical computations (diurnal ranges, extremes).

    data/: Contains raw CSVs, the cleaned weather_processed_final.csv, and JSON metadata (seasons.json, species_info.json).

    assets/: Local image files for the flora and fauna photo gallery.

Built as an educational project.