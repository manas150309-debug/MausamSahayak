import datetime as dt
import os
import tempfile
import unittest

from parul_risk_crop import crop_advisor, forecast, make_sample_crop_data, make_sample_history
from parul_risk_crop import train_crop_model, validate_thresholds


class CropTests(unittest.TestCase):
    def test_seasons(self):
        self.assertEqual(crop_advisor.season_for(dt.date(2026, 7, 10)), "kharif")
        self.assertEqual(crop_advisor.season_for(dt.date(2026, 11, 10)), "rabi")
        self.assertEqual(crop_advisor.season_for(dt.date(2026, 1, 10)), "rabi")
        self.assertEqual(crop_advisor.season_for(dt.date(2026, 4, 10)), "zaid")

    def test_trapezoid(self):
        r = (10, 20, 30, 40)
        self.assertEqual(crop_advisor.trapezoid(25, r), 1.0)
        self.assertEqual(crop_advisor.trapezoid(15, r), 0.5)
        self.assertEqual(crop_advisor.trapezoid(45, r), 0.0)

    def test_rabi_cool_dry_suggests_wheat_or_mustard(self):
        recs = crop_advisor.recommend("rabi", 16, 200, soil_moisture_pct=45, irrigated=True)
        ids = [r["crop_id"] for r in recs]
        self.assertIn("wheat", ids[:3])

    def test_kharif_wet_hot_suggests_rice(self):
        recs = crop_advisor.recommend("kharif", 28, 1200, soil_moisture_pct=70)
        self.assertEqual(recs[0]["crop_id"], "rice")

    def test_temperature_intolerant_crop_excluded(self):
        recs = crop_advisor.recommend("rabi", 45, 200)
        self.assertEqual(recs, [])

    def test_irrigation_changes_ranking_inputs(self):
        dry = crop_advisor.recommend("kharif", 28, 150, irrigated=False)
        irr = crop_advisor.recommend("kharif", 28, 150, irrigated=True)
        self.assertGreaterEqual(len(irr), len(dry))

    def test_normals_lookup_and_default(self):
        self.assertEqual(crop_advisor.seasonal_rain_normal("Faridabad", "kharif"), 450)
        self.assertEqual(crop_advisor.seasonal_rain_normal("Nowhere", "kharif"), 600)
        self.assertEqual(crop_advisor.seasonal_rain_normal(None, "rabi"), 80)


class FakeResp:
    def __init__(self, data): self._d = data
    def raise_for_status(self): pass
    def json(self): return self._d


class FakeSession:
    def __init__(self, data=None, fail=False): self.data, self.fail, self.calls = data, fail, 0
    def get(self, *a, **k):
        self.calls += 1
        if self.fail:
            raise RuntimeError("network down")
        return FakeResp(self.data)


def payload(now, hours=96, per_hour=1.0):
    start = now.replace(minute=0, second=0, microsecond=0) - dt.timedelta(hours=now.hour)
    times = [(start + dt.timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(hours)]
    return {"hourly": {"time": times, "precipitation": [per_hour] * hours}}


class ForecastTests(unittest.TestCase):
    def setUp(self):
        forecast._CACHE.clear()

    def test_parse_sums_next_windows(self):
        now = dt.datetime(2026, 9, 20, 10, 30, tzinfo=dt.timezone.utc)
        res = forecast.parse_open_meteo(payload(now), now)
        self.assertEqual(res["next_24h_mm"], 24.0)
        self.assertEqual(res["next_72h_mm"], 72.0)

    def test_failure_returns_none(self):
        self.assertIsNone(forecast.get_forecast(28.4, 77.3, session=FakeSession(fail=True)))

    def test_bad_payload_returns_none(self):
        self.assertIsNone(forecast.get_forecast(28.4, 77.3, session=FakeSession({"hourly": {}}), use_cache=False))

    def test_cache(self):
        now = dt.datetime.now(dt.timezone.utc)
        s = FakeSession(payload(now, hours=120))
        a = forecast.get_forecast(28.4, 77.3, session=s, now=now)
        b = forecast.get_forecast(28.4, 77.3, session=s, now=now)
        self.assertEqual(a, b)
        self.assertEqual(s.calls, 1)


class PipelineTests(unittest.TestCase):
    def test_validation_pipeline_runs_on_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "hist_SYNTHETIC.csv")
            import csv
            with open(p, "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(make_sample_history.COLUMNS); w.writerows(make_sample_history.generate(300))
            m = validate_thresholds.main([p, "--sweep"])
            self.assertEqual(m["tp"] + m["fp"] + m["fn"] + m["tn"], 300)
            self.assertIsNotNone(m["recall"])

    def test_ml_training_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "crops.csv")
            import csv
            with open(p, "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(["temperature", "humidity", "rainfall", "label"])
                w.writerows(make_sample_crop_data.generate(40))
            out = os.path.join(d, "m.joblib")
            res = train_crop_model.train(p, out, n_estimators=30)
            self.assertGreater(res["test_accuracy"], 0.15)  # chance is 0.05; classes overlap by design
            import joblib
            top = train_crop_model.predict_top(joblib.load(out), 15, 60, 150)
            self.assertEqual(len(top), 3)


if __name__ == "__main__":
    unittest.main()
