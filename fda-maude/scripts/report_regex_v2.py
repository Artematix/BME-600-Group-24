#!/usr/bin/env python
"""
report_regex_v2.py : tables and figures from the full-corpus pattern run (clean/regex_v2_full.csv.gz).

Used by `extract_regex_v2.py full` (at the end) and `extract_regex_v2.py report`. It can also run alone:
  python fda-maude/scripts/report_regex_v2.py
  python fda-maude/scripts/report_regex_v2.py --out fda-maude/clean/regex_v2_full.csv.gz --tables-dir ... --figures-dir ...

Words used
  pair = a report that states both the sensor value and the meter (fingerstick / lab) value.
  error = sensor minus meter, in mg/dL and in % of the meter value. Negative = the sensor read low.
  serious = FDA event type Death or Injury. malfunction = event type Malfunction (no harm coded).
  median = the middle value; IQR = the middle half (25th to 75th percentile).
  same-sentence pairs = the pattern found both numbers in one sentence (the safer patterns).

What it writes (results/text/tables/h_*.csv, results/text/figures/t12_*, t13_*, tables/h_regex_v2_stats.json)
  h_full_coverage.csv            reports, texts, pairs, bound pairs, wear day, zone, by event group and brand
  h_full_pairs_by_pattern.csv    which pattern gave the pair, by event group
  h_malf_vs_serious_errors.csv   error sizes, direction, meter bands: malfunction-only vs serious, by brand
  h_malf_vs_serious_tests.csv    Mann-Whitney and Cliff's delta on the error size; chi-square on the shares
  h_error_distribution.csv       10 % bins of the error, shares of pairs, by group and brand
  h_by_year.csv                  pairs, median error, direction, hidden lows, by year received
  h_harm_gradient.csv            share of pairs that sit in a death/injury report, per signed error band, by brand
  h_harm_gradient_abs.csv        the same per absolute-error band and direction
  h_harm_gradient_text.csv       text-stated harm words per error band, inside each event group (the extra check)
  h_outcome_coding.csv           FDA patient-outcome codes behind the serious pairs, by brand (the coding caveat)
  h_weighted_check.csv           weighted-sample estimates vs the full-corpus malfunction numbers
Deterministic (seed 20261106 for the bootstrap).
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
FDA = HERE.parent
SEED = 20261106
CUTOFF = "20260721"                # text cut-off used by the run set (3 months before the snapshot)
BRANDS = ["Abbott", "Dexcom", "Medtronic", "Senseonics", "Other"]
MAIN = ["Abbott", "Dexcom", "Medtronic", "Senseonics"]
BANDS = ["under 54", "54 to 69", "70 to 180", "181 to 250", "over 250"]
SAME_SENTENCE = {"abbott_template", "v1_prose_same_sentence", "v2_same_sentence", "v2_comparison_one_side", "v2_comparison_implicit"}
SIGNED_EDGES = list(range(-100, 101, 10)) + [200, 10_000]
ABS_EDGES = list(range(0, 101, 10)) + [200, 10_000]
MIN_N = 20                         # no share is shown for a cell with fewer pairs
FDA_OUTCOME_CODES = {"R": "Required Intervention", "H": "Hospitalization", "L": "Life Threatening", "D": "Death",
                     "O": "Other", "S": "Disability", "C": "Congenital Anomaly", "U": "Unknown"}
T0 = time.time()

# Chart style: the same palette and settings as text_results.py (project-wide, light surface)
C_BLUE, C_ORANGE, C_AQUA, C_GOLD = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BRAND_COLORS = {"Abbott": C_BLUE, "Dexcom": C_ORANGE, "Medtronic": C_AQUA, "Senseonics": C_GOLD, "Other": MUTED}
GROUP_COLORS = {"serious": C_BLUE, "malfunction": C_AQUA}
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


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
USECOLS = ["mdr_report_key", "event_group", "brand", "year_received", "sensor_value", "meter_value", "error_mgdl",
           "error_pct", "direction", "meter_band", "pattern", "value_flags", "sensor_display_word", "sensor_bound",
           "meter_bound", "bound_pattern", "two_sensor_readings", "wear_day", "zone_stated", "kw_reads_low",
           "kw_reads_high", "kw_inaccurate", "kw_insulin_dose", "kw_ate_carbs", "kw_hypo_symptoms", "kw_hyper_dka",
           "kw_fingerstick", "kw_ems_or_hospital", "kw_death_real", "kw_no_harm_boilerplate", "has_text"]
KW_COLS = [c for c in USECOLS if c.startswith("kw_")]
CAT_COLS = ["event_group", "brand", "direction", "meter_band", "pattern", "bound_pattern", "zone_stated",
            "sensor_display_word", "sensor_bound", "meter_bound", "value_flags"]


def load_full(path, max_rows=None):
    """The per-report pattern output, in chunks, with compact column types."""
    parts, n = [], 0
    for ch in pd.read_csv(path, usecols=USECOLS, dtype=str, chunksize=400_000):
        for c in ("sensor_value", "meter_value", "error_mgdl", "error_pct"):
            ch[c] = pd.to_numeric(ch[c], errors="coerce").astype("float32")
        ch["wear_day"] = pd.to_numeric(ch["wear_day"], errors="coerce").astype("float32")
        ch["year_received"] = pd.to_numeric(ch["year_received"], errors="coerce").astype("float32")
        for c in KW_COLS + ["has_text", "two_sensor_readings"]:
            ch[c] = ch[c].eq("yes")
        for c in CAT_COLS:
            ch[c] = ch[c].fillna("").astype("category")
        parts.append(ch)
        n += len(ch)
        log(f"  loaded {n:,} rows")
        if max_rows and n >= max_rows:
            break
    df = pd.concat(parts, ignore_index=True)
    for c in CAT_COLS:
        df[c] = df[c].astype(str).astype("category")     # one shared category index after the concat
    df["pair"] = df["sensor_value"].notna() & df["meter_value"].notna()
    df["serious"] = df["event_group"].isin(["death", "injury"])
    df["group"] = np.where(df["serious"], "serious", np.where(df["event_group"] == "malfunction", "malfunction", "other"))
    df["same_sentence"] = df["pattern"].isin(SAME_SENTENCE)
    df["abs_pct"] = df["error_pct"].abs()
    df["harm_text"] = df["kw_hypo_symptoms"] | df["kw_ems_or_hospital"] | df["kw_death_real"]
    df["action_text"] = df["kw_insulin_dose"] | df["kw_ate_carbs"]
    log(f"full output: {len(df):,} reports, {int(df['pair'].sum()):,} pairs")
    return df


def add_fda_fields(df, full_parquet):
    """Join date received and the FDA patient-outcome codes from the clean parquet (needed for the cut-off and the coding caveat)."""
    import pyarrow.parquet as pq
    t = pq.read_table(full_parquet, columns=["mdr_report_key", "date_received", "patient_outcome"]).to_pandas()
    t["mdr_report_key"] = t["mdr_report_key"].astype(str)
    t = t.drop_duplicates("mdr_report_key")
    df = df.merge(t, on="mdr_report_key", how="left")
    df["date_received"] = df["date_received"].fillna("")
    po = df["patient_outcome"].fillna("")

    def codes(s):
        out = set()
        for tok in str(s).split(";"):
            tok = tok.strip()
            if not tok:
                continue
            out.add(FDA_OUTCOME_CODES.get(tok, tok))
        return out
    c = po.map(codes)
    df["fda_req_intervention"] = c.map(lambda s: "Required Intervention" in s)
    df["fda_hospitalization"] = c.map(lambda s: "Hospitalization" in s)
    df["fda_life_threatening"] = c.map(lambda s: "Life Threatening" in s)
    df["fda_death"] = c.map(lambda s: "Death" in s)
    df["fda_other_only"] = c.map(lambda s: len(s) > 0 and s <= {"Other", "Unknown"})
    df["fda_req_intervention_only"] = c.map(lambda s: s - {"Other", "Unknown"} == {"Required Intervention"})
    log("joined date received and FDA outcome codes")
    return df


# ----------------------------------------------------------------------------
# Small statistics helpers
# ----------------------------------------------------------------------------
def wquantile(v, w, q):
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    if len(v) == 0:
        return np.nan
    o = np.argsort(v)
    v, w = v[o], w[o]
    cw = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cw, v))


def wilson(k, n, z=1.96):
    """Wilson 95 % interval for a share, in %."""
    if n == 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (centre - half), 100 * (centre + half)


def describe(p, w=None):
    """Error-size summary of a set of pairs (DataFrame rows with error_pct, error_mgdl, sensor_value, meter_value)."""
    if w is None:
        w = np.ones(len(p))
    w = np.asarray(w, float)
    out = {"n_pairs": int(len(p)), "weighted_n": int(round(w.sum())) if len(p) else 0}
    if not len(p):
        return out
    for col, name in (("error_pct", "pct"), ("error_mgdl", "mgdl")):
        v = p[col].to_numpy(float)
        for q, lab in ((0.5, "median"), (0.25, "q1"), (0.75, "q3"), (0.10, "p10"), (0.90, "p90")):
            out[f"{lab}_{name}"] = round(wquantile(v, w, q), 1)
    sh = lambda m: round(100 * float(w[np.asarray(m, bool)].sum() / w.sum()), 1)
    low = p["error_pct"] < 0
    out["pct_reads_low"] = sh(low)
    out["pct_reads_high"] = sh(~low)
    out["median_pct_reads_low"] = round(wquantile(p.loc[low, "error_pct"], w[low.to_numpy()], 0.5), 1) if low.any() else np.nan
    out["median_pct_reads_high"] = round(wquantile(p.loc[~low, "error_pct"], w[(~low).to_numpy()], 0.5), 1) if (~low).any() else np.nan
    out["median_abs_pct"] = round(wquantile(p["error_pct"].abs(), w, 0.5), 1)
    out["pct_abs_over_20"] = sh(p["error_pct"].abs() >= 20)
    out["pct_abs_over_40"] = sh(p["error_pct"].abs() >= 40)
    out["median_sensor_mgdl"] = round(wquantile(p["sensor_value"], w, 0.5), 0)
    out["median_meter_mgdl"] = round(wquantile(p["meter_value"], w, 0.5), 0)
    for b in BANDS:
        out[f"pct_meter_{b.replace(' ', '_')}"] = sh(p["meter_band"].astype(str) == b)
    out["pct_meter_under_70"] = sh(p["meter_value"] < 70)
    out["pct_false_low_70"] = sh((p["sensor_value"] < 70) & (p["meter_value"] >= 70))
    out["pct_missed_low_70"] = sh((p["sensor_value"] >= 70) & (p["meter_value"] < 70))
    out["pct_false_high_180"] = sh((p["sensor_value"] > 180) & (p["meter_value"] <= 180))
    out["pct_missed_high_180"] = sh((p["sensor_value"] <= 180) & (p["meter_value"] > 180))
    out["pct_same_sentence_pattern"] = sh(p["same_sentence"])
    return out


def cliffs_delta(a, b):
    """Cliff's delta from the Mann-Whitney U: -1 to 1, 0 = no difference. Positive = a tends to be larger."""
    from scipy.stats import mannwhitneyu
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < MIN_N or len(b) < MIN_N:
        return np.nan, np.nan
    u, pval = mannwhitneyu(a, b, alternative="two-sided")
    return 2 * u / (len(a) * len(b)) - 1, pval


def delta_label(d):
    if np.isnan(d):
        return "too few"
    d = abs(d)
    return "negligible" if d < 0.15 else "small" if d < 0.33 else "medium" if d < 0.47 else "large"


def share_test(k1, n1, k2, n2):
    """Risk difference (percentage points) with a 95 % interval and a chi-square p-value."""
    from scipy.stats import chi2_contingency
    if min(n1, n2) < MIN_N:
        return np.nan, np.nan, np.nan, np.nan
    p1, p2 = k1 / n1, k2 / n2
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    table = np.array([[k1, n1 - k1], [k2, n2 - k2]])
    pval = chi2_contingency(table)[1] if table.min() >= 0 and (table.sum(axis=1) > 0).all() else np.nan
    return 100 * (p1 - p2), 100 * (p1 - p2 - 1.96 * se), 100 * (p1 - p2 + 1.96 * se), pval


# ----------------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------------
def coverage_table(df):
    rows = []
    for g in ["death", "injury", "malfunction", "other", "all"]:
        dg = df if g == "all" else df[df["event_group"] == g]
        for b in BRANDS + ["All"]:
            d = dg if b == "All" else dg[dg["brand"] == b]
            if not len(d):
                continue
            txt = d["has_text"]
            n_txt = int(txt.sum())
            pct = lambda m: round(100 * int(m.sum()) / n_txt, 2) if n_txt else np.nan
            rows.append({"event_group": g, "brand": b, "reports": len(d), "with_text": n_txt,
                         "pairs": int(d["pair"].sum()), "pair_rate_pct_of_text": pct(d["pair"]),
                         "pairs_same_sentence": int((d["pair"] & d["same_sentence"]).sum()),
                         "bound_pairs": int((d["bound_pattern"].astype(str) != "").sum()),
                         "display_word_pct": pct(d["sensor_display_word"].astype(str) != ""),
                         "two_sensor_readings": int(d["two_sensor_readings"].sum()),
                         "wear_day_pct": pct(d["wear_day"].notna()), "zone_pct": pct(d["zone_stated"].astype(str) != ""),
                         "kw_reads_low_pct": pct(d["kw_reads_low"]), "kw_reads_high_pct": pct(d["kw_reads_high"]),
                         "kw_inaccurate_pct": pct(d["kw_inaccurate"]), "kw_fingerstick_pct": pct(d["kw_fingerstick"]),
                         "kw_ems_or_hospital_pct": pct(d["kw_ems_or_hospital"]), "kw_hypo_symptoms_pct": pct(d["kw_hypo_symptoms"])})
    return pd.DataFrame(rows)


def pattern_table(df):
    p = df[df["pair"]]
    t = pd.crosstab(p["pattern"].astype(str), p["group"].astype(str))
    t["all"] = t.sum(axis=1)
    t = t.sort_values("all", ascending=False).reset_index()
    t["share_of_pairs_pct"] = (100 * t["all"] / t["all"].sum()).round(1)
    return t


def errors_table(df):
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"])]
    rows = []
    for b in ["All"] + MAIN:
        pb = p if b == "All" else p[p["brand"] == b]
        for g in ["malfunction", "serious", "injury", "death"]:
            d = pb[pb["group"] == g] if g in ("malfunction", "serious") else pb[pb["event_group"] == g]
            rows.append({"brand": b, "group": g, **describe(d)})
            if g in ("malfunction", "serious"):
                ds = d[d["same_sentence"]]
                r = describe(ds)
                rows.append({"brand": b, "group": g + " (same-sentence patterns only)", **r})
    return pd.DataFrame(rows)


def tests_table(df):
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"])]
    rows = []
    for b in ["All"] + MAIN:
        pb = p if b == "All" else p[p["brand"] == b]
        m, s = pb[pb["group"] == "malfunction"], pb[pb["group"] == "serious"]
        for col, name in (("abs_pct", "absolute error %"), ("error_pct", "signed error %")):
            d, pv = cliffs_delta(m[col], s[col])
            rows.append({"brand": b, "measure": name, "n_malfunction": len(m), "n_serious": len(s),
                         "median_malfunction": round(float(m[col].median()), 1) if len(m) else np.nan,
                         "median_serious": round(float(s[col].median()), 1) if len(s) else np.nan,
                         "cliffs_delta_malf_minus_serious": round(d, 3) if not np.isnan(d) else np.nan,
                         "effect": delta_label(d), "p_mann_whitney": pv})
        for flag, name in ((m["error_pct"] < 0, "reads low"), (m["meter_value"] < 70, "meter under 70 (hidden low)"),
                           (m["abs_pct"] >= 40, "absolute error 40 % or more"),
                           ((m["sensor_value"] < 70) & (m["meter_value"] >= 70), "false low (sensor under 70, meter not)")):
            if name == "reads low":
                k2 = int((s["error_pct"] < 0).sum())
            elif name.startswith("meter under"):
                k2 = int((s["meter_value"] < 70).sum())
            elif name.startswith("absolute"):
                k2 = int((s["abs_pct"] >= 40).sum())
            else:
                k2 = int(((s["sensor_value"] < 70) & (s["meter_value"] >= 70)).sum())
            k1 = int(flag.sum())
            rd, lo, hi, pv = share_test(k1, len(m), k2, len(s))
            rows.append({"brand": b, "measure": name + " (share, points: malfunction minus serious)", "n_malfunction": len(m),
                         "n_serious": len(s), "median_malfunction": round(100 * k1 / len(m), 1) if len(m) else np.nan,
                         "median_serious": round(100 * k2 / len(s), 1) if len(s) else np.nan,
                         "cliffs_delta_malf_minus_serious": round(rd, 1) if not np.isnan(rd) else np.nan,
                         "effect": f"CI {lo:.1f} to {hi:.1f}" if not np.isnan(rd) else "too few", "p_mann_whitney": pv})
    return pd.DataFrame(rows)


def bin_labels(edges):
    labs = []
    for a, b in zip(edges[:-1], edges[1:]):
        labs.append(f"{a} to {b}" if b < 10_000 else f"over {a}")
    return labs


def distribution_table(df):
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"])]
    labs = bin_labels(SIGNED_EDGES)
    rows = []
    for b in ["All", "Abbott", "Dexcom", "Medtronic", "Senseonics"]:
        pb = p if b == "All" else p[p["brand"] == b]
        for g in ("malfunction", "serious"):
            d = pb[pb["group"] == g]
            if len(d) < MIN_N:
                continue
            cut = pd.cut(d["error_pct"], SIGNED_EDGES, right=False, labels=labs, include_lowest=True)
            vc = cut.value_counts().reindex(labs).fillna(0)
            for lab in labs:
                rows.append({"brand": b, "group": g, "error_pct_bin": lab, "pairs": int(vc[lab]),
                             "share_pct": round(100 * vc[lab] / len(d), 2)})
    return pd.DataFrame(rows)


def by_year_table(df):
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"]) & df["year_received"].notna()]
    rows = []
    for b in ["All", "Abbott", "Dexcom"]:
        pb = p if b == "All" else p[p["brand"] == b]
        for y in sorted(pb["year_received"].dropna().unique()):
            for g in ("malfunction", "serious"):
                d = pb[(pb["year_received"] == y) & (pb["group"] == g)]
                if len(d) < MIN_N:
                    continue
                rows.append({"brand": b, "year_received": int(y), "group": g, "pairs": len(d),
                             "median_error_pct": round(float(d["error_pct"].median()), 1),
                             "pct_reads_low": round(100 * float((d["error_pct"] < 0).mean()), 1),
                             "pct_meter_under_70": round(100 * float((d["meter_value"] < 70).mean()), 1),
                             "pct_abs_over_40": round(100 * float((d["abs_pct"] >= 40).mean()), 1),
                             "pct_same_sentence_pattern": round(100 * float(d["same_sentence"].mean()), 1)})
    return pd.DataFrame(rows)


def gradient_table(df, edges, col, by_direction=False):
    """Share of pairs that sit in a death/injury report, per error band and brand (Wilson 95 % interval)."""
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"])]
    labs = bin_labels(edges)
    rows = []
    for b in ["All"] + MAIN:
        pb = p if b == "All" else p[p["brand"] == b]
        dirs = ["low", "high"] if by_direction else ["both"]
        for dr in dirs:
            d = pb if dr == "both" else pb[pb["error_pct"] < 0] if dr == "low" else pb[pb["error_pct"] >= 0]
            if not len(d):
                continue
            n_s_all, n_all = int(d["serious"].sum()), len(d)
            cut = pd.cut(d[col], edges, right=False, labels=labs, include_lowest=True)
            for lab in labs:
                m = cut == lab
                n = int(m.sum())
                k = int((m & d["serious"]).sum())
                lo, hi = wilson(k, n) if n >= MIN_N else (np.nan, np.nan)
                rows.append({"brand": b, "direction": dr, "error_band": lab, "pairs": n, "pairs_serious": k,
                             "pairs_malfunction": n - k, "share_serious_pct": round(100 * k / n, 1) if n >= MIN_N else np.nan,
                             "ci_low": round(lo, 1) if n >= MIN_N else np.nan, "ci_high": round(hi, 1) if n >= MIN_N else np.nan,
                             "brand_overall_share_serious_pct": round(100 * n_s_all / n_all, 1)})
    return pd.DataFrame(rows)


def gradient_text_table(df):
    """Harm words in the text (symptoms, medical care, death) per absolute-error band, inside each event group."""
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"])]
    labs = bin_labels(ABS_EDGES)
    rows = []
    for b in ["All", "Abbott", "Dexcom"]:
        pb = p if b == "All" else p[p["brand"] == b]
        for g in ("malfunction", "serious"):
            d = pb[pb["group"] == g]
            if not len(d):
                continue
            cut = pd.cut(d["abs_pct"], ABS_EDGES, right=False, labels=labs, include_lowest=True)
            for lab in labs:
                m = cut == lab
                n = int(m.sum())
                k_h, k_a = int((m & d["harm_text"]).sum()), int((m & d["action_text"]).sum())
                lo, hi = wilson(k_h, n) if n >= MIN_N else (np.nan, np.nan)
                rows.append({"brand": b, "group": g, "abs_error_band": lab, "pairs": n,
                             "harm_words_pct": round(100 * k_h / n, 1) if n >= MIN_N else np.nan,
                             "ci_low": round(lo, 1) if n >= MIN_N else np.nan, "ci_high": round(hi, 1) if n >= MIN_N else np.nan,
                             "action_words_pct": round(100 * k_a / n, 1) if n >= MIN_N else np.nan})
    return pd.DataFrame(rows)


def outcome_coding_table(df):
    """What FDA outcome codes sit behind the serious pairs, by brand; and the no-harm sentence in malfunction pairs."""
    p = df[df["pair"] & df["group"].isin(["serious", "malfunction"])]
    rows = []
    for b in ["All"] + MAIN:
        pb = p if b == "All" else p[p["brand"] == b]
        s, m = pb[pb["group"] == "serious"], pb[pb["group"] == "malfunction"]
        pct = lambda d, c: round(100 * float(d[c].mean()), 1) if len(d) else np.nan
        rows.append({"brand": b, "serious_pairs": len(s), "malfunction_pairs": len(m),
                     "serious_required_intervention_only_pct": pct(s, "fda_req_intervention_only"),
                     "serious_required_intervention_any_pct": pct(s, "fda_req_intervention"),
                     "serious_hospitalization_pct": pct(s, "fda_hospitalization"),
                     "serious_life_threatening_pct": pct(s, "fda_life_threatening"), "serious_death_pct": pct(s, "fda_death"),
                     "serious_other_only_pct": pct(s, "fda_other_only"),
                     "serious_harm_words_pct": pct(s, "harm_text"), "malfunction_harm_words_pct": pct(m, "harm_text"),
                     "serious_action_words_pct": pct(s, "action_text"), "malfunction_action_words_pct": pct(m, "action_text"),
                     "malfunction_no_harm_sentence_pct": pct(m, "kw_no_harm_boilerplate"),
                     "serious_no_harm_sentence_pct": pct(s, "kw_no_harm_boilerplate")})
    return pd.DataFrame(rows)


def weighted_check_table(df, sample_parquet, n_boot=500):
    """Weighted estimates from the local malfunction sample vs the full-corpus malfunction numbers (same frame:
    malfunction reports received on or before the text cut-off)."""
    if not Path(sample_parquet).exists():
        log("sample parquet not found: weighted check skipped")
        return pd.DataFrame()
    sm = pd.read_parquet(sample_parquet, columns=["mdr_report_key", "weight", "manufacturer", "brand_name"])
    sm["mdr_report_key"] = sm["mdr_report_key"].astype(str)
    cols = ["mdr_report_key", "brand", "pair", "error_pct", "sensor_value", "meter_value", "abs_pct", "same_sentence"]
    sm = sm.merge(df[cols], on="mdr_report_key", how="left")
    sm["pair"] = sm["pair"].fillna(False).astype(bool)
    frame = df[(df["event_group"] == "malfunction") & (df["date_received"] <= CUTOFF) & (df["date_received"] != "")]
    rng = np.random.default_rng(SEED)
    rows = []

    def stats(d, w):
        w = np.asarray(w, float)
        out = {"pair_rate_pct": 100 * w[d["pair"].to_numpy()].sum() / w.sum() if w.sum() else np.nan}
        pp = d[d["pair"]]
        wp = w[d["pair"].to_numpy()]
        if len(pp) >= MIN_N:
            out["median_error_pct"] = wquantile(pp["error_pct"], wp, 0.5)
            out["pct_reads_low"] = 100 * wp[(pp["error_pct"] < 0).to_numpy()].sum() / wp.sum()
            out["pct_meter_under_70"] = 100 * wp[(pp["meter_value"] < 70).to_numpy()].sum() / wp.sum()
            out["pct_abs_over_40"] = 100 * wp[(pp["abs_pct"] >= 40).to_numpy()].sum() / wp.sum()
        else:
            out.update({"median_error_pct": np.nan, "pct_reads_low": np.nan, "pct_meter_under_70": np.nan, "pct_abs_over_40": np.nan})
        return out

    for b in ["All", "Abbott", "Dexcom"]:
        s = sm if b == "All" else sm[sm["brand"] == b]
        f = frame if b == "All" else frame[frame["brand"] == b]
        if not len(s):
            continue
        est = stats(s, s["weight"])
        boots = {k: [] for k in est}
        idx = np.arange(len(s))
        for _ in range(n_boot):
            take = rng.choice(idx, size=len(idx), replace=True)
            sb = s.iloc[take]
            r = stats(sb, sb["weight"])
            for k in est:
                boots[k].append(r[k])
        full_stats = stats(f, np.ones(len(f)))
        for k in est:
            arr = np.array([x for x in boots[k] if not (isinstance(x, float) and np.isnan(x))])
            lo, hi = (np.percentile(arr, 2.5), np.percentile(arr, 97.5)) if len(arr) > 10 else (np.nan, np.nan)
            rows.append({"brand": b, "measure": k, "sample_reports": len(s), "sample_pairs": int(s["pair"].sum()),
                         "weighted_estimate": round(float(est[k]), 2) if not np.isnan(est[k]) else np.nan,
                         "bootstrap_ci_low": round(float(lo), 2) if not np.isnan(lo) else np.nan,
                         "bootstrap_ci_high": round(float(hi), 2) if not np.isnan(hi) else np.nan,
                         "full_corpus_value": round(float(full_stats[k]), 2) if not np.isnan(full_stats[k]) else np.nan,
                         "full_corpus_reports": len(f), "full_corpus_pairs": int(f["pair"].sum()),
                         "inside_ci": ("yes" if (not np.isnan(lo) and lo <= full_stats[k] <= hi) else "no") if not np.isnan(full_stats[k]) and not np.isnan(lo) else ""})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def fig_recall(tables_dir, figures_dir):
    """t11: regex recall against the model, baseline vs tuned, by brand (from the tune tables)."""
    path = Path(tables_dir) / "h_regex_v2_recall_by_brand.csv"
    if not path.exists():
        return
    t = pd.read_csv(path)
    brands = ["Abbott", "Dexcom", "Medtronic", "Other", "All"]
    base = t[t["version"] == "v1 baseline"].set_index("brand").reindex(brands)
    tuned = t[t["version"] == "v2 tuned"].set_index("brand").reindex(brands)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(brands))
    w = 0.36
    b1 = ax.bar(x - w / 2, base["recall_pct"], w, color=MUTED, label="v1 patterns (baseline)", zorder=3)
    b2 = ax.bar(x + w / 2, tuned["recall_pct"], w, color=C_BLUE, label="v2 patterns (tuned)", zorder=3)
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1, f"{r.get_height():.0f}", ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{b}\n(n = {int(tuned.loc[b, 'model_pairs']):,})" for b in brands])
    ax.set_ylim(0, 105)
    ax.set_ylabel("Recall against the model, %")
    ax.set_title("Share of the model's sensor-meter pairs the patterns also find (run set, 124,599 reports)")
    ax.legend(loc="upper left", ncol=2)
    ax.tick_params(axis="x", length=0)
    fig.savefig(Path(figures_dir) / "t11_regex_v2_recall.png")
    plt.close(fig)


def fig_distribution(dist, errors, figures_dir):
    """t12: error distribution (10 % bins), malfunction-only vs serious pairs, Abbott and Dexcom."""
    labs = bin_labels(SIGNED_EDGES)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.9), sharey=True)
    for ax, b in zip(axes, ["Abbott", "Dexcom"]):
        for g in ("serious", "malfunction"):
            d = dist[(dist["brand"] == b) & (dist["group"] == g)].set_index("error_pct_bin").reindex(labs)
            if d["pairs"].sum() == 0:
                continue
            n = int(d["pairs"].sum())
            med = errors[(errors["brand"] == b) & (errors["group"] == g)]["median_pct"]
            med = float(med.iloc[0]) if len(med) else np.nan
            ax.step(np.arange(len(labs)), d["share_pct"].to_numpy(), where="mid", color=GROUP_COLORS[g], linewidth=2,
                    label=f"{g} (n = {n:,}; median {med:+.0f} %)")
        ax.axvline(10 - 0.5, color=AXIS, linewidth=1, linestyle="--", zorder=1)
        ax.set_title(f"{b}: pairs that state both values")
        ticks = list(range(0, len(labs), 2))
        ax.set_xticks(ticks)
        ax.set_xticklabels([SIGNED_EDGES[i] if SIGNED_EDGES[i] < 200 else "200" for i in ticks], fontsize=8.5)
        ax.set_xlabel("Sensor error, % of the meter value (10 % bins; left of the dashed line = reads low)")
        ax.tick_params(axis="x", length=0)
        ax.legend(loc="upper right")
    axes[0].set_ylabel("Share of pairs, %")
    fig.suptitle("Reported sensor errors: malfunction-only reports vs death/injury reports", x=0.01, ha="left", fontsize=10.5, fontweight="semibold", color=INK)
    fig.tight_layout()
    fig.savefig(Path(figures_dir) / "t12_malfunction_vs_serious_errors.png")
    plt.close(fig)


def fig_gradient(grad, figures_dir, min_n=50):
    """t13: share of pairs that sit in a death/injury report, by signed error band, Abbott vs Dexcom."""
    labs = bin_labels(SIGNED_EDGES)
    fig, ax = plt.subplots(figsize=(9.5, 4.0))
    x = np.arange(len(labs))
    for b in ("Abbott", "Dexcom"):
        d = grad[(grad["brand"] == b) & (grad["direction"] == "both")].set_index("error_band").reindex(labs)
        y = d["share_serious_pct"].where(d["pairs"] >= min_n).to_numpy(float)
        lo = d["ci_low"].where(d["pairs"] >= min_n).to_numpy(float)
        hi = d["ci_high"].where(d["pairs"] >= min_n).to_numpy(float)
        ax.fill_between(x, lo, hi, color=BRAND_COLORS[b], alpha=0.15, linewidth=0)
        ax.plot(x, y, color=BRAND_COLORS[b], marker="o", markersize=4, label=f"{b} (bands with {min_n}+ pairs)")
        ref = float(d["brand_overall_share_serious_pct"].dropna().iloc[0]) if d["brand_overall_share_serious_pct"].notna().any() else np.nan
        ax.axhline(ref, color=BRAND_COLORS[b], linewidth=1, linestyle="--", alpha=0.8)
        ax.text(len(labs) - 0.6, ref + 1.2, f"{b} overall {ref:.0f} %", color=BRAND_COLORS[b], fontsize=8.5, ha="right")
    ax.axvline(10 - 0.5, color=AXIS, linewidth=1, linestyle=":", zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels([l.replace(" to ", "..") for l in labs], rotation=45, ha="right", fontsize=8)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Pairs in a death/injury report, %")
    ax.set_xlabel("Sensor error band, % of the meter value (negative = reads low)")
    ax.set_title("Does the size of the error predict a harm code? Share of pairs filed as death/injury, per error band")
    ax.legend(loc="lower left")
    ax.tick_params(axis="x", length=0)
    fig.tight_layout()
    fig.savefig(Path(figures_dir) / "t13_harm_gradient.png")
    plt.close(fig)


# ----------------------------------------------------------------------------
def main(a=None):
    if a is None:
        ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
        ap.add_argument("--out", default=str(FDA / "clean" / "regex_v2_full.csv.gz"))
        ap.add_argument("--full-parquet", default=str(FDA / "clean" / "full.parquet"))
        ap.add_argument("--sample-parquet", default=str(FDA / "clean" / "sample_local.parquet"))
        ap.add_argument("--tables-dir", default=str(FDA / "results" / "text" / "tables"))
        ap.add_argument("--figures-dir", default=str(FDA / "results" / "text" / "figures"))
        ap.add_argument("--max-rows", type=int, default=None)
        a = ap.parse_args()
    tables, figures = Path(a.tables_dir), Path(a.figures_dir)
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    df = load_full(a.out, getattr(a, "max_rows", None))
    df = add_fda_fields(df, a.full_parquet)

    cov = coverage_table(df)
    cov.to_csv(tables / "h_full_coverage.csv", index=False)
    pat = pattern_table(df)
    pat.to_csv(tables / "h_full_pairs_by_pattern.csv", index=False)
    err = errors_table(df)
    err.to_csv(tables / "h_malf_vs_serious_errors.csv", index=False)
    tst = tests_table(df)
    tst.to_csv(tables / "h_malf_vs_serious_tests.csv", index=False)
    dist = distribution_table(df)
    dist.to_csv(tables / "h_error_distribution.csv", index=False)
    byy = by_year_table(df)
    byy.to_csv(tables / "h_by_year.csv", index=False)
    grad = gradient_table(df, SIGNED_EDGES, "error_pct")
    grad.to_csv(tables / "h_harm_gradient.csv", index=False)
    grad_abs = gradient_table(df, ABS_EDGES, "abs_pct", by_direction=True)
    grad_abs.to_csv(tables / "h_harm_gradient_abs.csv", index=False)
    gtxt = gradient_text_table(df)
    gtxt.to_csv(tables / "h_harm_gradient_text.csv", index=False)
    oc = outcome_coding_table(df)
    oc.to_csv(tables / "h_outcome_coding.csv", index=False)
    wc = weighted_check_table(df, a.sample_parquet)
    wc.to_csv(tables / "h_weighted_check.csv", index=False)
    log("tables written")

    fig_recall(tables, figures)
    fig_distribution(dist, err, figures)
    fig_gradient(grad, figures)
    log("figures written")

    # key numbers for the memo
    p = df[df["pair"]]
    stats = {"reports": int(len(df)), "reports_with_text": int(df["has_text"].sum()), "pairs": int(len(p)),
             "pairs_by_group": p["group"].value_counts().to_dict(),
             "pairs_by_brand_group": {f"{b} {g}": int(((p["brand"] == b) & (p["group"] == g)).sum()) for b in BRANDS for g in ("serious", "malfunction")},
             "bound_pairs": int((df["bound_pattern"].astype(str) != "").sum()),
             "display_word_reports": int((df["sensor_display_word"].astype(str) != "").sum()),
             "two_sensor_readings_reports": int(df["two_sensor_readings"].sum()),
             "wear_day_reports": int(df["wear_day"].notna().sum()), "zone_reports": int((df["zone_stated"].astype(str) != "").sum()),
             "same_sentence_share_of_pairs_pct": round(100 * float(p["same_sentence"].mean()), 1) if len(p) else None}
    (tables / "h_regex_v2_stats.json").write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")
    log("done")
    print(err[err["group"].isin(["malfunction", "serious"])][["brand", "group", "n_pairs", "median_pct", "q1_pct", "q3_pct", "pct_reads_low", "pct_meter_under_70", "pct_abs_over_40"]].to_string(index=False))
    print(grad[(grad["direction"] == "both") & (grad["brand"].isin(["Abbott", "Dexcom"]))][["brand", "error_band", "pairs", "share_serious_pct", "ci_low", "ci_high", "brand_overall_share_serious_pct"]].to_string(index=False))
    print(wc.to_string(index=False) if len(wc) else "no weighted check")


if __name__ == "__main__":
    main()
