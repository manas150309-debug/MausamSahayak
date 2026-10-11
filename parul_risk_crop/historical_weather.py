"""NASA POWER historical weather dataset utilities.

The bundled snapshot is evidence for retrospective analysis, not a live sensor
replacement. Source: NASA POWER daily point API, agroclimatology community.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from statistics import mean

import requests

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
FIELDS = ("date", "temperature_c", "temperature_min_c", "temperature_max_c", "humidity_pct", "precipitation_mm")


def parse_power(payload: dict) -> list[dict]:
    params = payload.get("properties", {}).get("parameter", {})
    required = ("T2M", "T2M_MIN", "T2M_MAX", "RH2M", "PRECTOTCORR")
    if not all(isinstance(params.get(k), dict) for k in required):
        raise ValueError("NASA POWER response is missing required parameters")
    rows = []
    for day in sorted(params["T2M"]):
        values = [params[k].get(day) for k in required]
        if any(v is None or float(v) <= -990 for v in values):
            continue
        rows.append(dict(zip(FIELDS, [dt.datetime.strptime(day, "%Y%m%d").date().isoformat(), *map(float, values)])))
    return rows


def fetch_power(lat: float, lon: float, start: str, end: str, session=requests) -> list[dict]:
    response = session.get(POWER_URL, params={
        "parameters": "T2M,T2M_MIN,T2M_MAX,RH2M,PRECTOTCORR", "community": "AG",
        "longitude": lon, "latitude": lat, "start": start, "end": end,
        "format": "JSON", "time-standard": "LST",
    }, timeout=45)
    response.raise_for_status()
    return parse_power(response.json())


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_summary(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("historical dataset is empty")
    rain = [float(r["precipitation_mm"]) for r in rows]
    temperatures = [float(r["temperature_c"]) for r in rows]
    humidities = [float(r["humidity_pct"]) for r in rows]
    wettest = max(rows, key=lambda r: float(r["precipitation_mm"]))
    return {
        "source": "NASA POWER",
        "period": {"start": rows[0]["date"], "end": rows[-1]["date"]},
        "days": len(rows),
        "mean_temperature_c": round(mean(temperatures), 1),
        "mean_humidity_pct": round(mean(humidities), 1),
        "total_precipitation_mm": round(sum(rain), 1),
        "rainy_days": sum(v >= 1.0 for v in rain),
        "wettest_day": {"date": wettest["date"], "precipitation_mm": round(float(wettest["precipitation_mm"]), 1)},
        "purpose": "Historical climate baseline for retrospective comparison; not a flood warning source.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--lat", type=float, default=28.4089)
    parser.add_argument("--lon", type=float, default=77.3178)
    parser.add_argument("--start", default="20250101")
    parser.add_argument("--end", default="20251231")
    args = parser.parse_args(argv)
    write_csv(fetch_power(args.lat, args.lon, args.start, args.end), args.output)
    print(json.dumps(load_summary(args.output), indent=2))


if __name__ == "__main__":
    main()
