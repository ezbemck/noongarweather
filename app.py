import streamlit as st # this is the streamlit library that is being used to create the web app
import plotly.express as px # this is the plotly library that is being used to create the graphs

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

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Past Data", "Info", "Unsure?"],
    index=["Home", "Past Data", "Info", "Unsure?"].index(
        st.session_state["page"]
    )
)

st.session_state["page"] = page

season_colours = {
    "Birak": "#C96A3D",
    "Bunuru": "#E5B73B",
    "Djeran": "#C97C6D",
    "Makuru": "#4A6FA5",
    "Djilba": "#4F9D69",
    "Kambarang": "#F2A93B",
}

# home page 
if page == "Home":
    st.title("Noongar Weather") # this is the title of the page
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

    st.write("")

    #this button is used to navigate to the past data page from the home page 
    if st.button("Explore Past Data"):
        st.session_state["page"] = "Past Data"
        st.rerun()



 
#past data second page 
elif page == "Past Data":
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

        season_chart_colours = {#this is the colour that is being used for the chart based on the selected season
            "Birak": "#C96A3D",
            "Bunuru": "#E5B73B",
            "Djeran": "#C97C6D",
            "Makuru": "#4A6FA5",
            "Djilba": "#4F9D69",
            "Kambarang": "#F2A93B",}
        
        chart_accent = season_chart_colours.get(#this is the accent colour that is being used for the chart based on the selected season
            selected_season, 
            "#4F9D69")


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

                # Add a year column so the data can be grouped by year
                filtered_data["year"] = filtered_data["date"].dt.year

                # Work out yearly temperature averages and rainfall totals
                yearly_data = (
                    filtered_data.groupby("year")
                    .agg(
                        max_temperature=("temp_max", "mean"),
                        min_temperature=("temp_min", "mean"),
                        total_rainfall=("rainfall_mm", "sum"),
                    )
                    .reset_index())

                # Temperature chart
                st.subheader("Temperature by Year")

                yearly_data["year"] = yearly_data["year"].astype(str)

                temperature_chart = px.line(
                    yearly_data,
                    x="year",
                    y=["max_temperature", "min_temperature"],
                    markers=True,
                    labels={
                        "year": "Year",
                        "value": "Temperature (°C)",
                        "variable": "Temperature",
                    },
                    color_discrete_sequence=[
                        chart_accent,
                          "#8BBFD9",],)
                
                temperature_chart.for_each_trace(# this is used to rename the traces in the chart to be more user friendly
                    lambda trace: trace.update(
                        name={
                            "max_temperature": "Maximum Temperature",
                            "min_temperature": "Minimum Temperature",
                            }.get(trace.name, trace.name)
                    ) )

                st.plotly_chart(# this is used to display the chart on the page
                    temperature_chart,
                    use_container_width=True )

                # Rainfall chart
                st.subheader("Total Rainfall by Year")

                rainfall_chart = px.bar(
                    yearly_data,
                    x="year",
                    y="total_rainfall",
                    labels={
                        "year": "Year",
                        "total_rainfall": "Total Rainfall (mm)",
                    },
                    color_discrete_sequence=[chart_accent],)

                st.plotly_chart(
                    rainfall_chart,
                    use_container_width=True
                )

        except ValueError as error:
            st.error(str(error))

        except ValueError as error:
            st.error(str(error))




#infomation page third page
elif page == "Info":
    st.title("Learn About the Noongar Seasons")
    st.write("Information about the six Noongar seasons will go here.")

#Not sure what the page is going to be yet
elif page == "Unsure?":
    st.title("Unsure Which Season?")
    st.write("Use this page to help identify a season.")