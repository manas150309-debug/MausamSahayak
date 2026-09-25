"""Summarise the user-trial form responses (Anil). CSV columns: see docs/user_trial_form.md

  python -m anil_docs.tools.trial_analysis responses.csv
"""
import csv
import statistics
import sys

SCORES = ["clarity_1to5", "hindi_quality_1to5", "usefulness_1to5", "trust_1to5"]


def analyse(rows):
    out = {"n": len(rows)}
    for col in SCORES:
        vals = [float(r[col]) for r in rows if r.get(col, "").strip()]
        out[col] = None if not vals else {"mean": round(statistics.mean(vals), 2), "min": min(vals), "max": max(vals)}
    times = [float(r["reply_seconds"]) for r in rows if r.get("reply_seconds", "").strip()]
    out["reply_seconds_median"] = None if not times else statistics.median(times)
    out["understood_evacuation_advice_pct"] = None
    yes = [r["understood_advice_yes_no"].strip().lower() for r in rows if r.get("understood_advice_yes_no", "").strip()]
    if yes:
        out["understood_evacuation_advice_pct"] = round(100 * yes.count("yes") / len(yes), 1)
    return out


if __name__ == "__main__":
    with open(sys.argv[1], newline="", encoding="utf-8") as fh:
        for k, v in analyse(list(csv.DictReader(fh))).items():
            print(k, v)
