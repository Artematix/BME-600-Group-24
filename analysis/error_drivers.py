"""Sensor lag and the drivers of CGM error (BMEN 600 Group 24).

Project: how accurate are CGM (continuous glucose monitor) readings against fingerstick reference,
by glucose range, and what drives the error. This script answers the midterm plan's PRIMARY
UNCERTAINTY: does the low-glucose bias persist after accounting for sensor lag and calibration?

Analysis set: REPLACE-BG independent pairs (fingersticks NOT used to calibrate the sensor), all 226
participants, all in-window days, METER ROWS ONLY (readings from the Contour Next / Precision Xtra
meters). Pump-sourced BG rows are dropped: the script shows (section "reference_quality") that
most of them in the CGM-only arm after randomisation are CGM values typed into the pump, not
fingersticks. The full set with pump rows ("Set B") is kept as a labelled comparison.
Check set: CGM+BGM arm, randomised phase only.

What it does
1. Lag scan: re-pair each fingerstick with the CGM reading T minutes LATER (T = -5, 0, 5, 10, 15, 20,
   nearest reading within 5 min) and, finer, with the straight-line interpolated CGM value at 1-min
   steps (-10 to 20). Best T = lowest MARD. Accuracy by average-binned range with and without lag
   correction, participant-bootstrap 95 % CIs (1,000 resamples, fixed seed). Lag by trend bin, by
   study phase / arm, and by reference source.
2. Rate-of-change (ROC) bins, overall and by range, with and without lag correction.
3. Wear day 1-7 (sessions confirmed by a start-up calibration) and hours since session start on day 1.
4. Time of day: night (00:00-06:00) vs day, 3-hour blocks, and night inside the 70-180 / stable subset.
5. One mixed-effects model (random intercept per participant) for the absolute relative difference.
6. Regression-to-the-mean table: low-range bias binned by reference, by CGM and by their average.
7. Shanghai (15-min flash CGM): lag at -15/0/15/30 min and ROC bins, patient-bootstrap CIs.
8. A timing-slack diagnostic: meter clock vs receiver clock from calibration entries.

Usage (from the repo root):
    python analysis/error_drivers.py "Uncommitted Data/Raw Data Dump" analysis [cache folder]
Outputs: analysis/error_drivers_stats.json and analysis/figures/17_*.png to 20_*.png.
Data is loaded only through analysis/preprocess.py (parquet cache; built on first use).
"""
import json
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preprocess as pp          # shared loaders + parquet cache (analysis/preprocess.py)

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

ROOT = sys.argv[1] if len(sys.argv) > 1 else pp.DEFAULT_ROOT
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis"
CACHE = sys.argv[3] if len(sys.argv) > 3 else pp.DEFAULT_CACHE
FIG = os.path.join(OUT, "figures")
pp.check_raw_data(ROOT)
os.makedirs(FIG, exist_ok=True)

SEED = 20261027                  # fixed seed for the bootstrap
N_BOOT = 1000                    # bootstrap resamples (participants drawn with replacement)
T_COARSE = [-5, 0, 5, 10, 15, 20]        # lag shifts in minutes, nearest real reading
T_FINE = list(range(-10, 21))            # lag shifts in minutes, interpolated trace
T_OFFSETS = [0, 5, 10, 15]               # the offsets promised in the midterm plan
NEAREST_TOL_S = 300              # same rule as the cache: nearest CGM reading within 5 min of the target time
INTERP_TOL_S = 450               # interpolation needs a reading within 7.5 min on each side of the target time
SH_SHIFTS = [-15, 0, 15, 30]     # Shanghai shifts (rows are 15 min apart)
SH_TOL_S = 120
MM_MAX_ROWS = 300_000            # mixed model: subsample above this many pairs (never reached here)
RANGES = pp.RANGE_LABELS                  # <54, 54-69, 70-180, 181-250, >250 (binned by the average of CGM and reference)
LOW = ["<54", "54-69"]
ROC_LABELS = ["falling fast", "falling", "stable", "rising", "rising fast"]
ROC_DESC = {"falling fast": "< -2", "falling": "-2 to -1", "stable": "-1 to 1", "rising": "1 to 2", "rising fast": "> 2"}
HOUR_BINS = [(0, 6), (6, 12), (12, 24)]
STATS = {"analysis_set": "REPLACE-BG independent pairs (reference not used for calibration), meter rows only, all participants, in-window days",
         "comparison_set_B": "same but all reference sources (meter rows + pump BG rows)",
         "seed": SEED, "bootstrap_resamples": N_BOOT, "ci": "95 % percentile CI from a bootstrap that resamples participants"}
T0 = time.time()


def log(*a):
    """Print a progress line with the elapsed seconds."""
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Chart styling (same palette as explore_raw_data.py)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"   # categorical slots 1-3
RAMP = ["#86b6ef", "#2a78d6", "#104281"]                      # ordinal blue ramp
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 9.5, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False,
    "lines.linewidth": 1.8, "savefig.dpi": 200, "savefig.bbox": "tight",
})
ERR_KW = {"ecolor": INK2, "elinewidth": 0.9, "capsize": 2, "capthick": 0.9}


def save(fig, name):
    """Save a figure into the figures folder and close it."""
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def roc_bin(roc):
    """Bin rate of change (mg/dL per min) into 5 trend bins: < -2, -2 to -1, -1 to 1, 1 to 2, > 2. NaN stays missing."""
    r = np.asarray(roc, dtype=float)
    lab = np.select([r < -2, r < -1, r <= 1, r <= 2, r > 2], ROC_LABELS, default="")
    return pd.Categorical(np.where(lab == "", None, lab), categories=ROC_LABELS)


def boot_stats(df, err_col="err", ref_col="ref", by="PtID", seed=SEED):
    """Pooled bias (mg/dL and %) and MARD (%) with participant-bootstrap 95 % CIs.

    df needs err_col (CGM minus reference) and ref_col. Participants (column `by`) are drawn with
    replacement N_BOOT times; each resample recomputes the pooled statistic from per-participant sums.
    The same seed is used in every call, so before/after comparisons share the same resamples.
    """
    if len(df) == 0:
        return {"n": 0, "n_pt": 0}
    e = df[err_col].to_numpy(dtype=float)
    r = df[ref_col].to_numpy(dtype=float)
    rel = e / r * 100
    g = pd.DataFrame({"pt": df[by].to_numpy(), "n": 1.0, "e": e, "rel": rel, "ard": np.abs(rel)}).groupby("pt").sum()
    n_pt = len(g)
    tot = g.n.sum()
    rng = np.random.default_rng(seed)
    w = rng.multinomial(n_pt, np.full(n_pt, 1 / n_pt), size=N_BOOT).astype(float)
    N = w @ g.n.to_numpy()

    def ci(col):
        s = (w @ g[col].to_numpy()) / N
        return [round(float(np.percentile(s, 2.5)), 2), round(float(np.percentile(s, 97.5)), 2)]

    return {"n": int(tot), "n_pt": int(n_pt),
            "bias_mgdl": round(float(g.e.sum() / tot), 2), "bias_mgdl_ci": ci("e"),
            "bias_pct": round(float(g.rel.sum() / tot), 2), "bias_pct_ci": ci("rel"),
            "mard": round(float(g.ard.sum() / tot), 2), "mard_ci": ci("ard")}


def by_group(df, col, groups, err_col="err", by="PtID"):
    """boot_stats for each value of `col` in `groups` (keys are strings)."""
    return {str(gv): boot_stats(df[df[col] == gv], err_col=err_col, by=by) for gv in groups}


def paired_diff(df, flag, value="abs_rel_err_pct", by="PtID"):
    """Participant-as-unit check: per-person mean ARD with flag True minus with flag False (median, IQR, share > 0)."""
    m = df.groupby([by, flag])[value].mean().unstack().dropna()
    d = m[True] - m[False]
    return {"participants": int(len(d)), "median_points": round(float(d.median()), 2),
            "iqr_points": [round(float(d.quantile(0.25)), 2), round(float(d.quantile(0.75)), 2)],
            "share_positive": round(float((d > 0).mean()), 3)}


class CgmLookup:
    """Fast lookup of a CGM trace at any target time, per person.

    Readings are stored sorted by (person, time) in one integer key, so a target time is found by
    binary search. nearest() returns the reading closest to the target within a tolerance (the
    cache's pairing rule). interp() returns the straight-line value between the readings just
    before and just after the target, if both are within the tolerance. Missing = NaN.
    """
    SHIFT = 2 ** 36

    def __init__(self, person, t, glucose):
        person = np.asarray(person, dtype=np.int64)
        t = np.asarray(t, dtype=np.int64)
        key = person * self.SHIFT + t
        order = np.argsort(key, kind="stable")
        self.key, self.t, self.person = key[order], t[order], person[order]
        self.g = np.asarray(glucose, dtype=np.float64)[order]
        self.n = len(key)

    def _neighbours(self, person, target):
        """Distances (s) to the last reading at or before the target and the first reading after it (inf = none)."""
        person = np.asarray(person, dtype=np.int64)
        target = np.asarray(target, dtype=np.int64)
        i = np.searchsorted(self.key, person * self.SHIFT + target, side="right")
        ib, ia = np.clip(i - 1, 0, self.n - 1), np.clip(i, 0, self.n - 1)
        okb = (i - 1 >= 0) & (self.person[ib] == person)
        oka = (i < self.n) & (self.person[ia] == person)
        db = np.where(okb, target - self.t[ib], np.inf)
        da = np.where(oka, self.t[ia] - target, np.inf)
        return ib, ia, db, da

    def nearest(self, person, target, tol=NEAREST_TOL_S):
        """Glucose of the reading nearest to each target time, within tol seconds (ties go to the earlier one)."""
        ib, ia, db, da = self._neighbours(person, target)
        use_b = db <= da
        d = np.where(use_b, db, da)
        g = np.where(use_b, self.g[ib], self.g[ia])
        return np.where(d <= tol, g, np.nan)

    def interp(self, person, target, tol=INTERP_TOL_S):
        """Straight-line interpolated glucose at each target time (both neighbours within tol seconds)."""
        ib, ia, db, da = self._neighbours(person, target)
        ok = (db <= tol) & ((da <= tol) | (db == 0))
        with np.errstate(invalid="ignore", divide="ignore"):
            frac = np.where(ok, db / np.maximum(db + da, 1.0), 0.0)
        frac = np.where(np.isfinite(frac), frac, 0.0)
        return np.where(ok, self.g[ib] + (self.g[ia] - self.g[ib]) * frac, np.nan)


def lag_scan(person, ref, shifted, shifts, by_label="participants", per_person=True):
    """MARD at every shift on the complete-case pairs (a value at every shift), with CIs and the best shift.

    shifted: array (pairs x shifts) of CGM values. Returns the curve, the bootstrap share of resamples
    picking each shift as best, and the per-person best shift (counts, median, quartiles).
    """
    cc = ~np.isnan(shifted).any(axis=1)
    person, ref, shifted = person[cc], ref[cc], shifted[cc]
    if len(ref) == 0:
        return {"pairs": 0}, np.array([])
    ard = np.abs(shifted - ref[:, None]) / ref[:, None] * 100
    rel = (shifted - ref[:, None]) / ref[:, None] * 100
    d = pd.DataFrame(np.column_stack([ard, rel, shifted - ref[:, None]]))
    d["pt"] = person
    g = d.groupby("pt")
    S = g.sum().to_numpy()
    n = g.size().to_numpy(dtype=float)
    k = len(shifts)
    rng = np.random.default_rng(SEED)
    w = rng.multinomial(len(n), np.full(len(n), 1 / len(n)), size=N_BOOT).astype(float)
    N = (w @ n)[:, None]
    boot = (w @ S) / N                                   # N_BOOT x (3k)
    point = S.sum(axis=0) / n.sum()
    curve = {}
    for j, T in enumerate(shifts):
        curve[str(T)] = {"mard": round(float(point[j]), 2),
                         "mard_ci": [round(float(np.percentile(boot[:, j], 2.5)), 2), round(float(np.percentile(boot[:, j], 97.5)), 2)],
                         "bias_pct": round(float(point[k + j]), 2),
                         "bias_pct_ci": [round(float(np.percentile(boot[:, k + j], 2.5)), 2), round(float(np.percentile(boot[:, k + j], 97.5)), 2)],
                         "bias_mgdl": round(float(point[2 * k + j]), 2)}
    shifts_arr = np.array(shifts)
    best = int(shifts_arr[int(np.argmin(point[:k]))])
    boot_best = shifts_arr[boot[:, :k].argmin(axis=1)]
    out = {"pairs": int(n.sum()), by_label: int(len(n)), "by_shift_min": curve, "best_T_min": best,
           "mard_at_0_and_best": [curve["0"]["mard"], curve[str(best)]["mard"]] if "0" in curve else None,
           "best_T_bootstrap_share": {str(T): round(float(np.mean(boot_best == T)), 3) for T in shifts if np.any(boot_best == T)},
           "best_T_bootstrap_95ci": [int(np.percentile(boot_best, 2.5)), int(np.percentile(boot_best, 97.5))]}
    per_pt_best = shifts_arr[(S[:, :k] / n[:, None]).argmin(axis=1)]
    if per_person:
        out.update({"per_person_best_T_counts": {str(T): int(np.sum(per_pt_best == T)) for T in shifts},
                    "per_person_best_T_median": float(np.median(per_pt_best)),
                    "per_person_best_T_iqr": [float(np.percentile(per_pt_best, 25)), float(np.percentile(per_pt_best, 75))],
                    "per_person_best_T_min_max": [int(per_pt_best.min()), int(per_pt_best.max())]})
    return out, per_pt_best


def clean(o):
    """Make numpy / pandas values JSON-safe."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else round(float(o), 4)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


# --------------------------------------------------------------------------
# 1. Load (only through preprocess.py) and check the reference quality
# --------------------------------------------------------------------------
log("loading cached tables")
pairs = pp.build_pairs(ROOT, CACHE)
setb = pairs["independent_meter"]
setb = setb[setb.in_study_window].reset_index(drop=True)
part = pp.load_participants(ROOT, CACHE)
setb = setb.merge(part[["PtID", "arm", "randomisation_day"]], on="PtID", how="left")
setb["arm"] = setb.arm.astype(str)
setb["phase"] = np.where(setb.day < setb.randomisation_day, "run-in", "randomised")
setb["roc_bin"] = roc_bin(setb.rate_of_change)
setb["exact_match"] = setb.cgm == setb.ref

# Reference quality: a real fingerstick equals the CGM reading by chance about 2 % of the time. Pump BG rows
# in the CGM-only arm after randomisation match far more often: they are CGM values typed into the pump.
q = setb.groupby(["arm", "phase", "source"], observed=True).agg(
    pairs=("err", "size"), participants=("PtID", "nunique"), mard=("abs_rel_err_pct", "mean"),
    share_cgm_equals_reference=("exact_match", "mean"), share_ard_under_2pct=("abs_rel_err_pct", lambda x: float((x <= 2).mean())))
STATS["reference_quality"] = {
    "why": "a fingerstick and a CGM reading agree exactly by chance in about 2 % of pairs; pump BG rows typed by the patient "
           "agree far more often in the CGM-only arm after randomisation, so they are mostly CGM values typed into the pump, not fingersticks",
    "rule_used": "the analysis set keeps meter rows only (source = meter); pump rows are dropped",
    "by_arm_phase_source": [{"arm": a, "phase": ph, "source": s, "pairs": int(r.pairs), "participants": int(r.participants),
                             "mard": round(float(r.mard), 2), "share_cgm_equals_reference": round(float(r.share_cgm_equals_reference), 3),
                             "share_ard_under_2pct": round(float(r.share_ard_under_2pct), 3)} for (a, ph, s), r in q.iterrows()],
    "pump_rows_dropped": int((setb.source == "pump").sum()), "set_B_pairs": int(len(setb))}
ind = setb[setb.is_verified_fingerstick].reset_index(drop=True)        # the headline rule built into preprocess.py (meter log, not a calibration)
cgm = pp.load_cgm(ROOT, CACHE)
session_start = cgm.groupby("session_id").t.min()                    # first reading of each sensor session (all days)
cw = cgm[cgm.in_study_window & ~cgm.glucose_missing]
lookup = CgmLookup(cw.PtID.to_numpy(), cw.t.to_numpy(), cw.glucose.to_numpy())
n_cgm_window = int(len(cw))
del cgm, cw
STATS["set"] = {"pairs": int(len(ind)), "participants": int(ind.PtID.nunique()), "cgm_readings_in_window": n_cgm_window,
                "pairs_with_roc": int(ind.roc_bin.notna().sum()), "pairs_in_confirmed_sessions": int(ind.session_confirmed_by_cal.sum()),
                "pairs_by_avg_range": ind.avg_range.value_counts().to_dict(), "pairs_at_night": int(ind.is_night.sum()),
                "pairs_by_arm": ind.arm.value_counts().to_dict(), "pairs_by_phase": ind.phase.value_counts().to_dict(),
                "cgm_clipped_pairs_kept": int(ind.cgm_clipped.sum()), "overall": boot_stats(ind), "set_B_overall": boot_stats(setb)}
log(f"analysis set: {len(ind):,} independent in-window METER pairs, {ind.PtID.nunique()} participants "
    f"(Set B with pump rows: {len(setb):,}); MARD {STATS['set']['overall']['mard']} vs Set B {STATS['set']['set_B_overall']['mard']}")

# --------------------------------------------------------------------------
# 2. Lag scan
# --------------------------------------------------------------------------
pt = ind.PtID.to_numpy(np.int64)
t_ref = ind.t.to_numpy(np.int64)
ref = ind.ref.to_numpy(float)
coarse = np.column_stack([lookup.nearest(pt, t_ref + 60 * T) for T in T_COARSE])
fine = np.column_stack([lookup.interp(pt, t_ref + 60 * T) for T in T_FINE])
agree0 = float(np.mean(coarse[:, T_COARSE.index(0)] == ind.cgm.to_numpy(float)))
log(f"re-pairing at T=0 reproduces the cached CGM value in {agree0 * 100:.2f} % of pairs")

lag_c, per_pt_best_c = lag_scan(pt, ref, coarse, T_COARSE)
lag_f, per_pt_best_f = lag_scan(pt, ref, fine, T_FINE)
T_BEST = lag_c["best_T_min"]
T_FINE_BEST = lag_f["best_T_min"]
lag_c["method"] = f"nearest real CGM reading within {NEAREST_TOL_S // 60} min of (fingerstick time + T); pairs with a reading at every T"
lag_f["method"] = f"straight-line interpolation between the readings before and after (fingerstick time + T), both within {INTERP_TOL_S / 60:.1f} min"
lag_f["per_person_best_T_hist"] = {str(T): int(np.sum(per_pt_best_f == T)) for T in T_FINE}
log(f"best lag: {T_BEST} min (nearest reading), {T_FINE_BEST} min (interpolated); "
    f"per-person median {lag_f['per_person_best_T_median']} min, IQR {lag_f['per_person_best_T_iqr']}")

# the same scans on subsets: by trend, by phase / arm, by reference source (Set B), and the check set
roc_all = ind.rate_of_change.to_numpy(float)
by_trend = {}
for lab in ROC_LABELS:
    m = (ind.roc_bin == lab).to_numpy()
    sc, _ = lag_scan(pt[m], ref[m], fine[m], T_FINE, per_person=False)
    by_trend[lab] = {"pairs": sc["pairs"], "best_T_min": sc["best_T_min"], "best_T_bootstrap_95ci": sc["best_T_bootstrap_95ci"],
                     "mard_at_T": {str(T): sc["by_shift_min"][str(T)]["mard"] for T in [-5, 0, 2, 5, 7, 10, 15]},
                     "mard_at_best": sc["by_shift_min"][str(sc["best_T_min"])]["mard"]}
by_phase = {}
for lab, m in [("run-in, both arms", (ind.phase == "run-in").to_numpy()),
               ("randomised, CGM-only arm", ((ind.phase == "randomised") & (ind.arm == "CGM Only")).to_numpy()),
               ("randomised, CGM+BGM arm", ((ind.phase == "randomised") & (ind.arm == "CGM+BGM")).to_numpy())]:
    sc, _ = lag_scan(pt[m], ref[m], fine[m], T_FINE, per_person=False)
    by_phase[lab] = {"pairs": sc["pairs"], "participants": sc["participants"], "best_T_min": sc["best_T_min"],
                     "best_T_bootstrap_95ci": sc["best_T_bootstrap_95ci"], "mard_at_T": {str(T): sc["by_shift_min"][str(T)]["mard"] for T in [0, 5, 10]}}
# Set B (with pump rows) and pump rows alone, for comparison
ptb, tb, refb = setb.PtID.to_numpy(np.int64), setb.t.to_numpy(np.int64), setb.ref.to_numpy(float)
fine_b = np.column_stack([lookup.interp(ptb, tb + 60 * T) for T in T_FINE])
by_source = {}
for lab, m in [("Set B: meter + pump rows", np.ones(len(setb), bool)), ("pump rows only", (setb.source == "pump").to_numpy()),
               ("pump rows, CGM-only arm, randomised", ((setb.source == "pump") & (setb.arm == "CGM Only") & (setb.phase == "randomised")).to_numpy())]:
    sc, _ = lag_scan(ptb[m], refb[m], fine_b[m], T_FINE, per_person=False)
    by_source[lab] = {"pairs": sc["pairs"], "best_T_min": sc["best_T_min"], "best_T_bootstrap_95ci": sc["best_T_bootstrap_95ci"],
                      "mard_at_T": {str(T): sc["by_shift_min"][str(T)]["mard"] for T in [-5, 0, 2, 5, 10]}}
del fine_b
chk_mask = ((ind.arm == "CGM+BGM") & (ind.phase == "randomised")).to_numpy()
chk_scan, _ = lag_scan(pt[chk_mask], ref[chk_mask], coarse[chk_mask], T_COARSE)
STATS["lag"] = {"T0_matches_cache_share": round(agree0, 4), "coarse": lag_c, "fine": lag_f,
                "T_best_used_for_correction_min": T_BEST, "T_best_interpolated_min": T_FINE_BEST,
                "pairs_available_per_shift": {str(T): int(np.sum(~np.isnan(coarse[:, j]))) for j, T in enumerate(T_COARSE)},
                "by_trend_bin_interpolated": by_trend, "by_phase_interpolated": by_phase, "by_reference_source_interpolated": by_source}
log("best T by trend: " + ", ".join(f"{k} {v['best_T_min']} min ({v['mard_at_T']['0']}->{v['mard_at_best']})" for k, v in by_trend.items()))
log("best T by phase: " + ", ".join(f"{k} {v['best_T_min']}" for k, v in by_phase.items()) + " | " + ", ".join(f"{k} {v['best_T_min']}" for k, v in by_source.items()))

# --------------------------------------------------------------------------
# 3. Lag correction: accuracy by range at T = 0 and at the best shift (same pairs)
# --------------------------------------------------------------------------
for j, T in enumerate(T_COARSE):
    ind[f"cgm_T{T}"] = coarse[:, j]
ind["cgm_Tfine"] = fine[:, T_FINE.index(T_FINE_BEST)]
ind["cgm_lag"] = ind[f"cgm_T{T_BEST}"]
lag = ind[ind.cgm_lag.notna()].copy()
lag["err_lag"] = lag.cgm_lag - lag.ref
lag["avg_range_lag"] = pp.glucose_range((lag.cgm_lag + lag.ref) / 2).to_numpy()


def before_after(df):
    """Bias / MARD overall and by average-binned range, as paired (T = 0) and lag-corrected (T = T_BEST), same pairs."""
    return {"pairs": int(len(df)), "participants": int(df.PtID.nunique()),
            "before": {"overall": boot_stats(df), **by_group(df, "avg_range", RANGES)},
            "after": {"overall": boot_stats(df, "err_lag"), **by_group(df, "avg_range_lag", RANGES, "err_lag")},
            "after_binned_by_unshifted_average": by_group(df, "avg_range", RANGES, "err_lag"),
            "before_by_reference_bin": by_group(df, "ref_range", RANGES),
            "after_by_reference_bin": by_group(df, "ref_range", RANGES, "err_lag")}


def offsets_table(df):
    """Low-range bias and MARD at every promised offset (0/5/10/15 min, nearest reading) and at the interpolated best T."""
    out = {}
    for T in T_OFFSETS + ["fine"]:
        col = f"cgm_T{T}" if T != "fine" else "cgm_Tfine"
        d = df[df[col].notna()].copy()
        d["e"] = d[col] - d.ref
        d["rng"] = pp.glucose_range((d[col] + d.ref) / 2).to_numpy()
        key = f"T{T}" if T != "fine" else f"T{T_FINE_BEST}_interpolated"
        out[key] = {"overall": boot_stats(d, "e"), **by_group(d, "rng", RANGES, "e")}
    return out


STATS["lag_correction"] = {"method": f"same pairs; CGM reading nearest to fingerstick time + {T_BEST} min (within 5 min); ranges re-binned by the new average",
                           "all_participants": before_after(lag), "offsets": offsets_table(ind),
                           "set_B_with_pump_rows": {"before_by_avg_range": by_group(setb, "avg_range", RANGES)}}
ba = STATS["lag_correction"]["all_participants"]
log("primary: bias % by average bin, before -> after lag correction")
for r in RANGES:
    b, a = ba["before"][r], ba["after"][r]
    log(f"  {r:>8}: {b['bias_pct']:+.1f} % {b['bias_pct_ci']} (n={b['n']:,}) -> {a['bias_pct']:+.1f} % {a['bias_pct_ci']} (n={a['n']:,}); "
        f"MARD {b['mard']:.1f} -> {a['mard']:.1f} %")

# check set: CGM+BGM arm, randomised phase
STATS["lag_check_cgm_bgm_randomised"] = {"set": "CGM+BGM arm, meter rows, pairs on or after the randomisation day", "scan": chk_scan,
                                         **before_after(lag[(lag.arm == "CGM+BGM") & (lag.phase == "randomised")])}
log(f"check set (CGM+BGM, randomised): {chk_scan['pairs']:,} pairs, best T {chk_scan['best_T_min']} min")

# --------------------------------------------------------------------------
# 4. Rate of change
# --------------------------------------------------------------------------
r = lag[lag.roc_bin.notna()]
STATS["roc"] = {"bins_mgdl_per_min": ROC_DESC, "roc_source": "central difference of the paired CGM reading's neighbours (cache); the bin is the trend at the fingerstick time",
                "pairs": int(len(r)), "share_of_lag_set_with_roc": round(float(len(r) / len(lag)), 4),
                "pairs_by_bin": r.roc_bin.value_counts().reindex(ROC_LABELS).to_dict(),
                "before": by_group(r, "roc_bin", ROC_LABELS), "after": by_group(r, "roc_bin", ROC_LABELS, "err_lag"),
                "range_x_roc_before": {rg: by_group(r[r.avg_range == rg], "roc_bin", ROC_LABELS) for rg in RANGES},
                "range_x_roc_after": {rg: by_group(r[r.avg_range_lag == rg], "roc_bin", ROC_LABELS, "err_lag") for rg in RANGES}}
log("ROC: " + "; ".join(f"{k} MARD {v['mard']:.1f}->{STATS['roc']['after'][k]['mard']:.1f}" for k, v in STATS["roc"]["before"].items()))

# --------------------------------------------------------------------------
# 5. Wear day
# --------------------------------------------------------------------------
wd = ind[ind.session_confirmed_by_cal & ind.wear_day.between(1, 7)].copy()
wd["hours_since_start"] = (wd.t_cgm - wd.session_id.map(session_start)) / 3600
d1 = wd[wd.wear_day == 1]
wd["wear_grp"] = np.select([wd.wear_day == 1, wd.wear_day == 7], ["1", "7"], default="2-6")
wd["is_day1"] = wd.wear_day == 1
STATS["wear_day"] = {"why_confirmed_only": "a session is confirmed when a calibration was entered in the 30 min before its first reading; "
                                           "unconfirmed sessions are mostly signal-loss fragments, where wear_day restarts at 1 by mistake",
                     "pairs": int(len(wd)), "pairs_excluded_unconfirmed": int((~ind.session_confirmed_by_cal).sum()),
                     "pairs_excluded_wear_day_over_7": int((ind.session_confirmed_by_cal & (ind.wear_day > 7)).sum()),
                     "by_wear_day": by_group(wd, "wear_day", range(1, 8)),
                     "day1_by_hours_since_first_reading": {f"{a}-{b} h": boot_stats(d1[(d1.hours_since_start >= a) & (d1.hours_since_start < b)]) for a, b in HOUR_BINS},
                     "per_person_day1_minus_days2to7": paired_diff(wd, "is_day1"),
                     "wear_group_x_range": {grp: by_group(wd[wd.wear_grp == grp], "avg_range", RANGES) for grp in ["1", "2-6", "7"]},
                     "sensitivity_all_sessions_by_wear_day": by_group(ind[ind.wear_day.between(1, 7)], "wear_day", range(1, 8))}
log("wear day MARD: " + ", ".join(f"d{k} {v['mard']:.1f}" for k, v in STATS["wear_day"]["by_wear_day"].items()))

# --------------------------------------------------------------------------
# 6. Time of day
# --------------------------------------------------------------------------
ind["block"] = ((ind.hour // 3) * 3).astype(int)
blocks = sorted(ind.block.unique())
sub = ind[(ind.avg_range == "70-180") & (ind.roc_bin == "stable")]
night = ind[ind.is_night]
STATS["time_of_day"] = {"night_definition": "00:00 to 06:00 on the meter clock",
                        "night": boot_stats(night), "day": boot_stats(ind[~ind.is_night]),
                        "per_person_night_minus_day": paired_diff(ind, "is_night"),
                        "by_3h_block": {f"{b:02d}-{b + 3:02d}": boot_stats(ind[ind.block == b]) for b in blocks},
                        "confound_check": {"subset": "pairs with average 70-180 mg/dL and stable rate of change (-1 to 1 mg/dL per min)",
                                           "night": boot_stats(sub[sub.is_night]), "day": boot_stats(sub[~sub.is_night]),
                                           "per_person_night_minus_day": paired_diff(sub, "is_night"),
                                           "share_cgm_low_by_over_40pct": {"night": round(float((sub[sub.is_night].rel_err_pct < -40).mean()), 4), "day": round(float((sub[~sub.is_night].rel_err_pct < -40).mean()), 4)},
                                           "share_cgm_high_by_over_40pct": {"night": round(float((sub[sub.is_night].rel_err_pct > 40).mean()), 4), "day": round(float((sub[~sub.is_night].rel_err_pct > 40).mean()), 4)}},
                        "mix": {"share_of_night_pairs_by_avg_range": night.avg_range.value_counts(normalize=True).round(3).to_dict(),
                                "share_of_day_pairs_by_avg_range": ind[~ind.is_night].avg_range.value_counts(normalize=True).round(3).to_dict(),
                                "stable_share_night": round(float((night.roc_bin == "stable").mean()), 3),
                                "stable_share_day": round(float((ind[~ind.is_night].roc_bin == "stable").mean()), 3)}}
tod = STATS["time_of_day"]
log(f"night MARD {tod['night']['mard']:.1f} vs day {tod['day']['mard']:.1f}; within 70-180 stable: {tod['confound_check']['night']['mard']:.1f} vs {tod['confound_check']['day']['mard']:.1f}")

# --------------------------------------------------------------------------
# 7. Mixed-effects model
# --------------------------------------------------------------------------
mm = ind[ind.roc_bin.notna() & ind.session_confirmed_by_cal & ind.wear_day.between(1, 7)].copy()
mm["ard"] = mm.abs_rel_err_pct.astype(float)
mm["range"] = mm.avg_range.astype(str)
mm["roc"] = mm.roc_bin.astype(str)
mm["wear"] = np.select([mm.wear_day == 1, mm.wear_day == 7], ["1", "7"], default="2-6")
mm["night"] = mm.is_night.astype(int)
n_avail = len(mm)
if n_avail > MM_MAX_ROWS:
    mm = mm.sample(MM_MAX_ROWS, random_state=SEED)
formula = "ard ~ C(range, Treatment('70-180')) + C(roc, Treatment('stable')) + C(wear, Treatment('2-6')) + night + C(arm, Treatment('CGM Only'))"
t1 = time.time()
res = smf.mixedlm(formula, mm, groups=mm["PtID"]).fit()
ci = res.conf_int()


def plain(term):
    """Turn a statsmodels term name into plain words."""
    if term == "Intercept":
        return "baseline: 70-180 mg/dL, stable, wear day 2-6, daytime, CGM-only arm"
    if term == "night":
        return "night (00:00-06:00) vs day"
    inner = term[term.index("[T.") + 3:-1]
    if term.startswith("C(range"):
        return f"range {inner} vs 70-180"
    if term.startswith("C(roc"):
        return f"{inner} ({ROC_DESC[inner]} mg/dL per min) vs stable"
    if term.startswith("C(wear"):
        return f"wear day {inner} vs 2-6"
    if term.startswith("C(arm"):
        return f"{inner} arm vs CGM-only"
    return term


STATS["mixed_model"] = {"outcome": "absolute relative difference (ARD, %) of each pair, as paired (no lag correction)",
                        "fixed_effects": "range (by average) + rate-of-change bin + wear day (1, 2-6, 7) + night + study arm",
                        "random_effect": "intercept per participant", "fit": "restricted maximum likelihood (statsmodels MixedLM)",
                        "pairs_available": int(n_avail), "pairs_used": int(len(mm)), "participants": int(mm.PtID.nunique()),
                        "converged": bool(res.converged), "fit_seconds": round(time.time() - t1, 1),
                        "between_person_sd": round(float(np.sqrt(res.cov_re.iloc[0, 0])), 2), "residual_sd": round(float(np.sqrt(res.scale)), 2),
                        "terms": [{"term": plain(k), "coef": round(float(res.params[k]), 2),
                                   "ci": [round(float(ci.loc[k, 0]), 2), round(float(ci.loc[k, 1]), 2)],
                                   "p": float(res.pvalues[k])} for k in res.params.index if k != "Group Var"]}
log(f"mixed model fitted in {time.time() - t1:.0f} s on {len(mm):,} pairs; converged={res.converged}")
for tm in STATS["mixed_model"]["terms"]:
    log(f"  {tm['term']}: {tm['coef']:+.2f} points {tm['ci']}")

# --------------------------------------------------------------------------
# 8. Regression to the mean: the same pairs binned three ways
# --------------------------------------------------------------------------
STATS["regression_to_the_mean"] = {rg: {"by_reference": boot_stats(ind[ind.ref_range == rg]), "by_cgm": boot_stats(ind[ind.cgm_range == rg]),
                                        "by_average": boot_stats(ind[ind.avg_range == rg]),
                                        "by_average_lag_corrected": boot_stats(lag[lag.avg_range_lag == rg], "err_lag")} for rg in RANGES}

# --------------------------------------------------------------------------
# 9. Shanghai: lag at 15-min steps and ROC bins
# --------------------------------------------------------------------------
shp = pairs["shanghai"].copy()
shc = pp.load_shanghai(ROOT, CACHE)["cgm"]
shc = shc[shc.cgm.notna()]
codes = {f: i for i, f in enumerate(sorted(shc.file.unique()))}
sh_lookup = CgmLookup(shc.file.map(codes).to_numpy(), (shc.ts.astype("int64") // 10 ** 9).to_numpy(), shc.cgm.to_numpy())
sh_file = shp.file.map(codes).to_numpy(np.int64)
sh_t = (shp.ts.astype("int64") // 10 ** 9).to_numpy(np.int64)
sh_shift = np.column_stack([sh_lookup.nearest(sh_file, sh_t + 60 * T, tol=SH_TOL_S) for T in SH_SHIFTS])
sh_scan, _ = lag_scan(shp.pid.to_numpy(), shp.ref.to_numpy(float), sh_shift, SH_SHIFTS, by_label="patients")
shp["roc_bin"] = roc_bin(shp.rate_of_change)
shp["exact_match"] = shp.cgm == shp.ref
shr = shp[shp.roc_bin.notna()].copy()
STATS["shanghai"] = {"set": "Shanghai T1DM + T2DM fingerstick pairs; the fingerstick sits on the nearest 15-min CGM row (up to 7.5 min slack)",
                     "pairs": int(len(shp)), "patients": int(shp.pid.nunique()), "ci_unit": "patient bootstrap",
                     "share_cgm_equals_reference": round(float(shp.exact_match.mean()), 3),
                     "lag_scan": sh_scan, "roc_pairs_by_bin": shr.roc_bin.value_counts().reindex(ROC_LABELS).to_dict(),
                     "roc": by_group(shr, "roc_bin", ROC_LABELS, by="pid"),
                     "by_group": {g: boot_stats(shp[shp.group == g], by="pid") for g in ["T1DM", "T2DM"]}}
log(f"Shanghai: best T {sh_scan['best_T_min']} min; MARD by shift " + ", ".join(f"{k}: {v['mard']:.1f}" for k, v in sh_scan["by_shift_min"].items()))

# --------------------------------------------------------------------------
# 10. Timing slack: meter clock vs receiver clock (calibration entries)
# --------------------------------------------------------------------------
cal = pp.load_calibrations(ROOT, CACHE)
bgm = pp.load_bgm(ROOT, CACHE)
c = cal[cal.in_study_window & ~cal.value_missing & ~cal.value_out_of_range][["PtID", "t", "value"]].rename(columns={"t": "t_cal"})
m = bgm[bgm.from_meter_log & bgm.in_study_window & ~bgm.value_out_of_range][["PtID", "t", "value"]]   # meter-log rows incl. calibration ones: this measures the calibration-vs-meter clock offset
c["value"] = c.value.astype(float)
m["value"] = m.value.astype(float)
off = pd.merge_asof(c.sort_values("t_cal"), m.sort_values("t"), left_on="t_cal", right_on="t", by=["PtID", "value"], direction="nearest", tolerance=900)
off = off[off.t.notna()]
offset_min = (off.t_cal - off.t) / 60
STATS["timing_slack"] = {"what": "calibration entry time (receiver clock) minus the matching meter reading time (meter clock), same value, within 15 min; "
                                 "includes the delay between the fingerstick and typing it in",
                         "matched_entries": int(len(off)), "median_min": round(float(offset_min.median()), 2),
                         "quartiles_min": [round(float(offset_min.quantile(q)), 2) for q in (0.25, 0.75)],
                         "share_within_1_min": round(float((offset_min.abs() <= 1).mean()), 3),
                         "share_within_2_min": round(float((offset_min.abs() <= 2).mean()), 3),
                         "share_within_5_min": round(float((offset_min.abs() <= 5).mean()), 3),
                         "pair_dt_s_quartiles": [int(ind.dt_s.quantile(q)) for q in (0.25, 0.5, 0.75)]}
log(f"timing slack: median {offset_min.median():.1f} min, {STATS['timing_slack']['share_within_2_min'] * 100:.0f} % within 2 min")

# --------------------------------------------------------------------------
# Figures 17-20
# --------------------------------------------------------------------------
# 17. MARD vs lag shift
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), gridspec_kw={"width_ratios": [3, 2]})
ax = axes[0]
cm = [lag_c["by_shift_min"][str(T)]["mard"] for T in T_COARSE]
lo = [lag_c["by_shift_min"][str(T)]["mard_ci"][0] for T in T_COARSE]
hi = [lag_c["by_shift_min"][str(T)]["mard_ci"][1] for T in T_COARSE]
fm = [lag_f["by_shift_min"][str(T)]["mard"] for T in T_FINE]
ax.fill_between(T_COARSE, lo, hi, color=C_BLUE, alpha=0.18, linewidth=0, label="95 % CI")
ax.plot(T_COARSE, cm, marker="o", ms=4, color=C_BLUE, label="nearest reading")
ax.plot(T_FINE, fm, color=C_ORANGE, lw=1.3, ls="--", label="interpolated trace")
ax.axvline(T_FINE_BEST, color=AXIS, lw=1, ls=":")
ax.text(T_FINE_BEST + 0.5, min(cm) + 0.15, f"lowest at {T_FINE_BEST} min", fontsize=9, color=INK2, va="bottom")
ax.set_xticks([-10, -5, 0, 5, 10, 15, 20])
ax.set_xlabel("T: CGM value taken T min after the fingerstick")
ax.set_ylabel("MARD (%)")
ax.set_title(f"MARD is lowest {T_BEST}-{T_FINE_BEST} min after the fingerstick")
ax.legend(loc="upper center", handlelength=1.6, ncol=1)
ax = axes[1]
ax.hist(per_pt_best_f, bins=np.arange(-10.5, 21.5, 1), color=C_BLUE, rwidth=0.85)
ax.axvline(lag_f["per_person_best_T_median"], color=INK2, lw=1, ls=":")
ax.text(lag_f["per_person_best_T_median"] + 0.6, ax.get_ylim()[1] * 0.9, f"median {lag_f['per_person_best_T_median']:.0f} min", fontsize=9, color=INK2)
ax.set_xlabel("best T per participant (min)")
ax.set_ylabel("participants")
ax.set_title("Per-participant best shift")
ax.set_xticks([-10, -5, 0, 5, 10, 15, 20])
fig.suptitle(f"Figure 17. Sensor lag: time shift that minimises MARD ({lag_c['pairs']:,} verified fingerstick pairs)", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "17_lag_scan.png")

# 18. Low-range bias with and without lag correction
low_stays = all(ba["after"][rg]["bias_pct_ci"][1] < 0 for rg in LOW)
fig, ax = plt.subplots(figsize=(6.4, 3.3))
x = np.arange(len(RANGES))
wdt = 0.38
for off_x, key, col, lab in [(-wdt / 2, "before", RAMP[0], "as paired (T = 0)"), (wdt / 2, "after", C_BLUE, f"lag-corrected (CGM {T_BEST} min later)")]:
    vals = [ba[key][rg]["bias_pct"] for rg in RANGES]
    err = np.array([[ba[key][rg]["bias_pct"] - ba[key][rg]["bias_pct_ci"][0], ba[key][rg]["bias_pct_ci"][1] - ba[key][rg]["bias_pct"]] for rg in RANGES]).T
    ax.bar(x + off_x, vals, wdt, color=col, label=lab, yerr=err, error_kw=ERR_KW)
    for xi, v, rg in zip(x + off_x, vals, RANGES):
        edge = ba[key][rg]["bias_pct_ci"][0] if v < 0 else ba[key][rg]["bias_pct_ci"][1]
        ax.text(xi, edge + (-0.3 if v < 0 else 0.3), f"{v:+.1f}", ha="center", va="top" if v < 0 else "bottom", fontsize=9, color=INK2)
ax.axhline(0, color=AXIS, lw=1)
ax.set_xticks(x)
ax.set_xticklabels([f"{rg}\n(n={ba['before'][rg]['n']:,})" for rg in RANGES])
ax.set_xlabel("average of CGM and fingerstick (mg/dL)")
ax.set_ylabel("bias: CGM minus fingerstick (%)")
ylo, yhi = ax.get_ylim()
ax.set_ylim(ylo - 1.5, yhi + 1)
ax.legend(loc="lower right")
ax.set_title(f"Figure 18. The low-range bias {'stays' if low_stays else 'changes'} after lag correction (bars: mean, lines: 95 % CI)")
fig.tight_layout()
save(fig, "18_low_range_bias_lag_corrected.png")

# 19. Bias and MARD by rate-of-change bin
fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.2))
x = np.arange(len(ROC_LABELS))
labels = [f"{k}\n{ROC_DESC[k]}" for k in ROC_LABELS]
for ax, metric, ylab in [(axes[0], "bias_pct", "bias: CGM minus fingerstick (%)"), (axes[1], "mard", "MARD (%)")]:
    for off_x, key, col, lab in [(-wdt / 2, "before", RAMP[0], "as paired (T = 0)"), (wdt / 2, "after", C_BLUE, f"lag-corrected ({T_BEST} min)")]:
        vals = [STATS["roc"][key][k][metric] for k in ROC_LABELS]
        err = np.array([[STATS["roc"][key][k][metric] - STATS["roc"][key][k][metric + "_ci"][0], STATS["roc"][key][k][metric + "_ci"][1] - STATS["roc"][key][k][metric]] for k in ROC_LABELS]).T
        ax.bar(x + off_x, vals, wdt, color=col, label=lab, yerr=err, error_kw=ERR_KW)
    ax.axhline(0, color=AXIS, lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylab)
    ax.set_xlabel("rate of change (mg/dL per min)")
axes[0].set_title("Bias by trend")
axes[1].set_title("MARD by trend")
axes[0].legend(loc="upper right")
fig.suptitle(f"Figure 19. Fast-moving glucose carries the largest error; lag correction removes part of it ({STATS['roc']['pairs']:,} pairs)", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "19_error_by_rate_of_change.png")

# 20. Wear day, first hours, night vs day
fig, axes = plt.subplots(1, 3, figsize=(6.8, 3.65), gridspec_kw={"width_ratios": [3, 2, 1.8]})
ax = axes[0]
days = list(range(1, 8))
v = [STATS["wear_day"]["by_wear_day"][str(d)]["mard"] for d in days]
lo = [STATS["wear_day"]["by_wear_day"][str(d)]["mard_ci"][0] for d in days]
hi = [STATS["wear_day"]["by_wear_day"][str(d)]["mard_ci"][1] for d in days]
ax.fill_between(days, lo, hi, color=C_BLUE, alpha=0.18, linewidth=0)
ax.plot(days, v, marker="o", ms=4, color=C_BLUE)
for d, vi, h in zip(days, v, hi):
    ax.text(d, h + 0.15, f"{vi:.1f}", ha="center", fontsize=9, color=INK2)
ax.set_xticks(days)
ax.set_xlabel("sensor wear day")
ax.set_ylabel("MARD (%)")
ax.set_title("By wear day (95 % CI band)")
ax = axes[1]
hb = STATS["wear_day"]["day1_by_hours_since_first_reading"]
keys = list(hb.keys())
v = [hb[k]["mard"] for k in keys]
err = np.array([[hb[k]["mard"] - hb[k]["mard_ci"][0], hb[k]["mard_ci"][1] - hb[k]["mard"]] for k in keys]).T
ax.bar(np.arange(len(keys)), v, 0.6, color=RAMP[2], yerr=err, error_kw=ERR_KW)
for i, (k, vi) in enumerate(zip(keys, v)):
    ax.text(i, hb[k]["mard_ci"][1] + 0.2, f"{vi:.1f}", ha="center", fontsize=9, color=INK2)
ax.set_xticks(np.arange(len(keys)))
ax.set_xticklabels(keys)
ax.set_xlabel("hours since first reading, day 1")
ax.set_title("First day by hours")
ax = axes[2]
v = [tod["night"]["mard"], tod["day"]["mard"]]
err = np.array([[tod[k]["mard"] - tod[k]["mard_ci"][0], tod[k]["mard_ci"][1] - tod[k]["mard"]] for k in ["night", "day"]]).T
ax.bar([0, 1], v, 0.6, color=[RAMP[2], RAMP[0]], yerr=err, error_kw=ERR_KW)
for i, (k, vi) in enumerate(zip(["night", "day"], v)):
    ax.text(i, tod[k]["mard_ci"][1] + 0.2, f"{vi:.1f}", ha="center", fontsize=9, color=INK2)
ax.set_xticks([0, 1])
ax.set_xticklabels(["night\n00-06", "day"])
pp_nd = tod["per_person_night_minus_day"]  # participant-as-unit check behind this pooled panel
ax.set_title(f"Time of day\nper person: no difference\n(median {pp_nd['median_points']:+.1f} points)", fontsize=8.5)
ymax = max(a.get_ylim()[1] for a in axes)
for a in axes:
    a.set_ylim(0, ymax + 0.8)
fig.suptitle("Figure 20. MARD by wear day, by hours on day 1, and night vs day (verified fingerstick pairs)", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
fig.text(0.01, 0.01,
         f"Time of day panel pools all pairs. Per person the night-day difference is about zero (median {pp_nd['median_points']:+.1f} points).\n"
         "Night has more large errors (over 40 %) in both directions, CGM too low and CGM too high.",
         ha="left", va="bottom", fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0.1, 1, 0.93))
save(fig, "20_wear_day_and_time_of_day.png")

# --------------------------------------------------------------------------
# Save
# --------------------------------------------------------------------------
STATS["runtime_s"] = round(time.time() - T0, 1)
with open(os.path.join(OUT, "error_drivers_stats.json"), "w", encoding="utf-8") as f:
    json.dump(clean(STATS), f, indent=1)
log("wrote", os.path.join(OUT, "error_drivers_stats.json"), f"runtime {STATS['runtime_s']} s")
