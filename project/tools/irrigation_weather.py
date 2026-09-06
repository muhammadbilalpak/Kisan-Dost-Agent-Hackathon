"""
Kisan Dost — Irrigation & Weather Tool
=========================================
Advises on irrigation scheduling and weather risks by district, crop, and stage.
Returns typed IrrigationAdvice Pydantic model.

Real API Bonus:
  Uses Open-Meteo Weather API and Open-Meteo Geocoding API (no API keys required)
  for live weather data. Falls back to offline static data if API is unavailable.
"""

from __future__ import annotations

import urllib.request
import json

from agents import function_tool
from models.schemas import IrrigationAdvice

# Pakistan district coordinates for Open-Meteo Geocoding fallback
DISTRICT_COORDS: dict[str, dict] = {
    "multan": {"lat": 30.20, "lon": 71.45},
    "bahawalpur": {"lat": 29.40, "lon": 71.68},
    "rahim yar khan": {"lat": 28.42, "lon": 70.30},
    "faisalabad": {"lat": 31.42, "lon": 73.08},
    "lahore": {"lat": 31.55, "lon": 74.35},
    "sahiwal": {"lat": 30.67, "lon": 73.11},
    "gujranwala": {"lat": 32.16, "lon": 74.19},
    "rawalpindi": {"lat": 33.60, "lon": 73.05},
    "quetta": {"lat": 30.18, "lon": 67.01},
    "hyderabad": {"lat": 25.40, "lon": 68.37},
    "sukkur": {"lat": 27.70, "lon": 68.86},
    "peshawar": {"lat": 34.01, "lon": 71.58},
    "vehari": {"lat": 30.04, "lon": 72.35},
    "khanewal": {"lat": 30.30, "lon": 71.93},
    "d g khan": {"lat": 30.05, "lon": 70.64},
    "jhang": {"lat": 31.27, "lon": 72.32},
    "sargodha": {"lat": 32.08, "lon": 72.67},
    "okara": {"lat": 30.81, "lon": 73.45},
}

# Regional climate baselines for Pakistani agricultural zones (offline fallback)
DISTRICT_CLIMATES: dict[str, dict] = {
    "multan": {"region": "south_punjab", "avg_temp": "28C - 38C", "heat_prone": True, "frost_prone": False},
    "bahawalpur": {"region": "south_punjab", "avg_temp": "30C - 40C", "heat_prone": True, "frost_prone": False},
    "rahim yar khan": {"region": "south_punjab", "avg_temp": "31C - 41C", "heat_prone": True, "frost_prone": False},
    "faisalabad": {"region": "central_punjab", "avg_temp": "22C - 34C", "heat_prone": True, "frost_prone": True},
    "lahore": {"region": "central_punjab", "avg_temp": "20C - 32C", "heat_prone": False, "frost_prone": True},
    "sahiwal": {"region": "central_punjab", "avg_temp": "24C - 35C", "heat_prone": True, "frost_prone": False},
    "gujranwala": {"region": "north_punjab", "avg_temp": "18C - 30C", "heat_prone": False, "frost_prone": True},
    "rawalpindi": {"region": "potohar", "avg_temp": "15C - 27C", "heat_prone": False, "frost_prone": True},
    "quetta": {"region": "balochistan_highlands", "avg_temp": "5C - 18C", "heat_prone": False, "frost_prone": True},
    "hyderabad": {"region": "lower_sindh", "avg_temp": "28C - 36C", "heat_prone": True, "frost_prone": False},
    "sukkur": {"region": "upper_sindh", "avg_temp": "32C - 42C", "heat_prone": True, "frost_prone": False},
    "peshawar": {"region": "kpk_valley", "avg_temp": "18C - 29C", "heat_prone": False, "frost_prone": True},
}


def _geocode_district(district: str) -> tuple[float, float] | None:
    """Use Open-Meteo Geocoding API to resolve district name to coordinates.
    No API key required. Returns (latitude, longitude) or None on failure.
    """
    # First try local lookup
    dist_lower = district.lower().strip()
    if dist_lower in DISTRICT_COORDS:
        coords = DISTRICT_COORDS[dist_lower]
        return coords["lat"], coords["lon"]

    # Fallback: Open-Meteo Geocoding API
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={district}&count=1&language=en&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "KisanDost/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "results" in data and len(data["results"]) > 0:
                r = data["results"][0]
                return r["latitude"], r["longitude"]
    except Exception:
        pass

    return None


def _fetch_open_meteo_weather(lat: float, lon: float) -> dict | None:
    """Fetch current weather from Open-Meteo Weather API (no API key required).
    Returns dict with temperature_2m, relative_humidity_2m, precipitation,
    wind_speed_10m, and weather_code or None on failure.
    """
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
            f"&forecast_days=3"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&timezone=Asia%2FKarachi"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "KisanDost/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception:
        return None


def _build_weather_summary(
    weather_data: dict,
    district: str,
    is_heat_crop: bool = False,
    is_frost_crop: bool = False,
    climate: dict | None = None,
) -> tuple[str, bool, bool]:
    """Build weather summary string and risk flags from Open-Meteo response.
    Returns (weather_summary, frost_risk, heatwave_risk).
    """
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    temp = current.get("temperature_2m", "N/A")
    humidity = current.get("relative_humidity_2m", "N/A")
    precip = current.get("precipitation", 0)
    wind = current.get("wind_speed_10m", "N/A")

    # 3-day forecast
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip_sums = daily.get("precipitation_sum", [])
    dates = daily.get("time", [])

    forecast_parts = []
    for i, date in enumerate(dates[:3]):
        t_max = max_temps[i] if i < len(max_temps) else "?"
        t_min = min_temps[i] if i < len(min_temps) else "?"
        p_sum = precip_sums[i] if i < len(precip_sums) else 0
        rain_note = f", Rain: {p_sum}mm" if p_sum and p_sum > 0 else ""
        forecast_parts.append(f"{date}: {t_min}C-{t_max}C{rain_note}")

    forecast_text = " | ".join(forecast_parts) if forecast_parts else "No forecast available"

    # Risk assessment (cotton/maize suffer heat stress at >= 38C; winter crops frost at <= 3C)
    frost_risk = False
    heatwave_risk = False

    if min_temps:
        frost_risk = any(t is not None and t <= 2.0 for t in min_temps) or (
            is_frost_crop and any(t is not None and t <= 4.0 for t in min_temps)
        )
    if max_temps:
        heatwave_risk = any(t is not None and t >= 42.0 for t in max_temps) or (
            is_heat_crop and any(t is not None and t >= 38.0 for t in max_temps)
        )

    if climate and climate.get("heat_prone") and is_heat_crop:
        if any(t is not None and t >= 36.0 for t in max_temps):
            heatwave_risk = True

    summary = (
        f"{district.title()} LIVE weather: {temp}C, Humidity: {humidity}%, "
        f"Precip: {precip}mm, Wind: {wind} km/h. "
        f"3-day forecast: {forecast_text}."
    )

    return summary, frost_risk, heatwave_risk


@function_tool
def irrigation_weather_advisor(
    district: str,
    crop: str,
    crop_stage: str,
) -> IrrigationAdvice:
    """Provide irrigation timing and weather alerts for a crop and district.

    Uses Open-Meteo Weather API (no API key required) for real-time weather data.
    Falls back to offline static data if API is unavailable.

    Args:
        district: Farmer's district (e.g. 'Multan', 'Faisalabad').
        crop: Cultivated crop name (e.g. 'wheat', 'cotton', 'rice').
        crop_stage: Growth stage (e.g. 'sowing', 'tillering', 'flowering', 'boll formation').
    """
    # ── Validation ──
    dist_clean = district.strip().lower() if district else "multan"
    crop_clean = crop.strip().lower() if crop else "wheat"
    stage_clean = crop_stage.strip().lower() if crop_stage else "vegetative"

    # Determine irrigation timing in days based on crop and growth stage
    if "rice" in crop_clean:
        days = 3
        irrig_note = f"Paddy in {stage_clean} stage requires shallow standing water (2-3 inches)."
    elif "cotton" in crop_clean:
        if any(s in stage_clean for s in ["flower", "boll", "phool", "tindi"]):
            days = 7
            irrig_note = f"Cotton is at critical reproductive stage ({stage_clean}). Moisture stress causes flower/boll drop."
        else:
            days = 12
            irrig_note = f"Cotton at vegetative stage ({stage_clean}). Irrigate to avoid leaf wilting."
    elif "wheat" in crop_clean or "gandum" in crop_clean:
        if any(s in stage_clean for s in ["cri", "crown", "kor", "pehla pani"]):
            days = 4
            irrig_note = "Crown Root Initiation (CRI) stage is critical! First irrigation must not be delayed."
        elif any(s in stage_clean for s in ["flower", "boora", "milking", "doodhiya"]):
            days = 8
            irrig_note = f"Wheat at {stage_clean} stage. Avoid irrigating on windy days to prevent lodging."
        else:
            days = 14
            irrig_note = f"Wheat crop at {stage_clean} stage in healthy condition."
    elif "maize" in crop_clean or "makki" in crop_clean:
        days = 6 if "tassel" in stage_clean or "flower" in stage_clean else 9
        irrig_note = f"Maize at {stage_clean} stage requires adequate root zone moisture."
    elif "sugarcane" in crop_clean or "ganna" in crop_clean:
        days = 10
        irrig_note = f"Sugarcane at {stage_clean} stage needs regular scheduled watering."
    else:
        days = 10
        irrig_note = f"{crop_clean.title()} at {stage_clean} stage in {dist_clean.title()}."

    # Try Open-Meteo real API first
    coords = _geocode_district(dist_clean)
    weather_data = None
    if coords:
        weather_data = _fetch_open_meteo_weather(coords[0], coords[1])

    climate = DISTRICT_CLIMATES.get(dist_clean, {
        "region": "general_plains",
        "avg_temp": "24C - 34C",
        "heat_prone": False,
        "frost_prone": False,
    })
    is_heat_crop = any(c in crop_clean for c in ["cotton", "maize", "sugarcane"])
    is_frost_crop = any(c in crop_clean for c in ["potato", "mustard", "wheat"])

    if weather_data:
        # Real API weather
        weather_summary, frost_risk, heatwave_risk = _build_weather_summary(
            weather_data, dist_clean, is_heat_crop, is_frost_crop, climate
        )
        weather_summary = f"{weather_summary} {irrig_note}"
    else:
        # Offline fallback
        heat_risk_flag = climate["heat_prone"] and is_heat_crop
        frost_risk_flag = climate["frost_prone"] and is_frost_crop

        weather_summary = (
            f"{dist_clean.title()} forecast (offline): Fair to partly cloudy, temps {climate['avg_temp']}. {irrig_note}"
        )
        frost_risk = frost_risk_flag
        heatwave_risk = heat_risk_flag

    return IrrigationAdvice(
        next_irrigation_in_days=days,
        weather_summary=weather_summary,
        frost_risk=frost_risk,
        heatwave_risk=heatwave_risk,
    )


# Backward-compatible alias
irrigation_weather = irrigation_weather_advisor
