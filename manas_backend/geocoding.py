"""Place-name lookup through the Open-Meteo geocoding API."""
from __future__ import annotations

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


def parse_locations(payload: dict) -> list[dict]:
    locations = []
    for item in payload.get("results", [])[:6]:
        try:
            lat, lon = float(item["latitude"]), float(item["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        parts = [item.get("name"), item.get("admin2"), item.get("admin1"), item.get("country")]
        label = ", ".join(dict.fromkeys(str(part) for part in parts if part))
        locations.append({
            "id": item.get("id"), "name": item.get("name", label), "label": label,
            "latitude": round(lat, 6), "longitude": round(lon, 6),
            "admin1": item.get("admin1"), "admin2": item.get("admin2"),
            "country": item.get("country"), "timezone": item.get("timezone"),
        })
    return locations


def search_locations(query: str, session=requests) -> list[dict]:
    response = session.get(GEOCODING_URL, params={
        "name": query.strip(), "count": 6, "language": "en", "format": "json", "countryCode": "IN",
    }, timeout=15)
    response.raise_for_status()
    return parse_locations(response.json())
