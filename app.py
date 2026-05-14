"""
NC Weather Dashboard - Streamlit App
Displays forecast data from nc_weather_output.json
Run with: streamlit run app.py
"""

import streamlit as st
import json
import os
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NC Weather",
    page_icon="⛅",
    layout="wide"
)

# ── Styling ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace;
    }
    .region-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #888;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.4rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    .city-card {
        background: #f9f9f9;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .city-card:hover {
        background: #f0f4ff;
        border-color: #b0c4ff;
    }
    .city-name {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        color: #1a1a2e;
    }
    .city-temp {
        font-size: 1.4rem;
        font-weight: 300;
        color: #1a1a2e;
    }
    .city-desc {
        font-size: 0.78rem;
        color: #666;
        margin-top: 0.1rem;
    }
    .precip {
        font-size: 0.75rem;
        color: #4a7fd4;
        font-family: 'IBM Plex Mono', monospace;
    }
    .forecast-period {
        background: #f9f9f9;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 0.9rem;
        margin-bottom: 0.4rem;
    }
    .period-name {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #888;
    }
    .period-temp {
        font-size: 1.6rem;
        font-weight: 300;
        color: #1a1a2e;
        line-height: 1.2;
    }
    .period-desc {
        font-size: 0.82rem;
        color: #444;
        margin-top: 0.25rem;
    }
    .period-detail {
        font-size: 0.75rem;
        color: #888;
        margin-top: 0.4rem;
        line-height: 1.5;
    }
    .wind-info {
        font-size: 0.75rem;
        color: #666;
        font-family: 'IBM Plex Mono', monospace;
        margin-top: 0.3rem;
    }
    .stButton button {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
    }
    .last-updated {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #aaa;
    }
</style>
""", unsafe_allow_html=True)

# ── Region groupings ───────────────────────────────────────────────────────────

REGIONS = {
    "Mountains": ["Asheville", "Boone", "Bryson City", "Hendersonville", "Murphy"],
    "Piedmont":  ["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem",
                  "Fayetteville", "High Point", "Concord", "Gastonia", "Sanford", "Statesville"],
    "Coast":     ["Wilmington", "New Bern", "Greenville", "Rocky Mount", "Jacksonville",
                  "Goldsboro", "Outer Banks", "Morehead City", "Elizabeth City"],
}

REGION_ICONS = {
    "Mountains": "⛰️",
    "Piedmont": "🌾",
    "Coast": "🌊",
}

# ── Load data ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)  # cache for 30 minutes
def load_weather_data():
    path = "nc_weather_output.json"
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def get_today(forecast):
    """Return the first daytime period from a forecast."""
    for period in forecast:
        if period["is_daytime"]:
            return period
    return forecast[0] if forecast else None

def get_tonight(forecast):
    """Return the first nighttime period from a forecast."""
    for period in forecast:
        if not period["is_daytime"]:
            return period
    return None

# ── App ────────────────────────────────────────────────────────────────────────

data = load_weather_data()

# Header
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown("# ⛅ NC Weather")
    st.markdown(f'<span class="last-updated">Last updated: {datetime.now().strftime("%B %d, %Y %I:%M %p")}</span>', unsafe_allow_html=True)
with col_refresh:
    st.write("")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

if data is None:
    st.error("No weather data found. Run `python nc_weather.py` first to fetch data.")
    st.stop()

# ── Layout: overview left, detail right ───────────────────────────────────────

col_overview, col_detail = st.columns([1.2, 1.8], gap="large")

with col_overview:
    st.markdown("### Today's Overview")

    selected_city = st.session_state.get("selected_city", "Raleigh")

    for region, cities in REGIONS.items():
        icon = REGION_ICONS[region]
        st.markdown(f'<div class="region-header">{icon} {region}</div>', unsafe_allow_html=True)

        for city in cities:
            city_data = data.get(city, {})
            if "error" in city_data or "forecast" not in city_data:
                continue

            today = get_today(city_data["forecast"])
            if not today:
                continue

            precip = today.get("precip_pct")
            precip_str = f"💧 {precip}%" if precip is not None else ""

            is_selected = city == selected_city
            card_style = "background:#e8f0ff; border-color:#7aa7ff;" if is_selected else ""

            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"""
                    <div class="city-card" style="{card_style}">
                        <div class="city-name">{city}</div>
                        <div class="city-desc">{today['short_desc']}</div>
                        {f'<div class="precip">{precip_str}</div>' if precip_str else ''}
                    </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                    <div class="city-card" style="{card_style}; text-align:right;">
                        <div class="city-temp">{today['temp']}°</div>
                        <div class="wind-info">{today['wind_dir']} {today['wind_speed']}</div>
                    </div>
                """, unsafe_allow_html=True)

            if st.button(f"View {city}", key=f"btn_{city}", use_container_width=True):
                st.session_state["selected_city"] = city
                st.rerun()

with col_detail:
    city = st.session_state.get("selected_city", "Raleigh")
    city_data = data.get(city, {})

    st.markdown(f"### {city} — 7-Day Forecast")

    if "error" in city_data:
        st.error(f"Could not load data for {city}.")
    elif "forecast" not in city_data:
        st.warning("No forecast data available.")
    else:
        forecast = city_data["forecast"]
        grid = city_data.get("grid", {})

        # Grid info badge
        st.markdown(f'<span class="last-updated">NWS Office: {grid.get("office","")} · Grid: {grid.get("gridX","")},{grid.get("gridY","")}</span>', unsafe_allow_html=True)
        st.write("")

        # Show all forecast periods
        for period in forecast:
            precip = period.get("precip_pct")
            precip_str = f"💧 {precip}% chance of precip" if precip is not None else ""

            day_night = "☀️" if period["is_daytime"] else "🌙"

            st.markdown(f"""
                <div class="forecast-period">
                    <div class="period-name">{day_night} {period['name']}</div>
                    <div class="period-temp">{period['temp']}°{period['temp_unit']}</div>
                    <div class="period-desc">{period['short_desc']}</div>
                    <div class="wind-info">💨 {period['wind_dir']} {period['wind_speed']}</div>
                    {f'<div class="precip">{precip_str}</div>' if precip_str else ''}
                    <div class="period-detail">{period['detail']}</div>
                </div>
            """, unsafe_allow_html=True)