"""Generate a SYNTHETIC flood-history CSV so the validation pipeline can be run
before real IMD/CWC data is collected.

!! The numbers this produces are NOT results. They only prove the pipeline works.
!! Replace data/sample_history_SYNTHETIC.csv with real event data (see
!! anil_docs/docs/data_sources.md) before quoting any precision/recall figure.
"""
import argparse
import csv
import random

COLUMNS = ["date", "rain_1h_mm", "rain_24h_mm", "rain_72h_mm", "water_level_cm", "danger_level_cm",
           "rise_cm_per_hr", "soil_moisture_pct", "forecast_rain_24h_mm", "flood_occurred"]


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def generate(n=600, seed=42, danger=450.0):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        flood = 1 if rng.random() < 0.12 else 0
        if flood:
            r24 = clip(rng.gauss(85, 30), 10, 260)
            ratio = rng.uniform(0.6, 1.1)
            rise = rng.gauss(8, 4)
            soil = clip(rng.gauss(85, 8), 40, 100)
            fc = clip(rng.gauss(60, 30), 0, 200)
        else:
            r24 = rng.expovariate(1 / 15) + (rng.uniform(30, 90) if rng.random() < 0.12 else 0)
            ratio = rng.uniform(0.2, 0.7)
            rise = rng.gauss(0.5, 2)
            soil = clip(rng.gauss(55, 15), 10, 100)
            fc = rng.expovariate(1 / 12)
        r72 = r24 * rng.uniform(1.0, 2.2)
        r1 = r24 * rng.uniform(0.05, 0.3)
        rows.append([f"synthetic-{i:04d}", round(r1, 1), round(r24, 1), round(r72, 1),
                     round(ratio * danger, 1), danger, round(rise, 1), round(soil, 1), round(fc, 1), flood])
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="parul_risk_crop/data/sample_history_SYNTHETIC.csv")
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        w.writerows(generate(a.n, a.seed))
    print(f"wrote {a.n} SYNTHETIC rows to {a.out}")
