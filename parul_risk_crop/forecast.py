"""Rainfall forecast clients (Parul).

AccuWeather is preferred when ``ACCUWEATHER_API_KEY`` is configured. Open-Meteo
is the zero-secret fallback. Any provider failure degrades safely: a missing
forecast never crashes the alert loop or gets interpreted as safe weather.
"""
from __future__ import annotations

import datetime as dt
import os
import time
from typing import Dict, Optional, Tuple

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
ACCUWEATHER_BASE = "https://dataservice.accuweather.com"
_CACHE: Dict[Tuple[str, float, float], Tuple[float, dict]] = {}
TTL_SECONDS = 30 * 60


def parse_open_meteo(payload: dict, now: dt.datetime) -> Optional[dict]:
    """Sum hourly precipitation for the next 24 h and 72 h from `now` (UTC)."""
    hourly = payload.get("hourly") or {}
    times, precip = hourly.get("time"), hourly.get("precipitation")
    if not times or not precip or len(times) != len(precip):
        return None
    n24 = n72 = 0.0
    seen = 0
    for t, p in zip(times, precip):
        if p is None:
            continue
        ts = dt.datetime.fromisoformat(t).replace(tzinfo=dt.timezone.utc)
        delta = (ts - now).total_seconds() / 3600.0
        if 0 < delta <= 24:
            n24 += p
        if 0 < delta <= 72:
            n72 += p
            seen += 1
    if seen < 24:          # too little coverage to trust
        return None
    return {"next_24h_mm": round(n24, 1), "next_72h_mm": round(n72, 1), "source": "open-meteo"}


def parse_accuweather_hourly(payload: list) -> Optional[dict]:
    """Aggregate metric hourly rain values returned by AccuWeather."""
    if not isinstance(payload, list) or len(payload) < 24:
        return None
    values = []
    for hour in payload[:72]:
        rain = (hour or {}).get("Rain") or {}
        value = rain.get("Value")
        if value is None:
            value = ((hour or {}).get("TotalLiquid") or {}).get("Value")
        try:
            values.append(max(0.0, float(value or 0.0)))
        except (TypeError, ValueError):
            values.append(0.0)
    return {
        "next_24h_mm": round(sum(values[:24]), 1),
        "next_72h_mm": round(sum(values[:72]), 1),
        "source": "accuweather",
    }


def get_accuweather_forecast(lat: float, lon: float, api_key: str, session=requests) -> Optional[dict]:
    """Resolve a coordinate to an AccuWeather location key, then fetch 72 h."""
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    location = session.get(
        f"{ACCUWEATHER_BASE}/locations/v1/geoposition/search",
        params={"q": f"{lat:.4f},{lon:.4f}"}, headers=headers, timeout=6,
    )
    location.raise_for_status()
    location_payload = location.json()
    if isinstance(location_payload, list):
        location_payload = location_payload[0] if location_payload else {}
    location_key = (location_payload or {}).get("Key")
    if not location_key:
        return None
    hourly = session.get(
        f"{ACCUWEATHER_BASE}/forecasts/v1/hourly/72hour/{location_key}",
        params={"metric": "true", "details": "true"}, headers=headers, timeout=8,
    )
    hourly.raise_for_status()
    return parse_accuweather_hourly(hourly.json())


def get_forecast(lat: float, lon: float, session=requests, now: Optional[dt.datetime] = None,
                 use_cache: bool = True, api_key: Optional[str] = None) -> Optional[dict]:
    api_key = api_key if api_key is not None else os.environ.get("ACCUWEATHER_API_KEY", "")
    provider = "accuweather" if api_key else "open-meteo"
    key = (provider, round(lat, 2), round(lon, 2))
    mono = time.monotonic()
    if use_cache and key in _CACHE and mono - _CACHE[key][0] < TTL_SECONDS:
        return _CACHE[key][1]
    try:
        result = get_accuweather_forecast(lat, lon, api_key, session) if api_key else None
    except Exception:
        result = None
    if result is None:
        try:
            r = session.get(OPEN_METEO_URL, params={"latitude": lat, "longitude": lon, "hourly": "precipitation",
                                                    "forecast_days": 4, "timezone": "UTC"}, timeout=6)
            r.raise_for_status()
            now = now or dt.datetime.now(dt.timezone.utc)
            result = parse_open_meteo(r.json(), now)
        except Exception:
            return None
    if result is not None:
        _CACHE[key] = (mono, result)
    return result


def get_current_conditions(lat: float, lon: float, session=requests) -> Optional[dict]:
    """Fetch location-specific agronomic inputs for places outside the sensor network."""
    try:
        response = session.get(OPEN_METEO_URL, params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,soil_moisture_0_to_1cm",
            "timezone": "auto",
        }, timeout=8)
        response.raise_for_status()
        current = response.json().get("current") or {}
        temperature = float(current["temperature_2m"])
        humidity = current.get("relative_humidity_2m")
        soil_fraction = current.get("soil_moisture_0_to_1cm")
        return {
            "temperature_c": round(temperature, 1),
            "humidity_pct": None if humidity is None else round(float(humidity), 1),
            "soil_moisture_pct": None if soil_fraction is None else round(float(soil_fraction) * 100, 1),
            "source": "Open-Meteo location forecast",
        }
    except (KeyError, TypeError, ValueError, requests.RequestException):
        return None
