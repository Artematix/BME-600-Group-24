"""
Subgroup analysis for BMEN 600 Group 24: who gets worse CGM sensor accuracy?

Unit of analysis = the participant (REPLACE-BG, 226 adults, Dexcom G4).
For each person we measure sensor accuracy on independent meter pairs
(fingersticks NOT used to calibrate the sensor) inside the study window
(day 0-329). Then we compare people by age, sex, BMI, HbA1c, diabetes
duration and study arm (pre-specified list), and by a longer exploratory list
(Benjamini-Hochberg corrected, at least 10 people per group, else "not
testable"). Shanghai (Abbott flash CGM) is the small comparator.

Run from the repo root (about 1 minute once the preprocess cache exists;
the first run builds the cache, about 40 s more):
    python analysis/subgroups.py "Uncommitted Data/Raw Data Dump" analysis

Outputs (under the second argument, default analysis/):
    participant_metrics.csv          one row per participant, PtID only
    cache/participant_metrics.parquet
    subgroups_stats.json             every number used in SUBGROUPS.md
    figures/21_participant_mard_distribution.png
    figures/22_prespecified_forest.png
    figures/23_strongest_association.png
    figures/24_exploratory_forest.png

Terms. MARD = mean absolute relative difference: the average size of the
sensor error as a percent of the fingerstick value. ARD = that size for one
pair. Bias = mean signed error in percent (negative = sensor reads low).
CV = coefficient of variation = glucose SD / mean glucose, in percent.
IQR = interquartile range, the middle half of people (25th to 75th percentile).
"""
import json
import os
import sys
import textwrap
import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preprocess as pp  # shared loaders + parquet cache (analysis/preprocess.py)

warnings.filterwarnings("ignore", category=FutureWarning)

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

ROOT = sys.argv[1] if len(sys.argv) > 1 else pp.DEFAULT_ROOT
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis"
CACHE = sys.argv[3] if len(sys.argv) > 3 else pp.DEFAULT_CACHE
FIG = os.path.join(OUT, "figures")

SEED = 600                 # fixed so every run gives the same bootstrap numbers
N_BOOT = 2000              # bootstrap resamples (participants resampled with replacement)
MIN_GROUP = 10             # fewer people than this in a group = "not testable"
MIN_LOW_PAIRS = 20         # pairs below 70 mg/dL needed for a low-range MARD
MIN_BLOCK_PAIRS = 20       # pairs needed in each half / each meter source for within-person tests
MIN_SHANGHAI_PAIRS = 10    # pairs needed for a Shanghai per-patient MARD
ALPHA = 0.05

RNG = np.random.default_rng(SEED)
T0 = time.time()
STATS = {}


def log(*a):
    """Print a progress line with elapsed seconds."""
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Chart styling (same palette as explore_raw_data.py)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#86b6ef", "#2a78d6", "#104281"]
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "font.size": 9,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 10, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 1.5, "savefig.dpi": 150, "savefig.bbox": "tight",
})


def save(fig, name):
    """Save a figure into the figures folder and close it."""
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


# --------------------------------------------------------------------------
# Small statistics helpers
# --------------------------------------------------------------------------
def q(x, p):
    """Percentile of a 1-D array ignoring NaN."""
    return float(np.nanpercentile(np.asarray(x, float), p))


def describe(x):
    """n, median, IQR and mean of a per-participant metric (NaN ignored)."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return {"n": 0, "median": None, "q1": None, "q3": None, "mean": None}
    return {"n": int(len(x)), "median": float(np.median(x)), "q1": q(x, 25), "q3": q(x, 75), "mean": float(x.mean())}


def boot_diff(ref, grp, stat=np.median):
    """Difference (group minus reference) of a statistic, with a bootstrap 95 % CI.

    Participants are resampled with replacement inside each group, N_BOOT times.
    Returns (estimate, ci_low, ci_high)."""
    a = np.asarray(ref, float)
    b = np.asarray(grp, float)
    ia = RNG.integers(0, len(a), (N_BOOT, len(a)))
    ib = RNG.integers(0, len(b), (N_BOOT, len(b)))
    d = stat(b[ib], axis=1) - stat(a[ia], axis=1)
    return float(stat(b) - stat(a)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def boot_paired(x, y, stat=np.median):
    """Within-person difference y - x: statistic of the paired differences with a bootstrap 95 % CI."""
    d = np.asarray(y, float) - np.asarray(x, float)
    idx = RNG.integers(0, len(d), (N_BOOT, len(d)))
    b = stat(d[idx], axis=1)
    return float(stat(d)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def spearman_ci(x, y):
    """Spearman rank correlation with p-value and a bootstrap 95 % CI (participants resampled)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    rho, p = stats.spearmanr(x, y)
    idx = RNG.integers(0, len(x), (N_BOOT, len(x)))
    rx = stats.rankdata(x[idx], axis=1)
    ry = stats.rankdata(y[idx], axis=1)
    rx = rx - rx.mean(axis=1, keepdims=True)
    ry = ry - ry.mean(axis=1, keepdims=True)
    r = (rx * ry).sum(axis=1) / np.sqrt((rx ** 2).sum(axis=1) * (ry ** 2).sum(axis=1))
    return {"n": int(len(x)), "rho": float(rho), "ci_low": float(np.percentile(r, 2.5)),
            "ci_high": float(np.percentile(r, 97.5)), "p": float(p)}


def detectable_diff(a, b):
    """Smallest difference in means the two groups could detect with 80 % power (two-sided 5 %).

    Rule of thumb: 2.8 x pooled SD x sqrt(1/n1 + 1/n2)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    sd = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float(2.8 * sd * np.sqrt(1 / len(a) + 1 / len(b)))


def bh(pvals):
    """Benjamini-Hochberg adjusted p-values (false discovery rate), NaN kept as NaN."""
    p = np.asarray(pvals, float)
    out = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    if ok.sum() > 0:
        out[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return out


def group_test(df, var, outcome, label, reference=None, order=None):
    """Compare a per-participant outcome between the groups of one variable.

    Groups with fewer than MIN_GROUP people are left out and listed. Two groups:
    Mann-Whitney U. Three or more: Kruskal-Wallis. Each group is contrasted with the
    reference group (default: the first group) as the difference in medians with a
    bootstrap 95 % CI, plus the smallest detectable difference in means."""
    d = df[[var, outcome]].dropna()
    if order is None:
        order = list(d[var].cat.categories) if hasattr(d[var], "cat") else sorted(d[var].unique())
    counts = d[var].value_counts()
    groups = [{"group": str(g), "n": int(counts.get(g, 0)), **{k: v for k, v in describe(d.loc[d[var] == g, outcome]).items() if k != "n"}}
              for g in order if counts.get(g, 0) > 0]
    keep = [g for g in order if counts.get(g, 0) >= MIN_GROUP]
    small = [{"group": str(g), "n": int(counts.get(g, 0))} for g in order if 0 < counts.get(g, 0) < MIN_GROUP]
    res = {"variable": var, "label": label, "outcome": outcome, "groups": groups, "excluded_small_groups": small,
           "testable": len(keep) >= 2, "test": None, "p": None, "reference": None, "contrasts": []}
    if not res["testable"]:
        res["reason"] = f"fewer than 2 groups with at least {MIN_GROUP} people"
        return res
    ref = reference if reference in keep else keep[0]
    samples = [d.loc[d[var] == g, outcome].values for g in keep]
    if len(keep) == 2:
        res["test"] = "Mann-Whitney U"
        res["p"] = float(stats.mannwhitneyu(samples[0], samples[1], alternative="two-sided").pvalue)
    else:
        res["test"] = "Kruskal-Wallis"
        res["p"] = float(stats.kruskal(*samples).pvalue)
    res["reference"] = str(ref)
    a = d.loc[d[var] == ref, outcome].values
    for g in keep:
        if g == ref:
            continue
        b = d.loc[d[var] == g, outcome].values
        est, lo, hi = boot_diff(a, b)
        res["contrasts"].append({"group": str(g), "vs": str(ref), "n": int(len(b)), "n_ref": int(len(a)),
                                 "diff_median": est, "ci_low": lo, "ci_high": hi,
                                 "detectable_diff_means": detectable_diff(a, b)})
    return res


def paired_test(x, y, label, outcome="mard"):
    """Within-person comparison (y minus x) with a Wilcoxon signed-rank p and a bootstrap CI."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    res = {"label": label, "outcome": outcome, "n": int(len(x)), "testable": len(x) >= MIN_GROUP,
           "test": "Wilcoxon signed-rank", "median_x": float(np.median(x)) if len(x) else None,
           "median_y": float(np.median(y)) if len(x) else None}
    if res["testable"]:
        est, lo, hi = boot_paired(x, y)
        res.update({"diff_median": est, "ci_low": lo, "ci_high": hi,
                    "p": float(stats.wilcoxon(y, x).pvalue)})
    else:
        res.update({"p": None, "reason": f"fewer than {MIN_GROUP} people with both values"})
    return res


def fit_ols(df, outcome, terms, log_outcome=False, bh_terms=None):
    """OLS of a per-participant outcome on the listed terms with HC3 robust standard errors.

    terms: list of (column, label). Binary columns must be 0/1. Returns n, R squared and,
    per term, the coefficient per unit, 95 % CI, p, BH-adjusted p (over `bh_terms`),
    and the coefficient per 1 SD of the covariate (binary terms: per group).
    log_outcome=True fits log(outcome); coefficients are then also given as percent change."""
    cols = [c for c, _ in terms]
    d = df[[outcome] + cols].dropna()
    y = np.log(d[outcome]) if log_outcome else d[outcome]
    X = sm.add_constant(d[cols].astype(float))
    fit = sm.OLS(y, X).fit(cov_type="HC3")
    ci = fit.conf_int()
    bh_set = set(bh_terms or cols)
    p_adj = dict(zip([c for c in cols if c in bh_set], bh([fit.pvalues[c] for c in cols if c in bh_set])))
    rows = []
    for c, lab in terms:
        binary = set(np.unique(d[c])).issubset({0, 1})
        scale = 1.0 if binary else float(d[c].std(ddof=1))
        row = {"term": c, "label": lab, "coef": float(fit.params[c]), "ci_low": float(ci.loc[c, 0]),
               "ci_high": float(ci.loc[c, 1]), "p": float(fit.pvalues[c]),
               "p_bh": float(p_adj[c]) if c in p_adj else None, "sd": None if binary else scale,
               "coef_per_sd": float(fit.params[c] * scale), "ci_low_per_sd": float(ci.loc[c, 0] * scale),
               "ci_high_per_sd": float(ci.loc[c, 1] * scale)}
        if log_outcome:
            row["pct_change_per_unit"] = float((np.exp(fit.params[c]) - 1) * 100)
            row["pct_change_ci"] = [float((np.exp(ci.loc[c, 0]) - 1) * 100), float((np.exp(ci.loc[c, 1]) - 1) * 100)]
        rows.append(row)
    return {"outcome": ("log " if log_outcome else "") + outcome, "n": int(fit.nobs), "r2": float(fit.rsquared),
            "r2_adj": float(fit.rsquared_adj), "se": "HC3 robust", "terms": rows}


def clean(o):
    """Make a nested result JSON-safe (numpy numbers to Python, NaN to null, floats rounded)."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else round(float(o), 4)
    return o


# --------------------------------------------------------------------------
# Per-participant metrics
# --------------------------------------------------------------------------
def within_20_20(err, ref):
    """True when the CGM is within 20 mg/dL (reference below 100 mg/dL) or within 20 % (100 or more)."""
    err = np.asarray(err, float)
    ref = np.asarray(ref, float)
    return np.where(ref < 100, np.abs(err) <= 20, np.abs(err) / ref <= 0.20)


def accuracy_block(df, prefix=""):
    """Accuracy of one block of pairs: n, MARD, median ARD, bias (%), percent within 20/20."""
    return pd.Series({
        prefix + "n_pairs": len(df),
        prefix + "mard": df.abs_rel_err_pct.mean(),
        prefix + "median_ard": df.abs_rel_err_pct.median(),
        prefix + "bias_pct": df.rel_err_pct.mean(),
        prefix + "pct_within_20_20": within_20_20(df.err.values, df.ref.values).mean() * 100,
    })


def pump_family(s):
    """Group the pump model string into one family: Medtronic, OmniPod, Animas, Tandem, unknown code, multiple."""
    if not isinstance(s, str) or s.strip() in ("", "None"):
        return np.nan
    fams = set()
    for tok in s.split(";"):
        t = tok.strip()
        if t == "multiple":
            fams.add("multiple")
        elif "Paradigm" in t or "MiniMed" in t:
            fams.add("Medtronic")
        elif "OmniPod" in t:
            fams.add("OmniPod")
        elif "Animas" in t or "Ping" in t:
            fams.add("Animas")
        elif "Tandem" in t:
            fams.add("Tandem")
        else:
            fams.add("Unknown code")
    if "multiple" in fams or len(fams) > 1:
        return "Multiple pumps"
    return fams.pop()


def device_family(model, source):
    """Which device recorded the fingerstick: Contour Next meter, Precision Xtra meter, OmniPod, Medtronic pump, other pump."""
    m = str(model)
    if source == "meter":
        return "Contour Next" if "Contour" in m else "Precision Xtra"
    if "OmniPod" in m:
        return "OmniPod (built-in FreeStyle strips)"
    if "Paradigm" in m or "MiniMed" in m:
        return "Medtronic pump entry"
    return "Other pump entry"


def pump_entry_check(pairs, ppl):
    """Are pump-entered BG values real fingersticks? By arm and entry type: pairs, people, pooled MARD,
    and the share of pairs whose error is exactly 0 or within 1 mg/dL (a typed-in CGM value gives 0)."""
    im = pairs["independent_meter"]
    im = im[im.in_study_window].merge(ppl[["PtID", "arm"]], on="PtID")
    src = im.source.astype(str)
    sub = im.subtype.astype(str)
    im["entry"] = np.where(src == "meter", "meter upload (Contour Next / Precision Xtra)", "pump entry, subtype " + sub)
    rows = []
    for (arm, entry), g in im.groupby(["arm", "entry"], observed=True):
        rows.append({"arm": str(arm), "entry": entry, "pairs": int(len(g)), "people": int(g.PtID.nunique()),
                     "mard_pooled": float(g.abs_rel_err_pct.mean()), "median_abs_err_mgdl": float(g.abs_err.median()),
                     "pct_err_exactly_zero": float((g.err == 0).mean() * 100),
                     "pct_within_1_mgdl": float((g.abs_err <= 1).mean() * 100),
                     "pct_flagged_pump_copy_of_meter": float(g.pump_copy_of_meter.mean() * 100)})
    return rows


def participant_metrics(ppl, pairs, cgm):
    """One row per participant.

    Primary accuracy = verified fingerstick pairs: independent meter pairs (not used for
    calibration) in the study window whose reference came from a glucose-meter upload
    (source == 'meter': Contour Next or Precision Xtra). Pump-entered BG values are NOT
    used, because many of them are CGM values typed into the pump (see pump_entry_check).
    Also: low-, mid- and high-range accuracy; the mix of each person's pairs (share low,
    share fast-changing, share at night); the old all-independent-pairs MARD; the pump-entry
    MARD; calibration-pair MARD; first / second half MARD; and the CGM glucose summary
    (time low / high, mean, SD, CV, readings per day)."""
    im_all = pairs["independent_meter"]
    im_all = im_all[im_all.in_study_window].copy()
    im = im_all[im_all.is_verified_fingerstick].copy()       # the headline rule built into preprocess.py (meter log, not a calibration)
    log(f"independent in-window pairs: {len(im_all):,}; verified fingerstick (meter-upload) pairs: {len(im):,} from {im.PtID.nunique()} people")
    acc = im.groupby("PtID").apply(accuracy_block)
    low = im[im.avg < 70].groupby("PtID").apply(lambda d: accuracy_block(d, "low_"))
    low = low.reindex(acc.index)
    low["low_n_pairs"] = low["low_n_pairs"].fillna(0).astype(int)
    for c in ["low_mard", "low_median_ard", "low_bias_pct", "low_pct_within_20_20"]:
        low.loc[low.low_n_pairs < MIN_LOW_PAIRS, c] = np.nan
    # Mid (70-180) and high (>180) range accuracy, same minimum-pairs rule.
    mid = im[(im.avg >= 70) & (im.avg <= 180)].groupby("PtID").apply(lambda d: accuracy_block(d, "mid_"))[["mid_n_pairs", "mid_mard"]].reindex(acc.index)
    mid.loc[mid.mid_n_pairs.fillna(0) < MIN_BLOCK_PAIRS, "mid_mard"] = np.nan
    high = im[im.avg > 180].groupby("PtID").apply(lambda d: accuracy_block(d, "high_"))[["high_n_pairs", "high_mard"]].reindex(acc.index)
    high.loc[high.high_n_pairs.fillna(0) < MIN_BLOCK_PAIRS, "high_mard"] = np.nan
    # Mix of each person's pairs: share low, share high, share fast-changing (|rate| > 1 mg/dL/min), share at night.
    roc = im.rate_of_change.abs()
    mix = pd.DataFrame({"PtID": im.PtID.values, "low": (im.avg < 70).values, "high": (im.avg > 180).values,
                        "fast": (roc > 1).values, "roc_known": roc.notna().values, "night": im.is_night.values,
                        "abs_roc": roc.values})
    mixg = mix.groupby("PtID").agg(pct_pairs_low=("low", "mean"), pct_pairs_high=("high", "mean"), n_fast=("fast", "sum"),
                                   n_roc=("roc_known", "sum"), pct_pairs_night=("night", "mean"), mean_abs_roc=("abs_roc", "mean"))
    mixg["pct_pairs_fast"] = mixg.n_fast / mixg.n_roc * 100
    mixg = mixg.drop(columns=["n_fast", "n_roc"])
    for c in ["pct_pairs_low", "pct_pairs_high", "pct_pairs_night"]:
        mixg[c] *= 100
    # The old definition (all independent pairs, pump entries included) and the pump entries alone.
    allp = im_all.groupby("PtID").agg(allpairs_n_pairs=("abs_rel_err_pct", "size"), allpairs_mard=("abs_rel_err_pct", "mean"))
    pm = im_all[(im_all.source == "pump") & ~im_all.pump_copy_of_meter]
    pump = pm.groupby("PtID").agg(pump_n_pairs=("abs_rel_err_pct", "size"), pump_mard=("abs_rel_err_pct", "mean"),
                                  pump_pct_err_zero=("err", lambda e: float((e == 0).mean() * 100)))
    pump.loc[pump.pump_n_pairs < MIN_BLOCK_PAIRS, ["pump_mard", "pump_pct_err_zero"]] = np.nan
    # Calibration pairs (the other pair type), in window.
    cal = pairs["calibration"]
    cal = cal[cal.in_study_window]
    calm = cal.groupby("PtID").agg(cal_n_pairs=("abs_rel_err_pct", "size"), cal_mard=("abs_rel_err_pct", "mean"))
    # First vs second half of each person's pair days.
    midday = im.groupby("PtID").day.agg(lambda s: (s.min() + s.max()) / 2)
    im["half"] = np.where(im.day.values <= midday.reindex(im.PtID).values, "first", "second")
    halves = im.groupby(["PtID", "half"]).agg(n=("abs_rel_err_pct", "size"), mard=("abs_rel_err_pct", "mean")).unstack()
    halves.columns = [f"{b}_half_{a}" for a, b in halves.columns]
    for h in ["first", "second"]:
        halves.loc[halves[f"{h}_half_n"].fillna(0) < MIN_BLOCK_PAIRS, f"{h}_half_mard"] = np.nan
    # Per-device-family MARD (descriptive), kept outside the main table.
    im_all["device_family"] = [device_family(m, s) for m, s in zip(im_all.device_model.astype(str), im_all.source.astype(str))]
    fam = im_all[~im_all.pump_copy_of_meter].groupby(["PtID", "device_family"]).agg(
        n=("abs_rel_err_pct", "size"), mard=("abs_rel_err_pct", "mean")).reset_index()
    fam = fam[fam.n >= MIN_BLOCK_PAIRS]
    STATS["device_family"] = {"note": f"per-participant MARD on each device's pairs (at least {MIN_BLOCK_PAIRS} pairs); pump copies of meter readings dropped",
                              "pairs_by_family": im_all.device_family.value_counts().to_dict(),
                              "per_participant": {f: describe(g.mard) for f, g in fam.groupby("device_family")}}
    # CGM glucose summary in the window.
    c = cgm[cgm.in_study_window & ~cgm.glucose_missing]
    gl = pd.DataFrame({"PtID": c.PtID.values, "g": c.glucose.values, "day": c.day.values})
    gl["low"] = gl.g < 70
    gl["high"] = gl.g > 180
    gs = gl.groupby("PtID").agg(cgm_n=("g", "size"), pct_below_70=("low", "mean"), pct_above_180=("high", "mean"),
                                mean_glucose=("g", "mean"), sd_glucose=("g", "std"))
    gs["pct_below_70"] *= 100
    gs["pct_above_180"] *= 100
    gs["cv_pct"] = gs.sd_glucose / gs.mean_glucose * 100
    gs["median_readings_per_day"] = gl.groupby(["PtID", "day"]).size().groupby("PtID").median()
    out = pd.concat([acc, low, mid, high, mixg, allp, pump, calm, halves, gs], axis=1).reset_index()
    out = ppl[["PtID"]].merge(out, on="PtID", how="left")
    out["n_pairs"] = out.n_pairs.fillna(0).astype(int)
    out["pairs_per_day"] = out.n_pairs / out.PtID.map(ppl.set_index("PtID").cgm_days_in_window)
    return out


def add_covariates(ppl):
    """Add the grouped versions of the covariates used in the tests."""
    d = ppl.copy()
    d["sex"] = pd.Categorical(d.sex.astype(str), ["F", "M"])
    d["arm"] = pd.Categorical(d.arm.astype(str), ["CGM Only", "CGM+BGM"])
    d["male"] = (d.sex == "M").astype(int)
    d["arm_cgm_bgm"] = (d.arm == "CGM+BGM").astype(int)
    d["age_group"] = pd.cut(d.age, [0, 34, 50, 200], labels=["<35", "35-50", ">50"])
    d["bmi_group"] = pd.cut(d.bmi, [0, 25, 30, 100], right=False, labels=["<25", "25-30", "30+"])
    h = d.hba1c_screening
    d["hba1c_group"] = pd.Categorical(np.select([h < 7, h <= 8, h > 8], ["<7", "7-8", ">8"], default=""), ["<7", "7-8", ">8"])
    ranks = d.diabetes_duration_yrs.rank(method="first")
    d["duration_group"] = pd.qcut(ranks, 3, labels=["shortest third", "middle third", "longest third"])
    STATS["definitions"]["duration_tertile_years"] = [
        {"group": str(g), "min": int(v.min()), "max": int(v.max())}
        for g, v in d.groupby("duration_group", observed=True).diabetes_duration_yrs]
    edu = d.education.astype(str)
    d["education_group"] = pd.Categorical(np.select(
        [edu.isin(["High school graduate/diploma/GED", "Some college but no degree", "Associate Degree"]),
         edu == "Bachelor's Degree",
         edu.isin(["Master's Degree", "Professional Degree", "Doctorate Degree"])],
        ["No bachelor's", "Bachelor's", "Graduate degree"], default=""),
        ["No bachelor's", "Bachelor's", "Graduate degree"])
    inc = d.income.astype(str)
    d["income_group"] = pd.Categorical(np.select(
        [inc.isin(["Less than $25,000", "$25,000 - $35,000", "$35,000 - less than $50,000"]),
         inc.isin(["$50,000 - less than $75,000", "$75,000 - less than $100,000"]),
         inc == "$100,000 - less than $200,000", inc == "$200,000 or more"],
        ["<$50k", "$50k-<$100k", "$100k-<$200k", "$200k+"], default=""),
        ["<$50k", "$50k-<$100k", "$100k-<$200k", "$200k+"])
    for c in ["insurance_private", "insurance_medicare", "insurance_medicaid", "insurance_other", "insurance_none",
              "comorb_hyperlipidemia", "comorb_hypertension", "comorb_hypothyroidism", "comorb_depression",
              "comorb_retinopathy", "comorb_obesity"]:
        d[c + "_yn"] = pd.Categorical(np.where(d[c], "yes", "no"), ["no", "yes"])
    d["site_str"] = pd.Categorical(d.site.astype(str), [str(s) for s in sorted(d.site.unique())])
    d["cgm_use_status"] = pd.Categorical(d.cgm_use_status.astype(str), ["Never", "In past, but not current", "Current"])
    dev = d.cgm_use_device.astype(str).where(d.cgm_use_device.notna(), None)
    d["cgm_use_device"] = pd.Categorical(dev, ["Dexcom", "Medtronic"])
    d["pump_family"] = pd.Categorical(d.pump_models.map(pump_family),
                                      ["Medtronic", "OmniPod", "Animas", "Tandem", "Unknown code", "Multiple pumps"])
    d["status"] = pd.Categorical(d.status.astype(str), ["Completed", "Dropped"])
    d["severe_hypo_history"] = pd.Categorical(np.where(d.severe_hypo_most_recent.astype(str) == "Never", "never", "yes"),
                                              ["never", "yes"])
    d["dka_history"] = pd.Categorical(np.where(d.dka_most_recent.astype(str) == "Never", "never", "yes (ever)"), ["never", "yes (ever)"])
    d["race"] = d.race.astype(str)
    d["ethnicity"] = d.ethnicity.astype(str)
    return d


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def fig21(m):
    """Strip plot of per-participant MARD (all pairs) and low-range MARD, median and IQR marked."""
    fig, ax = plt.subplots(figsize=(6, 2.9))
    rows = [("All pairs", m.mard.dropna(), C_BLUE), (f"Pairs below 70 mg/dL\n(people with {MIN_LOW_PAIRS}+ low pairs)", m.low_mard.dropna(), C_ORANGE)]
    for i, (lab, v, col) in enumerate(rows):
        jit = RNG.uniform(-0.22, 0.22, len(v))
        ax.scatter(v, i + jit, s=12, color=col, alpha=0.5, edgecolor=SURFACE, linewidth=0.4)
        q1, med, q3 = q(v, 25), float(np.median(v)), q(v, 75)
        ax.add_patch(plt.Rectangle((q1, i - 0.3), q3 - q1, 0.6, fill=False, edgecolor=INK, linewidth=1.2))
        ax.plot([med, med], [i - 0.3, i + 0.3], color=INK, lw=2)
        ax.text(q3 + 0.8, i + 0.33, f"n = {len(v)}: median {med:.1f} %, IQR {q1:.1f}-{q3:.1f} %", fontsize=8.5, color=INK2, va="bottom")
    ax.set_yticks([0, 1])
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("Per-participant MARD (%), verified fingerstick pairs")
    ax.set_ylim(-0.6, 1.8)
    ax.grid(axis="x")
    ax.grid(False, axis="y")
    ax.set_title("Sensor error per person: box = IQR (middle half), line = median")
    save(fig, "21_participant_mard_distribution.png")


def forest(ax, rows, star_key="sig", xlabel=""):
    """Draw a forest plot. rows: list of dicts with label, est, lo, hi, and optional extra series."""
    n = len(rows)
    ys = np.arange(n)[::-1]
    for y, r in zip(ys, rows):
        series = r["series"] if "series" in r else [(r["est"], r["lo"], r["hi"], C_BLUE, "o", 1.0, None)]
        k = len(series)
        for j, (est, lo, hi, col, mk, alpha, lab) in enumerate(series):
            off = (j - (k - 1) / 2) * 0.22
            ax.plot([lo, hi], [y + off, y + off], color=col, lw=1.4, alpha=alpha, solid_capstyle="butt")
            ax.plot(est, y + off, marker=mk, color=col, ms=5.5, alpha=alpha, markeredgecolor=SURFACE, markeredgewidth=0.5)
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([(("* " if r.get(star_key) else "") + r["label"]).replace("$", r"\$") for r in rows])
    ax.set_ylim(-0.7, n - 0.3)
    ax.grid(False, axis="y")
    ax.grid(True, axis="x")
    ax.set_xlabel(xlabel)


def fig22(models, uni):
    """Forest plot of the pre-specified covariates: unadjusted, adjusted (6 terms), adjusted + glycaemia."""
    labels = {"age": ("Age", "years"), "male": ("Male vs female", None), "bmi": ("BMI", "kg/m2"),
              "hba1c_screening": ("HbA1c", "%"), "diabetes_duration_yrs": ("Diabetes duration", "years"),
              "arm_cgm_bgm": ("CGM+BGM arm vs CGM-only", None)}
    m1 = {t["term"]: t for t in models["mard_step1"]["terms"]}
    m2 = {t["term"]: t for t in models["mard_step2"]["terms"]}
    rows = []
    for term in ["age", "male", "bmi", "hba1c_screening", "diabetes_duration_yrs", "arm_cgm_bgm"]:
        u = uni[term]
        a1, a2 = m1[term], m2[term]
        name, unit = labels[term]
        lab = name if a1["sd"] is None else f"{name} (per 1 SD = {a1['sd']:.1f} {unit})"
        rows.append({"label": lab, "sig": a1["p_bh"] is not None and a1["p_bh"] < ALPHA, "series": [
            (u["coef_per_sd"], u["ci_low_per_sd"], u["ci_high_per_sd"], MUTED, "o", 0.9, "Unadjusted"),
            (a1["coef_per_sd"], a1["ci_low_per_sd"], a1["ci_high_per_sd"], C_BLUE, "s", 1.0, "Adjusted for the other 5 terms"),
            (a2["coef_per_sd"], a2["ci_low_per_sd"], a2["ci_high_per_sd"], C_ORANGE, "D", 1.0, "Adjusted + glucose CV + % time below 70")]})
    fig, ax = plt.subplots(figsize=(6, 3.6))
    forest(ax, rows, xlabel="Change in per-participant MARD (percentage points) with 95 % CI")
    for col, mk, lab in [(MUTED, "o", "Unadjusted"), (C_BLUE, "s", "Adjusted (6 pre-specified terms)"), (C_ORANGE, "D", "Adjusted + glucose CV + % time below 70")]:
        ax.plot([], [], marker=mk, color=col, ls="-", label=lab)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, fontsize=8.5)
    ax.set_title(f"Pre-specified covariates (n = {models['mard_step1']['n']}); * = BH-adjusted p < 0.05 in the adjusted model", pad=30)
    # Subtitle: say why no label carries a star (BH = Benjamini-Hochberg multiple-testing correction).
    n_starred = sum(bool(r["sig"]) for r in rows)
    sub = ("No star is shown because no difference passed the multiple-testing correction\n"
           "(the correction guards against chance finds when many tests are run)." if n_starred == 0
           else f"{n_starred} of {len(rows)} terms passed the multiple-testing correction (starred).")
    ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=8.5, color=INK2, va="bottom", ha="left", linespacing=1.3)
    save(fig, "22_prespecified_forest.png")


def fig23(m, choice):
    """Scatter of per-participant MARD against the strongest continuous correlate, with a fitted line and bootstrap band."""
    x = m[choice["column"]].values.astype(float)
    y = m.mard.values.astype(float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    fig, ax = plt.subplots(figsize=(6, 3.8))
    ax.scatter(x, y, s=16, color=C_BLUE, alpha=0.55, edgecolor=SURFACE, linewidth=0.4)
    xs = np.linspace(x.min(), x.max(), 100)
    idx = RNG.integers(0, len(x), (N_BOOT, len(x)))
    preds = np.empty((N_BOOT, len(xs)))
    for i in range(N_BOOT):
        b = np.polyfit(x[idx[i]], y[idx[i]], 1)
        preds[i] = np.polyval(b, xs)
    b0 = np.polyfit(x, y, 1)
    ax.fill_between(xs, np.percentile(preds, 2.5, axis=0), np.percentile(preds, 97.5, axis=0), color=C_ORANGE, alpha=0.2, linewidth=0)
    ax.plot(xs, np.polyval(b0, xs), color=C_ORANGE, lw=2)
    ax.set_xlabel(choice["xlabel"])
    ax.set_ylabel("Per-participant MARD (%)")
    r = choice["spearman"]
    ax.text(0.98, 0.03, f"Spearman rho = {r['rho']:.2f} (95 % CI {r['ci_low']:.2f} to {r['ci_high']:.2f}), n = {r['n']}\nline = least-squares fit, band = bootstrap 95 % CI",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=8.5, color=INK2)
    ax.set_title(choice["title"])
    save(fig, "23_strongest_association.png")


def fig24(rows, not_testable):
    """Forest plot of every exploratory contrast (difference in median MARD vs reference), untestable items listed below."""
    fig, ax = plt.subplots(figsize=(6, 0.26 * len(rows) + 1.6))
    for r in rows:
        r["series"] = [(r["est"], r["lo"], r["hi"], C_ORANGE if r["sig"] else C_BLUE, "o", 1.0, None)]
    forest(ax, rows, xlabel="Difference in per-participant median MARD (percentage points) with bootstrap 95 % CI")
    ax.set_title("Exploratory list; * = BH-adjusted p < 0.05 within this list")
    txt = "Not testable (fewer than 10 people in a group): " + "; ".join(not_testable) if not_testable else "All exploratory items were testable."
    ax.text(0.0, -0.045, "\n".join(textwrap.wrap(txt, 100)), transform=ax.transAxes, fontsize=8, color=INK2, va="top", ha="left")
    save(fig, "24_exploratory_forest.png")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    pp.check_raw_data(ROOT)
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    STATS["run"] = {"seed": SEED, "n_boot": N_BOOT, "min_group": MIN_GROUP, "min_low_pairs": MIN_LOW_PAIRS,
                    "min_block_pairs": MIN_BLOCK_PAIRS, "cache_version": pp.CACHE_VERSION}
    STATS["definitions"] = {
        "unit": "participant",
        "pairs": "verified fingerstick pairs: independent meter pairs (not used for calibration) in the study window (day 0-329) whose reference came from a glucose-meter upload (source == meter). Pump-entered BG values are excluded because many are CGM values typed into the pump (see data_quality)",
        "allpairs_mard": "the same but on ALL independent pairs including pump-entered BG values (the older definition; shown as a sensitivity check)",
        "pump_mard": "MARD on pump-entered BG pairs only (pump copies of meter readings dropped; at least 20 pairs)",
        "pct_pairs_low / fast / night": "share of the person's verified pairs with average < 70 mg/dL / |rate of change| > 1 mg/dL per min / between 00:00 and 06:00",
        "mid_mard": "MARD on pairs with average 70-180 mg/dL (at least 20 pairs)",
        "mard": "mean of |CGM - reference| / reference x 100 over the person's pairs",
        "bias_pct": "mean of (CGM - reference) / reference x 100; negative = sensor reads low",
        "pct_within_20_20": "percent of pairs within 20 mg/dL when reference < 100 mg/dL, else within 20 %",
        "low_mard": f"MARD on pairs whose average of CGM and reference is below 70 mg/dL; NaN when fewer than {MIN_LOW_PAIRS} such pairs",
        "cgm_metrics": "CGM readings in the window, duplicates dropped: % time < 70, % time > 180, mean, SD, CV = SD / mean x 100, median readings per day",
    }
    ppl = pp.load_participants(ROOT, CACHE)
    pairs = pp.build_pairs(ROOT, CACHE)
    cgm = pp.load_cgm(ROOT, CACHE)
    log("loaded cache")

    m = participant_metrics(ppl, pairs, cgm)
    del cgm
    m.to_parquet(os.path.join(CACHE, "participant_metrics.parquet"), index=False)
    m.round(4).to_csv(os.path.join(OUT, "participant_metrics.csv"), index=False)
    log(f"participant metrics: {len(m)} rows, {m.mard.notna().sum()} with MARD, {m.low_mard.notna().sum()} with low-range MARD")

    d = add_covariates(ppl).merge(m, on="PtID")
    STATS["participant_summary"] = {k: describe(d[k]) for k in
                                    ["n_pairs", "pairs_per_day", "mard", "median_ard", "bias_pct", "pct_within_20_20",
                                     "low_n_pairs", "low_mard", "low_bias_pct", "mid_mard", "high_mard", "cal_mard",
                                     "allpairs_n_pairs", "allpairs_mard", "pump_n_pairs", "pump_mard", "pump_pct_err_zero",
                                     "pct_pairs_low", "pct_pairs_high", "pct_pairs_fast", "pct_pairs_night", "mean_abs_roc",
                                     "pct_below_70", "pct_above_180", "mean_glucose", "sd_glucose", "cv_pct", "median_readings_per_day"]}
    STATS["participant_summary"]["n_with_low_mard"] = int(d.low_mard.notna().sum())
    STATS["participant_summary"]["n_low_pairs_below_min"] = int((d.low_n_pairs < MIN_LOW_PAIRS).sum())
    STATS["participant_summary"]["spearman_mard_vs_low_mard"] = spearman_ci(d.mard, d.low_mard)
    STATS["participant_summary"]["spearman_mard_vs_cal_mard"] = spearman_ci(d.mard, d.cal_mard)
    STATS["participant_summary"]["spearman_mard_vs_allpairs_mard"] = spearman_ci(d.mard, d.allpairs_mard)
    # Data quality: pump-entered BG values versus real meter uploads, and what it does to the arm comparison.
    STATS["data_quality"] = {
        "pump_entries_by_arm": pump_entry_check(pairs, ppl),
        "pump_vs_meter_within_person": paired_test(d.mard, d.pump_mard, "Pump-entered BG pairs vs meter-upload pairs (same person)"),
        "arm_on_verified_pairs": group_test(d, "arm", "mard", "Study arm"),
        "arm_on_all_independent_pairs": group_test(d, "arm", "allpairs_mard", "Study arm"),
        "arm_on_pump_entries": group_test(d, "arm", "pump_mard", "Study arm"),
        "arm_on_calibration_pairs": group_test(d, "arm", "cal_mard", "Study arm"),
        "note": "In the CGM-only arm people dosed from the CGM and typed its value into the pump bolus calculator. "
                "Those entries are not fingersticks. They make the old all-pairs MARD too low and create a false arm difference."}

    # ---------------- pre-specified ----------------
    pre_cont = [("age", "Age (years)"), ("bmi", "BMI (kg/m2)"), ("hba1c_screening", "HbA1c at screening (%)"),
                ("diabetes_duration_yrs", "Diabetes duration (years)")]
    pre_grp = [("age_group", "Age group"), ("sex", "Sex"), ("bmi_group", "BMI group"), ("hba1c_group", "HbA1c group"),
               ("duration_group", "Diabetes duration tertile"), ("arm", "Study arm")]
    pre = {"continuous": [], "groups": [], "continuous_low": [], "groups_low": [], "groups_cal": []}
    for c, lab in pre_cont:
        pre["continuous"].append({"variable": c, "label": lab, "outcome": "mard", **spearman_ci(d[c], d.mard)})
        pre["continuous_low"].append({"variable": c, "label": lab, "outcome": "low_mard", **spearman_ci(d[c], d.low_mard)})
    for v, lab in pre_grp:
        pre["groups"].append(group_test(d, v, "mard", lab))
        pre["groups_low"].append(group_test(d, v, "low_mard", lab))
        pre["groups_cal"].append(group_test(d, v, "cal_mard", lab))
    for key in ["continuous", "groups"]:
        pass
    allp = [t["p"] for t in pre["continuous"]] + [t["p"] for t in pre["groups"]]
    adj = bh(allp)
    for t, p in zip(pre["continuous"] + pre["groups"], adj):
        t["p_bh_within_prespecified"] = float(p) if not np.isnan(p) else None
    STATS["prespecified"] = pre

    # Models.
    terms6 = [("age", "Age (per year)"), ("male", "Male vs female"), ("bmi", "BMI (per kg/m2)"),
              ("hba1c_screening", "HbA1c (per 1 %)"), ("diabetes_duration_yrs", "Diabetes duration (per year)"),
              ("arm_cgm_bgm", "CGM+BGM arm vs CGM-only")]
    gly = [("cv_pct", "Glucose CV (per 1 %)"), ("pct_below_70", "% time below 70 (per 1 %)")]
    mixt = [("pct_pairs_low", "% of own pairs below 70 (per 1 %)"), ("pct_pairs_fast", "% of own pairs fast-changing (per 1 %)")]
    six = [c for c, _ in terms6]
    models = {
        "mard_step1": fit_ols(d, "mard", terms6),
        "log_mard_step1": fit_ols(d, "mard", terms6, log_outcome=True),
        "mard_step2": fit_ols(d, "mard", terms6 + gly, bh_terms=six),
        "log_mard_step2": fit_ols(d, "mard", terms6 + gly, log_outcome=True, bh_terms=six),
        "mard_step3_pair_mix": fit_ols(d, "mard", terms6 + gly + mixt, bh_terms=six),
        "low_mard_step1": fit_ols(d, "low_mard", terms6),
        "log_low_mard_step1": fit_ols(d, "low_mard", terms6, log_outcome=True),
        "low_mard_step2": fit_ols(d, "low_mard", terms6 + gly, bh_terms=six),
        "allpairs_mard_step1_old_definition": fit_ols(d, "allpairs_mard", terms6),
        "mid_mard_step1": fit_ols(d, "mid_mard", terms6),
    }
    uni = {c: fit_ols(d, "mard", [(c, lab)])["terms"][0] for c, lab in terms6}
    models["univariable"] = uni
    STATS["models"] = models

    # Confound checks: glycaemia and data volume vs MARD.
    conf = [("cv_pct", "Glucose CV (%)"), ("pct_below_70", "% time below 70 mg/dL"), ("pct_above_180", "% time above 180 mg/dL"),
            ("mean_glucose", "Mean CGM glucose (mg/dL)"), ("sd_glucose", "Glucose SD (mg/dL)"),
            ("pct_pairs_low", "% of own pairs below 70 mg/dL"), ("pct_pairs_fast", "% of own pairs fast-changing"),
            ("pct_pairs_night", "% of own pairs at night"), ("mean_abs_roc", "Mean |rate of change| at pairs (mg/dL/min)"),
            ("median_readings_per_day", "CGM readings per day"), ("pairs_per_day", "Meter pairs per day"),
            ("n_pairs", "Number of meter pairs"), ("fingersticks_per_day", "Fingersticks per day at screening")]
    STATS["confounders"] = {"mard": [{"variable": c, "label": lab, **spearman_ci(d[c], d.mard)} for c, lab in conf],
                            "low_mard": [{"variable": c, "label": lab, **spearman_ci(d[c], d.low_mard)} for c, lab in conf],
                            "covariates_vs_cv": [{"variable": c, "label": lab, **spearman_ci(d[c], d.cv_pct)} for c, lab in pre_cont],
                            "covariates_vs_pct_below_70": [{"variable": c, "label": lab, **spearman_ci(d[c], d.pct_below_70)} for c, lab in pre_cont]}
    STATS["confounders"]["cv_by_arm"] = group_test(d, "arm", "cv_pct", "Study arm")
    STATS["confounders"]["pct_below_70_by_arm"] = group_test(d, "arm", "pct_below_70", "Study arm")
    STATS["confounders"]["pct_below_70_by_hba1c"] = group_test(d, "hba1c_group", "pct_below_70", "HbA1c group")
    STATS["confounders"]["cv_by_hba1c"] = group_test(d, "hba1c_group", "cv_pct", "HbA1c group")

    # ---------------- exploratory ----------------
    exp_grp = [("education_group", "Education"), ("income_group", "Income (answered only)"),
               ("insurance_private_yn", "Private insurance"), ("insurance_medicare_yn", "Medicare"),
               ("insurance_medicaid_yn", "Medicaid"), ("insurance_other_yn", "Other insurance"), ("insurance_none_yn", "No insurance"),
               ("site_str", "Clinic site"), ("cgm_use_status", "Prior CGM use"), ("cgm_use_device", "Prior CGM brand"),
               ("pump_family", "Pump family"), ("comorb_hyperlipidemia_yn", "Hyperlipidaemia"), ("comorb_hypertension_yn", "Hypertension"),
               ("comorb_hypothyroidism_yn", "Hypothyroidism"), ("comorb_depression_yn", "Depression"),
               ("comorb_retinopathy_yn", "Retinopathy"), ("comorb_obesity_yn", "Obesity listed as a condition"),
               ("status", "Completion status"), ("severe_hypo_history", "Severe hypo history (>12 months ago)"),
               ("dka_history", "DKA history")]
    exp_cont = [("diagnosis_age", "Age at diagnosis (years)"), ("fingersticks_per_day", "Fingersticks per day at screening"),
                ("n_comorbidities", "Number of listed conditions")]
    tests = []
    for v, lab in exp_grp:
        tests.append({"kind": "group", **group_test(d, v, "mard", lab)})
    for c, lab in exp_cont:
        r = spearman_ci(d[c], d.mard)
        # Top vs bottom tertile for the forest plot (same axis as the group contrasts).
        tert = pd.qcut(d[c].rank(method="first"), 3, labels=["low", "mid", "high"])
        est, lo, hi = boot_diff(d.loc[tert == "low", "mard"], d.loc[tert == "high", "mard"])
        tests.append({"kind": "continuous", "variable": c, "label": lab, "outcome": "mard", "testable": True,
                      "test": "Spearman", **r, "top_vs_bottom_tertile": {"diff_median": est, "ci_low": lo, "ci_high": hi,
                      "cut_points": [float(d[c].quantile(1 / 3)), float(d[c].quantile(2 / 3))]}})
    tests.append({"kind": "paired", "variable": "half", **paired_test(d.first_half_mard, d.second_half_mard,
                 "Second vs first half of each person's study days")})
    tests.append({"kind": "group", **group_test(d, "initial_study_cgm", "mard", "Run-in CGM type",
                                                order=["Blinded", "Standard"])})
    pv = [t["p"] if t.get("testable") else np.nan for t in tests]
    adj = bh(pv)
    for t, p in zip(tests, adj):
        t["p_bh"] = float(p) if not np.isnan(p) else None
        t["bh_significant"] = bool(t["p_bh"] is not None and t["p_bh"] < ALPHA)
    STATS["exploratory"] = {"n_tests_in_bh_family": int(np.sum(~np.isnan(np.asarray(pv, float)))), "tests": tests}
    # Also run the exploratory group tests on calibration pairs and low range (robustness; no BH, reported next to the main test).
    STATS["exploratory"]["robustness"] = {
        "cal_mard": [group_test(d, v, "cal_mard", lab) for v, lab in exp_grp],
        "low_mard": [group_test(d, v, "low_mard", lab) for v, lab in exp_grp]}
    # Meter model: Contour Next vs Precision Xtra pairs.
    im_all = pairs["independent_meter"]
    im_all = im_all[im_all.in_study_window]
    px = im_all[im_all.device_model.astype(str).str.contains("Precision")]
    STATS["exploratory"]["meter_model"] = {
        "contour_next_pairs": int((im_all.device_model.astype(str) == "Contour Next").sum()),
        "precision_xtra_pairs": int(len(px)), "precision_xtra_people_with_20_pairs": int((px.groupby("PtID").size() >= MIN_BLOCK_PAIRS).sum()),
        "note": "Precision Xtra is mostly a ketone meter here; ketone rows are excluded, so very few glucose pairs remain. Not testable. "
                "Pump-entered BG values are not a meter and are compared in data_quality instead."}
    # Race and ethnicity: describe only.
    STATS["exploratory"]["race_ethnicity"] = {
        "race": [{"group": g, **describe(v)} for g, v in d.groupby("race").mard],
        "ethnicity": [{"group": g, **describe(v)} for g, v in d.groupby("ethnicity").mard],
        "non_white_n": int((d.race != "White").sum()),
        "note": "described, not tested: only 14 non-White participants"}
    STATS["exploratory"]["income_not_answered"] = {**describe(d.loc[d.income_group.isna(), "mard"]), "note": "people who did not answer the income question"}
    STATS["exploratory"]["dropped"] = {**describe(d.loc[d.status == "Dropped", "mard"]), "note": "not testable (9 people)"}

    # ---------------- Shanghai ----------------
    sh = pp.load_shanghai(ROOT, CACHE)
    sp = pairs["shanghai"].copy()
    sp["group"] = sp.group.astype(str)
    sp["pid"] = sp.pid.astype(str)
    per = sp.groupby(["group", "pid"]).agg(n_pairs=("abs_rel_err_pct", "size"), mard=("abs_rel_err_pct", "mean"),
                                           bias_pct=("rel_err_pct", "mean")).reset_index()
    pt = sh["patients"].copy()
    pt["group"] = pt.group.astype(str)
    pt["pid"] = pt.pid.astype(str)
    pt = pt.sort_values(["group", "pid", "visit"]).drop_duplicates(["group", "pid"])
    s = per.merge(pt[["group", "pid", "sex", "Age (years)", "hba1c_pct"]], on=["group", "pid"], how="left")
    s = s[s.n_pairs >= MIN_SHANGHAI_PAIRS].copy()
    s["type"] = pd.Categorical(s.group, ["T1DM", "T2DM"])
    s["sex"] = pd.Categorical(s.sex.astype(str), ["F", "M"])
    a1, a2 = s["Age (years)"].quantile([1 / 3, 2 / 3])
    s["age_group"] = pd.cut(s["Age (years)"], [0, a1, a2, 200], labels=[f"<={a1:.0f}", f"{a1:.0f}-{a2:.0f}", f">{a2:.0f}"])
    h1, h2 = s.hba1c_pct.quantile([1 / 3, 2 / 3])
    s["hba1c_group"] = pd.cut(s.hba1c_pct, [0, h1, h2, 30], labels=[f"<={h1:.1f}", f"{h1:.1f}-{h2:.1f}", f">{h2:.1f}"])
    STATS["shanghai"] = {
        "patients_with_pairs": int(len(per)), "patients_with_min_pairs": int(len(s)), "min_pairs": MIN_SHANGHAI_PAIRS,
        "pairs_used": int(s.n_pairs.sum()), "mard": describe(s.mard), "bias_pct": describe(s.bias_pct),
        "by_type_all_patients": [{"group": g, **describe(v)} for g, v in per.groupby("group").mard],
        "tests": [group_test(s, v, "mard", lab) for v, lab in
                  [("type", "Diabetes type"), ("sex", "Sex"), ("age_group", "Age tertile (years)"), ("hba1c_group", "HbA1c tertile (%)")]],
        "spearman": {"age": spearman_ci(s["Age (years)"], s.mard), "hba1c": spearman_ci(s.hba1c_pct, s.mard),
                     "n_pairs": spearman_ci(s.n_pairs, s.mard)},
        "caveat": "small comparator: 3-14 days per patient, 15-min rows, fingerstick timing slack up to 7.5 min, in-patients"}

    # ---------------- strongest association (figure 23) ----------------
    cands = [(c, lab, "prespecified") for c, lab in pre_cont] + [(c, lab, "confounder") for c, lab in conf[:5]] + \
            [(c, lab, "exploratory") for c, lab in exp_cont]
    best = None
    for c, lab, fam in cands:
        r = spearman_ci(d[c], d.mard)
        if best is None or abs(r["rho"]) > abs(best["spearman"]["rho"]):
            best = {"column": c, "xlabel": lab, "family": fam, "spearman": r}
    best["title"] = f"Strongest correlate of per-participant MARD: {best['xlabel']}"
    STATS["figure_23_choice"] = best

    # ---------------- figures ----------------
    fig21(m)
    fig22(models, uni)
    fig23(d, best)
    rows, not_testable = [], []
    for t in tests:
        if not t.get("testable"):
            small = ", ".join("{} n={}".format(g["group"], g["n"]) for g in t.get("excluded_small_groups", []))
            not_testable.append("{} ({})".format(t["label"], small or "n=" + str(t.get("n", 0))))
            continue
        if t["kind"] == "group":
            for ctr in t["contrasts"]:
                rows.append({"label": f"{t['label']}: {ctr['group']} vs {ctr['vs']} ({ctr['n']} vs {ctr['n_ref']})",
                             "est": ctr["diff_median"], "lo": ctr["ci_low"], "hi": ctr["ci_high"], "sig": t["bh_significant"]})
            for g in t.get("excluded_small_groups", []):
                not_testable.append(f"{t['label']}: {g['group']} (n={g['n']})")
        elif t["kind"] == "continuous":
            tb = t["top_vs_bottom_tertile"]
            rows.append({"label": f"{t['label']}: top vs bottom third (rho {t['rho']:+.2f})", "est": tb["diff_median"],
                         "lo": tb["ci_low"], "hi": tb["ci_high"], "sig": t["bh_significant"]})
        else:
            rows.append({"label": f"{t['label']} (n={t['n']})", "est": t["diff_median"], "lo": t["ci_low"], "hi": t["ci_high"],
                         "sig": t["bh_significant"]})
    fig24(rows, not_testable)

    STATS["run"]["runtime_s"] = round(time.time() - T0, 1)
    with open(os.path.join(OUT, "subgroups_stats.json"), "w", encoding="utf-8") as f:
        json.dump(clean(STATS), f, indent=1)
    log("wrote", os.path.join(OUT, "subgroups_stats.json"))
    print_summary(d)


def print_summary(d):
    """Print the main tables in plain text (used to write SUBGROUPS.md)."""
    ps = STATS["participant_summary"]
    print("\n=== Per-participant summary (median [IQR], n) ===")
    for k in ["n_pairs", "pairs_per_day", "mard", "median_ard", "bias_pct", "pct_within_20_20", "low_n_pairs", "low_mard", "low_bias_pct",
              "mid_mard", "high_mard", "cal_mard", "allpairs_n_pairs", "allpairs_mard", "pump_n_pairs", "pump_mard", "pump_pct_err_zero",
              "pct_pairs_low", "pct_pairs_high", "pct_pairs_fast", "pct_pairs_night", "mean_abs_roc",
              "pct_below_70", "pct_above_180", "mean_glucose", "cv_pct", "median_readings_per_day"]:
        v = ps[k]
        print(f"{k:26s} {v['median']:8.2f} [{v['q1']:.2f}-{v['q3']:.2f}]  mean {v['mean']:.2f}  n={v['n']}")
    print("rho MARD vs low MARD:", ps["spearman_mard_vs_low_mard"], "\nrho MARD vs cal MARD:", ps["spearman_mard_vs_cal_mard"],
          "\nrho MARD vs all-pairs MARD:", ps["spearman_mard_vs_allpairs_mard"])
    print("\n=== Data quality: pump entries ===")
    for r in STATS["data_quality"]["pump_entries_by_arm"]:
        print(f"{r['arm']:9s} {r['entry']:46s} pairs {r['pairs']:7d} people {r['people']:3d} MARD {r['mard_pooled']:5.2f} "
              f"med|err| {r['median_abs_err_mgdl']:4.1f} err=0 {r['pct_err_exactly_zero']:5.1f}% within1 {r['pct_within_1_mgdl']:5.1f}% pumpcopy {r['pct_flagged_pump_copy_of_meter']:5.1f}%")
    t = STATS["data_quality"]["pump_vs_meter_within_person"]
    print(f"pump vs meter within person: n={t['n']} med meter {t['median_x']:.2f} pump {t['median_y']:.2f} diff {t.get('diff_median')} CI [{t.get('ci_low')}, {t.get('ci_high')}] p={t.get('p')}")
    for key in ["arm_on_verified_pairs", "arm_on_all_independent_pairs", "arm_on_pump_entries", "arm_on_calibration_pairs"]:
        t = STATS["data_quality"][key]
        gs = "; ".join(f"{g['group']} n={g['n']} med {g['median']:.2f} [{g['q1']:.2f}-{g['q3']:.2f}]" for g in t["groups"] if g["median"] is not None)
        cs = "; ".join(f"{c['group']}-{c['vs']}: {c['diff_median']:+.2f} [{c['ci_low']:+.2f},{c['ci_high']:+.2f}]" for c in t["contrasts"])
        print(f"{key:30s} p={t['p']:.4f} {gs} | {cs}")
    print("\n=== Pre-specified: continuous (Spearman) ===")
    for key in ["continuous", "continuous_low"]:
        for t in STATS["prespecified"][key]:
            print(f"{t['outcome']:9s} {t['label']:32s} rho {t['rho']:+.3f} [{t['ci_low']:+.3f},{t['ci_high']:+.3f}] p {t['p']:.3f} n {t['n']}"
                  + (f" p_bh {t['p_bh_within_prespecified']:.3f}" if t.get("p_bh_within_prespecified") is not None else ""))
    print("\n=== Pre-specified: groups ===")
    for key in ["groups", "groups_low", "groups_cal"]:
        for t in STATS["prespecified"][key]:
            gs = "; ".join(f"{g['group']} n={g['n']} med {g['median']:.2f} [{g['q1']:.2f}-{g['q3']:.2f}]" for g in t["groups"] if g["median"] is not None)
            cs = "; ".join(f"{c['group']}-{c['vs']}: {c['diff_median']:+.2f} [{c['ci_low']:+.2f},{c['ci_high']:+.2f}] mdd {c['detectable_diff_means']:.2f}" for c in t["contrasts"])
            pb = t.get("p_bh_within_prespecified")
            print(f"{t['outcome']:9s} {t['label']:28s} {t['test']} p={t['p']:.3f}" + (f" p_bh={pb:.3f}" if pb is not None else "") + f"\n    {gs}\n    {cs}")
    print("\n=== Models ===")
    for name, mod in STATS["models"].items():
        if name == "univariable":
            continue
        print(f"-- {name}: n={mod['n']} R2={mod['r2']:.3f}")
        for t in mod["terms"]:
            extra = f" pct/unit {t['pct_change_per_unit']:+.1f}" if "pct_change_per_unit" in t else ""
            print(f"   {t['label']:30s} {t['coef']:+.3f} [{t['ci_low']:+.3f},{t['ci_high']:+.3f}] p {t['p']:.3f}"
                  + (f" p_bh {t['p_bh']:.3f}" if t["p_bh"] is not None else "") + f" perSD {t['coef_per_sd']:+.2f}{extra}")
    print("\n=== Confounders (Spearman with MARD / low MARD) ===")
    for key in ["mard", "low_mard"]:
        for t in STATS["confounders"][key]:
            print(f"{key:9s} {t['label']:34s} rho {t['rho']:+.3f} [{t['ci_low']:+.3f},{t['ci_high']:+.3f}] p {t['p']:.4f} n {t['n']}")
    for key in ["covariates_vs_cv", "covariates_vs_pct_below_70"]:
        for t in STATS["confounders"][key]:
            print(f"{key:26s} {t['label']:28s} rho {t['rho']:+.3f} [{t['ci_low']:+.3f},{t['ci_high']:+.3f}] p {t['p']:.4f}")
    for key in ["cv_by_arm", "pct_below_70_by_arm", "pct_below_70_by_hba1c", "cv_by_hba1c"]:
        t = STATS["confounders"][key]
        print(key, t["test"], f"p={t['p']:.3f}", "; ".join(f"{g['group']} med {g['median']:.2f}" for g in t["groups"]))
    print("\n=== Exploratory (BH family) ===")
    for t in STATS["exploratory"]["tests"]:
        if not t.get("testable"):
            print(f"NOT TESTABLE {t['label']}: {t.get('reason', '')} {t.get('excluded_small_groups', '')}")
            continue
        if t["kind"] == "group":
            gs = "; ".join(f"{g['group']} n={g['n']} med {g['median']:.2f}" for g in t["groups"] if g["median"] is not None)
            cs = "; ".join(f"{c['group']}-{c['vs']}: {c['diff_median']:+.2f} [{c['ci_low']:+.2f},{c['ci_high']:+.2f}]" for c in t["contrasts"])
            print(f"{t['label']:45s} {t['test']} p={t['p']:.3f} p_bh={t['p_bh']:.3f}{' *' if t['bh_significant'] else ''}\n    {gs}\n    {cs}  excluded {t['excluded_small_groups']}")
        elif t["kind"] == "continuous":
            tb = t["top_vs_bottom_tertile"]
            print(f"{t['label']:45s} rho {t['rho']:+.3f} [{t['ci_low']:+.3f},{t['ci_high']:+.3f}] p={t['p']:.3f} p_bh={t['p_bh']:.3f}; top-bottom third {tb['diff_median']:+.2f} [{tb['ci_low']:+.2f},{tb['ci_high']:+.2f}] cuts {tb['cut_points']}")
        else:
            print(f"{t['label']:45s} n={t['n']} med x {t['median_x']:.2f} y {t['median_y']:.2f} diff {t['diff_median']:+.2f} [{t['ci_low']:+.2f},{t['ci_high']:+.2f}] p={t['p']:.4f} p_bh={t['p_bh']:.3f}")
    print("\nrobustness (cal / low) for exploratory groups:")
    for key in ["cal_mard", "low_mard"]:
        for t in STATS["exploratory"]["robustness"][key]:
            if t["testable"]:
                cs = "; ".join(f"{c['group']}-{c['vs']}: {c['diff_median']:+.2f} [{c['ci_low']:+.2f},{c['ci_high']:+.2f}]" for c in t["contrasts"])
                print(f"  {key:9s} {t['label']:40s} p={t['p']:.3f} {cs}")
    print("\ndevice families:", json.dumps(clean(STATS["device_family"]), indent=0))
    print("meter model:", STATS["exploratory"]["meter_model"])
    print("race:", [(r["group"], r["n"], round(r["median"], 2) if r["median"] else None) for r in STATS["exploratory"]["race_ethnicity"]["race"]])
    print("ethnicity:", [(r["group"], r["n"], round(r["median"], 2) if r["median"] else None) for r in STATS["exploratory"]["race_ethnicity"]["ethnicity"]])
    print("income not answered:", STATS["exploratory"]["income_not_answered"], "\ndropped:", STATS["exploratory"]["dropped"])
    print("\n=== Shanghai ===")
    S = STATS["shanghai"]
    print({k: S[k] for k in ["patients_with_pairs", "patients_with_min_pairs", "pairs_used", "mard", "bias_pct", "by_type_all_patients", "spearman"]})
    for t in S["tests"]:
        gs = "; ".join(f"{g['group']} n={g['n']} med {g['median']:.2f} [{g['q1']:.2f}-{g['q3']:.2f}]" for g in t["groups"] if g["median"] is not None)
        cs = "; ".join(f"{c['group']}-{c['vs']}: {c['diff_median']:+.2f} [{c['ci_low']:+.2f},{c['ci_high']:+.2f}]" for c in t["contrasts"])
        print(f"{t['label']:22s} testable={t['testable']} {t['test']} p={t['p']}\n    {gs}\n    {cs} excluded {t['excluded_small_groups']}")
    print("\nfigure 23 choice:", STATS["figure_23_choice"])
    print(f"\nruntime {STATS['run']['runtime_s']} s")


if __name__ == "__main__":
    main()
