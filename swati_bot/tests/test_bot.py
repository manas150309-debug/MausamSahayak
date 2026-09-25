import os
import re
import unittest

from manas_backend import db, ingest, service
from manas_backend.api import create_app
from manas_backend.config import Settings
from nishant_firmware.simulator import scenarios
from swati_bot import alerts, formatters, i18n, intents, sms
from swati_bot.api_client import ApiClient, ApiError
from swati_bot.logic import BotLogic
from swati_bot.store import Store

NOW = 1_790_000_000


class FakeResp:
    def __init__(self, status, body): self.status_code, self._b = status, body
    def json(self):
        if isinstance(self._b, Exception): raise self._b
        return self._b


class FlaskSession:
    """Lets ApiClient talk to the real Flask app in-process (true end-to-end test)."""
    def __init__(self, client): self.c = client
    def get(self, url, params=None, timeout=None):
        r = self.c.get("/" + url.split("/", 3)[3], query_string=params)
        return FakeResp(r.status_code, r.json)


class E2E(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.d = tempfile.TemporaryDirectory()
        path = os.path.join(self.d.name, "t.db")
        self.conn = db.connect(path); db.init_db(self.conn)
        service.add_node(self.conn, "n1", "Campus", 28.40, 77.31, "Faridabad", "Haryana", 450.0, NOW)
        service.add_node(self.conn, "n2", "River", 28.42, 77.33, "Faridabad", "Haryana", 450.0, NOW)
        for r in scenarios.backfill("normal", "n1", NOW, seed=1): ingest.store_reading(self.conn, "n1", r, NOW)
        for r in scenarios.backfill("flood", "n2", NOW, seed=1): ingest.store_reading(self.conn, "n2", r, NOW)
        app = create_app(Settings(db_path=path, api_key="k"), forecast_fn=lambda a, b: None, clock=lambda: NOW)
        self.api = ApiClient("http://x", session=FlaskSession(app.test_client()))
        self.store = Store(":memory:")
        self.logic = BotLogic(self.api, self.store)

    def tearDown(self):
        self.conn.close(); self.d.cleanup()

    def test_full_conversation_english(self):
        cid = 1
        self.assertTrue(self.logic.start(cid).ask_language)
        r = self.logic.set_language(cid, "en")
        self.assertTrue(r.ask_location)
        r = self.logic.set_location(cid, 28.401, 77.311)
        self.assertIn("Campus", r.text)
        now = self.logic.handle_text(cid, "what is the weather today").text
        self.assertIn("Temperature", now)
        self.assertIn("Flood:", now)
        risk = self.logic.handle_text(cid, "flood risk").text
        self.assertIn("Advisory only", risk)
        crop = self.logic.handle_text(cid, "crop advice")
        self.assertTrue(crop.ask_irrigation)
        self.assertIn("Crop suggestions", self.logic.crop(cid, True).text)
        self.assertIn("alerts", self.logic.handle_text(cid, "subscribe").text.lower())

    def test_hindi_flood_red_has_advisory_and_authorities(self):
        cid = 2
        self.logic.set_language(cid, "hi")
        self.logic.set_location(cid, 28.42, 77.33)         # nearest = flooding node n2
        text = self.logic.handle_text(cid, "बाढ़ का खतरा").text
        self.assertIn("🔴", text)
        self.assertIn("परामर्श", text)
        self.assertIn("112", text)
        self.assertNotIn("सुरक्षित है।", text.replace("इसका मतलब यह नहीं कि सब सुरक्षित है।", ""))

    def test_no_location_asks_for_it(self):
        r = self.logic.current(99)
        self.assertTrue(r.ask_location)

    def test_far_location_gives_no_local_data(self):
        self.logic.set_language(3, "en")
        r = self.logic.set_location(3, 19.07, 72.87)
        self.assertIn("too far", r.text)
        self.assertTrue(self.logic.current(3).ask_location)
        self.assertTrue(self.logic.subscribe(3).ask_location)

    def test_api_down_message(self):
        class Down:
            def nearest(self, *a): raise ApiError("boom")
            def risk(self, *a): raise ApiError("boom")
        logic = BotLogic(Down(), Store(":memory:"))
        logic.set_language(5, "en")
        self.assertIn("cannot reach", logic.set_location(5, 28.4, 77.3).text)

    def test_end_to_end_alert_flow_with_sms(self):
        cid = 7
        self.logic.set_language(cid, "en")
        self.logic.set_location(cid, 28.42, 77.33)
        self.logic.subscribe(cid)
        self.logic.set_phone(cid, "+919876543210")
        service.run_alert_check(self.conn, NOW)
        new = self.api.alerts(0)
        plans = alerts.plan_notifications(self.store, new, self.store.node_names())
        red = [p for p in plans if "River" in p.text and "Flood" in p.text]
        self.assertTrue(red)
        self.assertEqual(red[0].chat_id, cid)
        self.assertEqual(red[0].sms_to, "+919876543210")
        self.assertIn("FLOOD ALERT", red[0].sms_text)
        self.assertIn("advisory", red[0].text.lower())


class UnitTests(unittest.TestCase):
    def test_intents(self):
        cases = {"weather please": "weather", "aaj ka mausam": "weather", "बारिश कब होगी": "weather",
                 "flood aayega kya": "flood", "बाढ़ आएगी क्या": "flood", "kaunsi fasal boyein": "crop",
                 "फसल सलाह": "crop", "subscribe": "subscribe", "अलर्ट बंद": "unsubscribe", "नमस्ते": "greeting",
                 "asdf": None, "": None, "garmi": "heat", "hi": "greeting"}
        for text, want in cases.items():
            self.assertEqual(intents.detect_intent(text), want, text)

    def test_translations_are_complete(self):
        self.assertEqual(set(i18n.TEXT["en"]), set(i18n.TEXT["hi"]))
        for table in (i18n.REASONS, i18n.CROP_REASONS):
            self.assertEqual(set(table["en"]), set(table["hi"]))
        for adv in (i18n.FLOOD_ADVICE, i18n.HEAT_ADVICE):
            self.assertEqual(set(adv["en"]), set(adv["hi"]))
            self.assertEqual(set(adv["en"]), set(i18n.LEVEL_EMOJI))

    def test_every_engine_reason_code_is_translated(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "parul_risk_crop", "risk_engine.py")) as fh:
            src = fh.read()
        codes = set(re.findall(r'hit\(Level\.\w+,\s*"(\w+)"', src))
        self.assertGreater(len(codes), 15)
        for c in codes:
            self.assertIn(c, i18n.REASONS["en"], c)
            self.assertIn(c, i18n.REASONS["hi"], c)
        self.assertIn("sensor_offline_none", i18n.REASONS["hi"])

    def test_every_crop_reason_code_is_translated(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "parul_risk_crop", "crop_advisor.py")) as fh:
            src = fh.read()
        for c in set(re.findall(r'"(temp_ok|temp_marginal|rain_ok|rain_low|rain_high|needs_irrigation)"', src)):
            self.assertIn(c, i18n.CROP_REASONS["hi"])

    def test_no_advisory_text_claims_safe(self):
        claim = r"(\bis|\bare) (now )?safe|all clear|no danger"
        for kind in (i18n.FLOOD_ADVICE, i18n.HEAT_ADVICE):
            for level in ("UNKNOWN", "YELLOW", "ORANGE", "RED"):
                self.assertNotRegex(kind["en"][level].replace("does NOT mean it is safe", ""), claim)
        self.assertIn("NOT", i18n.FLOOD_ADVICE["en"]["UNKNOWN"])

    def test_red_text_mentions_authorities_and_advisory(self):
        for lang in ("en", "hi"):
            txt = i18n.FLOOD_ADVICE[lang]["RED"]
            self.assertIn("112", txt)
            self.assertIn("1078", txt)

    def test_format_stale_never_looks_safe(self):
        risk = {"reading": None, "minutes_since_last": None,
                "flood": {"level_name": "UNKNOWN", "stale": True, "reasons": [{"code": "sensor_offline", "params": {"minutes": None}}], "metrics": {}},
                "heat": {"level_name": "UNKNOWN", "stale": True, "reasons": [], "metrics": {}}}
        text = formatters.format_risk("en", risk, "X", 2)
        self.assertIn("unknown", text.lower())
        self.assertIn("NOT", text)
        self.assertIn("not sent any data", text)
        self.assertNotIn("🟢", text)

    def test_should_notify_rules(self):
        A = lambda kind, lvl, prev: {"kind": kind, "level": lvl, "previous_level": prev}
        self.assertTrue(alerts.should_notify(A("flood", 2, 0)))
        self.assertTrue(alerts.should_notify(A("flood", 1, 0)))      # station silent
        self.assertFalse(alerts.should_notify(A("flood", 0, 1)))     # unknown -> green: quiet
        self.assertTrue(alerts.should_notify(A("flood", 2, 4)))      # RED -> yellow: tell people
        self.assertFalse(alerts.should_notify(A("heat", 2, 0)))      # heat yellow is not pushed
        self.assertTrue(alerts.should_notify(A("heat", 3, 0)))

    def test_phone_validation(self):
        self.assertTrue(sms.valid_phone("+919876543210"))
        for bad in ("9876543210", "+911234567890", "+91987654321", "", None, "+9198765432100"):
            self.assertFalse(sms.valid_phone(bad), bad)

    def test_dryrun_sms(self):
        s = sms.DryRunSender(); self.assertTrue(s.send("+919876543210", "x")); self.assertEqual(len(s.sent), 1)

    def test_store(self):
        st = Store(":memory:")
        st.upsert_user(1, lang="en", node_id="n1", node_name="A", subscribed=1)
        st.upsert_user(2, lang="hi", node_id="n1", node_name="A", subscribed=0)
        self.assertEqual([u["chat_id"] for u in st.subscribers_for("n1")], [1])
        with self.assertRaises(ValueError): st.upsert_user(1, evil=1)
        st.set_meta("k", 5); self.assertEqual(st.get_meta("k"), "5")

    def test_latlon_text_sets_location(self):
        class Api:
            def nearest(self, la, lo): return {"node": {"node_id": "n", "name": "N"}, "distance_km": 1.0, "within_range": True}
        logic = BotLogic(Api(), Store(":memory:")); logic.set_language(1, "en")
        self.assertIn("Nearest station", logic.handle_text(1, "28.41, 77.31").text)

    def test_api_client_errors(self):
        class S:
            def __init__(self, r): self.r = r
            def get(self, *a, **k):
                if isinstance(self.r, Exception): raise self.r
                return self.r
        with self.assertRaises(ApiError): ApiClient("http://x", S(RuntimeError("net"))).nearest(1, 1)
        with self.assertRaises(ApiError) as c: ApiClient("http://x", S(FakeResp(500, {}))).nearest(1, 1)
        self.assertEqual(c.exception.status, 500)
        with self.assertRaises(ApiError): ApiClient("http://x", S(FakeResp(200, ValueError()))).nearest(1, 1)
        with self.assertRaises(ApiError) as c: ApiClient("http://x", S(FakeResp(404, {"error": "no_nodes"}))).nearest(1, 1)
        self.assertEqual(c.exception.status, 404)


if __name__ == "__main__":
    unittest.main()
