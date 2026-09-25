"""Flood and heat risk rules (Parul).

Pure functions, no I/O. All thresholds live in dataclasses so they can be tuned
against historical data (see validate_thresholds.py) without touching the logic.
Every triggered rule is returned as a structured Reason(code, params) so the bot
can translate it into Hindi/English.

These thresholds are STARTING VALUES. Calibrate them on IMD/CWC data for your
site and report the false-alarm and miss rates in the project report.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .levels import Level


@dataclass
class Reason:
    code: str
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"code": self.code, "params": self.params}


@dataclass
class RiskResult:
    kind: str
    level: Level
    stale: bool
    reasons: List[Reason]
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "kind": self.kind,
            "level": int(self.level),
            "level_name": self.level.name,
            "stale": self.stale,
            "reasons": [r.to_dict() for r in self.reasons],
            "metrics": self.metrics,
        }


# ----------------------------------------------------------------- flood
@dataclass(frozen=True)
class FloodThresholds:
    stale_minutes: float = 30.0
    # rainfall (mm) - IMD: heavy 64.5-115.5, very heavy 115.6-204.4 in 24 h
    yellow_rain_24h_mm: float = 30.0
    orange_rain_24h_mm: float = 65.0
    red_rain_24h_mm: float = 115.6
    yellow_rain_72h_mm: float = 75.0
    orange_rain_72h_mm: float = 150.0
    orange_rain_1h_mm: float = 30.0
    # river / drain level
    rising_cm_per_hr: float = 3.0
    rapid_rise_cm_per_hr: float = 10.0
    elevated_level_ratio: float = 0.5   # level / danger mark
    near_danger_ratio: float = 0.7
    # soil and forecast
    saturated_soil_pct: float = 85.0
    heavy_forecast_24h_mm: float = 65.0
    moderate_forecast_24h_mm: float = 30.0
    # sudden surge (landslide-dam breach, dam release): warning -> danger within hours
    flash_rise_cm_per_hr: float = 30.0
    # upstream node (gives lead time downstream)
    upstream_near_danger_ratio: float = 0.85


@dataclass
class FloodFeatures:
    rain_1h_mm: Optional[float] = None
    rain_24h_mm: Optional[float] = None
    rain_72h_mm: Optional[float] = None
    water_level_cm: Optional[float] = None
    danger_level_cm: Optional[float] = None   # None = node has no water sensor
    rise_cm_per_hr: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    forecast_rain_24h_mm: Optional[float] = None
    minutes_since_last: Optional[float] = None  # None = never reported
    # optional: state of the node UPSTREAM on the same river (early warning with lead time)
    upstream_rise_cm_per_hr: Optional[float] = None
    upstream_level_ratio: Optional[float] = None   # upstream level / upstream danger mark
    upstream_minutes_since_last: Optional[float] = None


def assess_flood(f: FloodFeatures, th: FloodThresholds = FloodThresholds()) -> RiskResult:
    level = Level.GREEN
    reasons: List[Reason] = []

    def hit(lv: Level, code: str, **params):
        nonlocal level
        if lv > level:
            level = lv
        if any(r.code == code for r in reasons):
            return                       # rules run RED -> YELLOW, so the first hit of a code is its highest
        reasons.append(Reason(code, params))

    stale = f.minutes_since_last is None or f.minutes_since_last > th.stale_minutes
    if stale:
        mins = None if f.minutes_since_last is None else round(f.minutes_since_last)
        hit(Level.UNKNOWN, "sensor_offline", minutes=mins)
    else:
        if f.rain_24h_mm is None:
            hit(Level.UNKNOWN, "rain_data_missing")
        if f.danger_level_cm is not None and f.water_level_cm is None:
            hit(Level.UNKNOWN, "water_level_missing")

    ratio = None
    if f.water_level_cm is not None and f.danger_level_cm:
        ratio = f.water_level_cm / f.danger_level_cm

    rising = f.rise_cm_per_hr is not None and f.rise_cm_per_hr >= th.rising_cm_per_hr
    rapid = f.rise_cm_per_hr is not None and f.rise_cm_per_hr >= th.rapid_rise_cm_per_hr
    saturated = f.soil_moisture_pct is not None and f.soil_moisture_pct >= th.saturated_soil_pct
    fc = f.forecast_rain_24h_mm
    heavy_fc = fc is not None and fc >= th.heavy_forecast_24h_mm
    r24, r72, r1 = f.rain_24h_mm, f.rain_72h_mm, f.rain_1h_mm

    # ---- RED
    if ratio is not None and ratio >= 1.0:
        hit(Level.RED, "level_above_danger", level_cm=round(f.water_level_cm, 1),
            danger_cm=f.danger_level_cm)
    if rapid and saturated and heavy_fc:
        hit(Level.RED, "rapid_rise_saturated_heavy_forecast",
            rise=round(f.rise_cm_per_hr, 1), soil=round(f.soil_moisture_pct), forecast_mm=round(fc))
    if rapid and ratio is not None and ratio >= 0.85:
        hit(Level.RED, "rapid_rise_near_danger", rise=round(f.rise_cm_per_hr, 1),
            percent=round(ratio * 100))
    if r24 is not None and r24 >= th.red_rain_24h_mm and saturated:
        hit(Level.RED, "very_heavy_rain_saturated", mm=round(r24, 1), soil=round(f.soil_moisture_pct))

    if f.rise_cm_per_hr is not None and f.rise_cm_per_hr >= th.flash_rise_cm_per_hr:
        hit(Level.RED, "flash_rise", rise=round(f.rise_cm_per_hr, 1))
    up_ok = f.upstream_minutes_since_last is not None and f.upstream_minutes_since_last <= th.stale_minutes
    up_rapid = up_ok and f.upstream_rise_cm_per_hr is not None and f.upstream_rise_cm_per_hr >= th.rapid_rise_cm_per_hr
    up_rising = up_ok and f.upstream_rise_cm_per_hr is not None and f.upstream_rise_cm_per_hr >= th.rising_cm_per_hr
    up_ratio = f.upstream_level_ratio if up_ok else None
    if up_rapid and up_ratio is not None and up_ratio >= th.upstream_near_danger_ratio:
        hit(Level.RED, "upstream_surge_near_danger", rise=round(f.upstream_rise_cm_per_hr, 1),
            percent=round(up_ratio * 100))

    # ---- ORANGE
    if up_rapid:
        hit(Level.ORANGE, "upstream_surge", rise=round(f.upstream_rise_cm_per_hr, 1))
    if r24 is not None and r24 > th.orange_rain_24h_mm:
        hit(Level.ORANGE, "rain_24h", mm=round(r24, 1))
    if r72 is not None and r72 >= th.orange_rain_72h_mm:
        hit(Level.ORANGE, "rain_72h", mm=round(r72, 1))
    if r1 is not None and r1 >= th.orange_rain_1h_mm:
        hit(Level.ORANGE, "rain_1h_intense", mm=round(r1, 1))
    if ratio is not None and ratio >= th.near_danger_ratio and rising:
        hit(Level.ORANGE, "level_near_danger_rising", percent=round(ratio * 100),
            rise=round(f.rise_cm_per_hr, 1))
    if rapid:
        hit(Level.ORANGE, "level_rising_rapid", rise=round(f.rise_cm_per_hr, 1))

    # ---- YELLOW
    if up_rising:
        hit(Level.YELLOW, "upstream_rising", rise=round(f.upstream_rise_cm_per_hr, 1))
    if r24 is not None and r24 > th.yellow_rain_24h_mm:
        hit(Level.YELLOW, "rain_24h", mm=round(r24, 1))
    if r72 is not None and r72 >= th.yellow_rain_72h_mm:
        hit(Level.YELLOW, "rain_72h", mm=round(r72, 1))
    if rising:
        hit(Level.YELLOW, "level_rising", rise=round(f.rise_cm_per_hr, 1))
    if ratio is not None and ratio >= th.elevated_level_ratio:
        hit(Level.YELLOW, "level_elevated", percent=round(ratio * 100))
    if heavy_fc:
        hit(Level.YELLOW, "forecast_heavy_rain", mm=round(fc))
    elif saturated and fc is not None and fc >= th.moderate_forecast_24h_mm:
        hit(Level.YELLOW, "saturated_soil_forecast_rain", soil=round(f.soil_moisture_pct),
            mm=round(fc))

    metrics = {
        "rain_1h_mm": r1, "rain_24h_mm": r24, "rain_72h_mm": r72,
        "water_level_cm": f.water_level_cm, "level_ratio": None if ratio is None else round(ratio, 3),
        "rise_cm_per_hr": f.rise_cm_per_hr, "soil_moisture_pct": f.soil_moisture_pct,
        "forecast_rain_24h_mm": fc, "minutes_since_last": f.minutes_since_last,
    }
    return RiskResult("flood", level, stale, reasons, metrics)


# ------------------------------------------------------------------ heat
@dataclass(frozen=True)
class HeatThresholds:
    stale_minutes: float = 30.0
    yellow_hi_c: float = 38.0
    orange_hi_c: float = 44.0
    red_hi_c: float = 52.0
    orange_temp_c: float = 40.0   # IMD heat-wave territory for plains
    red_temp_c: float = 45.0      # IMD severe heat wave territory


def heat_index_c(temp_c: float, rh_pct: float) -> float:
    """NWS Rothfusz heat index, input/output in Celsius."""
    t = temp_c * 9.0 / 5.0 + 32.0
    rh = rh_pct
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    if (simple + t) / 2.0 < 80.0:
        hi = simple
    else:
        hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh
              - 0.00683783 * t * t - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
              + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
        if rh < 13 and 80 <= t <= 112:
            hi -= ((13 - rh) / 4.0) * math.sqrt((17 - abs(t - 95.0)) / 17.0)
        elif rh > 85 and 80 <= t <= 87:
            hi += ((rh - 85) / 10.0) * ((87 - t) / 5.0)
    return (hi - 32.0) * 5.0 / 9.0


def assess_heat(temp_c: Optional[float], humidity_pct: Optional[float],
                minutes_since_last: Optional[float],
                th: HeatThresholds = HeatThresholds()) -> RiskResult:
    level = Level.GREEN
    reasons: List[Reason] = []

    def hit(lv, code, **p):
        nonlocal level
        reasons.append(Reason(code, p))
        if lv > level:
            level = lv

    stale = minutes_since_last is None or minutes_since_last > th.stale_minutes
    if stale:
        hit(Level.UNKNOWN, "sensor_offline",
            minutes=None if minutes_since_last is None else round(minutes_since_last))
    hi = None
    if temp_c is None or humidity_pct is None:
        if not stale:
            hit(Level.UNKNOWN, "temperature_missing")
    else:
        hi = heat_index_c(temp_c, humidity_pct)
        if hi >= th.red_hi_c or temp_c >= th.red_temp_c:
            hit(Level.RED, "extreme_heat", temp=round(temp_c, 1), hi=round(hi, 1))
        elif hi >= th.orange_hi_c or temp_c >= th.orange_temp_c:
            hit(Level.ORANGE, "severe_heat", temp=round(temp_c, 1), hi=round(hi, 1))
        elif hi >= th.yellow_hi_c:
            hit(Level.YELLOW, "high_heat", temp=round(temp_c, 1), hi=round(hi, 1))
    metrics = {"temperature_c": temp_c, "humidity_pct": humidity_pct,
               "heat_index_c": None if hi is None else round(hi, 1),
               "minutes_since_last": minutes_since_last}
    return RiskResult("heat", level, stale, reasons, metrics)
