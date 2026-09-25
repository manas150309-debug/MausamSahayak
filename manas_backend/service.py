"""Core backend logic: features, risk assessment, alerts, station lookup, crop advice (Manas).

Everything takes an explicit `now` (epoch seconds) so it can be tested deterministically.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sqlite3
import time
from typing import Callable, Dict, List, Optional

from parul_risk_crop import crop_advisor
from parul_risk_crop.levels import Level
from parul_risk_crop.risk_engine import FloodFeatures, FloodThresholds, HeatThresholds, assess_flood, assess_heat

from .config import Settings

ForecastFn = Callable[[float, float], Optional[dict]]


def _row(r):
    return None if r is None else dict(r)


# ------------------------------------------------------------------ nodes
def add_node(conn, node_id, name, lat, lon, district=None, state=None, danger_level_cm=None, now=None,
             upstream_node_id=None):
    now = int(now if now is not None else time.time())
    conn.execute(
        "INSERT INTO nodes(node_id,name,lat,lon,district,state,danger_level_cm,created_at,upstream_node_id)"
        " VALUES (?,?,?,?,?,?,?,?,?)"
        " ON CONFLICT(node_id) DO UPDATE SET name=excluded.name, lat=excluded.lat, lon=excluded.lon,"
        " district=excluded.district, state=excluded.state, danger_level_cm=excluded.danger_level_cm,"
        " upstream_node_id=excluded.upstream_node_id",
        (node_id, name, float(lat), float(lon), district, state,
         None if danger_level_cm is None else float(danger_level_cm), now, upstream_node_id or None))
    conn.commit()


def get_node(conn, node_id):
    return _row(conn.execute("SELECT * FROM nodes WHERE node_id=?", (node_id,)).fetchone())


def list_nodes(conn) -> List[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM nodes ORDER BY node_id")]


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def nearest_node(conn, lat, lon, max_km: Optional[float] = None):
    best = None
    for n in list_nodes(conn):
        d = haversine_km(lat, lon, n["lat"], n["lon"])
        if best is None or d < best[1]:
            best = (n, d)
    if best is None:
        return None
    return {"node": best[0], "distance_km": round(best[1], 2),
            "within_range": True if max_km is None else best[1] <= max_km}


# --------------------------------------------------------------- readings
def latest_reading(conn, node_id):
    return _row(conn.execute("SELECT * FROM readings WHERE node_id=? ORDER BY ts DESC LIMIT 1", (node_id,)).fetchone())


def history(conn, node_id, hours, now):
    rows = conn.execute("SELECT * FROM readings WHERE node_id=? AND ts>? AND ts<=? ORDER BY ts",
                        (node_id, int(now - hours * 3600), int(now) + 600)).fetchall()
    return [dict(r) for r in rows]


def rain_sum(conn, node_id, hours, now) -> Optional[float]:
    r = conn.execute("SELECT SUM(rain_mm) s, COUNT(rain_mm) c FROM readings WHERE node_id=? AND ts>? AND ts<=?",
                     (node_id, int(now - hours * 3600), int(now) + 600)).fetchone()
    return None if not r["c"] else round(r["s"], 2)


def rise_rate(conn, node_id, now, window_min=90.0) -> Optional[float]:
    """Least-squares slope of water level (cm per hour) over the recent window."""
    rows = conn.execute(
        "SELECT ts, water_level_cm w FROM readings WHERE node_id=? AND ts>? AND ts<=? AND water_level_cm IS NOT NULL ORDER BY ts",
        (node_id, int(now - window_min * 60), int(now) + 600)).fetchall()
    if len(rows) < 3 or rows[-1]["ts"] - rows[0]["ts"] < 20 * 60:
        return None
    xs = [(r["ts"] - rows[0]["ts"]) / 3600.0 for r in rows]
    ys = [r["w"] for r in rows]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return None if den == 0 else round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den, 2)


# -------------------------------------------------------------- assessment
def minutes_since_last(reading, now) -> Optional[float]:
    return None if reading is None else max(0.0, (now - reading["ts"]) / 60.0)


def _upstream_state(conn, node, now, settings):
    up = get_node(conn, node["upstream_node_id"]) if node.get("upstream_node_id") else None
    if up is None:
        return {}
    last = latest_reading(conn, up["node_id"])
    ratio = None
    if last and last["water_level_cm"] is not None and up["danger_level_cm"]:
        ratio = last["water_level_cm"] / up["danger_level_cm"]
    return {"upstream_rise_cm_per_hr": rise_rate(conn, up["node_id"], now, settings.rise_window_min),
            "upstream_level_ratio": ratio,
            "upstream_minutes_since_last": minutes_since_last(last, now)}


def build_flood_features(conn, node, now, forecast, settings: Settings) -> FloodFeatures:
    last = latest_reading(conn, node["node_id"])
    return FloodFeatures(
        **_upstream_state(conn, node, now, settings),
        rain_1h_mm=rain_sum(conn, node["node_id"], 1, now),
        rain_24h_mm=rain_sum(conn, node["node_id"], 24, now),
        rain_72h_mm=rain_sum(conn, node["node_id"], 72, now),
        water_level_cm=None if last is None else last["water_level_cm"],
        danger_level_cm=node["danger_level_cm"],
        rise_cm_per_hr=rise_rate(conn, node["node_id"], now, settings.rise_window_min),
        soil_moisture_pct=None if last is None else last["soil_moisture_pct"],
        forecast_rain_24h_mm=None if not forecast else forecast.get("next_24h_mm"),
        minutes_since_last=minutes_since_last(last, now))


def assess_node(conn, node_id, now, forecast_fn: Optional[ForecastFn] = None, settings: Optional[Settings] = None):
    settings = settings or Settings()
    node = get_node(conn, node_id)
    if node is None:
        return None
    forecast = None
    if forecast_fn is not None:
        try:
            forecast = forecast_fn(node["lat"], node["lon"])
        except Exception:
            forecast = None          # a broken forecast must never break monitoring
    last = latest_reading(conn, node_id)
    mins = minutes_since_last(last, now)
    ft = FloodThresholds(stale_minutes=settings.stale_minutes)
    ht = HeatThresholds(stale_minutes=settings.stale_minutes)
    flood = assess_flood(build_flood_features(conn, node, now, forecast, settings), ft)
    heat = assess_heat(None if last is None else last["temperature_c"],
                       None if last is None else last["humidity_pct"], mins, ht)
    return {"node_id": node_id, "generated_at": int(now), "reading": last,
            "minutes_since_last": None if mins is None else round(mins, 1),
            "forecast": forecast, "flood": flood.to_dict(), "heat": heat.to_dict()}


# ------------------------------------------------------------------ alerts
def _last_alert(conn, node_id, kind):
    return conn.execute("SELECT * FROM alerts WHERE node_id=? AND kind=? ORDER BY id DESC LIMIT 1",
                        (node_id, kind)).fetchone()


def run_alert_check(conn, now, forecast_fn: Optional[ForecastFn] = None, settings: Optional[Settings] = None) -> List[dict]:
    """Record an alert whenever a node's risk level changes.

    Escalation is recorded immediately. De-escalation is recorded only after
    `deescalate_minutes` so a level hovering around a threshold does not flap.
    Nodes that have never reported are skipped (not yet commissioned).
    """
    settings = settings or Settings()
    created = []
    for node in list_nodes(conn):
        if latest_reading(conn, node["node_id"]) is None:
            continue
        a = assess_node(conn, node["node_id"], now, forecast_fn, settings)
        for kind in ("flood", "heat"):
            res = a[kind]
            if kind == "heat" and res["stale"]:
                continue                      # stale is announced once, via the flood alert
            new = Level(res["level"])
            last = _last_alert(conn, node["node_id"], kind)
            old = Level(last["level"]) if last else Level.GREEN
            if new == old:
                continue
            if new < old and last is not None and now - last["ts"] < settings.deescalate_minutes * 60:
                continue
            cur = conn.execute(
                "INSERT INTO alerts(node_id, ts, kind, level, previous_level, stale, reasons) VALUES (?,?,?,?,?,?,?)",
                (node["node_id"], int(now), kind, int(new), int(old), int(res["stale"]), json.dumps(res["reasons"])))
            created.append(alert_dict(conn.execute("SELECT * FROM alerts WHERE id=?", (cur.lastrowid,)).fetchone()))
    conn.commit()
    return created


def alert_dict(r) -> dict:
    d = dict(r)
    d["reasons"] = json.loads(d["reasons"])
    d["level_name"] = Level(d["level"]).name
    d["previous_level_name"] = None if d["previous_level"] is None else Level(d["previous_level"]).name
    d["stale"] = bool(d["stale"])
    return d


def alerts_since(conn, since_id=0, limit=100) -> List[dict]:
    rows = conn.execute("SELECT * FROM alerts WHERE id>? ORDER BY id LIMIT ?", (int(since_id), int(limit))).fetchall()
    return [alert_dict(r) for r in rows]


# ------------------------------------------------------------------- crops
def crop_advice(conn, lat, lon, now, irrigated=False, settings: Optional[Settings] = None):
    settings = settings or Settings()
    near = nearest_node(conn, lat, lon, settings.max_node_distance_km)
    if near is None or not near["within_range"]:
        return {"error": "no_station_in_range", "nearest": near}
    node = near["node"]
    last = latest_reading(conn, node["node_id"])
    if last is None:
        return {"error": "no_data", "nearest": near}
    week = conn.execute("SELECT AVG(temperature_c) t FROM readings WHERE node_id=? AND ts>? AND temperature_c IS NOT NULL",
                        (node["node_id"], int(now - 7 * 86400))).fetchone()["t"]
    temp = week if week is not None else last["temperature_c"]
    if temp is None:
        return {"error": "no_temperature", "nearest": near}
    season = crop_advisor.season_for(dt.datetime.fromtimestamp(now, dt.timezone(dt.timedelta(hours=5, minutes=30))).date())
    rain = crop_advisor.seasonal_rain_normal(node.get("district"), season)
    recs = crop_advisor.recommend(season, temp, rain, last["soil_moisture_pct"], irrigated=irrigated)
    ml_recs = []
    try:
        import os
        model_path = os.path.join(os.path.dirname(__file__), "..", "parul_risk_crop", "data", "crop_model.joblib")
        if os.path.exists(model_path):
            import joblib
            from parul_risk_crop.train_crop_model import predict_top
            model = joblib.load(model_path)
            hum = float(last["humidity_pct"]) if last.get("humidity_pct") is not None else 65.0
            ml_recs = predict_top(model, temp, hum, rain, top_n=3)
    except Exception:
        ml_recs = []
    return {"node_id": node["node_id"], "distance_km": near["distance_km"], "season": season,
            "irrigated": irrigated,
            "inputs": {"mean_temp_c_7d": round(temp, 1), "seasonal_rain_normal_mm": rain,
                       "soil_moisture_pct": last["soil_moisture_pct"], "district": node.get("district")},
            "recommendations": recs,
            "ml_recommendations": ml_recs}

