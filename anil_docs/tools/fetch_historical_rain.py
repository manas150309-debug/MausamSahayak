"""Download historical daily rainfall and build a labelled CSV for threshold validation (Anil -> Parul).

Rainfall comes from Open-Meteo's archive API (reanalysis, free, no key; check its terms for your use).
Flood labels come from YOU: put one flood-event date (YYYY-MM-DD) per line in an events file, taken from
ASDMA / district reports / news. Every day from an event date to event date + window is labelled 1.

  python -m anil_docs.tools.fetch_historical_rain --lat 27.0 --lon 94.6 --start 2020-06-01 --end 2025-09-30 \
        --events events.txt --out parul_risk_crop/data/history_real.csv
  python -m parul_risk_crop.validate_thresholds parul_risk_crop/data/history_real.csv --sweep

Reanalysis rainfall smooths out local extremes, so treat the resulting recall as optimistic and the
threshold as a starting point, not truth. Report this limitation in the paper.
"""
import argparse
import csv
import datetime as dt

import requests

URL = "https://archive-api.open-meteo.com/v1/archive"
COLUMNS = ["date", "rain_1h_mm", "rain_24h_mm", "rain_72h_mm", "water_level_cm", "danger_level_cm",
           "rise_cm_per_hr", "soil_moisture_pct", "forecast_rain_24h_mm", "flood_occurred"]


def fetch_daily(lat, lon, start, end, session=requests):
    r = session.get(URL, params={"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
                                 "daily": "precipitation_sum", "timezone": "UTC"}, timeout=30)
    r.raise_for_status()
    d = r.json().get("daily") or {}
    return list(zip(d.get("time", []), d.get("precipitation_sum", [])))


def load_events(lines):
    out = []
    for ln in lines:
        ln = ln.split("#")[0].strip()
        if ln:
            out.append(dt.date.fromisoformat(ln))
    return out


def build_rows(daily, events, window_days=3):
    rows = []
    vals = [0.0 if v is None else float(v) for _, v in daily]
    for i, (day, _) in enumerate(daily):
        d = dt.date.fromisoformat(day)
        r24 = vals[i]
        r72 = sum(vals[max(0, i - 2): i + 1])
        flood = int(any(e <= d <= e + dt.timedelta(days=window_days) for e in events))
        rows.append([day, "", round(r24, 1), round(r72, 1), "", "", "", "", "", flood])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--events", required=True, help="text file, one flood date per line")
    ap.add_argument("--window-days", type=int, default=3)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with open(a.events, encoding="utf-8") as fh:
        events = load_events(fh)
    rows = build_rows(fetch_daily(a.lat, a.lon, a.start, a.end), events, a.window_days)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print(f"wrote {len(rows)} days ({sum(r[-1] for r in rows)} flood-labelled) to {a.out}")


if __name__ == "__main__":
    main()
