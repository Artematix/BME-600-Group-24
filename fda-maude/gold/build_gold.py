"""Build gold_labels_v1.csv from the hand-written label files and check every label.
Usage: python build_gold.py            (writes gold_labels_v1.csv)
       python build_gold.py relabel    (uses relabel_*.py files, writes gold_relabel_check_v1.csv)
Checks: every report labelled once, allowed values, numbers appear in the text as digits,
mmol/L conversions (x18, rounded), wear day and zone appear in the text, evidence quote found in text.
"""
import csv, json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "sample_narratives.jsonl")
MODE = sys.argv[1] if len(sys.argv) > 1 else "gold"

ALLOWED = {
    "fault_type": {"reads_low", "reads_high", "erratic", "stuck", "signal_loss", "sensor_error_or_early_end",
                   "adhesive_or_detachment", "insertion_or_skin_injury", "other_device", "unclear"},
    "multiple_pairs": {"yes", "no"},
    "parkes_zone_stated": {"A", "B", "C", "D", "E", None},
    "fingerstick_check_done": {"yes", "no", "not_stated"},
    "user_action": {"none", "ate_carbs", "took_insulin", "skipped_insulin", "sought_care", "other", "not_stated"},
    "outcome_severity": {"none", "symptoms_only", "hypoglycemia", "hyperglycemia_or_dka", "hospital_or_er", "death", "not_stated"},
    "confidence": {"low", "medium", "high"},
    "values_unit": {"mg/dL", "mmol/L", None},
}

rows = [json.loads(l) for l in open(DATA, encoding="utf-8") if l.strip()]
bykey = {r["mdr_report_key"]: r for r in rows}

def full_text(r):
    return " ".join((t.get("text") or "") for t in r.get("mdr_text", []))

def norm(s):
    # compare words only: drop quotes, brackets and other punctuation, collapse spaces
    s = re.sub(r"[^A-Za-z0-9/.%\s-]", " ", s)
    s = re.sub(r"\.(?!\d)", " ", s)
    return re.sub(r"\s+", " ", s).strip().upper()

def trim_evidence(ev, limit=120):
    # cut a long quote at a word boundary so it stays a true substring
    if len(ev) <= limit:
        return ev
    cut = ev[:limit]
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:")

labels = []
def add(key, fault_type, sensor, meter, unit, multiple_pairs, zone, wear_day, fingerstick, user_action, outcome, confidence, evidence, notes, sraw=None, mraw=None):
    labels.append(dict(mdr_report_key=key, fault_type=fault_type, sensor_value_mgdl=sensor, meter_value_mgdl=meter,
                       values_unit=unit, multiple_pairs=multiple_pairs, parkes_zone_stated=zone, wear_day=wear_day,
                       fingerstick_check_done=fingerstick, user_action=user_action, outcome_severity=outcome,
                       confidence=confidence, evidence=evidence, notes=notes, sraw=sraw, mraw=mraw))

if MODE == "gold":
    files = sorted(glob.glob(os.path.join(HERE, "labels_b*.py")))
    out = os.path.join(HERE, "gold_labels_v1.csv")
    labeller = "ai_reviewer_v1"
else:
    files = sorted(glob.glob(os.path.join(HERE, "relabel_*.py")))
    out = os.path.join(HERE, "gold_relabel_check_v1.csv")
    labeller = "ai_reviewer_v1_blind_recheck"

for f in files:
    exec(open(f, encoding="utf-8").read(), {"add": add})

problems = []
def num_in_text(n, text):
    # digits must appear as a whole number token (50, 50.00, 50MG/DL all count; 150 does not count for 50)
    return re.search(r"(?<![\d.])" + re.escape(str(n)) + r"(?:\.0+)?(?![\d])", text) is not None

seen = set()
for L in labels:
    k = L["mdr_report_key"]
    if k not in bykey:
        problems.append((k, "unknown key")); continue
    if k in seen:
        problems.append((k, "duplicate label"))
    seen.add(k)
    text = full_text(bykey[k])
    for fld, allowed in ALLOWED.items():
        if L[fld] not in allowed:
            problems.append((k, f"bad value {fld}={L[fld]}"))
    if L["values_unit"] == "mmol/L":
        for raw, conv, name in ((L["sraw"], L["sensor_value_mgdl"], "sensor"), (L["mraw"], L["meter_value_mgdl"], "meter")):
            if conv is None and raw is None:
                continue
            if raw is None or conv is None:
                problems.append((k, f"mmol {name}: raw/converted mismatch"))
                continue
            if raw not in text:
                problems.append((k, f"mmol {name} raw {raw} not in text"))
            if round(float(raw) * 18) != conv:
                problems.append((k, f"mmol {name} {raw}x18 != {conv}"))
    else:
        for name in ("sensor_value_mgdl", "meter_value_mgdl"):
            v = L[name]
            if v is not None and not num_in_text(v, text):
                problems.append((k, f"{name}={v} not in text"))
    if L["wear_day"] is not None and not num_in_text(L["wear_day"], text):
        problems.append((k, f"wear_day={L['wear_day']} not in text"))
    if L["parkes_zone_stated"] is not None:
        z = L["parkes_zone_stated"]
        if not re.search(rf"(THE\s+['\"]?{z}['\"]?\s+ZONE|ZONE\s+{z}\b|{z}\s+ZONE)", text, re.I):
            problems.append((k, f"zone {z} not found in text"))
    if len(L["evidence"]) > 120:
        L["evidence"] = trim_evidence(L["evidence"])
    for name in ("sensor_value_mgdl", "meter_value_mgdl"):
        v = L["sraw"] if (name == "sensor_value_mgdl" and L["values_unit"] == "mmol/L") else (L["mraw"] if (name == "meter_value_mgdl" and L["values_unit"] == "mmol/L") else L[name])
        if v is not None and str(v) not in L["evidence"]:
            problems.append((k, f"{name} value {v} is not inside the evidence quote"))
    nt = norm(text)
    for piece in L["evidence"].split(" ... "):
        piece = norm(piece).strip(" .")
        if piece and piece not in nt:
            problems.append((k, f"evidence piece not found: {piece[:60]}"))

missing = [k for k in bykey if k not in seen]
print(f"labels: {len(labels)}  unique: {len(seen)}  missing: {len(missing)}  problems: {len(problems)}")
for k in (missing if MODE == "gold" else []):
    print("MISSING", k)
for p in problems:
    print("PROBLEM", p)

cols = ["mdr_report_key", "brand", "manufacturer", "event_type", "date_received", "fault_type", "sensor_value_mgdl",
        "meter_value_mgdl", "values_unit", "multiple_pairs", "parkes_zone_stated", "wear_day", "fingerstick_check_done",
        "user_action", "outcome_severity", "confidence", "evidence", "labeller", "notes"]
order = {r["mdr_report_key"]: i for i, r in enumerate(rows)}
labels.sort(key=lambda L: order.get(L["mdr_report_key"], 9999))
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for L in labels:
        r = bykey.get(L["mdr_report_key"], {})
        w.writerow({
            "mdr_report_key": L["mdr_report_key"], "brand": r.get("brand_label", ""),
            "manufacturer": r.get("manufacturer_d_name", ""), "event_type": r.get("event_type", ""),
            "date_received": r.get("date_received", ""), "fault_type": L["fault_type"],
            "sensor_value_mgdl": "" if L["sensor_value_mgdl"] is None else L["sensor_value_mgdl"],
            "meter_value_mgdl": "" if L["meter_value_mgdl"] is None else L["meter_value_mgdl"],
            "values_unit": L["values_unit"] or "", "multiple_pairs": L["multiple_pairs"],
            "parkes_zone_stated": L["parkes_zone_stated"] or "", "wear_day": "" if L["wear_day"] is None else L["wear_day"],
            "fingerstick_check_done": L["fingerstick_check_done"], "user_action": L["user_action"],
            "outcome_severity": L["outcome_severity"], "confidence": L["confidence"], "evidence": L["evidence"],
            "labeller": labeller, "notes": L["notes"],
        })
print("wrote", out)
