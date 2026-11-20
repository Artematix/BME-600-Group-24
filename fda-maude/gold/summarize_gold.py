"""Summary numbers for GOLD_SET.md: counts by maker and event type, label distributions,
and the 100 reports a team member should check first (stratified, low confidence first).
Usage: python summarize_gold.py
"""
import os, random
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
g = pd.read_csv(os.path.join(HERE, "gold_labels_v1.csv"), dtype=str, keep_default_na=False)
print("n =", len(g))
print("\nBy brand x event_type:")
print(pd.crosstab(g["brand"], g["event_type"], margins=True).to_string())
for f in ["fault_type", "outcome_severity", "user_action", "fingerstick_check_done", "multiple_pairs",
          "parkes_zone_stated", "values_unit", "confidence"]:
    print(f"\n{f}:")
    vc = g[f].replace("", "(null)").value_counts()
    for k, v in vc.items():
        print(f"  {k}: {v} ({v / len(g) * 100:.0f}%)")
both = ((g["sensor_value_mgdl"] != "") & (g["meter_value_mgdl"] != "")).sum()
sens = (g["sensor_value_mgdl"] != "").sum()
met = (g["meter_value_mgdl"] != "").sum()
wear = (g["wear_day"] != "").sum()
print(f"\nboth numbers: {both}  sensor only or both: {sens}  meter only or both: {met}  wear_day: {wear}")
print("\nboth numbers by brand:")
print(g[(g["sensor_value_mgdl"] != "") & (g["meter_value_mgdl"] != "")].groupby(["brand", "event_type"]).size().to_string())
print("\nfault_type by brand:")
print(pd.crosstab(g["fault_type"], g["brand"]).to_string())
print("\noutcome by event_type:")
print(pd.crosstab(g["outcome_severity"], g["event_type"]).to_string())
print("\nconfidence by brand/event:")
print(pd.crosstab([g["brand"], g["event_type"]], g["confidence"]).to_string())

# 100 for the human check: stratified by brand x event type, in proportion to group size, low confidence first, then random
rng = random.Random(7)
rank = {"low": 0, "medium": 1, "high": 2}
groups = g.groupby(["brand", "event_type"])
sizes = groups.size()
quota = (sizes / len(g) * 100).round().astype(int)
# fix rounding so the total is exactly 100
diff = 100 - quota.sum()
if diff != 0:
    quota[quota.idxmax()] += diff
chosen = []
for key, grp in groups:
    rows = list(grp.itertuples())
    rng.shuffle(rows)
    rows.sort(key=lambda r: rank[r.confidence])
    chosen.extend(r.mdr_report_key for r in rows[: quota[key]])
chosen_df = g[g["mdr_report_key"].isin(chosen)]
print("\nhuman check set:", len(chosen))
print(pd.crosstab([chosen_df["brand"], chosen_df["event_type"]], chosen_df["confidence"]).to_string())
with open(os.path.join(HERE, "human_check_keys.txt"), "w") as f:
    f.write("\n".join(chosen) + "\n")
print("\nkeys written to human_check_keys.txt")
