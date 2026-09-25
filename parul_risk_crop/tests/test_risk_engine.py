import unittest

from parul_risk_crop.levels import Level
from parul_risk_crop.risk_engine import (FloodFeatures, FloodThresholds, HeatThresholds, assess_flood,
                                          assess_heat, heat_index_c)


def fresh(**kw):
    kw.setdefault("minutes_since_last", 2.0)
    kw.setdefault("rain_24h_mm", 0.0)
    return FloodFeatures(**kw)


def codes(res):
    return {r.code for r in res.reasons}


class FloodTests(unittest.TestCase):
    def test_calm_is_green(self):
        r = assess_flood(fresh(water_level_cm=100, danger_level_cm=450, rise_cm_per_hr=0, soil_moisture_pct=40))
        self.assertEqual(r.level, Level.GREEN)
        self.assertFalse(r.stale)

    def test_silent_sensor_is_never_green(self):
        r = assess_flood(FloodFeatures(minutes_since_last=90, rain_24h_mm=0))
        self.assertGreaterEqual(r.level, Level.UNKNOWN)
        self.assertTrue(r.stale)
        self.assertIn("sensor_offline", codes(r))

    def test_never_reported_is_unknown(self):
        r = assess_flood(FloodFeatures())
        self.assertEqual(r.level, Level.UNKNOWN)

    def test_stale_but_last_known_danger_still_red(self):
        r = assess_flood(FloodFeatures(minutes_since_last=120, water_level_cm=460, danger_level_cm=450))
        self.assertEqual(r.level, Level.RED)
        self.assertTrue(r.stale)

    def test_missing_water_sensor_reading_is_unknown(self):
        r = assess_flood(fresh(danger_level_cm=450, water_level_cm=None))
        self.assertEqual(r.level, Level.UNKNOWN)
        self.assertIn("water_level_missing", codes(r))

    def test_node_without_water_sensor_not_flagged(self):
        r = assess_flood(fresh(danger_level_cm=None, water_level_cm=None))
        self.assertEqual(r.level, Level.GREEN)

    def test_missing_rain_data_is_unknown(self):
        r = assess_flood(FloodFeatures(minutes_since_last=1, rain_24h_mm=None))
        self.assertEqual(r.level, Level.UNKNOWN)

    def test_rain_bands(self):
        self.assertEqual(assess_flood(fresh(rain_24h_mm=29)).level, Level.GREEN)
        self.assertEqual(assess_flood(fresh(rain_24h_mm=31)).level, Level.YELLOW)
        self.assertEqual(assess_flood(fresh(rain_24h_mm=66)).level, Level.ORANGE)

    def test_intense_hour_is_orange(self):
        self.assertEqual(assess_flood(fresh(rain_1h_mm=35)).level, Level.ORANGE)

    def test_72h_rain(self):
        self.assertEqual(assess_flood(fresh(rain_72h_mm=80)).level, Level.YELLOW)
        self.assertEqual(assess_flood(fresh(rain_72h_mm=160)).level, Level.ORANGE)

    def test_level_above_danger_is_red(self):
        r = assess_flood(fresh(water_level_cm=451, danger_level_cm=450))
        self.assertEqual(r.level, Level.RED)
        self.assertIn("level_above_danger", codes(r))

    def test_near_danger_and_rising_is_orange(self):
        r = assess_flood(fresh(water_level_cm=330, danger_level_cm=450, rise_cm_per_hr=4))
        self.assertEqual(r.level, Level.ORANGE)

    def test_near_danger_but_falling_is_only_yellow(self):
        r = assess_flood(fresh(water_level_cm=330, danger_level_cm=450, rise_cm_per_hr=-2))
        self.assertEqual(r.level, Level.YELLOW)

    def test_rapid_rise_saturated_heavy_forecast_is_red(self):
        r = assess_flood(fresh(water_level_cm=200, danger_level_cm=450, rise_cm_per_hr=12,
                               soil_moisture_pct=92, forecast_rain_24h_mm=80))
        self.assertEqual(r.level, Level.RED)

    def test_rapid_rise_alone_is_orange(self):
        r = assess_flood(fresh(water_level_cm=200, danger_level_cm=450, rise_cm_per_hr=12))
        self.assertEqual(r.level, Level.ORANGE)

    def test_very_heavy_rain_on_saturated_soil_is_red(self):
        r = assess_flood(fresh(rain_24h_mm=120, soil_moisture_pct=90))
        self.assertEqual(r.level, Level.RED)

    def test_forecast_only_raises_yellow(self):
        r = assess_flood(fresh(forecast_rain_24h_mm=90))
        self.assertEqual(r.level, Level.YELLOW)

    def test_flash_wave_is_red_even_far_below_danger(self):
        r = assess_flood(fresh(water_level_cm=150, danger_level_cm=450, rise_cm_per_hr=45))
        self.assertEqual(r.level, Level.RED)
        self.assertIn("flash_rise", codes(r))

    def test_upstream_surge_gives_early_orange(self):
        r = assess_flood(fresh(water_level_cm=100, danger_level_cm=450, rise_cm_per_hr=0,
                               upstream_rise_cm_per_hr=15, upstream_level_ratio=0.4, upstream_minutes_since_last=3))
        self.assertEqual(r.level, Level.ORANGE)
        self.assertIn("upstream_surge", codes(r))

    def test_upstream_surge_near_danger_is_red(self):
        r = assess_flood(fresh(water_level_cm=100, danger_level_cm=450,
                               upstream_rise_cm_per_hr=15, upstream_level_ratio=0.9, upstream_minutes_since_last=3))
        self.assertEqual(r.level, Level.RED)

    def test_upstream_rising_is_yellow(self):
        r = assess_flood(fresh(upstream_rise_cm_per_hr=4, upstream_minutes_since_last=3))
        self.assertEqual(r.level, Level.YELLOW)

    def test_stale_upstream_is_ignored_not_trusted(self):
        r = assess_flood(fresh(upstream_rise_cm_per_hr=20, upstream_level_ratio=0.9, upstream_minutes_since_last=200))
        self.assertEqual(r.level, Level.GREEN)

    def test_reasons_are_not_duplicated(self):
        r = assess_flood(fresh(rain_24h_mm=80, rain_72h_mm=160))
        cs = [x.code for x in r.reasons]
        self.assertEqual(len(cs), len(set(cs)))

    def test_result_serialises(self):
        d = assess_flood(fresh(rain_24h_mm=70)).to_dict()
        self.assertEqual(d["level_name"], "ORANGE")
        self.assertEqual(d["reasons"][0]["code"], "rain_24h")

    def test_custom_thresholds(self):
        th = FloodThresholds(orange_rain_24h_mm=40)
        self.assertEqual(assess_flood(fresh(rain_24h_mm=45), th).level, Level.ORANGE)


class HeatTests(unittest.TestCase):
    def test_heat_index_reference_values(self):
        # NWS chart: 90F / 70% RH -> ~106F ; 96F / 65% RH -> ~121F ; 80F/40% ~ 80F
        self.assertAlmostEqual(heat_index_c(32.2, 70), (106 - 32) * 5 / 9, delta=1.5)
        self.assertAlmostEqual(heat_index_c(35.6, 65), (121 - 32) * 5 / 9, delta=1.5)
        self.assertAlmostEqual(heat_index_c(26.7, 40), 26.0, delta=1.5)

    def test_levels(self):
        self.assertEqual(assess_heat(25, 50, 1).level, Level.GREEN)
        self.assertEqual(assess_heat(41, 20, 1).level, Level.ORANGE)
        self.assertEqual(assess_heat(46, 20, 1).level, Level.RED)
        self.assertEqual(assess_heat(34, 50, 1).level, Level.YELLOW)

    def test_stale_and_missing(self):
        self.assertGreaterEqual(assess_heat(25, 50, 100).level, Level.UNKNOWN)
        self.assertEqual(assess_heat(None, None, 1).level, Level.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
