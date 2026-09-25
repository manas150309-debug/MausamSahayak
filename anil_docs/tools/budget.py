"""Budget calculator (Anil). Reads docs/budget.csv (item, unit_cost_inr, qty_per_node, shared_qty) and prints totals."""
import csv
import os
import sys

DEFAULT = os.path.join(os.path.dirname(__file__), "..", "docs", "budget.csv")


def load(path=DEFAULT):
    with open(path, newline="", encoding="utf-8") as fh:
        return [{"item": r["item"], "unit": float(r["unit_cost_inr"]), "per_node": int(r["qty_per_node"]),
                 "shared": int(r["shared_qty"])} for r in csv.DictReader(r for r in fh if not r.startswith("#"))]


def totals(rows, nodes=2, contingency=0.10):
    per_node = sum(r["unit"] * r["per_node"] for r in rows)
    shared = sum(r["unit"] * r["shared"] for r in rows)
    subtotal = per_node * nodes + shared
    return {"per_node_inr": per_node, "shared_inr": shared, "nodes": nodes, "subtotal_inr": subtotal,
            "contingency_inr": round(subtotal * contingency), "grand_total_inr": round(subtotal * (1 + contingency))}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    for k, v in totals(load(), n).items():
        print(f"{k:18s} {v:,}")
