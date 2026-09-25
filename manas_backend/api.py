"""REST API + dashboard (Manas). Flask app factory so tests can inject a DB and forecast."""
from __future__ import annotations

import hmac
import os
import time
from typing import Optional

from flask import Flask, g, jsonify, request, send_from_directory

from . import db, ingest, service
from .config import Settings

STATIC = os.path.join(os.path.dirname(__file__), "static")


def create_app(settings: Optional[Settings] = None, forecast_fn=None, clock=time.time) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    # a throw-away connection makes sure the schema exists
    boot = db.connect(settings.db_path)
    db.init_db(boot)
    boot.close()

    def conn():
        if "conn" not in g:
            g.conn = db.connect(settings.db_path)
        return g.conn

    @app.teardown_appcontext
    def _close(_exc):
        c = g.pop("conn", None)
        if c is not None:
            c.close()

    def err(msg, code):
        return jsonify({"error": msg}), code

    def authorised():
        return bool(settings.api_key) and hmac.compare_digest(request.headers.get("X-API-Key", ""), settings.api_key)

    def now():
        return int(clock())

    def num_arg(name):
        try:
            return float(request.args[name])
        except (KeyError, ValueError):
            return None

    # ---- public read endpoints
    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "time": now()})

    @app.get("/")
    @app.get("/dashboard")
    def dashboard():
        return send_from_directory(STATIC, "dashboard.html")

    @app.get("/api/nodes")
    def nodes():
        return jsonify({"nodes": service.list_nodes(conn())})

    @app.get("/api/nodes/<node_id>/latest")
    def latest(node_id):
        node = service.get_node(conn(), node_id)
        if node is None:
            return err("unknown_node", 404)
        r = service.latest_reading(conn(), node_id)
        mins = service.minutes_since_last(r, now())
        return jsonify({"node": node, "reading": r, "age_minutes": None if mins is None else round(mins, 1),
                        "stale": mins is None or mins > settings.stale_minutes})

    @app.get("/api/nodes/<node_id>/history")
    def hist(node_id):
        if service.get_node(conn(), node_id) is None:
            return err("unknown_node", 404)
        hours = min(max(num_arg("hours") or 24, 1), 168)
        return jsonify({"node_id": node_id, "hours": hours, "readings": service.history(conn(), node_id, hours, now())})

    @app.get("/api/nodes/<node_id>/risk")
    def risk(node_id):
        a = service.assess_node(conn(), node_id, now(), forecast_fn, settings)
        return err("unknown_node", 404) if a is None else jsonify(a)

    @app.get("/api/nearest")
    def nearest():
        lat, lon = num_arg("lat"), num_arg("lon")
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return err("lat_lon_required", 400)
        n = service.nearest_node(conn(), lat, lon, settings.max_node_distance_km)
        return err("no_nodes", 404) if n is None else jsonify(n)

    @app.get("/api/crop-advice")
    def crops():
        lat, lon = num_arg("lat"), num_arg("lon")
        if lat is None or lon is None:
            return err("lat_lon_required", 400)
        irrigated = request.args.get("irrigated", "0").lower() in ("1", "true", "yes")
        res = service.crop_advice(conn(), lat, lon, now(), irrigated, settings)
        return (jsonify(res), 404) if "error" in res else jsonify(res)

    @app.get("/api/alerts")
    def alerts():
        since = int(num_arg("since_id") or 0)
        limit = int(min(num_arg("limit") or 100, 500))
        return jsonify({"alerts": service.alerts_since(conn(), since, limit)})

    # ---- protected write endpoints
    @app.post("/api/readings")
    def post_reading():
        if not authorised():
            return err("unauthorised", 401)
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or not body.get("node_id"):
            return err("node_id_required", 400)
        res = ingest.store_reading(conn(), str(body["node_id"]), body, now())
        if not res.ok:
            return err(res.reason, 404 if res.reason == "unknown_node" else 422)
        return jsonify({"status": res.reason, "dropped_fields": res.dropped_fields}), (201 if res.stored else 200)

    @app.post("/api/nodes")
    def post_node():
        if not authorised():
            return err("unauthorised", 401)
        b = request.get_json(silent=True) or {}
        try:
            service.add_node(conn(), str(b["node_id"]), b.get("name", b["node_id"]), float(b["lat"]), float(b["lon"]),
                             b.get("district"), b.get("state"), b.get("danger_level_cm"), now())
        except (KeyError, TypeError, ValueError):
            return err("node_id_lat_lon_required", 400)
        return jsonify({"status": "saved"}), 201

    @app.post("/api/simulate")
    def simulate():
        b = request.get_json(silent=True) or {}
        node_id = str(b.get("node_id", "node01"))
        scenario = b.get("scenario", "heavy_rain")
        if scenario not in ("normal", "heavy_rain", "flood", "silent"):
            return err("invalid_scenario", 400)
        import zlib
        from nishant_firmware.simulator import scenarios
        conn().execute("DELETE FROM readings WHERE node_id=?", (node_id,))
        conn().commit()
        for r in scenarios.backfill(scenario, node_id, now(), seed=zlib.crc32(node_id.encode())):
            ingest.store_reading(conn(), node_id, r, now())
        service.run_alert_check(conn(), now())
        return jsonify({"status": "scenario_applied", "node_id": node_id, "scenario": scenario})

    @app.post("/api/seed")
    def seed():
        from .cli import seed_demo
        b = request.get_json(silent=True) or {}
        scen = b.get("scenario")
        count = seed_demo(conn(), now(), scenario_override=scen)
        service.run_alert_check(conn(), now())
        return jsonify({"status": "seeded", "count": count})

    return app

