"""Validate and store telemetry (Manas).

A value outside its physical range is stored as NULL (sensor fault) instead of being
trusted - the risk engine then reports the station as UNKNOWN rather than guessing.
"""
from __future__ import annotations

import json
import math
import re
import sqlite3
import time
from dataclasses import dataclass, field
from typing import List, Optional

RANGES = {
    "temperature_c": (-40.0, 70.0), "humidity_pct": (0.0, 100.0), "pressure_hpa": (800.0, 1100.0),
    "rain_mm": (0.0, 200.0), "water_level_cm": (0.0, 3000.0), "soil_moisture_pct": (0.0, 100.0),
    "battery_v": (2.5, 5.5),
}
MEASUREMENTS = ("temperature_c", "humidity_pct", "pressure_hpa", "rain_mm", "water_level_cm", "soil_moisture_pct")
TOPIC_RE = re.compile(r"^mausam/nodes/([A-Za-z0-9_-]{1,32})/telemetry$")
MAX_PAST_S = 7 * 24 * 3600
MAX_FUTURE_S = 600


@dataclass
class IngestResult:
    ok: bool
    reason: str = ""
    stored: bool = False
    dropped_fields: List[str] = field(default_factory=list)
    ts: Optional[int] = None


def _num(v):
    if isinstance(v, bool) or v is None:
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def store_reading(conn: sqlite3.Connection, node_id: str, data: dict, now: Optional[int] = None) -> IngestResult:
    now = int(now if now is not None else time.time())
    if not conn.execute("SELECT 1 FROM nodes WHERE node_id=?", (node_id,)).fetchone():
        return IngestResult(False, "unknown_node")
    clean, dropped = {}, []
    for key, (lo, hi) in RANGES.items():
        if key not in data or data[key] is None:
            clean[key] = None
            continue
        x = _num(data[key])
        if x is None or not (lo <= x <= hi):
            clean[key] = None
            dropped.append(key)
        else:
            clean[key] = x
    if all(clean[k] is None for k in MEASUREMENTS):
        return IngestResult(False, "no_valid_measurements", dropped_fields=dropped)
    ts = _num(data.get("ts"))
    if ts is not None and ts > 1e11:          # milliseconds
        ts /= 1000.0
    if ts is None or ts < now - MAX_PAST_S or ts > now + MAX_FUTURE_S:
        ts = now                               # node clock missing or wrong
    ts = int(ts)
    rssi = _num(data.get("rssi"))
    cur = conn.execute(
        "INSERT OR IGNORE INTO readings(node_id, ts, received_at, temperature_c, humidity_pct, pressure_hpa,"
        " rain_mm, water_level_cm, soil_moisture_pct, battery_v, rssi) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (node_id, ts, now, clean["temperature_c"], clean["humidity_pct"], clean["pressure_hpa"],
         clean["rain_mm"], clean["water_level_cm"], clean["soil_moisture_pct"], clean["battery_v"],
         None if rssi is None else int(rssi)))
    conn.commit()
    return IngestResult(True, "stored" if cur.rowcount else "duplicate", bool(cur.rowcount), dropped, ts)


def handle_message(conn, topic: str, payload, now: Optional[int] = None) -> IngestResult:
    m = TOPIC_RE.match(topic or "")
    if not m:
        return IngestResult(False, "bad_topic")
    try:
        data = json.loads(payload.decode("utf-8") if isinstance(payload, (bytes, bytearray)) else payload)
    except (ValueError, UnicodeDecodeError):
        return IngestResult(False, "bad_json")
    if not isinstance(data, dict):
        return IngestResult(False, "bad_json")
    if data.get("node_id") not in (None, m.group(1)):
        return IngestResult(False, "node_id_mismatch")
    return store_reading(conn, m.group(1), data, now)
