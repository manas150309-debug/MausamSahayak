import json
import os
import tempfile
import time
import unittest

from manas_backend import cli, db, ingest, service
from manas_backend.api import create_app
from manas_backend.config import Settings
from nishant_firmware.simulator import scenarios

NOW = 1_790_000_000   # fixed "current time" for deterministic tests


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "t.db")
        self.settings = Settings(db_path=self.path, api_key="k")
        self.conn = db.connect(self.path)
        db.init_db(self.conn)
        service.add_node(self.conn, "n1", "Node 1", 28.40, 77.31, "Faridabad", "Haryana", 450.0, NOW)

    def tearDown(self):
        self.conn.close()
        self.dir.cleanup()

    def feed(self, scenario, node="n1", now=NOW):
        for r in scenarios.backfill(scenario, node, now, seed=1):
            ingest.store_reading(self.conn, node, r, now)


class IngestTests(Base):
    def test_stores_valid(self):
        res = ingest.store_reading(self.conn, "n1", {"ts": NOW, "temperature_c": 30, "rain_mm": 0.28}, NOW)
        self.assertTrue(res.ok and res.stored)

    def test_unknown_node_rejected(self):
        self.assertEqual(ingest.store_reading(self.conn, "zzz", {"temperature_c": 30}, NOW).reason, "unknown_node")

    def test_out_of_range_becomes_null_not_trusted(self):
        res = ingest.store_reading(self.conn, "n1", {"ts": NOW, "temperature_c": 30, "humidity_pct": 250}, NOW)
        self.assertEqual(res.dropped_fields, ["humidity_pct"])
        self.assertIsNone(service.latest_reading(self.conn, "n1")["humidity_pct"])

    def test_all_invalid_rejected(self):
        self.assertFalse(ingest.store_reading(self.conn, "n1", {"temperature_c": 999}, NOW).ok)

    def test_duplicate_timestamp_ignored(self):
        ingest.store_reading(self.conn, "n1", {"ts": NOW, "rain_mm": 1.0, "temperature_c": 30}, NOW)
        res = ingest.store_reading(self.conn, "n1", {"ts": NOW, "rain_mm": 1.0, "temperature_c": 30}, NOW)
        self.assertEqual(res.reason, "duplicate")
        self.assertEqual(service.rain_sum(self.conn, "n1", 1, NOW), 1.0)

    def test_bad_or_missing_ts_uses_server_time(self):
        res = ingest.store_reading(self.conn, "n1", {"ts": 5, "temperature_c": 30}, NOW)
        self.assertEqual(res.ts, NOW)
        res = ingest.store_reading(self.conn, "n1", {"ts": (NOW + 99999) * 1000, "temperature_c": 31}, NOW)
        self.assertEqual(res.ts, NOW)

    def test_millisecond_ts_accepted(self):
        res = ingest.store_reading(self.conn, "n1", {"ts": (NOW - 60) * 1000, "temperature_c": 30}, NOW)
        self.assertEqual(res.ts, NOW - 60)

    def test_nan_and_strings_dropped(self):
        res = ingest.store_reading(self.conn, "n1", {"temperature_c": 30, "humidity_pct": "abc", "rain_mm": float("nan")}, NOW)
        self.assertEqual(set(res.dropped_fields), {"humidity_pct", "rain_mm"})

    def test_mqtt_message_handling(self):
        p = json.dumps({"node_id": "n1", "ts": NOW, "temperature_c": 28.5}).encode()
        self.assertTrue(ingest.handle_message(self.conn, "mausam/nodes/n1/telemetry", p, NOW).ok)
        self.assertEqual(ingest.handle_message(self.conn, "other/topic", p, NOW).reason, "bad_topic")
        self.assertEqual(ingest.handle_message(self.conn, "mausam/nodes/n1/telemetry", b"{oops", NOW).reason, "bad_json")
        self.assertEqual(ingest.handle_message(self.conn, "mausam/nodes/n2/telemetry", p, NOW).reason, "node_id_mismatch")


class AssessmentTests(Base):
    def test_normal_is_green(self):
        self.feed("normal")
        a = service.assess_node(self.conn, "n1", NOW)
        self.assertEqual(a["flood"]["level_name"], "GREEN")
        self.assertEqual(a["heat"]["level_name"] in ("GREEN", "YELLOW", "ORANGE"), True)

    def test_flood_scenario_is_red(self):
        self.feed("flood")
        a = service.assess_node(self.conn, "n1", NOW)
        self.assertEqual(a["flood"]["level_name"], "RED", a["flood"])

    def test_heavy_rain_is_at_least_yellow(self):
        self.feed("heavy_rain")
        a = service.assess_node(self.conn, "n1", NOW)
        self.assertIn(a["flood"]["level_name"], ("YELLOW", "ORANGE", "RED"))

    def test_silent_station_is_unknown_never_green(self):
        self.feed("silent")
        a = service.assess_node(self.conn, "n1", NOW)
        self.assertTrue(a["flood"]["stale"])
        self.assertEqual(a["flood"]["level_name"], "UNKNOWN")

    def test_no_readings_is_unknown(self):
        a = service.assess_node(self.conn, "n1", NOW)
        self.assertEqual(a["flood"]["level_name"], "UNKNOWN")

    def test_rise_rate_positive_during_flood(self):
        self.feed("flood")
        peak = NOW - int(0.4 * 86400)          # storm peak in the scenario
        self.assertGreater(service.rise_rate(self.conn, "n1", peak), 10)

    def test_forecast_failure_does_not_break(self):
        self.feed("normal")
        def boom(lat, lon): raise RuntimeError("down")
        self.assertEqual(service.assess_node(self.conn, "n1", NOW, boom)["flood"]["level_name"], "GREEN")

    def test_forecast_feeds_engine(self):
        self.feed("normal")
        a = service.assess_node(self.conn, "n1", NOW, lambda la, lo: {"next_24h_mm": 90.0, "next_72h_mm": 120.0})
        self.assertEqual(a["flood"]["level_name"], "YELLOW")


class AlertTests(Base):
    def test_first_green_pass_creates_no_alert(self):
        self.feed("normal")
        flood = [a for a in service.run_alert_check(self.conn, NOW) if a["kind"] == "flood"]
        self.assertEqual(flood, [])

    def test_flood_creates_one_alert_then_dedupes(self):
        self.feed("flood")
        first = service.run_alert_check(self.conn, NOW)
        self.assertTrue(any(a["kind"] == "flood" and a["level_name"] == "RED" for a in first))
        self.assertEqual([a for a in service.run_alert_check(self.conn, NOW + 60) if a["kind"] == "flood"], [])

    def test_silent_node_alerts_unknown_once(self):
        self.feed("silent")
        alerts = service.run_alert_check(self.conn, NOW)
        self.assertEqual([(a["kind"], a["level_name"]) for a in alerts], [("flood", "UNKNOWN")])

    def test_deescalation_waits(self):
        self.feed("flood")
        service.run_alert_check(self.conn, NOW)
        # 10 minutes later the node goes quiet-but-fresh with low readings: new data at NOW+600 says GREEN-ish
        later = NOW + 4 * 86400        # rain windows have rolled off
        ingest.store_reading(self.conn, "n1", {"ts": later, "temperature_c": 30, "humidity_pct": 50, "rain_mm": 0,
                                               "water_level_cm": 100, "soil_moisture_pct": 40}, later)
        self.assertNotEqual(service.run_alert_check(self.conn, later), [])   # >30 min since last alert -> lowered
        # but with a fresh alert, an immediate drop is held back
        self.conn.execute("DELETE FROM alerts"); self.conn.commit()
        self.conn.execute("INSERT INTO alerts(node_id,ts,kind,level,previous_level,stale,reasons) VALUES ('n1',?,?,?,?,0,'[]')",
                          (later - 60, "flood", 4, 0)); self.conn.commit()
        self.assertEqual([a for a in service.run_alert_check(self.conn, later) if a["kind"] == "flood"], [])

    def test_uncommissioned_node_skipped(self):
        service.add_node(self.conn, "n2", "New", 28.5, 77.3, danger_level_cm=300)
        self.assertEqual(service.run_alert_check(self.conn, NOW), [])

    def test_alerts_since(self):
        self.feed("flood")
        service.run_alert_check(self.conn, NOW)
        al = service.alerts_since(self.conn, 0)
        self.assertGreaterEqual(len(al), 1)
        self.assertEqual(service.alerts_since(self.conn, al[-1]["id"]), [])


class NearestAndCropTests(Base):
    def test_nearest(self):
        service.add_node(self.conn, "far", "Far", 19.07, 72.87)
        n = service.nearest_node(self.conn, 28.41, 77.32, 30)
        self.assertEqual(n["node"]["node_id"], "n1")
        self.assertTrue(n["within_range"])
        m = service.nearest_node(self.conn, 19.0, 72.8, 30)
        self.assertEqual(m["node"]["node_id"], "far")

    def test_out_of_range(self):
        n = service.nearest_node(self.conn, 19.07, 72.87, 30)
        self.assertFalse(n["within_range"])
        self.assertEqual(service.crop_advice(self.conn, 19.07, 72.87, NOW, settings=self.settings)["error"], "no_station_in_range")

    def test_crop_advice(self):
        self.feed("normal")
        res = service.crop_advice(self.conn, 28.41, 77.32, NOW, irrigated=True, settings=self.settings)
        self.assertEqual(res["node_id"], "n1")
        self.assertIn(res["season"], ("kharif", "rabi", "zaid"))
        self.assertIn("recommendations", res)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        self.app = create_app(self.settings, forecast_fn=lambda la, lo: None, clock=lambda: NOW)
        self.c = self.app.test_client()

    def test_health_and_dashboard(self):
        self.assertEqual(self.c.get("/health").json["status"], "ok")
        r = self.c.get("/dashboard")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"MausamSahayak", r.data)
        r.close()

    def test_write_requires_key(self):
        self.assertEqual(self.c.post("/api/readings", json={"node_id": "n1", "temperature_c": 30}).status_code, 401)
        self.assertEqual(self.c.post("/api/readings", json={"node_id": "n1", "temperature_c": 30},
                                     headers={"X-API-Key": "wrong"}).status_code, 401)

    def test_no_key_configured_disables_writes(self):
        app = create_app(Settings(db_path=self.path, api_key=""), clock=lambda: NOW)
        r = app.test_client().post("/api/readings", json={"node_id": "n1", "temperature_c": 30}, headers={"X-API-Key": ""})
        self.assertEqual(r.status_code, 401)

    def test_post_and_read_back(self):
        h = {"X-API-Key": "k"}
        r = self.c.post("/api/readings", json={"node_id": "n1", "ts": NOW - 60, "temperature_c": 31.5, "humidity_pct": 60,
                                               "rain_mm": 0, "water_level_cm": 120, "soil_moisture_pct": 40}, headers=h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.c.post("/api/readings", json={"node_id": "nope", "temperature_c": 1}, headers=h).status_code, 404)
        self.assertEqual(self.c.post("/api/readings", json={"node_id": "n1", "temperature_c": 900}, headers=h).status_code, 422)
        lat = self.c.get("/api/nodes/n1/latest").json
        self.assertEqual(lat["reading"]["temperature_c"], 31.5)
        self.assertFalse(lat["stale"])
        self.assertEqual(self.c.get("/api/nodes/zzz/latest").status_code, 404)

    def test_risk_and_history_and_alerts(self):
        self.feed("flood")
        risk = self.c.get("/api/nodes/n1/risk").json
        self.assertEqual(risk["flood"]["level_name"], "RED")
        self.assertGreater(len(self.c.get("/api/nodes/n1/history?hours=6").json["readings"]), 10)
        service.run_alert_check(self.conn, NOW)
        self.assertGreaterEqual(len(self.c.get("/api/alerts?since_id=0").json["alerts"]), 1)

    def test_nearest_and_crops(self):
        self.feed("normal")
        self.assertEqual(self.c.get("/api/nearest?lat=28.41&lon=77.32").json["node"]["node_id"], "n1")
        self.assertEqual(self.c.get("/api/nearest?lat=abc&lon=1").status_code, 400)
        self.assertEqual(self.c.get("/api/crop-advice?lat=28.41&lon=77.32&irrigated=1").status_code, 200)
        self.assertEqual(self.c.get("/api/crop-advice?lat=19&lon=72").status_code, 404)

    def test_register_node(self):
        r = self.c.post("/api/nodes", json={"node_id": "n9", "lat": 28.0, "lon": 77.0, "danger_level_cm": 300},
                        headers={"X-API-Key": "k"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(self.c.get("/api/nodes").json["nodes"]), 2)


class UpstreamTests(Base):
    def test_downstream_warns_from_upstream_surge(self):
        service.add_node(self.conn, "up", "Upstream", 28.5, 77.4, "Faridabad", "Haryana", 450.0, NOW)
        service.add_node(self.conn, "n1", "Node 1", 28.40, 77.31, "Faridabad", "Haryana", 450.0, NOW, upstream_node_id="up")
        self.feed("normal", "n1")                       # downstream is calm
        # upstream level climbs 25 cm/h for the last 60 minutes
        for i in range(13):
            t = NOW - 3600 + i * 300
            ingest.store_reading(self.conn, "up", {"ts": t, "temperature_c": 25, "rain_mm": 1.0,
                                                   "water_level_cm": 150 + 25 * (i * 300 / 3600.0)}, NOW)
        a = service.assess_node(self.conn, "n1", NOW)
        codes = {r["code"] for r in a["flood"]["reasons"]}
        self.assertIn("upstream_surge", codes)
        self.assertGreaterEqual(a["flood"]["level"], 3)

    def test_schema_migration_adds_column(self):
        c = db.connect(":memory:")
        c.execute("CREATE TABLE nodes (node_id TEXT PRIMARY KEY, name TEXT, lat REAL NOT NULL, lon REAL NOT NULL,"
                  " district TEXT, state TEXT, danger_level_cm REAL, created_at INTEGER NOT NULL)")
        db.init_db(c)
        self.assertIn("upstream_node_id", {r["name"] for r in c.execute("PRAGMA table_info(nodes)")})


class DemoSeedTests(Base):
    def test_seed_demo_yields_all_states(self):
        cli.seed_demo(self.conn, NOW)
        levels = {n: service.assess_node(self.conn, n, NOW)["flood"]["level_name"] for n in ("node01", "node02", "node03")}
        self.assertEqual(levels, {"node01": "GREEN", "node02": "RED", "node03": "UNKNOWN"})


if __name__ == "__main__":
    unittest.main()
