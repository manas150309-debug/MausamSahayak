"""Rule-based crop advisor (version 1) - Parul.

score = weighted sum of trapezoid fits for temperature, rainfall and soil moisture.
Rainfall matters less when the farmer has irrigation.
"""
from __future__ import annotations

import csv
import datetime as dt
import os
from typing import Dict, List, Optional

from .crops_data import CROPS

NORMALS_PATH = os.path.join(os.path.dirname(__file__), "data", "district_normals.csv")


def season_for(date: dt.date) -> str:
    """Sowing-season calendar: kharif Jun-Sep, rabi Oct-Jan, zaid Feb-May."""
    m = date.month
    if 6 <= m <= 9:
        return "kharif"
    if m >= 10 or m == 1:
        return "rabi"
    return "zaid"


def trapezoid(x: float, r) -> float:
    lo, opt_lo, opt_hi, hi = r
    if x <= lo or x >= hi:
        return 0.0
    if opt_lo <= x <= opt_hi:
        return 1.0
    if x < opt_lo:
        return (x - lo) / (opt_lo - lo)
    return (hi - x) / (hi - opt_hi)


def _soil_range(soil):
    """soil = (min, best, max) -> trapezoid with a +/-5 point plateau around 'best'."""
    lo, best, hi = soil
    return (lo, best - 5, best + 5, hi)


def load_normals(path: str = NORMALS_PATH) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        rows = (ln for ln in fh if not ln.startswith("#"))
        for row in csv.DictReader(rows):
            out[row["district"].strip().lower()] = {
                "kharif": float(row["kharif_rain_mm"]),
                "rabi": float(row["rabi_rain_mm"]),
                "zaid": float(row["zaid_rain_mm"]),
            }
    return out


def seasonal_rain_normal(district: Optional[str], season: str, normals=None) -> float:
    normals = normals or load_normals()
    row = normals.get((district or "").strip().lower()) or normals["default"]
    return row[season]


def recommend(season: str, temp_c: float, seasonal_rain_mm: float,
              soil_moisture_pct: Optional[float] = None, irrigated: bool = False,
              top_n: int = 5, min_score: float = 0.4) -> List[dict]:
    w_temp, w_rain, w_soil = (0.55, 0.25, 0.20) if irrigated else (0.40, 0.45, 0.15)
    if soil_moisture_pct is None:
        total = w_temp + w_rain
        w_temp, w_rain, w_soil = w_temp / total, w_rain / total, 0.0
    out = []
    for c in CROPS:
        if season not in c["seasons"]:
            continue
        s_t = trapezoid(temp_c, c["temp"])
        s_r = trapezoid(seasonal_rain_mm, c["rain"])
        s_s = trapezoid(soil_moisture_pct, _soil_range(c["soil"])) if soil_moisture_pct is not None else 0.0
        score = w_temp * s_t + w_rain * s_r + w_soil * s_s
        if score < min_score or s_t == 0.0:   # a crop that cannot tolerate the temperature is never suggested
            continue
        reasons = []
        reasons.append({"code": "temp_ok" if s_t >= 0.99 else "temp_marginal", "params": {"temp": round(temp_c, 1)}})
        if irrigated:
            reasons.append({"code": "needs_irrigation" if s_r < 0.6 else "rain_ok", "params": {"rain": round(seasonal_rain_mm)}})
        else:
            reasons.append({"code": "rain_ok" if s_r >= 0.99 else ("rain_low" if seasonal_rain_mm < c["rain"][1] else "rain_high"),
                            "params": {"rain": round(seasonal_rain_mm)}})
        out.append({"crop_id": c["id"], "name_en": c["en"], "name_hi": c["hi"],
                    "score": round(score, 3), "reasons": reasons})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out[:top_n]
