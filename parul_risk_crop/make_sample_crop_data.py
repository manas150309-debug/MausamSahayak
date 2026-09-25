"""Create a SYNTHETIC crop dataset (temperature, humidity, rainfall, label) from the
rule table, so train_crop_model.py can be exercised offline.

!! A model trained on this data only re-learns the rules. Its accuracy is
!! meaningless. For real results download a public crop-recommendation dataset
!! (e.g. the Kaggle "Crop Recommendation Dataset", columns N,P,K,temperature,
!! humidity,ph,rainfall,label) and pass it to train_crop_model.py.
"""
import argparse
import csv
import random

from .crops_data import CROPS


def generate(n_per_crop=120, seed=1):
    rng = random.Random(seed)
    rows = []
    for c in CROPS:
        t, r = c["temp"], c["rain"]
        for _ in range(n_per_crop):
            rows.append([round(rng.uniform(t[1], t[2]), 2), round(rng.uniform(40, 90), 2),
                         round(rng.uniform(r[1], r[2]), 1), c["id"]])
    rng.shuffle(rows)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="parul_risk_crop/data/crop_data_SYNTHETIC.csv")
    a = ap.parse_args()
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["temperature", "humidity", "rainfall", "label"])
        w.writerows(generate())
    print("wrote", a.out)
