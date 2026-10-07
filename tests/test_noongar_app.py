"""Automated tests for the Noongar Weather app.

Run from the project root (the folder that contains app.py):

    python -m unittest discover -s tests -v
    # or
    python tests/test_noongar_app.py

Only the standard library `unittest` is used for the tests themselves.
The app tests use Streamlit's own `streamlit.testing.v1.AppTest`, which
ships with Streamlit, so nothing extra needs installing.
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"

SEASONS = ["Birak", "Bunuru", "Djeran", "Makuru", "Djilba", "Kambarang"]

# month -> season, taken from the "Why 6 Seasons?" table in app.py
EXPECTED_SEASON_BY_MONTH = {
    1: "Birak", 2: "Bunuru", 3: "Bunuru", 4: "Djeran",
    5: "Djeran", 6: "Makuru", 7: "Makuru", 8: "Djilba",
    9: "Djilba", 10: "Kambarang", 11: "Kambarang", 12: "Birak",
}


def setUpModule():
    # app.py and the loaders use paths relative to the project root.
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


# These imports need ROOT on sys.path, so they come after the path set-up.
sys.path.insert(0, str(ROOT))
from src.aggregations import get_period_extremes  # noqa: E402
from src.season_mapper import get_noongar_season  # noqa: E402
from src.weather_service import (  # noqa: E402
    filter_historical_weather,
    get_current_weather,
    load_processed_data,
)


def make_weather_df():
    """Small hand-checkable dataset (deliberately NOT in date order)."""
    rows = [
        # date,          max,  min,  rain, season
        ("2020-06-16", 16.0, 9.0, 78.4, "Makuru"),
        ("2020-01-01", 40.0, 22.0, 0.0, "Birak"),
        ("2021-12-31", 33.0, 22.0, 0.0, "Birak"),
        ("2020-01-02", 44.5, 25.0, 0.0, "Birak"),
        ("2020-06-15", 17.0, 8.0, 35.2, "Makuru"),
        ("2020-10-31", 24.0, 11.0, 1.2, "Kambarang"),
    ]
    df = pd.DataFrame(
        rows, columns=["date", "temp_max", "temp_min", "rainfall_mm", "noongar_season"]
    )
    df["date"] = pd.to_datetime(df["date"])
    df["temp_avg"] = (df["temp_max"] + df["temp_min"]) / 2
    return df


# ---------------------------------------------------------------------------
# 1. Algorithmic core: month -> Noongar season
# ---------------------------------------------------------------------------
class SeasonMapperTests(unittest.TestCase):
    def test_every_month_maps_to_the_documented_season(self):
        for month, expected in EXPECTED_SEASON_BY_MONTH.items():
            with self.subTest(month=month):
                self.assertEqual(get_noongar_season(month), expected)

    def test_year_wrap_boundary_december_and_january_are_both_birak(self):
        self.assertEqual(get_noongar_season(12), "Birak")
        self.assertEqual(get_noongar_season(1), "Birak")

    def test_season_changes_exactly_at_the_documented_boundaries(self):
        # (last month of one season, first month of the next)
        boundaries = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)]
        for before, after in boundaries:
            with self.subTest(before=before, after=after):
                self.assertNotEqual(
                    get_noongar_season(before), get_noongar_season(after)
                )

    def test_all_six_seasons_are_used_and_nothing_else(self):
        produced = {get_noongar_season(m) for m in range(1, 13)}
        self.assertEqual(produced, set(SEASONS))

    def test_invalid_months_are_rejected(self):
        for bad in (0, 13, -1, 99, None, "July"):
            with self.subTest(month=bad):
                with self.assertRaises((ValueError, TypeError, KeyError)):
                    get_noongar_season(bad)


# ---------------------------------------------------------------------------
# 2. Algorithmic core: summary statistics
# ---------------------------------------------------------------------------
class PeriodExtremesTests(unittest.TestCase):
    def test_finds_hottest_and_wettest_day(self):
        result = get_period_extremes(make_weather_df())
        self.assertAlmostEqual(result["hottest_day_temp_max"], 44.5)
        self.assertIn("2020-01-02", str(result["hottest_day_date"]))
        self.assertAlmostEqual(result["wettest_day_rainfall_mm"], 78.4)
        self.assertIn("2020-06-16", str(result["wettest_day_date"]))

    def test_average_diurnal_range_is_mean_of_max_minus_min(self):
        # (18 + 19.5 + 9 + 7 + 13 + 11) / 6
        result = get_period_extremes(make_weather_df())
        self.assertAlmostEqual(result["avg_diurnal_range"], 77.5 / 6, places=6)

    def test_single_day_dataset_edge_case(self):
        one_day = make_weather_df().iloc[[0]]
        result = get_period_extremes(one_day)
        self.assertAlmostEqual(result["hottest_day_temp_max"], 16.0)
        self.assertAlmostEqual(result["avg_diurnal_range"], 7.0)

    def test_all_dry_period_reports_zero_rain(self):
        dry = make_weather_df()
        dry["rainfall_mm"] = 0.0
        result = get_period_extremes(dry)
        self.assertEqual(result["wettest_day_rainfall_mm"], 0.0)


# ---------------------------------------------------------------------------
# 3. Data filtering / lookup
# ---------------------------------------------------------------------------
class WeatherServiceTests(unittest.TestCase):
    def setUp(self):
        self.df = make_weather_df()

    def test_filter_is_inclusive_at_both_ends(self):
        out = filter_historical_weather(
            self.df, start_date="2020-06-15", end_date="2020-06-16"
        )
        self.assertEqual(len(out), 2)

    def test_filter_single_day_boundary(self):
        out = filter_historical_weather(
            self.df, start_date="2020-01-01", end_date="2020-01-01"
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out.iloc[0]["temp_max"], 40.0)

    def test_filter_range_with_no_data_returns_empty(self):
        out = filter_historical_weather(
            self.df, start_date="1999-01-01", end_date="1999-12-31"
        )
        self.assertTrue(out.empty)

    def test_filter_start_after_end_is_empty_or_rejected(self):
        try:
            out = filter_historical_weather(
                self.df, start_date="2021-01-01", end_date="2020-01-01"
            )
        except ValueError:
            return  # raising is an acceptable design
        self.assertTrue(out.empty)

    def test_filter_garbage_date_string_is_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            filter_historical_weather(
                self.df, start_date="not-a-date", end_date="2020-01-01"
            )

    def test_current_weather_is_the_newest_record_even_if_unsorted(self):
        # newest row is 2021-12-31 (max 33.0) but is NOT the last row in df
        latest = get_current_weather(self.df)
        self.assertAlmostEqual(float(latest["temp_max"]), 33.0)
        self.assertIn("2021", str(latest["date"]))


# ---------------------------------------------------------------------------
# 4. The real processed dataset the deployed app relies on
# ---------------------------------------------------------------------------
class ProcessedDataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_processed_data()

    def test_required_columns_exist(self):
        needed = {"date", "temp_max", "temp_min", "temp_avg", "rainfall_mm", "noongar_season"}
        self.assertTrue(needed.issubset(self.data.columns))

    def test_no_duplicate_dates(self):
        self.assertFalse(self.data["date"].duplicated().any())

    def test_values_are_physically_sensible(self):
        self.assertTrue((self.data["rainfall_mm"].dropna() >= 0).all())
        both = self.data[["temp_max", "temp_min"]].dropna()
        self.assertTrue((both["temp_max"] >= both["temp_min"]).all())

    def test_season_column_agrees_with_the_mapper_for_every_row(self):
        expected = self.data["date"].dt.month.map(get_noongar_season)
        mismatches = self.data[expected != self.data["noongar_season"]]
        self.assertTrue(mismatches.empty, f"{len(mismatches)} rows disagree")

    def test_data_starts_no_earlier_than_the_1993_limit_the_app_advertises(self):
        self.assertGreaterEqual(int(self.data["date"].min().year), 1993)


# ---------------------------------------------------------------------------
# 5. Main functionality: drive the actual Streamlit app headlessly
# ---------------------------------------------------------------------------
def fake_open_meteo_response(temperature=21.5, weather_code=2):
    response = mock.MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "current": {
            "time": "2026-10-07T19:00",
            "temperature_2m": temperature,
            "weather_code": weather_code,
        }
    }
    return response


def run_app(live_weather=None, network_error=None):
    """Run app.py once with the network mocked, so tests are offline and fast."""
    st.cache_data.clear()
    with mock.patch("requests.get") as fake_get:
        if network_error is not None:
            fake_get.side_effect = network_error
        else:
            fake_get.return_value = live_weather or fake_open_meteo_response()
        at = AppTest.from_file(str(APP_PATH), default_timeout=60)
        at.run()
    return at


def markdown_text(at):
    return " ".join(str(m.value) for m in at.markdown)


def pick_birthday(at, day, month, year):
    at.selectbox[0].set_value(day)
    at.selectbox[1].set_value(month)
    at.selectbox[2].set_value(year)
    find_out = next(b for b in at.button if b.label.startswith("Find out"))
    find_out.click()
    return at.run()


class AppSmokeAndHomeTests(unittest.TestCase):
    def test_app_starts_without_exceptions(self):
        at = run_app()
        self.assertEqual(len(at.exception), 0)

    def test_home_tab_shows_live_temperature_and_description(self):
        at = run_app(fake_open_meteo_response(temperature=21.5, weather_code=2))
        text = markdown_text(at)
        self.assertIn("21.5 °C right now", text)
        self.assertIn("Partly cloudy", text)

    def test_home_tab_shows_current_noongar_season(self):
        at = run_app()
        month = datetime.now(ZoneInfo("Australia/Perth")).month
        self.assertIn(get_noongar_season(month), markdown_text(at))

    def test_unknown_weather_code_falls_back_to_generic_text(self):
        at = run_app(fake_open_meteo_response(weather_code=123))
        self.assertIn("Weather conditions available", markdown_text(at))

    def test_network_failure_shows_friendly_message_not_a_crash(self):
        at = run_app(network_error=requests.ConnectionError("offline"))
        self.assertEqual(len(at.exception), 0)
        self.assertIn("temporarily unavailable", markdown_text(at))

    def test_malformed_api_payload_is_handled(self):
        bad = mock.MagicMock()
        bad.raise_for_status.return_value = None
        bad.json.return_value = {"unexpected": "shape"}  # no "current" key
        at = run_app(bad)
        self.assertEqual(len(at.exception), 0)
        self.assertIn("temporarily unavailable", markdown_text(at))


class BirthdaySeasonTests(unittest.TestCase):
    def test_valid_birthday_shows_the_correct_season_card(self):
        at = pick_birthday(run_app(), day=15, month=7, year=2015)
        self.assertEqual(len(at.exception), 0)
        self.assertIn("You were born in Makuru", markdown_text(at))

    def test_leap_day_in_a_leap_year_is_accepted(self):
        at = pick_birthday(run_app(), day=29, month=2, year=2016)
        self.assertEqual(len(at.error), 0)
        self.assertIn("You were born in Bunuru", markdown_text(at))

    def test_leap_day_in_a_non_leap_year_is_rejected(self):
        at = pick_birthday(run_app(), day=29, month=2, year=2015)
        self.assertEqual(len(at.error), 1)
        self.assertIn("doesn't exist", at.error[0].value)

    def test_impossible_date_31_april_is_rejected(self):
        at = pick_birthday(run_app(), day=31, month=4, year=2010)
        self.assertEqual(len(at.error), 1)
        self.assertIn("doesn't exist", at.error[0].value)

    def test_birthday_before_1993_boundary_has_no_records(self):
        at = pick_birthday(run_app(), day=31, month=12, year=1992)
        self.assertEqual(len(at.error), 1)
        self.assertIn("No weather records", at.error[0].value)

    def test_birthday_in_the_future_has_no_records(self):
        year = datetime.now().year
        at = pick_birthday(run_app(), day=31, month=12, year=year)
        self.assertIn("No weather records", " ".join(e.value for e in at.error))


class SeasonButtonTests(unittest.TestCase):
    def test_clicking_the_open_season_closes_it(self):
        at = run_app()
        current = at.session_state["open_season"]
        at.button(key=f"season-btn-click-{current.lower()}").click()
        at.run()
        self.assertIsNone(at.session_state["open_season"])

    def test_clicking_a_different_season_swaps_to_it(self):
        at = run_app()
        current = at.session_state["open_season"]
        other = next(s for s in SEASONS if s != current)
        at.button(key=f"season-btn-click-{other.lower()}").click()
        at.run()
        self.assertEqual(at.session_state["open_season"], other)


if __name__ == "__main__":
    unittest.main(verbosity=2)