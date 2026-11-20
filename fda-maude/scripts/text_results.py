#!/usr/bin/env python
"""
text_results.py : Phase 1 text results and the join to Phase 2 (BMEN 600 Group 24).

What it does
- Reads the full text-extraction output (clean/text_extract_v3.jsonl; the `final` block of each row is the
  combined answer, `final_source` says whether a value came from the pattern layer or the model).
- Joins the run set (clean/run_set.csv.gz: tier, sampling weight, dates, FDA problem codes), the pattern-layer
  table (clean/regex_run_set.csv) and, when present, the clean serious table and the local sample (for the
  "no text" counts).
- Writes tables (CSV) to results/text/tables/ and figures t1_*.png to t6_*.png to results/text/figures/.
- Everything is split serious reports vs the weighted malfunction sample, and by maker.
  Medtronic is undercounted (most Guardian reports sit under pump codes) and had the weakest validation.

Sections (table prefixes)
  a. coverage            share of reports with each field filled; pattern layer vs model; guard drops; no text
  b. fault types         model fault type vs the FDA problem-code families; agreement with "Low Readings"
  c. error sizes         sensor minus meter (mg/dL and % of meter) for reports that state both values;
                         maker-stated Parkes zone vs the zone computed from the pair
  d. wear day            wear day of the reported failure vs a flat expectation
  e. actions, outcomes   user action, outcome, fingerstick check, by fault type and maker
  e. outcome vs FDA      the model's outcome category against the FDA patient-outcome codes (serious reports)
  f. join to Phase 2     reported error sizes binned to the Phase 2 lookup table (2 % steps, clipped at the
                         table's edges) -> error-weighted expected decision impact. Default table: the extended
                         grid analysis/simulation_v2_lookup_extended.csv (-90..+90 %) when it exists, else the
                         base analysis/simulation_v2_lookup.csv (-40..+40 %). When the table reaches past -40 %,
                         every group also gets a comparison row clipped at -40 % (the old result, a floor).

Usage (from the repo root; Windows: plain `python`)
  python fda-maude/scripts/text_results.py
  python fda-maude/scripts/text_results.py --max-rows 20000      # quick test on a partial file
All paths are arguments; see --help.
"""

import argparse
import collections
import datetime
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

T0 = time.time()


def log(msg):
    """Print a progress line with the seconds since start."""
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
MAKERS = ["Abbott", "Dexcom", "Medtronic", "Other"]
MAKER_LABEL = {"Abbott": "Abbott", "Dexcom": "Dexcom", "Medtronic": "Medtronic (undercounted; weakest validation)",
               "Other": "Other"}
FAULT_TYPES = ["reads_low", "reads_high", "erratic", "stuck", "signal_loss", "sensor_error_or_early_end",
               "adhesive_or_detachment", "insertion_or_skin_injury", "other_device", "unclear"]
USER_ACTIONS = ["none", "ate_carbs", "took_insulin", "skipped_insulin", "sought_care", "other", "not_stated"]
OUTCOMES = ["none", "symptoms_only", "hypoglycemia", "hyperglycemia_or_dka", "hospital_or_er", "death", "not_stated"]
ZONES = list("ABCDE")
RECALL_DATE = "20251124"           # FDA Class I recall of FreeStyle Libre 3 / 3 Plus (reads too low)
SENSOR_RANGE = (20.0, 600.0)       # plausible stated sensor value, mg/dL
METER_RANGE = (20.0, 1500.0)       # plausible stated meter / lab value, mg/dL
SENSOR_LIFE_DAYS = {"Abbott": 14, "Dexcom": 10}   # flat expectation: 1/14 per day (Libre), 1/10 (Dexcom G6/G7)
MAX_WEAR_DAY_SHOWN = 15
TRIAL_PARKES_SET_A = {"A": 83.7, "B": 14.6, "C": 1.4, "D": 0.3, "E": 0.0}   # analysis/ACCURACY_V2.md, Set A
TRIAL_WEAR_DAY_MARD = {"day1": 15.2, "day7": 11.8}                           # analysis/ERROR_DRIVERS.md s5
TIPPING_POINTS = (12.0, 20.0)                                                 # analysis/SIMULATION_V2.md s5
CODE_LOW = "Low Readings"
CODE_INCORRECT = "Incorrect, Inadequate or Imprecise Result or Readings"
CODE_HIGH = "High Readings"
WRONG_FAMILY = "Wrong readings (accuracy)"
JOIN_COLS_LOW = ["skipped_pct", "changed_1_pct", "low70_false_per_day", "high180_missed_pct", "tir_pct", "tbr70_pct", "lbgi"]   # tbr70 added 2026-10-30: past about -60 % the sensor sits below 70 all day, so alert counts fall while time "below 70" goes to 100 %
JOIN_COLS_ALL = JOIN_COLS_LOW + ["low70_missed_pct", "spurious_pct", "high180_false_per_day"]
FLOOR_CLIP = (-40.0, 40.0)         # edges of the original lookup (2026-10-27); kept as the "floor" comparison row
JOIN_REFERENCE_BIAS = (-12, -20, -30, -40, -60, -80)   # reference rows: the plain lookup at a constant bias (plus the table's low edge)
# FDA patient-outcome field: the first code is written out, later ones are single letters ("Hospitalization; O; R")
FDA_OUTCOME_CODES = {"R": "Required Intervention", "H": "Hospitalization", "L": "Life Threatening", "D": "Death",
                     "O": "Other", "S": "Disability", "C": "Congenital Anomaly", "U": "Unknown"}
FDA_OUTCOME_ORDER = ["Required Intervention", "Hospitalization", "Life Threatening", "Death", "Other", "Disability"]

# Chart styling: palette copied from analysis/explore_raw_data.py (dataviz reference palette, light surface)
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#86b6ef", "#2a78d6", "#104281"]
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
MAKER_COLORS = {"Abbott": C_BLUE, "Dexcom": C_ORANGE, "Medtronic": C_AQUA, "Other": MUTED}
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 10, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.labelsize": 9.5,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 2, "savefig.dpi": 200, "savefig.bbox": "tight",
})

# Parkes (consensus) error grid, type 1 diabetes version. Copied from analysis/explore_raw_data.py.
# Zone boundaries are the polylines of Pfutzner et al. 2013 (J Diabetes Sci Technol 7:1275), (reference, CGM) mg/dL.
PARKES_T1 = {
    "upper": {
        "B": ([0, 30, 140, 280, 430], [50, 50, 170, 380, 550]),
        "C": ([0, 30, 50, 70, 260], [60, 60, 80, 110, 550]),
        "D": ([0, 25, 50, 80, 125], [100, 100, 125, 215, 550]),
        "E": ([0, 35, 50], [150, 155, 550]),
    },
    "lower": {
        "B": ([50, 170, 385, 550], [30, 145, 300, 450]),
        "C": ([120, 260, 550], [30, 130, 250]),
        "D": ([250, 550], [40, 150]),
    },
}


def parkes_zone_labels(ref, cgm):
    """Parkes consensus error grid zone (A-E) for each (reference, CGM) pair in mg/dL."""
    ref = np.asarray(ref, float)
    cgm = np.asarray(cgm, float)
    z = np.full(len(ref), "A", dtype="<U1")
    for zone in "BCDE":
        xs, ys = PARKES_T1["upper"][zone]
        z[cgm > np.interp(ref, xs, ys, right=np.inf)] = zone
    for zone in "BCD":
        xs, ys = PARKES_T1["lower"][zone]
        z[cgm < np.interp(ref, xs, ys, left=-np.inf)] = zone
    return z


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def wquantile(values, weights, q):
    """Weighted quantile (q in 0-1). Weights of 1 give the usual quantile."""
    v = np.asarray(values, float)
    w = np.asarray(weights, float)
    if len(v) == 0:
        return np.nan
    idx = np.argsort(v)
    v, w = v[idx], w[idx]
    cw = (np.cumsum(w) - 0.5 * w) / w.sum()
    return float(np.interp(q, cw, v))


def wshare(mask, weights):
    """Weighted share (%) of rows where mask is True."""
    w = np.asarray(weights, float)
    if w.sum() == 0:
        return np.nan
    return float(100.0 * w[np.asarray(mask, bool)].sum() / w.sum())


def weights_of(sub):
    """Sampling weights of a frame: the `weight` column for sample rows, 1 for serious rows."""
    return sub["weight"].to_numpy(float)


def pct_table(sub, col, categories, weights):
    """Weighted distribution (%) of a category column over the given category list."""
    w = np.asarray(weights, float)
    tot = w.sum()
    out = {}
    for c in categories:
        out[c] = float(100.0 * w[(sub[col] == c).to_numpy()].sum() / tot) if tot else np.nan
    return out


def to_markdown(df, floatfmt="{:.1f}"):
    """Simple markdown table (no tabulate dependency)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append("" if np.isnan(v) else (f"{v:,.0f}" if abs(v) >= 1000 and float(v).is_integer() else floatfmt.format(v)))
            elif isinstance(v, (int, np.integer)):
                cells.append(f"{v:,}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def load_jsonl(path, max_rows=None):
    """Read the extraction output into a flat table (one row per report). Skips raw answers and bad lines."""
    recs = []
    bad = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_rows and i >= max_rows:
                break
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                bad += 1
                continue
            fin = r.get("final") or {}
            src = r.get("final_source") or {}
            llm = r.get("llm") or {}
            rx = r.get("regex") or {}
            recs.append({
                "mdr_report_key": str(r["mdr_report_key"]), "maker": r.get("maker"), "event_type": r.get("event_type"),
                "split": r.get("split"), "model_error": bool(r.get("error")), "latency_s": r.get("latency_s"),
                "attempts": r.get("attempts"), "guard_dropped": ";".join(r.get("guard_dropped") or []),
                "mmol_converted": ";".join(r.get("mmol_converted") or []),
                "fault_type": fin.get("fault_type"), "sensor": fin.get("sensor_value_mgdl"), "meter": fin.get("meter_value_mgdl"),
                "multiple_pairs": fin.get("multiple_pairs"), "zone_stated": fin.get("parkes_zone_stated"),
                "wear_day": fin.get("wear_day"), "fingerstick": fin.get("fingerstick_check_done"),
                "user_action": fin.get("user_action"), "outcome": fin.get("outcome_severity"), "confidence": fin.get("confidence"),
                "src_sensor": src.get("sensor_value_mgdl"), "src_meter": src.get("meter_value_mgdl"),
                "src_zone": src.get("parkes_zone_stated"), "src_wear": src.get("wear_day"),
                "llm_fault_type": llm.get("fault_type"), "llm_zone": llm.get("parkes_zone_stated"),
                "regex_template": rx.get("regex_template"), "regex_pair": rx.get("pair_found"),
                "display_word": rx.get("sensor_display_word"), "role_swap": r.get("role_swap"),
                "disagree": ";".join(r.get("disagree_fields") or []),
            })
    df = pd.DataFrame(recs)
    n_dup = int(df.duplicated("mdr_report_key").sum())
    df = df.drop_duplicates("mdr_report_key", keep="last").reset_index(drop=True)
    for c in ("sensor", "meter", "wear_day", "latency_s"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    log(f"jsonl: {len(df):,} reports ({bad} unreadable lines skipped, {n_dup} duplicate keys dropped)")
    return df


def load_run_set(path):
    """Run set: tier, weight, dates, brand, FDA problem codes, FDA patient-outcome codes."""
    cols = ["mdr_report_key", "date_received", "date_of_event", "event_type", "product_code", "brand_name",
            "product_problems", "patient_outcome", "tier", "weight", "maker"]
    rs = pd.read_csv(path, usecols=cols, dtype=str)
    rs["weight"] = pd.to_numeric(rs["weight"], errors="coerce").fillna(1.0)
    rs["is_libre3"] = rs["brand_name"].fillna("").str.upper().str.contains("LIBRE 3")
    log(f"run set: {len(rs):,} rows")
    return rs


def load_regex(path):
    """Pattern-layer table: a few columns used for checks."""
    cols = ["mdr_report_key", "sensor_lower_than_meter", "value_flag", "n_pairs", "kw_no_harm_boilerplate", "text_chars"]
    rx = pd.read_csv(path, usecols=cols, dtype=str)
    rx["text_chars"] = pd.to_numeric(rx["text_chars"], errors="coerce")
    log(f"regex table: {len(rx):,} rows")
    return rx


def load_family_map(path):
    """FDA problem term -> plain family (from report_results.py)."""
    m = pd.read_csv(path)
    return dict(zip(m["Problem (FDA term)"].str.strip(), m["Family"]))


def no_text_counts(serious_path, sample_path, cutoff="20260721"):
    """Serious reports outside the run set (too recent / no text) and sampled reports without text, by maker."""
    rows = []
    if serious_path and Path(serious_path).exists():
        s = pd.read_csv(serious_path, usecols=["mdr_report_key", "date_received", "manufacturer", "brand_name",
                                               "event_text", "mfr_narrative"], dtype=str)
        s["maker"] = [maker_of(a, b) for a, b in zip(s["manufacturer"], s["brand_name"])]
        has_text = s["event_text"].fillna("").str.strip().ne("") | (s["mfr_narrative"].fillna("").str.len() > 20)
        recent = s["date_received"].fillna("") > cutoff
        for mk in MAKERS + ["All"]:
            m = (s["maker"] == mk) if mk != "All" else np.ones(len(s), bool)
            rows.append({"tier": "serious", "maker": mk, "reports": int(m.sum()),
                         "too_recent_for_text": int((m & recent).sum()),
                         "no_text": int((m & ~recent & ~has_text).sum()),
                         "in_run_set": int((m & ~recent & has_text).sum())})
        log(f"serious table: {len(s):,} rows")
    if sample_path and Path(sample_path).exists():
        sm = pd.read_parquet(sample_path, columns=["manufacturer", "brand_name", "has_text", "weight"])
        sm["maker"] = [maker_of(a, b) for a, b in zip(sm["manufacturer"], sm["brand_name"])]
        ht = sm["has_text"].astype(str).str.lower().isin(["true", "1", "yes"]) if sm["has_text"].dtype == object else sm["has_text"].astype(bool)
        for mk in MAKERS + ["All"]:
            m = (sm["maker"] == mk) if mk != "All" else np.ones(len(sm), bool)
            rows.append({"tier": "sample", "maker": mk, "reports": int(m.sum()), "too_recent_for_text": 0,
                         "no_text": int((m & ~ht).sum()), "in_run_set": int((m & ht).sum())})
        log(f"sample parquet: {len(sm):,} rows")
    return pd.DataFrame(rows)


def maker_of(*names):
    """Maker label from manufacturer / brand strings (same rule as extract_regex.py)."""
    s = " ".join(str(n or "") for n in names).upper()
    if "ABBOTT" in s or "LIBRE" in s:
        return "Abbott"
    if "DEXCOM" in s:
        return "Dexcom"
    if "MEDTRONIC" in s or "MINIMED" in s or "GUARDIAN" in s or "SIMPLERA" in s or "ENLITE" in s:
        return "Medtronic"
    return "Other"


def parse_log(log_path, summary_path):
    """Run facts from the progress log and the summary JSON: wall-clock, throughput, errors, guard drops."""
    facts = {}
    if log_path and Path(log_path).exists():
        lines = Path(log_path).read_text(encoding="utf-8").splitlines()
        ts = []
        for ln in lines:
            m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", ln)
            if m:
                ts.append(datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
        if ts:
            facts["log_first_line"] = ts[0].isoformat(sep=" ")
            facts["log_last_line"] = ts[-1].isoformat(sep=" ")
            facts["elapsed_first_to_last_h"] = round((ts[-1] - ts[0]).total_seconds() / 3600, 2)
        facts["segments_started"] = sum(1 for ln in lines if "to do:" in ln)
        facts["resumes"] = sum(1 for ln in lines if "resume:" in ln)
        done = [ln for ln in lines if "run done:" in ln]
        seg_wall, seg_err = 0.0, 0
        for ln in done:
            m = re.search(r"run done: (\d+) reports in ([\d.]+) s = ([\d.]+) reports/min.*?errors (\d+); guard-drop rate ([\d.]+)", ln)
            if m:
                seg_wall += float(m.group(2))
                seg_err += int(m.group(4))
        facts["run_done_lines"] = len(done)
        facts["sum_of_run_segments_h"] = round(seg_wall / 3600, 2)
        facts["errors_in_run_done_lines"] = seg_err
        prog = [ln for ln in lines if "reports/min" in ln and "ETA" in ln]
        if prog:
            m = re.search(r"([\d.]+) reports/min", prog[-1])
            facts["last_progress_reports_per_min"] = float(m.group(1)) if m else None
            m = re.search(r"errors (\d+)", prog[-1])
            facts["last_progress_errors"] = int(m.group(1)) if m else None
    if summary_path and Path(summary_path).exists():
        s = json.loads(Path(summary_path).read_text(encoding="utf-8"))
        for k in ("n_requested", "n_ok", "n_errors", "wall_s", "reports_per_min", "latency_mean_s", "latency_p50_s",
                  "latency_p90_s", "guard_drop_rate", "guard_drop_reports", "retries", "role_swap_reports",
                  "mmol_converted_reports", "schema_fixed_reports", "output_tok_per_s_aggregate", "prompt_tokens_max"):
            facts["summary_" + k] = s.get(k)
        facts["summary_guard_drops_by_field"] = json.dumps(s.get("guard_drops_by_field"))
        facts["summary_previous_runs"] = json.dumps(s.get("previous_runs"))
        facts["summary_model"] = s.get("model")
        facts["summary_model_digest"] = str((s.get("model_info") or {}).get("digest", ""))[:12]
    return facts


# ----------------------------------------------------------------------------
# a. Coverage
# ----------------------------------------------------------------------------
def coverage_table(df):
    """Share of reports with each field filled, by tier and maker. Sample rows are weighted."""
    rows = []
    for tier in ["serious", "sample"]:
        for mk in MAKERS + ["All"]:
            sub = df[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True)]
            if sub.empty:
                continue
            w = weights_of(sub)
            pair = sub["sensor"].notna() & sub["meter"].notna()
            r = {"tier": tier if tier == "serious" else "sample (weighted)", "maker": MAKER_LABEL.get(mk, mk),
                 "n_reports": len(sub), "weighted_n": round(float(w.sum())),
                 "pct_model_error": wshare(sub["model_error"], w),
                 "pct_fault_type_known": wshare(sub["fault_type"].ne("unclear") & sub["fault_type"].notna(), w),
                 "pct_sensor_value": wshare(sub["sensor"].notna(), w),
                 "pct_meter_value": wshare(sub["meter"].notna(), w),
                 "pct_both_values": wshare(pair, w),
                 "pct_parkes_zone": wshare(sub["zone_stated"].notna(), w),
                 "pct_wear_day": wshare(sub["wear_day"].notna(), w),
                 "pct_fingerstick_stated": wshare(sub["fingerstick"].ne("not_stated"), w),
                 "pct_user_action_stated": wshare(sub["user_action"].ne("not_stated"), w),
                 "pct_outcome_stated": wshare(sub["outcome"].ne("not_stated"), w),
                 "pct_any_guard_drop": wshare(sub["guard_dropped"].ne(""), w),
                 "pct_zone_guard_drop": wshare(sub["guard_dropped"].str.contains("parkes_zone"), w),
                 "pct_number_guard_drop": wshare(sub["guard_dropped"].str.contains("value_raw"), w),
                 "pct_mmol_converted": wshare(sub["mmol_converted"].ne(""), w),
                 "pct_role_swap": wshare(sub["role_swap"].eq("yes"), w),
                 "pct_multiple_pairs": wshare(sub["multiple_pairs"].eq("yes") & pair, w)}
            # source of the values that are filled
            for fld, srccol in (("sensor", "src_sensor"), ("meter", "src_meter"), ("zone_stated", "src_zone"), ("wear_day", "src_wear")):
                filled = sub[sub[fld].notna()]
                wf = weights_of(filled)
                r[f"pct_{fld}_from_regex"] = wshare(filled[srccol].eq("regex"), wf) if len(filled) else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# b. Fault types vs FDA codes
# ----------------------------------------------------------------------------
def fault_type_table(df):
    """Fault type distribution (% of reports) by tier and maker."""
    rows = []
    for tier in ["serious", "sample"]:
        for mk in MAKERS + ["All"]:
            sub = df[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True)]
            if sub.empty:
                continue
            w = weights_of(sub)
            d = pct_table(sub, "fault_type", FAULT_TYPES, w)
            for ft in FAULT_TYPES:
                rows.append({"tier": tier if tier == "serious" else "sample (weighted)", "maker": MAKER_LABEL.get(mk, mk),
                             "fault_type": ft, "n": int((sub["fault_type"] == ft).sum()), "pct": d[ft]})
    return pd.DataFrame(rows)


def add_code_flags(df, term2fam):
    """Flags from the FDA problem codes: specific terms and the 'wrong readings' family."""
    probs = df["product_problems"].fillna("")
    terms = probs.str.split(";").apply(lambda xs: [t.strip() for t in xs if t.strip()])
    df["code_low"] = terms.apply(lambda ts: CODE_LOW in ts)
    df["code_incorrect"] = terms.apply(lambda ts: CODE_INCORRECT in ts)
    df["code_high"] = terms.apply(lambda ts: CODE_HIGH in ts)
    df["families"] = terms.apply(lambda ts: sorted({term2fam.get(t, "Unmapped") for t in ts}) or ["(no code)"])
    df["code_wrong_family"] = df["families"].apply(lambda fs: WRONG_FAMILY in fs)
    return df


def fault_vs_family_table(df):
    """Cross-table: text fault type x FDA problem family (% of reports of that fault type), serious and weighted sample."""
    rows = []
    for tier in ["serious", "sample"]:
        sub = df[df["split"] == tier]
        for ft in FAULT_TYPES:
            s2 = sub[sub["fault_type"] == ft]
            if s2.empty:
                continue
            w = weights_of(s2)
            fam_w = collections.defaultdict(float)
            for fams, wi in zip(s2["families"], w):
                for fm in fams:
                    fam_w[fm] += wi
            for fm, v in sorted(fam_w.items(), key=lambda x: -x[1]):
                rows.append({"tier": tier if tier == "serious" else "sample (weighted)", "fault_type": ft, "n_reports": len(s2),
                             "family": fm, "pct_of_fault_type_reports": 100.0 * v / w.sum()})
    return pd.DataFrame(rows)


def reads_low_vs_codes_table(df):
    """Agreement: text 'reads_low' vs the codes 'Low Readings' / 'Incorrect ... Readings'; and the reverse."""
    rows = []
    for tier in ["serious", "sample"]:
        for mk in MAKERS + ["All"]:
            sub = df[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True)]
            if sub.empty:
                continue
            rl = sub[sub["fault_type"] == "reads_low"]
            rh = sub[sub["fault_type"] == "reads_high"]
            cl = sub[sub["code_low"]]
            r = {"tier": tier if tier == "serious" else "sample (weighted)", "maker": MAKER_LABEL.get(mk, mk),
                 "n_text_reads_low": len(rl)}
            if len(rl):
                w = weights_of(rl)
                r.update({"reads_low_with_code_low_readings_pct": wshare(rl["code_low"], w),
                          "reads_low_with_code_incorrect_pct": wshare(rl["code_incorrect"], w),
                          "reads_low_with_code_high_readings_pct": wshare(rl["code_high"], w),
                          "reads_low_with_any_wrong_reading_code_pct": wshare(rl["code_wrong_family"], w),
                          "reads_low_with_neither_pct": wshare(~rl["code_wrong_family"], w)})
            r["n_text_reads_high"] = len(rh)
            if len(rh):
                w = weights_of(rh)
                r.update({"reads_high_with_code_high_readings_pct": wshare(rh["code_high"], w),
                          "reads_high_with_code_low_readings_pct": wshare(rh["code_low"], w),
                          "reads_high_with_any_wrong_reading_code_pct": wshare(rh["code_wrong_family"], w)})
            r["n_code_low_readings"] = len(cl)
            if len(cl):
                w = weights_of(cl)
                d = pct_table(cl, "fault_type", FAULT_TYPES, w)
                r.update({"code_low_text_reads_low_pct": d["reads_low"], "code_low_text_reads_high_pct": d["reads_high"],
                          "code_low_text_unclear_pct": d["unclear"],
                          "code_low_text_other_pct": max(0.0, 100.0 - d["reads_low"] - d["reads_high"] - d["unclear"])})
            rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# c. Error sizes and Parkes zones
# ----------------------------------------------------------------------------
def pairs_frame(df):
    """Reports that state both values, with plausible values. Adds error in mg/dL and % of the meter value."""
    both = df[df["sensor"].notna() & df["meter"].notna()].copy()
    plaus = both["sensor"].between(*SENSOR_RANGE) & both["meter"].between(*METER_RANGE)
    n_drop = int((~plaus).sum())
    p = both[plaus].copy()
    p["err_mgdl"] = p["sensor"] - p["meter"]
    p["err_pct"] = 100.0 * p["err_mgdl"] / p["meter"]
    p["direction"] = np.select([p["err_mgdl"] < 0, p["err_mgdl"] > 0], ["low", "high"], default="equal")
    p["zone_computed"] = parkes_zone_labels(p["meter"], p["sensor"])
    log(f"pairs: {len(both):,} with both values, {n_drop} outside the plausible ranges dropped, {len(p):,} kept")
    return p, n_drop


def describe_errors(p, w):
    """Distribution of the error (mg/dL and %) and the share reading low / high."""
    w = np.asarray(w, float)
    out = {"n_pairs": int(len(p)), "weighted_n": round(float(w.sum())) if len(p) else 0}
    for col, name in (("err_mgdl", "mgdl"), ("err_pct", "pct")):
        v = p[col].to_numpy(float)
        for q, lab in ((0.5, "median"), (0.25, "q1"), (0.75, "q3"), (0.10, "p10"), (0.90, "p90")):
            out[f"{lab}_{name}"] = wquantile(v, w, q) if len(p) else np.nan
    for d in ("low", "high", "equal"):
        out[f"pct_{d}"] = wshare(p["direction"] == d, w) if len(p) else np.nan
    out["median_sensor_mgdl"] = wquantile(p["sensor"], w, 0.5) if len(p) else np.nan
    out["median_meter_mgdl"] = wquantile(p["meter"], w, 0.5) if len(p) else np.nan
    out["pct_reads_low_label"] = wshare(p["fault_type"] == "reads_low", w) if len(p) else np.nan
    if len(p):
        # threshold crossings: the report's pair sits on opposite sides of the 70 or 180 mg/dL lines
        out["pct_false_low_70"] = wshare((p["sensor"] < 70) & (p["meter"] >= 70), w)      # sensor says low, meter not low
        out["pct_missed_low_70"] = wshare((p["sensor"] >= 70) & (p["meter"] < 70), w)     # meter low, sensor not low
        out["pct_false_high_180"] = wshare((p["sensor"] > 180) & (p["meter"] <= 180), w)
        out["pct_missed_high_180"] = wshare((p["sensor"] <= 180) & (p["meter"] > 180), w)
        out["pct_abs_err_over_20"] = wshare(p["err_pct"].abs() >= 20, w)
        out["pct_abs_err_over_40"] = wshare(p["err_pct"].abs() >= 40, w)
    return out


def error_groups(p):
    """Yield (group_type, group, tier, frame) for the error-size tables."""
    ser = p[p["split"] == "serious"]
    sam = p[p["split"] == "sample"]
    yield "tier", "All", "serious", ser
    yield "tier", "All", "sample (weighted)", sam
    for mk in MAKERS:
        yield "maker", MAKER_LABEL[mk], "serious", ser[ser["maker"] == mk]
        yield "maker", MAKER_LABEL[mk], "sample (weighted)", sam[sam["maker"] == mk]
    for et in ("Injury", "Death"):
        yield "event_type", et, "serious", ser[ser["event_type"] == et]
    yield "event_type", "Malfunction", "sample (weighted)", sam
    for ft in FAULT_TYPES:
        yield "fault_type", ft, "serious", ser[ser["fault_type"] == ft]
    l3 = ser[ser["is_libre3"]]
    yield "libre3_recall", "Libre 3: received before 2025-11-24", "serious", l3[l3["date_received"] < RECALL_DATE]
    yield "libre3_recall", "Libre 3: received on/after 2025-11-24", "serious", l3[l3["date_received"] >= RECALL_DATE]
    ev = l3["date_of_event"].fillna("")
    yield "libre3_recall", "Libre 3: event before 2025-11-24", "serious", l3[(ev != "") & (ev < RECALL_DATE)]
    yield "libre3_recall", "Libre 3: event on/after 2025-11-24", "serious", l3[(ev != "") & (ev >= RECALL_DATE)]
    for mk in ("Abbott", "Dexcom"):
        for d in ("low", "high"):
            yield "maker_direction", f"{mk} / sensor reads {d}", "serious", ser[(ser["maker"] == mk) & (ser["direction"] == d)]


def error_size_table(p):
    rows = []
    for gtype, g, tier, sub in error_groups(p):
        r = {"group_type": gtype, "group": g, "tier": tier}
        r.update(describe_errors(sub, weights_of(sub)))
        rows.append(r)
    return pd.DataFrame(rows)


def parkes_tables(p, df):
    """Stated vs computed Parkes zone (pairs with a stated zone), and zone shares among all stated zones."""
    z = p[p["zone_stated"].isin(ZONES)]
    rows, agree_rows = [], []
    for mk in MAKERS + ["All"]:
        sub = z[(z["maker"] == mk)] if mk != "All" else z
        if sub.empty:
            continue
        ct = pd.crosstab(sub["zone_stated"], sub["zone_computed"]).reindex(index=ZONES, columns=ZONES, fill_value=0)
        for st in ZONES:
            for cz in ZONES:
                rows.append({"maker": MAKER_LABEL.get(mk, mk), "zone_stated": st, "zone_computed": cz, "n": int(ct.loc[st, cz])})
        exact = float(np.mean(sub["zone_stated"].to_numpy() == sub["zone_computed"]) * 100)
        idx_s = sub["zone_stated"].map(ZONES.index).to_numpy()
        idx_c = pd.Series(sub["zone_computed"]).map(ZONES.index).to_numpy()
        within1 = float(np.mean(np.abs(idx_s - idx_c) <= 1) * 100)
        stated_worse = float(np.mean(idx_s > idx_c) * 100)
        computed_worse = float(np.mean(idx_s < idx_c) * 100)
        agree_rows.append({"maker": MAKER_LABEL.get(mk, mk), "n_pairs_with_stated_zone": len(sub), "exact_agreement_pct": exact,
                           "within_one_zone_pct": within1, "stated_zone_worse_pct": stated_worse, "computed_zone_worse_pct": computed_worse,
                           "stated_C_to_E_pct": float(sub["zone_stated"].isin(list("CDE")).mean() * 100),
                           "computed_C_to_E_pct": float(pd.Series(sub["zone_computed"]).isin(list("CDE")).mean() * 100)})
    # zone shares among all reports with a stated zone (not only pairs), by tier and maker
    share_rows = []
    for tier in ["serious", "sample"]:
        for mk in MAKERS + ["All"]:
            sub = df[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True) & df["zone_stated"].isin(ZONES)]
            if sub.empty:
                continue
            w = weights_of(sub)
            d = pct_table(sub, "zone_stated", ZONES, w)
            share_rows.append({"source": f"MAUDE {tier if tier == 'serious' else 'sample (weighted)'}", "maker": MAKER_LABEL.get(mk, mk),
                               "n_with_zone": len(sub), **{f"zone_{k}_pct": v for k, v in d.items()}})
    share_rows.append({"source": "REPLACE-BG trial, Set A (all pairs)", "maker": "Dexcom G4", "n_with_zone": 33467,
                       **{f"zone_{k}_pct": v for k, v in TRIAL_PARKES_SET_A.items()}})
    return pd.DataFrame(rows), pd.DataFrame(agree_rows), pd.DataFrame(share_rows)


# ----------------------------------------------------------------------------
# d. Wear day
# ----------------------------------------------------------------------------
def wear_day_tables(df):
    """Wear-day distribution of the reported failure vs a flat expectation (1/14 Libre, 1/10 Dexcom)."""
    dist_rows, sum_rows = [], []
    wd_all = df[df["wear_day"].notna() & (df["wear_day"] >= 1)]
    for tier in ["serious", "sample"]:
        for mk in MAKERS + ["All"]:
            sub = wd_all[(wd_all["split"] == tier) & ((wd_all["maker"] == mk) if mk != "All" else True)]
            if len(sub) < 10:
                continue
            w = weights_of(sub)
            life = SENSOR_LIFE_DAYS.get(mk)
            days = np.minimum(sub["wear_day"].to_numpy(float), MAX_WEAR_DAY_SHOWN + 1)
            for d in range(1, MAX_WEAR_DAY_SHOWN + 2):
                lab = str(d) if d <= MAX_WEAR_DAY_SHOWN else f">{MAX_WEAR_DAY_SHOWN}"
                dist_rows.append({"tier": tier if tier == "serious" else "sample (weighted)", "maker": MAKER_LABEL.get(mk, mk),
                                  "wear_day": lab, "n": int((days == d).sum()), "pct": wshare(days == d, w),
                                  "flat_expectation_pct": (100.0 / life if (life and d <= life) else (0.0 if life else np.nan))})
            wdv = sub["wear_day"].to_numpy(float)
            r = {"tier": tier if tier == "serious" else "sample (weighted)", "maker": MAKER_LABEL.get(mk, mk), "n_with_wear_day": len(sub),
                 "pct_of_reports_with_wear_day": wshare(df.loc[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True), "wear_day"].notna(),
                                                        weights_of(df[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True)])),
                 "median_wear_day": wquantile(wdv, w, 0.5), "pct_day_1": wshare(wdv == 1, w), "pct_days_1_2": wshare(wdv <= 2, w),
                 "pct_days_1_3": wshare(wdv <= 3, w)}
            if life:
                r.update({"sensor_life_days": life, "pct_last_two_days": wshare((wdv >= life - 1) & (wdv <= life), w),
                          "pct_beyond_life": wshare(wdv > life, w), "flat_day_1_pct": 100.0 / life, "flat_days_1_2_pct": 200.0 / life,
                          "flat_last_two_pct": 200.0 / life, "day_1_ratio_to_flat": wshare(wdv == 1, w) / (100.0 / life)})
            sum_rows.append(r)
    return pd.DataFrame(dist_rows), pd.DataFrame(sum_rows)


# ----------------------------------------------------------------------------
# e. User action and outcome
# ----------------------------------------------------------------------------
def action_outcome_tables(df):
    """User action, outcome and fingerstick check by tier, maker and fault type (% of reports)."""
    act_rows, out_rows, fs_rows, rl_rows = [], [], [], []
    for tier in ["serious", "sample"]:
        for mk in MAKERS + ["All"]:
            base = df[(df["split"] == tier) & ((df["maker"] == mk) if mk != "All" else True)]
            for ft in FAULT_TYPES + ["All"]:
                sub = base[base["fault_type"] == ft] if ft != "All" else base
                if len(sub) < 10:
                    continue
                w = weights_of(sub)
                tlab = tier if tier == "serious" else "sample (weighted)"
                mlab = MAKER_LABEL.get(mk, mk)
                da = pct_table(sub, "user_action", USER_ACTIONS, w)
                act_rows.append({"tier": tlab, "maker": mlab, "fault_type": ft, "n": len(sub), **{f"{k}_pct": v for k, v in da.items()}})
                do = pct_table(sub, "outcome", OUTCOMES, w)
                out_rows.append({"tier": tlab, "maker": mlab, "fault_type": ft, "n": len(sub), **{f"{k}_pct": v for k, v in do.items()},
                                 "any_glucose_event_or_worse_pct": do["hypoglycemia"] + do["hyperglycemia_or_dka"] + do["hospital_or_er"] + do["death"]})
                dfs = pct_table(sub, "fingerstick", ["yes", "no", "not_stated"], w)
                fs_rows.append({"tier": tlab, "maker": mlab, "fault_type": ft, "n": len(sub), **{f"{k}_pct": v for k, v in dfs.items()}})
                if ft == "reads_low":
                    rl_rows.append({"tier": tlab, "maker": mlab, "n_reads_low": len(sub),
                                    "ate_carbs_pct": da["ate_carbs"], "skipped_insulin_pct": da["skipped_insulin"],
                                    "ate_carbs_or_skipped_insulin_pct": da["ate_carbs"] + da["skipped_insulin"],
                                    "took_insulin_pct": da["took_insulin"], "sought_care_pct": da["sought_care"],
                                    "fingerstick_yes_pct": dfs["yes"], "hypoglycemia_pct": do["hypoglycemia"],
                                    "hyperglycemia_or_dka_pct": do["hyperglycemia_or_dka"], "hospital_or_er_pct": do["hospital_or_er"],
                                    "death_pct": do["death"]})
    return pd.DataFrame(act_rows), pd.DataFrame(out_rows), pd.DataFrame(fs_rows), pd.DataFrame(rl_rows)


def fda_outcome_flags(value):
    """Set of FDA patient-outcome codes in one report. Blank = none stated. Letters are turned into names."""
    out = set()
    for tok in str(value if value is not None else "").split(";"):
        t = tok.strip()
        if not t or t.lower() == "nan":
            continue
        out.add(FDA_OUTCOME_CODES.get(t, t))
    return out


def fda_key(name):
    """Column stem for an FDA outcome name: 'Required Intervention' -> 'fda_required_intervention'."""
    return "fda_" + name.lower().replace(" ", "_")


def outcome_vs_fda_table(df):
    """Serious reports: the model's outcome category against the FDA patient-outcome codes (a report may carry several).
    One row per model category plus 'All serious'. For each FDA code: the number and the % of the row's reports that carry it.
    'fda_care' = Hospitalization or Required Intervention (the FDA codes a clinic, ER or EMS visit usually gets)."""
    ser = df[df["split"] == "serious"].copy()
    flags = ser["patient_outcome"].map(fda_outcome_flags)
    names = FDA_OUTCOME_ORDER + ["none stated", "care"]
    for code in FDA_OUTCOME_ORDER:
        ser[fda_key(code)] = flags.map(lambda f, c=code: c in f)
    ser[fda_key("none stated")] = flags.map(lambda f: len(f) == 0)
    ser[fda_key("care")] = ser[fda_key("Hospitalization")] | ser[fda_key("Required Intervention")]
    cats = OUTCOMES + ["(no model answer)", "All serious"]
    rows = []
    for cat in cats:
        if cat == "All serious":
            sub = ser
        elif cat == "(no model answer)":
            sub = ser[~ser["outcome"].isin(OUTCOMES)]
            if len(sub) == 0:
                continue
        else:
            sub = ser[ser["outcome"] == cat]
        r = {"model_outcome": cat, "n": int(len(sub)), "pct_of_serious": 100.0 * len(sub) / len(ser)}
        for name in names:
            k = fda_key(name)
            r[k + "_n"] = int(sub[k].sum())
            r[k + "_pct"] = 100.0 * sub[k].mean() if len(sub) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# f. Join to the Phase 2 lookup table
# ----------------------------------------------------------------------------
def lookup_edges(lookup):
    """(lowest bias, highest bias, step) of a lookup table, in percent."""
    b = np.sort(lookup["bias_pct"].to_numpy(float))
    step = float(np.min(np.diff(b))) if len(b) > 1 else 2.0
    return float(b[0]), float(b[-1]), step


def clip_label(lo, hi):
    """Row label for the clip used: 'table edge (-90 / +90 %)' or 'clipped at -40 % (floor)'."""
    if (lo, hi) == FLOOR_CLIP:
        return "clipped at -40 % (floor)"
    return f"table edge ({lo:.0f} / {hi:+.0f} %)"



def join_lookup(sub, lookup, mode, clip=None):
    """Bin reported errors to the lookup's steps (2 %) and take the error-weighted mean of each outcome.
    mode 'low'  = sensor-below-meter errors only.
    mode 'all'  = both directions.
    clip = (lowest, highest) bias in percent; errors beyond it are counted in the edge bin. Default: the table's own
    edges. FLOOR_CLIP (-40, +40) reproduces the original join, where every result was a floor.
    Returns (dict of expected outcomes and shares, Series of weighted bin shares)."""
    lo_edge, hi_edge, step = lookup_edges(lookup)
    clip_lo, clip_hi = clip if clip is not None else (lo_edge, hi_edge)
    clip_lo, clip_hi = max(clip_lo, lo_edge), min(clip_hi, hi_edge)      # the clip cannot reach past the table
    e = sub["err_pct"].to_numpy(float)
    w = weights_of(sub)
    labelled_low = (sub["fault_type"] == "reads_low").to_numpy()
    if mode == "low":
        keep = e < 0
        e, w, labelled_low = e[keep], w[keep], labelled_low[keep]
    cols = JOIN_COLS_LOW if mode == "low" else JOIN_COLS_ALL
    out = {"n_pairs": int(len(e)), "weighted_n": round(float(w.sum())) if len(e) else 0,
           "clip_low_pct": clip_lo, "clip_high_pct": clip_hi}
    if len(e) == 0:
        return out, pd.Series(dtype=float)
    out["pct_model_labelled_reads_low"] = wshare(labelled_low, w)
    raw_bins = step * np.round(e / step)                                   # the bin before clipping
    bins = np.clip(raw_bins, clip_lo, clip_hi)
    share = pd.Series(w).groupby(bins).sum() / w.sum()
    share.index = share.index.astype(int)
    lk = lookup.set_index("bias_pct")
    base = lk.loc[0]
    for c in cols:
        med = lk[c + "_median"].reindex(share.index)
        out[f"{c}_expected"] = float((share * med).sum())
        if c in ("tir_pct", "tbr70_pct", "lbgi"):
            out[f"{c}_change_vs_true"] = float((share * med).sum() - base[c + "_median"])
    out["skipped_pct_expected_mean_person"] = float((share * lk["skipped_pct_mean"].reindex(share.index)).sum())
    out["median_err_pct"] = wquantile(e, w, 0.5)
    for tp in TIPPING_POINTS:
        if mode == "low":
            out[f"pct_beyond_minus_{int(tp)}"] = wshare(e <= -tp, w)
        else:
            out[f"pct_abs_beyond_{int(tp)}"] = wshare(np.abs(e) >= tp, w)
    # shares of pairs past an edge = pairs whose bin lies beyond it (they are counted in the edge bin)
    out["pct_beyond_minus_40"] = wshare(raw_bins < FLOOR_CLIP[0], w)
    out["pct_beyond_plus_40"] = wshare(raw_bins > FLOOR_CLIP[1], w) if mode == "all" else 0.0
    out["pct_beyond_clip_low"] = wshare(raw_bins < clip_lo, w)             # still beyond this row's own low edge
    out["pct_beyond_clip_high"] = wshare(raw_bins > clip_hi, w) if mode == "all" else 0.0
    return out, share


def join_groups(p):
    """Groups for the join: (label, frame)."""
    ser = p[p["split"] == "serious"]
    sam = p[p["split"] == "sample"]
    l3 = ser[ser["is_libre3"]]
    yield "Serious / Abbott", ser[ser["maker"] == "Abbott"]
    yield "Serious / Dexcom", ser[ser["maker"] == "Dexcom"]
    yield "Serious / Medtronic (undercounted; weakest validation)", ser[ser["maker"] == "Medtronic"]
    yield "Serious / all makers", ser
    yield "Malfunction sample (weighted) / all makers", sam
    yield "Malfunction sample (weighted) / Abbott", sam[sam["maker"] == "Abbott"]
    yield "Serious / Libre 3 received on/after 2025-11-24", l3[l3["date_received"] >= RECALL_DATE]
    yield "Serious / Libre 3 received before 2025-11-24", l3[l3["date_received"] < RECALL_DATE]
    yield "Serious / Injury", ser[ser["event_type"] == "Injury"]
    yield "Serious / Death", ser[ser["event_type"] == "Death"]


def join_tables(p, lookup):
    """Join tables. Every group once at the table's edges and, when the table reaches past -40 %, once more clipped at
    -40 % (the original result, a floor). Bin shares are for the edge clip only. Reference rows = the plain lookup."""
    lo_edge, hi_edge, _ = lookup_edges(lookup)
    clips = [(lo_edge, hi_edge)]
    if lo_edge < FLOOR_CLIP[0]:
        clips.append(FLOOR_CLIP)
    low_rows, all_rows, bin_rows = [], [], []
    for clip in clips:
        lab = clip_label(*clip)
        for label, sub in join_groups(p):
            o_low, share_low = join_lookup(sub, lookup, "low", clip)
            o_all, _ = join_lookup(sub, lookup, "all", clip)
            low_rows.append({"group": label, "clip": lab, **o_low})
            all_rows.append({"group": label, "clip": lab, **o_all})
            if clip == clips[0]:
                for b, s in share_low.items():
                    bin_rows.append({"group": label, "bias_bin_pct": int(b), "weighted_share_pct": 100.0 * float(s)})
    # reference rows: the lookup itself at a constant bias (what a bias of exactly that size does)
    lk = lookup.set_index("bias_pct")
    for b in dict.fromkeys(list(JOIN_REFERENCE_BIAS) + [int(lo_edge)]):
        if b not in lk.index:
            continue
        r = {"group": f"Reference: constant bias {b} % (lookup row)", "clip": "", "n_pairs": np.nan, "weighted_n": np.nan}
        for c in JOIN_COLS_LOW:
            r[f"{c}_expected"] = float(lk.loc[b, c + "_median"])
        for c in ("tir_pct", "tbr70_pct", "lbgi"):
            r[f"{c}_change_vs_true"] = float(lk.loc[b, c + "_median"] - lk.loc[0, c + "_median"])
        low_rows.append(r)
    return pd.DataFrame(low_rows), pd.DataFrame(all_rows), pd.DataFrame(bin_rows)


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def save(fig, path, dpi=None):
    """Write a figure. dpi=None keeps the shared rcParams value (200); t6 is written at 150 (figure rules, 2026-10-30)."""
    fig.savefig(path, **({"dpi": dpi} if dpi else {}))
    plt.close(fig)
    log(f"wrote {path}")


def fig_coverage(cov, path):
    """t1: share of reports with each field filled, by maker; serious vs weighted sample."""
    fields = [("pct_fault_type_known", "fault type known"), ("pct_both_values", "sensor + meter value"),
              ("pct_parkes_zone", "Parkes zone stated"), ("pct_wear_day", "wear day"),
              ("pct_fingerstick_stated", "fingerstick check stated"), ("pct_user_action_stated", "user action stated"),
              ("pct_outcome_stated", "outcome stated")]
    fig, axes = plt.subplots(1, 2, figsize=(6, 3.6), sharey=True)
    for ax, tier, title in zip(axes, ["serious", "sample (weighted)"], ["Serious reports (death + injury)", "Malfunction sample (weighted)"]):
        sub = cov[cov["tier"] == tier]
        y = np.arange(len(fields))
        h = 0.2
        for i, mk in enumerate(MAKERS):
            r = sub[sub["maker"] == MAKER_LABEL[mk]]
            if r.empty:
                continue
            vals = [float(r.iloc[0][f]) for f, _ in fields]
            ax.barh(y + (i - 1.5) * h, vals, height=h, color=MAKER_COLORS[mk], label=mk + ("*" if mk == "Medtronic" else ""))
        ax.set_yticks(y)
        ax.set_yticklabels([lab for _, lab in fields], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xlabel("share of reports (%)")
        ax.set_title(title, fontsize=9.5)
        ax.grid(axis="x", color=GRID)
        ax.grid(axis="y", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=9, bbox_to_anchor=(0.5, 0.035))
    fig.text(0.01, 0.0, "* Medtronic: undercounted (pump product codes) and weakest validation.", fontsize=9, color=INK2)
    fig.suptitle("What the text pipeline could read, by maker", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0.09, 1, 0.94))
    save(fig, path)


def fig_fault_types(ft, path):
    """t2: fault type distribution by maker, serious vs weighted sample."""
    labels = {"reads_low": "reads low", "reads_high": "reads high", "erratic": "erratic", "stuck": "stuck",
              "signal_loss": "signal loss", "sensor_error_or_early_end": "sensor error / early end",
              "adhesive_or_detachment": "adhesive / fell off", "insertion_or_skin_injury": "insertion / skin injury",
              "other_device": "other device problem", "unclear": "unclear"}
    fig, axes = plt.subplots(1, 2, figsize=(6, 4.0), sharey=True)
    for ax, tier, title in zip(axes, ["serious", "sample (weighted)"], ["Serious reports", "Malfunction sample (weighted)"]):
        sub = ft[ft["tier"] == tier]
        y = np.arange(len(FAULT_TYPES))
        h = 0.2
        for i, mk in enumerate(MAKERS):
            r = sub[sub["maker"] == MAKER_LABEL[mk]].set_index("fault_type").reindex(FAULT_TYPES)
            ax.barh(y + (i - 1.5) * h, r["pct"].fillna(0).to_numpy(), height=h, color=MAKER_COLORS[mk], label=mk + ("*" if mk == "Medtronic" else ""))
        ax.set_yticks(y)
        ax.set_yticklabels([labels[f] for f in FAULT_TYPES], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("share of reports (%)")
        ax.set_title(title, fontsize=9.5)
        ax.grid(axis="x", color=GRID)
        ax.grid(axis="y", visible=False)
    handles, lg = axes[0].get_legend_handles_labels()
    fig.legend(handles, lg, loc="lower center", ncol=4, fontsize=9, bbox_to_anchor=(0.5, 0.035))
    fig.text(0.01, 0.0, "* Medtronic: undercounted (pump product codes) and weakest validation.", fontsize=9, color=INK2)
    fig.suptitle("Fault type read from the text (model field), by maker", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0.08, 1, 0.94))
    save(fig, path)


def fig_error_sizes(p, es, path):
    """t3: histogram of the relative error for serious Abbott and Dexcom pairs; summary ranges per group below."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6.2), gridspec_kw={"height_ratios": [1.1, 1.0]})
    ser = p[p["split"] == "serious"]
    lo, hi = -100, 200
    bins = np.arange(lo, hi + 5, 5)
    for mk in ("Abbott", "Dexcom"):
        v = ser.loc[ser["maker"] == mk, "err_pct"].clip(lo, hi - 0.01).to_numpy()
        if len(v) == 0:
            continue
        ax1.hist(v, bins=bins, weights=np.full(len(v), 100.0 / len(v)), histtype="step", lw=2, color=MAKER_COLORS[mk],
                 label=f"{mk} (n = {len(v):,})")
    for x, lab, ha, dx in ((-20, "-20 %", "right", -2), (-12, "-12 %", "left", 2)):
        ax1.axvline(x, color=INK2, lw=1, ls=":")
        ax1.text(x + dx, ax1.get_ylim()[1] * 0.97, lab, ha=ha, va="top", fontsize=9, color=INK2)
    ax1.axvline(0, color=AXIS, lw=1)
    ax1.set_xlim(lo, hi)
    ax1.set_xlabel(f"sensor minus meter, % of the meter value (clipped at {lo} and +{hi})")
    ax1.set_ylabel("share of pairs (%)")
    ax1.set_title("Reported error size, serious reports with both values (5 % bins)", fontsize=9.5)
    ax1.legend(loc="upper right", fontsize=9)
    # summary ranges
    want = [("maker", MAKER_LABEL["Abbott"], "serious", "Abbott, serious"), ("maker", MAKER_LABEL["Dexcom"], "serious", "Dexcom, serious"),
            ("maker", MAKER_LABEL["Medtronic"], "serious", "Medtronic, serious (undercounted)"), ("maker", MAKER_LABEL["Other"], "serious", "Other, serious"),
            ("maker", MAKER_LABEL["Abbott"], "sample (weighted)", "Abbott, malfunction sample (w)"),
            ("libre3_recall", "Libre 3: received before 2025-11-24", "serious", "Libre 3 before recall"),
            ("libre3_recall", "Libre 3: received on/after 2025-11-24", "serious", "Libre 3 after recall")]
    rows = []
    for gtype, g, tier, lab in want:
        r = es[(es["group_type"] == gtype) & (es["group"] == g) & (es["tier"] == tier)]
        if not r.empty and r.iloc[0]["n_pairs"] > 0:
            rows.append((lab, r.iloc[0]))
    y = np.arange(len(rows))
    for i, (lab, r) in enumerate(rows):
        col = C_BLUE if "Abbott" in lab or "Libre" in lab else (C_ORANGE if "Dexcom" in lab else (C_AQUA if "Medtronic" in lab else MUTED))
        ax2.plot([max(r["p10_pct"], lo), min(r["p90_pct"], hi)], [i, i], color=col, lw=1.2, alpha=0.7)
        ax2.plot([max(r["q1_pct"], lo), min(r["q3_pct"], hi)], [i, i], color=col, lw=5, solid_capstyle="butt")
        ax2.plot(min(max(r["median_pct"], lo), hi), i, marker="o", color=INK, ms=4)
        ax2.text(hi + 3, i, f"n={int(r['n_pairs']):,}", va="center", fontsize=9, color=INK2)
    ax2.set_yticks(y)
    ax2.set_yticklabels([lab for lab, _ in rows], fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlim(lo, hi)
    ax2.axvline(0, color=AXIS, lw=1)
    ax2.axvline(-20, color=INK2, lw=1, ls=":")
    ax2.set_xlabel("sensor minus meter, % of the meter value (ranges cut at the axis edges)")
    ax2.set_title("Error size by group: dot = median, thick = IQR, thin = 10th to 90th percentile", fontsize=9.5)
    ax2.grid(axis="x", color=GRID)
    ax2.grid(axis="y", visible=False)
    fig.suptitle("How far off were the sensors in the reports? Negative = sensor read low", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, path)


def fig_parkes(ct, agree, path):
    """t4: stated vs computed Parkes zone, heatmaps for Abbott and Dexcom."""
    fig, axes = plt.subplots(1, 2, figsize=(6, 3.4))
    for ax, mk in zip(axes, ("Abbott", "Dexcom")):
        sub = ct[ct["maker"] == MAKER_LABEL[mk]]
        if sub.empty:
            ax.set_visible(False)
            continue
        m = sub.pivot(index="zone_stated", columns="zone_computed", values="n").reindex(index=ZONES, columns=ZONES, fill_value=0).to_numpy()
        tot = m.sum()
        ax.imshow(m / max(tot, 1), cmap=matplotlib.colors.LinearSegmentedColormap.from_list("ramp", [SURFACE] + RAMP), vmin=0, vmax=max(0.01, (m / max(tot, 1)).max()))
        for i in range(5):
            for j in range(5):
                if m[i, j] > 0:
                    ax.text(j, i, f"{m[i, j]:,}", ha="center", va="center", fontsize=9,
                            color=SURFACE if m[i, j] / max(tot, 1) > 0.5 * (m / max(tot, 1)).max() else INK)
        ax.set_xticks(range(5))
        ax.set_xticklabels(ZONES)
        ax.set_yticks(range(5))
        ax.set_yticklabels(ZONES)
        ax.set_xlabel("zone computed from the two values")
        ax.set_ylabel("zone stated by the maker")
        a = agree[agree["maker"] == MAKER_LABEL[mk]]
        ex = f"{a.iloc[0]['exact_agreement_pct']:.0f} %" if not a.empty else "-"
        ax.set_title(f"{mk}: n = {tot:,}, exact agreement {ex}", fontsize=9.5)
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("Maker-stated Parkes zone vs the zone we compute from the pair", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, path)


def fig_wear_day(dist, summ, path):
    """t5: wear day of the reported failure vs a flat expectation, Abbott and Dexcom."""
    fig, axes = plt.subplots(1, 2, figsize=(6, 3.4), sharey=False)
    for ax, mk in zip(axes, ("Abbott", "Dexcom")):
        life = SENSOR_LIFE_DAYS[mk]
        xs = np.arange(1, MAX_WEAR_DAY_SHOWN + 2)
        plotted, ymax = False, 0.0
        for tier, col, lab in (("serious", MAKER_COLORS[mk], "serious reports"), ("sample (weighted)", RAMP[0] if mk == "Abbott" else "#f3b79b", "malfunction sample (weighted)")):
            sub = dist[(dist["tier"] == tier) & (dist["maker"] == MAKER_LABEL[mk])]
            if sub.empty:
                continue
            vals = sub.set_index("wear_day")["pct"].reindex([str(d) for d in range(1, MAX_WEAR_DAY_SHOWN + 1)] + [f">{MAX_WEAR_DAY_SHOWN}"]).fillna(0).to_numpy()
            off = -0.2 if tier == "serious" else 0.2
            n = int(sub["n"].sum())
            ax.bar(xs + off, vals, width=0.4, color=col, label=f"{lab}, n = {n:,}")
            plotted = True
            ymax = max(ymax, float(np.nanmax(vals)))
        if not plotted:
            ax.set_visible(False)
            continue
        ax.hlines(100.0 / life, 0.5, life + 0.5, color=INK2, lw=1.2, ls="--")
        ax.text(life + 0.4, 100.0 / life + 0.4, f"flat: 1/{life} per day", ha="right", va="bottom", fontsize=9, color=INK2)
        ax.set_ylim(0, max(ymax, 100.0 / life) * 1.45)
        ticks = list(range(1, MAX_WEAR_DAY_SHOWN - 1, 2)) + [MAX_WEAR_DAY_SHOWN + 1]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(d) for d in ticks[:-1]] + [f"{MAX_WEAR_DAY_SHOWN + 1}+"], fontsize=8.5)
        ax.set_xlabel("wear day stated in the report")
        ax.set_ylabel("share of reports with a wear day (%)")
        ax.set_title(f"{mk} ({life}-day sensor life assumed)", fontsize=9.5)
        ax.legend(loc="upper right", fontsize=8.5)
    fig.suptitle("Wear day of the reported failure (complaint timing, not a failure rate)", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=INK)
    fig.text(0.01, 0.005, f"Trial (REPLACE-BG, Dexcom G4): day 1 MARD {TRIAL_WEAR_DAY_MARD['day1']} % vs day 7 {TRIAL_WEAR_DAY_MARD['day7']} % (ERROR_DRIVERS.md s5).",
             fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    save(fig, path)


def fig_join(bins, low, lookup, path, lookup_name="simulation_v2_lookup.csv"):
    """t6: reported reads-low errors on the lookup's bias steps (the table's full negative range), and the expected
    decision impact per group. Marks the -12 % and -20 % tipping points and the old -40 % table edge."""
    lo_edge, hi_edge, step = lookup_edges(lookup)
    edge = low[low["clip"].str.startswith("table edge")]
    floor = low[low["clip"].str.startswith("clipped at -40")]
    fig = plt.figure(figsize=(7.4, 7.0))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.15, 1.0], hspace=0.55, wspace=0.14)
    ax = fig.add_subplot(gs[0, :])
    groups = [("Serious / Abbott", C_BLUE), ("Serious / Dexcom", C_ORANGE)]
    xs = np.arange(lo_edge, 0.1, step)
    width = step * 0.42
    top = 1.0
    for i, (g, col) in enumerate(groups):
        sub = bins[bins["group"] == g].set_index("bias_bin_pct")["weighted_share_pct"].reindex(xs.astype(int)).fillna(0)
        n = edge.loc[edge["group"] == g, "n_pairs"]
        n_lab = f", n = {int(n.iloc[0]):,}" if len(n) else ""
        ax.bar(xs + (i - 0.5) * width, sub.to_numpy(), width=width, color=col,
               label=g.replace("Serious / ", "serious ") + f" reads-low pairs{n_lab}")
        top = max(top, float(sub.max()))
    ax.set_ylim(0, top * 1.7)
    ax2 = ax.twinx()
    lk = lookup[lookup["bias_pct"] <= 0]
    ax2.plot(lk["bias_pct"], lk["skipped_pct_median"], color=INK, lw=1.5, label="lookup: corrections skipped (median person)")
    ax2.set_ylim(0, float(lk["skipped_pct_median"].max()) * 1.7)
    ax2.set_ylabel("corrections skipped (% of decisions)")
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    # tipping points and the old table edge
    marks = [(-TIPPING_POINTS[0], f"{-TIPPING_POINTS[0]:.0f} %: skipping starts", ":"),
             (-TIPPING_POINTS[1], f"{-TIPPING_POINTS[1]:.0f} %: tipping point", ":"),
             (FLOOR_CLIP[0], f"{FLOOR_CLIP[0]:.0f} %: old table edge", "--")]
    for x, lab, ls in marks:
        ax.axvline(x, color=INK2, lw=1, ls=ls)
        ax.text(x - step * 0.25, top * 1.66, lab, rotation=90, va="top", ha="right", fontsize=7.5, color=INK2)
    ax.set_xlim(lo_edge - step, step)
    ax.set_xlabel(f"sensor bias, % of the meter value (negative = reads low); errors below {lo_edge:.0f} % are counted in the {lo_edge:.0f} % bin")
    ax.set_ylabel("share of reads-low pairs (%)")
    ax.set_title(f"Where the reported reads-low errors fall on the simulation's bias steps ({lo_edge:.0f} to 0 %)", fontsize=9.5)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, ncol=1)
    # expected impact per group: horizontal bars, labels on the first panel only
    show = [(edge, "Serious / Abbott", "Abbott serious", C_BLUE),
            (floor, "Serious / Abbott", "Abbott serious, old -40 % floor", RAMP[0]),
            (edge, "Serious / Dexcom", "Dexcom serious", C_ORANGE),
            (edge, "Malfunction sample (weighted) / all makers", "malfunction sample (w)", MUTED),
            (edge, "Serious / Libre 3 received on/after 2025-11-24", "Libre 3 post-recall", RAMP[2]),
            (low, "Reference: constant bias -20 % (lookup row)", "constant -20 % bias", AXIS)]
    panels = [("skipped_pct_expected", "corrections skipped (%)"), ("low70_false_per_day_expected", "false low alerts per day"),
              ("tbr70_pct_expected", "time shown below 70 (%)"), ("high180_missed_pct_expected", "high episodes missed (%)")]
    first = None
    for j, (col, lab) in enumerate(panels):
        axp = fig.add_subplot(gs[1, j], sharey=first)
        vals, cols, labs = [], [], []
        for frame, g, glab, c in show:
            r = frame[frame["group"] == g]
            if r.empty or pd.isna(r.iloc[0][col]):
                continue
            vals.append(float(r.iloc[0][col]))
            cols.append(c)
            labs.append(glab)
        ypos = np.arange(len(vals))
        axp.barh(ypos, vals, color=cols, height=0.65)
        for i, v in enumerate(vals):
            axp.text(v, i, f" {v:.1f}" if v < 10 else f" {v:.0f}", ha="left", va="center", fontsize=8.5, color=INK2)
        axp.set_yticks(ypos)
        if first is None:
            axp.set_yticklabels(labs, fontsize=8.5)
            axp.invert_yaxis()
            first = axp
        else:
            axp.tick_params(labelleft=False)
        axp.set_title(lab, fontsize=9)
        axp.set_xlim(0, max(vals + [1]) * 1.35)
        axp.grid(axis="x", color=GRID)
        axp.grid(axis="y", visible=False)
    allrow = edge[edge["group"] == "Serious / all makers"]
    skip_all = float(allrow.iloc[0]["skipped_pct_expected"]) if len(allrow) else float("nan")
    fig.suptitle(f"Join: the reported reads-low errors would skip about {skip_all:.0f} % of correction doses (median trial person)",
                 x=0.01, ha="left", fontsize=10.5, fontweight="semibold", color=INK)
    fig.text(0.01, 0.005, f"Reported errors are the worst cases people complained about, not an average sensor. "
             f"Lookup: analysis/{lookup_name}, bias grid {lo_edge:.0f} to {hi_edge:+.0f} %.", fontsize=8.5, color=INK2)
    save(fig, path, dpi=150)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Phase 1 text results and the join to Phase 2.")
    ap.add_argument("--jsonl", default=str(REPO / "fda-maude/clean/text_extract_v3.jsonl"))
    ap.add_argument("--run-set", default=str(REPO / "fda-maude/clean/run_set.csv.gz"))
    ap.add_argument("--regex", default=str(REPO / "fda-maude/clean/regex_run_set.csv"))
    ap.add_argument("--serious", default=str(REPO / "fda-maude/clean/serious.csv.gz"), help="clean serious table (for the no-text counts)")
    ap.add_argument("--sample-parquet", default=str(REPO / "fda-maude/clean/sample_local.parquet"))
    default_lookup = REPO / "analysis/simulation_v2_lookup_extended.csv"        # -90..+90 % grid (2026-10-30)
    if not default_lookup.exists():
        default_lookup = REPO / "analysis/simulation_v2_lookup.csv"             # base -40..+40 % grid
    ap.add_argument("--lookup", default=str(default_lookup),
                    help="Phase 2 lookup table (bias_pct rows). Default: the extended grid when it exists, else the base file")
    ap.add_argument("--family-map", default=str(REPO / "fda-maude/results/report/tables/d_problem_family_mapping.csv"))
    ap.add_argument("--log", default=str(REPO / "fda-maude/clean/logs/text_extract_v3.log"))
    ap.add_argument("--summary", default=str(REPO / "fda-maude/clean/text_extract_v3_summary.json"))
    ap.add_argument("--out-tables", default=str(REPO / "fda-maude/results/text/tables"))
    ap.add_argument("--out-figures", default=str(REPO / "fda-maude/results/text/figures"))
    ap.add_argument("--max-rows", type=int, default=None, help="read only the first N JSONL rows (test)")
    ap.add_argument("--skip-serious", action="store_true", help="skip the clean serious table (faster test)")
    args = ap.parse_args()

    out_t = Path(args.out_tables)
    out_f = Path(args.out_figures)
    out_t.mkdir(parents=True, exist_ok=True)
    out_f.mkdir(parents=True, exist_ok=True)

    df = load_jsonl(args.jsonl, args.max_rows)
    rs = load_run_set(args.run_set)
    rx = load_regex(args.regex)
    lookup = pd.read_csv(args.lookup)
    lk_lo, lk_hi, lk_step = lookup_edges(lookup)
    log(f"lookup: {args.lookup} ({len(lookup)} rows, bias {lk_lo:.0f} to {lk_hi:+.0f} % in {lk_step:.0f} % steps)")
    term2fam = load_family_map(args.family_map)

    df = df.merge(rs.drop(columns=["event_type", "maker"]), on="mdr_report_key", how="left")
    df = df.merge(rx, on="mdr_report_key", how="left")
    df["weight"] = df["weight"].fillna(1.0)
    df["split"] = df["split"].fillna(df["tier"])
    df["is_libre3"] = df["is_libre3"].fillna(False).astype(bool)
    missing_rs = int(df["tier"].isna().sum())
    log(f"merged: {len(df):,} reports; {missing_rs} without a run-set row; "
        f"serious {int((df['split'] == 'serious').sum()):,}, sample {int((df['split'] == 'sample').sum()):,}")
    df = add_code_flags(df, term2fam)

    facts = parse_log(args.log, args.summary)
    facts["rows_in_jsonl"] = len(df)
    facts["rows_expected"] = len(rs)
    facts["model_errors_in_jsonl"] = int(df["model_error"].sum())
    facts["guard_drop_reports"] = int(df["guard_dropped"].ne("").sum())
    facts["guard_drop_rate_pct"] = round(100.0 * df["guard_dropped"].ne("").mean(), 2)
    drops = collections.Counter(d for s in df["guard_dropped"] if s for d in s.split(";"))
    facts["guard_drops_by_field"] = json.dumps(dict(drops))
    zone_drop = df["guard_dropped"].str.contains("parkes_zone")
    facts["zone_guard_drops_rescued_by_regex"] = int((zone_drop & df["zone_stated"].notna()).sum())
    facts["zone_guard_drops_total"] = int(zone_drop.sum())
    facts["median_latency_s"] = float(df["latency_s"].median())
    facts["retried_reports"] = int((df["attempts"].fillna(1) > 1).sum())
    if facts.get("elapsed_first_to_last_h"):
        facts["rows_per_min_over_elapsed"] = round(len(df) / (facts["elapsed_first_to_last_h"] * 60.0), 1)
    pd.DataFrame([{"metric": k, "value": v} for k, v in facts.items()]).to_csv(out_t / "a_run_facts.csv", index=False)
    log("a_run_facts.csv written")

    # a. coverage
    cov = coverage_table(df)
    cov.to_csv(out_t / "a_coverage_by_group.csv", index=False)
    if not args.skip_serious:
        nt = no_text_counts(args.serious, args.sample_parquet)
        if not nt.empty:
            nt.to_csv(out_t / "a_no_text.csv", index=False)
    log("coverage tables written")

    # b. fault types
    ft = fault_type_table(df)
    ft.to_csv(out_t / "b_fault_type_by_group.csv", index=False)
    fault_vs_family_table(df).to_csv(out_t / "b_fault_type_vs_code_family.csv", index=False)
    agree_codes = reads_low_vs_codes_table(df)
    agree_codes.to_csv(out_t / "b_reads_low_vs_codes.csv", index=False)
    log("fault type tables written")

    # c. error sizes and Parkes
    p, n_implausible = pairs_frame(df)
    es = error_size_table(p)
    es.to_csv(out_t / "c_error_sizes.csv", index=False)
    ct, agree, shares = parkes_tables(p, df)
    ct.to_csv(out_t / "c_parkes_stated_vs_computed.csv", index=False)
    agree.to_csv(out_t / "c_parkes_agreement.csv", index=False)
    shares.to_csv(out_t / "c_parkes_zone_shares.csv", index=False)
    log("error size and Parkes tables written")

    # d. wear day
    wd_dist, wd_sum = wear_day_tables(df)
    wd_dist.to_csv(out_t / "d_wear_day_distribution.csv", index=False)
    wd_sum.to_csv(out_t / "d_wear_day_summary.csv", index=False)
    log("wear day tables written")

    # e. actions and outcomes
    act, outc, fs, rl = action_outcome_tables(df)
    act.to_csv(out_t / "e_user_action.csv", index=False)
    outc.to_csv(out_t / "e_outcome.csv", index=False)
    fs.to_csv(out_t / "e_fingerstick_check.csv", index=False)
    rl.to_csv(out_t / "e_reads_low_actions_outcomes.csv", index=False)
    ovf = outcome_vs_fda_table(df)
    ovf.to_csv(out_t / "e_outcome_vs_fda.csv", index=False)
    log("action and outcome tables written")

    # f. join
    low, allj, bins = join_tables(p, lookup)
    low.to_csv(out_t / "f_join_reads_low.csv", index=False)
    allj.to_csv(out_t / "f_join_all_errors.csv", index=False)
    bins.to_csv(out_t / "f_join_bins.csv", index=False)
    log("join tables written")

    # figures
    fig_coverage(cov, out_f / "t1_coverage.png")
    fig_fault_types(ft, out_f / "t2_fault_types.png")
    fig_error_sizes(p, es, out_f / "t3_error_sizes.png")
    fig_parkes(ct, agree, out_f / "t4_parkes_agreement.png")
    fig_wear_day(wd_dist, wd_sum, out_f / "t5_wear_day.png")
    fig_join(bins, low, lookup, out_f / "t6_join.png", Path(args.lookup).name)

    # key numbers (JSON) and markdown versions of the key tables
    stats = {"run_facts": facts, "n_pairs_implausible_dropped": n_implausible,
             "coverage": cov.to_dict(orient="records"), "error_sizes": es.to_dict(orient="records"),
             "parkes_agreement": agree.to_dict(orient="records"), "wear_day_summary": wd_sum.to_dict(orient="records"),
             "reads_low_actions": rl.to_dict(orient="records"), "outcome_vs_fda": ovf.to_dict(orient="records"),
             "join_lookup_file": Path(args.lookup).name, "join_lookup_edges_pct": [lk_lo, lk_hi], "join_floor_clip_pct": list(FLOOR_CLIP),
             "join_reads_low": low.to_dict(orient="records"),
             "join_all_errors": allj.to_dict(orient="records"), "reads_low_vs_codes": agree_codes.to_dict(orient="records")}
    (out_t / "text_results_stats.json").write_text(json.dumps(stats, indent=1, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else str(o)), encoding="utf-8")

    md = ["# Key tables (markdown copies of the CSVs in this folder)", ""]
    md += ["## a. Run facts", to_markdown(pd.DataFrame([{"metric": k, "value": v} for k, v in facts.items()])), ""]
    cov_cols = ["tier", "maker", "n_reports", "weighted_n", "pct_fault_type_known", "pct_both_values", "pct_parkes_zone", "pct_wear_day",
                "pct_fingerstick_stated", "pct_user_action_stated", "pct_outcome_stated", "pct_sensor_from_regex", "pct_zone_stated_from_regex",
                "pct_wear_day_from_regex", "pct_any_guard_drop", "pct_zone_guard_drop", "pct_number_guard_drop", "pct_model_error"]
    md += ["## a. Coverage", to_markdown(cov[cov_cols]), ""]
    order = [(t, MAKER_LABEL.get(m, m)) for t in ("serious", "sample (weighted)") for m in MAKERS + ["All"]]
    ftp = ft.pivot_table(index="fault_type", columns=["tier", "maker"], values="pct").reindex(FAULT_TYPES)
    ftp = ftp.reindex(columns=[c for c in order if c in ftp.columns])
    ftp.columns = [f"{t} / {m.split(' (')[0]}" for t, m in ftp.columns]
    md += ["## b. Fault type (% of reports)", to_markdown(ftp.reset_index()), ""]
    md += ["## b. Text reads_low vs codes", to_markdown(agree_codes), ""]
    es_cols = ["group_type", "group", "tier", "n_pairs", "weighted_n", "median_mgdl", "q1_mgdl", "q3_mgdl", "p10_mgdl", "p90_mgdl",
               "median_pct", "q1_pct", "q3_pct", "p10_pct", "p90_pct", "pct_low", "pct_high", "median_sensor_mgdl", "median_meter_mgdl"]
    md += ["## c. Error sizes", to_markdown(es[es_cols]), ""]
    md += ["## c. Parkes agreement", to_markdown(agree), ""]
    md += ["## c. Parkes zone shares", to_markdown(shares), ""]
    md += ["## d. Wear day summary", to_markdown(wd_sum), ""]
    md += ["## e. reads_low: actions and outcomes", to_markdown(rl), ""]
    md += ["## e. Fingerstick check (all fault types)", to_markdown(fs[fs["fault_type"] == "All"]), ""]
    md += ["## e. Outcome (all fault types)", to_markdown(outc[outc["fault_type"] == "All"]), ""]
    md += ["## e. Model outcome vs FDA patient-outcome codes (serious reports; a report may carry several codes)", to_markdown(ovf), ""]
    md += [f"## f. Join, reads-low pairs (lookup: {Path(args.lookup).name}, bias {lk_lo:.0f} to {lk_hi:+.0f} %)", to_markdown(low, "{:.2f}"), ""]
    md += ["## f. Join, all pairs (both directions)", to_markdown(allj, "{:.2f}"), ""]
    (out_t / "key_tables.md").write_text("\n".join(md), encoding="utf-8")
    log(f"done: tables in {out_t}, figures in {out_f}")


if __name__ == "__main__":
    main()
