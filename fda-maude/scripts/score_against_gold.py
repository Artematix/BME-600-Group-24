#!/usr/bin/env python
"""
score_against_gold.py : scores the text layers against the hand-labelled gold set (Phase 1, BMEN 600 Group 24).

What it does
- Joins three tables by mdr_report_key: the gold labels (gold/gold_labels_v1.csv), the regex output
  (extract_regex.py CSV) and the model output (llm_extract.py JSONL).
- Scores three systems:
    regex    = the pattern layer alone (numbers, zone, wear day, multiple_pairs only)
    llm      = the model alone
    combined = regex value when the Abbott template matched (or any regex pair, see --combine-rule),
               else the model value. Zone and wear day: regex when found, else model.
- Categorical fields (fault_type, user_action, outcome_severity, fingerstick_check_done, multiple_pairs):
  accuracy and Cohen's kappa, overall and per maker (Abbott / Dexcom / Medtronic).
- Number fields (sensor_value_mgdl, meter_value_mgdl, wear_day, parkes_zone_stated): exact-match rate
  among gold-present values and among system-present values, plus precision / recall of "value present".
- Confusion tables for fault_type and outcome_severity.
- Optional: a second model run (--llm2) gives run-to-run reproducibility; an earlier metrics JSON
  (--compare) gives a version-vs-version table.
- Writes a markdown report, a metrics JSON (for later comparison) and an error list CSV.

Usage
  python fda-maude/scripts/score_against_gold.py --gold fda-maude/gold/gold_labels_v1.csv
      --regex fda-maude/results/text/regex_sample.csv --llm fda-maude/results/text/llm_sample_p8.jsonl
      --version v1 --out fda-maude/results/text/validation_v1.md
      [--llm2 second_run.jsonl] [--compare fda-maude/results/text/validation_v1_metrics.json]
      [--combine-rule template|anypair]
"""

import argparse
import collections
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract_regex import maker_of  # noqa: E402

CAT_FIELDS = ["fault_type", "outcome_severity", "user_action", "fingerstick_check_done", "multiple_pairs"]
NUM_FIELDS = ["sensor_value_mgdl", "meter_value_mgdl", "wear_day", "parkes_zone_stated"]
REGEX_FIELDS = ["sensor_value_mgdl", "meter_value_mgdl", "wear_day", "parkes_zone_stated", "multiple_pairs"]
ALL_FIELDS = CAT_FIELDS + NUM_FIELDS
MAKERS = ["Abbott", "Dexcom", "Medtronic"]
FAULT_ORDER = ["reads_low", "reads_high", "erratic", "stuck", "signal_loss", "sensor_error_or_early_end",
               "adhesive_or_detachment", "insertion_or_skin_injury", "other_device", "unclear"]
OUTCOME_ORDER = ["none", "symptoms_only", "hypoglycemia", "hyperglycemia_or_dka", "hospital_or_er", "death", "not_stated"]
SHORT = {"reads_low": "low", "reads_high": "high", "erratic": "errat", "stuck": "stuck", "signal_loss": "signal",
         "sensor_error_or_early_end": "error", "adhesive_or_detachment": "adhes", "insertion_or_skin_injury": "skin",
         "other_device": "other", "unclear": "uncl", "none": "none", "symptoms_only": "sympt", "hypoglycemia": "hypo",
         "hyperglycemia_or_dka": "hyper", "hospital_or_er": "hosp", "death": "death", "not_stated": "n/s"}
TARGETS = {"fault_type": 0.70, "outcome_severity": 0.75, "numbers_exact": 0.95}


# ----------------------------------------------------------------------------
# Loading and normalising
# ----------------------------------------------------------------------------
def norm_num(v):
    """'' / None / NaN -> None, else float. '80' -> 80.0."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    if s == "" or s.lower() in ("nan", "none", "null"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def norm_zone(v):
    """'' / None -> None, else the upper-case letter."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip().upper()
    return s if s in ("A", "B", "C", "D", "E") else None


def norm_cat(v):
    """Categorical value as a string, or None when empty."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip()
    return s if s else None


def normalise_row(d):
    """Apply the right normaliser to every scored field of one row dict."""
    out = {}
    for f in CAT_FIELDS:
        out[f] = norm_cat(d.get(f))
    for f in ("sensor_value_mgdl", "meter_value_mgdl", "wear_day"):
        out[f] = norm_num(d.get(f))
    out["parkes_zone_stated"] = norm_zone(d.get("parkes_zone_stated"))
    return out


def load_gold(path):
    """Gold CSV -> dict key -> row (normalised fields + maker, event_type, evidence, notes)."""
    g = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = {}
    for _, r in g.iterrows():
        row = normalise_row(r.to_dict())
        row["maker"] = maker_of(r.get("manufacturer", ""), r.get("brand", ""))
        row["event_type"] = r.get("event_type", "")
        row["evidence"] = r.get("evidence", "")
        row["notes"] = r.get("notes", "")
        row["confidence"] = r.get("confidence", "")
        rows[str(r["mdr_report_key"])] = row
    return rows


def load_regex(path):
    """extract_regex.py CSV -> dict key -> normalised fields + regex_template, pair_found."""
    rows = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            row = normalise_row(r)
            row["regex_template"] = r.get("regex_template", "none")
            row["pair_found"] = r.get("pair_found", "no")
            rows[str(r["mdr_report_key"])] = row
    return rows


def load_llm(path):
    """llm_extract.py JSONL -> dict key -> normalised fields (from the `llm` form) + meta."""
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            form = r.get("llm") or {}
            row = normalise_row(form)
            row["error"] = r.get("error", "")
            row["guard_dropped"] = r.get("guard_dropped", [])
            row["prompt_version"] = r.get("prompt_version", "")
            row["run_tag"] = r.get("run_tag", "")
            rows[str(r["mdr_report_key"])] = row
    return rows


def combine(rx, llm, rule):
    """Combined rule. Numbers from the regex when its template matched, else from the model.
    Zone and wear day: regex when it found one, else the model. Judgement fields: the model."""
    out = {f: llm.get(f) for f in ALL_FIELDS}
    if rule == "template":
        use_regex = rx.get("regex_template") == "abbott_template"
    else:  # anypair
        use_regex = rx.get("pair_found") == "yes" or rx.get("regex_template") == "abbott_template"
    if use_regex:
        for f in ("sensor_value_mgdl", "meter_value_mgdl", "multiple_pairs"):
            out[f] = rx.get(f)
    for f in ("parkes_zone_stated", "wear_day"):
        out[f] = rx.get(f) if rx.get(f) is not None else llm.get(f)
    return out


# ----------------------------------------------------------------------------
# Metrics
# ----------------------------------------------------------------------------
def same(a, b):
    """Equality that treats None == None as a match and compares numbers as floats."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, float) or isinstance(b, float):
        try:
            return float(a) == float(b)
        except (TypeError, ValueError):
            return False
    return str(a) == str(b)


def cat_metrics(gold_vals, sys_vals):
    """Accuracy and Cohen's kappa for two lists of labels (None becomes 'missing')."""
    g = ["missing" if v is None else str(v) for v in gold_vals]
    s = ["missing" if v is None else str(v) for v in sys_vals]
    n = len(g)
    if n == 0:
        return {"n": 0, "accuracy": None, "kappa": None}
    acc = sum(1 for a, b in zip(g, s) if a == b) / n
    labels = sorted(set(g) | set(s))
    if len(labels) < 2:
        kappa = None  # undefined: only one label in both lists
    else:
        with np.errstate(all="ignore"):
            k = cohen_kappa_score(g, s)
        kappa = None if (k is None or (isinstance(k, float) and math.isnan(k))) else float(k)
    return {"n": n, "accuracy": acc, "kappa": kappa}


def num_metrics(gold_vals, sys_vals):
    """Exact-match and presence metrics for one number field."""
    n = len(gold_vals)
    G = sum(1 for v in gold_vals if v is not None)
    S = sum(1 for v in sys_vals if v is not None)
    B = sum(1 for g, s in zip(gold_vals, sys_vals) if g is not None and s is not None)
    E = sum(1 for g, s in zip(gold_vals, sys_vals) if g is not None and s is not None and same(g, s))
    both_null = sum(1 for g, s in zip(gold_vals, sys_vals) if g is None and s is None)
    wrong_value = B - E           # both present, different value
    invented = S - B              # system gives a value, gold has none
    missed = G - B                # gold has a value, system gives none
    return {"n": n, "gold_present": G, "sys_present": S, "both_present": B, "exact": E,
            "exact_among_gold": (E / G) if G else None, "exact_among_sys": (E / S) if S else None,
            "presence_precision": (B / S) if S else None, "presence_recall": (B / G) if G else None,
            "row_agreement": (E + both_null) / n if n else None,
            "wrong_value": wrong_value, "invented": invented, "missed": missed}


def score_system(gold, system, keys, fields):
    """All metrics for one system, overall and per maker. Returns nested dict."""
    out = {}
    groups = {"All": keys}
    for m in MAKERS:
        groups[m] = [k for k in keys if gold[k]["maker"] == m]
    for gname, ks in groups.items():
        out[gname] = {}
        for f in fields:
            gv = [gold[k][f] for k in ks]
            sv = [system.get(k, {}).get(f) for k in ks]
            if f in CAT_FIELDS:
                out[gname][f] = cat_metrics(gv, sv)
            else:
                out[gname][f] = num_metrics(gv, sv)
    return out


def confusion(gold, system, keys, field, order):
    """Confusion table as a DataFrame: gold rows x system columns."""
    labels = [l for l in order if any(gold[k][field] == l for k in keys) or any(system.get(k, {}).get(field) == l for k in keys)]
    extra = sorted({gold[k][field] for k in keys} | {system.get(k, {}).get(field) for k in keys})
    labels += [l for l in extra if l not in labels and l is not None]
    tab = pd.DataFrame(0, index=labels, columns=labels + ["missing"])
    for k in keys:
        g = gold[k][field]
        s = system.get(k, {}).get(field)
        tab.loc[g, s if s is not None else "missing"] += 1
    tab = tab.loc[:, (tab != 0).any(axis=0)]
    return tab


def reproducibility(run1, run2, keys):
    """Share of identical answers per field and share of fully identical forms between two runs."""
    out = {}
    for f in ALL_FIELDS:
        out[f] = sum(1 for k in keys if same(run1.get(k, {}).get(f), run2.get(k, {}).get(f))) / len(keys)
    out["all_fields_identical"] = sum(1 for k in keys if all(same(run1.get(k, {}).get(f), run2.get(k, {}).get(f)) for f in ALL_FIELDS)) / len(keys)
    return out


# ----------------------------------------------------------------------------
# Markdown helpers
# ----------------------------------------------------------------------------
def pct(x, digits=0):
    return "-" if x is None else f"{100 * x:.{digits}f}%"


def kap(x):
    return "-" if x is None else f"{x:.2f}"


def md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines) + "\n"


def cat_table(metrics, systems, field):
    """One categorical field: rows = groups, columns = system accuracy / kappa."""
    header = ["Group", "n"] + [f"{s} accuracy" for s in systems] + [f"{s} kappa" for s in systems]
    rows = []
    for g in ["All"] + MAKERS:
        n = metrics[systems[0]][g][field]["n"]
        rows.append([g, n] + [pct(metrics[s][g][field]["accuracy"]) for s in systems] + [kap(metrics[s][g][field]["kappa"]) for s in systems])
    return md_table(header, rows)


def num_table(metrics, systems, field):
    """One number field: rows = system x group."""
    header = ["System", "Group", "gold has value", "system has value", "exact", "exact among gold values",
              "exact among system values", "presence precision", "presence recall", "wrong value", "invented", "missed"]
    rows = []
    for s in systems:
        for g in ["All"] + MAKERS:
            m = metrics[s][g][field]
            rows.append([s, g, m["gold_present"], m["sys_present"], m["exact"], pct(m["exact_among_gold"]),
                         pct(m["exact_among_sys"]), pct(m["presence_precision"]), pct(m["presence_recall"]),
                         m["wrong_value"], m["invented"], m["missed"]])
    return md_table(header, rows)


def confusion_md(tab, title):
    cols = [SHORT.get(c, c) for c in tab.columns]
    header = [title + " (gold down, system across)"] + cols
    rows = [[SHORT.get(idx, idx)] + [int(v) for v in tab.loc[idx]] for idx in tab.index]
    return md_table(header, rows)


def pooled_numbers(metrics, system, group="All"):
    """Pool the four number fields: exact among system-present values (the 95 % target)."""
    E = sum(metrics[system][group][f]["exact"] for f in NUM_FIELDS)
    S = sum(metrics[system][group][f]["sys_present"] for f in NUM_FIELDS)
    G = sum(metrics[system][group][f]["gold_present"] for f in NUM_FIELDS)
    return {"exact": E, "sys_present": S, "gold_present": G,
            "exact_among_sys": (E / S) if S else None, "exact_among_gold": (E / G) if G else None}


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Score regex, model and combined outputs against the gold set.")
    ap.add_argument("--gold", required=True)
    ap.add_argument("--regex", required=True, help="extract_regex.py CSV on the gold reports")
    ap.add_argument("--llm", required=True, help="llm_extract.py JSONL on the gold reports (run 1)")
    ap.add_argument("--llm2", default=None, help="a second run of the same version (reproducibility)")
    ap.add_argument("--version", required=True, help="label for this version, e.g. v1")
    ap.add_argument("--out", required=True, help="markdown report path")
    ap.add_argument("--compare", default=None, help="metrics JSON of an earlier version to compare with")
    ap.add_argument("--combine-rule", default="template", choices=["template", "anypair"])
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    t0 = time.time()
    gold = load_gold(args.gold)
    rx = load_regex(args.regex)
    llm = load_llm(args.llm)
    keys = sorted(k for k in gold if k in rx and k in llm)
    missing = [k for k in gold if k not in keys]
    print(f"gold {len(gold)}, regex {len(rx)}, llm {len(llm)}, joined {len(keys)}, gold rows without output {len(missing)}")
    llm_errors = sum(1 for k in keys if llm[k].get("error"))

    comb = {k: combine(rx[k], llm[k], args.combine_rule) for k in keys}
    comb_alt = {k: combine(rx[k], llm[k], "anypair" if args.combine_rule == "template" else "template") for k in keys}
    systems = {"regex": rx, "llm": llm, "combined": comb}
    metrics = {}
    for name, sysrows in systems.items():
        metrics[name] = score_system(gold, sysrows, keys, ALL_FIELDS)
    metrics["combined_alt"] = score_system(gold, comb_alt, keys, NUM_FIELDS + ["multiple_pairs"])

    llm2 = repro = metrics2 = None
    if args.llm2:
        llm2 = load_llm(args.llm2)
        keys2 = [k for k in keys if k in llm2]
        repro = reproducibility(llm, llm2, keys2)
        metrics2 = {"llm": score_system(gold, llm2, keys2, ALL_FIELDS),
                    "combined": score_system(gold, {k: combine(rx[k], llm2[k], args.combine_rule) for k in keys2}, keys2, ALL_FIELDS)}
        print(f"run 2: {len(keys2)} reports joined; identical forms {repro['all_fields_identical']:.1%}")

    prev = None
    if args.compare:
        prev = json.loads(Path(args.compare).read_text(encoding="utf-8"))

    # ---------------- markdown ----------------
    v = args.version
    title = args.title or f"Validation of text extraction {v} against the gold set"
    L = [f"# {title}", "",
         f"Date: {time.strftime('%Y-%m-%d')}. Gold: `{Path(args.gold).name}` ({len(gold)} reports). "
         f"Regex: `{Path(args.regex).name}`. Model run 1: `{Path(args.llm).name}`"
         + (f". Model run 2: `{Path(args.llm2).name}`" if args.llm2 else "") + ".", "",
         "Words: kappa = Cohen's kappa, agreement corrected for chance (1.00 = perfect, 0 = chance). "
         "Accuracy = share of reports where the system gives the gold label. "
         "\"Exact among system values\" = of the values the system wrote, the share equal to gold. "
         "\"Exact among gold values\" = of the values in the gold, the share the system got right. "
         "Presence precision / recall = how well the system knows WHEN a value exists. "
         "Invented = system wrote a value where the gold has none. Missed = gold has a value, system wrote none.", "",
         "Systems: `regex` = pattern layer alone (only numbers, zone, wear day, multiple_pairs). `llm` = model alone. "
         f"`combined` = regex value when {'the Abbott template matched' if args.combine_rule == 'template' else 'the regex found any pair'}, "
         "else the model; zone and wear day from the regex when it found one, else the model; judgement fields from the model.", "",
         f"Joined reports: {len(keys)}. Model errors (no form): {llm_errors}.", ""]

    # headline
    L += ["## 1. Headline numbers", ""]
    rows = []
    for f in ["fault_type", "outcome_severity", "user_action", "fingerstick_check_done", "multiple_pairs"]:
        tgt = TARGETS.get(f)
        k = metrics["combined"]["All"][f]["kappa"]
        rows.append([f, kap(metrics["llm"]["All"][f]["kappa"]), kap(k), "-" if k is None else f"{k:.3f}",
                     pct(metrics["combined"]["All"][f]["accuracy"]), f"{tgt:.2f}" if tgt else "-",
                     ("met" if round(k or 0, 2) >= tgt else "MISSED") if tgt else "-"])
    L.append(md_table(["Field", "llm kappa", "combined kappa", "exact (3 dp)", "combined accuracy", "target kappa", "status"], rows))
    L.append("Status compares the kappa rounded to 2 decimals with the target, as the target is written (kappa on 287 reports has a sampling error of about 0.03). The exact value is shown next to it.\n")
    rows = []
    for s in ["regex", "llm", "combined"]:
        p = pooled_numbers(metrics, s)
        rows.append([s, p["gold_present"], p["sys_present"], p["exact"], pct(p["exact_among_sys"], 1), pct(p["exact_among_gold"], 1),
                     "met" if (p["exact_among_sys"] or 0) >= TARGETS["numbers_exact"] else "MISSED"])
    L.append("Numbers pooled (sensor value, meter value, wear day, zone). Target: 95 % exact among system values.\n")
    L.append(md_table(["System", "gold values", "system values", "exact", "exact among system values", "exact among gold values", "status"], rows))

    # categorical per field
    L += ["## 2. Judgement fields: accuracy and kappa, per maker", ""]
    for f in CAT_FIELDS:
        syss = ["regex", "llm", "combined"] if f == "multiple_pairs" else ["llm"]
        L += [f"### {f}", "", cat_table(metrics, syss, f)]
        if metrics2:
            m1, m2 = metrics["llm"]["All"][f], metrics2["llm"]["All"][f]
            L.append(f"Run 2 (same version, same settings): accuracy {pct(m2['accuracy'])}, kappa {kap(m2['kappa'])} "
                     f"(run 1: {pct(m1['accuracy'])}, {kap(m1['kappa'])}).\n")

    # numbers per field
    L += ["## 3. Number fields", ""]
    for f in NUM_FIELDS:
        L += [f"### {f}", "", num_table(metrics, ["regex", "llm", "combined"], f)]
    alt = "anypair" if args.combine_rule == "template" else "template"
    rows = []
    for f in NUM_FIELDS + ["multiple_pairs"]:
        a, b = metrics["combined"]["All"][f], metrics["combined_alt"]["All"][f]
        if f == "multiple_pairs":
            rows.append([f, pct(a["accuracy"]), pct(b["accuracy"])])
        else:
            rows.append([f, f"{pct(a['exact_among_sys'])} ({a['exact']}/{a['sys_present']})", f"{pct(b['exact_among_sys'])} ({b['exact']}/{b['sys_present']})"])
    L += [f"Combine rule check (exact among system values; multiple_pairs = accuracy): `{args.combine_rule}` (used) vs `{alt}`.", "",
          md_table(["Field", args.combine_rule, alt], rows)]

    # confusion tables
    L += ["## 4. Confusion tables (model answers)", ""]
    L += ["Rows = gold label. Columns = model label. Short names: low = reads_low, high = reads_high, errat = erratic, "
          "signal = signal_loss, error = sensor_error_or_early_end, adhes = adhesive_or_detachment, skin = insertion_or_skin_injury, "
          "other = other_device, uncl = unclear; sympt = symptoms_only, hypo = hypoglycemia, hyper = hyperglycemia_or_dka, "
          "hosp = hospital_or_er, n/s = not_stated.", ""]
    L += ["### fault_type, all makers", "", confusion_md(confusion(gold, llm, keys, "fault_type", FAULT_ORDER), "fault_type")]
    for m in MAKERS:
        ks = [k for k in keys if gold[k]["maker"] == m]
        L += [f"### fault_type, {m}", "", confusion_md(confusion(gold, llm, ks, "fault_type", FAULT_ORDER), m)]
    L += ["### outcome_severity, all makers", "", confusion_md(confusion(gold, llm, keys, "outcome_severity", OUTCOME_ORDER), "outcome")]
    for m in MAKERS:
        ks = [k for k in keys if gold[k]["maker"] == m]
        L += [f"### outcome_severity, {m}", "", confusion_md(confusion(gold, llm, ks, "outcome_severity", OUTCOME_ORDER), m)]
    L += ["### user_action, all makers", "", confusion_md(confusion(gold, llm, keys, "user_action",
          ["none", "ate_carbs", "took_insulin", "skipped_insulin", "sought_care", "other", "not_stated"]), "action")]

    # reproducibility
    if repro:
        L += ["## 5. Run-to-run reproducibility (same version, two runs, same settings)", ""]
        rows = [[f, pct(repro[f], 1)] for f in ALL_FIELDS] + [["all fields identical", pct(repro["all_fields_identical"], 1)]]
        L.append(md_table(["Field", "identical answers"], rows))
        rows = []
        for f in CAT_FIELDS:
            rows.append([f, kap(metrics["llm"]["All"][f]["kappa"]), kap(metrics2["llm"]["All"][f]["kappa"]),
                         kap(metrics["combined"]["All"][f]["kappa"]), kap(metrics2["combined"]["All"][f]["kappa"])])
        L.append("Kappa against gold in each run:\n")
        L.append(md_table(["Field", "llm run 1", "llm run 2", "combined run 1", "combined run 2"], rows))

    # comparison
    if prev:
        pv = prev.get("version", "earlier")
        L += [f"## 6. {pv} vs {v}", "", "Kappa of the combined system, per field and maker. Numbers: exact among system values (combined).", ""]
        rows = []
        for f in CAT_FIELDS:
            for g in ["All"] + MAKERS:
                a = prev["metrics"]["combined"][g][f]["kappa"]
                b = metrics["combined"][g][f]["kappa"]
                rows.append([f, g, kap(a), kap(b), "-" if (a is None or b is None) else f"{b - a:+.2f}"])
        L.append(md_table(["Field", "Group", f"{pv} kappa", f"{v} kappa", "change"], rows))
        rows = []
        for f in NUM_FIELDS:
            for g in ["All"] + MAKERS:
                a, b = prev["metrics"]["combined"][g][f], metrics["combined"][g][f]
                rows.append([f, g, f"{pct(a['exact_among_sys'])} ({a['exact']}/{a['sys_present']})",
                             f"{pct(b['exact_among_sys'])} ({b['exact']}/{b['sys_present']})",
                             f"{pct(a['exact_among_gold'])}", f"{pct(b['exact_among_gold'])}"])
        L.append(md_table(["Field", "Group", f"{pv} exact among system", f"{v} exact among system", f"{pv} exact among gold", f"{v} exact among gold"], rows))
        if prev.get("reproducibility") and repro:
            rows = [[f, pct(prev["reproducibility"].get(f), 1), pct(repro[f], 1)] for f in ALL_FIELDS + ["all_fields_identical"]]
            L.append(md_table(["Field", f"{pv} identical", f"{v} identical"], rows))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")

    # metrics JSON
    payload = {"version": v, "date": time.strftime("%Y-%m-%d"), "gold": str(args.gold), "regex": str(args.regex),
               "llm": str(args.llm), "llm2": args.llm2, "combine_rule": args.combine_rule, "n_joined": len(keys),
               "metrics": metrics, "metrics_run2": metrics2, "reproducibility": repro,
               "pooled_numbers": {s: pooled_numbers(metrics, s) for s in ("regex", "llm", "combined")}}
    mpath = out.with_name(out.stem + "_metrics.json")
    mpath.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    # error list: every model / combined disagreement with the gold
    epath = out.with_name(out.stem + "_errors.csv")
    with open(epath, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["mdr_report_key", "maker", "event_type", "field", "gold", "regex", "llm", "combined", "gold_confidence", "gold_evidence", "gold_notes"])
        for k in keys:
            for fld in ALL_FIELDS:
                gv, cv, lv = gold[k][fld], comb[k].get(fld), llm[k].get(fld)
                if not same(gv, cv) or not same(gv, lv):
                    w.writerow([k, gold[k]["maker"], gold[k]["event_type"], fld, gv, rx[k].get(fld) if fld in REGEX_FIELDS else "",
                                lv, cv, gold[k]["confidence"], gold[k]["evidence"][:120], gold[k]["notes"][:160]])

    # console summary
    print(f"\n{v}: combined kappa fault_type {kap(metrics['combined']['All']['fault_type']['kappa'])}, "
          f"outcome_severity {kap(metrics['combined']['All']['outcome_severity']['kappa'])}, "
          f"user_action {kap(metrics['combined']['All']['user_action']['kappa'])}; "
          f"numbers exact among system values {pct(pooled_numbers(metrics, 'combined')['exact_among_sys'], 1)}")
    for m in MAKERS:
        print(f"  {m}: fault {kap(metrics['combined'][m]['fault_type']['kappa'])}, outcome {kap(metrics['combined'][m]['outcome_severity']['kappa'])}, "
              f"llm-alone fault {kap(metrics['llm'][m]['fault_type']['kappa'])}")
    print(f"wrote {out}, {mpath}, {epath} in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
