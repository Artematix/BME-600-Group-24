"""
accuracy_v2.py - core CGM accuracy analysis, version 2 (BMEN 600 Group 24).

Every number here comes from the cached tables built by analysis/preprocess.py. Raw files are never
re-parsed in this script.

What it does:
  1. Defines the analysis sets A-E (REPLACE-BG) and S (Shanghai); counts pairs and participants in each.
     Sets A-C use only references read from the meter's own log. Pump BG entries are excluded because in the
     CGM-only arm they are mostly CGM values typed into the pump (the script prints the evidence: pump_entry_check).
  2. Overall accuracy per set: bias, MARD, median ARD, 15/15, 20/20, 40/40 agreement, Parkes zones.
     Every number gets a 95 % CI from a bootstrap that resamples PARTICIPANTS (1,000 resamples, fixed seed).
  3. Accuracy by glucose range: binned by the average of CGM and reference (one axis), then by CGM value.
  4. FDA iCGM-style table (21 CFR 862.1355), binned by CGM value, with lower one-sided 95 % bounds.
  5. Misclassification at 70/180 and 70/200 mg/dL; hypoglycaemia detection at 70 and 54 mg/dL.
  6. Bland-Altman limits of agreement for repeated measures per participant (Bland & Altman 2007).
  7. Meter-uncertainty sensitivity: simulated meter error at the ISO 15197 limit and at half of it.
  8. Shanghai comparator (items 2-3, compact).
  9. Figures 13-16.

Run from the repo root (about 1-2 minutes):
    python analysis/accuracy_v2.py "Uncommitted Data/Raw Data Dump" analysis [tables.md]
Outputs: <outdir>/accuracy_v2_stats.json, <outdir>/figures/13_..16_*.png and, if a third argument is
given, a markdown dump of every table (used to draft ACCURACY_V2.md).
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preprocess as pp  # noqa: E402  (shared cache; the only data source of this script)

T0 = time.time()
SEED = 600            # fixed seed: bootstrap weights and simulated meter error are reproducible
N_BOOT = 1000         # bootstrap resamples (participants drawn with replacement)
BIN5 = ["<54", "54-69", "70-180", "181-250", ">250"]
BIN3 = ["<70", "70-180", ">180"]
LOW_N_PAIRS, LOW_N_PART = 50, 10   # a range estimate is flagged "low n" below these counts

# FDA iCGM special controls, 21 CFR 862.1355(b)(6)(i)(A)-(G): bin by the CGM value; each percentage must have a
# lower one-sided 95 % confidence bound above the threshold. https://www.law.cornell.edu/cfr/text/21/862.1355
ICGM_RULES = [  # (CGM bin, criterion, kind, k, threshold %, clause)
    ("<70", "within 15 mg/dL", "abs", 15, 85, "(A)"),
    ("<70", "within 40 mg/dL", "abs", 40, 98, "(G)"),
    ("70-180", "within 15 %", "rel", 15, 70, "(B)"),
    ("70-180", "within 40 %", "rel", 40, 99, "(D)"),
    (">180", "within 15 %", "rel", 15, 80, "(C)"),
    (">180", "within 40 %", "rel", 40, 99, "(E)"),
    ("all", "within 20 %", "rel", 20, 87, "(F)"),
]

# Published MARD values for context. Citations are the ones already used in METHODS_REVIEW.md / the research plan.
PUBLISHED = [
    {"device": "Dexcom G4 Platinum, Software 505", "setting": "adults, clinic sessions, 7 days", "reference": "YSI lab / meter",
     "mard_pct": "9.0 (lab), 11.3 (meter)", "source": "Bailey 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604574"},
    {"device": "Dexcom G4 Platinum, original vs Software 505", "setting": "children 2-17, clinic", "reference": "YSI lab",
     "mard_pct": "17 (original), 10 (505)", "source": "Laffel 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4717517"},
    {"device": "Abbott FreeStyle Navigator II", "setting": "adults, free-living home use, 10,597 pairs", "reference": "built-in meter",
     "mard_pct": "14.2 overall; 30.6 below 70, 13.9 at 70-180, 9.8 above 180", "source": "Thabit 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4649721"},
    {"device": "Abbott FreeStyle Libre (first generation)", "setting": "72 adults, home use 14 days, 13,195 pairs", "reference": "reader meter / YSI",
     "mard_pct": "11.4 (meter), 12 (lab, clinic days); consensus zone A 86.7, A+B 99.7", "source": "Bailey 2015, https://doi.org/10.1089/dia.2014.0378"},
    {"device": "Abbott FreeStyle Libre", "setting": "742 inpatients with type 2 diabetes, 25,579 pairs", "reference": "hospital meter",
     "mard_pct": "14 overall; 24.5 at 3 AM (bias -23); 72 % of pairs read low", "source": "Wen 2022, https://pmc.ncbi.nlm.nih.gov/articles/PMC9639390"},
]

# --------------------------------------------------------------------------
# Chart styling: same palette and rcParams as explore_raw_data.py (dataviz reference palette, light surface)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#86b6ef", "#2a78d6", "#104281"]
C_GOOD, C_CRIT = "#0ca30c", "#d03b3b"                     # status colours; always paired with a text label
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 10.5, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "axes.labelsize": 9.5,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 2, "savefig.dpi": 150, "savefig.bbox": "tight",
})


def log(*a):
    """Print a progress line with elapsed seconds."""
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Metric helpers
# --------------------------------------------------------------------------
def bin5(v):
    """Glucose bins used for every range table: <54, 54-69, 70-180 (inclusive), 181-250 (180 < v <= 250), >250 mg/dL."""
    v = np.asarray(v, float)
    return np.select([v < 54, v < 70, v <= 180, v <= 250], BIN5[:4], default=BIN5[4])


def bin3(v):
    """iCGM bins by CGM value: <70, 70-180 (inclusive), >180 mg/dL."""
    v = np.asarray(v, float)
    return np.select([v < 70, v <= 180], BIN3[:2], default=BIN3[2])


def cat3(v, high):
    """Clinical category: low (<70), in range (70..high inclusive), high (>high)."""
    v = np.asarray(v, float)
    return np.select([v < 70, v <= high], ["low", "in"], default="high")


def within_k(df, k):
    """1.0 if the pair agrees within k mg/dL (reference < 100) or within k % (reference >= 100), else 0.0."""
    ref = df.ref.to_numpy(float)
    return np.where(ref < 100, df.abs_err.to_numpy(float) <= k, df.abs_rel_err_pct.to_numpy(float) <= k).astype(float)


# Parkes (consensus) error grid, type 1 version. Copied unchanged from analysis/explore_raw_data.py (that file is a
# script, not an importable module). Zone polylines from Pfutzner et al. 2013, J Diabetes Sci Technol 7:1275,
# in (reference, CGM) mg/dL; a point on a boundary belongs to the lower-risk zone.
PARKES_T1 = {
    "upper": {"B": ([0, 30, 140, 280, 430], [50, 50, 170, 380, 550]), "C": ([0, 30, 50, 70, 260], [60, 60, 80, 110, 550]),
              "D": ([0, 25, 50, 80, 125], [100, 100, 125, 215, 550]), "E": ([0, 35, 50], [150, 155, 550])},
    "lower": {"B": ([50, 170, 385, 550], [30, 145, 300, 450]), "C": ([120, 260, 550], [30, 130, 250]), "D": ([250, 550], [40, 150])},
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


# --------------------------------------------------------------------------
# Participant bootstrap
# --------------------------------------------------------------------------
class Booter:
    """Bootstrap that resamples participants (clusters) with replacement.

    Every pooled statistic we report is a ratio of two sums over pairs (mean error = sum(err) / n; a percentage =
    sum(indicator) / n; sensitivity = sum(true positives) / sum(positives)). Resampling participants with
    replacement and re-pooling their pairs is the same as weighting each participant's sums by how many times
    it was drawn. So each resample is a weighted sum of per-participant sums (exact, and fast).
    The 95 % CI is the 2.5-97.5 percentile range; the one-sided lower 95 % bound is the 5th percentile.
    """

    def __init__(self, cluster_ids, seed=SEED, n_boot=N_BOOT):
        self.codes, self.ids = pd.factorize(np.asarray(cluster_ids))
        self.P = len(self.ids)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(self.P, np.full(self.P, 1.0 / self.P), size=n_boot).astype(float)

    def _sums(self, x):
        return np.bincount(self.codes, weights=np.asarray(x, float), minlength=self.P)

    def n_part(self, mask):
        """Number of participants with at least one pair where mask is true."""
        return int((self._sums(mask) > 0).sum())

    def ratio(self, num, den):
        """Point estimate and bootstrap CI of sum(num) / sum(den)."""
        qn, qd = self._sums(num), self._sums(den)
        den_tot = qd.sum()
        point = qn.sum() / den_tot if den_tot > 0 else np.nan
        with np.errstate(divide="ignore", invalid="ignore"):
            b = (self.W @ qn) / (self.W @ qd)
        b = b[np.isfinite(b)]
        if len(b) < 50:
            lo, hi, lo1 = np.nan, np.nan, np.nan
        else:
            lo, hi = np.percentile(b, [2.5, 97.5])
            lo1 = np.percentile(b, 5)
        return {"value": float(point), "ci_low": float(lo), "ci_high": float(hi), "lower_95_one_sided": float(lo1),
                "n_pairs": int(round(den_tot)) if den_tot == round(den_tot) else float(den_tot), "n_participants": int((qd > 0).sum())}

    def median(self, values, mask=None):
        """Point estimate and bootstrap CI of the pooled median (weighted median per resample)."""
        v = np.asarray(values, float)
        codes = self.codes
        if mask is not None:
            v, codes = v[mask], codes[mask]
        order = np.argsort(v, kind="stable")
        v, codes = v[order], codes[order]
        out = np.empty(len(self.W))
        for i, w in enumerate(self.W):
            cw = np.cumsum(w[codes])
            out[i] = v[np.searchsorted(cw, cw[-1] / 2.0)] if cw[-1] > 0 else np.nan
        lo, hi = np.nanpercentile(out, [2.5, 97.5])
        return {"value": float(np.median(v)), "ci_low": float(lo), "ci_high": float(hi), "n_pairs": int(len(v))}


# --------------------------------------------------------------------------
# Analysis blocks
# --------------------------------------------------------------------------
def overall_block(bt, df, with_median=True):
    """Pooled accuracy metrics for one set, each with a participant-bootstrap CI."""
    n = len(df)
    ones = np.ones(n)
    err, rel, arel = df.err.to_numpy(float), df.rel_err_pct.to_numpy(float), df.abs_rel_err_pct.to_numpy(float)
    out = {"n_pairs": int(n), "n_participants": int(bt.P),
           "bias_mgdl": bt.ratio(err, ones), "bias_pct": bt.ratio(rel, ones), "mard_pct": bt.ratio(arel, ones)}
    if with_median:
        out["median_ard_pct"] = bt.median(arel)
    for k in (15, 20, 40):
        out[f"within_{k}_{k}_pct"] = bt.ratio(within_k(df, k) * 100, ones)
    out["cgm_below_ref_pct"] = bt.ratio((df.cgm.to_numpy(float) < df.ref.to_numpy(float)) * 100.0, ones)
    z = parkes_zone_labels(df.ref, df.cgm)
    for zone in "ABCDE":
        out[f"parkes_{zone}_pct"] = bt.ratio((z == zone) * 100.0, ones)
    out["parkes_AB_pct"] = bt.ratio(np.isin(z, ["A", "B"]) * 100.0, ones)
    out["parkes_CDE_pairs"] = int(np.isin(z, ["C", "D", "E"]).sum())
    return out


def range_block(bt, df, bins, labels):
    """Accuracy by glucose range. `bins` is the bin label of every pair (by average or by CGM value)."""
    err, rel, arel = df.err.to_numpy(float), df.rel_err_pct.to_numpy(float), df.abs_rel_err_pct.to_numpy(float)
    w20 = within_k(df, 20) * 100
    rows = {}
    for lab in labels:
        m = (bins == lab).astype(float)
        n_pairs, n_part = int(m.sum()), bt.n_part(m)
        rows[lab] = {"n_pairs": n_pairs, "n_participants": n_part, "low_n": bool(n_pairs < LOW_N_PAIRS or n_part < LOW_N_PART),
                     "bias_mgdl": bt.ratio(err * m, m), "bias_pct": bt.ratio(rel * m, m), "mard_pct": bt.ratio(arel * m, m),
                     "within_20_20_pct": bt.ratio(w20 * m, m)}
    return rows


def icgm_block(bt, df):
    """FDA iCGM-style agreement table, binned by the CGM value, with the rule's own criteria and thresholds."""
    ref, cgm = df.ref.to_numpy(float), df.cgm.to_numpy(float)
    abs_err, arel = df.abs_err.to_numpy(float), df.abs_rel_err_pct.to_numpy(float)
    cb = bin3(cgm)
    rows = []
    for b, label, kind, k, thr, clause in ICGM_RULES:
        m = np.ones(len(df)) if b == "all" else (cb == b).astype(float)
        hit = (abs_err <= k) if kind == "abs" else (arel <= k)
        r = bt.ratio(hit * m * 100.0, m)
        rows.append({"cgm_bin": b, "criterion": label, "cfr_clause": clause, "threshold_pct": thr, "n_pairs": int(m.sum()),
                     "n_participants": r["n_participants"], "observed_pct": r["value"], "lower_95_one_sided_pct": r["lower_95_one_sided"],
                     "ci_low": r["ci_low"], "ci_high": r["ci_high"], "passes": bool(r["lower_95_one_sided"] > thr)})
    cross = {"cgm_below_70_ref_above_180": int(((cgm < 70) & (ref > 180)).sum()),
             "cgm_above_180_ref_below_70": int(((cgm > 180) & (ref < 70)).sum())}
    ours = {}
    for b in BIN3:   # the same bins with our 15/15, 20/20, 40/40 definition (100 mg/dL cut), for comparison
        m = (cb == b).astype(float)
        ours[b] = {f"within_{k}_{k}_pct": bt.ratio(within_k(df, k) * 100 * m, m) for k in (15, 20, 40)}
    return {"rules": rows, "cross_range_pairs": cross, "same_bins_with_100_cut_definition": ours}


def misclass_block(bt, df):
    """3x3 confusion matrices (reference category vs CGM category) and the four error rates at 70/180 and 70/200."""
    ref, cgm = df.ref.to_numpy(float), df.cgm.to_numpy(float)
    out = {}
    for high in (180, 200):
        rc, cc = cat3(ref, high), cat3(cgm, high)
        cats = ["low", "in", "high"]
        counts = {r: {c: int(((rc == r) & (cc == c)).sum()) for c in cats} for r in cats}
        row_pct = {r: {c: (counts[r][c] / max(1, sum(counts[r].values())) * 100) for c in cats} for r in cats}
        rl, rh = (rc == "low"), (rc == "high")
        rates = {
            "missed_low_pct": bt.ratio((rl & (cc != "low")) * 100.0, rl.astype(float)),
            "false_low_pct": bt.ratio((~rl & (cc == "low")) * 100.0, (~rl).astype(float)),
            "missed_high_pct": bt.ratio((rh & (cc != "high")) * 100.0, rh.astype(float)),
            "false_high_pct": bt.ratio((~rh & (cc == "high")) * 100.0, (~rh).astype(float)),
            "any_wrong_category_pct": bt.ratio((rc != cc) * 100.0, np.ones(len(df))),
        }
        out[f"70_{high}"] = {"thresholds": [70, high], "counts_ref_rows_cgm_cols": counts, "row_pct": row_pct, "rates": rates}
    det = {}
    for thr in (70, 54):
        pos, pred = ref < thr, cgm < thr
        det[str(thr)] = {"counts": {"TP": int((pos & pred).sum()), "FN": int((pos & ~pred).sum()), "FP": int((~pos & pred).sum()), "TN": int((~pos & ~pred).sum())},
                         "sensitivity_pct": bt.ratio((pos & pred) * 100.0, pos.astype(float)),
                         "specificity_pct": bt.ratio((~pos & ~pred) * 100.0, (~pos).astype(float)),
                         "ppv_pct": bt.ratio((pos & pred) * 100.0, pred.astype(float)),
                         "npv_pct": bt.ratio((~pos & ~pred) * 100.0, (~pred).astype(float))}
    out["hypo_detection"] = det
    return out


def bland_altman_rm(bt, d):
    """Bland & Altman 2007 (J Biopharm Stat 17:571-82), multiple observations per individual, true value varies.

    One-way random-effects ANOVA on the differences d (subject = random effect, unbalanced):
    MS_within = within-subject variance; between-subject variance = (MS_between - MS_within) / m0,
    m0 = (N - sum(n_i^2) / N) / (I - 1). SD of a single difference = sqrt(between + within).
    Limits of agreement = mean difference +- 1.96 * SD. CIs by the participant bootstrap (weights = draws).
    """
    d = np.asarray(d, float)
    n_i = np.bincount(bt.codes, minlength=bt.P).astype(float)
    s1, s2 = bt._sums(d), bt._sums(d * d)
    ssw_i, sb_i = s2 - s1 ** 2 / n_i, s1 ** 2 / n_i

    def calc(w):
        N, I = w @ n_i, w.sum(axis=1)
        grand = (w @ s1) / N
        msw = (w @ ssw_i) / (N - I)
        msb = ((w @ sb_i) - N * grand ** 2) / (I - 1)
        m0 = (N - (w @ (n_i ** 2)) / N) / (I - 1)
        var_b = np.maximum(0.0, (msb - msw) / m0)
        return grand, np.sqrt(var_b + msw), var_b, msw

    g, sd, vb, vw = calc(np.ones((1, bt.P)))
    gb, sdb, _, _ = calc(bt.W)
    lo_b, hi_b = gb - 1.96 * sdb, gb + 1.96 * sdb
    return {"n_pairs": int(len(d)), "n_participants": int(bt.P), "bias": float(g[0]), "bias_ci": [float(x) for x in np.percentile(gb, [2.5, 97.5])],
            "mean_of_participant_means": float(np.mean(s1 / n_i)), "sd_between_participants": float(np.sqrt(vb[0])),
            "sd_within_participant": float(np.sqrt(vw[0])), "sd_total": float(sd[0]),
            "loa_low": float(g[0] - 1.96 * sd[0]), "loa_low_ci": [float(x) for x in np.percentile(lo_b, [2.5, 97.5])],
            "loa_high": float(g[0] + 1.96 * sd[0]), "loa_high_ci": [float(x) for x in np.percentile(hi_b, [2.5, 97.5])],
            "naive_sd_ignoring_clustering": float(np.std(d, ddof=1)),
            "pct_pairs_inside_loa": float(np.mean((d >= g[0] - 1.96 * sd[0]) & (d <= g[0] + 1.96 * sd[0])) * 100)}


def meter_sensitivity(df, rng, n_draws=20):
    """Add simulated meter error to the reference and recompute MARD and the low-range bias.

    ISO 15197:2013 lets 95 % of meter results fall within 15 mg/dL (reference < 100) or 15 % (>= 100). We model
    that as Gaussian error with SD = limit / 1.96 ("ISO limit") and half of it ("half ISO"). The reference is
    kept at 20 mg/dL or more. Each level is drawn n_draws times; the mean over draws is reported.
    """
    ref, cgm = df.ref.to_numpy(float), df.cgm.to_numpy(float)

    def metrics(r):
        e = cgm - r
        low = (cgm + r) / 2 < 70
        return np.array([np.mean(np.abs(e) / r) * 100, np.mean(np.abs(e[low]) / r[low]) * 100, np.mean(e[low]), np.mean(e[low] / r[low]) * 100, low.sum()])

    names = ["mard_pct", "mard_pct_avg_below_70", "bias_mgdl_avg_below_70", "bias_pct_avg_below_70", "n_pairs_avg_below_70"]
    base = metrics(ref)
    out = {"n_pairs": int(len(df)), "n_draws": n_draws, "baseline": dict(zip(names, base.tolist()))}
    for level, scale in [("iso_limit", 1.0), ("half_iso", 0.5)]:
        sd = np.where(ref < 100, 15.0, 0.15 * ref) / 1.96 * scale
        res = np.array([metrics(np.maximum(ref + rng.normal(0.0, sd), 20.0)) for _ in range(n_draws)])
        m = res.mean(axis=0)
        out[level] = {"meter_error_sd": "7.65 mg/dL below 100, 7.65 % above" if scale == 1.0 else "3.83 mg/dL below 100, 3.83 % above",
                      **dict(zip(names, m.tolist())), "change_vs_baseline": dict(zip(names[:4], (m[:4] - base[:4]).tolist())),
                      "spread_over_draws_mard_pct": [float(res[:, 0].min()), float(res[:, 0].max())]}
    return out


def set_summary(df, cluster):
    """Counts that describe one set."""
    out = {"n_pairs": int(len(df)), "n_participants": int(df[cluster].nunique())}
    if "arm" in df:
        out["n_participants_cgm_bgm"] = int(df.loc[df.arm == "CGM+BGM", cluster].nunique())
        out["n_participants_cgm_only"] = int(df.loc[df.arm == "CGM Only", cluster].nunique())
        out["n_pairs_run_in"] = int((~df.randomised).sum())
        out["n_pairs_randomised"] = int(df.randomised.sum())
    if "cgm_clipped" in df:
        out["n_pairs_cgm_clipped_39_or_401"] = int(df.cgm_clipped.sum())
    if "pump_copy_of_meter" in df:
        out["n_pairs_pump_copy_of_meter"] = int(df.pump_copy_of_meter.sum())
        out["n_pairs_exact_repeat_reference"] = int(df.ref_is_duplicate.sum())
        out["n_pairs_from_pump_entries"] = int((df.source == "pump").sum())
    pairs_per = df.groupby(cluster).size()
    out["pairs_per_participant_median"] = float(pairs_per.median())
    out["pairs_per_participant_min_max"] = [int(pairs_per.min()), int(pairs_per.max())]
    return out


def v(stat, nd=1):
    """Format value (CI) for tables."""
    if stat is None or not np.isfinite(stat["value"]):
        return "n/a"
    s = f"{stat['value']:.{nd}f}"
    if np.isfinite(stat.get("ci_low", np.nan)):
        s += f" ({stat['ci_low']:.{nd}f} to {stat['ci_high']:.{nd}f})"
    return s


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def save(fig, outdir, name):
    path = os.path.join(outdir, "figures", name)
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


def dot_whisker(ax, xs, stats, color, fmt="{:.1f}", dy=0.0):
    """Point estimate with a 95 % CI whisker and a value label above each point."""
    vals = [s["value"] for s in stats]
    lo = [s["value"] - s["ci_low"] for s in stats]
    hi = [s["ci_high"] - s["value"] for s in stats]
    ax.errorbar(xs, vals, yerr=[lo, hi], fmt="none", ecolor=color, elinewidth=1.5, capsize=4, capthick=1.5, zorder=3)
    ax.plot(xs, vals, "o", color=color, ms=8, mec=SURFACE, mew=1.5, zorder=4)
    span = (ax.get_ylim()[1] - ax.get_ylim()[0]) if ax.get_ylim()[1] != ax.get_ylim()[0] else 1
    for x, val, h in zip(xs, vals, hi):
        ax.text(x + 0.08, val + h + dy, fmt.format(val), ha="left", va="bottom", fontsize=9, color=INK2)


def fig13(stats, outdir):
    """Figure 13: Set A accuracy by range on one axis (average of CGM and meter): n, bias, MARD."""
    rows = stats["sets"]["A"]["by_avg_range"]
    xs = np.arange(len(BIN5))
    fig, axes = plt.subplots(3, 1, figsize=(6.5, 7.4), sharex=True)
    n = [rows[b]["n_pairs"] for b in BIN5]
    axes[0].bar(xs, n, width=0.5, color=C_BLUE)
    for x, val in zip(xs, n):
        axes[0].text(x, val + max(n) * 0.02, f"{val:,}", ha="center", va="bottom", fontsize=9, color=INK2)
    axes[0].set_ylim(0, max(n) * 1.18)
    axes[0].set_ylabel("pairs")
    axes[0].set_title("Pairs per range")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y / 1000:.0f}K" if y >= 1000 else f"{y:.0f}"))

    bias = [rows[b]["bias_pct"] for b in BIN5]
    axes[1].axhline(0, color=INK2, lw=1)
    axes[1].set_ylim(min(s["ci_low"] for s in bias) - 3, max(max(s["ci_high"] for s in bias) + 3, 3))
    dot_whisker(axes[1], xs, bias, C_BLUE, fmt="{:+.1f} %")
    axes[1].set_ylabel("bias, CGM minus meter (%)")
    axes[1].set_title("Bias (negative = sensor reads low)")

    mard = [rows[b]["mard_pct"] for b in BIN5]
    axes[2].set_ylim(0, max(s["ci_high"] for s in mard) * 1.25)
    dot_whisker(axes[2], xs, mard, C_BLUE, fmt="{:.1f} %")
    axes[2].set_ylabel("MARD (%)")
    axes[2].set_title("MARD (mean absolute relative difference)")
    axes[2].set_xticks(xs, BIN5)
    axes[2].set_xlabel("average of CGM and meter glucose (mg/dL)")
    A = stats["sets"]["A"]["overall"]
    B = stats["sets"]["B"]
    # Subtitle: how far Set B (all participants) sits from Set A in any range, on bias and on MARD
    gap = max(abs(rows[b][m]["value"] - B["by_avg_range"][b][m]["value"]) for b in BIN5 for m in ("bias_pct", "mard_pct"))
    within = "1 point" if gap <= 1.0 else f"{gap:.1f} points"
    fig.suptitle(f"Set A (CGM+BGM arm, randomised phase, non-calibration pairs): n = {A['n_pairs']:,} pairs, "
                 f"{A['n_participants']} people. Whiskers = 95 % CI (participant bootstrap)\n"
                 f"Set B (all {B['overall']['n_participants']} people, {B['overall']['n_pairs']:,} pairs) matches within {within} "
                 f"on bias and MARD in every range.", fontsize=9.5, x=0.01, ha="left", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    save(fig, outdir, "13_accuracy_by_range_setA.png")


def fig14(stats, outdir):
    """Figure 14: iCGM-style agreement by CGM-value range against the 21 CFR 862.1355 thresholds (Set A)."""
    rows = stats["sets"]["A"]["icgm"]["rules"]
    fig, ax = plt.subplots(figsize=(6.5, 3.9))
    ys = np.arange(len(rows))[::-1]
    for y, r in zip(ys, rows):
        ok = r["passes"]
        ax.plot([r["lower_95_one_sided_pct"], r["observed_pct"]], [y, y], color=C_BLUE, lw=2.5, solid_capstyle="butt", zorder=3)
        ax.plot(r["observed_pct"], y, "o", color=C_BLUE, ms=8, mec=SURFACE, mew=1.5, zorder=4)
        ax.plot([r["threshold_pct"]] * 2, [y - 0.32, y + 0.32], color=C_ORANGE, lw=2.5, zorder=2)
        ax.text(101.3, y, ("pass" if ok else "FAIL") + f"  {r['observed_pct']:.1f} % (bound {r['lower_95_one_sided_pct']:.1f})",
                va="center", ha="left", fontsize=9, color=C_GOOD if ok else C_CRIT, fontweight="semibold")
    labels = [f"CGM {r['cgm_bin']}: {r['criterion']}" if r["cgm_bin"] != "all" else f"all pairs: {r['criterion']}" for r in rows]
    ax.set_yticks(ys, labels)
    ax.set_xlim(55, 100.5)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlabel("pairs that agree with the meter (%)")
    handles = [Line2D([], [], marker="o", color=C_BLUE, lw=2.5, ms=8, mec=SURFACE, label="observed, with lower one-sided 95 % bound"),
               Line2D([], [], color=C_ORANGE, lw=2.5, label="iCGM threshold (bound must exceed it)")]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=1, fontsize=9)
    A = stats["sets"]["A"]["overall"]
    ax.set_title(f"iCGM-style agreement by CGM value, Set A (n = {A['n_pairs']:,} pairs, {A['n_participants']} people)", pad=38)
    fig.tight_layout()
    save(fig, outdir, "14_icgm_agreement_by_cgm_range.png")


def fig15(stats, outdir):
    """Figure 15: misclassification at 70 / 180 (and 200) mg/dL, Set A, with 95 % CIs."""
    mc = stats["sets"]["A"]["misclassification"]
    r180, r200 = mc["70_180"]["rates"], mc["70_200"]["rates"]
    # Fifth group: sensor-shown lows the meter did not confirm = 100 - PPV at 70 mg/dL (same bootstrap CI, mirrored).
    ppv70 = mc["hypo_detection"]["70"]["ppv_pct"]
    unconfirmed_low = {"value": 100.0 - ppv70["value"], "ci_low": 100.0 - ppv70["ci_high"], "ci_high": 100.0 - ppv70["ci_low"]}
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    groups = ["Missed lows\n(meter <70, CGM >=70)", "False lows\n(meter >=70, CGM <70)", "Missed highs\n(meter high, CGM not)", "False highs\n(meter not high, CGM high)",
              "Sensor-shown lows\nnot confirmed by meter\n(of all CGM <70 pairs)"]
    bars = [(0.0, r180["missed_low_pct"], C_BLUE), (1.0, r180["false_low_pct"], C_BLUE),
            (1.82, r180["missed_high_pct"], C_BLUE), (2.18, r200["missed_high_pct"], RAMP[0]),
            (2.82, r180["false_high_pct"], C_BLUE), (3.18, r200["false_high_pct"], RAMP[0]),
            (4.3, unconfirmed_low, C_ORANGE)]  # extra gap so the long x labels of groups 4 and 5 do not touch
    top = 0
    for x, s, c in bars:
        ax.bar(x, s["value"], width=0.34, color=c, zorder=2)
        ax.errorbar(x, s["value"], yerr=[[s["value"] - s["ci_low"]], [s["ci_high"] - s["value"]]], fmt="none", ecolor=INK2, elinewidth=1.2, capsize=3, zorder=3)
        ax.text(x, s["ci_high"] + 0.4, f"{s['value']:.1f}", ha="center", va="bottom", fontsize=9, color=INK2)
        top = max(top, s["ci_high"])
    ax.set_xticks([0, 1, 2, 3, 4.3], groups, fontsize=9)
    ax.set_ylim(0, top * 1.25)
    ax.set_ylabel("share of pairs in the group (%)")
    handles = [Line2D([], [], marker="s", ls="", color=C_BLUE, ms=9, label="high threshold 180 mg/dL"),
               Line2D([], [], marker="s", ls="", color=RAMP[0], ms=9, label="high threshold 200 mg/dL"),
               Line2D([], [], marker="s", ls="", color=C_ORANGE, ms=9,
                      label="share of sensor-shown lows (CGM <70) that the meter did not\nconfirm = 100 - PPV (PPV = share of sensor lows that were real)")]
    ax.legend(handles=handles, loc="upper center")
    nl = mc["70_180"]["counts_ref_rows_cgm_cols"]
    n_low = sum(nl["low"].values())
    n_high180 = sum(nl["high"].values())
    n_high200 = sum(mc["70_200"]["counts_ref_rows_cgm_cols"]["high"].values())
    n_cgm_low = mc["hypo_detection"]["70"]["counts"]["TP"] + mc["hypo_detection"]["70"]["counts"]["FP"]
    ax.set_title(f"Pairs on the wrong side of a threshold, Set A. Whiskers = 95 % CI\n"
                 f"meter <70: {n_low:,} pairs; meter >180: {n_high180:,}; meter >200: {n_high200:,}; sensor-shown <70: {n_cgm_low:,}", fontsize=9.5)
    fig.tight_layout()
    save(fig, outdir, "15_misclassification_70_180.png")


def fig16(df, ba, outdir):
    """Figure 16: Bland-Altman (difference vs mean) for Set A as hexbin density, with repeated-measures limits."""
    avg = df.avg.to_numpy(float)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6))
    fig.subplots_adjust(wspace=0.42, top=0.8, bottom=0.17, left=0.09, right=0.86)
    panels = [(df.err.to_numpy(float), ba["mgdl"], "CGM minus meter (mg/dL)", (-150, 150), "mg/dL scale"),
              (df.rel_err_pct.to_numpy(float), ba["pct"], "CGM minus meter (% of meter)", (-100, 100), "percent scale")]
    hbs, outside = [], []
    box = dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.85)
    for ax, (d, b, ylab, yl, ttl) in zip(axes, panels):
        hb = ax.hexbin(avg, d, gridsize=(44, 30), extent=(0, 450, yl[0], yl[1]), mincnt=1, cmap="Blues", norm=LogNorm(vmin=1, vmax=5000), linewidths=0.2, edgecolors="face")
        hbs.append(hb)
        ax.axhline(b["bias"], color=INK, lw=1.4)
        for lim in (b["loa_low"], b["loa_high"]):
            ax.axhline(lim, color=INK2, lw=1.2, ls="--")
        ax.text(445, b["bias"], f"bias {b['bias']:+.1f}", va="bottom", ha="right", fontsize=9, color=INK, bbox=box)
        ax.text(445, b["loa_high"], f"+1.96 SD: {b['loa_high']:+.1f}", va="bottom", ha="right", fontsize=9, color=INK2, bbox=box)
        ax.text(445, b["loa_low"], f"-1.96 SD: {b['loa_low']:+.1f}", va="top", ha="right", fontsize=9, color=INK2, bbox=box)
        ax.set_ylim(*yl)
        ax.set_xlim(0, 450)
        ax.set_ylabel(ylab)
        ax.set_xlabel("average of CGM and meter (mg/dL)")
        ax.grid(axis="y", visible=True)
        outside.append(int(((d < yl[0]) | (d > yl[1])).sum()))
        ax.set_title(ttl, fontsize=9.5)
    cb = fig.colorbar(hbs[1], ax=axes, pad=0.03, fraction=0.05)
    cb.set_label("pairs per cell (log scale)", fontsize=9)
    cb.ax.tick_params(labelsize=8.5)
    fig.suptitle(f"Bland-Altman, Set A: {ba['mgdl']['n_pairs']:,} pairs, {ba['mgdl']['n_participants']} people. Limits of agreement (dashed) use the\n"
                 f"repeated-measures method (Bland & Altman 2007). Pairs outside the plot window: {outside[0]:,} (left), {outside[1]:,} (right).",
                 fontsize=9.5, x=0.01, ha="left", y=0.99)
    save(fig, outdir, "16_bland_altman_setA.png")


# --------------------------------------------------------------------------
# Markdown dump of the tables (optional, for drafting the write-up)
# --------------------------------------------------------------------------
def tables_markdown(stats):
    L = []
    L.append("## Sets\n")
    L.append("| Set | pairs | participants | CGM+BGM / CGM-only | run-in / randomised pairs | clipped CGM | pump copies | exact repeats |")
    L.append("|---|---|---|---|---|---|---|---|")
    for k, s in stats["sets"].items():
        d = s["definition_counts"]
        L.append(f"| {k}: {s['name']} | {d['n_pairs']:,} | {d['n_participants']} | {d.get('n_participants_cgm_bgm', '-')} / {d.get('n_participants_cgm_only', '-')} | "
                 f"{d.get('n_pairs_run_in', '-')} / {d.get('n_pairs_randomised', '-')} | {d.get('n_pairs_cgm_clipped_39_or_401', '-')} | {d.get('n_pairs_pump_copy_of_meter', '-')} | {d.get('n_pairs_exact_repeat_reference', '-')} |")
    L.append("\n## Funnel E0 -> A\n")
    L.append("| Step | pairs | participants | bias mg/dL | bias % | MARD % (95 % CI) | within 20/20 % | Parkes A+B % |")
    L.append("|---|---|---|---|---|---|---|---|")
    for f in stats["funnel_E_to_A"]:
        o = f["overall"]
        L.append(f"| {f['step']} | {o['n_pairs']:,} | {o['n_participants']} | {o['bias_mgdl']['value']:+.1f} | {o['bias_pct']['value']:+.1f} | {v(o['mard_pct'])} | {o['within_20_20_pct']['value']:.1f} | {o['parkes_AB_pct']['value']:.1f} |")
    L.append("\n## Overall per set\n")
    L.append("| Set | pairs | people | bias mg/dL (CI) | bias % (CI) | MARD % (CI) | median ARD % (CI) | 15/15 % | 20/20 % (CI) | 40/40 % | Parkes A / B / C / D / E % | CGM < meter % |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, s in stats["sets"].items():
        o = s["overall"]
        pk = " / ".join(f"{o[f'parkes_{z}_pct']['value']:.2f}" for z in "ABCDE")
        L.append(f"| {k} | {o['n_pairs']:,} | {o['n_participants']} | {v(o['bias_mgdl'])} | {v(o['bias_pct'])} | {v(o['mard_pct'])} | {v(o.get('median_ard_pct'))} | "
                 f"{o['within_15_15_pct']['value']:.1f} | {v(o['within_20_20_pct'])} | {o['within_40_40_pct']['value']:.1f} | {pk} | {o['cgm_below_ref_pct']['value']:.1f} |")
    for k, s in stats["sets"].items():
        for axis in ("by_avg_range", "by_cgm_range"):
            if axis not in s:
                continue
            L.append(f"\n## Set {k}: {axis}\n")
            L.append("| Range (mg/dL) | pairs | people | bias mg/dL (CI) | bias % (CI) | MARD % (CI) | within 20/20 % (CI) | low n |")
            L.append("|---|---|---|---|---|---|---|---|")
            for b, r in s[axis].items():
                L.append(f"| {b} | {r['n_pairs']:,} | {r['n_participants']} | {v(r['bias_mgdl'])} | {v(r['bias_pct'])} | {v(r['mard_pct'])} | {v(r['within_20_20_pct'])} | {'yes' if r['low_n'] else ''} |")
    for k, s in stats["sets"].items():
        if "icgm" not in s:
            continue
        L.append(f"\n## Set {k}: iCGM table\n")
        L.append("| CGM bin | criterion | pairs | observed % | lower one-sided 95 % bound | iCGM threshold | pass? |")
        L.append("|---|---|---|---|---|---|---|")
        for r in s["icgm"]["rules"]:
            L.append(f"| {r['cgm_bin']} | {r['criterion']} {r['cfr_clause']} | {r['n_pairs']:,} | {r['observed_pct']:.1f} | {r['lower_95_one_sided_pct']:.1f} | > {r['threshold_pct']} | {'pass' if r['passes'] else 'FAIL'} |")
        L.append(f"\ncross-range pairs: {s['icgm']['cross_range_pairs']}")
    for k, s in stats["sets"].items():
        if "misclassification" not in s:
            continue
        mc = s["misclassification"]
        for key in ("70_180", "70_200"):
            m = mc[key]
            L.append(f"\n## Set {k}: confusion matrix {key} (rows = meter, cols = CGM; count and row %)\n")
            L.append("| meter \\ CGM | low | in range | high | total |")
            L.append("|---|---|---|---|---|")
            for r in ("low", "in", "high"):
                c = m["counts_ref_rows_cgm_cols"][r]
                p = m["row_pct"][r]
                L.append(f"| {r} | {c['low']:,} ({p['low']:.1f} %) | {c['in']:,} ({p['in']:.1f} %) | {c['high']:,} ({p['high']:.1f} %) | {sum(c.values()):,} |")
            rt = m["rates"]
            L.append(f"\nmissed lows {v(rt['missed_low_pct'])}; false lows {v(rt['false_low_pct'], 2)}; missed highs {v(rt['missed_high_pct'])}; false highs {v(rt['false_high_pct'])}; any wrong category {v(rt['any_wrong_category_pct'])}")
        L.append(f"\n## Set {k}: hypoglycaemia detection\n")
        L.append("| threshold | TP / FN / FP / TN | sensitivity % (CI) | specificity % (CI) | PPV % (CI) | NPV % (CI) |")
        L.append("|---|---|---|---|---|---|")
        for thr, d in mc["hypo_detection"].items():
            c = d["counts"]
            L.append(f"| {thr} | {c['TP']:,} / {c['FN']:,} / {c['FP']:,} / {c['TN']:,} | {v(d['sensitivity_pct'])} | {v(d['specificity_pct'], 2)} | {v(d['ppv_pct'])} | {v(d['npv_pct'], 2)} |")
    for k, s in stats["sets"].items():
        if "bland_altman" not in s:
            continue
        L.append(f"\n## Set {k}: Bland-Altman\n")
        L.append("| scale | bias (CI) | SD between people | SD within person | SD total | naive SD | LoA low (CI) | LoA high (CI) | % inside |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for sc, b in s["bland_altman"].items():
            L.append(f"| {sc} | {b['bias']:+.1f} ({b['bias_ci'][0]:+.1f} to {b['bias_ci'][1]:+.1f}) | {b['sd_between_participants']:.1f} | {b['sd_within_participant']:.1f} | {b['sd_total']:.1f} | {b['naive_sd_ignoring_clustering']:.1f} | "
                     f"{b['loa_low']:+.1f} ({b['loa_low_ci'][0]:+.1f} to {b['loa_low_ci'][1]:+.1f}) | {b['loa_high']:+.1f} ({b['loa_high_ci'][0]:+.1f} to {b['loa_high_ci'][1]:+.1f}) | {b['pct_pairs_inside_loa']:.1f} |")
    ms = stats["meter_sensitivity_setA"]
    L.append("\n## Meter sensitivity (Set A)\n")
    L.append("| meter error added | MARD % | MARD % (avg < 70) | bias mg/dL (avg < 70) | bias % (avg < 70) |")
    L.append("|---|---|---|---|---|")
    b = ms["baseline"]
    L.append(f"| none (observed) | {b['mard_pct']:.1f} | {b['mard_pct_avg_below_70']:.1f} | {b['bias_mgdl_avg_below_70']:+.1f} | {b['bias_pct_avg_below_70']:+.1f} |")
    for lv in ("half_iso", "iso_limit"):
        m = ms[lv]
        L.append(f"| {lv} ({m['meter_error_sd']}) | {m['mard_pct']:.1f} ({m['change_vs_baseline']['mard_pct']:+.1f}) | {m['mard_pct_avg_below_70']:.1f} ({m['change_vs_baseline']['mard_pct_avg_below_70']:+.1f}) | "
                 f"{m['bias_mgdl_avg_below_70']:+.1f} ({m['change_vs_baseline']['bias_mgdl_avg_below_70']:+.1f}) | {m['bias_pct_avg_below_70']:+.1f} ({m['change_vs_baseline']['bias_pct_avg_below_70']:+.1f}) |")
    L.append("\n## Pump BG entries vs meter-log rows (randomised phase, non-calibration pairs)\n")
    L.append("| arm | reference source | pump row copies a meter reading | pairs | people | MARD % | median ARD % | CGM = reference exactly % | within 2 mg/dL % |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in stats["pump_entry_check"]:
        L.append(f"| {r['arm']} | {r['reference_source']} | {'yes' if r['pump_row_copies_a_meter_reading'] else 'no'} | {r['n_pairs']:,} | {r['n_participants']} | {r['mard_pct']:.1f} | {r['median_ard_pct']:.1f} | {r['pct_pairs_cgm_equals_reference']:.1f} | {r['pct_pairs_within_2_mgdl']:.1f} |")
    L.append("\n## Sensitivity variants of Set A\n")
    L.append("| Variant | pairs | people | bias % | MARD % (CI) | 20/20 % |")
    L.append("|---|---|---|---|---|---|")
    for k, o in stats["setA_variants"].items():
        L.append(f"| {k} | {o['n_pairs']:,} | {o['n_participants']} | {o['bias_pct']['value']:+.1f} | {v(o['mard_pct'])} | {o['within_20_20_pct']['value']:.1f} |")
    L.append("\n## Reconciliation with RESULTS.md (set E0 = all meter pairs, all days)\n")
    for k, val in stats["reconciliation_with_results_md"].items():
        L.append(f"- {k}: {val}")
    return "\n".join(L) + "\n"


def clean(o):
    """Make numpy / pandas values JSON-safe."""
    if isinstance(o, dict):
        return {str(k): clean(x) for k, x in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(x) for x in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(root, outdir, tables_path=None):
    os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)
    pairs = pp.build_pairs(root)
    part = pp.load_participants(root)
    pm = pairs["meter"].merge(part[["PtID", "arm", "randomisation_day"]], on="PtID", how="left")
    pm["arm"] = pm.arm.astype(str)
    pm["randomised"] = pm.day >= pm.randomisation_day
    pc = pairs["calibration"]
    ps = pairs["shanghai"].copy()
    log("loaded: meter pairs", len(pm), "calibration pairs", len(pc), "Shanghai pairs", len(ps))

    inwin, indep = pm.in_study_window.to_numpy(), (~pm.used_for_calibration).to_numpy()
    from_meter = pm.from_meter_log.to_numpy()           # reference read from the meter's own log, not a value typed into a pump (preprocess.py flag)
    rand = pm.randomised.to_numpy()
    E0 = pm
    E = pm[inwin]
    Em = pm[inwin & from_meter]
    B = pm[inwin & pm.is_verified_fingerstick.to_numpy()]   # = inwin & indep & from_meter: the headline rule built into preprocess.py
    A1 = B[B.arm == "CGM+BGM"]
    A = A1[A1.randomised]
    C = B[(B.arm == "CGM Only") & B.randomised]
    D = pc[pc.in_study_window]
    sets = {
        "A": ("meter-log fingersticks not used for calibration, in window, CGM+BGM arm, randomised phase (headline)", A, "PtID"),
        "B": ("meter-log fingersticks not used for calibration, in window, all participants and phases", B, "PtID"),
        "C": ("meter-log fingersticks not used for calibration, in window, CGM-only arm, randomised phase (sensitivity)", C, "PtID"),
        "D": ("calibration pairs, in window (sensor just before correction)", D, "PtID"),
        "E": ("all meter-table pairs in window, every reference source, including calibration-timed ones (old headline set)", E, "PtID"),
        "S": ("Shanghai fingerstick pairs (Abbott flash CGM), all patients with a fingerstick", ps, "pid"),
    }
    stats = {"generated": time.strftime("%Y-%m-%d %H:%M"), "seed": SEED, "n_boot": N_BOOT, "cache_version": pp.CACHE_VERSION,
             "bin_rules": {"range_bins": "<54; 54-69; 70-180 (70 <= v <= 180); 181-250 (180 < v <= 250); >250 mg/dL. Note: preprocess.py bins put exactly 180 and 250 in the upper bin; here they go in the lower bin as the labels say.",
                           "within_k_k": "within k mg/dL when the reference is below 100 mg/dL, else within k %",
                           "icgm_table": "the rule's own criteria: mg/dL limits for CGM < 70, percent limits at or above 70, +-20 % for all pairs; binned by CGM value",
                           "run_in_vs_randomised": "randomised phase = reference day >= participant's randomisation day (days since enrolment)",
                           "reference_source": "Sets A, B, C use only rows read from the meter's own log (source = meter, Contour Next). Pump BG entries are excluded: "
                                               "in the CGM-only arm they are mostly CGM values typed into the pump bolus calculator (see pump_entry_check)."},
             "sets": {}}
    # Evidence for the reference-source rule: pump BG entries vs meter-log rows, randomised phase, non-calibration, by arm
    chk = pm[inwin & indep & rand]
    stats["pump_entry_check"] = []
    for (arm, src, copy), g in chk.groupby(["arm", "source", "pump_copy_of_meter"], observed=True):
        stats["pump_entry_check"].append({"arm": arm, "reference_source": str(src), "pump_row_copies_a_meter_reading": bool(copy), "n_pairs": int(len(g)),
                                          "n_participants": int(g.PtID.nunique()), "mard_pct": float(g.abs_rel_err_pct.mean()), "median_ard_pct": float(g.abs_rel_err_pct.median()),
                                          "pct_pairs_cgm_equals_reference": float((g.abs_err == 0).mean() * 100), "pct_pairs_within_2_mgdl": float((g.abs_err <= 2).mean() * 100)})
    booters = {}
    for key, (name, df, cl) in sets.items():
        log(f"set {key}: {len(df):,} pairs, {df[cl].nunique()} participants")
        bt = Booter(df[cl].to_numpy())
        booters[key] = bt
        s = {"name": name, "definition_counts": set_summary(df, cl), "overall": overall_block(bt, df)}
        s["by_avg_range"] = range_block(bt, df, bin5(df.avg), BIN5)
        s["by_cgm_range"] = range_block(bt, df, bin5(df.cgm), BIN5)
        if key in ("A", "B", "C", "D", "E"):
            s["icgm"] = icgm_block(bt, df)
            s["misclassification"] = misclass_block(bt, df)
        if key == "A":
            s["bland_altman"] = {"mgdl": bland_altman_rm(bt, df.err), "pct": bland_altman_rm(bt, df.rel_err_pct)}
            s["by_ref_range_for_reconciliation"] = range_block(bt, df, bin5(df.ref), BIN5)
        if key == "S":
            s["by_group"] = {}
            for g in ("T1DM", "T2DM"):
                dg = df[df.group == g]
                s["by_group"][g] = overall_block(Booter(dg.pid.to_numpy()), dg, with_median=False)
        stats["sets"][key] = s

    # funnel from the midterm headline (E0: all meter pairs, all days) to Set A
    log("funnel E0 -> A")
    funnel = [("E0: all meter-table pairs, all days (midterm headline)", E0), ("E: keep the study window only (day 0-329)", E),
              ("Em: keep meter-log rows only (drop pump BG entries)", Em), ("B: drop pairs used for calibration", B),
              ("A1: CGM+BGM arm only", A1), ("A: randomised phase only", A)]
    stats["funnel_E_to_A"] = []
    for step, df in funnel:
        stats["funnel_E_to_A"].append({"step": step, "overall": overall_block(Booter(df.PtID.to_numpy()), df, with_median=False)})
    e0 = stats["funnel_E_to_A"][0]["overall"]
    bt0 = Booter(E0.PtID.to_numpy())
    ref_bins0 = range_block(bt0, E0, bin5(E0.ref), BIN5)
    avg_bins0 = range_block(bt0, E0, bin5(E0.avg), BIN5)
    parkes0 = "/".join("{:.2f}".format(e0["parkes_%s_pct" % z]["value"]) for z in "ABCDE")
    stats["reconciliation_with_results_md"] = {
        "results_md_meter_pairs": "475,502 pairs, bias -4.0 mg/dL (-1.3 %), MARD 10.4 %, within 20/20 88.2 %, Parkes A/B/C/D/E 88.1/10.9/0.8/0.1/0.01; MARD by reference <54 41.8 %, 54-69 18.7 %; bias by average <54 -6.6 %, 54-69 -4.8 %",
        "recomputed_E0": f"{e0['n_pairs']:,} pairs, bias {e0['bias_mgdl']['value']:+.1f} mg/dL ({e0['bias_pct']['value']:+.1f} %), MARD {e0['mard_pct']['value']:.1f} %, within 20/20 {e0['within_20_20_pct']['value']:.1f} %, "
                         f"Parkes A/B/C/D/E {parkes0}; MARD by reference <54 {ref_bins0['<54']['mard_pct']['value']:.1f} %, 54-69 {ref_bins0['54-69']['mard_pct']['value']:.1f} %; "
                         f"bias by average <54 {avg_bins0['<54']['bias_pct']['value']:+.1f} %, 54-69 {avg_bins0['54-69']['bias_pct']['value']:+.1f} %",
        "note": "Bins here put exactly 180 and 250 mg/dL in the lower range; RESULTS.md bins put them in the upper range. Differences are in the last digit at most.",
    }

    # sensitivity variants of Set A
    log("Set A variants")
    A_all = pm[inwin & indep & rand & (pm.arm == "CGM+BGM").to_numpy()]
    C_pump = pm[inwin & indep & rand & (pm.arm == "CGM Only").to_numpy() & ~from_meter]
    variants = {"A as defined (meter-log rows only)": A,
                "A plus pump BG entries (every reference source)": A_all,
                "pump BG entries only, CGM+BGM arm, randomised, not calibration": A_all[A_all.source == "pump"],
                "pump BG entries only, CGM-only arm, randomised, not calibration": C_pump,
                "A without clipped CGM values (39 or 401)": A[~A.cgm_clipped],
                "A without exact repeat references": A[~A.ref_is_duplicate],
                "A plus run-in phase (CGM+BGM arm, all in-window days)": A1}
    stats["setA_variants"] = {k: overall_block(Booter(df.PtID.to_numpy()), df, with_median=False) for k, df in variants.items()}

    log("meter sensitivity")
    stats["meter_sensitivity_setA"] = meter_sensitivity(A, np.random.default_rng(SEED + 1))
    stats["published_mard"] = PUBLISHED

    log("figures")
    fig13(stats, outdir)
    fig14(stats, outdir)
    fig15(stats, outdir)
    fig16(A, stats["sets"]["A"]["bland_altman"], outdir)

    stats["runtime_s"] = round(time.time() - T0, 1)
    path = os.path.join(outdir, "accuracy_v2_stats.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean(stats), f, indent=1)
    log("wrote", path)
    if tables_path:
        with open(tables_path, "w", encoding="utf-8") as f:
            f.write(tables_markdown(stats))
        log("wrote", tables_path)
    a = stats["sets"]["A"]["overall"]
    log(f"Set A: n = {a['n_pairs']:,} pairs, {a['n_participants']} people, MARD {v(a['mard_pct'])} %, bias {v(a['bias_pct'])} %")
    log("done in", stats["runtime_s"], "s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: python analysis/accuracy_v2.py "Uncommitted Data/Raw Data Dump" analysis [tables.md]')
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
