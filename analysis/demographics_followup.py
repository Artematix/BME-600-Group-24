"""
Follow-up of the one demographic lead (BMEN 600 Group 24): in the low range the Dexcom G4 reads
lower in women than in men.

Project: how accurate CGM (continuous glucose monitor) readings are against fingerstick reference, and
what drives the error. DEMOGRAPHICS_DEEP.md (2026-11-06) ran 680 tests on who the person is; one
passed correction: low-range bias -6.4 % in women vs -2.2 % in men (men minus women +4.2 points,
CI +2.0 to +6.0, BH p 0.016). This script asks three questions about that result.
  1. Where is it? Split the sex gap by wear day, time of day, trend, lag correction, meter type, arm,
     phase, glucose band, pair source, and by which device defines "low". Also the mid and high range.
  2. Sensor or person? Compare the low-glucose profile of women and men (how often, how deep, when,
     how fast), then re-test the gap after matching pairs on glucose level and trend.
  3. Does anything in the data explain it? Body size, HbA1c, age, insulin dose per kg. (No haematocrit
     or other lab value exists in either dataset; the script records that.)
Plus: Shanghai (Abbott flash sensor, small), MAUDE complaint texts (Dexcom, sex filled), and what the
gap would do to decisions (simulation lookup table).

Rule: every test is listed before any test runs (written to the JSON under `preregistration`) and
every result is reported. Benjamini-Hochberg (BH) correction within three families: REPLACE-BG,
Shanghai, MAUDE. The original test (verified pairs below 70) is shown as the anchor row and is not
counted again.

Unit of analysis = the participant unless stated (per-person mean bias on pairs below 70 mg/dL by
the average of CGM and fingerstick, 20 or more such pairs; Mann-Whitney test; bootstrap CI on the
difference in medians; seed 600, same helpers as demographics_deep.py). Pooled-pair results use a
participant bootstrap.

Usage (from the repo root; Windows: plain `python`):
    python analysis/demographics_followup.py "Uncommitted Data/Raw Data Dump" analysis [cache folder] [--no-maude]
Outputs: analysis/demographics_followup_stats.json, analysis/figures/35_sex_low_range_bias.png,
markdown tables on stdout (pasted into DEMOGRAPHICS_FOLLOWUP.md). Needs the preprocess cache and
cache/participant_metrics.parquet (run subgroups.py first). About 3 minutes; 1 minute of it is MAUDE.

Terms. Bias = mean of (CGM minus fingerstick) as % of the fingerstick; negative = sensor reads low.
Low range = pairs whose average of CGM and fingerstick is below 70 mg/dL. CI = 95 % confidence
interval. BH p = p after the Benjamini-Hochberg correction for many tests. ROC = rate of change of
the CGM trace at the fingerstick time (mg/dL per minute). Lag correction = compare the fingerstick
with the CGM reading taken 5 min later. Matching = compare women and men only within pairs of the
same glucose level and trend, then average. Mixed model = a regression that knows which pairs belong
to the same person. TDD = total daily insulin dose (basal + bolus) from the pump log.
"""
import json
import os
import sys
import time
import warnings

FLAGS = [a for a in sys.argv[1:] if a.startswith("--")]
sys.argv = [a for a in sys.argv if not a.startswith("--")]        # demographics_deep reads positional args at import
SKIP_MAUDE = "--no-maude" in FLAGS

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import preprocess as pp              # shared loaders + parquet cache
import demographics_deep as dd       # shared statistics helpers (group_test, boot_diff, fit_ols, spearman_ci, bh, clean, covariates)

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

ROOT = sys.argv[1] if len(sys.argv) > 1 else pp.DEFAULT_ROOT
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis"
CACHE = sys.argv[3] if len(sys.argv) > 3 else pp.DEFAULT_CACHE
FIG = os.path.join(OUT, "figures")
pp.check_raw_data(ROOT)
os.makedirs(FIG, exist_ok=True)
warnings.filterwarnings("ignore")

SEED = 600                       # same seed as subgroups.py / demographics_deep.py
N_BOOT = 2000                    # bootstrap resamples (participants drawn with replacement)
MIN_LOW_PAIRS = dd.MIN_LOW_PAIRS  # 20 pairs below 70 for a per-person low-range bias
MIN_GROUP = dd.MIN_GROUP         # 10 people per group to test
MIN_STRATUM = 5                  # pairs per sex per stratum for the matched comparison
MIN_TDD_DAYS = 14                # pump days needed for a person's insulin dose
LAG_SHIFT_S = 300                # lag correction: CGM reading 5 min after the fingerstick (ERROR_DRIVERS.md section 3)
LAG_TOL_S = 300                  # nearest reading within 5 min of the target time (same rule as the cache)
EPISODE_MIN_READINGS = 3         # a CGM low episode = 3 or more consecutive readings below 70 (15 min)
AVG_EDGES = [0, 40, 45, 50, 55, 60, 65, 70]
AVG_LABELS = ["<40", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69"]
REF_EDGES = [0, 40, 45, 50, 55, 60, 65, 70, 75, 80, 10_000]
REF_LABELS = AVG_LABELS + ["70-74", "75-79", "80+"]
FIG_EDGES = [0, 45, 50, 55, 60, 65, 70, 100, 140, 181, 251, 10_000]
FIG_LABELS = ["<45", "45-49", "50-54", "55-59", "60-64", "65-69", "70-99", "100-139", "140-180", "181-250", ">250"]
ROC3 = ["falling", "flat", "rising", "unknown"]
RNG = np.random.default_rng(SEED)
T0 = time.time()
STATS = {}
FAMILIES = {"replace_bg": [], "shanghai": [], "maude": []}


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Chart styling (same palette as error_drivers.py / demographics_deep.py)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
C_F, C_M = C_ORANGE, C_BLUE          # women orange, men blue, in every panel
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 9, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "x", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 8,
    "lines.linewidth": 1.5, "savefig.dpi": 200, "savefig.bbox": "tight",
})


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def register(family, block, test_id, label, res, p_key="p"):
    """Add one pre-registered p-value to a BH family; p_bh is written into `res` at the end."""
    p = res.get(p_key)
    FAMILIES[family].append({"block": block, "id": test_id, "label": label, "p": float(p) if p is not None and not np.isnan(p) else np.nan, "ref": res})


def finish_families():
    out = {}
    for name, fam in FAMILIES.items():
        p = np.array([f["p"] for f in fam], float)
        adj = dd.bh(p)
        blocks = np.array([f["block"] for f in fam])
        adj_block = np.full(len(p), np.nan)
        for b in np.unique(blocks):
            m = blocks == b
            adj_block[m] = dd.bh(p[m])
        for f, a, ab in zip(fam, adj, adj_block):
            f["ref"]["p_bh"] = None if np.isnan(a) else float(a)
            f["ref"]["p_bh_block"] = None if np.isnan(ab) else float(ab)
            f["ref"]["bh_significant"] = bool(not np.isnan(a) and a < 0.05)
        ok = ~np.isnan(p)
        out[name] = {"n_tests": int(ok.sum()), "n_raw_p_below_0_05": int((p[ok] < 0.05).sum()), "expected_by_chance": float(ok.sum() * 0.05),
                     "n_pass_bh": int((adj[ok] < 0.05).sum()), "smallest_p_bh": float(np.nanmin(adj)) if ok.any() else None,
                     "passed": [{"block": f["block"], "id": f["id"], "label": f["label"], "p": f["p"], "p_bh": float(a)} for f, a in zip(fam, adj) if not np.isnan(a) and a < 0.05],
                     "tests": [{"block": f["block"], "id": f["id"], "label": f["label"], "p": f["p"], "p_bh": None if np.isnan(a) else float(a)} for f, a in zip(fam, adj)]}
    return out


def roc3(roc):
    """Three trend bins: falling (< -1 mg/dL per min), flat (-1 to 1), rising (> 1); missing = unknown."""
    r = np.asarray(roc, float)
    lab = np.select([r < -1, r <= 1, r > 1], ["falling", "flat", "rising"], default="unknown")
    return pd.Categorical(lab, ROC3)


def per_person(df, name, min_pairs=MIN_LOW_PAIRS):
    """Per-person mean bias (%), mean error (mg/dL), pair count and mean fingerstick on the given pairs; NaN below min_pairs."""
    g = df.groupby("PtID").agg(n=("rel_err_pct", "size"), bias=("rel_err_pct", "mean"), err_mgdl=("err", "mean"), ref_mean=("ref", "mean"))
    g.loc[g.n < min_pairs, ["bias", "err_mgdl"]] = np.nan
    return g.rename(columns=lambda c: f"{name}_{c}")


def sex_gap(f, col, label, mgdl_col=None):
    """Women vs men on a per-person value: medians, means, men-minus-women difference in medians with bootstrap CI,
    Mann-Whitney p (demographics_deep.group_test; women are the reference group)."""
    r = dd.group_test(f, "sex", col, label)
    g = {x["group"]: x for x in r["groups"]}
    out = {"label": label, "outcome": col, "testable": r["testable"],
           "n_F": int(g.get("F", {}).get("n", 0)), "n_M": int(g.get("M", {}).get("n", 0)),
           "median_F": g.get("F", {}).get("median"), "median_M": g.get("M", {}).get("median"),
           "mean_F": g.get("F", {}).get("mean"), "mean_M": g.get("M", {}).get("mean"),
           "diff_median_M_minus_F": None, "ci_low": None, "ci_high": None, "p": r["p"], "test": r["test"]}
    if r["contrasts"]:
        c = r["contrasts"][0]
        out.update({"diff_median_M_minus_F": c["diff_median"], "ci_low": c["ci_low"], "ci_high": c["ci_high"], "detectable_diff_means": c["detectable_diff_means"]})
    if not r["testable"]:
        out["reason"] = r.get("reason")
    if mgdl_col is not None and mgdl_col in f:
        out["median_mgdl_F"] = dd.describe(f.loc[f.sex == "F", mgdl_col])["median"]
        out["median_mgdl_M"] = dd.describe(f.loc[f.sex == "M", mgdl_col])["median"]
    return out


def pooled_sex_gap(df, by="PtID", value="rel_err_pct", n_boot=N_BOOT, strata=None, min_per_stratum=MIN_STRATUM):
    """Pooled-pair bias by sex, men minus women, with a participant bootstrap CI (participants resampled within each sex).
    With `strata` (a column), the gap is standardised: within each stratum the men-minus-women difference is taken, then
    averaged with weights = the pooled share of pairs in that stratum (strata with fewer than min_per_stratum pairs in
    either sex are dropped). Without strata it is the plain pooled difference."""
    d = df[[by, "sex", value] + ([strata] if strata else [])].dropna().copy()
    if strata is None:
        d["_s"] = "all"
        strata = "_s"
    s_levels = sorted(d[strata].astype(str).unique())
    s_idx = {s: i for i, s in enumerate(s_levels)}
    mats = {}
    for sex in ["F", "M"]:
        sub = d[d.sex == sex]
        pts = np.sort(sub[by].unique())
        if len(pts) == 0:                                                   # a sex with no pairs in this split
            mats[sex] = (np.zeros((0, len(s_levels))), np.zeros((0, len(s_levels))), np.zeros((n_boot, 0)), 0, 0)
            continue
        p_idx = {p: i for i, p in enumerate(pts)}
        S = np.zeros((len(pts), len(s_levels)))
        C = np.zeros_like(S)
        ii = sub[by].map(p_idx).to_numpy().astype(int)
        jj = sub[strata].astype(str).map(s_idx).to_numpy().astype(int)
        np.add.at(S, (ii, jj), sub[value].to_numpy(float))
        np.add.at(C, (ii, jj), 1.0)
        W = RNG.multinomial(len(pts), np.full(len(pts), 1 / len(pts)), size=n_boot).astype(float)
        mats[sex] = (S, C, W, len(pts), len(sub))

    def est(sF, cF, sM, cM):
        ok = (cF >= min_per_stratum) & (cM >= min_per_stratum)
        w = (cF + cM) * ok
        tot = w.sum(axis=-1, keepdims=True)
        w = np.divide(w, tot, out=np.zeros_like(w), where=tot > 0)
        diff = np.where(ok, sM / np.maximum(cM, 1) - sF / np.maximum(cF, 1), 0.0)
        return (w * diff).sum(axis=-1), ok.sum(axis=-1), (w * np.where(ok, sF / np.maximum(cF, 1), 0)).sum(axis=-1), (w * np.where(ok, sM / np.maximum(cM, 1), 0)).sum(axis=-1)

    SF, CF, WF, nF, pairsF = mats["F"]
    SM, CM, WM, nM, pairsM = mats["M"]
    if nF == 0 or nM == 0:
        return {"pairs_F": pairsF, "pairs_M": pairsM, "people_F": nF, "people_M": nM, "gap_M_minus_F": None, "ci_low": None, "ci_high": None, "note": "a sex has no pairs"}
    point, n_used, biasF, biasM = est(SF.sum(0), CF.sum(0), SM.sum(0), CM.sum(0))
    boot, _, _, _ = est(WF @ SF, WF @ CF, WM @ SM, WM @ CM)
    used = (CF.sum(0) >= min_per_stratum) & (CM.sum(0) >= min_per_stratum)
    return {"pairs_F": int(pairsF), "pairs_M": int(pairsM), "people_F": int(nF), "people_M": int(nM),
            "bias_F": float(biasF), "bias_M": float(biasM), "gap_M_minus_F": float(point),
            "ci_low": float(np.percentile(boot, 2.5)), "ci_high": float(np.percentile(boot, 97.5)),
            "strata_used": int(n_used), "strata_total": len(s_levels), "pairs_used": int((CF.sum(0) + CM.sum(0))[used].sum()),
            "weights": "pooled share of pairs per stratum" if len(s_levels) > 1 else "none (plain pooled difference)"}


def pooled_share_gap(df, flag, by="PtID", n_boot=N_BOOT):
    """Share (%) of pairs with flag True, women vs men, men minus women, participant bootstrap CI."""
    d = df[[by, "sex"]].copy()
    d["v"] = df[flag].astype(float) * 100
    r = pooled_sex_gap(d, by=by, value="v", n_boot=n_boot)
    return {"share_F": r.get("bias_F"), "share_M": r.get("bias_M"), "diff_M_minus_F": r.get("gap_M_minus_F"), "ci_low": r.get("ci_low"), "ci_high": r.get("ci_high"),
            "pairs_F": r.get("pairs_F"), "pairs_M": r.get("pairs_M"), "people_F": r.get("people_F"), "people_M": r.get("people_M")}


def mixed_male(df, formula, groups="PtID"):
    """Mixed model (random intercept per person); returns the `male` coefficient (points of bias), CI and p."""
    needed = ["rel_err_pct", "male"] + [c for c in ["avg_bin", "ref_bin", "roc3", "night", "wear1", "arm_cgm_bgm"] if c in formula]
    d = df.dropna(subset=[c for c in needed if c in df]).copy()
    if len(d) < 10 or d.male.nunique() < 2:
        return {"formula": formula, "pairs": int(len(d)), "people": int(d[groups].nunique()) if len(d) else 0, "coef_male": None, "ci_low": None, "ci_high": None, "p": np.nan, "error": "too few pairs or one sex only"}
    try:
        res = smf.mixedlm(formula, d, groups=d[groups]).fit(reml=True)
        ci = res.conf_int()
        return {"formula": formula, "pairs": int(res.nobs), "people": int(d[groups].nunique()), "coef_male": float(res.params["male"]),
                "ci_low": float(ci.loc["male", 0]), "ci_high": float(ci.loc["male", 1]), "p": float(res.pvalues["male"]), "converged": bool(res.converged)}
    except Exception as e:                                             # tiny sets (Shanghai) can fail to fit
        return {"formula": formula, "pairs": int(len(d)), "people": int(d[groups].nunique()), "coef_male": None, "ci_low": None, "ci_high": None, "p": np.nan, "error": str(e)[:120]}


def fmt(v, nd=1, sign=False):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n.a."
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n.a."
    return "<0.001" if p < 0.001 else f"{p:.3f}" if p < 0.01 else f"{p:.2f}"


def md(header, rows):
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print()


def gap_row(name, r):
    pl = r.get("pooled", {})
    if r["testable"]:
        est = f"{fmt(r['diff_median_M_minus_F'], 1, True)} ({fmt(r['ci_low'], 1, True)} to {fmt(r['ci_high'], 1, True)})"
    else:
        est = f"n.t. per person; pooled {fmt(pl.get('gap_M_minus_F'), 1, True)} ({fmt(pl.get('ci_low'), 1, True)} to {fmt(pl.get('ci_high'), 1, True)})"
    return [name, f"{fmt(r['median_F'])} ({r['n_F']}; {r.get('pairs_F', 0):,} pairs)", f"{fmt(r['median_M'])} ({r['n_M']}; {r.get('pairs_M', 0):,} pairs)",
            est, fmt_p(r["p"]), fmt_p(r.get("p_bh")) if r.get("p_bh") is not None else ("anchor" if r.get("anchor") else "n.a.")]


# --------------------------------------------------------------------------
# 1. Load
# --------------------------------------------------------------------------
log("loading cached tables")
ppl = pp.load_participants(ROOT, CACHE)
pairs = pp.build_pairs(ROOT, CACHE)
metrics = dd.load_metrics()
extra_o = dd.extra_outcomes(pairs)
extra_p = dd.extra_predictors()
d = dd.add_covariates(ppl.merge(extra_p, on="PtID", how="left")).merge(metrics, on="PtID", how="left").merge(extra_o, on="PtID", how="left")
base_cols = ["PtID", "sex", "male", "arm", "arm_cgm_bgm", "age", "weight_kg", "height_cm", "bmi", "hba1c_screening", "diabetes_duration_yrs", "cv_pct", "pct_below_70",
             "low_bias_pct", "low_mard", "low_n_pairs", "missed_low_rate", "false_low_rate", "n_meter_low", "n_cgm_low", "cgm_days_in_window", "site"]
f0 = d[base_cols].copy()

v = pairs["verified"].merge(ppl[["PtID", "sex", "arm", "randomisation_day"]], on="PtID", how="left")
v["sex"] = pd.Categorical(v.sex.astype(str), ["F", "M"])
v["male"] = (v.sex == "M").astype(int)
v["arm_cgm_bgm"] = (v.arm.astype(str) == "CGM+BGM").astype(int)
v["phase"] = np.where(v.day < v.randomisation_day, "run-in", "randomised")
v["roc3"] = roc3(v.rate_of_change)
v["wear1"] = (v.session_confirmed_by_cal & (v.wear_day == 1)).astype(int)
v["wear2_7"] = v.session_confirmed_by_cal & v.wear_day.between(2, 7)
v["night"] = v.is_night.astype(int)
v["device"] = v.device_model.astype(str)
cal = pairs["calibration"]
cal = cal[cal.in_study_window].merge(ppl[["PtID", "sex"]], on="PtID", how="left")
cal["sex"] = pd.Categorical(cal.sex.astype(str), ["F", "M"])
cal["male"] = (cal.sex == "M").astype(int)
log(f"verified pairs {len(v):,} ({v.PtID.nunique()} people); calibration pairs in window {len(cal):,}; low pairs (avg < 70): {(v.avg < 70).sum():,}")

STATS["run"] = {"date": "2026-11-06", "seed": SEED, "n_boot": N_BOOT, "min_low_pairs": MIN_LOW_PAIRS, "min_group": MIN_GROUP, "min_stratum_pairs": MIN_STRATUM,
                "lag_shift_s": LAG_SHIFT_S, "cache_version": pp.CACHE_VERSION, "maude_skipped": SKIP_MAUDE,
                "pairs": {"verified": int(len(v)), "verified_low_avg_lt_70": int((v.avg < 70).sum()), "calibration_in_window": int(len(cal)),
                          "verified_low_by_sex": v[v.avg < 70].groupby("sex", observed=True).size().to_dict()},
                "meter_models_in_verified_pairs": v.device.value_counts().to_dict()}

# --------------------------------------------------------------------------
# 2. Pre-registration: the whole test list, written before any test runs
# --------------------------------------------------------------------------
SPLITS = [  # id, label, frame key, description
    ("anchor_low", "Verified pairs, average below 70 (the original test; anchor, not counted)", "The pre-registered result from DEMOGRAPHICS_DEEP.md"),
    ("band_lt54", "Average below 54", "glucose band"), ("band_54_69", "Average 54-69", "glucose band"),
    ("wear1", "Sensor wear day 1 (confirmed sessions)", "wear day"), ("wear2_7", "Sensor wear days 2-7 (confirmed sessions)", "wear day"),
    ("night", "Night pairs (00:00-06:00)", "time of day"), ("daytime", "Daytime pairs (06:00-24:00)", "time of day"),
    ("falling", "Glucose falling (ROC < -1 mg/dL/min)", "trend"), ("flat", "Glucose flat (ROC -1 to 1)", "trend"), ("rising", "Glucose rising (ROC > 1)", "trend"),
    ("lag", "Lag-corrected pairs (CGM 5 min later), average below 70", "lag"),
    ("meter_contour", "Contour Next meter pairs", "meter type"), ("meter_precision", "Precision Xtra meter pairs", "meter type"),
    ("arm_cgm_only", "CGM-only arm (all days)", "arm"), ("arm_cgm_bgm", "CGM+BGM arm (all days)", "arm"),
    ("phase_runin", "Run-in phase, both arms", "phase"), ("phase_rand_cgm_only", "Randomised phase, CGM-only arm", "phase"),
    ("phase_rand_cgm_bgm", "Randomised phase, CGM+BGM arm (the check set)", "phase"),
    ("cal_low", "Calibration pairs, average below 70 (other pair source)", "pair source"),
    ("low_by_ref", "Low by fingerstick (fingerstick below 70)", "which device defines low"), ("low_by_cgm", "Low by sensor (CGM below 70)", "which device defines low"),
    ("mid", "Mid range: average 70-180", "other ranges"), ("high", "High range: average above 180", "other ranges"), ("all", "All verified pairs", "other ranges"),
]
PROFILE = [  # id, label, source
    ("pct_below_70", "% of CGM time below 70 mg/dL", "CGM trace"), ("episodes_per_day", "CGM low episodes per day (3+ readings below 70)", "CGM trace"),
    ("episode_nadir", "Mean lowest CGM value of the episodes (mg/dL)", "CGM trace"), ("episode_minutes", "Mean episode length (min)", "CGM trace"),
    ("episode_pct_lt54", "% of episodes reaching below 54", "CGM trace"), ("episode_pct_night", "% of episodes starting at night (00-06)", "CGM trace"),
    ("episode_slope", "Mean CGM slope in the 15 min before the episode (mg/dL/min)", "CGM trace"), ("episode_pct_fast", "% of episodes entered fast (slope < -1)", "CGM trace"),
    ("low_n", "Number of low pairs (average below 70)", "pairs"), ("low_ref_mean", "Mean fingerstick of the low pairs (mg/dL)", "pairs"),
    ("low_pct_ref_lt54", "% of low pairs with fingerstick below 54", "pairs"), ("low_pct_night", "% of low pairs at night", "pairs"),
    ("low_roc_mean", "Mean ROC at the low pairs (mg/dL/min)", "pairs"), ("low_pct_falling", "% of low pairs with glucose falling", "pairs"),
    ("low_pct_wear1", "% of low pairs on wear day 1", "pairs"), ("low_pct_clipped", "% of low pairs with the CGM at its 39 mg/dL floor", "pairs"),
]
MATCHING = [("pooled", "Pooled low pairs, no matching (mixed model, male only)"), ("matched_avg_roc", "Matched on glucose bin (5 mg/dL of the average) and trend"),
            ("matched_full", "Matched on glucose bin and trend, plus night, wear day 1 and arm"), ("matched_ref_roc", "Sensitivity: matched on fingerstick bin (5 mg/dL) and trend")]
ADJUST = [("male_only", "Sex alone", []), ("weight", "+ weight", ["weight_kg"]), ("bmi", "+ BMI", ["bmi"]), ("height", "+ height", ["height_cm"]),
          ("hba1c", "+ HbA1c", ["hba1c_screening"]), ("age", "+ age", ["age"]), ("tdd_per_kg", "+ insulin dose per kg (TDD / weight)", ["tdd_per_kg"]),
          ("all_body", "+ weight, BMI, height, HbA1c, age, dose per kg", ["weight_kg", "bmi", "height_cm", "hba1c_screening", "age", "tdd_per_kg"]),
          ("all_body_glucose", "+ the six above + CV + % time below 70", ["weight_kg", "bmi", "height_cm", "hba1c_screening", "age", "tdd_per_kg", "cv_pct", "pct_below_70"])]
WITHIN = [("weight_kg", "weight"), ("bmi", "BMI"), ("height_cm", "height"), ("hba1c_screening", "HbA1c"), ("age", "age"), ("tdd_per_kg", "insulin dose per kg")]
SHANGHAI_TESTS = [("sh_low_avg", "Shanghai: pairs with average below 70, pooled bias by sex"), ("sh_low_ref", "Shanghai: pairs with fingerstick below 70"), ("sh_mid", "Shanghai: pairs with average 70-180 (context)")]
MAUDE_TESTS = [("m_reads_low_share", "Share of pairs where the sensor read below the meter"), ("m_reads_low_depth", "Depth of reads-low pairs: median error, % of meter"),
               ("m_hidden_low", "Hidden low: meter below 70 and sensor 70 or more"), ("m_meter_lt70", "Meter below 70 (any sensor value)"), ("m_false_low", "False low: sensor below 70 and meter 70 or more")]
DECISION = [("near_false_low", "Pairs with fingerstick 70-79: % with CGM below 70 (false low near the line)"), ("near_missed_low", "Pairs with fingerstick 60-69: % with CGM 70 or more (missed low near the line)")]
STATS["preregistration"] = {
    "written_before_tests_ran": True,
    "unit": "participant (per-person mean bias on 20+ pairs), Mann-Whitney, bootstrap CI of the difference in medians, men minus women; pooled-pair checks use a participant bootstrap",
    "fallback_rule": "a split is testable per person when 10+ people of each sex have 20+ pairs in it; otherwise the registered p comes from a mixed model (random intercept per person) "
                     "on the pooled pairs of that split, and the estimate shown is the pooled men-minus-women gap with a participant-bootstrap CI. Both versions are reported for every split.",
    "families": {"replace_bg": "blocks A (splits), B (low profile and matching), C (body and physiology), F (decision thresholds); one BH family",
                 "shanghai": "block D", "maude": "block E"},
    "A_splits": [{"id": i, "label": l, "group": g} for i, l, g in SPLITS] + [{"id": "sex_x_arm", "label": "Sex x arm interaction on low-range bias (OLS, HC3)", "group": "arm"}],
    "B_profile": [{"id": i, "label": l, "source": s} for i, l, s in PROFILE],
    "B_matching": [{"id": i, "label": l} for i, l in MATCHING],
    "C_adjusted": [{"id": i, "label": l, "covariates": c} for i, l, c in ADJUST],
    "C_within_sex": [f"{lab} vs low-range bias, within {s}" for _, lab in WITHIN for s in ("women", "men")],
    "D_shanghai": [{"id": i, "label": l} for i, l in SHANGHAI_TESTS],
    "E_maude": [{"id": i, "label": l} for i, l in MAUDE_TESTS],
    "F_decision": [{"id": i, "label": l} for i, l in DECISION],
    "not_counted": ["anchor_low (the original result)", "mg/dL versions of each split (reported next to the % version)", "missed-low and false-low rates by sex (already in the DEMOGRAPHICS_DEEP family)",
                    "descriptive rows (pooled bias by glucose bin, lookup-table numbers)"],
}
with open(os.path.join(OUT, "demographics_followup_stats.json"), "w", encoding="utf-8") as fh:
    json.dump(dd.clean(STATS), fh, indent=1)
log("pre-registration written")

# --------------------------------------------------------------------------
# 3. Block A: where is the gap? Splits of the per-person low-range bias
# --------------------------------------------------------------------------
log("loading the CGM table for lag correction and low episodes")
cgm = pp.load_cgm(ROOT, CACHE)
cw = cgm[cgm.in_study_window & ~cgm.glucose_missing][["PtID", "t", "glucose", "hour"]].copy()
del cgm
cw["t"] = cw.t.astype("int64")
right = cw[["PtID", "t", "glucose"]].rename(columns={"t": "t2", "glucose": "cgm2"}).sort_values("t2", kind="stable")


def repair(frame, shift_s, tol_s=LAG_TOL_S):
    """CGM reading nearest to (fingerstick time + shift) within tol, per person; NaN when none."""
    left = pd.DataFrame({"PtID": frame.PtID.to_numpy(), "target": frame.t.to_numpy().astype("int64") + shift_s, "idx": np.arange(len(frame))})
    m = pd.merge_asof(left.sort_values("target", kind="stable"), right, left_on="target", right_on="t2", by="PtID", direction="nearest", tolerance=tol_s)
    return m.sort_values("idx").cgm2.to_numpy(float)


agree0 = float(np.nanmean(repair(v, 0) == v.cgm.to_numpy(float)))
cgm_lag = repair(v, LAG_SHIFT_S)
vl = v.copy()
vl["cgm"] = cgm_lag
vl["err"] = vl.cgm - vl.ref
vl["rel_err_pct"] = vl.err / vl.ref * 100
vl["avg"] = (vl.cgm + vl.ref) / 2
vl = vl[vl.cgm.notna()]
log(f"re-pairing at T=0 reproduces the cached CGM value in {agree0 * 100:.2f} % of pairs; lag-corrected pairs {len(vl):,}")

low = v.avg < 70
frames = {
    "anchor_low": v[low], "band_lt54": v[v.avg < 54], "band_54_69": v[(v.avg >= 54) & (v.avg < 70)],
    "wear1": v[low & (v.wear1 == 1)], "wear2_7": v[low & v.wear2_7], "night": v[low & v.is_night], "daytime": v[low & ~v.is_night],
    "falling": v[low & (v.roc3 == "falling")], "flat": v[low & (v.roc3 == "flat")], "rising": v[low & (v.roc3 == "rising")],
    "lag": vl[vl.avg < 70], "meter_contour": v[low & (v.device == "Contour Next")], "meter_precision": v[low & v.device.str.contains("Precision")],
    "arm_cgm_only": v[low & (v.arm_cgm_bgm == 0)], "arm_cgm_bgm": v[low & (v.arm_cgm_bgm == 1)],
    "phase_runin": v[low & (v.phase == "run-in")], "phase_rand_cgm_only": v[low & (v.phase == "randomised") & (v.arm_cgm_bgm == 0)],
    "phase_rand_cgm_bgm": v[low & (v.phase == "randomised") & (v.arm_cgm_bgm == 1)],
    "cal_low": cal[cal.avg < 70], "low_by_ref": v[v.ref < 70], "low_by_cgm": v[v.cgm < 70],
    "mid": v[(v.avg >= 70) & (v.avg <= 180)], "high": v[v.avg > 180], "all": v,
}
f = f0.copy()
for key, _, _ in SPLITS:
    f = f.merge(per_person(frames[key], key).reset_index(), on="PtID", how="left")
A = {}
for key, label, group in SPLITS:
    r = sex_gap(f, f"{key}_bias", label, mgdl_col=f"{key}_err_mgdl")
    r["group"] = group
    r["pairs_F"] = int(len(frames[key][frames[key].sex == "F"]))
    r["pairs_M"] = int(len(frames[key][frames[key].sex == "M"]))
    r["pooled"] = pooled_sex_gap(frames[key])
    if r["testable"]:
        r["p_from"] = "per-person Mann-Whitney"
    else:                                                     # pre-specified fallback: pooled pairs, mixed-model p
        r["pooled"]["mixed"] = mixed_male(frames[key], "rel_err_pct ~ male")
        r["p"] = r["pooled"]["mixed"]["p"]
        r["p_from"] = "mixed model on pooled pairs (fallback: fewer than 10 people per sex with 20+ pairs)"
    if key == "anchor_low":
        r["anchor"] = True
    else:
        register("replace_bg", "A_splits", key, label, r)
    A[key] = r
    pl = r["pooled"]
    log(f"A {key:>20}: W {fmt(r['median_F'])} ({r['n_F']}) vs M {fmt(r['median_M'])} ({r['n_M']}); M-W {fmt(r['diff_median_M_minus_F'], 1, True)} "
        f"({fmt(r['ci_low'], 1, True)} to {fmt(r['ci_high'], 1, True)}) p {fmt_p(r['p'])} [{r['p_from'][:12]}]; pooled {fmt(pl.get('bias_F'))}/{fmt(pl.get('bias_M'))} "
        f"gap {fmt(pl.get('gap_M_minus_F'), 1, True)} ({fmt(pl.get('ci_low'), 1, True)} to {fmt(pl.get('ci_high'), 1, True)}) pairs {r['pairs_F']:,}/{r['pairs_M']:,}")
# sex x arm interaction (difference of differences), and the same within the randomised phase
f["rand_bias"] = np.where(f.arm_cgm_bgm == 1, f.phase_rand_cgm_bgm_bias, f.phase_rand_cgm_only_bias)
inter = {}
for name, col in [("all_days", "anchor_low_bias"), ("randomised_phase", "rand_bias")]:
    sub = f.dropna(subset=[col])
    fit = smf.ols(f"{col} ~ male * arm_cgm_bgm", sub).fit(cov_type="HC3")
    ci = fit.conf_int()
    inter[name] = {"n": int(fit.nobs), "interaction_coef": float(fit.params["male:arm_cgm_bgm"]), "ci_low": float(ci.loc["male:arm_cgm_bgm", 0]),
                   "ci_high": float(ci.loc["male:arm_cgm_bgm", 1]), "p": float(fit.pvalues["male:arm_cgm_bgm"]),
                   "gap_cgm_only": float(fit.params["male"]), "gap_cgm_bgm": float(fit.params["male"] + fit.params["male:arm_cgm_bgm"])}
register("replace_bg", "A_splits", "sex_x_arm", "Sex x arm interaction on low-range bias (OLS, HC3)", inter["all_days"])
A["sex_x_arm"] = inter
STATS["A_splits"] = A
STATS["A_splits"]["lag_check"] = {"t0_repairing_matches_cache_share": agree0, "lag_corrected_pairs": int(len(vl))}
STATS["A_splits"]["note_meter_type"] = f"Precision Xtra pairs are {int(v.device.str.contains('Precision').sum())} of {len(v):,} verified pairs; not testable"
log("block A done")

# --------------------------------------------------------------------------
# 4. Block B: sensor or person? Low-glucose profile by sex, then matching
# --------------------------------------------------------------------------
# 4a. CGM low episodes from the trace (3+ consecutive readings below 70, gaps under 10 min)
cw = cw.sort_values(["PtID", "t"], kind="stable").reset_index(drop=True)
g = cw.glucose.to_numpy(float)
t = cw.t.to_numpy()
p = cw.PtID.to_numpy()
hour = cw.hour.to_numpy(float)
is_low = g < 70
same_prev = np.r_[False, p[1:] == p[:-1]]
gap_s = np.r_[np.inf, np.diff(t).astype(float)]
contiguous = same_prev & (gap_s <= 600)
new_run = ~contiguous | (is_low != np.r_[False, is_low[:-1]])
run_id = np.cumsum(new_run)
idx = np.arange(len(g))
runs = pd.DataFrame({"run": run_id[is_low], "PtID": p[is_low], "g": g[is_low], "i": idx[is_low]}).groupby("run").agg(PtID=("PtID", "first"), n=("g", "size"), nadir=("g", "min"), i0=("i", "min"))
ep = runs[runs.n >= EPISODE_MIN_READINGS].copy()
i0 = ep.i0.to_numpy()
ok3 = (i0 >= 3)
ib = np.where(ok3, i0 - 3, 0)
ok3 &= (p[ib] == p[i0]) & ((t[i0] - t[ib]) >= 780) & ((t[i0] - t[ib]) <= 1020)
slope = np.where(ok3, (g[i0] - g[ib]) / np.maximum((t[i0] - t[ib]) / 60, 1), np.nan)
ep["slope"] = slope
ep["night"] = hour[i0] < 6
ep["minutes"] = ep.n * 5
ep["lt54"] = ep.nadir < 54
ep["fast"] = ep.slope < -1
epp = ep.groupby("PtID").agg(n_episodes=("n", "size"), episode_nadir=("nadir", "mean"), episode_minutes=("minutes", "mean"), episode_pct_lt54=("lt54", "mean"),
                             episode_pct_night=("night", "mean"), episode_slope=("slope", "mean"), episode_pct_fast=("fast", lambda s: s[ep.loc[s.index, "slope"].notna()].mean()))
for c in ["episode_pct_lt54", "episode_pct_night", "episode_pct_fast"]:
    epp[c] *= 100
f = f.merge(epp.reset_index(), on="PtID", how="left")
f["n_episodes"] = f.n_episodes.fillna(0)
f["episodes_per_day"] = f.n_episodes / f.cgm_days_in_window
del g, t, p, hour, is_low, same_prev, gap_s, contiguous, new_run, run_id, idx, cw
log(f"CGM low episodes: {len(ep):,} (3+ readings below 70) in {ep.PtID.nunique()} people; slope known for {int(ep.slope.notna().sum()):,}")

# 4b. The low pairs themselves (verified, average below 70): depth, time, trend, wear day, clipping
lowp = v[low].copy()
lowp["avg_bin"] = pd.cut(lowp.avg, AVG_EDGES, right=False, labels=AVG_LABELS).astype(str)
lowp["ref_bin"] = pd.cut(lowp.ref, REF_EDGES, right=False, labels=REF_LABELS).astype(str)
lowp["ref_lt54"] = lowp.ref < 54
lowp["falling"] = lowp.roc3 == "falling"
lowp["clipped"] = lowp.is_clipped_low.astype(bool)
prof = lowp.groupby("PtID").agg(low_n=("err", "size"), low_ref_mean=("ref", "mean"), low_pct_ref_lt54=("ref_lt54", "mean"), low_pct_night=("is_night", "mean"),
                                low_roc_mean=("rate_of_change", "mean"), low_pct_falling=("falling", "mean"), low_pct_wear1=("wear1", "mean"), low_pct_clipped=("clipped", "mean"))
for c in ["low_pct_ref_lt54", "low_pct_night", "low_pct_falling", "low_pct_wear1", "low_pct_clipped"]:
    prof[c] *= 100
prof.loc[prof.low_n < MIN_LOW_PAIRS, [c for c in prof.columns if c != "low_n"]] = np.nan     # shares only for the people whose bias was compared
f = f.drop(columns=[c for c in prof.columns if c in f]).merge(prof.reset_index(), on="PtID", how="left")
f["low_n"] = f.low_n.fillna(0)
B = {"profile": {}}
for key, label, source in PROFILE:
    r = sex_gap(f, key, label)
    r["source"] = source
    register("replace_bg", "B_profile", key, label, r)
    B["profile"][key] = r
    log(f"B {key:>18}: W {fmt(r['median_F'], 2)} vs M {fmt(r['median_M'], 2)}; diff {fmt(r['diff_median_M_minus_F'], 2, True)} p {fmt_p(r['p'])}")

# 4c. Matching: the sex gap on the same low pairs, pooled, then within glucose x trend strata (participant bootstrap), and as mixed models
lowp["stratum_avg_roc"] = lowp.avg_bin + "|" + lowp.roc3.astype(str)
lowp["stratum_ref_roc"] = lowp.ref_bin + "|" + lowp.roc3.astype(str)
B["matching"] = {
    "pooled": {"standardised": pooled_sex_gap(lowp), "mixed": mixed_male(lowp, "rel_err_pct ~ male")},
    "matched_avg_roc": {"standardised": pooled_sex_gap(lowp, strata="stratum_avg_roc"), "mixed": mixed_male(lowp, "rel_err_pct ~ male + C(avg_bin) + C(roc3)")},
    "matched_full": {"standardised": None, "mixed": mixed_male(lowp, "rel_err_pct ~ male + C(avg_bin) + C(roc3) + night + wear1 + arm_cgm_bgm")},
    "matched_ref_roc": {"standardised": pooled_sex_gap(lowp, strata="stratum_ref_roc"), "mixed": mixed_male(lowp, "rel_err_pct ~ male + C(ref_bin) + C(roc3)")},
}
for key, label in MATCHING:
    register("replace_bg", "B_matching", key, label, B["matching"][key]["mixed"])
    m = B["matching"][key]["mixed"]
    s = B["matching"][key]["standardised"]
    log(f"B matching {key:>16}: mixed {fmt(m['coef_male'], 2, True)} ({fmt(m['ci_low'], 2, True)} to {fmt(m['ci_high'], 2, True)}) p {fmt_p(m['p'])}"
        + (f"; standardised {fmt(s['gap_M_minus_F'], 2, True)} ({fmt(s['ci_low'], 2, True)} to {fmt(s['ci_high'], 2, True)}), strata {s['strata_used']}/{s['strata_total']}" if s else ""))
# the mix of low pairs by stratum, by sex (where women's and men's low pairs sit)
mix = lowp.groupby(["sex", "avg_bin"], observed=True).size().unstack(0).fillna(0)
B["matching"]["low_pair_mix_by_avg_bin_pct"] = {s: (mix[s] / mix[s].sum() * 100).round(1).to_dict() for s in ["F", "M"]}
mix2 = lowp.groupby(["sex", "roc3"], observed=True).size().unstack(0).fillna(0)
B["matching"]["low_pair_mix_by_trend_pct"] = {s: (mix2[s] / mix2[s].sum() * 100).round(1).to_dict() for s in ["F", "M"]}
B["matching"]["bias_by_stratum"] = {k: {"pairs_F": int(gg[gg.sex == "F"].shape[0]), "pairs_M": int(gg[gg.sex == "M"].shape[0]),
                                        "bias_F": float(gg[gg.sex == "F"].rel_err_pct.mean()) if (gg.sex == "F").any() else None,
                                        "bias_M": float(gg[gg.sex == "M"].rel_err_pct.mean()) if (gg.sex == "M").any() else None}
                                    for k, gg in lowp.groupby("stratum_avg_roc")}
# pooled bias by glucose bin for the figure (women vs men, participant bootstrap CIs)
v["fig_bin"] = pd.cut(v.avg, FIG_EDGES, right=False, labels=FIG_LABELS).astype(str)
by_bin = {}
for b in FIG_LABELS:
    r = pooled_sex_gap(v[v.fig_bin == b])
    by_bin[b] = r
# per-sex CIs for the bins (participant bootstrap of each sex's pooled bias)
for b in FIG_LABELS:
    sub = v[v.fig_bin == b]
    for s in ["F", "M"]:
        ss = sub[sub.sex == s]
        gsum = ss.groupby("PtID").rel_err_pct.agg(["sum", "size"])
        if len(gsum) == 0:
            by_bin[b][f"ci_{s}"] = [None, None]
            continue
        W = RNG.multinomial(len(gsum), np.full(len(gsum), 1 / len(gsum)), size=N_BOOT).astype(float)
        boot = (W @ gsum["sum"].to_numpy()) / (W @ gsum["size"].to_numpy())
        by_bin[b][f"ci_{s}"] = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
B["pooled_bias_by_glucose_bin"] = by_bin
STATS["B_profile_and_matching"] = B
log("block B done")

# --------------------------------------------------------------------------
# 5. Block C: body and physiology
# --------------------------------------------------------------------------
pu = pp.load_pump(ROOT, CACHE)
ba = pu["basal"]
ba = ba[ba.in_study_window & ~ba.duration_suspect & ba.duration_min.notna()]
bday = pd.DataFrame({"PtID": ba.PtID.to_numpy(), "day": ba.day.to_numpy(), "u": (ba.rate_u_per_h.fillna(0) * ba.duration_min / 60).to_numpy(),
                     "h": (ba.duration_min / 60).to_numpy()}).groupby(["PtID", "day"]).sum()
bday = bday[(bday.h >= 20) & (bday.h <= 28)]
bo = pu["bolus"]
bo = bo[bo.in_study_window]
boday = bo.groupby(["PtID", "day"]).total_u.sum().rename("bolus_u")
tdd = bday.join(boday, how="left").fillna({"bolus_u": 0.0})
tdd["tdd"] = tdd.u + tdd.bolus_u
per_tdd = tdd.groupby("PtID").agg(tdd_days=("tdd", "size"), tdd_u=("tdd", "median"), basal_u=("u", "median"), bolus_u=("bolus_u", "median")).reset_index()
per_tdd.loc[per_tdd.tdd_days < MIN_TDD_DAYS, ["tdd_u", "basal_u", "bolus_u"]] = np.nan
f = f.merge(per_tdd, on="PtID", how="left")
f["tdd_per_kg"] = f.tdd_u / f.weight_kg
del pu, ba, bo, bday, boday, tdd
log(f"insulin dose: {int(f.tdd_u.notna().sum())} people with {MIN_TDD_DAYS}+ pump days; median TDD {f.tdd_u.median():.1f} U, {f.tdd_per_kg.median():.2f} U/kg")

C = {"by_sex": {}, "adjusted": {}, "within_sex": {}}
for col, lab in WITHIN + [("cv_pct", "glucose CV (%)"), ("pct_below_70", "% CGM time below 70"), ("tdd_u", "TDD (U/day)"), ("basal_u", "basal (U/day)"), ("bolus_u", "bolus (U/day)")]:
    C["by_sex"][col] = {"label": lab, "F": dd.describe(f.loc[f.sex == "F", col]), "M": dd.describe(f.loc[f.sex == "M", col])}
for key, label, covs in ADJUST:
    terms = [("male", "Male vs female")] + [(c, c) for c in covs]
    r = dd.fit_ols(f, "low_bias_pct", terms)
    male = r["terms"][0]
    res = {"label": label, "n": r["n"], "r2": r["r2"], "coef_male": male["coef"], "ci_low": male["ci_low"], "ci_high": male["ci_high"], "p": male["p"],
           "covariate_terms": r["terms"][1:]}
    register("replace_bg", "C_adjusted", key, f"Low-range bias by sex, {label}", res)
    C["adjusted"][key] = res
    log(f"C adjusted {key:>16}: male {fmt(res['coef_male'], 2, True)} ({fmt(res['ci_low'], 2, True)} to {fmt(res['ci_high'], 2, True)}) p {fmt_p(res['p'])} n {res['n']}")
for col, lab in WITHIN:
    for s, sname in [("F", "women"), ("M", "men")]:
        sub = f[f.sex == s]
        r = dd.spearman_ci(sub[col], sub["low_bias_pct"])
        r["label"] = f"{lab} vs low-range bias, within {sname}"
        register("replace_bg", "C_within_sex", f"{col}_{s}", r["label"], r)
        C["within_sex"][f"{col}_{s}"] = r
# labs: what exists
smp = pd.read_csv(os.path.join(pp.rb_dir(ROOT), "Sample.txt"), sep="|", usecols=["Analyte"])
sh_cols = list(pp.load_shanghai(ROOT, CACHE)["patients"].columns)
C["lab_values_available"] = {"replace_bg_central_lab_analytes": sorted(smp.Analyte.dropna().unique().tolist()),
                             "replace_bg_screening_measurements": ["weight", "height", "HbA1c (local and central lab)"],
                             "shanghai_lab_columns": [c for c in sh_cols if any(k in c for k in ("Plasma", "C-peptide", "Insulin (", "HbA1c", "Albumin", "Cholesterol", "Triglyceride", "Lipoprotein", "Creatinine", "Filtration", "Uric", "Urea"))],
                             "haematocrit_or_haemoglobin": "not present in either dataset"}
STATS["C_body_physiology"] = C
log("block C done")

# --------------------------------------------------------------------------
# 6. Block D: Shanghai (Abbott flash sensor)
# --------------------------------------------------------------------------
sh = pp.load_shanghai(ROOT, CACHE)
pt = sh["patients"].copy()
pt["group"] = pt.group.astype(str)
pt["pid"] = pt.pid.astype(str)
pt = pt.sort_values(["group", "pid", "visit"]).drop_duplicates(["group", "pid"])[["group", "pid", "sex"]]
sp = pairs["shanghai"].copy()
sp["group"] = sp.group.astype(str)
sp["pid"] = sp.pid.astype(str)
sp = sp.merge(pt, on=["group", "pid"], how="left")
sp["sex"] = pd.Categorical(sp.sex.astype(str), ["F", "M"])
sp["male"] = (sp.sex == "M").astype(int)
sp["PtID"] = sp.group + "_" + sp.pid
D = {"pairs": int(len(sp)), "patients": int(sp.PtID.nunique()), "patients_by_sex": sp.drop_duplicates("PtID").sex.value_counts().to_dict(),
     "patients_with_20plus_low_pairs": int((sp[sp.avg < 70].groupby("PtID").size() >= MIN_LOW_PAIRS).sum())}
for key, label in SHANGHAI_TESTS:
    sub = {"sh_low_avg": sp[sp.avg < 70], "sh_low_ref": sp[sp.ref < 70], "sh_mid": sp[(sp.avg >= 70) & (sp.avg <= 180)]}[key]
    r = {"label": label, "standardised": pooled_sex_gap(sub, by="PtID"), "mixed": mixed_male(sub, "rel_err_pct ~ male", groups="PtID")}
    r["p"] = r["mixed"]["p"]
    register("shanghai", "D_shanghai", key, label, r)
    D[key] = r
    s = r["standardised"]
    log(f"D {key}: W {fmt(s.get('bias_F'))} % ({s['pairs_F']} pairs, {s['people_F']} pt) vs M {fmt(s.get('bias_M'))} % ({s['pairs_M']}, {s['people_M']}); "
        f"gap {fmt(s.get('gap_M_minus_F'), 1, True)} ({fmt(s.get('ci_low'), 1, True)} to {fmt(s.get('ci_high'), 1, True)}); mixed p {fmt_p(r['p'])}")
STATS["D_shanghai"] = D
log("block D done")

# --------------------------------------------------------------------------
# 7. Block E: MAUDE complaint texts (Dexcom, sex filled) - a weak outside check
# --------------------------------------------------------------------------
E = {"skipped": SKIP_MAUDE}
if not SKIP_MAUDE:
    sys.path.insert(0, os.path.join(REPO, "fda-maude", "scripts"))
    import text_results as tr
    import brand_comparison as bc
    paths = {"jsonl": os.path.join(REPO, "fda-maude", "clean", "text_extract_v3.jsonl"), "run_set": os.path.join(REPO, "fda-maude", "clean", "run_set.csv.gz"),
             "serious": os.path.join(REPO, "fda-maude", "clean", "serious.csv.gz"), "sample": os.path.join(REPO, "fda-maude", "clean", "sample_local.parquet"),
             "family_map": os.path.join(REPO, "fda-maude", "results", "report", "tables", "d_problem_family_mapping.csv")}
    missing = [k for k, pth in paths.items() if not os.path.exists(pth)]
    if missing:
        E["skipped"] = True
        E["reason"] = f"files not found: {missing}"
        log("MAUDE skipped:", E["reason"])
    else:
        log("loading MAUDE text results (about a minute)")
        mdf = tr.load_jsonl(paths["jsonl"])
        rs = bc.load_run_set_ext(paths["run_set"])
        mdf = mdf.merge(rs.drop(columns=["event_type", "maker"]), on="mdr_report_key", how="left")
        mdf["split"] = mdf["split"].fillna(mdf["tier"])
        mdf = tr.add_code_flags(mdf, tr.load_family_map(paths["family_map"]))
        mdf["brand"] = [bc.brand_of(m, mf, b) for m, mf, b in zip(mdf["maker"], mdf["manufacturer"], mdf["brand_name"])]
        mdf["wr"] = mdf["fault_type"].isin(bc.WRONG_TEXT) | mdf["code_wrong_family"].fillna(False).astype(bool)
        demo = bc.load_demographics(paths["serious"], paths["sample"])
        mdf = mdf.merge(demo, on="mdr_report_key", how="left")
        mdf["sex"] = mdf["sex"].fillna("not filled")
        mp, n_drop = tr.pairs_frame(mdf)
        mp = mp[mp["wr"] & (mp["split"] == "serious")].copy()
        mp["reads_low"] = mp["err_mgdl"] < 0
        mp["hidden_low"] = (mp["meter"] < 70) & (mp["sensor"] >= 70)
        mp["meter_lt70"] = mp["meter"] < 70
        mp["false_low"] = (mp["sensor"] < 70) & (mp["meter"] >= 70)
        rng_m = np.random.default_rng(SEED)
        E["set"] = {"what": "serious wrong-reading reports (model fault type reads_low/high/erratic/stuck, or FDA code in the wrong-readings family) that state a sensor and a meter value",
                    "pairs_all_brands": int(len(mp)), "pairs_with_sex_all_brands": int(mp["sex"].isin(["Female", "Male"]).sum()),
                    "pairs_dexcom": int((mp["brand"] == "Dexcom").sum()), "pairs_dexcom_with_sex": int(((mp["brand"] == "Dexcom") & mp["sex"].isin(["Female", "Male"])).sum()),
                    "share_of_sexed_pairs_that_are_dexcom": float(((mp["brand"] == "Dexcom") & mp["sex"].isin(["Female", "Male"])).sum() / max(mp["sex"].isin(["Female", "Male"]).sum(), 1))}

        def maude_block(sub):
            fe, ma = sub[sub["sex"] == "Female"], sub[sub["sex"] == "Male"]
            out = {"pairs_F": int(len(fe)), "pairs_M": int(len(ma))}
            out["m_reads_low_share"] = bc.share_test(int(fe.reads_low.sum()), len(fe), int(ma.reads_low.sum()), len(ma), rng_m, 1000)
            rl_f, rl_m = fe.loc[fe.reads_low, "err_pct"], ma.loc[ma.reads_low, "err_pct"]
            out["m_reads_low_depth"] = bc.size_test(rl_f, rl_m, rng_m, 1000)
            out["m_reads_low_depth"]["median_meter_F"] = float(fe.loc[fe.reads_low, "meter"].median()) if len(rl_f) else None
            out["m_reads_low_depth"]["median_meter_M"] = float(ma.loc[ma.reads_low, "meter"].median()) if len(rl_m) else None
            out["m_reads_low_depth"]["median_err_mgdl_F"] = float(fe.loc[fe.reads_low, "err_mgdl"].median()) if len(rl_f) else None
            out["m_reads_low_depth"]["median_err_mgdl_M"] = float(ma.loc[ma.reads_low, "err_mgdl"].median()) if len(rl_m) else None
            for key in ["m_hidden_low", "m_meter_lt70", "m_false_low"]:
                col = key[2:]
                out[key] = bc.share_test(int(fe[col].sum()), len(fe), int(ma[col].sum()), len(ma), rng_m, 1000)
            return out

        E["dexcom"] = maude_block(mp[mp["brand"] == "Dexcom"])
        E["all_brands_context"] = maude_block(mp)
        E["abbott_context"] = maude_block(mp[mp["brand"] == "Abbott"])
        for key, label in MAUDE_TESTS:
            r = E["dexcom"][key]
            r["label"] = label
            r["p"] = r.get("mann_whitney_p", r.get("chi_square_p"))
            register("maude", "E_maude", key, label, r)
            log(f"E Dexcom {key}: " + (f"W {fmt(r['share_a_pct'])} % vs M {fmt(r['share_b_pct'])} %, diff {fmt(r['risk_diff_points'], 1, True)} ({fmt(r['risk_diff_ci_low'], 1, True)} to {fmt(r['risk_diff_ci_high'], 1, True)})"
                                        if "share_a_pct" in r else f"W median {fmt(r['median_a'])} % vs M {fmt(r['median_b'])} %, diff {fmt(r['median_diff_a_minus_b'], 1, True)} ({fmt(r['median_diff_ci_low'], 1, True)} to {fmt(r['median_diff_ci_high'], 1, True)})") + f" p {fmt_p(r['p'])}")
        del mdf, rs, demo
STATS["E_maude"] = E
log("block E done")

# --------------------------------------------------------------------------
# 8. Block F: does 2.5 mg/dL at 60 matter? Threshold crossings and the simulation lookup
# --------------------------------------------------------------------------
F = {}
near = {"near_false_low": (v[(v.ref >= 70) & (v.ref < 80)], "cgm_lt70"), "near_missed_low": (v[(v.ref >= 60) & (v.ref < 70)], "cgm_ge70")}
v["cgm_lt70"] = v.cgm < 70
v["cgm_ge70"] = v.cgm >= 70
for key, label in DECISION:
    sub, flag = near[key]
    sub = v.loc[sub.index]
    r = pooled_share_gap(sub, flag)
    r["label"] = label
    # p from a mixed model on the 0/100 indicator (random intercept per person)
    mm = sub[["PtID", "male", flag]].copy()
    mm["rel_err_pct"] = mm[flag].astype(float) * 100
    r["mixed"] = mixed_male(mm, "rel_err_pct ~ male")
    r["p"] = r["mixed"]["p"]
    register("replace_bg", "F_decision", key, label, r)
    F[key] = r
    log(f"F {key}: W {fmt(r['share_F'])} % vs M {fmt(r['share_M'])} %; diff {fmt(r['diff_M_minus_F'], 1, True)} ({fmt(r['ci_low'], 1, True)} to {fmt(r['ci_high'], 1, True)}) p {fmt_p(r['p'])}")
F["missed_low_rate_by_sex"] = sex_gap(f, "missed_low_rate", "Per-person missed-low rate (fingerstick below 70, CGM 70 or more), %")
F["false_low_rate_by_sex"] = sex_gap(f, "false_low_rate", "Per-person false-low rate (CGM below 70, fingerstick 70 or more), %")
F["missed_low_rate_by_sex"]["anchor"] = F["false_low_rate_by_sex"]["anchor"] = True
lk_path = os.path.join(OUT, "simulation_v2_lookup.csv")
if os.path.exists(lk_path):
    lk = pd.read_csv(lk_path).sort_values("bias_pct")
    cols = {"skipped_pct_median": "corrections skipped (% of all corrections)", "skipped_of_needed_pct_median": "corrections skipped (% of needed)", "changed_1_pct_median": "doses changed by 1 U or more (%)",
            "low70_false_per_day_median": "false low alerts per day", "low70_missed_pct_median": "true lows missed (%)", "tir_pct_median": "time in range shown (%)",
            "tbr70_pct_median": "time below 70 shown (%)", "lbgi_median": "LBGI (low blood glucose index)"}
    medF, medM = A["anchor_low"]["median_F"], A["anchor_low"]["median_M"]
    points = {"women_median_low_bias": medF, "men_median_low_bias": medM, "zero": 0.0, "minus_4_2": -4.2, "plus_4_2": 4.2}
    F["lookup"] = {"source": lk_path, "note": "the lookup applies one constant bias to the whole CGM trace all day; the sex gap exists only below 70 mg/dL, so these are upper bounds for what the gap alone could do",
                   "at": {name: {lab: float(np.interp(b, lk.bias_pct, lk[c])) for c, lab in cols.items()} for name, b in points.items()}}
    F["lookup"]["women_minus_men"] = {lab: F["lookup"]["at"]["women_median_low_bias"][lab] - F["lookup"]["at"]["men_median_low_bias"][lab] for lab in cols.values()}
    F["lookup"]["gap_in_mgdl_at_60"] = float((medM - medF) / 100 * 60)
STATS["F_decision"] = F
log("block F done")

# --------------------------------------------------------------------------
# 8b. Block G (post hoc, added after seeing the arm result; NOT in the BH families):
#     could selective fingerstick testing make the gap? In the blinded run-in the person could not see the
#     sensor, so a fingerstick could not be chosen because the sensor looked low. Also: how often each sex
#     tested, and how often their tests were low, by arm.
# --------------------------------------------------------------------------
v = v.merge(ppl[["PtID", "initial_study_cgm"]], on="PtID", how="left")
v["blinded"] = v.initial_study_cgm.astype(str) == "Blinded"
G = {"note": "post hoc, after seeing the arm result; not pre-registered and not counted in the BH families", "splits": {}}
g_splits = [("runin_blinded", "Run-in, blinded CGM (person could not see the sensor), average below 70", v[low & (v.phase == "run-in") & v.blinded]),
            ("runin_standard", "Run-in, standard (visible) CGM, average below 70", v[low & (v.phase == "run-in") & ~v.blinded]),
            ("runin_blinded_cal", "Run-in, blinded CGM, calibration pairs below 70", cal.merge(ppl[["PtID", "randomisation_day", "initial_study_cgm"]], on="PtID").query("day < randomisation_day and initial_study_cgm == 'Blinded' and avg < 70"))]
fg = f0[["PtID", "sex", "male"]].copy()
for key, label, frame in g_splits:
    fg = fg.merge(per_person(frame, key).reset_index(), on="PtID", how="left")
    r = sex_gap(fg, f"{key}_bias", label, mgdl_col=f"{key}_err_mgdl")
    r["pairs_F"], r["pairs_M"] = int((frame.sex == "F").sum()), int((frame.sex == "M").sum())
    r["pooled"] = pooled_sex_gap(frame)
    r["pooled"]["mixed"] = mixed_male(frame, "rel_err_pct ~ male")
    G["splits"][key] = r
    pl = r["pooled"]
    log(f"G {key:>18}: per person W {fmt(r['median_F'])} ({r['n_F']}) vs M {fmt(r['median_M'])} ({r['n_M']}) gap {fmt(r['diff_median_M_minus_F'], 1, True)} ({fmt(r['ci_low'], 1, True)} to {fmt(r['ci_high'], 1, True)}) p {fmt_p(r['p'])}; "
        f"pooled {fmt(pl.get('bias_F'))}/{fmt(pl.get('bias_M'))} gap {fmt(pl.get('gap_M_minus_F'), 1, True)} ({fmt(pl.get('ci_low'), 1, True)} to {fmt(pl.get('ci_high'), 1, True)}) mixed p {fmt_p(pl['mixed']['p'])} pairs {r['pairs_F']:,}/{r['pairs_M']:,}")
# testing behaviour: fingersticks per day and the share of them that were low, by sex, overall and by arm in the randomised phase
beh = v.groupby("PtID").agg(pairs=("err", "size"), low_pairs=("avg", lambda a: int((a < 70).sum()))).reset_index().merge(f0[["PtID", "sex", "arm_cgm_bgm", "cgm_days_in_window"]], on="PtID")
beh["pairs_per_day"] = beh.pairs / beh.cgm_days_in_window
beh["pct_pairs_low"] = beh.low_pairs / beh.pairs * 100
rp = v[v.phase == "randomised"].groupby("PtID").agg(r_pairs=("err", "size"), r_low=("avg", lambda a: int((a < 70).sum())), r_days=("day", "nunique")).reset_index()
beh = beh.merge(rp, on="PtID", how="left")
beh["r_pairs_per_day"] = beh.r_pairs / beh.r_days
beh["r_pct_pairs_low"] = beh.r_low / beh.r_pairs * 100
G["testing_behaviour"] = {"all_days": {c: sex_gap(beh, c, c) for c in ["pairs_per_day", "pct_pairs_low"]},
                          "randomised_phase_by_arm": {arm: {c: sex_gap(beh[beh.arm_cgm_bgm == k], c, c) for c in ["r_pairs_per_day", "r_pct_pairs_low"]} for arm, k in [("CGM-only", 0), ("CGM+BGM", 1)]}}
STATS["G_posthoc"] = G
log("block G (post hoc) done")

# --------------------------------------------------------------------------
# 9. BH over the families, write the JSON
# --------------------------------------------------------------------------
STATS["bh_summary"] = finish_families()
STATS["run"]["runtime_s"] = round(time.time() - T0, 1)
with open(os.path.join(OUT, "demographics_followup_stats.json"), "w", encoding="utf-8") as fh:
    json.dump(dd.clean(STATS), fh, indent=1)
log("stats written;", {k: (vv["n_tests"], vv["n_raw_p_below_0_05"], vv["n_pass_bh"]) for k, vv in STATS["bh_summary"].items()}, "(tests, raw p<0.05, pass BH)")

# --------------------------------------------------------------------------
# 10. Figure 35
# --------------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.25, 1.0, 1.05]})
# (a) forest of the splits
ax = axes[0]
order = [k for k, _, _ in SPLITS if k not in ("meter_contour", "meter_precision", "all")]
short = {"anchor_low": "All low pairs (original)", "band_lt54": "Average below 54", "band_54_69": "Average 54-69", "wear1": "Wear day 1", "wear2_7": "Wear days 2-7",
         "night": "Night 00-06", "daytime": "Daytime", "falling": "Falling glucose", "flat": "Flat glucose", "rising": "Rising glucose", "lag": "Lag-corrected (+5 min)",
         "arm_cgm_only": "CGM-only arm", "arm_cgm_bgm": "CGM+BGM arm", "phase_runin": "Run-in phase", "phase_rand_cgm_only": "Randomised, CGM-only",
         "phase_rand_cgm_bgm": "Randomised, CGM+BGM", "cal_low": "Calibration pairs", "low_by_ref": "Low by fingerstick", "low_by_cgm": "Low by sensor",
         "mid": "Mid range 70-180", "high": "High range >180"}
ys = np.arange(len(order))[::-1]
ylabels = []
for y, k in zip(ys, order):
    r = A[k]
    col = INK if k == "anchor_low" else (C_BLUE if k not in ("mid", "high") else MUTED)
    if r["testable"]:
        est, lo, hi = r["diff_median_M_minus_F"], r["ci_low"], r["ci_high"]
        ax.errorbar(est, y, xerr=[[est - lo], [hi - est]], fmt="o", ms=4, color=col, ecolor=col, elinewidth=1, capsize=2)
        ylabels.append(f"{short[k]} ({r['n_F']}/{r['n_M']})")
    else:                                                 # fallback: pooled pairs (hollow marker)
        pl = r["pooled"]
        est, lo, hi = pl.get("gap_M_minus_F"), pl.get("ci_low"), pl.get("ci_high")
        if est is not None and lo is not None:
            ax.errorbar(est, y, xerr=[[est - lo], [hi - est]], fmt="o", ms=4, mfc=SURFACE, color=col, ecolor=col, elinewidth=1, capsize=2)
        ylabels.append(f"{short[k]} ({r['pairs_F']:,}/{r['pairs_M']:,} pairs)")
ax.axvline(0, color=AXIS, lw=1)
ax.axvline(A["anchor_low"]["diff_median_M_minus_F"], color=INK, lw=0.8, ls=":")
ax.set_yticks(ys)
ax.set_yticklabels(ylabels, fontsize=7.5)
ax.set_xlim(-6, 13)
ax.set_xlabel("men minus women, bias (points of %); lines: 95 % CI")
ax.set_title("(a) The gap is in every split of the low range, not above it")
ax.text(-5.8, -0.9, "labels: women/men with 20+ pairs; hollow = pooled pairs where too few people qualify", fontsize=6.8, color=INK2, va="top")
# (b) pooled bias by glucose bin, women vs men
ax = axes[1]
x = np.arange(len(FIG_LABELS))
for s, col, lab, off in [("F", C_F, "women", -0.08), ("M", C_M, "men", 0.08)]:
    vals = np.array([by_bin[b][f"bias_{s}"] for b in FIG_LABELS], float)
    lo = np.array([by_bin[b][f"ci_{s}"][0] for b in FIG_LABELS], float)
    hi = np.array([by_bin[b][f"ci_{s}"][1] for b in FIG_LABELS], float)
    ax.errorbar(x + off, vals, yerr=[vals - lo, hi - vals], fmt="o-", ms=4, color=col, ecolor=col, elinewidth=0.9, capsize=2, label=lab, lw=1.3)
ax.axhline(0, color=AXIS, lw=1)
ax.axvline(5.5, color=GRID, lw=1)
ax.set_xticks(x)
ax.set_xticklabels(FIG_LABELS, rotation=60, ha="right", fontsize=7)
ax.set_ylim(-14, 10)
ax.set_xlabel("average of CGM and fingerstick (mg/dL)")
ax.set_ylabel("pooled bias: CGM minus fingerstick (%)")
ax.grid(axis="y")
ax.grid(False, axis="x")
ax.legend(loc="lower right")
ax.set_title("(b) Women's sensors read lower only below 70")
ax.text(0.05, 9.2, "below 70: women read 3-4 points lower in every bin (y-axis cut at +10)", fontsize=6.8, color=INK2, va="top")
# (c) matching and adjustment
ax = axes[2]
rows_c = [("Original: per-person medians", A["anchor_low"]["diff_median_M_minus_F"], A["anchor_low"]["ci_low"], A["anchor_low"]["ci_high"], INK),
          ("Pooled pairs, no matching", B["matching"]["pooled"]["standardised"]["gap_M_minus_F"], B["matching"]["pooled"]["standardised"]["ci_low"], B["matching"]["pooled"]["standardised"]["ci_high"], C_BLUE),
          ("Matched: glucose bin x trend", B["matching"]["matched_avg_roc"]["standardised"]["gap_M_minus_F"], B["matching"]["matched_avg_roc"]["standardised"]["ci_low"], B["matching"]["matched_avg_roc"]["standardised"]["ci_high"], C_BLUE),
          ("Matched + night, wear day 1, arm\n(mixed model)", B["matching"]["matched_full"]["mixed"]["coef_male"], B["matching"]["matched_full"]["mixed"]["ci_low"], B["matching"]["matched_full"]["mixed"]["ci_high"], C_BLUE),
          ("Matched: fingerstick bin x trend", B["matching"]["matched_ref_roc"]["standardised"]["gap_M_minus_F"], B["matching"]["matched_ref_roc"]["standardised"]["ci_low"], B["matching"]["matched_ref_roc"]["standardised"]["ci_high"], C_BLUE),
          ("Adjusted: weight, BMI, height,\nHbA1c, age, insulin per kg", C["adjusted"]["all_body"]["coef_male"], C["adjusted"]["all_body"]["ci_low"], C["adjusted"]["all_body"]["ci_high"], C_AQUA),
          ("+ glucose CV, % time below 70", C["adjusted"]["all_body_glucose"]["coef_male"], C["adjusted"]["all_body_glucose"]["ci_low"], C["adjusted"]["all_body_glucose"]["ci_high"], C_AQUA)]
ys = np.arange(len(rows_c))[::-1]
for y, (lab, est, lo, hi, col) in zip(ys, rows_c):
    ax.errorbar(est, y, xerr=[[est - lo], [hi - est]], fmt="o", ms=4, color=col, ecolor=col, elinewidth=1, capsize=2)
    ax.text(est, y + 0.22, f"{est:+.1f}", ha="center", va="bottom", fontsize=7.5, color=INK2)
ax.axvline(0, color=AXIS, lw=1)
ax.set_yticks(ys)
ax.set_yticklabels([r[0] for r in rows_c], fontsize=7.5)
ax.set_ylim(-0.7, len(rows_c) - 0.2)
ax.set_xlim(-2, 9)
ax.set_xlabel("men minus women, bias below 70 mg/dL (points of %)")
ax.set_title("(c) Matching on glucose level and trend does not remove it")
fig.suptitle(f"Figure 35. In the low range the Dexcom G4 reads lower in women than in men: where it is, and what does not explain it "
             f"(REPLACE-BG, {len(v):,} verified fingerstick pairs, {len(lowp):,} below 70 mg/dL)", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
fig.text(0.01, -0.02, "Bias = CGM minus fingerstick as % of the fingerstick; negative = sensor reads low. Low range = average of CGM and fingerstick below 70 mg/dL. "
         "Panels a and c: positive = men's sensors read higher than women's. Panel b: participant-bootstrap 95 % CIs.", fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(os.path.join(FIG, "35_sex_low_range_bias.png"))
plt.close(fig)
log("wrote figure 35")

# --------------------------------------------------------------------------
# 11. Markdown tables for the memo
# --------------------------------------------------------------------------
print("\n### Block A: splits (per-person low-range bias, %; medians (n people); men minus women, difference in medians with CI)")
md(["Split", "Women", "Men", "Men minus women (CI)", "p", "BH p"], [gap_row(A[k]["label"], A[k]) for k, _, _ in SPLITS])
print("mg/dL medians (women / men): " + "; ".join(f"{k}: {fmt(A[k].get('median_mgdl_F'))} / {fmt(A[k].get('median_mgdl_M'))}" for k, _, _ in SPLITS if A[k]["testable"]))
print("pooled pairs (women / men bias %, pairs): " + "; ".join(f"{k}: {fmt(A[k]['pooled'].get('bias_F'))} / {fmt(A[k]['pooled'].get('bias_M'))} ({A[k]['pairs_F']:,} / {A[k]['pairs_M']:,})" for k, _, _ in SPLITS))
print(f"sex x arm interaction: all days {fmt(inter['all_days']['interaction_coef'], 1, True)} ({fmt(inter['all_days']['ci_low'], 1, True)} to {fmt(inter['all_days']['ci_high'], 1, True)}) p {fmt_p(inter['all_days']['p'])} BH {fmt_p(inter['all_days'].get('p_bh'))}; "
      f"randomised phase {fmt(inter['randomised_phase']['interaction_coef'], 1, True)} ({fmt(inter['randomised_phase']['ci_low'], 1, True)} to {fmt(inter['randomised_phase']['ci_high'], 1, True)}) p {fmt_p(inter['randomised_phase']['p'])}\n")
print("### Block B: low-glucose profile by sex (per person; medians)")
md(["Measure", "Women (n)", "Men (n)", "Men minus women (CI)", "p", "BH p"], [[B["profile"][k]["label"], f"{fmt(B['profile'][k]['median_F'], 2)} ({B['profile'][k]['n_F']})", f"{fmt(B['profile'][k]['median_M'], 2)} ({B['profile'][k]['n_M']})",
                                                                            f"{fmt(B['profile'][k]['diff_median_M_minus_F'], 2, True)} ({fmt(B['profile'][k]['ci_low'], 2, True)} to {fmt(B['profile'][k]['ci_high'], 2, True)})", fmt_p(B["profile"][k]["p"]), fmt_p(B["profile"][k].get("p_bh"))] for k, _, _ in PROFILE])
print("### Block B: matching")
rows = []
for k, lab in MATCHING:
    s, m = B["matching"][k]["standardised"], B["matching"][k]["mixed"]
    rows.append([lab, f"{fmt(s['gap_M_minus_F'], 1, True)} ({fmt(s['ci_low'], 1, True)} to {fmt(s['ci_high'], 1, True)}); strata {s['strata_used']}, pairs {s['pairs_used']:,}" if s else "(regression only)",
                 f"{fmt(m['coef_male'], 1, True)} ({fmt(m['ci_low'], 1, True)} to {fmt(m['ci_high'], 1, True)})", fmt_p(m["p"]), fmt_p(m.get("p_bh"))])
md(["Comparison", "Standardised gap, men minus women (CI)", "Mixed-model gap (CI)", "p", "BH p"], rows)
print("low-pair mix by glucose bin, % of each sex's low pairs:", json.dumps(B["matching"]["low_pair_mix_by_avg_bin_pct"]))
print("low-pair mix by trend:", json.dumps(B["matching"]["low_pair_mix_by_trend_pct"]), "\n")
print("### Block C: body and physiology")
md(["Variable", "Women median (IQR)", "Men median (IQR)"], [[C["by_sex"][c]["label"], f"{fmt(C['by_sex'][c]['F']['median'], 2)} ({fmt(C['by_sex'][c]['F']['q1'], 2)}-{fmt(C['by_sex'][c]['F']['q3'], 2)}; n {C['by_sex'][c]['F']['n']})",
                                                              f"{fmt(C['by_sex'][c]['M']['median'], 2)} ({fmt(C['by_sex'][c]['M']['q1'], 2)}-{fmt(C['by_sex'][c]['M']['q3'], 2)}; n {C['by_sex'][c]['M']['n']})"] for c in C["by_sex"]])
md(["Model for low-range bias", "n", "Sex term: men minus women (CI)", "p", "BH p"], [[C["adjusted"][k]["label"], C["adjusted"][k]["n"], f"{fmt(C['adjusted'][k]['coef_male'], 1, True)} ({fmt(C['adjusted'][k]['ci_low'], 1, True)} to {fmt(C['adjusted'][k]['ci_high'], 1, True)})",
                                                                                      fmt_p(C["adjusted"][k]["p"]), fmt_p(C["adjusted"][k].get("p_bh"))] for k, _, _ in ADJUST])
md(["Within-sex correlation with low-range bias", "Women: rho (CI), p, BH p", "Men: rho (CI), p, BH p"], [[lab, f"{fmt(C['within_sex'][c + '_F']['rho'], 2, True)} ({fmt(C['within_sex'][c + '_F']['ci_low'], 2, True)} to {fmt(C['within_sex'][c + '_F']['ci_high'], 2, True)}), p {fmt_p(C['within_sex'][c + '_F']['p'])}, BH {fmt_p(C['within_sex'][c + '_F'].get('p_bh'))}",
                                                                                                           f"{fmt(C['within_sex'][c + '_M']['rho'], 2, True)} ({fmt(C['within_sex'][c + '_M']['ci_low'], 2, True)} to {fmt(C['within_sex'][c + '_M']['ci_high'], 2, True)}), p {fmt_p(C['within_sex'][c + '_M']['p'])}, BH {fmt_p(C['within_sex'][c + '_M'].get('p_bh'))}"] for c, lab in WITHIN])
print("labs available:", json.dumps(C["lab_values_available"]), "\n")
print("### Block D: Shanghai")
md(["Pairs", "Women: bias % (pairs, patients)", "Men: bias % (pairs, patients)", "Men minus women (CI)", "mixed-model p", "BH p"],
   [[D[k]["label"], f"{fmt(D[k]['standardised'].get('bias_F'))} ({D[k]['standardised']['pairs_F']}, {D[k]['standardised']['people_F']})", f"{fmt(D[k]['standardised'].get('bias_M'))} ({D[k]['standardised']['pairs_M']}, {D[k]['standardised']['people_M']})",
     f"{fmt(D[k]['standardised'].get('gap_M_minus_F'), 1, True)} ({fmt(D[k]['standardised'].get('ci_low'), 1, True)} to {fmt(D[k]['standardised'].get('ci_high'), 1, True)})", fmt_p(D[k]["p"]), fmt_p(D[k].get("p_bh"))] for k, _ in SHANGHAI_TESTS])
if not E.get("skipped"):
    print("### Block E: MAUDE (Dexcom serious wrong-reading pairs with sex filled)")
    rows = []
    for k, lab in MAUDE_TESTS:
        r = E["dexcom"][k]
        if "share_a_pct" in r:
            rows.append([lab, f"{fmt(r['share_a_pct'])} %", f"{fmt(r['share_b_pct'])} %", f"{fmt(r['risk_diff_points'], 1, True)} ({fmt(r['risk_diff_ci_low'], 1, True)} to {fmt(r['risk_diff_ci_high'], 1, True)})", fmt_p(r["p"]), fmt_p(r.get("p_bh"))])
        else:
            rows.append([lab, f"{fmt(r['median_a'])} % (meter {fmt(r['median_meter_F'], 0)})", f"{fmt(r['median_b'])} % (meter {fmt(r['median_meter_M'], 0)})", f"{fmt(r['median_diff_a_minus_b'], 1, True)} ({fmt(r['median_diff_ci_low'], 1, True)} to {fmt(r['median_diff_ci_high'], 1, True)})", fmt_p(r["p"]), fmt_p(r.get("p_bh"))])
    md(["Measure", f"Women ({E['dexcom']['pairs_F']:,} pairs)", f"Men ({E['dexcom']['pairs_M']:,} pairs)", "Women minus men (CI)", "p", "BH p"], rows)
    for ctx in ["all_brands_context", "abbott_context"]:
        r = E[ctx]
        print(f"{ctx}: pairs W {r['pairs_F']:,} / M {r['pairs_M']:,}; reads low {fmt(r['m_reads_low_share']['share_a_pct'])} / {fmt(r['m_reads_low_share']['share_b_pct'])} %; depth median {fmt(r['m_reads_low_depth']['median_a'])} / {fmt(r['m_reads_low_depth']['median_b'])} %; "
              f"hidden low {fmt(r['m_hidden_low']['share_a_pct'])} / {fmt(r['m_hidden_low']['share_b_pct'])} %; false low {fmt(r['m_false_low']['share_a_pct'])} / {fmt(r['m_false_low']['share_b_pct'])} %")
    print()
print("### Block F: decisions")
for k, _ in DECISION:
    r = F[k]
    print(f"{r['label']}: women {fmt(r['share_F'])} % vs men {fmt(r['share_M'])} %; men minus women {fmt(r['diff_M_minus_F'], 1, True)} ({fmt(r['ci_low'], 1, True)} to {fmt(r['ci_high'], 1, True)}); p {fmt_p(r['p'])}; BH {fmt_p(r.get('p_bh'))}; pairs {r['pairs_F']:,} / {r['pairs_M']:,}")
for k in ["missed_low_rate_by_sex", "false_low_rate_by_sex"]:
    r = F[k]
    print(f"{r['label']}: women {fmt(r['median_F'])} ({r['n_F']}) vs men {fmt(r['median_M'])} ({r['n_M']}); diff {fmt(r['diff_median_M_minus_F'], 1, True)} ({fmt(r['ci_low'], 1, True)} to {fmt(r['ci_high'], 1, True)}); p {fmt_p(r['p'])} (anchor, from the deep check)")
if "lookup" in F:
    md(["Lookup row (constant bias on the whole trace)"] + list(F["lookup"]["at"].keys()), [[lab] + [fmt(F["lookup"]["at"][n][lab], 2) for n in F["lookup"]["at"]] for lab in F["lookup"]["at"]["zero"]])
    print(f"gap at 60 mg/dL: {F['lookup']['gap_in_mgdl_at_60']:.2f} mg/dL")
print("\n### Block G: post hoc (not in the BH families)")
md(["Split", "Women", "Men", "Men minus women (CI)", "p", "Pooled gap (CI); mixed-model p"],
   [gap_row(r["label"], r)[:5] + [f"{fmt(r['pooled'].get('gap_M_minus_F'), 1, True)} ({fmt(r['pooled'].get('ci_low'), 1, True)} to {fmt(r['pooled'].get('ci_high'), 1, True)}); p {fmt_p(r['pooled']['mixed']['p'])}"] for r in G["splits"].values()])
tb = G["testing_behaviour"]
for c, lab in [("pairs_per_day", "verified fingersticks per day"), ("pct_pairs_low", "% of fingersticks that were low (average below 70)")]:
    r = tb["all_days"][c]
    print(f"{lab}, all days: women {fmt(r['median_F'], 2)} vs men {fmt(r['median_M'], 2)}; diff {fmt(r['diff_median_M_minus_F'], 2, True)} ({fmt(r['ci_low'], 2, True)} to {fmt(r['ci_high'], 2, True)}); p {fmt_p(r['p'])}")
for arm in ["CGM-only", "CGM+BGM"]:
    for c, lab in [("r_pairs_per_day", "fingersticks per day"), ("r_pct_pairs_low", "% low")]:
        r = tb["randomised_phase_by_arm"][arm][c]
        print(f"randomised phase, {arm} arm, {lab}: women {fmt(r['median_F'], 2)} ({r['n_F']}) vs men {fmt(r['median_M'], 2)} ({r['n_M']}); diff {fmt(r['diff_median_M_minus_F'], 2, True)} ({fmt(r['ci_low'], 2, True)} to {fmt(r['ci_high'], 2, True)}); p {fmt_p(r['p'])}")
print("\n### BH summary")
for name, s in STATS["bh_summary"].items():
    print(f"{name}: {s['n_tests']} tests, {s['n_raw_p_below_0_05']} with raw p < 0.05 ({s['expected_by_chance']:.1f} expected by chance), {s['n_pass_bh']} pass BH; smallest BH p {fmt_p(s['smallest_p_bh'])}")
    for t_ in s["passed"]:
        print(f"   pass: {t_['block']} / {t_['id']}: {t_['label']} (p {fmt_p(t_['p'])}, BH {fmt_p(t_['p_bh'])})")
log(f"done in {time.time() - T0:.0f} s")
