"""Rainfall forecast client (Parul).

Uses Open-Meteo (free, no API key). Any failure returns None so the rest of the
system keeps working - a missing forecast must never crash the alert loop, and
the risk engine treats a missing forecast as "no extra information".
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Dict, Optional, Tuple

import requests

URL = "https://api.open-meteo.com/v1/forecast"
_CACHE: Dict[Tuple[float, float], Tuple[float, dict]] = {}
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


def get_forecast(lat: float, lon: float, session=requests, now: Optional[dt.datetime] = None,
                 use_cache: bool = True) -> Optional[dict]:
    key = (round(lat, 2), round(lon, 2))
    mono = time.monotonic()
    if use_cache and key in _CACHE and mono - _CACHE[key][0] < TTL_SECONDS:
        return _CACHE[key][1]
    try:
        r = session.get(URL, params={"latitude": lat, "longitude": lon, "hourly": "precipitation",
                                     "forecast_days": 4, "timezone": "UTC"}, timeout=10)
        r.raise_for_status()
        now = now or dt.datetime.now(dt.timezone.utc)
        result = parse_open_meteo(r.json(), now)
    except Exception:
        return None
    if result is not None:
        _CACHE[key] = (mono, result)
    return result
