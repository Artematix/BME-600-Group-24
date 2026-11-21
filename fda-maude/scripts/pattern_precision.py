#!/usr/bin/env python
"""
pattern_precision.py : measures the precision of the version 2 text patterns (Phase 1, BMEN 600 Group 24).

Precision = of the sensor-meter pairs the patterns output, the share that are right.
A pair = the sensor value and the fingerstick meter value a report states for the same moment.

Three measurements
  1. gold    Against the reference set (287 reports labelled by an AI reviewer, gold/gold_labels_v1.csv).
  2. model   Against the language model on the run set (clean/text_extract_v3.jsonl, 124,599 reports).
  3. sample  A direct read of 100 random malfunction-only pairs (seed 20261120, spread over makers by share).

The patterns are NOT re-run over all reports. The saved output clean/regex_v2_full.csv.gz is used.
The patterns are re-run only on the 287 reference reports and the 100 sampled reports, as a check that the
saved output still matches the current pattern script.

Commands (run from the repo root, plain python):
  python -B fda-maude/scripts/pattern_precision.py sample             draw the 100 reports, write the sample CSV
                                                                     (verdicts already in the CSV are kept)
  python -B fda-maude/scripts/pattern_precision.py texts --batch 1    print 10 report texts for reading (to the screen only)
  python -B fda-maude/scripts/pattern_precision.py judge --verdicts f merge a verdict file (key,verdict,reason) into the sample CSV
  python -B fda-maude/scripts/pattern_precision.py stats              build all counts, write the stats JSON

Files written
  results/text/pattern_precision_sample.csv   one row per sampled report (no report text)
  results/text/pattern_precision_stats.json   all counts
"""

import argparse
import collections
import csv
import json
import math
import random
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FDA = HERE.parent

SEED = 20261120
N_SAMPLE = 100
STRATA = ["Abbott", "Dexcom", "Medtronic", "Other"]        # "Other" = Senseonics and every other maker
VERDICTS = ["right", "swapped", "wrong moment", "wrong number", "unclear"]
SAMPLE_COLUMNS = ["mdr_report_key", "maker", "sensor_value_mgdl", "meter_value_mgdl", "verdict", "reason"]
SENSOR_RANGE = (20.0, 600.0)      # same plausibility limits as extract_regex_v2.py
METER_RANGE = (20.0, 1500.0)

P_FULL = FDA / "clean" / "regex_v2_full.csv.gz"
P_PARQUET = FDA / "clean" / "full.parquet"
P_MODEL = FDA / "clean" / "text_extract_v3.jsonl"
P_GOLD = FDA / "gold" / "gold_labels_v1.csv"
P_SAMPLE = FDA / "results" / "text" / "pattern_precision_sample.csv"
P_STATS = FDA / "results" / "text" / "pattern_precision_stats.json"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def wilson(k, n, z=1.959964):
    """95 % Wilson interval for k right out of n. Returns (low, high) as shares."""
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def share(k, n):
    """Count, total, percent and Wilson interval in one small dict."""
    lo, hi = wilson(k, n)
    return {"count": int(k), "of": int(n), "pct": round(100 * k / n, 1) if n else None,
            "wilson95_low_pct": round(100 * lo, 1) if n else None, "wilson95_high_pct": round(100 * hi, 1) if n else None}


def stratum_of(brand):
    return brand if brand in ("Abbott", "Dexcom", "Medtronic") else "Other"


def event_side(event_group):
    return "malfunction-only" if event_group == "malfunction" else "death or injury"


def load_full_output():
    """The saved pattern output for all 3,382,071 reports (one row per report)."""
    cols = ["mdr_report_key", "event_type", "event_group", "brand", "sensor_value", "meter_value", "pattern", "value_flags"]
    df = pd.read_csv(P_FULL, dtype=str, keep_default_na=False, usecols=cols)
    df["sensor_num"] = pd.to_numeric(df["sensor_value"], errors="coerce")
    df["meter_num"] = pd.to_numeric(df["meter_value"], errors="coerce")
    df["regex_pair"] = df["sensor_num"].notna() & df["meter_num"].notna()
    log(f"saved pattern output: {len(df):,} reports, {int(df['regex_pair'].sum()):,} pairs")
    return df


def load_texts(keys):
    """Report texts for a set of report ids, read from the big table one block at a time."""
    import pyarrow.parquet as pq
    from extract_regex_v2 import frame_to_reports
    keys = set(str(k) for k in keys)
    pf = pq.ParquetFile(P_PARQUET)
    cols = ["mdr_report_key", "event_type", "product_code", "brand_name", "manufacturer", "date_received",
            "event_text", "mfr_narrative"]
    out = {}
    for g in range(pf.metadata.num_row_groups):
        df = pf.read_row_group(g, columns=cols).to_pandas()
        df = df[df["mdr_report_key"].astype(str).isin(keys)]
        if len(df):
            for r in frame_to_reports(df):
                out[r["mdr_report_key"]] = r
        if len(out) == len(keys):
            break
    return out


def rerun_check(saved, reports):
    """Re-run the current pattern script on a few reports and compare with the saved output."""
    from extract_regex_v2 import extract_v2
    same = diff = 0
    diff_keys = []
    for key, rep in reports.items():
        row = extract_v2(rep)
        a = (row["sensor_value"], row["meter_value"])
        b = (saved[key]["sensor_value"], saved[key]["meter_value"])
        if a == b:
            same += 1
        else:
            diff += 1
            diff_keys.append(key)
    return {"reports_rerun": same + diff, "same_as_saved": same, "different": diff, "different_keys": diff_keys}


# ----------------------------------------------------------------------------
# 1. Against the reference set
# ----------------------------------------------------------------------------
def measure_gold(full):
    gold = pd.read_csv(P_GOLD, dtype=str, keep_default_na=False)
    gold["g_sensor"] = pd.to_numeric(gold["sensor_value_mgdl"], errors="coerce")
    gold["g_meter"] = pd.to_numeric(gold["meter_value_mgdl"], errors="coerce")
    gold["gold_pair"] = gold["g_sensor"].notna() & gold["g_meter"].notna()
    d = gold.merge(full, on="mdr_report_key", how="left", suffixes=("_gold", ""))
    not_in_output = int(d["pattern"].isna().sum())
    d["regex_pair"] = d["regex_pair"].fillna(False).astype(bool)
    from extract_regex import maker_of
    d["maker"] = [maker_of(m, b) for m, b in zip(d["manufacturer"], d["brand_gold"])]
    d["side"] = d["event_type_gold"].map(lambda e: "malfunction-only" if e == "Malfunction" else "death or injury")
    d["sensor_right"] = d["regex_pair"] & (d["sensor_num"] == d["g_sensor"])
    d["meter_right"] = d["regex_pair"] & (d["meter_num"] == d["g_meter"])
    d["both_right"] = d["sensor_right"] & d["meter_right"]
    d["swapped"] = d["regex_pair"] & d["gold_pair"] & (d["sensor_num"] == d["g_meter"]) & (d["meter_num"] == d["g_sensor"])

    def block(x):
        n = int(x["regex_pair"].sum())
        g = int(x["gold_pair"].sum())
        found = int((x["gold_pair"] & x["regex_pair"]).sum())
        return {"reference_reports": int(len(x)),
                "reference_pairs": g,
                "pattern_pairs": n,
                "pattern_pairs_where_reference_has_a_pair": found,
                "pattern_pairs_where_reference_has_no_pair": n - found,
                "sensor_value_right": share(int(x["sensor_right"].sum()), n),
                "meter_value_right": share(int(x["meter_right"].sum()), n),
                "both_right": share(int(x["both_right"].sum()), n),
                "swapped": int(x["swapped"].sum()),
                "reference_pairs_missed_by_patterns": share(g - found, g),
                "reference_pairs_found_and_both_right": share(int((x["gold_pair"] & x["both_right"]).sum()), g)}

    out = {"all": block(d), "by_side": {s: block(d[d["side"] == s]) for s in ("malfunction-only", "death or injury")},
           "by_maker": {m: block(d[d["maker"] == m]) for m in ("Abbott", "Dexcom", "Medtronic")},
           "reference_reports_not_in_saved_output": not_in_output}
    wrong = d[d["regex_pair"] & ~d["both_right"]]
    out["pattern_pairs_not_both_right"] = [
        {"mdr_report_key": r.mdr_report_key, "maker": r.maker, "event_type": r.event_type_gold, "pattern": r.pattern,
         "pattern_sensor": r.sensor_value, "pattern_meter": r.meter_value,
         "reference_sensor": r.sensor_value_mgdl, "reference_meter": r.meter_value_mgdl, "reference_notes": r.notes[:140]}
        for r in wrong.itertuples()]
    missed = d[d["gold_pair"] & ~d["regex_pair"]]
    out["reference_pairs_missed"] = [
        {"mdr_report_key": r.mdr_report_key, "maker": r.maker, "event_type": r.event_type_gold,
         "reference_sensor": r.sensor_value_mgdl, "reference_meter": r.meter_value_mgdl, "reference_notes": r.notes[:140]}
        for r in missed.itertuples()]
    return out, d


# ----------------------------------------------------------------------------
# 2. Against the language model (run set)
# ----------------------------------------------------------------------------
def measure_model(full):
    from extract_regex_v2 import load_model_reference
    ref = load_model_reference(str(P_MODEL))
    d = ref.merge(full, on="mdr_report_key", how="left")
    not_in_output = int(d["pattern"].isna().sum())
    d["regex_pair"] = d["regex_pair"].fillna(False).astype(bool)
    d["model_pair"] = (d["m_sensor"].notna() & d["m_meter"].notna()
                       & d["m_sensor"].between(*SENSOR_RANGE) & d["m_meter"].between(*METER_RANGE))
    both = d["model_pair"] & d["regex_pair"]
    d["exact"] = both & (d["sensor_num"] == d["m_sensor"]) & (d["meter_num"] == d["m_meter"])
    d["within5"] = both & ((d["sensor_num"] - d["m_sensor"]).abs() <= 5) & ((d["meter_num"] - d["m_meter"]).abs() <= 5)
    d["swapped"] = both & (d["sensor_num"] == d["m_meter"]) & (d["meter_num"] == d["m_sensor"]) & ~d["exact"]
    d["sensor_same"] = both & (d["sensor_num"] == d["m_sensor"])
    d["meter_same"] = both & (d["meter_num"] == d["m_meter"])
    d["brand_cmp"] = d["brand"].where(d["brand"].isin(["Abbott", "Dexcom", "Medtronic"]), "Other")
    d["side"] = d["event_group"].fillna("").map(event_side)
    # does the text list several pairs? (the patterns then take the first one; the model often takes another one)
    d["lists"] = d["value_flags"].fillna("").str.contains("multiple_pairs|list").map(
        {True: "text lists several pairs", False: "text holds one pair"})

    def block(x):
        b = x["model_pair"] & x["regex_pair"]
        nb, nm, nr = int(b.sum()), int(x["model_pair"].sum()), int(x["regex_pair"].sum())
        return {"reports": int(len(x)), "model_pairs": nm, "pattern_pairs": nr, "both_output_a_pair": nb,
                "agree_on_both_values": share(int(x["exact"].sum()), nb),
                "agree_within_5_mgdl": share(int(x["within5"].sum()), nb),
                "sensor_value_same": share(int(x["sensor_same"].sum()), nb),
                "meter_value_same": share(int(x["meter_same"].sum()), nb),
                "swapped": share(int(x["swapped"].sum()), nb),
                "pattern_pairs_the_model_did_not_output": share(nr - nb, nr),
                "model_pairs_the_patterns_also_output_recall": share(nb, nm)}

    out = {"all": block(d),
           "by_maker": {m: block(d[d["brand_cmp"] == m]) for m in STRATA},
           "by_side": {s: block(d[d["side"] == s]) for s in ("malfunction-only", "death or injury")},
           "by_pattern": {p: block(x) for p, x in d[d["regex_pair"]].groupby("pattern")},
           "by_one_pair_or_several": {k: block(x) for k, x in d[d["regex_pair"]].groupby("lists")},
           "malfunction_only_by_one_pair_or_several": {
               k: block(x) for k, x in d[d["regex_pair"] & (d["side"] == "malfunction-only")].groupby("lists")},
           "run_set_reports_not_in_saved_output": not_in_output,
           "memo_values_REGEX_V2_FULL_CORPUS": {"model_pairs": 18436, "pattern_pairs": 17426, "both_output_a_pair": 16426,
                                                "agree_on_both_values_pct": 88.4, "agree_within_5_mgdl_pct": 89.5,
                                                "swapped_pct": 0.2, "recall_pct": 89.1, "pattern_only_pairs": 1000}}
    a, m = out["all"], out["memo_values_REGEX_V2_FULL_CORPUS"]
    out["matches_memo"] = {
        "both_output_a_pair": a["both_output_a_pair"] == m["both_output_a_pair"],
        "agree_on_both_values_pct": a["agree_on_both_values"]["pct"] == m["agree_on_both_values_pct"],
        "agree_within_5_mgdl_pct": a["agree_within_5_mgdl"]["pct"] == m["agree_within_5_mgdl_pct"],
        "pattern_pairs": a["pattern_pairs"] == m["pattern_pairs"],
        "model_pairs": a["model_pairs"] == m["model_pairs"]}
    # the table the tuning step saved (read only), as a second thing to compare with
    p_tab = FDA / "results" / "text" / "tables" / "h_regex_v2_recall_by_brand.csv"
    if p_tab.exists():
        tab = pd.read_csv(p_tab)
        r = tab[(tab["version"] == "v2 tuned") & (tab["brand"] == "All")].iloc[0]
        out["saved_table_h_regex_v2_recall_by_brand"] = {
            "pattern_pairs": int(r["regex_pairs"]), "both_output_a_pair": int(r["both"]),
            "agree_on_both_values_pct": float(r["agree_exact_pct"]), "agree_within_5_mgdl_pct": float(r["agree_within5_pct"]),
            "pattern_only_pairs": int(r["regex_only_pairs"])}
        out["matches_saved_table"] = {
            "pattern_pairs": a["pattern_pairs"] == int(r["regex_pairs"]),
            "both_output_a_pair": a["both_output_a_pair"] == int(r["both"]),
            "agree_on_both_values_pct": a["agree_on_both_values"]["pct"] == float(r["agree_exact_pct"]),
            "agree_within_5_mgdl_pct": a["agree_within_5_mgdl"]["pct"] == float(r["agree_within5_pct"]),
            "pattern_only_pairs": a["pattern_pairs_the_model_did_not_output"]["count"] == int(r["regex_only_pairs"])}
    return out


# ----------------------------------------------------------------------------
# 3. The sample of 100 malfunction-only pairs
# ----------------------------------------------------------------------------
def draw_sample(full):
    """Seeded draw of N_SAMPLE malfunction-only pairs, spread over makers in proportion to their share."""
    frame = full[full["regex_pair"] & (full["event_group"] == "malfunction")].copy()
    frame["maker"] = frame["brand"].map(stratum_of)
    sizes = {m: int((frame["maker"] == m).sum()) for m in STRATA}
    total = sum(sizes.values())
    exact = {m: N_SAMPLE * sizes[m] / total for m in STRATA}
    alloc = {m: int(math.floor(exact[m])) for m in STRATA}
    left = N_SAMPLE - sum(alloc.values())
    for m in sorted(STRATA, key=lambda m: (-(exact[m] - alloc[m]), STRATA.index(m)))[:left]:   # largest remainders
        alloc[m] += 1
    rng = random.Random(SEED)
    picked = []
    for m in STRATA:
        keys = sorted(frame.loc[frame["maker"] == m, "mdr_report_key"].tolist(), key=lambda k: (len(k), k))
        picked += rng.sample(keys, alloc[m])
    smp = frame[frame["mdr_report_key"].isin(set(picked))].set_index("mdr_report_key").loc[picked].reset_index()
    info = {"seed": SEED, "frame": "malfunction-only reports where the saved pattern output holds a pair",
            "frame_pairs": total, "frame_pairs_by_maker": sizes,
            "frame_share_pct_by_maker": {m: round(100 * sizes[m] / total, 2) for m in STRATA},
            "sample_size": N_SAMPLE, "sample_by_maker": alloc,
            "frame_pairs_by_pattern": {k: int(v) for k, v in frame["pattern"].value_counts().items()}}
    return smp, info


def read_sample_csv():
    if not P_SAMPLE.exists():
        return {}
    with open(P_SAMPLE, encoding="utf-8", newline="") as f:
        return {r["mdr_report_key"]: r for r in csv.DictReader(f)}


def write_sample_csv(smp, verdicts):
    with open(P_SAMPLE, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(SAMPLE_COLUMNS)
        for r in smp.itertuples():
            v = verdicts.get(r.mdr_report_key, {})
            w.writerow([r.mdr_report_key, r.maker, r.sensor_value, r.meter_value, v.get("verdict", ""), v.get("reason", "")])


def cmd_sample(a):
    full = load_full_output()
    smp, info = draw_sample(full)
    old = read_sample_csv()
    write_sample_csv(smp, old)
    kept = sum(1 for k in smp["mdr_report_key"] if old.get(k, {}).get("verdict"))
    log(f"sample: {info['sample_by_maker']} from {info['frame_pairs']:,} pairs; verdicts kept {kept}; wrote {P_SAMPLE}")


def compact_text(text):
    """Shorter print of one report text, for reading.
    - The description of the event (D5) is kept in full; a part that is repeated word for word is printed once.
    - In the maker's narrative (H10) only sentences that hold a digit are kept. The rest is stock wording.
    Every sentence that holds a number is therefore still printed."""
    import re
    t = " ".join((text or "").split())
    d5, _, h10 = t.partition("[H10 MANUFACTURER NARRATIVE]")
    seen, parts = set(), []
    for seg in d5.split(" | "):
        k = seg.strip().upper()
        if k and k not in seen:
            seen.add(k)
            parts.append(seg.strip())
    out = " | ".join(parts)
    if h10.strip():
        sents = re.split(r"(?<=[.;])\s+|\s\|\s", h10.strip())
        keep, seen_h = [], set()
        for s in sents:
            k = s.strip().upper()
            if re.search(r"\d", re.sub(r"\(B\)\(\d\)", "", k)) and k not in seen_h:
                seen_h.add(k)
                keep.append(s.strip())
        out += f" [H10: {len(sents)} sentences, {len(keep)} with numbers] " + " ".join(keep)
    return out


def cmd_texts(a):
    """Print one batch of sampled report texts to the screen, for reading. Nothing is written to disk."""
    full = load_full_output()
    smp, _ = draw_sample(full)
    lo = (a.batch - 1) * a.size
    part = smp.iloc[lo:lo + a.size]
    texts = load_texts(part["mdr_report_key"])
    for i, r in enumerate(part.itertuples(), lo + 1):
        t = texts[r.mdr_report_key]["text"] or ""
        t = " ".join(t.split()) if a.full_text else compact_text(t)
        if a.max_chars and len(t) > a.max_chars:
            t = t[:a.max_chars] + f" ...[cut, {len(t)} chars in all]"
        print(f"\n=== #{i} key {r.mdr_report_key} | {r.maker} | pattern {r.pattern} | flags {r.value_flags or '-'} | "
              f"SENSOR {r.sensor_value} METER {r.meter_value}")
        print(t.encode("ascii", "replace").decode("ascii"))


def cmd_judge(a):
    """Merge a verdict file (columns: mdr_report_key, verdict, reason) into the sample CSV."""
    full = load_full_output()
    smp, _ = draw_sample(full)
    verdicts = read_sample_csv()
    with open(a.verdicts, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            k = r["mdr_report_key"].strip()
            if k not in set(smp["mdr_report_key"]):
                raise SystemExit(f"verdict for a report that is not in the sample: {k}")
            if r["verdict"].strip() not in VERDICTS:
                raise SystemExit(f"unknown verdict for {k}: {r['verdict']!r}")
            if len(r["reason"].split()) > 12:
                raise SystemExit(f"reason longer than 12 words for {k}: {r['reason']!r}")
            verdicts[k] = {"verdict": r["verdict"].strip(), "reason": r["reason"].strip()}
    write_sample_csv(smp, verdicts)
    done = sum(1 for k in smp["mdr_report_key"] if verdicts.get(k, {}).get("verdict"))
    log(f"verdicts in the sample file: {done} of {len(smp)}")


def reference_name(text):
    """What the Abbott template calls the device that gave the reference value ("... OBTAINED ON A METER")."""
    import re
    t = " ".join((text or "").upper().split())
    m = re.search(r"OBTAINED\s+ON\s+(?:AN?\s+|THE\s+)?(.{1,40}?)(?:,|\s+AND\s+THE\s+RESULTS|\s+WHEN\s+PLOTTED)", t)
    if not m:
        return "prose (no template slot)"
    p = m.group(1)
    if "COMPARISON DEVICE" in p:
        return "the comparison device (kind not named)"
    if "UNKNOWN" in p:
        return "unknown device"
    if "METER" in p or "PRECISION" in p:
        return "a meter (meter, HCP meter, Abbott meter, reader's built-in meter)"
    return "other wording: " + p.strip().lower()


def measure_sample(full):
    smp, info = draw_sample(full)
    rows = read_sample_csv()
    if set(rows) != set(smp["mdr_report_key"]):
        raise SystemExit("the sample CSV does not hold the seeded draw; run the 'sample' command first")
    smp["verdict"] = [rows[k]["verdict"] for k in smp["mdr_report_key"]]
    for k, v in zip(smp["mdr_report_key"], smp["verdict"]):
        if v not in VERDICTS:
            raise SystemExit(f"report {k} has no valid verdict yet: {v!r}")
        if (rows[k]["sensor_value_mgdl"], rows[k]["meter_value_mgdl"]) != tuple(
                smp.loc[smp["mdr_report_key"] == k, ["sensor_value", "meter_value"]].iloc[0]):
            raise SystemExit(f"report {k}: values in the sample CSV differ from the saved pattern output")
    smp["right"] = smp["verdict"] == "right"
    smp["false_low_call"] = (smp["sensor_num"] < 70) & (smp["meter_num"] >= 70)
    smp["same_sentence"] = ~smp["pattern"].isin(["v1_prose_adjacent_sentence", "v2_adjacent_sentence", "v2_text_unique"])
    n = len(smp)
    decided = smp[smp["verdict"] != "unclear"]
    out = dict(info)
    out["reader"] = "AI reader (Claude), not a person. One reader, one pass."
    out["verdict_counts"] = {v: int((smp["verdict"] == v).sum()) for v in VERDICTS}
    out["precision_right_of_all"] = share(int(smp["right"].sum()), n)
    out["precision_right_of_decided_unclear_left_out"] = share(int(decided["right"].sum()), len(decided))
    fl = smp[smp["false_low_call"]]
    out["false_low_calls_sensor_under_70_meter_70_or_more"] = {
        "right": share(int(fl["right"].sum()), len(fl)),
        "verdict_counts": {v: int((fl["verdict"] == v).sum()) for v in VERDICTS}}
    out["by_maker"] = {m: {"right": share(int(x["right"].sum()), len(x)),
                           "verdict_counts": {v: int((x["verdict"] == v).sum()) for v in VERDICTS if (x["verdict"] == v).any()}}
                       for m, x in smp.groupby("maker")}
    out["by_pattern"] = {p: {"right": share(int(x["right"].sum()), len(x)),
                             "verdict_counts": {v: int((x["verdict"] == v).sum()) for v in VERDICTS if (x["verdict"] == v).any()}}
                         for p, x in smp.groupby("pattern")}
    tpl = smp["pattern"] == "abbott_template"
    out["abbott_template_pairs"] = share(int((tpl & smp["right"]).sum()), int(tpl.sum()))
    out["all_other_patterns_pairs"] = share(int((~tpl & smp["right"]).sum()), int((~tpl).sum()))
    lists = smp["value_flags"].str.contains("multiple_pairs|list")
    out["text_lists_several_pairs"] = share(int((lists & smp["right"]).sum()), int(lists.sum()))
    out["text_holds_one_pair"] = share(int((~lists & smp["right"]).sum()), int((~lists).sum()))
    out["sample_pairs_from_two_sentence_patterns"] = int((~smp["same_sentence"]).sum())
    two = ["v1_prose_adjacent_sentence", "v2_adjacent_sentence", "v2_text_unique"]
    out["frame_pairs_from_two_sentence_patterns"] = int(sum(info["frame_pairs_by_pattern"].get(p, 0) for p in two))
    return out, smp


# ----------------------------------------------------------------------------
# stats: everything into one JSON
# ----------------------------------------------------------------------------
def cmd_stats(a):
    missing = [str(p) for p in (P_FULL, P_PARQUET, P_MODEL, P_GOLD) if not p.exists()]
    full = load_full_output()
    stats = {"date": time.strftime("%Y-%m-%d"), "script": "fda-maude/scripts/pattern_precision.py",
             "saved_pattern_output": "fda-maude/clean/regex_v2_full.csv.gz",
             "saved_output_reports": int(len(full)), "saved_output_pairs": int(full["regex_pair"].sum()),
             "saved_output_pairs_malfunction_only": int((full["regex_pair"] & (full["event_group"] == "malfunction")).sum()),
             "missing_input_files": missing}
    saved = full.set_index("mdr_report_key")[["sensor_value", "meter_value"]].to_dict("index")

    gold_stats, gold_frame = measure_gold(full)
    gold_texts = load_texts(gold_frame["mdr_report_key"])
    gold_stats["rerun_check"] = rerun_check(saved, gold_texts)
    stats["1_reference_set"] = gold_stats
    log(f"reference set: pattern pairs {gold_stats['all']['pattern_pairs']}, both right {gold_stats['all']['both_right']}")

    stats["2_language_model"] = measure_model(full)
    log(f"model: {stats['2_language_model']['all']}")

    smp_stats, smp = measure_sample(full)
    smp_texts = load_texts(smp["mdr_report_key"])
    smp_stats["rerun_check"] = rerun_check(saved, smp_texts)
    names = collections.Counter(reference_name(smp_texts[k]["text"])
                                for k, p in zip(smp["mdr_report_key"], smp["pattern"]) if p == "abbott_template")
    smp_stats["abbott_template_pairs_by_name_of_reference_device"] = dict(names.most_common())
    # stricter count: right AND the text names the reference as a meter or as blood glucose (not just "comparison device")
    named = [(p != "abbott_template") or reference_name(smp_texts[k]["text"]).startswith("a meter")
             for k, p in zip(smp["mdr_report_key"], smp["pattern"])]
    smp_stats["right_and_reference_named_as_meter_or_blood_glucose"] = share(
        int((smp["right"] & pd.Series(named, index=smp.index)).sum()), len(smp))
    stats["3_direct_read_malfunction_only"] = smp_stats
    log(f"sample: {smp_stats['verdict_counts']}, precision {smp_stats['precision_right_of_all']}")

    P_STATS.write_text(json.dumps(stats, indent=1), encoding="utf-8")
    log(f"wrote {P_STATS}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["sample", "texts", "judge", "stats"])
    ap.add_argument("--batch", type=int, default=1, help="texts: which batch to print (1 = the first)")
    ap.add_argument("--size", type=int, default=10, help="texts: reports per batch")
    ap.add_argument("--max-chars", type=int, default=6000, help="texts: cut each printed text after this many characters (0 = no cut)")
    ap.add_argument("--full-text", action="store_true", help="texts: print every sentence (default: the short print, see compact_text)")
    ap.add_argument("--verdicts", default=None, help="judge: CSV with columns mdr_report_key, verdict, reason")
    a = ap.parse_args(argv)
    {"sample": cmd_sample, "texts": cmd_texts, "judge": cmd_judge, "stats": cmd_stats}[a.command](a)


if __name__ == "__main__":
    main()
