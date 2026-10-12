"""REST API + dashboard (Manas). Flask app factory so tests can inject a DB and forecast."""
from __future__ import annotations

import hmac
import os
import time
from pathlib import Path
from typing import Optional

from flask import Flask, g, jsonify, redirect, request, send_from_directory, session

from . import auth, db, ingest, notifications, service
from .config import Settings

STATIC = os.path.join(os.path.dirname(__file__), "static")


def create_app(settings: Optional[Settings] = None, forecast_fn=None, geocode_fn=None, clock=time.time) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.secret_key = settings.session_secret or settings.api_key or "mausam-dev-session-secret"
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 14,
    )

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
    def home():
        return redirect("/dashboard")

    @app.get("/login")
    def login_page():
        if session.get("user_id"):
            return redirect("/dashboard")
        return send_from_directory(STATIC, "login.html")

    @app.get("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect("/login")
        return send_from_directory(STATIC, "dashboard.html")

    # ---- user accounts and notification preferences
    @app.post("/api/auth/signup")
    def signup():
        try:
            user = auth.create_user(conn(), request.get_json(silent=True) or {}, now())
        except auth.ValidationError as exc:
            return err(str(exc), 400)
        session.clear()
        session["user_id"] = user["id"]
        session.permanent = True
        delivery = notifications.send_welcome(conn(), user, settings, now())
        return jsonify({"user": user, "welcome_delivery": delivery}), 201

    @app.post("/api/auth/login")
    def login():
        body = request.get_json(silent=True) or {}
        user = auth.authenticate(conn(), str(body.get("email", "")), str(body.get("password", "")), now())
        if user is None:
            return err("Invalid email or password", 401)
        session.clear()
        session["user_id"] = user["id"]
        session.permanent = True
        return jsonify({"user": user})

    @app.post("/api/auth/logout")
    def logout():
        session.clear()
        return jsonify({"status": "signed_out"})

    @app.get("/api/auth/me")
    def me():
        user = auth.get_user(conn(), session.get("user_id", 0)) if session.get("user_id") else None
        return (jsonify({"user": user}), 200) if user else err("authentication_required", 401)

    @app.put("/api/auth/preferences")
    def preferences():
        if not session.get("user_id"):
            return err("authentication_required", 401)
        try:
            user = auth.update_preferences(conn(), session["user_id"], request.get_json(silent=True) or {})
        except auth.ValidationError as exc:
            return err(str(exc), 400)
        return jsonify({"user": user})

    @app.get("/api/notifications")
    def notification_history():
        if not session.get("user_id"):
            return err("authentication_required", 401)
        return jsonify({"deliveries": notifications.delivery_history(conn(), session["user_id"])})

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

    @app.get("/api/locations/search")
    def location_search():
        query = " ".join(request.args.get("q", "").split())
        if len(query) < 2 or len(query) > 100:
            return err("location_query_must_be_2_to_100_characters", 400)
        try:
            if geocode_fn is not None:
                locations = geocode_fn(query)
            else:
                from .geocoding import search_locations
                locations = search_locations(query)
        except Exception:
            app.logger.exception("location search failed")
            return err("location_search_unavailable", 502)
        return jsonify({"query": query, "locations": locations})

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

    @app.get("/api/evidence")
    def evidence():
        from parul_risk_crop.historical_weather import load_summary
        data_dir = Path(__file__).parents[1] / "parul_risk_crop" / "data"
        datasets = (
            ("Faridabad", 28.4089, 77.3178, "faridabad_nasa_power_2025.csv"),
            ("Delhi", 28.6139, 77.2090, "delhi_nasa_power_2025.csv"),
            ("Greater Noida", 28.4744, 77.5040, "greater_noida_nasa_power_2025.csv"),
        )
        try:
            locations = []
            for name, lat, lon, filename in datasets:
                summary = load_summary(data_dir / filename)
                summary.update({"location": name, "coordinates": {"latitude": lat, "longitude": lon}})
                locations.append(summary)
            return jsonify({
                "source": "NASA POWER",
                "period": locations[0]["period"],
                "locations": locations,
                "spatial_note": (
                    "These nearby NCR coordinates resolve to the same NASA POWER native grid cell, "
                    "so their 2025 values match. The three named snapshots preserve transparent "
                    "location coverage without claiming false street-level precision."
                ),
                "purpose": "Regional historical baseline for retrospective comparison; not a flood warning source.",
            })
        except (OSError, ValueError):
            return err("historical_dataset_unavailable", 503)

    @app.post("/api/nodes/<node_id>/explain")
    def explain(node_id):
        from .ai_explainer import explain_assessment
        assessment = service.assess_node(conn(), node_id, now(), forecast_fn, settings)
        if assessment is None:
            return err("unknown_node", 404)
        body = request.get_json(silent=True) or {}
        language = "hi" if body.get("language") == "hi" else "en"
        result = explain_assessment(assessment, str(body.get("question", "Explain this station risk.")), language,
                                    settings.openai_api_key, settings.openai_model,
                                    settings.gemini_api_key, settings.gemini_model)
        return jsonify(result)

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
        created = service.run_alert_check(conn(), now(), forecast_fn, settings) if res.stored else []
        delivered = notifications.dispatch_alerts(conn(), created, settings, now())
        return jsonify({"status": res.reason, "dropped_fields": res.dropped_fields,
                        "alerts_created": len(created), "notifications_processed": delivered}), (201 if res.stored else 200)

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
        if not settings.demo_mode:
            return err("demo_mode_disabled", 403)
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
        created = service.run_alert_check(conn(), now())
        delivered = notifications.dispatch_alerts(conn(), created, settings, now())
        return jsonify({"status": "scenario_applied", "node_id": node_id, "scenario": scenario,
                        "alerts_created": len(created), "notifications_processed": delivered})

    @app.post("/api/seed")
    def seed():
        if not settings.demo_mode:
            return err("demo_mode_disabled", 403)
        from .cli import seed_demo
        b = request.get_json(silent=True) or {}
        scen = b.get("scenario")
        count = seed_demo(conn(), now(), scenario_override=scen)
        created = service.run_alert_check(conn(), now())
        delivered = notifications.dispatch_alerts(conn(), created, settings, now())
        return jsonify({"status": "seeded", "count": count, "alerts_created": len(created),
                        "notifications_processed": delivered})

    return app
