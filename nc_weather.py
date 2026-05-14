"""
NC Weather Fetcher - Phase 1 (with caching)
Pulls 7-day forecasts for key NC locations using the NWS API (api.weather.gov).
No API key required. Free to use.

Caching: grid info (lat/lon → NWS grid URLs) is saved to grid_cache.json
on the first run and reused on every subsequent run. Only forecast data
is fetched fresh each time.
"""

import requests
import json
import os

# ── Configuration ──────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "NCWeatherPage/1.0 (ethanwolffy@gmail.com)",
    "Accept": "application/geo+json"
}

GRID_CACHE_FILE = "grid_cache.json"

LOCATIONS = {
    # Mountains
    "Asheville":        (35.5951, -82.5515),
    "Boone":            (36.2168, -81.6746),
    "Bryson City":      (35.4329, -83.4457),
    "Hendersonville":   (35.3187, -82.4604),
    "Murphy":           (35.0885, -84.0169),
    # Piedmont
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
    # Eastern / Coastal
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

# ── Grid cache helpers ─────────────────────────────────────────────────────────

def load_grid_cache():
    """Load cached grid info from disk if it exists."""
    if os.path.exists(GRID_CACHE_FILE):
        with open(GRID_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_grid_cache(cache):
    """Save grid info to disk."""
    with open(GRID_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"Grid cache saved to {GRID_CACHE_FILE}")

def get_grid_info(city, lat, lon):
    """
    Call the /points endpoint to resolve a lat/lon to an NWS grid.
    Returns grid metadata including forecast URLs.
    """
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

def resolve_grids():
    """
    Return grid info for all locations.
    Loads from cache if available; fetches from API for any missing entries
    and updates the cache.
    """
    cache = load_grid_cache()
    updated = False

    for city, (lat, lon) in LOCATIONS.items():
        if city not in cache:
            print(f"  Resolving grid for {city} (not in cache)...")
            try:
                cache[city] = get_grid_info(city, lat, lon)
                updated = True
            except Exception as e:
                print(f"  ⚠ Could not resolve grid for {city}: {e}")

    if updated:
        save_grid_cache(cache)
    else:
        print("All grids loaded from cache — no API calls needed.")

    return cache

# ── Forecast fetching ──────────────────────────────────────────────────────────

def get_forecast(grid_info):
    """
    Fetch the 7-day forecast for a location using its cached grid URL.
    This is called fresh every run since forecast data changes frequently.
    """
    response = requests.get(grid_info["forecast_url"], headers=HEADERS, timeout=10)
    response.raise_for_status()
    periods = response.json()["properties"]["periods"]

    forecast = []
    for period in periods:
        forecast.append({
            "name":         period["name"],
            "is_daytime":   period["isDaytime"],
            "temp":         period["temperature"],
            "temp_unit":    period["temperatureUnit"],
            "wind_speed":   period["windSpeed"],
            "wind_dir":     period["windDirection"],
            "short_desc":   period["shortForecast"],
            "detail":       period["detailedForecast"],
            "precip_pct":   period.get("probabilityOfPrecipitation", {}).get("value"),
        })
    return forecast

# ── Main ───────────────────────────────────────────────────────────────────────

def fetch_all_nc_weather():
    print("── Resolving grids ──")
    grids = resolve_grids()

    print("\n── Fetching forecasts ──")
    results = {}
    for city, grid_info in grids.items():
        print(f"  Fetching forecast: {city}...")
        try:
            results[city] = {
                "grid": grid_info,
                "forecast": get_forecast(grid_info)
            }
        except Exception as e:
            print(f"  ⚠ Error fetching {city}: {e}")
            results[city] = {"error": str(e)}

    return results

if __name__ == "__main__":
    weather_data = fetch_all_nc_weather()

    with open("nc_weather_output.json", "w") as f:
        json.dump(weather_data, f, indent=2)

    print("\nDone! Output saved to nc_weather_output.json")

    # Quick preview
    sample = weather_data.get("Raleigh", {})
    if "forecast" in sample:
        print("\n── Raleigh Forecast Preview ──")
        for period in sample["forecast"][:3]:
            print(f"  {period['name']}: {period['temp']}°{period['temp_unit']} — {period['short_desc']}")