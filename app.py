import streamlit as st # this is the streamlit library that is being used to create the web app
import plotly.express as px # this is the plotly library that is being used to create the graphs
import plotly.graph_objects as go
import math
import json
import pandas as pd
import requests
import base64
from pathlib import Path
from html import escape
from datetime import date as calendar_date, datetime
from zoneinfo import ZoneInfo
from plotly.subplots import make_subplots

from src.aggregations import get_period_extremes
from src.season_mapper import get_noongar_season
from src.weather_service import (
    filter_historical_weather,
    get_current_weather,
    get_season_dashboard,
    load_processed_data,
)

data = load_processed_data()
DATA_MIN_DATE = data["date"].min()
DATA_MAX_DATE = data["date"].max()
DATA_MIN_YEAR = int(DATA_MIN_DATE.year)
DATA_MAX_YEAR = int(DATA_MAX_DATE.year)
DEFAULT_YEAR_RANGE = (max(DATA_MIN_YEAR, DATA_MAX_YEAR - 4), DATA_MAX_YEAR)
SEASONS_PATH = Path(__file__).resolve().parent / "data" / "seasons.json"
with SEASONS_PATH.open(encoding="utf-8") as seasons_file:
    season_data = json.load(seasons_file)
SPECIES_INFO_PATH = Path(__file__).resolve().parent / "data" / "species_info.json"
with SPECIES_INFO_PATH.open(encoding="utf-8") as species_file:
    species_info = json.load(species_file)

CULTURAL_ACKNOWLEDGEMENT = (
    "The six-season knowledge belongs to Noongar people as its custodians. "
    "This app presents a general educational overview for a primary-school audience. "
    "For the fuller depth of this knowledge, please go to the Noongar Boodjar "
    "Language Centre, SWALSC, or other Noongar community sources directly."
)

st.set_page_config(
    page_title="Noongar Weather",
    page_icon="🌿",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;500;600;700;800&display=swap');

    :root {
        --terracotta: #B8623F;
        --deep-teal: #2F6F6E;
        --ochre: #D9A441;
        --sage: #7C9070;
        --warm-charcoal: #2B2420;
        --warm-cream: #F7F1E8;
        --season-accent: #7C9070;
    }

    .stApp {
        background: var(--warm-cream);
        color: var(--warm-charcoal);
        font-family: 'Nunito', sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp [data-testid="stMetricValue"] {
        color: var(--terracotta) !important;
        font-family: 'Baloo 2', sans-serif !important;
        font-weight: 700;
        text-align: center;
    }
    h1, h2, h3, p, [data-testid="stMetricLabel"] { text-align: center; }
    p, label, li, [data-testid="stCaptionContainer"] {
        color: var(--warm-charcoal);
        font-family: 'Nunito', sans-serif;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: var(--deep-teal);
        font-family: 'Baloo 2', sans-serif;
        font-size: 1.1rem;
        border-radius: 14px 14px 0 0;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--terracotta);
        border-bottom: 4px solid var(--terracotta);
    }
    button[kind="primary"] {
        background: var(--terracotta) !important;
        border-color: var(--terracotta) !important;
        color: white !important;
        border-radius: 16px;
        font-family: 'Nunito', sans-serif;
        font-weight: 800;
    }
    button[kind="secondary"] {
        background: #FFF9F1 !important;
        color: var(--deep-teal) !important;
        border-color: var(--deep-teal) !important;
        border-radius: 16px;
        font-family: 'Nunito', sans-serif;
        font-weight: 800;
    }
    [data-testid="stBaseButton-primary"] {
        background: var(--terracotta) !important;
        border-color: var(--terracotta) !important;
        color: #FFFFFF !important;
    }
    [data-testid="stBaseButton-secondary"] {
        background: #FFF9F1 !important;
        border-color: var(--deep-teal) !important;
        color: var(--deep-teal) !important;
    }
    [data-testid="stMetric"] {
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: color-mix(in srgb, var(--season-accent) 16%, white);
        border: 2px solid color-mix(in srgb, var(--season-accent) 40%, white);
        border-radius: 20px;
        padding: 20px 14px;
        box-shadow: 0 8px 20px rgba(43, 36, 32, 0.09);
        text-align: center;
    }
    [data-testid="stMetricValue"] { font-size: 2rem; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(43, 36, 32, 0.08);
    }
    [data-testid="stImage"] img {
        width: 100% !important;
        height: 160px !important;
        object-fit: cover !important;
        object-position: center center !important;
        border-radius: 14px;
        transition: transform 180ms ease, box-shadow 180ms ease;
    }
    [data-testid="stImage"] img:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 10px 20px rgba(43, 36, 32, 0.16);
    }
    .species-photo-card {
        display: block;
        position: relative;
        aspect-ratio: 4 / 3;
        overflow: hidden;
        border: 3px solid var(--card-accent);
        border-radius: 20px;
        background: #FFF9F1;
        box-shadow: 0 8px 20px rgba(43,36,32,.1);
    }
    .species-photo-card summary {
        display: block;
        width: 100%;
        height: 100%;
        cursor: pointer;
        list-style: none;
        position: relative;
    }
    .species-photo-card summary::-webkit-details-marker { display: none; }
    .species-photo-card img, .species-placeholder {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center center;
    }
    .species-placeholder {
        display: grid;
        place-items: center;
        background: color-mix(in srgb, var(--card-accent) 16%, white);
        font-size: 4rem;
    }
    .species-category-badge {
        position: absolute;
        left: 12px;
        top: 12px;
        z-index: 1;
        border-radius: 999px;
        background: #FFF9F1;
        color: #2B2420;
        padding: 6px 12px;
        font-size: .9rem;
        font-weight: 800;
        box-shadow: 0 3px 10px rgba(43,36,32,.16);
    }
    .species-overlay {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 8px;
        overflow-y: auto;
        padding: 20px;
        background: rgba(43,36,32,.88);
        color: #FFFFFF;
        opacity: 0;
        transform: translateY(12px);
        transition: opacity 220ms ease, transform 220ms ease;
    }
    .species-overlay p { color: #FFFFFF; margin: 0; text-align: left; }
    .species-photo-card:hover .species-overlay,
    .species-photo-card:focus-within .species-overlay,
    .species-photo-card[open] .species-overlay {
        opacity: 1;
        transform: translateY(0);
    }
    .species-tap-hint { font-size: .8rem; opacity: .8; }
    .species-card-title { font-size: 1.1rem; font-weight: 800; margin: 8px 0 20px; }
    .stApp [role="radiogroup"] {
        justify-content: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .stApp [role="radiogroup"] [role="radio"] {
        background: #FFF9F1 !important;
        border: 2px solid #D9A441 !important;
        border-radius: 999px;
        color: #2F6F6E !important;
        font-family: 'Nunito', sans-serif;
        font-weight: 800;
    }
    .stApp [role="radiogroup"] [role="radio"][aria-checked="true"] {
        background: #B8623F !important;
        border-color: #B8623F !important;
        color: white !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]),
    [data-testid="stVerticalBlockBorderWrapper"]:has(.season-photo-placeholder) {
        transition: transform 180ms ease, box-shadow 180ms ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]):hover,
    [data-testid="stVerticalBlockBorderWrapper"]:has(.season-photo-placeholder):hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 24px rgba(43, 36, 32, 0.14);
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]):hover::after,
    [data-testid="stVerticalBlockBorderWrapper"]:has(.season-photo-placeholder):hover::after {
        content: '✦';
        position: absolute;
        top: 10px;
        right: 14px;
        color: var(--ochre);
        font-size: 1.4rem;
        pointer-events: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 style='text-align:center; font-size:3.5rem; color:#B8623F;'>🌿 Noongar Weather</h1>",
    unsafe_allow_html=True,
)

home_tab, past_tab, seasons_tab, why_tab, about_tab = st.tabs(
    ["Home", "Past Data", "Learn About the Seasons", "Why 6 Seasons?", "About"])


season_colours = {
    "Birak": "#C96A3D",
    "Bunuru": "#E5B73B",
    "Djeran": "#C97C6D",
    "Makuru": "#4A6FA5",
    "Djilba": "#4F9D69",
    "Kambarang": "#F2A93B",
}

season_emojis = {
    "Birak": "☀️",
    "Bunuru": "🌊",
    "Djeran": "🍂",
    "Makuru": "🌧️",
    "Djilba": "🌸",
    "Kambarang": "🦜",
}


def local_image_path(category, name, expected_path=None):
    """Find an optional local, licensed image for a season entry."""
    app_dir = Path(__file__).resolve().parent
    if expected_path:
        expected_image = app_dir / expected_path
        if expected_image.is_file():
            return expected_image
        root_asset = app_dir / "assets" / Path(expected_path).name
        if root_asset.is_file():
            return root_asset

    slug = "".join(character.lower() if character.isalnum() else "-" for character in name)
    slug = "-".join(part for part in slug.split("-") if part)
    asset_dir = app_dir / "assets" / category
    for extension in (".webp", ".jpg", ".jpeg", ".png"):
        image_path = asset_dir / f"{slug}{extension}"
        if image_path.is_file():
            return image_path
    return None


def render_photo_cards(items, category, accent, placeholder_emoji, image_map=None):
    """Render centered local-image cards, with a friendly fallback if absent."""
    image_map = image_map or {}
    columns_per_row = min(3, len(items))
    for start in range(0, len(items), columns_per_row):
        row_items = items[start:start + columns_per_row]
        columns = st.columns(columns_per_row)
        for column, item in zip(columns, row_items):
            with column:
                with st.container(border=True):
                    image_path = local_image_path(category, item, image_map.get(item))
                    if image_path:
                        st.image(str(image_path), width="stretch")
                        st.caption("Image credit: Wikimedia Commons")
                    else:
                        st.markdown(
                            f"<div class='season-photo-placeholder' style='height:135px; display:grid; place-items:center; "
                            f"background:{accent}18; border:2px solid {accent}; border-radius:14px; "
                            f"font-size:3.2rem;'>{placeholder_emoji}</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown(
                        f"<p style='text-align:center; font-weight:800; color:#2B2420;'>{escape(item)}</p>",
                        unsafe_allow_html=True,
                    )


def render_species_card(entry, accent):
    common_name = entry["common_name"]
    category = entry["category"]
    information = species_info.get(common_name, {})
    asset_category = {"flower": "flowers", "animal": "animals", "food": "food"}[category]
    image_path = local_image_path(asset_category, common_name, entry.get("image"))
    placeholder_emoji = {"flower": "🌼", "animal": "🦜", "food": "🍓"}[category]
    if image_path:
        image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
        image_html = f'<img src="data:image/jpeg;base64,{image_data}" alt="{escape(common_name)}">'
    else:
        image_html = f'<div class="species-placeholder" aria-label="Photo coming soon">{placeholder_emoji}</div>'

    scientific_name = information.get("scientific_name", entry.get("scientific_name", ""))
    why = information.get("why", entry.get("why", ""))
    if "noongar_word" in information:
        noongar_line = f'<p><strong>Noongar name:</strong> {escape(information["noongar_word"])}</p>'
    else:
        noongar_line = ""
    if category == "food" and information.get("where_to_find"):
        where_line = f'<p><strong>Where to find:</strong> {escape(information["where_to_find"])}</p>'
    else:
        where_line = ""

    category_label = {"flower": "🌸 Flower", "animal": "🦘 Animal", "food": "🍽️ Food"}[category]
    card_html = (
        f'<details class="species-photo-card" style="--card-accent:{accent};">'
        f'<summary>'
        f'{image_html}'
        f'<span class="species-category-badge">{category_label}</span>'
        f'<span class="species-overlay">'
        f'<em>{escape(scientific_name)}</em>'
        f'{noongar_line}'
        f'<p>{escape(why)}</p>'
        f'{where_line}'
        f'<span class="species-tap-hint">Tap to close</span>'
        f'</span>'
        f'</summary>'
        f'</details>'
        f'<p class="species-card-title">{escape(common_name)}</p>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_species_gallery(season_info, accent):
    entries = []
    for category in ("flowers", "animals", "food"):
        entries.extend(season_info.get("images", {}).get(category, []))

    for start in range(0, len(entries), 3):
        columns = st.columns(3, gap="medium")
        for column, entry in zip(columns, entries[start:start + 3]):
            with column:
                render_species_card(entry, accent)


def render_did_you_know(items, accent):
    facts = "".join(
        f"<p style='margin:10px 0 0;'>🌿 {escape(item.strip())}</p>"
        for item in items
    )
    st.markdown(
        f"""
        <div style="background:#FFF9F1; border:2px solid {accent}50;
                    border-left:8px solid {accent}; border-radius:20px;
                    padding:22px 26px; margin:10px 0 24px;
                    box-shadow:0 8px 20px rgba(43,36,32,.08);">
            <strong style="color:#2F6F6E;">💡 Did you know?</strong>
            {facts}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cultural_acknowledgement():
    st.markdown(
        f"""
        <div style="background:#FFF9F1; border:2px solid #2F6F6E;
                    border-radius:20px; padding:24px 28px; margin:18px 0;
                    box-shadow:0 8px 20px rgba(43,36,32,.08);">
            <h3 style="color:#2F6F6E; margin-top:0;">Cultural Acknowledgement</h3>
            <p style="margin-bottom:0;">{escape(CULTURAL_ACKNOWLEDGEMENT)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def reset_past_filters():
    st.session_state["past_year_range"] = DEFAULT_YEAR_RANGE
    st.session_state["past_seasons"] = list(season_colours)
    st.session_state.pop("past_applied_year_range", None)
    st.session_state.pop("past_applied_seasons", None)


@st.cache_data(ttl=600, show_spinner=False)
def get_live_perth_weather():
    """Fetch current Perth conditions from Open-Meteo, cached for ten minutes."""
    url = (
        "https://api.open-meteo.com/v1/forecast?latitude=-31.95&longitude=115.86"
        "&current=temperature_2m,weather_code&timezone=Australia%2FPerth"
    )
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        current = response.json()["current"]
        observed_at = datetime.fromisoformat(current["time"]).astimezone(
            ZoneInfo("Australia/Perth")
        )
        weather_descriptions = {
            0: "Clear skies",
            1: "Mostly clear",
            2: "Partly cloudy",
            3: "Cloudy",
            45: "Foggy",
            48: "Foggy",
            51: "Light drizzle",
            53: "Drizzle",
            55: "Heavy drizzle",
            61: "Light rain",
            63: "Rain",
            65: "Heavy rain",
            71: "Light snow",
            73: "Snow",
            75: "Heavy snow",
            80: "Rain showers",
            81: "Rain showers",
            82: "Heavy rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Thunderstorm with hail",
        }
        return {
            "temperature": float(current["temperature_2m"]),
            "weather": weather_descriptions.get(int(current["weather_code"]), "Weather conditions available"),
            "observed_at": observed_at,
        }
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None

# Home
@st.fragment(run_every="1m")
def render_today_summary():
    now_perth = datetime.now(ZoneInfo("Australia/Perth"))
    today = now_perth.date()
    current_season = get_noongar_season(now_perth.month)
    accent = season_colours[current_season]
    current_translation = season_data[current_season].get("translation", "")
    live_weather = get_live_perth_weather()

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            f"""
            <div style="min-height:220px; background:#FFF9F1; border:2px solid #D9A441;
                        border-radius:20px; padding:28px; display:flex; flex-direction:column;
                        justify-content:center; box-shadow:0 8px 20px rgba(43,36,32,.08);">
                <h2 style="color:#2F6F6E; margin:0;">📅 In Perth today</h2>
                <p style="font-size:1.4rem; font-weight:800; margin:12px 0 0;">{now_perth.strftime('%A, %-d %B %Y')}</p>
                <p style="font-size:2rem; font-weight:800; color:#B8623F; margin:0;">{now_perth.strftime('%-I:%M %p')} AWST</p>
                <p style="margin:8px 0 0;">The clock updates every minute.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        if live_weather:
            temperature_text = f"{live_weather['temperature']:.1f} °C right now"
            rainfall_text = (
                f"{live_weather['weather']} · Updated "
                f"{live_weather['observed_at'].strftime('%-I:%M %p')} AWST"
            )
        else:
            temperature_text = "Live temperature is temporarily unavailable."
            rainfall_text = "The historical record is separate and is shown on the About tab."

        st.markdown(
            f"""
            <div style="min-height:220px; background:{accent}20; border:2px solid {accent};
                        border-radius:20px; padding:28px; display:flex; flex-direction:column;
                        justify-content:center; box-shadow:0 8px 20px rgba(43,36,32,.08);">
                <h2 style="color:{accent}; margin:0;">{season_emojis[current_season]} {current_season}</h2>
                <p style="font-weight:800; margin:4px 0 12px;">{escape(current_translation)}</p>
                <p style="font-size:1.8rem; font-weight:800; margin:0;">{escape(temperature_text)}</p>
                <p style="margin:8px 0 0;">{escape(rainfall_text)}</p>
                <p style="font-size:.9rem; margin:8px 0 0;">Live conditions from Open-Meteo; not a daily maximum or forecast.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with home_tab:
    st.title("☀️ Boorloo Weather Today")
    st.write("See today's Perth date, time, and Noongar season. Weather readings are shown only when the dataset contains today's observations.")
    render_today_summary()


# Past Data
with past_tab:
    st.title("🧭 Past Weather Explorer")
    st.write("Choose some years and seasons to explore how Perth weather changes.")
    st.info(
        f"Move the year slider, choose one or more seasons, then press **Show my weather**. "
        f"The slider is limited to the data we have ({DATA_MIN_YEAR}–{DATA_MAX_YEAR}). "
        "The charts compare daily temperatures and rainfall totals."
    )

    selected_year_range = st.slider(
        "🗓️ Choose a year range",
        min_value=DATA_MIN_YEAR,
        max_value=DATA_MAX_YEAR,
        value=DEFAULT_YEAR_RANGE,
        step=1,
        key="past_year_range",
        help="The ends of the slider cannot go beyond the years in this dataset.",
    )
    selected_seasons = st.multiselect(
        "🍂 Choose seasons to compare",
        options=list(season_colours),
        default=list(season_colours),
        format_func=lambda season: f"{season_emojis[season]} {season}",
        key="past_seasons",
        help="Choose one season or several. Clear all choices to see no seasonal records.",
    )

    apply_col, reset_col = st.columns([1, 1])
    with apply_col:
        show_results = st.button("Show my weather", type="primary", use_container_width=True)
    with reset_col:
        st.button("Reset filters", type="secondary", use_container_width=True, on_click=reset_past_filters)

    if show_results:
        st.session_state["past_applied_year_range"] = selected_year_range
        st.session_state["past_applied_seasons"] = selected_seasons

    applied_year_range = st.session_state.get("past_applied_year_range")
    applied_seasons = st.session_state.get("past_applied_seasons")

    if applied_year_range is None or applied_seasons is None:
        st.markdown("### Ready? Pick your filters above and press **Show my weather** 🌦️")
    elif not applied_seasons:
        st.warning("Choose at least one season to see weather records.")
    else:
        start_year, end_year = applied_year_range
        start_date = max(DATA_MIN_DATE.date(), calendar_date(start_year, 1, 1))
        end_date = min(DATA_MAX_DATE.date(), calendar_date(end_year, 12, 31))
        filtered_data = filter_historical_weather(
            data,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        filtered_data = filtered_data[filtered_data["noongar_season"].isin(applied_seasons)].copy()

        if filtered_data.empty:
            st.warning("No records match those choices. Try another year or season.")
        else:
            chart_accent = season_colours[applied_seasons[0]] if len(applied_seasons) == 1 else "#2F6F6E"
            st.markdown(f"<style>:root {{ --season-accent: {chart_accent}; }}</style>", unsafe_allow_html=True)
            st.markdown(f"### 🎉 We found {len(filtered_data):,} days of weather!")

            period_metrics = get_period_extremes(filtered_data)
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("🔥 Hottest day", f"{period_metrics['hottest_day_temp_max']:.1f} °C", period_metrics["hottest_day_date"])
            with metric_col2:
                st.metric("🌧️ Wettest day", f"{period_metrics['wettest_day_rainfall_mm']:.1f} mm", period_metrics["wettest_day_date"])
            with metric_col3:
                st.metric("🌤️ Average day-night range", f"{period_metrics['avg_diurnal_range']:.1f} °C", "Maximum minus minimum")

            st.markdown("### 🌡️ Temperature: chilly mornings and warm afternoons")
            st.caption("Each box shows the spread of daily minimum or maximum temperatures. Diamonds mark the average for that season.")
            temperature_long = filtered_data.melt(
                id_vars=["date", "noongar_season"],
                value_vars=["temp_min", "temp_max"],
                var_name="measurement",
                value_name="temperature",
            )
            temperature_long["measurement"] = temperature_long["measurement"].map({
                "temp_min": "Daily minimum", "temp_max": "Daily maximum"
            })
            temperature_chart = px.box(
                temperature_long,
                x="noongar_season",
                y="temperature",
                color="measurement",
                color_discrete_map={"Daily minimum": "#2F6F6E", "Daily maximum": "#B8623F"},
                points="outliers",
                category_orders={"noongar_season": list(season_colours)},
                labels={"noongar_season": "Noongar season", "temperature": "Temperature (°C)", "measurement": "Daily reading"},
                template="plotly_white",
            )
            seasonal_averages = (
                temperature_long.groupby(["noongar_season", "measurement"], as_index=False)["temperature"]
                .mean()
            )
            for measurement, average_data in seasonal_averages.groupby("measurement"):
                temperature_chart.add_scatter(
                    x=average_data["noongar_season"],
                    y=average_data["temperature"],
                    mode="markers",
                    name=f"{measurement} average",
                    marker={"symbol": "diamond", "size": 12, "line": {"width": 1, "color": "#2B2420"}},
                    hovertemplate="%{x}<br>Average: %{y:.1f} °C<extra></extra>",
                )
            temperature_chart.update_layout(height=440, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFF9F1", legend_title_text="Temperature")
            st.plotly_chart(temperature_chart, width="stretch", key="past_temperature_distribution")

            st.markdown("### 🌧️ Rainfall: follow a rainy season")
            monthly_rain = filtered_data.assign(month=filtered_data["date"].dt.to_period("M").dt.to_timestamp())
            monthly_rain = (
                monthly_rain.groupby(["month", "noongar_season"], as_index=False)["rainfall_mm"]
                .sum()
                .sort_values("month")
            )
            monthly_rain["cumulative_rainfall"] = monthly_rain["rainfall_mm"].cumsum()
            rainfall_chart = make_subplots(specs=[[{"secondary_y": True}]])
            rainfall_chart.add_trace(
                go.Bar(
                    x=monthly_rain["month"],
                    y=monthly_rain["rainfall_mm"],
                    name="Rain that month",
                    marker_color=[season_colours[season] for season in monthly_rain["noongar_season"]],
                    customdata=monthly_rain[["noongar_season"]],
                    hovertemplate="%{x|%b %Y}<br>%{y:.1f} mm<br>%{customdata[0]}<extra></extra>",
                ),
                secondary_y=False,
            )
            rainfall_chart.add_trace(
                go.Scatter(
                    x=monthly_rain["month"],
                    y=monthly_rain["cumulative_rainfall"],
                    name="Rain added over time",
                    mode="lines",
                    line={"color": "#2F6F6E", "width": 4},
                    hovertemplate="By %{x|%b %Y}: %{y:.1f} mm<extra></extra>",
                ),
                secondary_y=True,
            )
            rainfall_chart.update_yaxes(title_text="Rain that month (mm)", secondary_y=False)
            rainfall_chart.update_yaxes(title_text="Cumulative rain (mm)", secondary_y=True)
            rainfall_chart.update_xaxes(title_text="Month")
            rainfall_chart.update_layout(
                height=440,
                barmode="overlay",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFF9F1",
                hovermode="x unified",
                legend_title_text="Rainfall",
            )
            st.plotly_chart(rainfall_chart, width="stretch", key="past_rainfall_cumulative")
            season_totals = filtered_data.groupby("noongar_season")["rainfall_mm"].sum().sort_values(ascending=False)
            wettest_season = season_totals.index[0]
            driest_season = season_totals.index[-1]
            st.info(
                f"In this selection, {season_emojis[wettest_season]} **{wettest_season}** has the most recorded rain "
                f"({season_totals.iloc[0]:.1f} mm); {season_emojis[driest_season]} **{driest_season}** has the least "
                f"({season_totals.iloc[-1]:.1f} mm). Makuru is commonly associated with wetter weather and Bunuru with hot, dry weather."
            )


# seasonal exploration page
with seasons_tab:
    st.title("Learn About the Noongar Seasons")
    st.write(
        "Explore the six Noongar seasons and the seasonal changes associated with them.")
    st.divider()

    seasons = season_data
    season_names = list(seasons)
    now_perth = datetime.now(ZoneInfo("Australia/Perth"))
    st.session_state.setdefault("open_season", get_noongar_season(now_perth.month))

    st.markdown("### 🌞 Choose a season")
    st.caption("Tap a season to explore it. Tap it again to close it.")

    # Big, season-coloured buttons. Clicking the already-open season closes
    # it; clicking a different one swaps to that season instead. Plain
    # st.button + session_state -- no chart-click events to depend on, so
    # this works the same on every browser and every device.
    open_season_now = st.session_state["open_season"]
    button_styles = []
    for season, colour in season_colours.items():
        slug = season.lower()
        is_open = open_season_now == season
        # Idle state: light tint with a coloured border. Open state: solid
        # fill in the season's colour. Both are plain CSS keyed off each
        # button's own container key -- no extra marker elements needed.
        bg = colour if is_open else f"{colour}20"
        text_colour = "#FFFFFF" if is_open else "#2B2420"
        button_styles.append(
            f"""
            .st-key-season-btn-{slug} button {{
                border: 3px solid {colour} !important;
                background: {bg} !important;
                color: {text_colour} !important;
                border-radius: 18px !important;
                font-family: 'Baloo 2', sans-serif !important;
                font-weight: 700 !important;
                font-size: 1.05rem !important;
                min-height: 64px !important;
                box-shadow: 0 6px 14px rgba(43,36,32,.08);
            }}
            .st-key-season-btn-{slug} button:hover {{
                background: {colour}{"" if is_open else "40"} !important;
                transform: translateY(-2px);
            }}
            """
        )
    st.markdown(f"<style>{''.join(button_styles)}</style>", unsafe_allow_html=True)

    button_cols = st.columns(3)
    for index, season in enumerate(season_names):
        slug = season.lower()
        is_open = open_season_now == season
        with button_cols[index % 3]:
            with st.container(key=f"season-btn-{slug}"):
                clicked = st.button(
                    f"{season_emojis[season]} {season}\n{seasons[season]['months']}",
                    key=f"season-btn-click-{slug}",
                    use_container_width=True,
                )
                if clicked:
                    st.session_state["open_season"] = None if is_open else season
                    st.rerun()

    open_season = st.session_state["open_season"]

    if open_season is None:
        st.info("🌼 Tap a season above to see its signs, photos, and traditional practices.")
    else:
        selected_info_season = open_season
        season_info = seasons[selected_info_season]
        accent = season_colours[selected_info_season]
        season_slug = selected_info_season.lower()

        entrance_offsets = {
            "Birak": "translateY(16px) scale(.92)",
            "Bunuru": "translateX(-16px) scale(.92)",
            "Djeran": "translateY(-16px) scale(.92)",
            "Makuru": "scale(.82)",
            "Djilba": "translateX(16px) scale(.92)",
            "Kambarang": "rotate(-4deg) scale(.88)",
        }

        with st.container(key=f"season-panel-{season_slug}"):
            st.markdown(
                f"""
                <style>
                @keyframes entrance-{season_slug} {{
                    from {{ opacity: 0; transform: {entrance_offsets[selected_info_season]}; }}
                    to {{ opacity: 1; transform: translate(0) scale(1) rotate(0); }}
                }}
                .st-key-season-panel-{season_slug} {{
                    background: {accent}20 !important;
                    border-radius: 20px;
                    padding: 18px;
                    transition: background-color 250ms ease;
                }}
                .st-key-season-panel-{season_slug} h2,
                .st-key-season-panel-{season_slug} h3 {{ color: {accent} !important; }}
                .st-key-season-panel-{season_slug} [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]),
                .st-key-season-panel-{season_slug} [data-testid="stVerticalBlockBorderWrapper"]:has(.season-photo-placeholder) {{
                    border: 2px solid {accent} !important;
                    border-radius: 18px;
                    position: relative;
                    background: #FFFCF7;
                }}
                .st-key-season-panel-{season_slug} [data-testid="stColumn"]:has([data-testid="stImage"]),
                .st-key-season-panel-{season_slug} [data-testid="stColumn"]:has(.season-photo-placeholder) {{
                    animation: entrance-{season_slug} 560ms cubic-bezier(.2,.8,.2,1) both;
                }}
                .st-key-season-panel-{season_slug} [data-testid="stColumn"]:nth-child(2) {{ animation-delay: 90ms; }}
                .st-key-season-panel-{season_slug} [data-testid="stColumn"]:nth-child(3) {{ animation-delay: 180ms; }}
                </style>
                """,
                unsafe_allow_html=True,
            )

            info_col, signs_col = st.columns(2, gap="large")
            with info_col:
                st.markdown(
                    f"""
                    <div style="min-height:220px; border:2px solid {accent};
                                background:{accent}20; border-radius:20px; padding:24px;
                                box-shadow:0 8px 20px rgba(43,36,32,.08); text-align:center;">
                        <h2 style="color:{accent};">{season_emojis[selected_info_season]} {selected_info_season}</h2>
                        <p style="font-size:1.2rem; font-weight:800;">📅 {escape(season_info['months'])}</p>
                        <p style="font-size:1.05rem;">{escape(season_info.get('translation', ''))}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with signs_col:
                seasonal_signs = "".join(
                    f"<li>{escape(sign.strip())}</li>"
                    for sign in season_info["seasonal_signs"]
                )
                st.markdown(
                    f"""
                    <div style="min-height:220px; border:2px solid {accent};
                                background:{accent}20; border-radius:20px; padding:24px;
                                box-shadow:0 8px 20px rgba(43,36,32,.08);">
                        <h2 style="color:{accent};">🔎 Seasonal signs</h2>
                        <ul style="font-size:1.05rem; line-height:1.55; padding-left:24px;">{seasonal_signs}</ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("### 🌿 Season discoveries")
            st.caption("Tap any card to keep its details open. Hover with a mouse to preview the same information.")
            render_species_gallery(season_info, accent)

            st.markdown("### 🔥 Traditional practices")
            render_did_you_know(season_info["traditional_practices"], accent)


with why_tab:
    with st.container(key="why-seasons-screen"):
        st.markdown(
            """
            <style>
            .st-key-why-seasons-screen h1, .st-key-why-seasons-screen h2,
            .st-key-why-seasons-screen h3, .st-key-why-seasons-screen p,
            .st-key-why-seasons-screen li, .st-key-why-seasons-screen table {
                text-align: center;
            }
            .st-key-why-seasons-screen table {
                margin: 24px auto;
                width: min(100%, 900px);
                border-collapse: separate;
                border-spacing: 0;
                overflow: hidden;
                border-radius: 16px;
                box-shadow: 0 8px 20px rgba(43,36,32,.08);
            }
            .st-key-why-seasons-screen th, .st-key-why-seasons-screen td {
                padding: 12px;
                text-align: center !important;
                border-bottom: 1px solid #E5D8C8;
            }
            .st-key-why-seasons-screen th { background: #2F6F6E; color: white; }
            .st-key-why-seasons-screen td { background: #FFF9F1; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.title("🌍 Why Six Seasons?")
        st.markdown(
            "### 🗣️ Different places, different words\n"
            "Australians might say **jumper** where people elsewhere say **sweater**, "
            "or **lollies** where others say **sweets**. The words can change from "
            "place to place, even when we are talking about similar things."
        )
        st.markdown(
            "### 🌦️ So why should every place use the same seasons?\n"
            "A four-season calendar is familiar, but it does not describe every "
            "place in the same way. The Noongar six-season calendar describes "
            "seasonal changes on Noongar Country through signs in the weather, "
            "plants, and animals, rather than only dividing the year into four "
            "named blocks. The seasons can be understood through what is changing "
            "around us."
        )

        st.subheader("📅 One year, two ways to describe it")
        st.markdown(
            "| Month | Common four-season name | Noongar season |\n"
            "|:---:|:---:|:---:|\n"
            "| January | Summer | Birak |\n| February | Summer | Bunuru |\n"
            "| March | Autumn | Bunuru |\n| April | Autumn | Djeran |\n"
            "| May | Autumn | Djeran |\n| June | Winter | Makuru |\n"
            "| July | Winter | Makuru |\n| August | Winter | Djilba |\n"
            "| September | Spring | Djilba |\n| October | Spring | Kambarang |\n"
            "| November | Spring | Kambarang |\n| December | Summer | Birak |"
        )
        st.markdown(
            "### 👀 Look for what is changing\n"
            "The Noongar seasonal calendar is connected to this place and to "
            "observations of the environment. The names and descriptions below "
            "are a starting point for learning, not a substitute for Noongar "
            "community knowledge."
        )

        season_indicators = {
            "Birak": ("Dec – Jan", "First summer · season of the young"),
            "Bunuru": ("Feb – Mar", "Second summer · season of adolescence"),
            "Djeran": ("Apr – May", "Autumn · season of adulthood"),
            "Makuru": ("Jun – Jul", "Winter · season of fertility"),
            "Djilba": ("Aug – Sep", "First spring · season of conception"),
            "Kambarang": ("Oct – Nov", "Second spring · season of birth"),
        }
        for season, (months, description) in season_indicators.items():
            accent = season_colours[season]
            st.markdown(
                f"""
                <div style="background:{accent}18; border:2px solid {accent};
                            border-radius:18px; padding:20px 24px; margin:14px auto;
                            max-width:850px; text-align:center;">
                    <h3 style="color:{accent}; margin:0;">{season_emojis[season]} {season}</h3>
                    <p style="font-size:1.1rem; font-weight:800; margin:5px 0;">{months} · {description}</p>
                    <p style="margin:0;">{escape(description)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 📚 Sources & Citations")
        st.markdown(
            "<p><a href='https://www.bom.gov.au/resources/indigenous-weather-knowledge/indigenous-seasonal-calendars/nyoongar-calendar'>Bureau of Meteorology — Nyoongar Indigenous Weather Knowledge</a></p>"
            "<p><a href='https://www.noongarboodjar.com.au/'>Noongar Boodjar Language Centre</a></p>"
            "<p><a href='https://www.noongar.org.au/'>South West Aboriginal Land and Sea Council (SWALSC)</a></p>",
            unsafe_allow_html=True,
        )
        render_cultural_acknowledgement()

with about_tab:
    st.title("📖 About Noongar Weather")
    st.write("How the weather data and seasonal learning content come together.")

    st.subheader("🌦️ Weather data")
    latest_record = get_current_weather(data)
    st.markdown(
        f"### 📍 Latest historical observation · {latest_record['date']}\n"
        "This is the newest daily BoM record in the saved dataset, not today's live Open-Meteo reading."
    )
    latest_col1, latest_col2, latest_col3, latest_col4 = st.columns(4)
    with latest_col1:
        st.metric("Maximum", f"{latest_record['temp_max']:.1f} °C")
    with latest_col2:
        st.metric("Minimum", f"{latest_record['temp_min']:.1f} °C")
    with latest_col3:
        st.metric("Daily average", f"{latest_record['temp_avg']:.1f} °C")
    with latest_col4:
        st.metric("Rainfall", f"{latest_record['rainfall_mm']:.1f} mm")

    st.subheader("🌦️ Data provenance")
    st.markdown(
        "The historical dataset uses Bureau of Meteorology station **PERTH METRO (009225)**. "
        "It combines the daily maximum temperature, daily minimum temperature, and daily rainfall CSVs. "
        "The source files are in `data/raw/`."
    )
    st.markdown(
        "**How the data is prepared:** BoM CSVs are loaded, merged by date, and cleaned; "
        "dates are mapped to Noongar seasons by `season_mapper.py`; daily average temperature "
        "is calculated; and the result is exported to `data/processed/weather_processed_final.csv`."
    )
    st.markdown(
        "[Bureau of Meteorology — Perth Metro station 009225](https://www.bom.gov.au/climate/averages/tables/cw_009225.shtml)"
    )
    st.markdown(
        "**Live conditions:** temperature and weather code come from Open-Meteo at "
        "latitude -31.95, longitude 115.86, using the Australia/Perth timezone. "
        "Live data updates independently from the historical BoM CSV dataset."
    )

    st.subheader("🌿 Cultural knowledge sources")
    st.write(
        "The seasonal signs, flowers, animals, foods, and practices in `seasons.json` are a "
        "general learning summary. Season translations follow the BoM Nyoongar calendar. "
        "The Noongar Boodjar Language Centre and SWALSC are named as Noongar language and "
        "community sources for checking terminology and finding fuller cultural context."
    )
    st.markdown(
        "- [Bureau of Meteorology — Nyoongar calendar](https://www.bom.gov.au/resources/indigenous-weather-knowledge/indigenous-seasonal-calendars/nyoongar-calendar)\n"
        "- [Noongar Boodjar Language Centre](https://www.noongarboodjar.com.au/)\n"
        "- [South West Aboriginal Land and Sea Council (SWALSC)](https://www.noongar.org.au/)"
    )

    render_cultural_acknowledgement()

    st.subheader("🖼️ Image Credits")
    image_credits = [
        ('"Brachyscome iberidifolia - Bergianska trädgården - Stockholm, Sweden - DSC00172.JPG" by Daderot — CC0', "https://commons.wikimedia.org/wiki/File:Brachyscome_iberidifolia_-_Bergianska_tr%C3%A4dg%C3%A5rden_-_Stockholm,_Sweden_-_DSC00172.JPG"),
        ('"Magpie fledgling, fallen from nest, abandoned - geograph.org.uk - 6538468.jpg" by David Hawgood — CC BY-SA 2.0', "https://commons.wikimedia.org/wiki/File:Magpie_fledgling,_fallen_from_nest,_abandoned_-_geograph.org.uk_-_6538468.jpg"),
        ('"Jarrah - Eucalyptus marginata.jpg" by Podiceps60 — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Jarrah_-_Eucalyptus_marginata.jpg"),
        ('"Tursiops aduncus, Port River, Adelaide, Australia - 2003.jpg" by Aude Steiner — CC BY-SA 1.0', "https://commons.wikimedia.org/wiki/File:Tursiops_aduncus,_Port_River,_Adelaide,_Australia_-_2003.jpg"),
        ('"Corymbia ficifolia Flowers.jpg" by JJ Harrison (jjharrison.com.au) — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Corymbia_ficifolia_Flowers.jpg"),
        ('"Formica neogagates, alate.jpg" by Beatriz Moisset — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Formica_neogagates,_alate.jpg"),
        ('"Dianella revoluta.jpg" by Sam Genas — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Dianella_revoluta.jpg"),
        ('"Black Swan at Martin Mere.JPG" by Francis C. Franklin — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Black_Swan_at_Martin_Mere.JPG"),
        ('"Acacia pulchella 1.jpg" by h3 six — CC BY-SA 2.0', "https://commons.wikimedia.org/wiki/File:Acacia_pulchella_1.jpg"),
        ('"Cracticus tibicen hypoleuca male domain.jpg" by JJ Harrison (jjharrison.com.au) — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Cracticus_tibicen_hypoleuca_male_domain.jpg"),
        ('"B menziesii gnangarra 21.jpg" by Gnangarra — CC BY 2.5 AU', "https://commons.wikimedia.org/wiki/File:B_menziesii_gnangarra_21.jpg"),
        ('"Bob t rugosa rugosa gn.jpg" by Gnangcomapp — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Bob_t_rugosa_rugosa_gn.jpg"),
        ('"Trachymene coerulea at Lake Walyungup, Rockingham Lakes Regional Park, June 2022 03.jpg" by Calistemon — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Trachymene_coerulea_at_Lake_Walyungup,_Rockingham_Lakes_Regional_Park,_June_2022_03.jpg"),
        ('"(Verticordia acerosa close-up in Three Springs, Australia) - DPLA - dca2d9c746243dfb435a24d073d74810.jpg" by Carlquist, Sherwin John — CC BY 4.0', "https://commons.wikimedia.org/wiki/File:(Verticordia_acerosa_close-up_in_Three_Springs,_Australia)_-_DPLA_-_dca2d9c746243dfb435a24d073d74810.jpg"),
        ('"Eucalyptus calophylla flowers2 Cataby email.jpg" by Cas Liber — Public domain', "https://commons.wikimedia.org/wiki/File:Eucalyptus_calophylla_flowers2_Cataby_email.jpg"),
        ('"Eucalyptus laeliae habit.jpg" by Murray Fagg — CC BY 3.0 AU', "https://commons.wikimedia.org/wiki/File:Eucalyptus_laeliae_habit.jpg"),
        ('"Macrozamia riedlei kz02.jpg" by Krzysztof Ziarnek, Kenraiz — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Macrozamia_riedlei_kz02.jpg"),
        ('"Beaufortia aestiva flower.jpg" by Allthingsnative — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Beaufortia_aestiva_flower.jpg"),
        ('"Banksia menziesii 1 gnangarra.jpg" by Gnangarra — CC BY 2.5 AU', "https://commons.wikimedia.org/wiki/File:Banksia_menziesii_1_gnangarra.jpg"),
        ('"Patersonia occidentalis flower with Hover fly.jpg" by Jean and Fred Hort — CC BY 2.0', "https://commons.wikimedia.org/wiki/File:Patersonia_occidentalis_flower_with_Hover_fly.jpg"),
        ('"Agonis flexuosa.jpg" by Eric in SF — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Agonis_flexuosa.jpg"),
        ('"Base of old Jarrah tree.jpg" by JarrahTree — CC BY 2.5 AU', "https://commons.wikimedia.org/wiki/File:Base_of_old_Jarrah_tree.jpg"),
        ('"Anigozanthos manglesii Kings Park.JPG" by Davidwilcox — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Anigozanthos_manglesii_Kings_Park.JPG"),
        ('"Elythranthera emarginata (6724961065).jpg" by Kevin Thiele — CC BY 2.0', "https://commons.wikimedia.org/wiki/File:Elythranthera_emarginata_(6724961065).jpg"),
        ('"Xanthorrhoea preissii 1.jpg" by Dcoetzee — Public domain', "https://commons.wikimedia.org/wiki/File:Xanthorrhoea_preissii_1.jpg"),
        ('"Dugite (Pseudonaja affinis).png" by Bradford G. Jones — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Dugite_(Pseudonaja_affinis).png"),
        ('"Notechis scutatus 260523890.jpg" by Max Tibby — CC0', "https://commons.wikimedia.org/wiki/File:Notechis_scutatus_260523890.jpg"),
        ('"Varanus gouldii Tongue.jpg" by Alan — CC BY 2.0', "https://commons.wikimedia.org/wiki/File:Varanus_gouldii_Tongue.jpg"),
        ('"Portunus pelagicus male.jpg" by self (Commons uploader) — CC BY-SA 3.0', "https://commons.wikimedia.org/wiki/File:Portunus_pelagicus_male.jpg"),
        ('"Chelodina oblonga 2025.jpg" by Sevenstxrsquid — CC BY 4.0', "https://commons.wikimedia.org/wiki/File:Chelodina_oblonga_2025.jpg"),
        ('"Western Grey Kangaroo, Dhilba Guuranda–Innes NP 20230208 3.jpg" by DXR — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Western_Grey_Kangaroo,_Dhilba_Guuranda%E2%80%93Innes_NP_20230208_3.jpg"),
        ('"Emu 1 - Tidbinbilla.jpg" by JJ Harrison (jjharrison.com.au) — CC BY-SA 4.0', "https://commons.wikimedia.org/wiki/File:Emu_1_-_Tidbinbilla.jpg"),
        ('"DSC 1648 quandong (Santalum acuminatum) on road to Pimba, South Australia (15031022055).jpg" by John Jennings — CC BY 2.0', "https://commons.wikimedia.org/wiki/File:DSC_1648_quandong_(Santalum_acuminatum)_on_road_to_Pimba,_South_Australia_(15031022055).jpg"),
    ]
    for credit, commons_url in image_credits:
        st.markdown(f"- {credit} — [Wikimedia Commons]({commons_url})")

    st.subheader("🧑‍🎓 About this project")
    st.write(
        "Built by **[Team/student name]** as a **[school/university] project** to help Perth "
        "primary school students learn about the six Noongar seasons alongside real local weather data."
    )