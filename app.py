"""
NC Weather Dashboard - Streamlit App
Fetches live forecast data directly from the NWS API (api.weather.gov).
Run with: streamlit run app.py
"""

import streamlit as st
import requests
import json
import os

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
    .last-updated {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #aaa;
    }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "NCWeatherPage/1.0 (ethan.wolffy@gmail.com)",
    "Accept": "application/geo+json"
}

GRID_CACHE_FILE = "grid_cache.json"

LOCATIONS = {
    "Asheville":        (35.5951, -82.5515),
    "Boone":            (36.2168, -81.6746),
    "Bryson City":      (35.4329, -83.4457),
    "Hendersonville":   (35.3187, -82.4604),
    "Murphy":           (35.0885, -84.0169),
    "Charlotte":        (35.2271, -80.8431),
    "Raleigh":          (35.7796, -78.6382),
    "Greensboro":       (36.0726, -79.7920),
    "Durham":           (35.9940, -78.8986),
    "Winston-Salem":    (36.0999, -80.2442),
    "Fayetteville":     (35.0527, -78.8784),
    "High Point":       (35.9557, -80.0053),
    "Concord":          (35.4088, -80.5795),
    "Gastonia":         (35.2621, -81.1873),
    "Sanford":          (35.4799, -79.1803),
    "Statesville":      (35.7826, -80.8873),
    "Wilmington":       (34.2257, -77.9447),
    "New Bern":         (35.1085, -77.0441),
    "Greenville":       (35.6127, -77.3664),
    "Rocky Mount":      (35.9382, -77.7905),
    "Jacksonville":     (34.7540, -77.4302),
    "Goldsboro":        (35.3849, -77.9925),
    "Outer Banks":      (35.9060, -75.6799),
    "Morehead City":    (34.7232, -76.7235),
    "Elizabeth City":   (36.2946, -76.2511),
}

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

# ── Data fetching ──────────────────────────────────────────────────────────────

def load_grid_cache():
    if os.path.exists(GRID_CACHE_FILE):
        with open(GRID_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_grid_cache(cache):
    with open(GRID_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_grid_info(city, lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    props = response.json()["properties"]
    return {
        "city": city,
        "lat": lat,
        "lon": lon,
        "office": props["gridId"],
        "gridX": props["gridX"],
        "gridY": props["gridY"],
        "forecast_url": props["forecast"],
        "hourly_url": props["forecastHourly"]
    }

def get_forecast(grid_info):
    response = requests.get(grid_info["forecast_url"], headers=HEADERS, timeout=10)
    response.raise_for_status()
    periods = response.json()["properties"]["periods"]
    forecast = []
    for period in periods:
        forecast.append({
            "name":       period["name"],
            "is_daytime": period["isDaytime"],
            "temp":       period["temperature"],
            "temp_unit":  period["temperatureUnit"],
            "wind_speed": period["windSpeed"],
            "wind_dir":   period["windDirection"],
            "short_desc": period["shortForecast"],
            "detail":     period["detailedForecast"],
            "precip_pct": period.get("probabilityOfPrecipitation", {}).get("value"),
        })
    return forecast

@st.cache_data(ttl=1800)  # cache for 30 minutes
def fetch_all_weather():
    """Fetch forecasts for all locations. Grid info is cached to disk; forecasts are live."""
    cache = load_grid_cache()
    updated = False
    results = {}

    for city, (lat, lon) in LOCATIONS.items():
        try:
            # Resolve grid if not cached
            if city not in cache:
                cache[city] = get_grid_info(city, lat, lon)
                updated = True

            # Always fetch fresh forecast
            results[city] = {
                "grid": cache[city],
                "forecast": get_forecast(cache[city])
            }
        except Exception as e:
            results[city] = {"error": str(e)}

    if updated:
        save_grid_cache(cache)

    return results

def get_today(forecast):
    for period in forecast:
        if period["is_daytime"]:
            return period
    return forecast[0] if forecast else None

# ── App ────────────────────────────────────────────────────────────────────────

# Header
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown("# ⛅ NC Weather")
with col_refresh:
    st.write("")
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Load data with a spinner
with st.spinner("Loading forecasts..."):
    data = fetch_all_weather()

# ── Layout ─────────────────────────────────────────────────────────────────────

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
        st.error(f"Could not load data for {city}: {city_data['error']}")
    elif "forecast" not in city_data:
        st.warning("No forecast data available.")
    else:
        forecast = city_data["forecast"]
        grid = city_data.get("grid", {})

        st.markdown(f'<span class="last-updated">NWS Office: {grid.get("office","")} · Grid: {grid.get("gridX","")},{grid.get("gridY","")}</span>', unsafe_allow_html=True)
        st.write("")

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