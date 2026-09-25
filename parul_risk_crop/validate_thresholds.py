"""Validate flood thresholds on historical data (Parul).

Input CSV columns: date, rain_1h_mm, rain_24h_mm, rain_72h_mm, water_level_cm,
danger_level_cm, rise_cm_per_hr, soil_moisture_pct, forecast_rain_24h_mm,
flood_occurred (0/1). Every row is treated as a fresh, reporting station.

A row is a PREDICTED event when the engine level >= --alert-level (default ORANGE).
Reports precision, recall, false-alarm ratio, false-alarm rate and miss rate, and
can sweep the orange 24 h rainfall threshold to show the trade-off.

Usage:
  python -m parul_risk_crop.validate_thresholds data.csv --alert-level ORANGE --sweep
"""
import argparse
import csv
from dataclasses import replace

from .levels import Level
from .risk_engine import FloodFeatures, FloodThresholds, assess_flood


def _f(v):
    return None if v in ("", None) else float(v)


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def to_features(row):
    return FloodFeatures(
        rain_1h_mm=_f(row.get("rain_1h_mm")), rain_24h_mm=_f(row.get("rain_24h_mm")),
        rain_72h_mm=_f(row.get("rain_72h_mm")), water_level_cm=_f(row.get("water_level_cm")),
        danger_level_cm=_f(row.get("danger_level_cm")), rise_cm_per_hr=_f(row.get("rise_cm_per_hr")),
        soil_moisture_pct=_f(row.get("soil_moisture_pct")),
        forecast_rain_24h_mm=_f(row.get("forecast_rain_24h_mm")), minutes_since_last=0.0)


def confusion(rows, th, alert_level=Level.ORANGE):
    tp = fp = fn = tn = 0
    for row in rows:
        predicted = assess_flood(to_features(row), th).level >= alert_level
        actual = int(row["flood_occurred"]) == 1
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and actual:
            fn += 1
        else:
            tn += 1
    return tp, fp, fn, tn


def metrics(tp, fp, fn, tn):
    div = lambda a, b: a / b if b else None
    precision, recall = div(tp, tp + fp), div(tp, tp + fn)
    f1 = None if precision is None or recall is None or (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall,
            "f1": f1, "false_alarm_ratio": div(fp, tp + fp), "false_alarm_rate": div(fp, fp + tn),
            "miss_rate": div(fn, tp + fn)}


def fmt(v):
    return "n/a" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--alert-level", default="ORANGE", choices=[l.name for l in Level])
    ap.add_argument("--sweep", action="store_true")
    a = ap.parse_args(argv)
    rows = load_rows(a.csv)
    lvl = Level[a.alert_level]
    if "SYNTHETIC" in a.csv.upper():
        print("*** WARNING: synthetic data - these numbers are NOT valid project results ***")
    m = metrics(*confusion(rows, FloodThresholds(), lvl))
    print(f"rows={len(rows)} alert_level>={lvl.name}")
    for k, v in m.items():
        print(f"  {k:18s} {fmt(v)}")
    if a.sweep:
        print("\norange_rain_24h_mm sweep (yellow kept below orange):")
        print(f"  {'orange':>6} {'prec':>6} {'recall':>6} {'f1':>6} {'FAR':>6}")
        for o in range(40, 111, 10):
            th = replace(FloodThresholds(), orange_rain_24h_mm=float(o), yellow_rain_24h_mm=min(30.0, o - 5.0))
            r = metrics(*confusion(rows, th, lvl))
            print(f"  {o:6d} {fmt(r['precision']):>6} {fmt(r['recall']):>6} {fmt(r['f1']):>6} {fmt(r['false_alarm_ratio']):>6}")
    return m


if __name__ == "__main__":
    main()
