"""Self-check: compare the blind re-labels (gold_relabel_check_v1.csv) with the first labels (gold_labels_v1.csv).
Prints percent exact agreement per field and Cohen's kappa for fault_type, user_action, outcome_severity.
Usage: python check_agreement.py
"""
import os
import pandas as pd
from sklearn.metrics import cohen_kappa_score

HERE = os.path.dirname(os.path.abspath(__file__))
g = pd.read_csv(os.path.join(HERE, "gold_labels_v1.csv"), dtype=str, keep_default_na=False)
r = pd.read_csv(os.path.join(HERE, "gold_relabel_check_v1.csv"), dtype=str, keep_default_na=False)
m = r.merge(g, on="mdr_report_key", suffixes=("_re", "_gold"))
fields = ["fault_type", "sensor_value_mgdl", "meter_value_mgdl", "values_unit", "multiple_pairs", "parkes_zone_stated",
          "wear_day", "fingerstick_check_done", "user_action", "outcome_severity", "confidence"]
print(f"reports compared: {len(m)}")
print("| Field | Exact agreement | Cohen's kappa |")
print("|---|---|---|")
rows = []
for f in fields:
    a, b = m[f + "_gold"], m[f + "_re"]
    agree = (a == b).mean() * 100
    kappa = ""
    if f in ("fault_type", "user_action", "outcome_severity", "fingerstick_check_done", "confidence"):
        try:
            kappa = f"{cohen_kappa_score(a, b):.2f}"
        except Exception as e:
            kappa = "n/a"
    print(f"| {f} | {agree:.0f}% ({int((a == b).sum())}/{len(m)}) | {kappa} |")
    rows.append((f, agree, kappa))
print()
print("Disagreements:")
for _, row in m.iterrows():
    diffs = [f"{f}: {row[f + '_gold']} -> {row[f + '_re']}" for f in fields if row[f + "_gold"] != row[f + "_re"]]
    if diffs:
        print(row["mdr_report_key"], row["brand_gold"], "|", "; ".join(diffs))
