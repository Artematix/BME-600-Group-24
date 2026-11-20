"""Wear day 1: sensors that fail early, or every sensor settling in? (BMEN 600 Group 24)

Project: how accurate is a CGM (continuous glucose monitor) against fingerstick readings, and what drives
the error. ERROR_DRIVERS.md found the Dexcom G4 worst on wear day 1 (MARD 15.2 % vs 11.8 % on day 7).
This script separates two stories behind that result:
  (a) selection: sensors that are bad from the start get pulled early and replaced, so day 1 holds more
      bad sensors than later days;
  (b) settling: every sensor is worse on its first day and improves afterwards.

Analysis set: the headline verified fingerstick pairs (preprocess.verified_pairs: reference from the meter
log, not a calibration, inside the study window; 168,990 pairs, 226 people), restricted to sensor sessions
confirmed by a start-up calibration, as in error_drivers.py.

Sensor sessions. The cache infers a session from gaps of >= 115 min between readings (no sensor ID exists).
A fragment that starts WITHOUT a start-up calibration is the same sensor resuming after a signal gap (the
G4 needs a 2-hour warm-up and two calibrations at every real start), so this script glues such fragments
back onto the confirmed session they follow, as long as the whole session stays under 170 h (the G4 stops
at 7 days). Wear day is then recomputed from the glued session's first reading with the cache's own rule
(wear_day = floor(hours since first reading / 24) + 1). The raw (unglued) sessions are kept as a sensitivity.

What it does
1. Describes the sessions: how many, how long, how many end early, reach day 7, or run past it.
2. Selection test: day-1 error by how long the session lasted; how much of the day-1 excess over day 7
   comes from sessions that never reached day 7; the same check inside the first 12 hours only and
   within person.
3. Settling test: error by hours since start (6- and 12-h bins) and by wear day within 7-day sessions;
   a settling fit (floor + exponential); each sensor's own day-1 minus day-2 / day-7 error; each person's
   own day-1 minus day-7 error.
4. Direction: bias and spread by wear day (is day 1 biased, or just noisier?).
5. Calibration check: day-1 error by 6-h block; error by hours since the last calibration, day 1 vs later;
   sensor error at the moment of each calibration by wear day; calibrations per day.
6. Low range (< 70 mg/dL by the average of CGM and meter): day 1 vs later by session length; missed-low
   and false-low rates by wear day.
CIs: 95 % percentile intervals from a participant bootstrap (1,000 resamples, fixed seed). All 226
participants are resampled once and every statistic uses the same resamples, so differences are paired.

Usage (from the repo root):
    python analysis/wear_day.py "Uncommitted Data/Raw Data Dump" analysis [cache folder]
Outputs: analysis/wear_day_stats.json, analysis/figures/33_wear_day_selection_vs_settling.png,
         analysis/figures/34_wear_day_calibration.png.
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
from scipy.optimize import curve_fit

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

SEED = 20261106                  # fixed seed for the bootstrap
N_BOOT = 1000                    # bootstrap resamples (participants drawn with replacement)
MAX_SESSION_H = 170              # a glued session may not run longer than this (G4 hard stop: 7 days = 168 h from sensor start)
STARTUP_CAL_WINDOW_S = pp.STARTUP_CAL_WINDOW_S   # calibrations up to 30 min before the first reading belong to the session
MIN_PAIRS_SESSION = 3            # a session needs this many pairs on each compared day to enter a same-sensor comparison
MIN_PAIRS_PERSON = 5             # a person needs this many pairs on each compared day
LEN_GROUPS = ["1", "2-3", "4-6", "7", "8+"]       # last wear day the session reached
LEN_EDGES = [0, 1, 3, 6, 7, 999]
MAIN_GROUPS = ["1", "2-3", "4-6", "7"]            # "8+" cannot happen on a G4 and is treated as an artefact
LOW_LIMIT = 70                   # mg/dL: the low line used for missed and false lows (same as accuracy_v2.py)
FLOOR_HOURS = (96, 168)          # "settled level" = pooled MARD over days 5-7 of 7-day sessions
SETTLE_TOL = [1.0, 0.5]          # points of MARD above the floor that still count as settled
CAL_BINS = [(0, 1), (1, 3), (3, 6), (6, 12), (12, 24)]   # hours since the last calibration
DAY1_BLOCKS = [(0, 6), (6, 12), (12, 18), (18, 24)]
STATS = {"analysis_set": "verified fingerstick pairs (meter log, not used for calibration, study window) in sensor sessions "
                         "confirmed by a start-up calibration; glued sessions (see 'sessions.method'); wear days 1-7",
         "seed": SEED, "bootstrap_resamples": N_BOOT,
         "ci": "95 % percentile CI from a bootstrap that resamples the 226 participants; one shared set of resamples, so differences are paired"}
T0 = time.time()


def log(*a):
    """Print a progress line with the elapsed seconds."""
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Chart styling (same palette as error_drivers.py / explore_raw_data.py)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = ["#86b6ef", "#2a78d6", "#104281"]
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
# Bootstrap helpers
# --------------------------------------------------------------------------
class Boot:
    """Participant bootstrap with ONE shared set of resamples.

    The participants are drawn with replacement N_BOOT times (multinomial weights, fixed seed), once.
    Every statistic here is a ratio of per-participant sums, so one resample is a weighted sum. Because
    every subset uses the same weights, a difference between two subsets (day 1 minus day 2, short minus
    long sessions) is a paired difference and gets its own CI. Same idea as error_drivers.boot_stats, but
    with the weights shared across calls.
    """

    def __init__(self, participants, seed=SEED, n_boot=N_BOOT):
        self.pts = pd.Index(np.sort(np.unique(np.asarray(participants))))
        n = len(self.pts)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(n, np.full(n, 1 / n), size=n_boot).astype(float)   # n_boot x participants

    def sums(self, pt, X):
        """Per-participant column sums of X (one row per pair). Returns participants x columns."""
        i = self.pts.get_indexer(np.asarray(pt))
        S = np.zeros((len(self.pts), X.shape[1]))
        np.add.at(S, i, X)
        return S

    def ratio(self, pt, num, den):
        """Point estimate and bootstrap draws of sum(num) / sum(den)."""
        S = self.sums(pt, np.column_stack([num, den]).astype(float))
        with np.errstate(invalid="ignore", divide="ignore"):
            point = S[:, 0].sum() / S[:, 1].sum() if S[:, 1].sum() > 0 else np.nan
            b = (self.W @ S[:, 0]) / (self.W @ S[:, 1])
        return float(point), b

    def wmedian(self, pt, v):
        """Median over units (sessions or people) with the participant weights: point estimate and draws."""
        v = np.asarray(v, dtype=float)
        i = self.pts.get_indexer(np.asarray(pt))
        order = np.argsort(v, kind="stable")
        vs = v[order]
        cw = np.cumsum(self.W[:, i[order]], axis=1)
        idx = (cw >= cw[:, -1:] / 2).argmax(axis=1)
        return float(np.median(v)), vs[idx]


def ci(b):
    """95 % percentile interval of bootstrap draws, rounded."""
    b = np.asarray(b, dtype=float)
    b = b[np.isfinite(b)]
    if len(b) == 0:
        return [None, None]
    return [round(float(np.percentile(b, 2.5)), 2), round(float(np.percentile(b, 97.5)), 2)]


def r2(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 2)


def metric_boot(df, metric):
    """(point, draws) for one metric of a pairs table: mard, bias_pct, bias_mgdl, sd_pct, low20, high20, missed_low, false_low."""
    pt = df.PtID.to_numpy()
    one = np.ones(len(df))
    rel = df.rel_err_pct.to_numpy(dtype=float)
    if metric == "mard":
        return BOOT.ratio(pt, np.abs(rel), one)
    if metric == "bias_pct":
        return BOOT.ratio(pt, rel, one)
    if metric == "bias_mgdl":
        return BOOT.ratio(pt, df.err.to_numpy(dtype=float), one)
    if metric == "sd_pct":                     # spread of the % error: sqrt(E[x^2] - E[x]^2)
        p1, b1 = BOOT.ratio(pt, rel, one)
        p2, b2 = BOOT.ratio(pt, rel ** 2, one)
        with np.errstate(invalid="ignore"):
            return float(np.sqrt(p2 - p1 ** 2)), np.sqrt(b2 - b1 ** 2)
    if metric == "low20":                      # share of pairs where the CGM reads more than 20 % below the meter
        return BOOT.ratio(pt, (rel < -20).astype(float) * 100, one)
    if metric == "high20":
        return BOOT.ratio(pt, (rel > 20).astype(float) * 100, one)
    if metric == "missed_low":                 # meter < 70 but CGM >= 70 (same rule as accuracy_v2.py), % of true lows
        tl = (df.ref < LOW_LIMIT).to_numpy()
        return BOOT.ratio(pt, (tl & (df.cgm >= LOW_LIMIT).to_numpy()).astype(float) * 100, tl.astype(float))
    if metric == "false_low":                  # meter >= 70 but CGM < 70, % of true not-lows
        nl = (df.ref >= LOW_LIMIT).to_numpy()
        return BOOT.ratio(pt, (nl & (df.cgm < LOW_LIMIT).to_numpy()).astype(float) * 100, nl.astype(float))
    raise ValueError(metric)


def est(df, metrics=("mard", "bias_pct", "bias_mgdl", "sd_pct")):
    """Point estimates and CIs for several metrics of a pairs subset, plus counts."""
    out = {"n": int(len(df)), "n_pt": int(df.PtID.nunique())}
    if "wear_key" in df:
        out["n_sessions"] = int(df.wear_key.nunique())
    if len(df) == 0:
        return out
    for m in metrics:
        p, b = metric_boot(df, m)
        out[m] = r2(p)
        out[m + "_ci"] = ci(b)
    return out


def diff(df_a, df_b, metric):
    """Paired bootstrap difference (A minus B) of one metric."""
    pa, ba = metric_boot(df_a, metric)
    pb, bb = metric_boot(df_b, metric)
    return {"points": r2(pa - pb), "ci": ci(ba - bb), "a": r2(pa), "b": r2(pb), "n_a": int(len(df_a)), "n_b": int(len(df_b))}


def unit_diff(df, unit_col, day_a, day_b, min_pairs):
    """Same-unit comparison: for each unit (session or person) with >= min_pairs pairs on both days,
    its mean ARD on day_a minus day_b. Median over units (participant-bootstrap CI), IQR, share worse on day_a."""
    a = df[df.wd == day_a].groupby(unit_col).agg(pt=("PtID", "first"), n_a=("ard", "size"), m_a=("ard", "mean"))
    b = df[df.wd == day_b].groupby(unit_col).agg(n_b=("ard", "size"), m_b=("ard", "mean"))
    u = a.join(b, how="inner")
    u = u[(u.n_a >= min_pairs) & (u.n_b >= min_pairs)]
    if len(u) == 0:
        return {"units": 0}
    d = (u.m_a - u.m_b).to_numpy(dtype=float)
    pt = u.pt.to_numpy()
    med, bmed = BOOT.wmedian(pt, d)
    sh, bsh = BOOT.ratio(pt, (d > 0).astype(float) * 100, np.ones(len(d)))
    return {"units": int(len(u)), "participants": int(u.pt.nunique()), "min_pairs_each_day": min_pairs,
            "median_points": r2(med), "median_ci": ci(bmed),
            "iqr_points": [r2(np.percentile(d, 25)), r2(np.percentile(d, 75))],
            "mean_points": r2(d.mean()), "share_worse_on_first_pct": r2(sh), "share_ci": ci(bsh)}


def settle_model(h, floor, extra, tau):
    """MARD(h) = floor + extra * exp(-h / tau): a settled level plus an extra error that fades with time constant tau (hours)."""
    return floor + extra * np.exp(-h / tau)


def fit_settle(h, m, n):
    """Weighted least-squares fit of settle_model to bin MARDs (weights = pairs per bin). Returns (floor, extra, tau)."""
    ok = np.isfinite(m) & (n > 0)
    try:
        p, _ = curve_fit(settle_model, h[ok], m[ok], p0=[12.0, 3.0, 24.0], sigma=1 / np.sqrt(n[ok]),
                         bounds=([0, 0, 1], [60, 60, 2000]), maxfev=20000)
        return p
    except Exception:
        return np.array([np.nan, np.nan, np.nan])


def settling_hour(curve, starts, floor, tol):
    """First bin start from which every later bin stays within tol points of the floor. None if never."""
    over = np.asarray(curve) - floor > tol
    for k in range(len(curve)):
        if not over[k:].any():
            return float(starts[k])
    return None


def clean(o):
    """Make numpy / pandas values JSON-safe."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


# --------------------------------------------------------------------------
# 1. Load (only through preprocess.py)
# --------------------------------------------------------------------------
log("loading cached tables")
pairs = pp.verified_pairs(ROOT, CACHE)
cgm = pp.load_cgm(ROOT, CACHE)
cal = pp.load_calibrations(ROOT, CACHE)
cal_pairs = pp.build_pairs(ROOT, CACHE)["calibration"]
BOOT = Boot(pairs.PtID.to_numpy())
log(f"{len(pairs):,} verified pairs, {len(BOOT.pts)} participants, {len(cgm):,} CGM readings")

# --------------------------------------------------------------------------
# 2. Sessions: raw fragments from the cache -> glued sensor sessions
# --------------------------------------------------------------------------
frag = cgm.groupby("session_id").agg(PtID=("PtID", "first"), t0=("t", "min"), t1=("t", "max"), n_readings=("t", "size"),
                                     confirmed=("session_confirmed_by_cal", "first"), in_window=("in_study_window", "max")).reset_index()
frag = frag.sort_values(["PtID", "t0"]).reset_index(drop=True)
frag["hours"] = (frag.t1 - frag.t0) / 3600
prev_t1 = frag.groupby("PtID").t1.shift(1)
frag["gap_before_h"] = (frag.t0 - prev_t1) / 3600
key = np.zeros(len(frag), dtype=np.int64)
k, cur_pt, cur_t0 = 0, None, None
for i, r in enumerate(frag.itertuples(index=False)):
    if r.PtID != cur_pt:
        cur_pt, cur_t0 = r.PtID, None
    # a confirmed fragment always starts a session; an unconfirmed one continues the current session unless that would run past 170 h
    if r.confirmed or cur_t0 is None or (r.t1 - cur_t0) / 3600 > MAX_SESSION_H:
        k += 1
        cur_t0 = r.t0
    key[i] = k
frag["wear_key"] = key
frag["glued"] = frag.groupby("wear_key").cumcount() > 0
ses = frag.groupby("wear_key").agg(PtID=("PtID", "first"), t0=("t0", "min"), t1=("t1", "max"), fragments=("session_id", "size"),
                                   confirmed=("confirmed", "first"), in_window=("in_window", "max"), n_readings=("n_readings", "sum")).reset_index()
ses["hours"] = (ses.t1 - ses.t0) / 3600
ses["max_wear_day"] = (ses.hours // 24 + 1).astype(int)
ses["len_group"] = pd.cut(ses.max_wear_day, LEN_EDGES, labels=LEN_GROUPS).astype(str)
ses = ses.sort_values(["PtID", "t0"]).reset_index(drop=True)
ses["gap_to_next_start_h"] = (ses.groupby("PtID").t0.shift(-1) - ses.t1) / 3600
del cgm

fw = frag[frag.in_window]
sw = ses[ses.in_window]
conf = sw[sw.confirmed]
unconf_frag = fw[~fw.confirmed]
raw_len = pd.cut((fw.hours // 24 + 1).astype(int), LEN_EDGES, labels=LEN_GROUPS).astype(str)


def session_row(g):
    """One row of the session description table."""
    d = {"sessions": int(len(g)), "share_of_sessions_pct": r2(len(g) / len(conf) * 100), "participants": int(g.PtID.nunique()),
         "median_hours": r2(g.hours.median()), "hours_iqr": [r2(g.hours.quantile(0.25)), r2(g.hours.quantile(0.75))],
         "fragments_per_session": r2(g.fragments.mean()), "share_with_a_glued_fragment_pct": r2((g.fragments > 1).mean() * 100),
         "next_session_starts_within_6h_pct": r2((g.gap_to_next_start_h <= 6).mean() * 100),
         "next_session_starts_within_24h_pct": r2((g.gap_to_next_start_h <= 24).mean() * 100),
         "median_gap_to_next_start_h": r2(g.gap_to_next_start_h.median())}
    return d


STATS["sessions"] = {
    "method": f"raw sessions = cache rule (gap >= {pp.SESSION_GAP_S // 60} min starts a new one). A fragment with no start-up calibration in the "
              f"{STARTUP_CAL_WINDOW_S // 60} min before its first reading is glued onto the session it follows (same sensor after a signal gap), "
              f"unless the glued session would exceed {MAX_SESSION_H} h. Wear day = floor(hours since the glued session's first reading / 24) + 1. "
              "Sessions whose first fragment is unconfirmed are excluded, as in error_drivers.py",
    "raw_fragments_touching_window": int(len(fw)), "raw_confirmed": int(fw.confirmed.sum()), "raw_unconfirmed": int((~fw.confirmed).sum()),
    "raw_unconfirmed_glued": int((unconf_frag.glued).sum()), "raw_unconfirmed_left_standalone": int((~unconf_frag.glued).sum()),
    "gap_before_unconfirmed_fragment_h": {"median": r2(unconf_frag.gap_before_h.median()), "share_under_6h_pct": r2((unconf_frag.gap_before_h < 6).mean() * 100),
                                          "share_over_24h_pct": r2((unconf_frag.gap_before_h > 24).mean() * 100)},
    "gap_before_confirmed_fragment_h": {"median": r2(fw[fw.confirmed].gap_before_h.median()), "q25": r2(fw[fw.confirmed].gap_before_h.quantile(0.25)),
                                        "q75": r2(fw[fw.confirmed].gap_before_h.quantile(0.75)), "min": r2(fw[fw.confirmed].gap_before_h.min())},
    "raw_sessions_by_last_wear_day": {g: int((raw_len == g).sum()) for g in LEN_GROUPS},
    "raw_confirmed_sessions_by_last_wear_day": {g: int(((raw_len == g) & fw.confirmed).sum()) for g in LEN_GROUPS},
    "glued_sessions_touching_window": int(len(sw)), "glued_confirmed": int(len(conf)), "glued_unconfirmed_excluded": int((~sw.confirmed).sum()),
    "participants": int(conf.PtID.nunique()), "sessions_per_participant_median": r2(conf.groupby("PtID").size().median()),
    "by_last_wear_day": {g: session_row(conf[conf.len_group == g]) for g in LEN_GROUPS},
    "ended_before_day_3": int((conf.max_wear_day <= 2).sum()), "ended_before_day_3_pct": r2((conf.max_wear_day <= 2).mean() * 100),
    "reached_day_7": int((conf.max_wear_day == 7).sum()), "reached_day_7_pct": r2((conf.max_wear_day == 7).mean() * 100),
    "beyond_day_7": int((conf.max_wear_day >= 8).sum()), "beyond_day_7_pct": r2((conf.max_wear_day >= 8).mean() * 100),
    "beyond_day_7_note": "a G4 session cannot run past 7 days (168 h from sensor start, about 166 h of readings); these are clock changes or wrong glueing and are excluded",
    "hours_histogram_7day_sessions": {f"{a}-{b}": int(conf[(conf.len_group == '7')].hours.between(a, b, inclusive="left").sum()) for a, b in
                                      [(144, 150), (150, 156), (156, 160), (160, 162), (162, 164), (164, 166), (166, 168), (168, 170)]},
    "why_no_tail_past_7_days": "every start (new sensor OR restart of the same sensor) forces a 2-h warm-up and two calibrations, so a restart begins a "
                               "new session; the data cannot tell a restart from a replacement",
}
log(f"sessions: {len(fw):,} raw fragments -> {len(sw):,} glued sessions ({len(conf):,} confirmed); reached day 7: {STATS['sessions']['reached_day_7_pct']} %, "
    f"ended before day 3: {STATS['sessions']['ended_before_day_3_pct']} %, beyond day 7: {STATS['sessions']['beyond_day_7']}")

# --------------------------------------------------------------------------
# 3. Attach sessions to the pairs; recompute wear day from the glued session start
# --------------------------------------------------------------------------
P = pairs.merge(frag[["session_id", "wear_key"]], on="session_id", how="left")
P = P.merge(ses[["wear_key", "t0", "hours", "max_wear_day", "len_group", "confirmed"]].rename(columns={"t0": "s_t0", "hours": "s_hours", "confirmed": "s_confirmed"}),
            on="wear_key", how="left")
P["hrs"] = (P.t_cgm - P.s_t0) / 3600
P["wd"] = (P.hrs // 24 + 1).astype(int)
P["ard"] = P.abs_rel_err_pct.astype(float)
first_frag = P.session_confirmed_by_cal.to_numpy()
agree = float((P.loc[first_frag, "wd"] == P.loc[first_frag, "wear_day"]).mean())
n_unconf = int((~P.s_confirmed).sum())
n_art = int((P.s_confirmed & (P.len_group == "8+")).sum())
n_wd8 = int((P.s_confirmed & (P.len_group != "8+") & (P.wd > 7)).sum())
P = P[P.s_confirmed & (P.len_group != "8+") & P.wd.between(1, 7)].reset_index(drop=True)
P["is_7day"] = P.len_group == "7"
S7 = P[P.is_7day].reset_index(drop=True)
STATS["pairs"] = {"verified_pairs": int(len(pairs)), "excluded_unconfirmed_session": n_unconf, "excluded_session_beyond_day_7": n_art,
                  "excluded_wear_day_over_7": n_wd8, "analysis_pairs": int(len(P)), "participants": int(P.PtID.nunique()), "sessions": int(P.wear_key.nunique()),
                  "pairs_in_7day_sessions": int(len(S7)), "sessions_7day_with_pairs": int(S7.wear_key.nunique()),
                  "recomputed_wear_day_equals_cache_on_confirmed_fragments": round(agree, 4),
                  "pairs_on_glued_fragments": int((~P.session_confirmed_by_cal).sum()),
                  "pairs_by_wear_day": {str(d): int((P.wd == d).sum()) for d in range(1, 8)},
                  "pairs_per_session_per_day_7day_sessions": {str(d): r2((S7.wd == d).sum() / S7.wear_key.nunique()) for d in range(1, 8)},
                  "overall": est(P)}
log(f"analysis pairs: {len(P):,} ({len(S7):,} in 7-day sessions); recomputed wear day matches the cache on {agree * 100:.1f} % of confirmed fragments")

# --------------------------------------------------------------------------
# 4. Selection test: day-1 error by how long the session lasted
# --------------------------------------------------------------------------
d1 = P[P.wd == 1]
d7 = S7[S7.wd == 7]
d1_7 = S7[S7.wd == 1]
by_len = {g: est(d1[d1.len_group == g]) for g in MAIN_GROUPS}
for g in MAIN_GROUPS:
    by_len[g]["share_of_day1_pairs_pct"] = r2((d1.len_group == g).mean() * 100)
    by_len[g]["pairs_per_session"] = r2(len(d1[d1.len_group == g]) / max(d1[d1.len_group == g].wear_key.nunique(), 1))
# decomposition of the day-1 excess over the day-7 level
m1_all, b1_all = metric_boot(d1, "mard")
m1_7, b1_7 = metric_boot(d1_7, "mard")
m7, b7 = metric_boot(d7, "mard")
excess, b_exc = m1_all - m7, b1_all - b7
sel, b_sel = m1_all - m1_7, b1_all - b1_7
sett, b_set = m1_7 - m7, b1_7 - b7
with np.errstate(invalid="ignore", divide="ignore"):
    STATS["selection"] = {
        "question": "do sessions that ended early have worse day-1 error than sessions that reached day 7?",
        "day1_by_session_length": by_len,
        "day1_short_vs_7day": {g: diff(d1[d1.len_group == g], d1_7, "mard") for g in ["1", "2-3", "4-6"]},
        "day1_first_12h_by_session_length": {g: est(d1[(d1.len_group == g) & (d1.hrs < 12)], ("mard", "bias_pct")) for g in MAIN_GROUPS},
        "day1_first_12h_short_vs_7day": {g: diff(d1[(d1.len_group == g) & (d1.hrs < 12)], d1_7[d1_7.hrs < 12], "mard") for g in ["1", "2-3", "4-6"]},
        "decomposition": {
            "day1_mard_all_sessions": r2(m1_all), "day1_mard_all_ci": ci(b1_all),
            "day1_mard_7day_sessions": r2(m1_7), "day1_mard_7day_ci": ci(b1_7),
            "day7_mard": r2(m7), "day7_mard_ci": ci(b7),
            "excess_day1_over_day7_points": r2(excess), "excess_ci": ci(b_exc),
            "selection_part_points": r2(sel), "selection_part_ci": ci(b_sel), "selection_share_pct": r2(sel / excess * 100), "selection_share_ci": ci(b_sel / b_exc * 100),
            "settling_part_points": r2(sett), "settling_part_ci": ci(b_set), "settling_share_pct": r2(sett / excess * 100), "settling_share_ci": ci(b_set / b_exc * 100),
            "how": "excess = day-1 MARD (all sessions) minus day-7 MARD; selection part = day-1 MARD (all) minus day-1 MARD (7-day sessions only); "
                   "settling part = day-1 MARD (7-day sessions) minus day-7 MARD"},
        "day1_vs_day7_gap_7day_sessions_only": diff(d1_7, d7, "mard"),
        "day1_vs_day7_gap_all_sessions": {"points": r2(excess), "ci": ci(b_exc)},
    }
# within person: the same person's day-1 error on sessions that ended early vs on their sessions that reached day 7


def within_person_day1(mask_a, min_pairs):
    """Per person: mean day-1 ARD on sessions in mask_a minus mean day-1 ARD on 7-day sessions (>= min_pairs each)."""
    a = d1[mask_a].groupby("PtID").ard.agg(["size", "mean"]).rename(columns={"size": "n_a", "mean": "m_a"})
    b = d1[d1.is_7day].groupby("PtID").ard.agg(["size", "mean"]).rename(columns={"size": "n_b", "mean": "m_b"})
    u = a.join(b, how="inner")
    u = u[(u.n_a >= min_pairs) & (u.n_b >= min_pairs)]
    dd = (u.m_a - u.m_b).to_numpy(dtype=float)
    med, bmed = BOOT.wmedian(u.index.to_numpy(), dd)
    sh, bsh = BOOT.ratio(u.index.to_numpy(), (dd > 0).astype(float) * 100, np.ones(len(dd)))
    return {"participants": int(len(u)), "min_pairs_each": min_pairs, "median_points": r2(med), "median_ci": ci(bmed),
            "mean_points": r2(dd.mean()), "iqr_points": [r2(np.percentile(dd, 25)), r2(np.percentile(dd, 75))],
            "share_worse_on_short_pct": r2(sh), "share_ci": ci(bsh)}


STATS["selection"]["within_person_short_minus_7day_day1_mard"] = within_person_day1(~d1.is_7day, MIN_PAIRS_PERSON)
STATS["selection"]["within_person_ended_day1_minus_7day_day1_mard"] = within_person_day1(d1.len_group == "1", MIN_PAIRS_SESSION)
dec = STATS["selection"]["decomposition"]
log("selection: day-1 MARD by session length " + ", ".join(f"{g}: {by_len[g]['mard']}" for g in MAIN_GROUPS) +
    f" | excess {dec['excess_day1_over_day7_points']} = selection {dec['selection_part_points']} ({dec['selection_share_pct']} %) + settling {dec['settling_part_points']}")

# --------------------------------------------------------------------------
# 5. Settling test: the same 7-day sensors by hours since start and by wear day
# --------------------------------------------------------------------------
def curve(df, width):
    """MARD, bias and counts per time bin of `width` hours over 0-168 h, with CIs and the bootstrap draws of MARD."""
    starts = np.arange(0, 168, width)
    rows, draws = [], []
    for s in starts:
        sub = df[(df.hrs >= s) & (df.hrs < s + width)]
        p, b = metric_boot(sub, "mard") if len(sub) else (np.nan, np.full(N_BOOT, np.nan))
        pb, _ = metric_boot(sub, "bias_pct") if len(sub) else (np.nan, None)
        rows.append({"hours": f"{s}-{s + width}", "start_h": int(s), "n": int(len(sub)), "mard": r2(p), "mard_ci": ci(b), "bias_pct": r2(pb)})
        draws.append(b)
    return rows, np.column_stack(draws), starts


c6, D6, starts6 = curve(S7, 6)
c12, D12, starts12 = curve(S7, 12)
by_day = {str(d): est(S7[S7.wd == d]) for d in range(1, 8)}
floor_df = S7[(S7.hrs >= FLOOR_HOURS[0]) & (S7.hrs < FLOOR_HOURS[1])]
floor_p, floor_b = metric_boot(floor_df, "mard")
excess_by_day = {}
for d in range(1, 8):
    p, b = metric_boot(S7[S7.wd == d], "mard")
    excess_by_day[str(d)] = {"points": r2(p - floor_p), "ci": ci(b - floor_b)}
# settling hour by rule (point curve and bootstrap curves)
m6 = np.array([r["mard"] if r["mard"] is not None else np.nan for r in c6], dtype=float)
m12 = np.array([r["mard"] if r["mard"] is not None else np.nan for r in c12], dtype=float)
settle_rule = {}
for tol in SETTLE_TOL:
    for lab, m, D, st in [("6h_bins", m6, D6, starts6), ("12h_bins", m12, D12, starts12)]:
        pt_hour = settling_hour(m, st, floor_p, tol)
        bh = [settling_hour(D[i], st, floor_b[i], tol) for i in range(N_BOOT)]
        bh = np.array([np.nan if h is None else h for h in bh], dtype=float)
        settle_rule[f"tol_{tol}_{lab}"] = {"settling_hour": pt_hour, "ci": ci(bh), "share_of_draws_never_settled_pct": r2(np.isnan(bh).mean() * 100)}
# settling fit: floor + extra * exp(-h / tau) on the 6-h bins
n6 = np.array([r["n"] for r in c6], dtype=float)
h6 = starts6 + 3.0
fit = fit_settle(h6, m6, n6)
fits = np.array([fit_settle(h6, D6[i], n6) for i in range(N_BOOT)])
with np.errstate(invalid="ignore", divide="ignore"):
    half_life, b_half = fit[2] * np.log(2), fits[:, 2] * np.log(2)
    t_half_point = fit[2] * np.log(fit[1] / 0.5)                      # hour when the extra error falls below 0.5 point
    b_t_half_point = fits[:, 2] * np.log(fits[:, 1] / 0.5)
    extra_at = {f"{h} h": r2(fit[1] * np.exp(-h / fit[2])) for h in [0, 12, 24, 48, 72, 96]}
STATS["settling"] = {
    "question": "do the same sensors (sessions that reached day 7) improve from day 1 to day 2 and then flatten?",
    "set": "pairs in 7-day sessions (glued), wear days 1-7",
    "by_wear_day": by_day,
    "by_6h_bin": c6, "by_12h_bin": c12,
    "floor": {"definition": f"pooled MARD over hours {FLOOR_HOURS[0]}-{FLOOR_HOURS[1]} (days 5-7)", "mard": r2(floor_p), "mard_ci": ci(floor_b), "n": int(len(floor_df))},
    "excess_over_floor_by_wear_day": excess_by_day,
    "drop_day1_to_day2": diff(S7[S7.wd == 1], S7[S7.wd == 2], "mard"),
    "drop_day2_to_day3": diff(S7[S7.wd == 2], S7[S7.wd == 3], "mard"),
    "drop_day3_to_day4": diff(S7[S7.wd == 3], S7[S7.wd == 4], "mard"),
    "drop_day4_to_day5": diff(S7[S7.wd == 4], S7[S7.wd == 5], "mard"),
    "drop_day1_to_day7": diff(S7[S7.wd == 1], S7[S7.wd == 7], "mard"),
    "drop_first12h_to_second12h": diff(S7[S7.hrs < 12], S7[(S7.hrs >= 12) & (S7.hrs < 24)], "mard"),
    "settling_hour_by_rule": {"rule": "first bin start from which every later bin stays within tol points of the floor", **settle_rule},
    "settling_fit": {"model": "MARD(h) = floor + extra * exp(-h / tau), weighted by pairs per 6-h bin",
                     "floor": r2(fit[0]), "floor_ci": ci(fits[:, 0]), "extra_at_start": r2(fit[1]), "extra_ci": ci(fits[:, 1]),
                     "tau_h": r2(fit[2]), "tau_ci": ci(fits[:, 2]), "half_life_h": r2(half_life), "half_life_ci": ci(b_half),
                     "hour_extra_below_0.5_point": r2(t_half_point), "hour_extra_below_0.5_point_ci": ci(b_t_half_point),
                     "extra_error_at": extra_at},
    "same_sensor_day1_minus_day2": unit_diff(S7, "wear_key", 1, 2, MIN_PAIRS_SESSION),
    "same_sensor_day1_minus_day7": unit_diff(S7, "wear_key", 1, 7, MIN_PAIRS_SESSION),
    "same_sensor_day2_minus_day7": unit_diff(S7, "wear_key", 2, 7, MIN_PAIRS_SESSION),
    "within_person_day1_minus_day7": unit_diff(S7, "PtID", 1, 7, MIN_PAIRS_PERSON),
    "within_person_day1_minus_day2": unit_diff(S7, "PtID", 1, 2, MIN_PAIRS_PERSON),
}
log("settling: 7-day sessions MARD by day " + ", ".join(f"d{d} {by_day[str(d)]['mard']}" for d in range(1, 8)) +
    f" | floor {r2(floor_p)} | fit tau {r2(fit[2])} h, extra {r2(fit[1])} | same-sensor d1-d2 median {STATS['settling']['same_sensor_day1_minus_day2']['median_points']}")

# --------------------------------------------------------------------------
# 6. Direction: biased or just noisier?
# --------------------------------------------------------------------------
STATS["direction"] = {
    "set": "7-day sessions",
    "by_wear_day": {str(d): est(S7[S7.wd == d], ("mard", "bias_pct", "bias_mgdl", "sd_pct", "low20", "high20")) for d in range(1, 8)},
    "day1_minus_day7": {m: diff(S7[S7.wd == 1], S7[S7.wd == 7], m) for m in ["bias_pct", "sd_pct", "low20", "high20"]},
    "all_sessions_by_wear_day": {str(d): est(P[P.wd == d], ("mard", "bias_pct", "sd_pct", "low20", "high20")) for d in range(1, 8)},
    "note": "low20 / high20 = share of pairs where the CGM reads more than 20 % below / above the meter; sd_pct = spread (standard deviation) of the % error",
}
dr = STATS["direction"]["by_wear_day"]
log("direction (7-day sessions): " + ", ".join(f"d{d} bias {dr[str(d)]['bias_pct']:+.1f} sd {dr[str(d)]['sd_pct']:.1f}" for d in [1, 2, 7]))

# --------------------------------------------------------------------------
# 7. Calibration check
# --------------------------------------------------------------------------
calv = cal[~cal.value_missing & ~cal.value_out_of_range][["PtID", "t", "value"]].rename(columns={"t": "t_cal"}).sort_values("t_cal").reset_index(drop=True)
S7c = pd.merge_asof(S7.sort_values("t_cgm"), calv[["PtID", "t_cal"]], left_on="t_cgm", right_on="t_cal", by="PtID", direction="backward")
S7c["h_cal"] = (S7c.t_cgm - S7c.t_cal) / 3600
S7c["day1"] = S7c.wd == 1


def cal_bin(df, a, b):
    return df[(df.h_cal >= a) & (df.h_cal < b)]


since_cal = {}
for a, b in CAL_BINS:
    lab = f"{a}-{b} h"
    since_cal[lab] = {"day1": est(cal_bin(S7c[S7c.day1], a, b), ("mard", "bias_pct")), "days2to7": est(cal_bin(S7c[~S7c.day1], a, b), ("mard", "bias_pct")),
                      "day1_minus_days2to7": diff(cal_bin(S7c[S7c.day1], a, b), cal_bin(S7c[~S7c.day1], a, b), "mard")}
# calibrations per session-day (7-day sessions): a calibration belongs to the session if it falls between 30 min before the first reading and the last reading
s7_tab = ses[ses.confirmed & (ses.len_group == "7") & ses.in_window][["PtID", "wear_key", "t0", "t1"]].copy()
s7_tab["t_open"] = s7_tab.t0 - STARTUP_CAL_WINDOW_S          # the session "opens" 30 min before its first reading, so the start-up calibrations land in it
s7_tab = s7_tab.sort_values("t_open")
cs = pd.merge_asof(calv, s7_tab, left_on="t_cal", right_on="t_open", by="PtID", direction="backward")
cs = cs[cs.t1.notna() & (cs.t_cal <= cs.t1)].copy()
cs["wd"] = ((cs.t_cal - cs.t0).clip(lower=0) // 86400 + 1).astype(int)
n_s7 = s7_tab.wear_key.nunique()
cals_per_day = {str(d): r2((cs.wd == d).sum() / n_s7) for d in range(1, 8)}
# sensor error at the moment of calibration (calibration value vs the CGM reading just before it), by wear day
CP = cal_pairs[cal_pairs.in_study_window].merge(frag[["session_id", "wear_key"]], on="session_id", how="left")
CP = CP.merge(ses[["wear_key", "t0", "len_group", "confirmed"]].rename(columns={"t0": "s_t0", "confirmed": "s_confirmed"}), on="wear_key", how="left")
CP["hrs"] = (CP.t_cgm - CP.s_t0) / 3600
CP["wd"] = (CP.hrs // 24 + 1).astype(int)
CP["ard"] = CP.abs_rel_err_pct.astype(float)
CP7 = CP[CP.s_confirmed & (CP.len_group == "7") & CP.wd.between(1, 7)]
STATS["calibration"] = {
    "device_rule": "G4: two calibrations after the 2-h warm-up, then one every 12 h; the receiver shows no readings until the start-up calibrations are entered",
    "day1_by_6h_block_7day_sessions": {f"{a}-{b} h": est(S7[(S7.hrs >= a) & (S7.hrs < b)], ("mard", "bias_pct")) for a, b in DAY1_BLOCKS},
    "first12h_minus_second12h": STATS["settling"]["drop_first12h_to_second12h"],
    "by_hours_since_last_calibration_7day_sessions": since_cal,
    "pairs_with_a_calibration_before": int(S7c.t_cal.notna().sum()), "pairs_without": int(S7c.t_cal.isna().sum()),
    "calibrations_per_session_per_day_7day_sessions": cals_per_day,
    "calibrations_counted": int(len(cs)), "sessions_counted": int(n_s7),
    "error_at_calibration_time_by_wear_day_7day_sessions": {
        "what": "calibration pairs: the fingerstick typed into the receiver vs the CGM reading up to 10 min BEFORE it, i.e. the sensor's error just before it is corrected",
        **{str(d): est(CP7[CP7.wd == d], ("mard", "bias_pct")) for d in range(1, 8)},
        "day1_minus_day7": diff(CP7[CP7.wd == 1], CP7[CP7.wd == 7], "mard")},
}
cb = STATS["calibration"]["by_hours_since_last_calibration_7day_sessions"]
log("calibration: MARD by hours since last calibration, day 1 vs days 2-7: " + ", ".join(f"{k} {v['day1']['mard']} vs {v['days2to7']['mard']}" for k, v in cb.items()))
log("calibration pairs (error before correction) by wear day: " + ", ".join(f"d{d} {STATS['calibration']['error_at_calibration_time_by_wear_day_7day_sessions'][str(d)]['mard']}" for d in range(1, 8)))

# --------------------------------------------------------------------------
# 8. Low range (< 70 mg/dL by the average of CGM and meter)
# --------------------------------------------------------------------------
P["wd_grp"] = np.select([P.wd == 1, P.wd == 7], ["1", "7"], default="2-6")
low = P[P.avg < LOW_LIMIT]
low7 = low[low.is_7day]
lows = low[~low.is_7day]
STATS["low_range"] = {
    "set": f"pairs with average of CGM and meter < {LOW_LIMIT} mg/dL",
    "7day_sessions_by_wear_day_group": {g: est(low7[low7.wd_grp == g], ("mard", "bias_pct", "bias_mgdl")) for g in ["1", "2-6", "7"]},
    "short_sessions_by_wear_day_group": {g: est(lows[lows.wd_grp == g], ("mard", "bias_pct", "bias_mgdl")) for g in ["1", "2-6"]},
    "all_sessions_by_wear_day_group": {g: est(low[low.wd_grp == g], ("mard", "bias_pct", "bias_mgdl")) for g in ["1", "2-6", "7"]},
    "day1_bias_7day_minus_days2to6": diff(low7[low7.wd_grp == "1"], low7[low7.wd_grp == "2-6"], "bias_pct"),
    "day1_bias_short_minus_7day": diff(lows[lows.wd_grp == "1"], low7[low7.wd_grp == "1"], "bias_pct"),
    "day1_low_by_6h_block_7day_sessions": {f"{a}-{b} h": est(low7[(low7.hrs >= a) & (low7.hrs < b)], ("mard", "bias_pct")) for a, b in DAY1_BLOCKS},
    "missed_low_by_wear_day": {"definition": f"meter < {LOW_LIMIT} and CGM >= {LOW_LIMIT}, as % of meter-low pairs (accuracy_v2.py rule)",
                               "7day_sessions": {str(d): est(S7[S7.wd == d], ("missed_low", "false_low")) for d in range(1, 8)},
                               "all_sessions": {str(d): est(P[P.wd == d], ("missed_low", "false_low")) for d in range(1, 8)},
                               "7day_day1_minus_day7": {m: diff(S7[S7.wd == 1], S7[S7.wd == 7], m) for m in ["missed_low", "false_low"]}},
    "meter_low_pairs_by_wear_day_7day": {str(d): int(((S7.wd == d) & (S7.ref < LOW_LIMIT)).sum()) for d in range(1, 8)},
}
lr = STATS["low_range"]
log(f"low range (7-day sessions): bias day 1 {lr['7day_sessions_by_wear_day_group']['1']['bias_pct']} %, days 2-6 {lr['7day_sessions_by_wear_day_group']['2-6']['bias_pct']} %, "
    f"day 7 {lr['7day_sessions_by_wear_day_group']['7']['bias_pct']} %; missed lows d1 {lr['missed_low_by_wear_day']['7day_sessions']['1']['missed_low']} % vs d7 {lr['missed_low_by_wear_day']['7day_sessions']['7']['missed_low']} %")

# --------------------------------------------------------------------------
# 9. Sensitivity: raw (unglued) sessions, exactly the error_drivers.py filter
# --------------------------------------------------------------------------
R = pairs[pairs.session_confirmed_by_cal & pairs.wear_day.between(1, 7)].copy()
R["len_group"] = pd.cut((R.session_days // 1 + 1).astype(int), LEN_EDGES, labels=LEN_GROUPS).astype(str)
R["wear_key"] = R.session_id
R = R[R.len_group != "8+"]
r1, r1_7, r7 = R[R.wear_day == 1], R[(R.wear_day == 1) & (R.len_group == "7")], R[(R.wear_day == 7) & (R.len_group == "7")]
rm1, rb1 = metric_boot(r1, "mard")
rm17, rb17 = metric_boot(r1_7, "mard")
rm7, rb7 = metric_boot(r7, "mard")
with np.errstate(invalid="ignore", divide="ignore"):
    STATS["sensitivity_raw_sessions"] = {
        "set": "raw cache sessions confirmed by a start-up calibration, cache wear_day 1-7 (the error_drivers.py filter); session length = cache session_days",
        "pairs": int(len(R)), "sessions_by_length": {g: int(R[R.len_group == g].session_id.nunique()) for g in MAIN_GROUPS},
        "day1_mard_by_session_length": {g: est(r1[r1.len_group == g], ("mard", "bias_pct")) for g in MAIN_GROUPS},
        "by_wear_day_7day_sessions": {str(d): est(R[(R.wear_day == d) & (R.len_group == "7")], ("mard", "bias_pct")) for d in range(1, 8)},
        "decomposition": {"day1_mard_all": r2(rm1), "day1_mard_7day": r2(rm17), "day7_mard": r2(rm7),
                          "excess_points": r2(rm1 - rm7), "selection_part_points": r2(rm1 - rm17), "selection_share_pct": r2((rm1 - rm17) / (rm1 - rm7) * 100),
                          "selection_share_ci": ci((rb1 - rb17) / (rb1 - rb7) * 100), "settling_part_points": r2(rm17 - rm7)},
    }
log(f"sensitivity (raw sessions): selection share {STATS['sensitivity_raw_sessions']['decomposition']['selection_share_pct']} %")

# --------------------------------------------------------------------------
# Figure 33: selection (left) vs settling (right)
# --------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.5), gridspec_kw={"width_ratios": [2, 3]})
ax = axes[0]
x = np.arange(len(MAIN_GROUPS))
vals = [by_len[g]["mard"] for g in MAIN_GROUPS]
err = np.array([[by_len[g]["mard"] - by_len[g]["mard_ci"][0], by_len[g]["mard_ci"][1] - by_len[g]["mard"]] for g in MAIN_GROUPS]).T
cols = [RAMP[2], RAMP[1], RAMP[1], RAMP[0]]
ax.bar(x, vals, 0.62, color=cols, yerr=err, error_kw=ERR_KW)
for xi, g in zip(x, MAIN_GROUPS):
    ax.text(xi, by_len[g]["mard_ci"][1] + 0.25, f"{by_len[g]['mard']:.1f}", ha="center", va="bottom", fontsize=9, color=INK2)
ax.axhline(m7, color=INK2, lw=1, ls="--", label=f"day-7 level {m7:.1f}")
ax.legend(loc="upper right", handlelength=1.6)
ax.set_xticks(x)
ax.set_xticklabels([f"ended\nday 1" if g == "1" else (f"reached\nday 7" if g == "7" else f"ended\ndays {g}") for g in MAIN_GROUPS])
for xi, g in zip(x, MAIN_GROUPS):
    ax.annotate(f"{by_len[g]['share_of_day1_pairs_pct']:.0f} % of\nday-1 pairs", xy=(xi, 0), xycoords=ax.get_xaxis_transform(), xytext=(0, -28), textcoords="offset points", ha="center", va="top", fontsize=8, color=MUTED)
ax.set_ylabel("MARD on wear day 1 (%)")
ax.set_ylim(0, max(by_len[g]["mard_ci"][1] for g in MAIN_GROUPS) + 4.0)
ax.set_title("Day-1 error by how long the sensor lasted")
ax = axes[1]
xc = starts6 + 3
lo = np.array([r["mard_ci"][0] for r in c6], dtype=float)
hi = np.array([r["mard_ci"][1] for r in c6], dtype=float)
ax.fill_between(xc, lo, hi, color=C_BLUE, alpha=0.18, linewidth=0, label="95 % CI")
ax.plot(xc, m6, marker="o", ms=3.2, color=C_BLUE, label="MARD, 6-h bins")
hh = np.linspace(0, 168, 200)
ax.plot(hh, settle_model(hh, *fit), color=C_ORANGE, lw=1.3, ls="--", label=f"fit: time constant {fit[2]:.0f} h")
ax.axhline(floor_p, color=INK2, lw=1, ls=":")
ax.text(1, floor_p - 0.25, f"days 5-7 level {floor_p:.1f}", ha="left", va="top", fontsize=8.5, color=INK2)
for d in range(1, 8):
    ax.axvline(24 * d, color=GRID, lw=0.8)
ax.set_xticks(np.arange(0, 169, 24))
ax.set_xticklabels([f"{h}" for h in range(0, 169, 24)])
ymin, ymax = np.floor(np.nanmin(lo)) - 0.6, np.nanmax(hi) + 2.8          # headroom for the legend above the curve
ax.set_ylim(ymin, ymax)
for d in range(1, 8):
    ax.text(24 * d - 12, ymin + 0.1, f"day {d}", ha="center", va="bottom", fontsize=8, color=MUTED)
ax.set_xlabel("hours since the sensor's first reading")
ax.set_ylabel("MARD (%)")
dd12 = STATS["settling"]["drop_day1_to_day2"]
ax.set_title(f"Same sensors (7-day sessions): day 1 to day 2 drops {abs(dd12['points']):.1f} points")
ax.legend(loc="upper right", ncol=1, handlelength=1.6)
fig.suptitle(f"The day-1 excess is mostly the sensor settling in, not bad sensors being discarded "
             f"({dec['settling_share_pct']:.0f} % settling, {dec['selection_share_pct']:.0f} % selection)", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
fig.text(0.01, 0.01, f"Left: wear-day-1 pairs of {len(d1):,} verified fingersticks, grouped by the last wear day the sensor reached (bars: mean, lines: 95 % CI). "
         f"Right: {len(S7):,} pairs in {S7.wear_key.nunique():,} sessions that reached day 7.", ha="left", va="bottom", fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.06, 1, 0.93))
save(fig, "33_wear_day_selection_vs_settling.png")

# --------------------------------------------------------------------------
# Figure 34: calibration timing
# --------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), gridspec_kw={"width_ratios": [3, 2]})
ax = axes[0]
labs = list(since_cal.keys())
x = np.arange(len(labs))
wdt = 0.38
for off, key, col, lab in [(-wdt / 2, "day1", RAMP[2], "wear day 1"), (wdt / 2, "days2to7", RAMP[0], "wear days 2-7")]:
    v = [since_cal[k][key]["mard"] for k in labs]
    e = np.array([[since_cal[k][key]["mard"] - since_cal[k][key]["mard_ci"][0], since_cal[k][key]["mard_ci"][1] - since_cal[k][key]["mard"]] for k in labs]).T
    ax.bar(x + off, v, wdt, color=col, label=lab, yerr=e, error_kw=ERR_KW)
    for xi, k in zip(x + off, labs):
        ax.text(xi, since_cal[k][key]["mard_ci"][1] + 0.2, f"{since_cal[k][key]['mard']:.1f}", ha="center", va="bottom", fontsize=8, color=INK2)
ax.set_xticks(x)
ax.set_xticklabels(labs)
ax.set_xlabel("hours since the last calibration")
ax.set_ylabel("MARD (%)")
ax.set_ylim(0, max(since_cal[k][key]["mard_ci"][1] for k in labs for key in ["day1", "days2to7"]) + 2.5)
ax.set_title("Day 1 is worse at every time since the last calibration")
ax.legend(loc="upper center", ncol=2)
ax = axes[1]
days = list(range(1, 8))
cpd = STATS["calibration"]["error_at_calibration_time_by_wear_day_7day_sessions"]
v = [cpd[str(d)]["mard"] for d in days]
lo = [cpd[str(d)]["mard_ci"][0] for d in days]
hi = [cpd[str(d)]["mard_ci"][1] for d in days]
ax.fill_between(days, lo, hi, color=C_ORANGE, alpha=0.18, linewidth=0)
ax.plot(days, v, marker="o", ms=4, color=C_ORANGE)
for d, vi, h in zip(days, v, hi):
    ax.text(d, h + 0.25, f"{vi:.1f}", ha="center", fontsize=8.5, color=INK2)
ax.set_xticks(days)
ax.set_xlabel("wear day")
ax.set_ylabel("MARD at calibration time (%)")
ax.set_ylim(0, max(hi) + 2.5)
ax.set_title("Sensor error just before each calibration")
fig.suptitle("Figure 34. Calibration timing does not explain day 1 (7-day sessions; bars and bands: 95 % CI)", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
fig.text(0.01, 0.01, "Left: verified fingerstick pairs grouped by the time since the last calibration entered into the receiver. "
         "Right: calibration fingersticks vs the CGM reading up to 10 min before them, i.e. the error the calibration then corrects.",
         ha="left", va="bottom", fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.07, 1, 0.93))
save(fig, "34_wear_day_calibration.png")

# --------------------------------------------------------------------------
# Save
# --------------------------------------------------------------------------
STATS["runtime_s"] = round(time.time() - T0, 1)
with open(os.path.join(OUT, "wear_day_stats.json"), "w", encoding="utf-8") as f:
    json.dump(clean(STATS), f, indent=1)
log("wrote", os.path.join(OUT, "wear_day_stats.json"), f"runtime {STATS['runtime_s']} s")
