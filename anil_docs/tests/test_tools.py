import csv
import datetime as dt
import os
import tempfile
import unittest

from anil_docs.tools import budget, fetch_historical_rain as fh, trial_analysis


class FakeSession:
    def get(self, url, params=None, timeout=None):
        class R:
            def raise_for_status(self): pass
            def json(self):
                return {"daily": {"time": ["2024-07-01", "2024-07-02", "2024-07-03", "2024-07-04"],
                                  "precipitation_sum": [10.0, 60.0, None, 5.0]}}
        return R()


class ToolTests(unittest.TestCase):
    def test_rows_and_labels(self):
        daily = fh.fetch_daily(27, 94, "2024-07-01", "2024-07-04", FakeSession())
        rows = fh.build_rows(daily, [dt.date(2024, 7, 2)], window_days=1)
        self.assertEqual([r[-1] for r in rows], [0, 1, 1, 0])
        self.assertEqual(rows[2][2], 0.0)          # None rainfall -> 0
        self.assertEqual(rows[2][3], 70.0)         # 72 h rolling sum = 10 + 60 + 0

    def test_events_parser(self):
        self.assertEqual(fh.load_events(["2024-07-02 # big one", "", "# c"]), [dt.date(2024, 7, 2)])

    def test_output_feeds_validation(self):
        from parul_risk_crop import validate_thresholds
        daily = [(f"2024-07-{d:02d}", v) for d, v in zip(range(1, 11), [5, 5, 80, 90, 5, 5, 5, 5, 70, 5])]
        rows = fh.build_rows(daily, [dt.date(2024, 7, 3), dt.date(2024, 7, 9)], 1)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "h.csv")
            with open(p, "w", newline="") as f:
                w = csv.writer(f); w.writerow(fh.COLUMNS); w.writerows(rows)
            m = validate_thresholds.main([p])
        self.assertEqual(m["tp"] + m["fp"] + m["fn"] + m["tn"], 10)

    def test_budget(self):
        rows = budget.load()
        t = budget.totals(rows, nodes=2)
        self.assertGreater(t["per_node_inr"], 5000)
        self.assertLess(t["per_node_inr"], 12000)         # matches the plan's Rs 9k-12k per node
        self.assertEqual(t["subtotal_inr"], t["per_node_inr"] * 2 + t["shared_inr"])
        self.assertGreater(budget.totals(rows, 3)["grand_total_inr"], t["grand_total_inr"])

    def test_trial_analysis(self):
        rows = [{"clarity_1to5": "4", "hindi_quality_1to5": "5", "usefulness_1to5": "", "trust_1to5": "3",
                 "reply_seconds": "2", "understood_advice_yes_no": "yes"},
                {"clarity_1to5": "2", "hindi_quality_1to5": "4", "usefulness_1to5": "", "trust_1to5": "3",
                 "reply_seconds": "4", "understood_advice_yes_no": "no"}]
        r = trial_analysis.analyse(rows)
        self.assertEqual(r["clarity_1to5"]["mean"], 3.0)
        self.assertIsNone(r["usefulness_1to5"])
        self.assertEqual(r["reply_seconds_median"], 3.0)
        self.assertEqual(r["understood_evacuation_advice_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
