#!/usr/bin/env python
"""
brand_comparison.py : brand-vs-brand comparison of the wrong-reading complaints, plus a demographics cut
(BMEN 600 Group 24, Phase 1 text results).

What it does
- Loads the same files as text_results.py (it imports that script's loading code): the model output
  (clean/text_extract_v3.jsonl), the run set (clean/run_set.csv.gz), the pattern-layer table (clean/regex_run_set.csv)
  and the FDA problem-code family map. Adds patient age and sex from clean/serious.csv.gz and clean/sample_local.parquet.
- Comparison set = reports whose fault is a wrong reading, by the text (fault type reads low / reads high / erratic /
  stuck) OR by the FDA problem codes (family "Wrong readings (accuracy)"). Direction and error size always come from
  the two stated numbers (sensor minus meter), never from the model's label.
- Brands: Abbott, Dexcom, Medtronic (caution: undercounted under pump codes, weakest validation), Senseonics (Eversense;
  split out of "Other" because it has enough reports). What is left stays "Other": counted, not tested.
- Compares the brands on error size, direction, meter band (where the true glucose was), Parkes zone, wear day,
  fingerstick check, user action, outcome (model and FDA codes) and report year. Tests and effect sizes:
    sizes  : Kruskal-Wallis across brands; Mann-Whitney per pair; Cliff's delta; bootstrap 95 % CIs
    shares : chi-square; Cramer's V; risk differences per pair with bootstrap 95 % CIs
- Confound checks: (a) Abbott template vs prose pairs; (b) serious reports vs the weighted malfunction sample;
  (c) report year and the two Libre 3 recall windows.
- Demographics: fill rates of age and sex, age and sex per brand, the same cuts by age group and sex, filled vs unfilled.
- Writes tables g_*.csv to results/text/tables/, figures t7 to t10 to results/text/figures/, g_key_tables.md and
  g_brand_comparison_stats.json. Never touches the a_ to f_ tables.

Usage (from the repo root; Windows: plain `python`)
  python fda-maude/scripts/brand_comparison.py
  python fda-maude/scripts/brand_comparison.py --n-boot 200      # faster test
All paths are arguments; see --help. Deterministic: seed 20261106, 1,000 bootstrap resamples.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text_results as tr  # noqa: E402  (loading code, helpers, palette and rcParams)

log = tr.log
REPO = tr.REPO
KEY = "mdr_report_key"

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
SEED = 20261106
N_BOOT_DEFAULT = 1000
MIN_N_TEST = 20                      # no test below this many rows in a group
BRANDS = ["Abbott", "Dexcom", "Medtronic", "Senseonics"]
ALL_BRANDS = BRANDS + ["Other"]
BRAND_LABEL = {"Abbott": "Abbott", "Dexcom": "Dexcom", "Medtronic": "Medtronic (caution)",
               "Senseonics": "Senseonics (Eversense)", "Other": "Other makers"}
BRAND_COLORS = {"Abbott": tr.C_BLUE, "Dexcom": tr.C_ORANGE, "Medtronic": tr.C_AQUA, "Senseonics": "#eda100", "Other": tr.MUTED}
WRONG_TEXT = ["reads_low", "reads_high", "erratic", "stuck"]
METER_BANDS = [("<54", 0.0, 54.0), ("54-69", 54.0, 70.0), ("70-180", 70.0, 180.0001), ("181-250", 180.0001, 250.0001), (">250", 250.0001, np.inf)]
AGE_GROUPS = [("<18", 0.0, 18.0), ("18-39", 18.0, 40.0), ("40-64", 40.0, 65.0), ("65+", 65.0, 200.0)]
AGE_MAX = 110.0
WEAR_BANDS = [("day 1", 1, 2), ("days 2-3", 2, 4), ("days 4-7", 4, 8), ("days 8-10", 8, 11), ("days 11-14", 11, 15), ("day 15+", 15, 10_000)]
# Recall windows, by the date FDA received the report (texts arrive months after the event)
RECALL_WINDOWS = [("W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23)", "20240724", "20250123"),
                  ("W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward)", "20251124", "20991231")]
WINDOW_SHORT = {RECALL_WINDOWS[0][0]: "W1", RECALL_WINDOWS[1][0]: "W2"}
YEAR_MIN, YEAR_MAX = 2018, 2026
FDA_CODES = tr.FDA_OUTCOME_ORDER                 # Required Intervention, Hospitalization, Life Threatening, Death, Other, Disability
PRODUCT_LINES = [("LIBRE 3 PLUS", "Libre 3 Plus"), ("LIBRE 3", "Libre 3"), ("LIBRE 2 PLUS", "Libre 2 Plus"), ("LIBRE 2", "Libre 2"),
                 ("LIBRE 14", "Libre 14 day"), ("LIBRE", "Libre (other)"), ("G7", "Dexcom G7"), ("G6", "Dexcom G6"), ("G5", "Dexcom G5"),
                 ("G4", "Dexcom G4"), ("EVERSENSE", "Eversense"), ("SIMPLERA", "Simplera"), ("GUARDIAN", "Guardian")]
SENSOR_BANDS = METER_BANDS


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def band_of(values, bands, missing="not filled"):
    """Label each number with its band (lower edge included, upper edge excluded)."""
    v = np.asarray(values, float)
    out = np.full(len(v), missing, dtype=object)
    for lab, lo, hi in bands:
        out[(v >= lo) & (v < hi)] = lab
    return out


def brand_of(maker, manufacturer, brand_name):
    """Brand label: text_results' maker, with Senseonics (Eversense) split out of 'Other'."""
    s = f"{manufacturer or ''} {brand_name or ''}".upper()
    if maker == "Other" and ("SENSEONICS" in s or "EVERSENSE" in s):
        return "Senseonics"
    return maker if maker in BRANDS else "Other"


def product_line_of(brand_name):
    s = str(brand_name or "").upper()
    for pat, lab in PRODUCT_LINES:
        if pat in s:
            return lab
    return "unspecified"


def window_of(date_received):
    """Recall window label by date received, or 'outside the windows'."""
    d = date_received.fillna("")
    out = pd.Series("outside the windows", index=d.index, dtype=object)
    for lab, lo, hi in RECALL_WINDOWS:
        out[(d >= lo) & (d <= hi)] = lab
    return out


def size_word_delta(d):
    """Plain word for a Cliff's delta (Romano 2006 cut-offs)."""
    if d is None or np.isnan(d):
        return ""
    a = abs(d)
    return "negligible" if a < 0.147 else "small" if a < 0.33 else "medium" if a < 0.474 else "large"


def size_word_v(v):
    """Plain word for a Cramer's V."""
    if v is None or np.isnan(v):
        return ""
    return "negligible" if v < 0.1 else "small" if v < 0.3 else "medium" if v < 0.5 else "large"


def p_word(p):
    if p is None or np.isnan(p):
        return ""
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


# ----------------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------------
def cliffs_delta(x, y):
    """Cliff's delta = P(x > y) - P(x < y). +1: every x is above every y. 0: no difference. -1: every x below."""
    x = np.asarray(x, float)
    y = np.sort(np.asarray(y, float))
    n_below = np.searchsorted(y, x, side="left")              # y values below each x
    n_above = len(y) - np.searchsorted(y, x, side="right")    # y values above each x
    return float((n_below.sum() - n_above.sum()) / (len(x) * len(y)))


def size_test(x, y, rng, n_boot):
    """Two groups of numbers (a = x, b = y): medians, median difference, Cliff's delta, bootstrap 95 % CIs,
    Mann-Whitney p. Bootstrap = resample each group with replacement n_boot times."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    out = {"n_a": int(len(x)), "n_b": int(len(y)),
           "median_a": float(np.median(x)) if len(x) else np.nan, "median_b": float(np.median(y)) if len(y) else np.nan,
           "iqr_a": f"{np.percentile(x, 25):.0f} to {np.percentile(x, 75):.0f}" if len(x) else "",
           "iqr_b": f"{np.percentile(y, 25):.0f} to {np.percentile(y, 75):.0f}" if len(y) else "",
           "median_diff_a_minus_b": np.nan, "median_diff_ci_low": np.nan, "median_diff_ci_high": np.nan,
           "cliffs_delta": np.nan, "cliffs_delta_ci_low": np.nan, "cliffs_delta_ci_high": np.nan,
           "effect_size_word": "", "mann_whitney_p": np.nan, "p_text": "too few"}
    if len(x) < MIN_N_TEST or len(y) < MIN_N_TEST:
        return out
    out["median_diff_a_minus_b"] = out["median_a"] - out["median_b"]
    out["cliffs_delta"] = cliffs_delta(x, y)
    boot = np.empty((n_boot, 2))
    for b in range(n_boot):
        xb = x[rng.integers(0, len(x), len(x))]
        yb = y[rng.integers(0, len(y), len(y))]
        boot[b, 0] = np.median(xb) - np.median(yb)
        boot[b, 1] = cliffs_delta(xb, yb)
    out["median_diff_ci_low"], out["median_diff_ci_high"] = (float(v) for v in np.percentile(boot[:, 0], [2.5, 97.5]))
    out["cliffs_delta_ci_low"], out["cliffs_delta_ci_high"] = (float(v) for v in np.percentile(boot[:, 1], [2.5, 97.5]))
    out["effect_size_word"] = size_word_delta(out["cliffs_delta"])
    out["mann_whitney_p"] = float(stats.mannwhitneyu(x, y, alternative="two-sided").pvalue)
    out["p_text"] = p_word(out["mann_whitney_p"])
    return out


def share_test(k_a, n_a, k_b, n_b, rng, n_boot):
    """Two shares (k of n): shares in %, risk difference in points, bootstrap 95 % CI, chi-square p (2 x 2)."""
    out = {"n_a": int(n_a), "n_b": int(n_b), "share_a_pct": 100.0 * k_a / n_a if n_a else np.nan,
           "share_b_pct": 100.0 * k_b / n_b if n_b else np.nan, "risk_diff_points": np.nan,
           "risk_diff_ci_low": np.nan, "risk_diff_ci_high": np.nan, "chi_square_p": np.nan, "p_text": "too few"}
    if n_a < MIN_N_TEST or n_b < MIN_N_TEST:
        return out
    out["risk_diff_points"] = out["share_a_pct"] - out["share_b_pct"]
    a = rng.binomial(int(n_a), k_a / n_a, n_boot) / n_a
    b = rng.binomial(int(n_b), k_b / n_b, n_boot) / n_b
    d = 100.0 * (a - b)
    out["risk_diff_ci_low"], out["risk_diff_ci_high"] = (float(v) for v in np.percentile(d, [2.5, 97.5]))
    tab = np.array([[k_a, n_a - k_a], [k_b, n_b - k_b]], float)
    if (tab.sum(0) > 0).all():
        out["chi_square_p"] = float(stats.chi2_contingency(tab, correction=False)[1])
    out["p_text"] = p_word(out["chi_square_p"])
    return out


def kw_test(groups):
    """Kruskal-Wallis across groups of numbers: H, p, epsilon-squared (effect size, 0 = no difference)."""
    gs = []
    for g in groups:
        g = np.asarray(g, float)
        g = g[~np.isnan(g)]
        if len(g) >= MIN_N_TEST:
            gs.append(g)
    out = {"k_groups": len(gs), "n": int(sum(len(g) for g in gs)), "kruskal_H": np.nan, "kruskal_p": np.nan, "epsilon_squared": np.nan, "p_text": "too few"}
    if len(gs) < 2:
        return out
    H, p = stats.kruskal(*gs)
    k, n = len(gs), out["n"]
    out.update({"kruskal_H": float(H), "kruskal_p": float(p), "epsilon_squared": float(max((H - k + 1) / (n - k), 0.0)), "p_text": p_word(p)})
    return out


def chi2_test(table):
    """Chi-square test of a counts table (rows = groups, columns = categories): chi2, df, p, Cramer's V.
    Groups (rows) with fewer than MIN_N_TEST reports are left out of the test; k_groups says how many were tested."""
    t = np.asarray(table, float)
    if t.ndim == 2:
        t = t[t.sum(1) >= MIN_N_TEST]
        t = t[:, t.sum(0) > 0] if t.size else t
    out = {"n": float(t.sum()) if t.size else 0.0, "k_groups": int(t.shape[0]) if t.ndim == 2 else 0, "chi2": np.nan, "df": np.nan,
           "chi_square_p": np.nan, "cramers_v": np.nan, "effect_size_word": "", "p_text": "too few"}
    if t.ndim < 2 or t.shape[0] < 2 or t.shape[1] < 2:
        return out
    chi2, p, dof, _ = stats.chi2_contingency(t, correction=False)
    v = float(np.sqrt(chi2 / (t.sum() * (min(t.shape) - 1))))
    out.update({"chi2": float(chi2), "df": int(dof), "chi_square_p": float(p), "cramers_v": v, "effect_size_word": size_word_v(v), "p_text": p_word(p)})
    return out


def wpct(sub, mask, w=None):
    """Weighted share (%) of rows where mask is True."""
    w = tr.weights_of(sub) if w is None else w
    return tr.wshare(np.asarray(mask, bool), w) if len(sub) else np.nan


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def load_run_set_ext(path):
    """text_results' run-set columns plus the manufacturer (needed to split Senseonics out of 'Other')."""
    cols = ["mdr_report_key", "date_received", "date_of_event", "event_type", "product_code", "brand_name", "manufacturer",
            "product_problems", "patient_outcome", "tier", "weight", "maker"]
    rs = pd.read_csv(path, usecols=cols, dtype=str)
    rs["weight"] = pd.to_numeric(rs["weight"], errors="coerce").fillna(1.0)
    rs["is_libre3"] = rs["brand_name"].fillna("").str.upper().str.contains("LIBRE 3")
    log(f"run set: {len(rs):,} rows")
    return rs


def load_demographics(serious_path, sample_path):
    """Patient age (years) and sex per report, from the clean serious table and the local sample."""
    cols = [KEY, "patient_age_value", "patient_age_unit", "patient_sex", "reporter_occupation_code"]
    parts = []
    if serious_path and Path(serious_path).exists():
        parts.append(pd.read_csv(serious_path, usecols=cols, dtype=str))
        log(f"serious table read for demographics: {len(parts[-1]):,} rows")
    if sample_path and Path(sample_path).exists():
        sm = pd.read_parquet(sample_path, columns=cols)
        for c in cols:
            sm[c] = sm[c].map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v))
        parts.append(sm)
        log(f"sample parquet read for demographics: {len(sm):,} rows")
    if not parts:
        return pd.DataFrame(columns=[KEY, "age_years", "age_group", "sex", "age_filled", "sex_filled", "reporter"])
    d = pd.concat(parts, ignore_index=True).drop_duplicates(KEY)
    val = pd.to_numeric(d["patient_age_value"], errors="coerce")
    unit = d["patient_age_unit"].fillna("").str.upper().str.strip()
    factor = unit.map({"YR": 1.0, "MO": 1 / 12.0, "DA": 1 / 365.25, "WK": 1 / 52.18})
    age = val * factor
    age[(age < 0) | (age > AGE_MAX)] = np.nan
    d["age_years"] = age
    d["age_group"] = band_of(age, AGE_GROUPS)
    sex = d["patient_sex"].fillna("").str.strip().str.title()
    d["sex"] = np.where(sex.isin(["Female", "Male"]), sex, np.where(sex == "", "not filled", "undisclosed"))
    d["age_filled"] = age.notna()
    d["sex_filled"] = d["sex"].isin(["Female", "Male"])
    occ = d["reporter_occupation_code"].fillna("").str.upper()
    d["reporter"] = np.where(occ.str.contains("PATIENT|FAMILY|FRIEND|CAREGIVER"), "patient or family",
                             np.where(occ.str.contains("PHYSICIAN|NURSE|PHARMACIST|HEALTH|RISK"), "health professional",
                                      np.where(occ == "", "not filled", "other / code only")))
    return d[[KEY, "age_years", "age_group", "sex", "age_filled", "sex_filled", "reporter"]]


def build_frame(args):
    df = tr.load_jsonl(args.jsonl, args.max_rows)
    rs = load_run_set_ext(args.run_set)
    rx = tr.load_regex(args.regex)
    df = df.merge(rs.drop(columns=["event_type", "maker"]), on=KEY, how="left").merge(rx, on=KEY, how="left")
    df["weight"] = df["weight"].fillna(1.0)
    df["split"] = df["split"].fillna(df["tier"])
    df["is_libre3"] = df["is_libre3"].fillna(False).astype(bool)
    df = tr.add_code_flags(df, tr.load_family_map(args.family_map))
    df["brand"] = [brand_of(m, mf, b) for m, mf, b in zip(df["maker"], df["manufacturer"], df["brand_name"])]
    df["wr_text"] = df["fault_type"].isin(WRONG_TEXT)
    df["wr_code"] = df["code_wrong_family"].fillna(False).astype(bool)
    df["wr"] = df["wr_text"] | df["wr_code"]
    df["year"] = pd.to_numeric(df["date_received"].str[:4], errors="coerce")
    df["window"] = window_of(df["date_received"])
    df["product_line"] = df["brand_name"].map(product_line_of)
    df["template"] = np.where(df["regex_template"] == "abbott_template", "Abbott template", "prose")
    flags = df["patient_outcome"].map(tr.fda_outcome_flags)
    for code in FDA_CODES:
        df[tr.fda_key(code)] = flags.map(lambda f, c=code: c in f)
    df["fda_none_stated"] = flags.map(lambda f: len(f) == 0)
    df["wear_band"] = band_of(df["wear_day"], WEAR_BANDS)
    demo = load_demographics(args.serious, args.sample_parquet)
    df = df.merge(demo, on=KEY, how="left")
    df["age_group"] = df["age_group"].fillna("not filled")
    df["sex"] = df["sex"].fillna("not filled")
    df["age_filled"] = df["age_filled"].fillna(False).astype(bool)
    df["sex_filled"] = df["sex_filled"].fillna(False).astype(bool)
    df["reporter"] = df["reporter"].fillna("not filled")
    log(f"merged: {len(df):,} reports; wrong-reading set {int(df['wr'].sum()):,} "
        f"(serious {int((df['wr'] & (df['split'] == 'serious')).sum()):,}); demographics matched for {int(df['age_years'].notna().sum()):,} ages")
    return df


def pairs_from(df):
    p, n_drop = tr.pairs_frame(df)
    p["abs_err_pct"] = p["err_pct"].abs()
    p["meter_band"] = band_of(p["meter"], METER_BANDS)
    p["sensor_band"] = band_of(p["sensor"], SENSOR_BANDS)
    p["zone_de_computed"] = pd.Series(p["zone_computed"]).isin(["D", "E"]).to_numpy()
    p["meter_under_70"] = p["meter"] < 70
    p["meter_over_250"] = p["meter"] > 250
    p["sensor_under_70"] = p["sensor"] < 70
    p["false_low_70"] = (p["sensor"] < 70) & (p["meter"] >= 70)
    p["missed_low_70"] = (p["sensor"] >= 70) & (p["meter"] < 70)
    return p, n_drop


# ----------------------------------------------------------------------------
# 1. The comparison set
# ----------------------------------------------------------------------------
def counts_table(df, p):
    rows = []
    for tier in ["serious", "sample"]:
        for b in ALL_BRANDS + ["All"]:
            sub = df[(df["split"] == tier) & ((df["brand"] == b) if b != "All" else True)]
            if sub.empty:
                continue
            w = tr.weights_of(sub)
            ps = p[(p["split"] == tier) & ((p["brand"] == b) if b != "All" else True)]
            r = {"tier": tier if tier == "serious" else "sample (weighted)", "brand": BRAND_LABEL.get(b, b),
                 "reports_in_run_set": len(sub), "weighted_reports": round(float(w.sum())),
                 "wrong_reading_by_text": int(sub["wr_text"].sum()), "wrong_reading_by_code": int(sub["wr_code"].sum()),
                 "wrong_reading_by_both": int((sub["wr_text"] & sub["wr_code"]).sum()),
                 "wrong_reading_either": int(sub["wr"].sum()), "wrong_reading_either_weighted": round(float(w[sub["wr"].to_numpy()].sum())),
                 "pct_of_reports_wrong_reading": wpct(sub, sub["wr"]),
                 "pct_text_only": wpct(sub[sub["wr"]], sub.loc[sub["wr"], "wr_text"] & ~sub.loc[sub["wr"], "wr_code"]) if sub["wr"].any() else np.nan,
                 "pct_code_only": wpct(sub[sub["wr"]], ~sub.loc[sub["wr"], "wr_text"] & sub.loc[sub["wr"], "wr_code"]) if sub["wr"].any() else np.nan,
                 "pairs_both_values": len(ps), "pairs_in_wrong_reading_set": int(ps["wr"].sum()),
                 "pct_of_wrong_reading_reports_with_pair": 100.0 * ps["wr"].sum() / sub["wr"].sum() if sub["wr"].sum() else np.nan}
            rows.append(r)
    return pd.DataFrame(rows)


def other_makers_table(df):
    sub = df[(df["split"] == "serious") & df["wr"] & (df["brand"] == "Other")]
    vc = sub["manufacturer"].fillna("").str.upper().str.replace(r"[.,]", "", regex=True).str.strip().value_counts().head(12)
    return pd.DataFrame({"manufacturer": vc.index, "wrong_reading_serious_reports": vc.values})


# ----------------------------------------------------------------------------
# 2. Error sizes and distributions
# ----------------------------------------------------------------------------
def describe(sub, w=None):
    """Error-size summary of a pairs frame (weighted where w is given)."""
    w = tr.weights_of(sub) if w is None else np.asarray(w, float)
    d = tr.describe_errors(sub, w)
    d["median_abs_err_pct"] = tr.wquantile(sub["abs_err_pct"], w, 0.5) if len(sub) else np.nan
    d["pct_meter_under_70"] = wpct(sub, sub["meter_under_70"], w) if len(sub) else np.nan
    d["pct_meter_over_250"] = wpct(sub, sub["meter_over_250"], w) if len(sub) else np.nan
    d["pct_sensor_under_70"] = wpct(sub, sub["sensor_under_70"], w) if len(sub) else np.nan
    d["pct_zone_DE_computed"] = wpct(sub, sub["zone_de_computed"], w) if len(sub) else np.nan
    return d


def error_size_tables(pw, rng, n_boot):
    """pw = pairs in the wrong-reading set. Descriptives per brand (serious and weighted sample; all / low / high),
    full percentile table, Kruskal-Wallis across brands and pairwise Mann-Whitney tests."""
    rows = []
    for tier in ["serious", "sample"]:
        for b in ALL_BRANDS + ["All"]:
            base = pw[(pw["split"] == tier) & ((pw["brand"] == b) if b != "All" else True)]
            for dname, dsub in (("all pairs", base), ("sensor below meter", base[base["direction"] == "low"]), ("sensor above meter", base[base["direction"] == "high"])):
                if len(dsub) == 0:
                    continue
                r = {"tier": tier if tier == "serious" else "sample (weighted)", "brand": BRAND_LABEL.get(b, b), "pairs": dname}
                r.update(describe(dsub))
                rows.append(r)
    desc = pd.DataFrame(rows)
    # percentiles (serious, all directions)
    prow = []
    ser = pw[pw["split"] == "serious"]
    for b in ALL_BRANDS + ["All"]:
        sub = ser[(ser["brand"] == b)] if b != "All" else ser
        if len(sub) == 0:
            continue
        for col, name in (("err_pct", "error, % of meter"), ("err_mgdl", "error, mg/dL"), ("abs_err_pct", "absolute error, % of meter")):
            v = sub[col].to_numpy(float)
            r = {"brand": BRAND_LABEL.get(b, b), "measure": name, "n": len(sub)}
            for q in (1, 5, 10, 25, 50, 75, 90, 95, 99):
                r[f"p{q}"] = float(np.percentile(v, q))
            prow.append(r)
    pct = pd.DataFrame(prow)
    # Kruskal-Wallis across the four brands (serious)
    kw_rows = []
    for dname, dsub in (("all pairs", ser), ("sensor below meter", ser[ser["direction"] == "low"]), ("sensor above meter", ser[ser["direction"] == "high"])):
        for col, name in (("err_pct", "error, % of meter"), ("err_mgdl", "error, mg/dL"), ("abs_err_pct", "absolute error, % of meter"),
                          ("meter", "meter value, mg/dL"), ("sensor", "sensor value, mg/dL")):
            groups = [dsub.loc[dsub["brand"] == b, col] for b in BRANDS]
            r = {"pairs": dname, "measure": name}
            for b, g in zip(BRANDS, groups):
                r[f"median_{b}"] = float(np.median(g)) if len(g) else np.nan
                r[f"n_{b}"] = int(len(g))
            r.update(kw_test(groups))
            kw_rows.append(r)
    kw = pd.DataFrame(kw_rows)
    # pairwise tests
    pw_rows = []
    pairs_of_brands = [(a, b) for i, a in enumerate(BRANDS) for b in BRANDS[i + 1:]]
    for dname, dsub in (("all pairs", ser), ("sensor below meter", ser[ser["direction"] == "low"]), ("sensor above meter", ser[ser["direction"] == "high"])):
        for col, name in (("err_pct", "error, % of meter"), ("err_mgdl", "error, mg/dL"), ("abs_err_pct", "absolute error, % of meter"), ("meter", "meter value, mg/dL")):
            if dname != "all pairs" and col in ("abs_err_pct", "meter"):
                continue
            for a, b in pairs_of_brands:
                r = {"pairs": dname, "measure": name, "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
                r.update(size_test(dsub.loc[dsub["brand"] == a, col], dsub.loc[dsub["brand"] == b, col], rng, n_boot))
                pw_rows.append(r)
    pairwise = pd.DataFrame(pw_rows)
    # binned distribution (serious, err_pct), for the record
    edges = [-100, -90, -80, -70, -60, -50, -40, -30, -20, -10, 0, 10, 20, 40, 60, 100, 150, 200, 300, 500, 1e9]
    labels = [f"{edges[i]} to {edges[i+1]}" if edges[i + 1] < 1e8 else f"over {edges[i]}" for i in range(len(edges) - 1)]
    brow = []
    for b in BRANDS:
        v = ser.loc[ser["brand"] == b, "err_pct"].to_numpy(float)
        if len(v) == 0:
            continue
        h, _ = np.histogram(np.clip(v, -100, 1e8), bins=edges)
        for lab, c in zip(labels, h):
            brow.append({"brand": BRAND_LABEL[b], "error_pct_bin": lab, "n": int(c), "pct_of_brand_pairs": 100.0 * c / len(v)})
    bins = pd.DataFrame(brow)
    return desc, pct, kw, pairwise, bins


# ----------------------------------------------------------------------------
# 3. Shares: direction, bands, zones, wear day, fingerstick, action, outcome, FDA codes
# ----------------------------------------------------------------------------
def share_block(groups, col, cats, variable, base, test_cats=None):
    """groups: list of (brand, frame). Returns (rows: one per category with n and % per brand, test dict)."""
    rows = []
    counts = []
    test_cats = test_cats or cats
    for cat in cats:
        r = {"variable": variable, "base": base, "category": cat}
        for b, sub in groups:
            w = tr.weights_of(sub)
            m = (sub[col] == cat).to_numpy()
            r[f"n_{b}"] = int(m.sum())
            r[f"pct_{b}"] = tr.wshare(m, w) if len(sub) else np.nan
        rows.append(r)
    for b, sub in groups:
        counts.append([int((sub[col] == c).sum()) for c in test_cats])
    t = {"variable": variable, "base": base}
    for b, sub in groups:
        t[f"n_{b}"] = int(len(sub))
    t.update(chi2_test(np.array(counts)))
    return rows, t


def share_tables(dfw, pw):
    """dfw = serious wrong-reading reports; pw = serious pairs in the set. Distributions per brand + chi-square tests."""
    rows, tests = [], []
    gp = [(b, pw[pw["brand"] == b]) for b in BRANDS]
    gd = [(b, dfw[dfw["brand"] == b]) for b in BRANDS]
    pd_ = pw[pw["direction"] != "equal"]
    r, t = share_block([(b, pd_[pd_["brand"] == b]) for b in BRANDS], "direction", ["low", "high"], "direction (from the two numbers)", "pairs with a direction")
    rows += r; tests.append(t)
    r, t = share_block(gp, "meter_band", [x[0] for x in METER_BANDS], "meter (true glucose) band, mg/dL", "pairs")
    rows += r; tests.append(t)
    r, t = share_block(gp, "sensor_band", [x[0] for x in SENSOR_BANDS], "sensor reading band, mg/dL", "pairs")
    rows += r; tests.append(t)
    r, t = share_block(gp, "zone_computed", tr.ZONES, "Parkes zone computed from the pair", "pairs")
    rows += r; tests.append(t)
    zs = dfw[dfw["zone_stated"].isin(tr.ZONES)]
    r, t = share_block([(b, zs[zs["brand"] == b]) for b in BRANDS], "zone_stated", tr.ZONES, "Parkes zone stated by the maker", "reports with a stated zone")
    rows += r; tests.append(t)
    wd = dfw[dfw["wear_band"] != "not filled"]
    r, t = share_block([(b, wd[wd["brand"] == b]) for b in BRANDS], "wear_band", [x[0] for x in WEAR_BANDS], "wear day of the failure", "reports with a wear day")
    rows += r; tests.append(t)
    r, t = share_block(gd, "fingerstick", ["yes", "no", "not_stated"], "fingerstick check mentioned", "wrong-reading reports")
    rows += r; tests.append(t)
    r, t = share_block(gd, "user_action", tr.USER_ACTIONS, "user action (model)", "wrong-reading reports")
    rows += r; tests.append(t)
    r, t = share_block(gd, "outcome", tr.OUTCOMES, "outcome severity (model)", "wrong-reading reports")
    rows += r; tests.append(t)
    r, t = share_block(gd, "event_type", ["Injury", "Death"], "FDA event type", "wrong-reading reports")
    rows += r; tests.append(t)
    for code in FDA_CODES + ["none stated"]:
        k = tr.fda_key(code)
        tmp = dfw.assign(_f=np.where(dfw[k], "yes", "no"))
        r, t = share_block([(b, tmp[tmp["brand"] == b]) for b in BRANDS], "_f", ["yes"], f"FDA outcome code: {code}", "wrong-reading reports", test_cats=["yes", "no"])
        rows += r; tests.append(t)
    r, t = share_block(gd, "reporter", ["patient or family", "health professional", "other / code only", "not filled"], "who reported (FDA occupation field)", "wrong-reading reports")
    rows += r; tests.append(t)
    r, t = share_block(gd, "template", ["Abbott template", "prose"], "text form", "wrong-reading reports")
    rows += r; tests.append(t)
    return pd.DataFrame(rows), pd.DataFrame(tests)


def binary_specs():
    """(label, frame kind, column) of the yes/no measures compared pairwise between brands."""
    return [("sensor read low (of pairs with a direction)", "pairs_dir", "is_low"),
            ("meter under 70 (hidden low)", "pairs", "meter_under_70"), ("meter over 250", "pairs", "meter_over_250"),
            ("sensor under 70", "pairs", "sensor_under_70"), ("false low: sensor under 70, meter not", "pairs", "false_low_70"),
            ("missed low: meter under 70, sensor not", "pairs", "missed_low_70"), ("Parkes zone D or E (computed)", "pairs", "zone_de_computed"),
            ("fingerstick check: yes", "reports", "fs_yes"), ("ate carbs", "reports", "ua_carbs"), ("took insulin", "reports", "ua_insulin"),
            ("sought care", "reports", "ua_care"), ("outcome hypoglycaemia (model)", "reports", "oc_hypo"),
            ("outcome hospital or ER (model)", "reports", "oc_hosp"), ("outcome death (model)", "reports", "oc_death"),
            ("FDA event type Death", "reports", "fda_event_death"), ("FDA code Hospitalization", "reports", tr.fda_key("Hospitalization")),
            ("FDA code Required Intervention", "reports", tr.fda_key("Required Intervention")),
            ("FDA code Life Threatening", "reports", tr.fda_key("Life Threatening")), ("FDA code Death", "reports", tr.fda_key("Death"))]


def add_binary_cols(dfw, pw):
    dfw = dfw.copy()
    dfw["fs_yes"] = dfw["fingerstick"] == "yes"
    dfw["ua_carbs"] = dfw["user_action"] == "ate_carbs"
    dfw["ua_insulin"] = dfw["user_action"] == "took_insulin"
    dfw["ua_care"] = dfw["user_action"] == "sought_care"
    dfw["oc_hypo"] = dfw["outcome"] == "hypoglycemia"
    dfw["oc_hosp"] = dfw["outcome"] == "hospital_or_er"
    dfw["oc_death"] = dfw["outcome"] == "death"
    dfw["fda_event_death"] = dfw["event_type"] == "Death"
    pw = pw.copy()
    pw["is_low"] = pw["direction"] == "low"
    return dfw, pw


def pairwise_share_table(dfw, pw, rng, n_boot, group_col="brand", groups=None, label_map=None):
    """Risk differences for the yes/no measures between every pair of groups."""
    dfw, pw = add_binary_cols(dfw, pw)
    groups = groups or BRANDS
    label_map = label_map or BRAND_LABEL
    rows = []
    for lab, kind, col in binary_specs():
        frame = pw[pw["direction"] != "equal"] if kind == "pairs_dir" else (pw if kind == "pairs" else dfw)
        for i, a in enumerate(groups):
            for b in groups[i + 1:]:
                fa, fb = frame[frame[group_col] == a], frame[frame[group_col] == b]
                r = {"measure": lab, "base": "pairs" if kind.startswith("pairs") else "wrong-reading reports", "group_a": label_map.get(a, a), "group_b": label_map.get(b, b)}
                r.update(share_test(int(fa[col].sum()), len(fa), int(fb[col].sum()), len(fb), rng, n_boot))
                rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 4. Confound checks
# ----------------------------------------------------------------------------
def template_tables(dfw, pw, rng, n_boot):
    """(a) Abbott template pairs vs Abbott prose pairs vs Dexcom prose pairs; and template vs prose within all Abbott reports."""
    ab = pw[pw["brand"] == "Abbott"]
    groups = [("Abbott, template pairs", ab[ab["template"] == "Abbott template"]), ("Abbott, prose pairs", ab[ab["template"] == "prose"]),
              ("Dexcom, all pairs (prose)", pw[pw["brand"] == "Dexcom"]), ("Senseonics, all pairs (prose)", pw[pw["brand"] == "Senseonics"])]
    rows = []
    for lab, sub in groups:
        if len(sub) == 0:
            continue
        r = {"group": lab}
        r.update(describe(sub))
        r["pct_fingerstick_yes"] = wpct(sub, sub["fingerstick"] == "yes")
        r["pct_outcome_hospital_or_er"] = wpct(sub, sub["outcome"] == "hospital_or_er")
        r["pct_outcome_none"] = wpct(sub, sub["outcome"] == "none")
        r["pct_fda_death"] = wpct(sub, sub["event_type"] == "Death")
        for lab2, lo, hi in METER_BANDS:
            r[f"pct_meter_{lab2}"] = wpct(sub, sub["meter_band"] == lab2)
        rows.append(r)
    desc = pd.DataFrame(rows)
    tests = []
    g = dict(groups)
    for a, b in (("Abbott, template pairs", "Abbott, prose pairs"), ("Abbott, prose pairs", "Dexcom, all pairs (prose)"),
                 ("Abbott, template pairs", "Dexcom, all pairs (prose)"), ("Abbott, prose pairs", "Senseonics, all pairs (prose)")):
        for col, name in (("err_pct", "error, % of meter"), ("err_mgdl", "error, mg/dL"), ("meter", "meter value, mg/dL")):
            r = {"measure": name, "group_a": a, "group_b": b}
            r.update(size_test(g[a][col], g[b][col], rng, n_boot))
            tests.append(r)
        for col, name in (("err_pct", "error, % of meter: sensor below meter only"),):
            r = {"measure": name, "group_a": a, "group_b": b}
            r.update(size_test(g[a].loc[g[a]["direction"] == "low", col], g[b].loc[g[b]["direction"] == "low", col], rng, n_boot))
            tests.append(r)
        for col, name in (("is_low", "share reading low (of pairs with a direction)"), ("meter_under_70", "share meter under 70"), ("meter_over_250", "share meter over 250"),
                          ("zone_de_computed", "share Parkes D or E (computed)")):
            fa = g[a][g[a]["direction"] != "equal"] if col == "is_low" else g[a]
            fb = g[b][g[b]["direction"] != "equal"] if col == "is_low" else g[b]
            ka = int((fa["direction"] == "low").sum()) if col == "is_low" else int(fa[col].sum())
            kb = int((fb["direction"] == "low").sum()) if col == "is_low" else int(fb[col].sum())
            r = {"measure": name, "group_a": a, "group_b": b}
            r.update(share_test(ka, len(fa), kb, len(fb), rng, n_boot))
            tests.append(r)
    tests = pd.DataFrame(tests)
    # template vs prose within all Abbott wrong-reading reports (not only pairs): what the two text forms report
    abr = dfw[dfw["brand"] == "Abbott"]
    rrows = []
    for lab, sub in (("Abbott template reports", abr[abr["template"] == "Abbott template"]), ("Abbott prose reports", abr[abr["template"] == "prose"]),
                     ("Dexcom reports", dfw[dfw["brand"] == "Dexcom"])):
        r = {"group": lab, "n": len(sub), "pct_with_pair": wpct(sub, sub["sensor"].notna() & sub["meter"].notna()),
             "pct_fault_reads_low": wpct(sub, sub["fault_type"] == "reads_low"), "pct_fault_reads_high": wpct(sub, sub["fault_type"] == "reads_high"),
             "pct_zone_stated": wpct(sub, sub["zone_stated"].isin(tr.ZONES)), "pct_wear_day": wpct(sub, sub["wear_day"].notna()),
             "pct_fingerstick_yes": wpct(sub, sub["fingerstick"] == "yes"), "pct_user_action_stated": wpct(sub, sub["user_action"] != "not_stated"),
             "pct_ate_carbs": wpct(sub, sub["user_action"] == "ate_carbs"), "pct_took_insulin": wpct(sub, sub["user_action"] == "took_insulin"),
             "pct_sought_care": wpct(sub, sub["user_action"] == "sought_care"), "pct_outcome_none": wpct(sub, sub["outcome"] == "none"),
             "pct_outcome_hospital_or_er": wpct(sub, sub["outcome"] == "hospital_or_er"), "pct_outcome_death": wpct(sub, sub["outcome"] == "death"),
             "pct_fda_hospitalization": wpct(sub, sub[tr.fda_key("Hospitalization")]), "pct_fda_required_intervention": wpct(sub, sub[tr.fda_key("Required Intervention")]),
             "pct_fda_death": wpct(sub, sub["event_type"] == "Death"), "pct_age_filled": wpct(sub, sub["age_filled"]), "pct_sex_filled": wpct(sub, sub["sex_filled"]),
             "median_text_chars": float(sub["text_chars"].median()) if len(sub) else np.nan}
        rrows.append(r)
    return desc, tests, pd.DataFrame(rrows)


def tier_tables(df, p, rng, n_boot):
    """(b) Serious reports vs the weighted malfunction sample, per brand: error sizes, direction, text-label direction."""
    rows = []
    for tier in ["serious", "sample"]:
        for b in BRANDS:
            sub = df[(df["split"] == tier) & (df["brand"] == b) & df["wr"]]
            ps = p[(p["split"] == tier) & (p["brand"] == b) & p["wr"]]
            if len(sub) == 0:
                continue
            w = tr.weights_of(sub)
            r = {"tier": tier if tier == "serious" else "sample (weighted)", "brand": BRAND_LABEL[b], "wrong_reading_reports": len(sub),
                 "weighted_reports": round(float(w.sum())), "pct_with_pair": wpct(sub, sub["sensor"].notna() & sub["meter"].notna()),
                 "label_reads_low_pct": wpct(sub, sub["fault_type"] == "reads_low"), "label_reads_high_pct": wpct(sub, sub["fault_type"] == "reads_high"),
                 "label_low_share_of_low_plus_high_pct": (100.0 * w[(sub["fault_type"] == "reads_low").to_numpy()].sum()
                                                         / max(w[sub["fault_type"].isin(["reads_low", "reads_high"]).to_numpy()].sum(), 1e-9)),
                 "code_low_readings_pct": wpct(sub, sub["code_low"]), "code_high_readings_pct": wpct(sub, sub["code_high"]),
                 "pairs": len(ps), "pairs_weighted": round(float(tr.weights_of(ps).sum())) if len(ps) else 0}
            if len(ps):
                d = describe(ps)
                r.update({"median_err_pct": d["median_pct"], "q1_err_pct": d["q1_pct"], "q3_err_pct": d["q3_pct"], "median_err_mgdl": d["median_mgdl"],
                          "pct_low": d["pct_low"], "pct_high": d["pct_high"], "pct_meter_under_70": d["pct_meter_under_70"], "pct_meter_over_250": d["pct_meter_over_250"]})
            rows.append(r)
    desc = pd.DataFrame(rows)
    tests = []
    for tier in ["serious", "sample"]:
        ps = p[(p["split"] == tier) & p["wr"]]
        for a, b in (("Abbott", "Dexcom"), ("Abbott", "Medtronic"), ("Abbott", "Senseonics")):
            r = {"tier": tier + (" (unweighted rows)" if tier == "sample" else ""), "measure": "error, % of meter", "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
            r.update(size_test(ps.loc[ps["brand"] == a, "err_pct"], ps.loc[ps["brand"] == b, "err_pct"], rng, n_boot))
            tests.append(r)
            fa, fb = ps[(ps["brand"] == a) & (ps["direction"] != "equal")], ps[(ps["brand"] == b) & (ps["direction"] != "equal")]
            r = {"tier": tier + (" (unweighted rows)" if tier == "sample" else ""), "measure": "share reading low", "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
            r.update(share_test(int((fa["direction"] == "low").sum()), len(fa), int((fb["direction"] == "low").sum()), len(fb), rng, n_boot))
            tests.append(r)
    return desc, pd.DataFrame(tests)


def year_tables(dfw, pw, rng, n_boot):
    """(c) Year and recall windows: reports and pairs per year and brand; brand tests inside and outside the windows."""
    rows = []
    for y in range(int(dfw["year"].min()), int(dfw["year"].max()) + 1):
        for b in BRANDS:
            sub = dfw[(dfw["year"] == y) & (dfw["brand"] == b)]
            ps = pw[(pw["year"] == y) & (pw["brand"] == b)]
            r = {"year": y, "brand": BRAND_LABEL[b], "wrong_reading_reports": len(sub), "pairs": len(ps),
                 "pct_reports_with_pair": 100.0 * len(ps) / len(sub) if len(sub) else np.nan,
                 "recall_window_in_year": "; ".join(sorted({WINDOW_SHORT[w] for w in sub["window"] if w in WINDOW_SHORT}))}
            if len(ps) >= MIN_N_TEST:
                d = describe(ps)
                r.update({"median_err_pct": d["median_pct"], "q1_err_pct": d["q1_pct"], "q3_err_pct": d["q3_pct"], "pct_low": d["pct_low"],
                          "pct_meter_under_70": d["pct_meter_under_70"], "pct_meter_over_250": d["pct_meter_over_250"]})
            r["pct_fda_death"] = wpct(sub, sub["event_type"] == "Death") if len(sub) else np.nan
            r["pct_outcome_hospital_or_er"] = wpct(sub, sub["outcome"] == "hospital_or_er") if len(sub) else np.nan
            rows.append(r)
    by_year = pd.DataFrame(rows)
    # periods: each window, outside the windows, and all time
    periods = [(w[0], pw["window"] == w[0], dfw["window"] == w[0]) for w in RECALL_WINDOWS]
    periods.append(("outside the windows", pw["window"] == "outside the windows", dfw["window"] == "outside the windows"))
    periods.append(("all time", np.ones(len(pw), bool), np.ones(len(dfw), bool)))
    prow, trow = [], []
    for lab, mp, md in periods:
        sub_p, sub_d = pw[mp], dfw[md]
        for b in BRANDS:
            ps, ds = sub_p[sub_p["brand"] == b], sub_d[sub_d["brand"] == b]
            r = {"period": lab, "brand": BRAND_LABEL[b], "wrong_reading_reports": len(ds), "pairs": len(ps)}
            if len(ps):
                d = describe(ps)
                r.update({"median_err_pct": d["median_pct"], "q1_err_pct": d["q1_pct"], "q3_err_pct": d["q3_pct"], "median_err_mgdl": d["median_mgdl"],
                          "pct_low": d["pct_low"], "pct_high": d["pct_high"], "pct_meter_under_70": d["pct_meter_under_70"], "pct_meter_over_250": d["pct_meter_over_250"],
                          "median_err_pct_low_only": tr.wquantile(ps.loc[ps["direction"] == "low", "err_pct"], np.ones(int((ps["direction"] == "low").sum())), 0.5) if (ps["direction"] == "low").any() else np.nan})
            prow.append(r)
        for a, b in (("Abbott", "Dexcom"), ("Abbott", "Senseonics"), ("Dexcom", "Senseonics"), ("Abbott", "Medtronic")):
            fa, fb = sub_p[sub_p["brand"] == a], sub_p[sub_p["brand"] == b]
            r = {"period": lab, "measure": "error, % of meter", "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
            r.update(size_test(fa["err_pct"], fb["err_pct"], rng, n_boot))
            trow.append(r)
            r = {"period": lab, "measure": "error, % of meter: sensor below meter only", "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
            r.update(size_test(fa.loc[fa["direction"] == "low", "err_pct"], fb.loc[fb["direction"] == "low", "err_pct"], rng, n_boot))
            trow.append(r)
            fa2, fb2 = fa[fa["direction"] != "equal"], fb[fb["direction"] != "equal"]
            r = {"period": lab, "measure": "share reading low", "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
            r.update(share_test(int((fa2["direction"] == "low").sum()), len(fa2), int((fb2["direction"] == "low").sum()), len(fb2), rng, n_boot))
            trow.append(r)
            r = {"period": lab, "measure": "share meter under 70", "brand_a": BRAND_LABEL[a], "brand_b": BRAND_LABEL[b]}
            r.update(share_test(int(fa["meter_under_70"].sum()), len(fa), int(fb["meter_under_70"].sum()), len(fb), rng, n_boot))
            trow.append(r)
    # Abbott vs Dexcom per year
    yrow = []
    for y in range(YEAR_MIN, YEAR_MAX + 1):
        fa, fb = pw[(pw["year"] == y) & (pw["brand"] == "Abbott")], pw[(pw["year"] == y) & (pw["brand"] == "Dexcom")]
        r = {"year": y, "measure": "error, % of meter", "brand_a": "Abbott", "brand_b": "Dexcom"}
        r.update(size_test(fa["err_pct"], fb["err_pct"], rng, n_boot))
        yrow.append(r)
        fa2, fb2 = fa[fa["direction"] != "equal"], fb[fb["direction"] != "equal"]
        r = {"year": y, "measure": "share reading low", "brand_a": "Abbott", "brand_b": "Dexcom"}
        r.update(share_test(int((fa2["direction"] == "low").sum()), len(fa2), int((fb2["direction"] == "low").sum()), len(fb2), rng, n_boot))
        yrow.append(r)
    return by_year, pd.DataFrame(prow), pd.DataFrame(trow), pd.DataFrame(yrow)


def product_line_table(dfw, pw, rng, n_boot):
    rows = []
    for pl in [x[1] for x in PRODUCT_LINES] + ["unspecified"]:
        sub, ps = dfw[dfw["product_line"] == pl], pw[pw["product_line"] == pl]
        if len(sub) < MIN_N_TEST:
            continue
        r = {"product_line": pl, "brand": BRAND_LABEL.get(sub["brand"].mode().iloc[0], ""), "wrong_reading_reports": len(sub), "pairs": len(ps),
             "pct_fda_death": wpct(sub, sub["event_type"] == "Death"), "pct_outcome_hospital_or_er": wpct(sub, sub["outcome"] == "hospital_or_er")}
        if len(ps) >= MIN_N_TEST:
            d = describe(ps)
            r.update({"median_err_pct": d["median_pct"], "q1_err_pct": d["q1_pct"], "q3_err_pct": d["q3_pct"], "median_err_mgdl": d["median_mgdl"],
                      "pct_low": d["pct_low"], "pct_high": d["pct_high"], "pct_meter_under_70": d["pct_meter_under_70"], "pct_meter_over_250": d["pct_meter_over_250"],
                      "pct_zone_DE_computed": d["pct_zone_DE_computed"]})
        rows.append(r)
    tests = []
    for a, b in (("Libre 3", "Libre 2"), ("Libre 3 Plus", "Libre 3"), ("Dexcom G7", "Dexcom G6"), ("Libre 3", "Dexcom G7"), ("Libre 2", "Dexcom G6")):
        fa, fb = pw[pw["product_line"] == a], pw[pw["product_line"] == b]
        r = {"measure": "error, % of meter", "line_a": a, "line_b": b}
        r.update(size_test(fa["err_pct"], fb["err_pct"], rng, n_boot))
        tests.append(r)
        fa2, fb2 = fa[fa["direction"] != "equal"], fb[fb["direction"] != "equal"]
        r = {"measure": "share reading low", "line_a": a, "line_b": b}
        r.update(share_test(int((fa2["direction"] == "low").sum()), len(fa2), int((fb2["direction"] == "low").sum()), len(fb2), rng, n_boot))
        tests.append(r)
    return pd.DataFrame(rows), pd.DataFrame(tests)


# ----------------------------------------------------------------------------
# 5. Demographics
# ----------------------------------------------------------------------------
def fill_tables(df, dfw):
    """Fill rate of age and sex: by brand and tier (wrong-reading set), by model outcome, by FDA event type and codes."""
    rows = []
    for tier in ["serious", "sample"]:
        for b in ALL_BRANDS + ["All"]:
            sub = df[(df["split"] == tier) & df["wr"] & ((df["brand"] == b) if b != "All" else True)]
            if len(sub) == 0:
                continue
            rows.append({"cut": "brand", "tier": tier if tier == "serious" else "sample (weighted)", "group": BRAND_LABEL.get(b, b), "n": len(sub),
                         "pct_age_filled": wpct(sub, sub["age_filled"]), "pct_sex_filled": wpct(sub, sub["sex_filled"]),
                         "pct_both_filled": wpct(sub, sub["age_filled"] & sub["sex_filled"]), "pct_sex_undisclosed": wpct(sub, sub["sex"] == "undisclosed"),
                         "pct_reporter_patient_or_family": wpct(sub, sub["reporter"] == "patient or family")})
    for cat in tr.OUTCOMES:
        sub = dfw[dfw["outcome"] == cat]
        if len(sub) >= MIN_N_TEST:
            rows.append({"cut": "model outcome", "tier": "serious", "group": cat, "n": len(sub), "pct_age_filled": wpct(sub, sub["age_filled"]),
                         "pct_sex_filled": wpct(sub, sub["sex_filled"]), "pct_both_filled": wpct(sub, sub["age_filled"] & sub["sex_filled"])})
    for et in ["Injury", "Death"]:
        sub = dfw[dfw["event_type"] == et]
        if len(sub):
            rows.append({"cut": "FDA event type", "tier": "serious", "group": et, "n": len(sub), "pct_age_filled": wpct(sub, sub["age_filled"]),
                         "pct_sex_filled": wpct(sub, sub["sex_filled"]), "pct_both_filled": wpct(sub, sub["age_filled"] & sub["sex_filled"])})
    for code in FDA_CODES + ["none stated"]:
        sub = dfw[dfw[tr.fda_key(code)]]
        if len(sub) >= MIN_N_TEST:
            rows.append({"cut": "FDA outcome code", "tier": "serious", "group": code, "n": len(sub), "pct_age_filled": wpct(sub, sub["age_filled"]),
                         "pct_sex_filled": wpct(sub, sub["sex_filled"]), "pct_both_filled": wpct(sub, sub["age_filled"] & sub["sex_filled"])})
    for b in BRANDS:
        for et in ["Injury", "Death"]:
            sub = dfw[(dfw["brand"] == b) & (dfw["event_type"] == et)]
            if len(sub) >= MIN_N_TEST:
                rows.append({"cut": "brand x FDA event type", "tier": "serious", "group": f"{BRAND_LABEL[b]} / {et}", "n": len(sub), "pct_age_filled": wpct(sub, sub["age_filled"]),
                             "pct_sex_filled": wpct(sub, sub["sex_filled"]), "pct_both_filled": wpct(sub, sub["age_filled"] & sub["sex_filled"])})
    for y in range(YEAR_MIN, YEAR_MAX + 1):
        sub = dfw[dfw["year"] == y]
        if len(sub) >= MIN_N_TEST:
            rows.append({"cut": "year", "tier": "serious", "group": str(y), "n": len(sub), "pct_age_filled": wpct(sub, sub["age_filled"]),
                         "pct_sex_filled": wpct(sub, sub["sex_filled"]), "pct_both_filled": wpct(sub, sub["age_filled"] & sub["sex_filled"])})
    return pd.DataFrame(rows)


def age_sex_by_brand(dfw, rng, n_boot):
    rows, tests = [], []
    aged = dfw[dfw["age_filled"]]
    for b in BRANDS + ["All"]:
        sub = aged[aged["brand"] == b] if b != "All" else aged
        subs = dfw[(dfw["brand"] == b) if b != "All" else np.ones(len(dfw), bool)]
        sexed = subs[subs["sex_filled"]]
        if len(sub) == 0:
            continue
        a = sub["age_years"].to_numpy(float)
        r = {"brand": BRAND_LABEL.get(b, b), "n_with_age": len(sub), "median_age": float(np.median(a)), "q1_age": float(np.percentile(a, 25)), "q3_age": float(np.percentile(a, 75)),
             "p10_age": float(np.percentile(a, 10)), "p90_age": float(np.percentile(a, 90))}
        for lab, lo, hi in AGE_GROUPS:
            r[f"pct_age_{lab}"] = 100.0 * ((a >= lo) & (a < hi)).mean()
        r["n_with_sex"] = len(sexed)
        r["pct_female_of_filled"] = 100.0 * (sexed["sex"] == "Female").mean() if len(sexed) else np.nan
        rows.append(r)
    desc = pd.DataFrame(rows)
    kw = kw_test([aged.loc[aged["brand"] == b, "age_years"] for b in BRANDS])
    kw.update({"measure": "age, years, across brands"})
    tests.append(kw)
    for i, a in enumerate(BRANDS):
        for b in BRANDS[i + 1:]:
            r = {"measure": "age, years", "group_a": BRAND_LABEL[a], "group_b": BRAND_LABEL[b]}
            r.update(size_test(aged.loc[aged["brand"] == a, "age_years"], aged.loc[aged["brand"] == b, "age_years"], rng, n_boot))
            tests.append(r)
            sa, sb = dfw[(dfw["brand"] == a) & dfw["sex_filled"]], dfw[(dfw["brand"] == b) & dfw["sex_filled"]]
            r = {"measure": "share female (of filled)", "group_a": BRAND_LABEL[a], "group_b": BRAND_LABEL[b]}
            r.update(share_test(int((sa["sex"] == "Female").sum()), len(sa), int((sb["sex"] == "Female").sum()), len(sb), rng, n_boot))
            tests.append(r)
    sex_tab = [[int(((dfw["brand"] == b) & (dfw["sex"] == s)).sum()) for s in ("Female", "Male")] for b in BRANDS]
    ct = chi2_test(np.array(sex_tab))
    ct.update({"measure": "sex (female / male) across brands"})
    tests.append(ct)
    # age-group mix across brands
    ag_tab = [[int(((aged["brand"] == b) & (aged["age_group"] == g[0])).sum()) for g in AGE_GROUPS] for b in BRANDS]
    ct = chi2_test(np.array(ag_tab))
    ct.update({"measure": "age group mix across brands"})
    tests.append(ct)
    return desc, pd.DataFrame(tests)


def group_cut(dfw, pw, col, groups, label, rng, n_boot, brands=("All", "Abbott", "Dexcom")):
    """Error size, direction, meter band and outcome by a grouping column (age group or sex), overall and per brand.
    Tests: Kruskal-Wallis / Mann-Whitney across the groups for the error, chi-square for direction and outcome, pairwise tests."""
    rows, tests = [], []
    for b in brands:
        d_b = dfw if b == "All" else dfw[dfw["brand"] == b]
        p_b = pw if b == "All" else pw[pw["brand"] == b]
        for g in groups:
            ds, ps = d_b[d_b[col] == g], p_b[p_b[col] == g]
            if len(ds) == 0:
                continue
            r = {"cut": label, "brand": BRAND_LABEL.get(b, b), "group": g, "wrong_reading_reports": len(ds), "pairs": len(ps),
                 "pct_fingerstick_yes": wpct(ds, ds["fingerstick"] == "yes"), "pct_ate_carbs": wpct(ds, ds["user_action"] == "ate_carbs"),
                 "pct_took_insulin": wpct(ds, ds["user_action"] == "took_insulin"), "pct_sought_care": wpct(ds, ds["user_action"] == "sought_care"),
                 "pct_outcome_hypoglycemia": wpct(ds, ds["outcome"] == "hypoglycemia"), "pct_outcome_hospital_or_er": wpct(ds, ds["outcome"] == "hospital_or_er"),
                 "pct_outcome_death": wpct(ds, ds["outcome"] == "death"), "pct_fda_death": wpct(ds, ds["event_type"] == "Death"),
                 "pct_fda_hospitalization": wpct(ds, ds[tr.fda_key("Hospitalization")]), "pct_fda_life_threatening": wpct(ds, ds[tr.fda_key("Life Threatening")]),
                 "pct_reporter_patient_or_family": wpct(ds, ds["reporter"] == "patient or family")}
            if len(ps) >= MIN_N_TEST:
                d = describe(ps)
                r.update({"median_err_pct": d["median_pct"], "q1_err_pct": d["q1_pct"], "q3_err_pct": d["q3_pct"], "median_err_mgdl": d["median_mgdl"],
                          "pct_low": d["pct_low"], "pct_high": d["pct_high"], "median_sensor_mgdl": d["median_sensor_mgdl"], "median_meter_mgdl": d["median_meter_mgdl"],
                          "pct_zone_DE_computed": d["pct_zone_DE_computed"]})
                for lab, lo, hi in METER_BANDS:
                    r[f"pct_meter_{lab}"] = wpct(ps, ps["meter_band"] == lab)
            rows.append(r)
        # tests across the groups within this brand
        kw = kw_test([p_b.loc[p_b[col] == g, "err_pct"] for g in groups])
        kw.update({"cut": label, "brand": BRAND_LABEL.get(b, b), "measure": "error, % of meter, across groups (Kruskal-Wallis)"})
        tests.append(kw)
        kw = kw_test([p_b.loc[p_b[col] == g, "abs_err_pct"] for g in groups])
        kw.update({"cut": label, "brand": BRAND_LABEL.get(b, b), "measure": "absolute error, % of meter, across groups (Kruskal-Wallis)"})
        tests.append(kw)
        pd_ = p_b[p_b["direction"] != "equal"]
        ct = chi2_test(np.array([[int(((pd_[col] == g) & (pd_["direction"] == d)).sum()) for d in ("low", "high")] for g in groups]))
        ct.update({"cut": label, "brand": BRAND_LABEL.get(b, b), "measure": "direction (low / high) across groups (chi-square)"})
        tests.append(ct)
        ct = chi2_test(np.array([[int(((p_b[col] == g) & (p_b["meter_band"] == m[0])).sum()) for m in METER_BANDS] for g in groups]))
        ct.update({"cut": label, "brand": BRAND_LABEL.get(b, b), "measure": "meter band across groups (chi-square)"})
        tests.append(ct)
        ct = chi2_test(np.array([[int(((d_b[col] == g) & (d_b["outcome"] == o)).sum()) for o in tr.OUTCOMES] for g in groups]))
        ct.update({"cut": label, "brand": BRAND_LABEL.get(b, b), "measure": "outcome (model) across groups (chi-square)"})
        tests.append(ct)
        ct = chi2_test(np.array([[int(((d_b[col] == g) & (d_b["event_type"] == e)).sum()) for e in ("Injury", "Death")] for g in groups]))
        ct.update({"cut": label, "brand": BRAND_LABEL.get(b, b), "measure": "FDA event type (injury / death) across groups (chi-square)"})
        tests.append(ct)
    # pairwise between groups (all brands together)
    prow = []
    for i, a in enumerate(groups):
        for g2 in groups[i + 1:]:
            fa, fb = pw[pw[col] == a], pw[pw[col] == g2]
            r = {"cut": label, "measure": "error, % of meter", "group_a": a, "group_b": g2}
            r.update(size_test(fa["err_pct"], fb["err_pct"], rng, n_boot))
            prow.append(r)
            r = {"cut": label, "measure": "absolute error, % of meter", "group_a": a, "group_b": g2}
            r.update(size_test(fa["abs_err_pct"], fb["abs_err_pct"], rng, n_boot))
            prow.append(r)
            fa2, fb2 = fa[fa["direction"] != "equal"], fb[fb["direction"] != "equal"]
            r = {"cut": label, "measure": "share reading low", "group_a": a, "group_b": g2}
            r.update(share_test(int((fa2["direction"] == "low").sum()), len(fa2), int((fb2["direction"] == "low").sum()), len(fb2), rng, n_boot))
            prow.append(r)
            r = {"cut": label, "measure": "share meter under 70", "group_a": a, "group_b": g2}
            r.update(share_test(int(fa["meter_under_70"].sum()), len(fa), int(fb["meter_under_70"].sum()), len(fb), rng, n_boot))
            prow.append(r)
            da, db = dfw[dfw[col] == a], dfw[dfw[col] == g2]
            for lab, m in (("share outcome hospital or ER (model)", "hospital_or_er"), ("share outcome hypoglycaemia (model)", "hypoglycemia")):
                r = {"cut": label, "measure": lab, "group_a": a, "group_b": g2}
                r.update(share_test(int((da["outcome"] == m).sum()), len(da), int((db["outcome"] == m).sum()), len(db), rng, n_boot))
                prow.append(r)
            r = {"cut": label, "measure": "share FDA event type Death", "group_a": a, "group_b": g2}
            r.update(share_test(int((da["event_type"] == "Death").sum()), len(da), int((db["event_type"] == "Death").sum()), len(db), rng, n_boot))
            prow.append(r)
    return pd.DataFrame(rows), pd.DataFrame(tests), pd.DataFrame(prow)


def filled_vs_unfilled(dfw, pw, rng, n_boot):
    """Do reports with an age (or sex) look different from reports without one?"""
    rows, tests = [], []
    for field, flag in (("age", "age_filled"), ("sex", "sex_filled")):
        for lab, m_d, m_p in ((f"{field} filled", dfw[flag], pw[flag]), (f"{field} not filled", ~dfw[flag], ~pw[flag])):
            ds, ps = dfw[m_d], pw[m_p]
            r = {"field": field, "group": lab, "wrong_reading_reports": len(ds), "pairs": len(ps), "pct_with_pair": 100.0 * len(ps) / len(ds) if len(ds) else np.nan,
                 "median_year": float(ds["year"].median()) if len(ds) else np.nan}
            for b in BRANDS:
                r[f"pct_brand_{b}"] = wpct(ds, ds["brand"] == b)
            r.update({"pct_fda_death": wpct(ds, ds["event_type"] == "Death"), "pct_outcome_hospital_or_er": wpct(ds, ds["outcome"] == "hospital_or_er"),
                      "pct_outcome_none": wpct(ds, ds["outcome"] == "none"), "pct_fda_hospitalization": wpct(ds, ds[tr.fda_key("Hospitalization")]),
                      "pct_fingerstick_yes": wpct(ds, ds["fingerstick"] == "yes"), "pct_reporter_patient_or_family": wpct(ds, ds["reporter"] == "patient or family"),
                      "pct_abbott_template": wpct(ds, ds["template"] == "Abbott template")})
            if len(ps):
                d = describe(ps)
                r.update({"median_err_pct": d["median_pct"], "q1_err_pct": d["q1_pct"], "q3_err_pct": d["q3_pct"], "pct_low": d["pct_low"], "pct_meter_under_70": d["pct_meter_under_70"]})
            rows.append(r)
        fa, fb = pw[pw[flag]], pw[~pw[flag]]
        r = {"field": field, "measure": "error, % of meter: filled vs not filled"}
        r.update(size_test(fa["err_pct"], fb["err_pct"], rng, n_boot))
        tests.append(r)
        fa2, fb2 = fa[fa["direction"] != "equal"], fb[fb["direction"] != "equal"]
        r = {"field": field, "measure": "share reading low: filled vs not filled"}
        r.update(share_test(int((fa2["direction"] == "low").sum()), len(fa2), int((fb2["direction"] == "low").sum()), len(fb2), rng, n_boot))
        tests.append(r)
        da, db = dfw[dfw[flag]], dfw[~dfw[flag]]
        r = {"field": field, "measure": "share FDA event type Death: filled vs not filled"}
        r.update(share_test(int((da["event_type"] == "Death").sum()), len(da), int((db["event_type"] == "Death").sum()), len(db), rng, n_boot))
        tests.append(r)
        r = {"field": field, "measure": "share outcome hospital or ER (model): filled vs not filled"}
        r.update(share_test(int((da["outcome"] == "hospital_or_er").sum()), len(da), int((db["outcome"] == "hospital_or_er").sum()), len(db), rng, n_boot))
        tests.append(r)
        # within brands (the fill rate differs by brand, so check inside each)
        for b in ("Abbott", "Dexcom"):
            fa, fb = pw[(pw["brand"] == b) & pw[flag]], pw[(pw["brand"] == b) & ~pw[flag]]
            r = {"field": field, "measure": f"error, % of meter: filled vs not filled, {b} only"}
            r.update(size_test(fa["err_pct"], fb["err_pct"], rng, n_boot))
            tests.append(r)
            da, db = dfw[(dfw["brand"] == b) & dfw[flag]], dfw[(dfw["brand"] == b) & ~dfw[flag]]
            r = {"field": field, "measure": f"share FDA event type Death: filled vs not filled, {b} only"}
            r.update(share_test(int((da["event_type"] == "Death").sum()), len(da), int((db["event_type"] == "Death").sum()), len(db), rng, n_boot))
            tests.append(r)
    return pd.DataFrame(rows), pd.DataFrame(tests)


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def brand_legend_label(b, n=None):
    lab = b + ("*" if b == "Medtronic" else "")
    return lab if n is None else f"{lab} (n = {n:,})"


def fig_error_sizes(pw, path):
    """t7: distribution of the error per brand (serious pairs), and ranges by direction."""
    ser = pw[pw["split"] == "serious"]
    fig = plt.figure(figsize=(7.0, 6.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], hspace=0.5, wspace=0.12)
    ax = fig.add_subplot(gs[0, :])
    lo, hi = -100, 300
    bins = np.arange(lo, hi + 10, 10)
    for b in BRANDS:
        v = ser.loc[ser["brand"] == b, "err_pct"].clip(lo, hi - 0.01).to_numpy()
        if len(v) < MIN_N_TEST:
            continue
        ax.hist(v, bins=bins, weights=np.full(len(v), 100.0 / len(v)), histtype="step", lw=2 if b in ("Abbott", "Dexcom") else 1.4,
                color=BRAND_COLORS[b], label=brand_legend_label(b, len(v)))
    ax.axvline(0, color=tr.AXIS, lw=1)
    for x, lab in ((-20, "-20 %"), (20, "+20 %")):
        ax.axvline(x, color=tr.INK2, lw=1, ls=":")
    ax.text(-22, ax.get_ylim()[1] * 0.97, "-20 %", ha="right", va="top", fontsize=8.5, color=tr.INK2)
    ax.text(22, ax.get_ylim()[1] * 0.97, "+20 %", ha="left", va="top", fontsize=8.5, color=tr.INK2)
    ax.set_xlim(lo, hi)
    ax.set_xlabel(f"sensor minus meter, % of the meter value (10 % bins; values beyond {lo} and +{hi} are put in the end bins)")
    ax.set_ylabel("share of the brand's pairs (%)")
    ax.set_title("Reported error size, serious wrong-reading reports that state both values", fontsize=9.5)
    ax.legend(loc="upper right", fontsize=8.5)
    for j, (dname, dlab, xlim, xlab) in enumerate((("low", "Sensor below meter (reads low)", (-100, 0), "error, % of meter"),
                                                   ("high", "Sensor above meter (reads high)", (0, 400), "error, % of meter (cut at +400)"))):
        axr = fig.add_subplot(gs[1, j])
        rows = []
        for b in BRANDS:
            v = ser.loc[(ser["brand"] == b) & (ser["direction"] == dname), "err_pct"].to_numpy(float)
            if len(v) >= MIN_N_TEST:
                rows.append((b, v))
        for i, (b, v) in enumerate(rows):
            q = np.percentile(v, [10, 25, 50, 75, 90])
            c = BRAND_COLORS[b]
            axr.plot([max(q[0], xlim[0]), min(q[4], xlim[1])], [i, i], color=c, lw=1.2, alpha=0.7)
            axr.plot([max(q[1], xlim[0]), min(q[3], xlim[1])], [i, i], color=c, lw=6, solid_capstyle="butt")
            axr.plot(min(max(q[2], xlim[0]), xlim[1]), i, marker="o", color=tr.INK, ms=4.5, zorder=3)
            axr.text(xlim[0] + 0.01 * (xlim[1] - xlim[0]), i + 0.36, f"median {q[2]:+.0f} %, n = {len(v):,}", ha="left", va="center", fontsize=7.5, color=tr.INK2)
        axr.set_yticks(range(len(rows)))
        axr.set_yticklabels([brand_legend_label(b) for b, _ in rows], fontsize=9)
        axr.set_ylim(len(rows) - 0.35, -0.7)
        axr.set_xlim(*xlim)
        axr.set_xlabel(xlab)
        axr.set_title(dlab, fontsize=9.5)
        axr.grid(axis="x", color=tr.GRID)
        axr.grid(axis="y", visible=False)
    fig.suptitle("How far off were the sensors, by brand? Negative = sensor read low", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=tr.INK)
    fig.text(0.01, 0.045, "Lower panels: dot = median, thick line = middle half (IQR), thin line = 10th to 90th percentile.", fontsize=8.5, color=tr.INK2)
    fig.text(0.01, 0.012, "* Medtronic: undercounted (pump product codes) and weakest validation. MAUDE counts reflect reporting, not failure rates.", fontsize=8.5, color=tr.INK2)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.9, bottom=0.14, hspace=0.5, wspace=0.3)
    tr.save(fig, path)


def fig_meter_bands(pw, shares_pairwise, path):
    """t8: where the true glucose (meter) and the sensor reading sat, per brand; and the share reading low with 95 % CI."""
    ser = pw[pw["split"] == "serious"]
    fig, axes = plt.subplots(1, 3, figsize=(8.0, 3.6), gridspec_kw={"width_ratios": [1.25, 1.25, 0.9], "wspace": 0.45})
    ramp = ["#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]       # one-hue ordinal ramp (dataviz blue 200 to 700)
    brands = [b for b in BRANDS if (ser["brand"] == b).sum() >= MIN_N_TEST]
    for ax, col, title in zip(axes[:2], ("meter_band", "sensor_band"), ("True glucose (meter value)", "What the sensor showed")):
        y = np.arange(len(brands))
        left = np.zeros(len(brands))
        for k, (lab, lo, hi) in enumerate(METER_BANDS):
            vals = np.array([100.0 * (ser.loc[ser["brand"] == b, col] == lab).mean() for b in brands])
            ax.barh(y, vals, left=left, color=ramp[k], edgecolor=tr.SURFACE, linewidth=1.5, height=0.62, label=f"{lab} mg/dL")
            for i, v in enumerate(vals):
                if v >= 9:
                    ax.text(left[i] + v / 2, i, f"{v:.0f}", ha="center", va="center", fontsize=8, color=tr.SURFACE if k >= 2 else tr.INK)
            left += vals
        ax.set_yticks(y)
        ax.set_yticklabels([f"{brand_legend_label(b)}\n(n = {int((ser['brand'] == b).sum()):,})" for b in brands], fontsize=8.5)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xlabel("share of the brand's pairs (%)")
        ax.set_title(title, fontsize=9.5)
        ax.grid(axis="x", color=tr.GRID)
        ax.grid(axis="y", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.08), ncol=5, fontsize=8, title="glucose band (mg/dL)", title_fontsize=8)
    ax = axes[2]
    rows = []
    for b in brands:
        sub = ser[(ser["brand"] == b) & (ser["direction"] != "equal")]
        k, n = int((sub["direction"] == "low").sum()), len(sub)
        if n < MIN_N_TEST:
            continue
        p = k / n
        se = np.sqrt(p * (1 - p) / n)
        rows.append((b, 100 * p, 100 * 1.96 * se, n))
    for i, (b, v, h, n) in enumerate(rows):
        ax.errorbar(v, i, xerr=h, fmt="o", color=BRAND_COLORS[b], ecolor=BRAND_COLORS[b], ms=7, capsize=3, lw=1.5)
        ax.text(v, i - 0.3, f"{v:.0f} %", ha="center", va="bottom", fontsize=8.5, color=tr.INK2)
    ax.axvline(50, color=tr.INK2, lw=1, ls=":")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([brand_legend_label(b) for b, *_ in rows], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_ylim(len(rows) - 0.5, -0.7)
    ax.set_xlim(0, 100)
    ax.set_xlabel("pairs where the sensor\nread low (%)")
    ax.set_title("Direction (95 % CI)", fontsize=9.5)
    ax.grid(axis="x", color=tr.GRID)
    ax.grid(axis="y", visible=False)
    fig.suptitle("Where was the glucose when the sensor was wrong? Serious wrong-reading pairs, by brand", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=tr.INK)
    fig.text(0.01, 0.012, "* Medtronic: undercounted and weakest validation. Reports describe the cases people complained about, not typical sensor use.", fontsize=8.5, color=tr.INK2)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.82, bottom=0.3, wspace=0.55)
    tr.save(fig, path)


def fig_by_year(by_year, path):
    """t9: wrong-reading serious reports, share reading low and median error per year and brand; recall windows shaded."""
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.4), sharex=True, gridspec_kw={"hspace": 0.38})
    yrs = list(range(YEAR_MIN, YEAR_MAX + 1))
    spans = [(2024 + (205 / 365), 2025 + (23 / 365), "Jul 2024 recall\n(Libre 3 falsely HIGH)"), (2025 + (327 / 365), 2026 + (202 / 365), "Nov 2025 recall\n(Libre 3 falsely LOW)")]
    panels = [("wrong_reading_reports", "wrong-reading serious reports (count)", None), ("pct_low", "pairs where the sensor read low (%)", (0, 100)),
              ("median_err_pct", "median error, % of meter", None)]
    for ax, (col, ylab, ylim) in zip(axes, panels):
        for b in BRANDS:
            sub = by_year[(by_year["brand"] == BRAND_LABEL[b]) & by_year["year"].between(YEAR_MIN, YEAR_MAX)].set_index("year").reindex(yrs)
            v = sub[col].to_numpy(float)
            if np.all(np.isnan(v)):
                continue
            ax.plot(yrs, v, marker="o", ms=5, lw=2 if b in ("Abbott", "Dexcom") else 1.4, color=BRAND_COLORS[b], label=brand_legend_label(b),
                    markerfacecolor=BRAND_COLORS[b], markeredgecolor=tr.SURFACE, markeredgewidth=1)
        for x0, x1, lab in spans:
            ax.axvspan(x0, min(x1, YEAR_MAX + 0.6), color=tr.GRID, alpha=0.6, lw=0)
        if ylim:
            ax.set_ylim(*ylim)
            ax.axhline(50, color=tr.INK2, lw=1, ls=":")
        if col == "median_err_pct":
            ax.axhline(0, color=tr.AXIS, lw=1)
        ax.set_ylabel(ylab, fontsize=9)
        ax.grid(axis="y", color=tr.GRID)
    top = axes[0].get_ylim()[1]
    axes[0].set_ylim(0, top * 1.3)
    for ax_i, (x0, x1, lab) in zip((axes[0], axes[1]), spans):          # one window label per panel, so they do not collide
        ax_i.text((x0 + min(x1, YEAR_MAX + 0.6)) / 2, ax_i.get_ylim()[1] * 0.98, lab, ha="center", va="top", fontsize=7.5, color=tr.INK2)
    axes[0].set_title("Wrong-reading serious reports per year, by date FDA received the report", fontsize=9.5)
    axes[1].set_title("Direction of the error (pairs only; years with fewer than 20 pairs are blank)", fontsize=9.5)
    axes[2].set_title("Size of the error (pairs only; a median near 0 means the two directions balance, not a small error)", fontsize=9.5)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.035), ncol=4, fontsize=8.5)
    axes[2].set_xticks(yrs)
    axes[2].set_xlim(YEAR_MIN - 0.4, YEAR_MAX + 0.6)
    axes[2].set_xlabel("year FDA received the report (2026 = to the 2026-07-21 text cut-off)")
    fig.suptitle("Brand differences by year; grey = the two Libre 3 recall windows", x=0.01, ha="left", fontsize=11, fontweight="semibold", color=tr.INK)
    fig.text(0.01, 0.008, "* Medtronic: undercounted and weakest validation. Report counts reflect reporting behaviour (and recall news), not failure rates.", fontsize=8.5, color=tr.INK2)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.93, bottom=0.12, hspace=0.42)
    tr.save(fig, path)


def fig_demographics(dfw, pw, fill, age_cut, sex_cut, path):
    """t10: age distribution per brand, fill rates, error size and direction by age group and sex."""
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 6.6), gridspec_kw={"hspace": 0.55, "wspace": 0.35})
    # (a) age distribution per brand
    ax = axes[0, 0]
    aged = dfw[dfw["age_filled"]]
    bins = np.arange(0, 101, 10)
    for b in BRANDS:
        v = aged.loc[aged["brand"] == b, "age_years"].clip(0, 99.9).to_numpy()
        if len(v) < MIN_N_TEST:
            continue
        ax.hist(v, bins=bins, weights=np.full(len(v), 100.0 / len(v)), histtype="step", lw=2 if b in ("Abbott", "Dexcom") else 1.4, color=BRAND_COLORS[b],
                label=brand_legend_label(b, len(v)))
    ax.set_xlabel("patient age, years (10-year bins)")
    ax.set_ylabel("share of reports with an age (%)")
    ax.set_title("Age of the patient, where filled", fontsize=9.5)
    ax.legend(fontsize=7.5, loc="upper left")
    # (b) fill rates per brand
    ax = axes[0, 1]
    sub = fill[(fill["cut"] == "brand") & (fill["tier"] == "serious")]
    brands = [b for b in BRANDS if (sub["group"] == BRAND_LABEL[b]).any()]
    y = np.arange(len(brands))
    for k, (col, lab, c) in enumerate((("pct_age_filled", "age filled", "#2a78d6"), ("pct_sex_filled", "sex filled", "#9ec5f4"))):
        vals = [float(sub.loc[sub["group"] == BRAND_LABEL[b], col].iloc[0]) for b in brands]
        ax.barh(y + (k - 0.5) * 0.36, vals, height=0.34, color=c, label=lab)
        for i, v in enumerate(vals):
            ax.text(v + 1, i + (k - 0.5) * 0.36, f"{v:.0f}", va="center", fontsize=8, color=tr.INK2)
    dth = fill[(fill["cut"] == "FDA event type")]
    ax.set_yticks(y)
    ax.set_yticklabels([brand_legend_label(b) for b in brands], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("wrong-reading serious reports with the field filled (%)")
    note = ""
    if len(dth) == 2:
        d_age = {r["group"]: r["pct_age_filled"] for _, r in dth.iterrows()}
        note = f"age filled: injury {d_age.get('Injury', np.nan):.0f} %, death {d_age.get('Death', np.nan):.0f} %"
    ax.set_title("How often age and sex are filled in" + (f"\n({note})" if note else ""), fontsize=9.5)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", color=tr.GRID)
    ax.grid(axis="y", visible=False)
    # (c) share reading low by age group and by sex, with 95 % CI: all brands, Abbott, Dexcom
    ax = axes[1, 0]
    groups = [g[0] for g in AGE_GROUPS]
    cats = [("age_group", g, f"{g} y") for g in groups] + [("sex", "Female", "Female"), ("sex", "Male", "Male")]
    x = np.arange(len(cats))
    pd_ = pw[pw["direction"] != "equal"]
    for k, b in enumerate(("All", "Abbott", "Dexcom")):
        base = pd_ if b == "All" else pd_[pd_["brand"] == b]
        vals, errs = [], []
        for col, g, _ in cats:
            sub = base[base[col] == g]
            n = len(sub)
            if n < MIN_N_TEST:
                vals.append(np.nan)
                errs.append(0.0)
                continue
            p = (sub["direction"] == "low").mean()
            vals.append(100 * p)
            errs.append(100 * 1.96 * np.sqrt(p * (1 - p) / n))
        colr = tr.INK2 if b == "All" else BRAND_COLORS[b]
        ax.errorbar(x + (k - 1) * 0.22, vals, yerr=errs, fmt="o", color=colr, ecolor=colr, ms=5.5, capsize=2, lw=1.2,
                    label="all brands" if b == "All" else brand_legend_label(b), markeredgecolor=tr.SURFACE, markeredgewidth=0.8)
    ax.axhline(50, color=tr.INK2, lw=1, ls=":")
    ax.axvline(len(groups) - 0.5, color=tr.AXIS, lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, _, lab in cats], fontsize=8.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("pairs where the sensor read low (%)")
    ax.set_title("Direction by age group and by sex (95 % CI)", fontsize=9.5)
    ax.legend(fontsize=7.5, loc="lower left", ncol=3)
    # (d) what people did and what happened, by age group (all brands; reports with an age)
    ax = axes[1, 1]
    aged_w = dfw[dfw["age_filled"]]
    measures = [("took insulin", aged_w["user_action"] == "took_insulin"), ("ate carbs", aged_w["user_action"] == "ate_carbs"),
                ("outcome: hypoglycaemia", aged_w["outcome"] == "hypoglycemia"), ("outcome: hospital or ER", aged_w["outcome"] == "hospital_or_er")]
    ramp = ["#9ec5f4", "#5598e7", "#2a78d6", "#104281"]
    y = np.arange(len(measures))
    h = 0.19
    for k, g in enumerate(groups):
        m_g = (aged_w["age_group"] == g).to_numpy()
        vals = [100.0 * mask.to_numpy()[m_g].mean() for _, mask in measures]
        ax.barh(y + (k - 1.5) * h, vals, height=h * 0.92, color=ramp[k], label=f"{g} y (n = {int(m_g.sum()):,})")
        for i, v in enumerate(vals):
            ax.text(v + 1, i + (k - 1.5) * h, f"{v:.0f}", va="center", fontsize=6.5, color=tr.INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([lab for lab, _ in measures], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of wrong-reading reports with an age (%)")
    ax.set_title("What people did and what happened, by age group", fontsize=9.5)
    ax.legend(fontsize=7, loc="upper right", title="age group", title_fontsize=7)
    ax.grid(axis="x", color=tr.GRID)
    ax.grid(axis="y", visible=False)
    fig.suptitle("Demographics of the wrong-reading reports (serious reports; age filled in about half, sex in two fifths)", x=0.01, ha="left", fontsize=10.5, fontweight="semibold", color=tr.INK)
    fig.text(0.01, 0.01, "* Medtronic: undercounted and weakest validation. Age and sex are filled by the reporter; missing is not random (mostly Abbott reports; see the memo).", fontsize=8.5, color=tr.INK2)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.9, bottom=0.1, hspace=0.5, wspace=0.42)
    tr.save(fig, path)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Brand-vs-brand comparison of the wrong-reading complaints, plus demographics.")
    ap.add_argument("--jsonl", default=str(REPO / "fda-maude/clean/text_extract_v3.jsonl"))
    ap.add_argument("--run-set", default=str(REPO / "fda-maude/clean/run_set.csv.gz"))
    ap.add_argument("--regex", default=str(REPO / "fda-maude/clean/regex_run_set.csv"))
    ap.add_argument("--serious", default=str(REPO / "fda-maude/clean/serious.csv.gz"), help="clean serious table (age, sex, reporter)")
    ap.add_argument("--sample-parquet", default=str(REPO / "fda-maude/clean/sample_local.parquet"))
    ap.add_argument("--family-map", default=str(REPO / "fda-maude/results/report/tables/d_problem_family_mapping.csv"))
    ap.add_argument("--out-tables", default=str(REPO / "fda-maude/results/text/tables"))
    ap.add_argument("--out-figures", default=str(REPO / "fda-maude/results/text/figures"))
    ap.add_argument("--n-boot", type=int, default=N_BOOT_DEFAULT, help="bootstrap resamples (default 1000)")
    ap.add_argument("--max-rows", type=int, default=None, help="read only the first N JSONL rows (test)")
    args = ap.parse_args()
    out_t, out_f = Path(args.out_tables), Path(args.out_figures)
    out_t.mkdir(parents=True, exist_ok=True)
    out_f.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    df = build_frame(args)
    p, n_implausible = pairs_from(df)
    pw_all = p[p["wr"]].copy()                                   # pairs inside the wrong-reading set (both tiers)
    dfw = df[(df["split"] == "serious") & df["wr"]].copy()       # serious wrong-reading reports
    pw = pw_all[pw_all["split"] == "serious"].copy()             # serious pairs in the set
    log(f"comparison set: serious {len(dfw):,} reports, {len(pw):,} pairs; sample {int(((df['split'] == 'sample') & df['wr']).sum()):,} reports, "
        f"{int((pw_all['split'] == 'sample').sum()):,} pairs; {n_implausible} implausible pairs dropped upstream")

    # 1. counts
    counts = counts_table(df, p)
    counts.to_csv(out_t / "g_comparison_set_counts.csv", index=False)
    other_makers_table(df).to_csv(out_t / "g_other_makers.csv", index=False)
    log("g_comparison_set_counts.csv written")

    # 2. error sizes
    desc, pct, kw, pairwise, bins = error_size_tables(pw_all, rng, args.n_boot)
    desc.to_csv(out_t / "g_brand_error_sizes.csv", index=False)
    pct.to_csv(out_t / "g_brand_error_percentiles.csv", index=False)
    kw.to_csv(out_t / "g_brand_error_kruskal.csv", index=False)
    pairwise.to_csv(out_t / "g_brand_error_pairwise.csv", index=False)
    bins.to_csv(out_t / "g_brand_error_bins.csv", index=False)
    log("error size tables written")

    # 3. shares
    shares, share_tests = share_tables(dfw, pw)
    shares.to_csv(out_t / "g_brand_shares.csv", index=False)
    share_tests.to_csv(out_t / "g_brand_share_tests.csv", index=False)
    share_pw = pairwise_share_table(dfw, pw, rng, args.n_boot)
    share_pw.to_csv(out_t / "g_brand_shares_pairwise.csv", index=False)
    log("share tables written")

    # 4. confounds
    tmpl_desc, tmpl_tests, tmpl_reports = template_tables(dfw, pw, rng, args.n_boot)
    tmpl_desc.to_csv(out_t / "g_confound_template_pairs.csv", index=False)
    tmpl_tests.to_csv(out_t / "g_confound_template_tests.csv", index=False)
    tmpl_reports.to_csv(out_t / "g_confound_template_reports.csv", index=False)
    tier_desc, tier_tests = tier_tables(df, p, rng, args.n_boot)
    tier_desc.to_csv(out_t / "g_confound_serious_vs_sample.csv", index=False)
    tier_tests.to_csv(out_t / "g_confound_serious_vs_sample_tests.csv", index=False)
    by_year, periods, period_tests, year_tests = year_tables(dfw, pw, rng, args.n_boot)
    by_year.to_csv(out_t / "g_brand_by_year.csv", index=False)
    periods.to_csv(out_t / "g_recall_windows.csv", index=False)
    period_tests.to_csv(out_t / "g_recall_windows_tests.csv", index=False)
    year_tests.to_csv(out_t / "g_brand_by_year_tests.csv", index=False)
    lines, line_tests = product_line_table(dfw, pw, rng, args.n_boot)
    lines.to_csv(out_t / "g_product_lines.csv", index=False)
    line_tests.to_csv(out_t / "g_product_lines_tests.csv", index=False)
    log("confound tables written")

    # 5. demographics
    fill = fill_tables(df, dfw)
    fill.to_csv(out_t / "g_demographics_fill.csv", index=False)
    age_brand, age_brand_tests = age_sex_by_brand(dfw, rng, args.n_boot)
    age_brand.to_csv(out_t / "g_demographics_age_sex_by_brand.csv", index=False)
    age_brand_tests.to_csv(out_t / "g_demographics_age_sex_by_brand_tests.csv", index=False)
    age_cut, age_tests, age_pw = group_cut(dfw[dfw["age_filled"]], pw[pw["age_filled"]], "age_group", [g[0] for g in AGE_GROUPS], "age group", rng, args.n_boot)
    sex_cut, sex_tests, sex_pw = group_cut(dfw[dfw["sex_filled"]], pw[pw["sex_filled"]], "sex", ["Female", "Male"], "sex", rng, args.n_boot)
    pd.concat([age_cut, sex_cut], ignore_index=True).to_csv(out_t / "g_demographics_by_group.csv", index=False)
    pd.concat([age_tests, sex_tests], ignore_index=True).to_csv(out_t / "g_demographics_by_group_tests.csv", index=False)
    pd.concat([age_pw, sex_pw], ignore_index=True).to_csv(out_t / "g_demographics_by_group_pairwise.csv", index=False)
    fvu, fvu_tests = filled_vs_unfilled(dfw, pw, rng, args.n_boot)
    fvu.to_csv(out_t / "g_demographics_filled_vs_unfilled.csv", index=False)
    fvu_tests.to_csv(out_t / "g_demographics_filled_vs_unfilled_tests.csv", index=False)
    log("demographics tables written")

    # figures
    fig_error_sizes(pw_all, out_f / "t7_brand_error_sizes.png")
    fig_meter_bands(pw_all, share_pw, out_f / "t8_brand_meter_bands.png")
    fig_by_year(by_year, out_f / "t9_brand_by_year.png")
    fig_demographics(dfw, pw, fill, age_cut, sex_cut, out_f / "t10_demographics.png")

    # key numbers and markdown copies
    stats_out = {"seed": SEED, "n_boot": args.n_boot, "definition": "wrong reading = text fault type in " + ", ".join(WRONG_TEXT) + " OR FDA problem-code family 'Wrong readings (accuracy)'",
                 "recall_windows_by_date_received": [{"label": w[0], "from": w[1], "to": w[2]} for w in RECALL_WINDOWS],
                 "n_serious_wrong_reading": int(len(dfw)), "n_serious_pairs": int(len(pw)), "counts": counts.to_dict(orient="records"),
                 "error_sizes": desc.to_dict(orient="records"), "kruskal": kw.to_dict(orient="records"), "pairwise_sizes": pairwise.to_dict(orient="records"),
                 "share_tests": share_tests.to_dict(orient="records"), "pairwise_shares": share_pw.to_dict(orient="records"),
                 "template": tmpl_desc.to_dict(orient="records"), "template_tests": tmpl_tests.to_dict(orient="records"), "template_reports": tmpl_reports.to_dict(orient="records"),
                 "serious_vs_sample": tier_desc.to_dict(orient="records"), "serious_vs_sample_tests": tier_tests.to_dict(orient="records"),
                 "recall_windows": periods.to_dict(orient="records"), "recall_window_tests": period_tests.to_dict(orient="records"),
                 "product_lines": lines.to_dict(orient="records"), "product_line_tests": line_tests.to_dict(orient="records"),
                 "fill": fill.to_dict(orient="records"), "age_sex_by_brand": age_brand.to_dict(orient="records"), "age_sex_by_brand_tests": age_brand_tests.to_dict(orient="records"),
                 "by_group": pd.concat([age_cut, sex_cut]).to_dict(orient="records"), "by_group_tests": pd.concat([age_tests, sex_tests]).to_dict(orient="records"),
                 "by_group_pairwise": pd.concat([age_pw, sex_pw]).to_dict(orient="records"),
                 "filled_vs_unfilled": fvu.to_dict(orient="records"), "filled_vs_unfilled_tests": fvu_tests.to_dict(orient="records")}
    (out_t / "g_brand_comparison_stats.json").write_text(json.dumps(stats_out, indent=1, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else str(o)), encoding="utf-8")

    md = ["# Brand comparison: markdown copies of the g_*.csv tables in this folder", "",
          "Made by `scripts/brand_comparison.py`. Memo: `../BRAND_COMPARISON.md`. Medtronic rows carry a caution (undercounted; weakest validation). "
          "MAUDE counts reflect reporting behaviour, not failure rates.", ""]
    md += ["## g. Comparison set counts", tr.to_markdown(counts), ""]
    cols_desc = ["tier", "brand", "pairs", "n_pairs", "weighted_n", "median_mgdl", "q1_mgdl", "q3_mgdl", "median_pct", "q1_pct", "q3_pct", "p10_pct", "p90_pct",
                 "pct_low", "pct_high", "median_sensor_mgdl", "median_meter_mgdl", "pct_meter_under_70", "pct_meter_over_250", "pct_zone_DE_computed"]
    md += ["## g. Error sizes by brand", tr.to_markdown(desc[cols_desc]), ""]
    md += ["## g. Error percentiles by brand (serious)", tr.to_markdown(pct), ""]
    md += ["## g. Kruskal-Wallis across brands (serious)", tr.to_markdown(kw, "{:.3f}"), ""]
    cols_pw = ["pairs", "measure", "brand_a", "brand_b", "n_a", "n_b", "median_a", "median_b", "median_diff_a_minus_b", "median_diff_ci_low", "median_diff_ci_high",
               "cliffs_delta", "cliffs_delta_ci_low", "cliffs_delta_ci_high", "effect_size_word", "p_text"]
    md += ["## g. Pairwise brand tests on sizes (serious)", tr.to_markdown(pairwise[cols_pw], "{:.2f}"), ""]
    md += ["## g. Shares by brand (serious wrong-reading reports / pairs)", tr.to_markdown(shares), ""]
    md += ["## g. Chi-square tests on the shares", tr.to_markdown(share_tests, "{:.3f}"), ""]
    cols_sp = ["measure", "base", "group_a", "group_b", "n_a", "n_b", "share_a_pct", "share_b_pct", "risk_diff_points", "risk_diff_ci_low", "risk_diff_ci_high", "p_text"]
    md += ["## g. Pairwise brand risk differences", tr.to_markdown(share_pw[cols_sp]), ""]
    md += ["## g. Confound (a): Abbott template vs prose, pairs", tr.to_markdown(tmpl_desc), ""]
    md += ["## g. Confound (a): tests", tr.to_markdown(tmpl_tests, "{:.2f}"), ""]
    md += ["## g. Confound (a): what the text forms report (all Abbott wrong-reading reports)", tr.to_markdown(tmpl_reports), ""]
    md += ["## g. Confound (b): serious vs weighted malfunction sample", tr.to_markdown(tier_desc), ""]
    md += ["## g. Confound (b): tests", tr.to_markdown(tier_tests, "{:.2f}"), ""]
    md += ["## g. Confound (c): by year", tr.to_markdown(by_year), ""]
    md += ["## g. Confound (c): recall windows", tr.to_markdown(periods), ""]
    md += ["## g. Confound (c): tests by period", tr.to_markdown(period_tests, "{:.2f}"), ""]
    md += ["## g. Confound (c): Abbott vs Dexcom by year", tr.to_markdown(year_tests, "{:.2f}"), ""]
    md += ["## g. Product lines", tr.to_markdown(lines), ""]
    md += ["## g. Product line tests", tr.to_markdown(line_tests, "{:.2f}"), ""]
    md += ["## g. Demographics: fill rates", tr.to_markdown(fill), ""]
    md += ["## g. Demographics: age and sex by brand", tr.to_markdown(age_brand), ""]
    md += ["## g. Demographics: age and sex by brand, tests", tr.to_markdown(age_brand_tests, "{:.3f}"), ""]
    md += ["## g. Demographics: by age group and sex", tr.to_markdown(pd.concat([age_cut, sex_cut], ignore_index=True)), ""]
    md += ["## g. Demographics: tests across groups", tr.to_markdown(pd.concat([age_tests, sex_tests], ignore_index=True), "{:.3f}"), ""]
    md += ["## g. Demographics: pairwise tests between groups", tr.to_markdown(pd.concat([age_pw, sex_pw], ignore_index=True), "{:.2f}"), ""]
    md += ["## g. Demographics: filled vs unfilled", tr.to_markdown(fvu), ""]
    md += ["## g. Demographics: filled vs unfilled, tests", tr.to_markdown(fvu_tests, "{:.2f}"), ""]
    (out_t / "g_key_tables.md").write_text("\n".join(md), encoding="utf-8")
    log(f"done: tables in {out_t}, figures in {out_f}")


if __name__ == "__main__":
    main()
