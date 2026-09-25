import random
import unittest

from nishant_firmware.simulator import scenarios, simulate


class ScenarioTests(unittest.TestCase):
    def test_backfill_length_and_order(self):
        rows = list(scenarios.backfill("normal", "n", 1_790_000_000, seed=1))
        self.assertEqual(len(rows), 288)
        self.assertTrue(all(b["ts"] - a["ts"] == 300 for a, b in zip(rows, rows[1:])))
        self.assertEqual(rows[-1]["ts"], 1_790_000_000)

    def test_silent_drops_last_45_minutes(self):
        rows = list(scenarios.backfill("silent", "n", 1_790_000_000, seed=1))
        self.assertEqual(len(rows), 288 - 9)

    def test_rain_totals(self):
        heavy = sum(r["rain_mm"] for r in scenarios.backfill("heavy_rain", "n", 1_790_000_000, seed=2))
        flood = sum(r["rain_mm"] for r in scenarios.backfill("flood", "n", 1_790_000_000, seed=2))
        dry = sum(r["rain_mm"] for r in scenarios.backfill("normal", "n", 1_790_000_000, seed=2))
        self.assertEqual(dry, 0)
        self.assertTrue(70 < heavy < 120, heavy)
        self.assertTrue(160 < flood < 250, flood)

    def test_flood_crosses_danger_mark(self):
        rows = list(scenarios.backfill("flood", "n", 1_790_000_000, seed=2))
        self.assertGreater(rows[-1]["water_level_cm"], 450)

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):
            scenarios.make_reading("tsunami", 0.5, 1, random.Random())


class FakeSender:
    def __init__(self): self.sent = []
    def send(self, r): self.sent.append(r); return 201


class RunTests(unittest.TestCase):
    def test_replay(self):
        s = FakeSender()
        simulate.run(s, "n1", "normal", log=lambda *_: None)
        self.assertEqual(len(s.sent), 288)

    def test_realtime_count(self):
        s = FakeSender()
        simulate.run(s, "n1", "heavy_rain", realtime=True, interval=0, count=5, log=lambda *_: None)
        self.assertEqual(len(s.sent), 5)


if __name__ == "__main__":
    unittest.main()
