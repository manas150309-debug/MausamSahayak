"""Train the version-2 crop recommender (Random Forest) - Parul.

Uses only features our stations can measure or fetch: temperature, humidity and
rainfall. Reports a held-out test accuracy and 5-fold cross-validation accuracy.

  python -m parul_risk_crop.train_crop_model data.csv --out parul_risk_crop/data/crop_model.joblib
"""
import argparse

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score, train_test_split

FEATURES = ["temperature", "humidity", "rainfall"]


def train(csv_path, out_path=None, seed=42, n_estimators=200):
    df = pd.read_csv(csv_path)
    missing = [c for c in FEATURES + ["label"] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")
    X, y = df[FEATURES], df["label"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=seed)
    model.fit(Xtr, ytr)
    test_acc = accuracy_score(yte, model.predict(Xte))
    cv = cross_val_score(RandomForestClassifier(n_estimators=n_estimators, random_state=seed), X, y, cv=5)
    if out_path:
        joblib.dump(model, out_path)
    return {"test_accuracy": float(test_acc), "cv_mean": float(cv.mean()), "cv_std": float(cv.std()),
            "n_rows": int(len(df)), "n_classes": int(y.nunique())}


def predict_top(model, temperature, humidity, rainfall, top_n=3):
    X = pd.DataFrame([[temperature, humidity, rainfall]], columns=FEATURES)
    proba = model.predict_proba(X)[0]
    ranked = sorted(zip(model.classes_, proba), key=lambda p: p[1], reverse=True)[:top_n]
    return [{"crop_id": c, "probability": round(float(p), 3)} for c, p in ranked]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="parul_risk_crop/data/crop_model.joblib")
    a = ap.parse_args()
    print(train(a.csv, a.out))
