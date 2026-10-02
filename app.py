import streamlit as st # this is the streamlit library that is being used to create the web app
import plotly.express as px # this is the plotly library that is being used to create the graphs
import json

from src.weather_service import (
    filter_historical_weather,
    get_current_weather,
    get_season_dashboard,
    load_processed_data,
)

data = load_processed_data()

st.set_page_config(
    page_title="Noongar Weather",
    page_icon="🌿",
    layout="wide",
)

st.markdown(
    "<h1 style='font-size: 70px;'>Noongar Weather</h1>",
    unsafe_allow_html=True)# changed this to be more tabs rather than buttons

home_tab, past_tab, info_tab, why_tab = st.tabs(
    ["Home", "Past Data", "Info", "Why 6 Seasons?"])


season_colours = {
    "Birak": "#C96A3D",
    "Bunuru": "#E5B73B",
    "Djeran": "#C97C6D",
    "Makuru": "#4A6FA5",
    "Djilba": "#4F9D69",
    "Kambarang": "#F2A93B",
}

# home page 
with home_tab:
    st.title("Boorloo Weather Today") # this is the title of the page
    st.write("Explore Perth weather alongside the six Noongar seasons.")# this is the description of the page

    current_weather = get_current_weather(data)#this is the function that gets the current weather data from the data file

    current_season = current_weather["noongar_season"] # this is the current season that is being displayed on the page
    accent = season_colours.get(current_season, "#4F9D69")#this is the accent colour that is being used on the page based on the current season

    #this next part is use for the style of the page
    st.markdown(f"""
    <style>
    div[data-testid="stMetric"] {{
        border-left: 6px solid {accent};
        padding-left: 15px;}}

    h1, h2, h3 {{color: {accent};}}
    </style>
    """,
    unsafe_allow_html=True)

    st.subheader("Latest Weather Record")# this is the subheader of the page

    st.write(
        f"Date: {current_weather['date']}  |  "
        f"Season: {current_weather['noongar_season']}" )
    #this is the date and season that is being displayed on the page

    st.markdown(
    f"""
<div style="background-color: {accent}20; border: 2px solid {accent}; border-radius: 12px; padding: 20px; margin-top: 10px; margin-bottom: 25px;">
<h3 style="margin: 0; color: {accent};">Current Noongar Season: {current_season}</h3>
<p style="margin-top: 8px;">Seasonal information will be added here from an approved source.</p>
</div>
""",
    unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4) # this is the columns that are being used to display the weather data

    with col1:
        st.metric(
            "Maximum Temperature",
            f"{current_weather['temp_max']} °C")

    with col2:
        st.metric(
            "Minimum Temperature",
            f"{current_weather['temp_min']} °C")

    with col3:
        st.metric(
            "Average Temperature",
            f"{current_weather['temp_avg']} °C")

    with col4:
        st.metric(
            "Rainfall",
            f"{current_weather['rainfall_mm']} mm")
        #these all display the current weather data in a metric format with the title and value

 
#past data second page 
with past_tab:
    st.title("Past Weather Data")
    st.write("Explore historical Perth weather records.")

    st.subheader("Choose your filters")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start date")

    with col2:
        end_date = st.date_input("End date")

    selected_season = st.selectbox(
        "Noongar season",
        [   "All Seasons",
            "Birak",
            "Bunuru",
            "Djeran",
            "Makuru",
            "Djilba",
            "Kambarang",])

    col3, col4 = st.columns(2)

    with col3:
        apply_filters = st.button("Apply filters")

    with col4:
        reset_filters = st.button("Reset")

    if apply_filters:
        season_filter = None if selected_season == "All Seasons" else selected_season

         #reuse the module-level season_colours dict instead of redefining it here
        chart_accent = season_colours.get(selected_season, "#4F9D69")


        try:
            filtered_data = filter_historical_weather(
                data,
                start_date=str(start_date),
                end_date=str(end_date),
                season=season_filter,
            )

            if filtered_data.empty:
                st.warning("No weather records found for those filters.")

            else:
                st.success(f"Found {len(filtered_data)} weather records.")
                st.dataframe(filtered_data)

                daily_data = filtered_data.sort_values("date")


                # Temperature chart
                st.subheader("Temperature by Day")


                temperature_chart = px.line(
                     daily_data,
                    x="date",
                    y=["temp_max", "temp_min"],
                    markers=True,
                    labels={
                        "date": "Date",
                        "value": "Temperature (°C)",
                        "variable": "Temperature",
                },
                color_discrete_sequence=[
                    chart_accent,
                     "#8BBFD9",
                    ],
                )

                temperature_chart.for_each_trace(# this is used to rename the traces in the chart to be more user friendly
                    lambda trace: trace.update(
                        name={
                            "max_temperature": "Maximum Temperature",
                            "min_temperature": "Minimum Temperature",
                            }.get(trace.name, trace.name)
                    ) )

                st.plotly_chart(
                    temperature_chart,
                    width="stretch"
                    )

                # Rainfall chart
                st.subheader("Rainfall by Day")

                rainfall_chart = px.bar(
                    daily_data,
                    x="date",
                    y="rainfall_mm",
                    labels={
                        "date": "Date",
                        "rainfall_mm": "Rainfall (mm)",
                    },
                    color_discrete_sequence=[
                        chart_accent,
                    "#8BBFD9",
                     ], 
                )

                st.plotly_chart(
                    rainfall_chart,
                    use_container_width=True
                )

        except ValueError as error:
            st.error(str(error))


#infomation page third page
with info_tab:
    st.title("Learn About the Noongar Seasons")
    st.write(
        "Explore the six Noongar seasons and the seasonal changes associated with them.")
    st.divider()

# Load season information from JSON file
    with open("data/seasons.json", "r") as file:
        seasons = json.load(file)

# Season selector
    selected_info_season = st.selectbox(
        "Choose a season to learn more",
        list(seasons.keys())
    )

    season_info = seasons[selected_info_season]

 # Season heading
    st.markdown(
        f"""
        <div style="
            border-left: 8px solid {season_info['colour']};
            background-color: {season_info['colour']}20;
            padding: 24px;
            border-radius: 12px;
            margin-top: 20px;
            margin-bottom: 20px;
        ">
            <h2>{selected_info_season}</h2>
            <p><strong>📅 Months:</strong> {season_info['months']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Seasonal Signs")
        for sign in season_info["seasonal_signs"]:
            st.write(f"• {sign}")

    with col2:
        st.subheader("Native Flowers")
        for flower in season_info["flowers"]:
            st.write(f"• {flower}")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Animals")
        for animal in season_info["animals"]:
            st.write(f"• {animal}")

    with col4:
        st.subheader("Seasonal Foods")
        for food in season_info["food"]:
            st.write(f"• {food}")

    st.subheader("Traditional Practices")
    for practice in season_info["traditional_practices"]:
        st.write(f"• {practice}")
        




    
    
#fourth page - why the app uses six Noongar seasons instead of the four European ones
with why_tab:
    st.title("Why Six Seasons?")
 
    st.write(
        "This app uses the Noongar six-season calendar instead of the "
        "familiar four-season European one. Here's why that distinction "
        "matters, especially for a Perth weather app."
    )
 
    st.markdown(
        """
The four-season calendar (summer, autumn, winter, spring) was built for the
Northern Hemisphere and doesn't map cleanly onto Perth's climate. The Noongar
six-season calendar, by contrast, comes from tens of thousands of years of
direct observation of this specific region — tracking real signals like
flowering plants, animal behaviour, wind direction, and rainfall, rather than
fixed calendar dates. The seasons can run long or short from year to year,
because they follow what's actually happening on Country, not a fixed date
range.
"""
    )
 
    st.subheader("Two calendars, one year")
    st.write(
        "Laid month-by-month, it's easy to see how little the four imported "
        "seasons line up with what's actually going on outside:"
    )
 
    st.markdown(
        """
| Month | European season | Noongar season |
|---|---|---|
| January | Summer | Birak |
| February | Summer | Bunuru |
| March | Autumn | Bunuru |
| April | Autumn | Djeran |
| May | Autumn | Djeran |
| June | Winter | Makuru |
| July | Winter | Makuru |
| August | Winter | Djilba |
| September | Spring | Djilba |
| October | Spring | Kambarang |
| November | Spring | Kambarang |
| December | Summer | Birak |
"""
    )
 
    st.write(
        "Notice August is labelled 'Winter', yet it's already Djilba — when "
        "the first wildflowers start to bloom. September is called "
        "'Spring', but it's still Djilba weather on the ground. The "
        "six-season calendar tracks what's actually changing, instead of "
        "forcing it into an imported four-box template."
    )
 
    st.subheader("What marks each season")
 
    season_indicators = {
        "Birak": (
            "Dec \u2013 Jan",
            "Rain eases and heat builds. Traditionally the fire season, "
            "with controlled burns used to renew the land."
        ),
        "Bunuru": (
            "Feb \u2013 Mar",
            "The hottest, driest stretch of the year. Traditionally a time "
            "to move toward coasts, rivers and estuaries for food."
        ),
        "Djeran": (
            "Apr \u2013 May",
            "The first cool nights and dewy mornings arrive, with red-"
            "flowering plants signalling the turn toward wetter weather."
        ),
        "Makuru": (
            "Jun \u2013 Jul",
            "The coldest and wettest season. Traditionally a shift inland "
            "as waterways rise and animals pair up to breed."
        ),
        "Djilba": (
            "Aug \u2013 Sep",
            "A changeable mix of cold mornings and emerging warmth, as the "
            "first wildflowers of the season begin to bloom."
        ),
        "Kambarang": (
            "Oct \u2013 Nov",
            "A burst of wildflowers and new growth as the land dries out "
            "again ahead of summer."
        ),
    }
 
    for season, (months, blurb) in season_indicators.items():
        accent = season_colours.get(season, "#4F9D69")
        st.markdown(
            f"""
<div style="border-left: 6px solid {accent}; background-color: {accent}15;
            border-radius: 8px; padding: 12px 18px; margin-bottom: 10px;">
<strong style="color: {accent};">{season}</strong>
<span style="color: #666;"> &middot; {months}</span>
<p style="margin: 6px 0 0 0;">{blurb}</p>
</div>
""",
            unsafe_allow_html=True,
        )
 
    st.caption(
        "Seasonal information draws on the Bureau of Meteorology's "
        "Indigenous Weather Knowledge resource and Tourism Western "
        "Australia, with respect to Noongar people as the custodians of "
        "this knowledge. For the full depth of this knowledge, see the "
        "Bureau of Meteorology and Noongar community sources directly."
    )
