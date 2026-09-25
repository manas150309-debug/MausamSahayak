"""Synthetic sensor data for demos and tests (Nishant).

make_reading(scenario, p, ts, rng) returns what a real node would publish for one
5-minute interval. `p` is progress (0..1) through a 24 h window of 288 intervals.

Scenarios
  normal      dry day, stable river
  heavy_rain  ~90 mm over the day, river rises to about half of a 450 cm danger mark
  flood       ~200 mm over the day, river crosses the 450 cm danger mark near the end
  silent      same as normal but the last SILENT_MINUTES of data are never sent
"""
import math
import random

INTERVALS = 288
INTERVAL_S = 300
MM_PER_TIP = 0.2794     # keep in sync with firmware config.h
SILENT_MINUTES = 45
SCENARIOS = ("normal", "heavy_rain", "flood", "silent")


def _cum_rain(amp, p):
    """Cumulative rain (mm) up to progress p for a gaussian storm centred at p=0.6."""
    return INTERVALS * amp * 0.1 * math.sqrt(math.pi) * (math.erf((p - 0.6) / 0.2) - math.erf(-3.0))


def make_reading(scenario, p, ts, rng=None, node_id="node01"):
    rng = rng or random.Random()
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; choose from {SCENARIOS}")
    amp = {"heavy_rain": 0.9, "flood": 2.0}.get(scenario, 0.0)
    ist_hour = ((int(ts) + 19800) // 3600) % 24
    temp = 30 + 6 * math.sin(2 * math.pi * (ist_hour - 9) / 24)
    storm = math.exp(-((p - 0.6) / 0.2) ** 2) if amp else 0.0
    rain = amp * storm * rng.uniform(0.8, 1.2)
    rain = round(rain / MM_PER_TIP) * MM_PER_TIP           # tipping bucket resolution
    cum = _cum_rain(amp, p) if amp else 0.0
    temp -= 4 * storm
    humidity = min(99.0, 62 - 1.5 * (temp - 30) + 30 * storm)
    soil = min(96.0, 40 + 0.5 * cum)
    k = {"heavy_rain": 1.2, "flood": 1.9}.get(scenario, 0.0)
    level = 120 + k * cum + rng.uniform(-0.5, 0.5)
    return {
        "node_id": node_id, "ts": int(ts),
        "temperature_c": round(temp + rng.uniform(-0.3, 0.3), 1),
        "humidity_pct": round(humidity + rng.uniform(-1, 1), 1),
        "pressure_hpa": round(1004 - 6 * storm + rng.uniform(-0.3, 0.3), 1),
        "rain_mm": round(rain, 2),
        "water_level_cm": round(level, 1),
        "soil_moisture_pct": round(soil + rng.uniform(-0.5, 0.5), 1),
        "battery_v": round(3.9 + rng.uniform(-0.05, 0.05), 2),
        "rssi": rng.randint(-85, -60),
    }


def backfill(scenario, node_id, now, seed=None):
    """Yield the 288 readings ending at `now` (minus the silent gap for 'silent')."""
    rng = random.Random(seed)
    start = int(now) - (INTERVALS - 1) * INTERVAL_S
    count = INTERVALS - (SILENT_MINUTES * 60 // INTERVAL_S if scenario == "silent" else 0)
    for i in range(count):
        yield make_reading(scenario, i / (INTERVALS - 1), start + i * INTERVAL_S, rng, node_id)
