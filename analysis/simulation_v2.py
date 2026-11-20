"""
Fault simulation, version 2, for BMEN 600 Group 24.

Question: how much does a CGM sensor error change real treatment decisions?

What changed from version 1 (analysis/bias_simulation.py)
  Version 1 counted threshold crossings at every 5-minute reading under a constant
  low bias. That measures how much time people spend near 70 or 200 mg/dL, not the
  sensor. Version 2 counts DECISIONS at decision points and adds more fault types.

Decision points
  1. Correction-dose decisions: every pump bolus-calculator ("wizard") record in the
     study window where the patient typed a glucose value. The record carries the
     patient's own insulin sensitivity factor (ISF), target and insulin on board (IOB).
     "True" glucose = the CGM reading nearest within 5 min. The faulted sensor would
     have shown the faulted value of that reading. Dose rule (validated against the
     pump's own recommendation): dose = max(0, (G - target) / ISF - IOB) when G is
     above the pump's "correct above" level, else 0.
  2. Low-glucose episodes: >= 15 min (3 readings) below 70 (and below 54) on the true
     trace vs the faulted trace. Outcomes: false alerts, missed alerts, delay.
  3. High-glucose episodes: the same at 180 and at 200 mg/dL.

Fault families (applied per participant to the in-window CGM trace on a 5-min grid)
  bias (-40..+40 % in 2 % steps; the lookup table; wider grids via --lookup-*), white and AR(1) noise, drift over
  the sensor's wear, dropouts, lag, and a mixed "recall-like" fault. Noise, dropouts and
  the mixed fault use 10 Monte Carlo draws per participant (fixed seed).

Usage (from the repo root; Python 3.11)
  python analysis/simulation_v2.py "Uncommitted Data/Raw Data Dump" analysis
  Argument 1 = data folder, argument 2 = output folder (these are the defaults).
  Argument 3 (optional) = cache folder, default analysis/cache (analysis/preprocess.py).
  Set the environment variable SIM_V2_QUICK=1 for a 20-participant, 2-draw test run.

  Extended lookup (added 2026-10-30; the defaults above are unchanged). Options may stand anywhere:
    --lookup-min -90 --lookup-max 90 --lookup-step 2   bias grid in percent (default -40, 40, 2)
    --lookup-only                                      write only the lookup CSV: no other fault
                                                       families, no figures, no stats JSON
    --lookup-out PATH                                  where to write the lookup CSV
                                                       (default <output folder>/simulation_v2_lookup.csv)
  python analysis/simulation_v2.py "Uncommitted Data/Raw Data Dump" analysis --lookup-min -90 --lookup-max 90 \
      --lookup-step 2 --lookup-only --lookup-out analysis/simulation_v2_lookup_extended.csv

Outputs (all under the output folder)
  simulation_v2_stats.json          every number quoted in SIMULATION_V2.md
  simulation_v2_lookup.csv          bias level -> every outcome, median / IQR / mean across participants
  simulation_v2_participants.csv    one row per participant: outcomes at -20 % bias + glucose metrics
  figures/25_decision_impact_vs_bias.png, 26_fault_families.png,
  figures/27_dose_change_distribution.png, 28_risk_indices_vs_bias.png
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preprocess as pp          # shared loaders + parquet cache (analysis/preprocess.py)

def take_lookup_options(argv):
    """Pull the --lookup-* options out of the argument list. Returns (positional arguments, options).
    Values may follow the option as the next word or after '=' (--lookup-min=-90)."""
    opts = {"lookup_min": None, "lookup_max": None, "lookup_step": None, "lookup_only": False, "lookup_out": None}
    valued = ("--lookup-min", "--lookup-max", "--lookup-step", "--lookup-out")
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        name, eq, value = a.partition("=")
        if a == "--lookup-only":
            opts["lookup_only"] = True
        elif name in valued:
            if not eq:
                if i + 1 >= len(argv):
                    sys.exit(f"{name} needs a value")
                i += 1
                value = argv[i]
            opts[name[2:].replace("-", "_")] = value
        elif a.startswith("--lookup"):
            sys.exit(f"unknown option {a}; see --help")
        else:
            positional.append(a)
        i += 1
    for k in ("lookup_min", "lookup_max", "lookup_step"):
        if opts[k] is not None:
            try:
                opts[k] = int(opts[k])
            except ValueError:
                sys.exit(f"--{k.replace('_', '-')} must be a whole number of percent, got {opts[k]!r}")
    return positional, opts


ARGS, LOOKUP_OPTS = take_lookup_options(sys.argv[1:])

if ARGS and ARGS[0] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

ROOT = ARGS[0] if len(ARGS) > 0 else "Uncommitted Data/Raw Data Dump"
OUT = ARGS[1] if len(ARGS) > 1 else "analysis"
FIG = os.path.join(OUT, "figures")
CACHE = ARGS[2] if len(ARGS) > 2 else pp.DEFAULT_CACHE
QUICK = os.environ.get("SIM_V2_QUICK", "") == "1"

pp.check_raw_data(ROOT)

# --- settings -------------------------------------------------------------------
SEED = 20261027
SLOT_S = 300                                   # the CGM grid: one slot per 5 min
LOW_T, LOW_T2, HIGH_T, HIGH_T2 = 70, 54, 180, 200
THRESHOLDS = [("low70", LOW_T, "below"), ("low54", LOW_T2, "below"), ("high180", HIGH_T, "above"), ("high200", HIGH_T2, "above")]
EPISODE_MIN_SLOTS = 3                          # 3 readings = 15 min starts or ends an episode
MATCH_SLOTS = 6                                # an alert within +/- 30 min of a true episode start counts as the same episode
DEVICE_MIN, DEVICE_MAX = 39, 401               # the G4 display range; a faulted sensor still clips here
WIZARD_TOL_S = 300                             # wizard record -> nearest CGM reading within 5 min
METER_TOL_S = 300                              # wizard BG input -> meter row with the same value within 5 min
SKIP_U, CHANGE_U = 0.5, (0.5, 1.0)             # dose outcome cut-offs in insulin units
LOOKUP_MIN = -40 if LOOKUP_OPTS["lookup_min"] is None else LOOKUP_OPTS["lookup_min"]     # percent; negative = reads low
LOOKUP_MAX = 40 if LOOKUP_OPTS["lookup_max"] is None else LOOKUP_OPTS["lookup_max"]
LOOKUP_STEP = 2 if LOOKUP_OPTS["lookup_step"] is None else LOOKUP_OPTS["lookup_step"]
LOOKUP_ONLY = LOOKUP_OPTS["lookup_only"]                                                 # only the lookup CSV is written
LOOKUP_OUT = LOOKUP_OPTS["lookup_out"] or os.path.join(OUT, "simulation_v2_lookup.csv")
if LOOKUP_STEP <= 0 or LOOKUP_MIN > LOOKUP_MAX:
    sys.exit(f"bad lookup grid: min {LOOKUP_MIN}, max {LOOKUP_MAX}, step {LOOKUP_STEP}")
if LOOKUP_MIN < -100:
    sys.exit("--lookup-min below -100 % makes no sense: the sensor cannot read below zero")
BIAS_LEVELS = list(range(LOOKUP_MIN, LOOKUP_MAX + 1, LOOKUP_STEP))   # default -40..+40 in 2 % steps (41 rows)
HEADLINE_BIAS = [-10, -20, -30, 10, 20]
if not LOOKUP_ONLY and any(b not in BIAS_LEVELS for b in HEADLINE_BIAS):
    sys.exit(f"the full run needs the headline levels {HEADLINE_BIAS} in the bias grid; use --lookup-only for other grids")
NOISE_SD = [5, 10, 20]                         # mg/dL
AR_PHI = 0.8                                   # AR(1): each 5-min error keeps 80 % of the previous error
DRIFT_PCT = [10, 20, 30]                       # bias reaches -X % at the start of wear day 7
DROPOUT_PCT = [2, 5, 10]                       # share of readings lost in random 15-120 min gaps
GAP_MIN_SLOTS, GAP_MAX_SLOTS = 3, 24
LAG_MIN = [5, 10, 15]
MIXED_BIAS, MIXED_SD = -20, 10
N_DRAWS = 2 if QUICK else 10
N_BOOT = 1000
MATCHED = [("bias", -20), ("noise_white", 10), ("noise_ar", 10), ("drift", 20), ("dropout", 5), ("lag", 10), ("mixed", 0)]
FAMILIES = ["bias", "noise_white", "noise_ar", "drift", "dropout", "lag", "mixed"]
SENS_BIAS = [0, -10, -20, -30]                 # levels for the meter-as-truth sensitivity
T0 = time.time()


def log(*a):
    """Print a progress line with elapsed seconds."""
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------------
def load_tables():
    """Load the in-window CGM trace, the wizard decisions and the meter rows from the shared cache."""
    log("loading cache tables (analysis/preprocess.py) ...")
    cgm = pp.load_cgm(ROOT, CACHE)
    cgm = cgm[cgm.in_study_window][["PtID", "t", "glucose", "session_id", "session_confirmed_by_cal"]].sort_values(["PtID", "t"]).reset_index(drop=True)
    wz = pp.load_pump(ROOT, CACHE)["wizard"]
    bgm = pp.load_bgm(ROOT, CACHE)
    # meter-log rows only (preprocess.py from_meter_log; pump "BG" rows are often CGM values typed into the pump). Calibration rows are
    # kept here on purpose and flagged: prepare_wizard matches them first, then drops and counts them (dropped_calibration_fingerstick).
    meter = bgm[bgm.from_meter_log & bgm.in_study_window & ~bgm.value_out_of_range][["PtID", "t", "value", "used_for_calibration"]]
    parts = pp.load_participants(ROOT, CACHE)
    return cgm, wz, meter, parts


def prepare_wizard(wz, cgm, meter, parts):
    """Select usable correction-dose decisions and attach the matched CGM reading and meter check.

    Keep in-window records with a typed glucose, an ISF and a target. The pump's correction
    target is `target_mgdl` (OmniPod, Tandem) or `target_high_mgdl` (Medtronic range). The
    "correct above" level is `target_high_mgdl` where present, else the target.
    `meter_truth` marks the records used in the meter-as-truth sensitivity: CGM+BGM arm only,
    typed value equal (within 2 mg/dL) to a meter-device reading within 5 min, typed value not
    identical to the nearest CGM reading, and that meter reading not used to calibrate the sensor.
    (In the CGM-only arm the typed values are CGM values, so they cannot serve as a reference.)
    """
    w = wz[wz.in_study_window].copy()
    info = {"wizard_rows_in_window": int(len(w)), "with_bg_input": int(w.bg_input_entered.sum())}
    w["target"] = w.target_mgdl.where(w.target_mgdl.notna(), w.target_high_mgdl)
    w["correct_above"] = w.target_high_mgdl.where(w.target_high_mgdl.notna(), w.target_mgdl)
    w = w[(w.bg_input_entered | (w.rec_correction_u != 0)) & w.isf_mgdl_per_u.notna() & w.target.notna()]
    info["with_isf_and_target"] = int(len(w))
    # validate the pre-IOB part of the rule against the pump's own recommended correction
    corr = np.where(w.bg_input_mgdl > w.correct_above, (w.bg_input_mgdl - w.target) / w.isf_mgdl_per_u, 0.0)
    info["rule_matches_pump_correction_within_0.15u_pct"] = round(float((np.abs(corr - w.rec_correction_u) < 0.15).mean() * 100), 1)
    net = ((corr - w.iob_u.fillna(0)).clip(lower=0) - (w.rec_net_u - w.rec_carb_u)).abs() < 0.15
    info["rule_minus_iob_matches_pump_net_within_0.15u_pct"] = round(float(net.mean() * 100), 1)
    w = w[["PtID", "t", "bg_input_mgdl", "isf_mgdl_per_u", "target", "correct_above", "iob_u"]].sort_values("t")
    c = cgm[["PtID", "t", "glucose"]].rename(columns={"t": "t_cgm", "glucose": "g_cgm"}).sort_values("t_cgm")
    w = pd.merge_asof(w, c, left_on="t", right_on="t_cgm", by="PtID", direction="nearest", tolerance=WIZARD_TOL_S)
    w = w[w.g_cgm.notna()].copy()
    info["with_cgm_within_5min"] = int(len(w))
    info["participants"] = int(w.PtID.nunique())
    m = meter.rename(columns={"t": "t_meter", "value": "meter", "used_for_calibration": "meter_is_calibration"}).sort_values("t_meter")
    w = pd.merge_asof(w.sort_values("t"), m, left_on="t", right_on="t_meter", by="PtID", direction="nearest", tolerance=METER_TOL_S)
    w = w.merge(parts[["PtID", "arm"]], on="PtID", how="left")
    w["arm"] = w.arm.astype(str)
    meter_match = w.meter.notna() & ((w.meter - w.bg_input_mgdl).abs() <= 2)
    same_as_cgm = w.bg_input_mgdl == w.g_cgm
    within5 = (w.bg_input_mgdl - w.g_cgm).abs() <= 0.05 * w.g_cgm
    info["typed_value_vs_nearest_cgm_by_arm"] = {a: {"n": int((w.arm == a).sum()), "identical_pct": round(float(same_as_cgm[w.arm == a].mean() * 100), 1),
                                                     "within_5pct_pct": round(float(within5[w.arm == a].mean() * 100), 1),
                                                     "matches_a_meter_reading_pct": round(float(meter_match[w.arm == a].mean() * 100), 1)}
                                                 for a in sorted(w.arm.unique())}
    info["bg_input_matches_a_meter_reading_any_arm"] = int(meter_match.sum())
    is_cal = w.meter_is_calibration.eq(True)                              # NaN (no meter row) counts as not a calibration
    w["meter_truth"] = meter_match & (w.arm == "CGM+BGM") & ~same_as_cgm & ~is_cal
    info["meter_truth_subset"] = {"rule": "CGM+BGM arm, typed value = meter-device reading within 5 min, typed value != nearest CGM reading, meter reading not used for calibration",
                                  "n": int(w.meter_truth.sum()), "dropped_cgm_only_arm": int((meter_match & (w.arm != "CGM+BGM")).sum()),
                                  "dropped_identical_to_cgm": int((meter_match & (w.arm == "CGM+BGM") & same_as_cgm).sum()),
                                  "dropped_calibration_fingerstick": int((meter_match & (w.arm == "CGM+BGM") & ~same_as_cgm & is_cal).sum())}
    w["iob_u"] = w.iob_u.fillna(0.0)
    return w.sort_values(["PtID", "t"]).reset_index(drop=True), info


def sensor_age_days(t, session_id, confirmed):
    """Days since the start of the current sensor, per reading.

    A session start counts as a new sensor only when a calibration confirmed it (the G4 asks
    for calibrations after every warm-up). Unconfirmed starts are treated as signal-loss gaps
    inside the same sensor, so the drift clock keeps running.
    """
    first = pd.Series(t).groupby(session_id).transform("min").to_numpy()
    is_start = np.concatenate(([True], session_id[1:] != session_id[:-1]))
    anchor = np.where(is_start & (confirmed | (np.arange(len(t)) == 0)), first, np.nan)
    anchor = pd.Series(anchor).ffill().to_numpy()
    return (t - anchor) / 86400.0


def build_participant(pid, c, w):
    """Put one participant's trace on a 5-min grid and index the wizard decisions on it."""
    t = c.t.to_numpy(np.int64)
    g = c.glucose.to_numpy(np.float64)
    slot0 = t[0] // SLOT_S
    slots = t // SLOT_S - slot0
    n = int(slots[-1]) + 1
    keep = np.concatenate(([True], slots[1:] != slots[:-1]))      # first reading per slot
    grid = np.full(n, np.nan)
    grid[slots[keep]] = g[keep]
    age = np.full(n, np.nan)
    age[slots[keep]] = sensor_age_days(t, c.session_id.to_numpy(), c.session_confirmed_by_cal.to_numpy())[keep]
    p = {"PtID": int(pid), "g": grid, "age": age, "has": ~np.isnan(grid), "n_days": int(len(np.unique(t // 86400))),
         "n_readings": int(len(t)), "collisions": int((~keep).sum())}
    if len(w):
        ws = (w.t_cgm.to_numpy(np.int64) // SLOT_S - slot0).astype(np.int64)
        ok = ~np.isnan(grid[ws])                                   # the matched reading survived the grid (not a collision)
        p["w_slot"] = ws[ok]
        p["w_isf"], p["w_target"], p["w_above"], p["w_iob"] = (w[k].to_numpy(np.float64)[ok] for k in ["isf_mgdl_per_u", "target", "correct_above", "iob_u"])
        p["w_bg"] = w.bg_input_mgdl.to_numpy(np.float64)[ok]
        p["w_meter"] = w.meter_truth.to_numpy(bool)[ok]
        p["w_dropped"] = int((~ok).sum())
    else:
        p["w_slot"] = np.zeros(0, np.int64)
        p["w_dropped"] = 0
    return p


# --------------------------------------------------------------------------------
# Faults
# --------------------------------------------------------------------------------
def ar1_noise(rng, n, sd, phi=AR_PHI):
    """AR(1) noise with marginal SD `sd`: e[t] = phi * e[t-1] + sqrt(1 - phi^2) * sd * w[t], w ~ N(0, 1)."""
    return lfilter([1.0], [1.0, -phi], rng.standard_normal(n)) * (sd * np.sqrt(1 - phi ** 2))


def dropout_mask(rng, has, pct):
    """Random gaps of 15-120 min (3-24 slots) until `pct` percent of the readings are removed."""
    n, target, removed = len(has), pct / 100 * has.sum(), 0
    drop = np.zeros(n, bool)
    while removed < target:
        s = int(rng.integers(0, n))
        e = min(s + int(rng.integers(GAP_MIN_SLOTS, GAP_MAX_SLOTS + 1)), n)
        new = has[s:e] & ~drop[s:e]
        removed += int(new.sum())
        drop[s:e] |= new
    return drop


def apply_fault(p, family, size, rng):
    """Return the faulted trace (NaN = no reading), clipped to the device display range."""
    g = p["g"]
    if family == "bias":
        f = g * (1 + size / 100)
    elif family == "noise_white":
        f = g + rng.normal(0, size, len(g))
    elif family == "noise_ar":
        f = g + ar1_noise(rng, len(g), size)
    elif family == "drift":                       # 0 at the first reading of the sensor, -size % from the start of day 7 on
        f = g * (1 - size / 100 * np.minimum(p["age"] / 6.0, 1.0))
    elif family == "dropout":
        f = g.copy()
        f[dropout_mask(rng, p["has"], size)] = np.nan
    elif family == "lag":                         # the sensor shows the glucose of `size` minutes ago
        k = int(size // 5)
        f = np.full(len(g), np.nan)
        f[k:] = g[:-k]
        f = np.where(p["has"] & np.isnan(f), g, f)    # right after a data gap there is no older value: keep the current one
    elif family == "mixed":
        f = g * (1 + MIXED_BIAS / 100) + ar1_noise(rng, len(g), MIXED_SD)
    else:
        raise ValueError(family)
    return np.clip(f, DEVICE_MIN, DEVICE_MAX)   # NaN stays NaN


# --------------------------------------------------------------------------------
# Outcomes
# --------------------------------------------------------------------------------
def find_episodes(state):
    """Episodes on a 5-min grid. state: 1 = beyond the threshold, 0 = in range, -1 = no reading.

    An episode starts at the first of >= 3 consecutive '1' slots (15 min) and ends at the first
    run of >= 3 consecutive non-'1' slots (15 min in range, or 15 min without readings).
    Returns (starts, ends) in slot units; ends are exclusive.
    """
    n = len(state)
    change = np.flatnonzero(state[1:] != state[:-1]) + 1
    run_start = np.concatenate(([0], change))
    run_len = np.diff(np.append(run_start, n))
    strong = run_len >= EPISODE_MIN_SLOTS
    s_start, s_low = run_start[strong], state[run_start[strong]] == 1
    if not s_low.any():
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    prev_low = np.concatenate(([False], s_low[:-1]))
    ep = np.flatnonzero(s_low & ~prev_low)
    not_low = np.flatnonzero(~s_low)
    if len(not_low):
        nxt = np.searchsorted(not_low, ep, side="left")
        ends = np.where(nxt < len(not_low), s_start[not_low[np.minimum(nxt, len(not_low) - 1)]], n)
    else:
        ends = np.full(len(ep), n)
    return s_start[ep], ends


def episode_state(g, thr, side):
    """1 where the reading is beyond the threshold, 0 in range, -1 where there is no reading."""
    beyond = (g < thr) if side == "below" else (g > thr)
    return np.where(np.isnan(g), -1, beyond.astype(np.int8)).astype(np.int8)


def match_episodes(ts, te, fs, fe, g_f):
    """Compare faulted episodes [fs, fe) with true ones [ts, te) (slot units, ends exclusive).

    Each true episode gets a window from 30 min before its start to its end (at least 30 min
    after the start). The true episode is detected if any faulted episode is ongoing inside
    that window; the delay is the faulted start minus the true start (negative = early alert).
    A faulted episode that overlaps no window is a false alert.
    """
    w = MATCH_SLOTS
    a, b = ts - w, np.maximum(te, ts + w + 1)                            # windows [a, b), both sorted
    j = np.searchsorted(fe, a, side="right")                             # first faulted episode ending after the window opens
    jj = np.minimum(j, max(len(fs) - 1, 0))
    detected = (j < len(fs)) & (fs[jj] < b) if len(fs) else np.zeros(len(ts), bool)
    delays = (fs[jj[detected]] - ts[detected]) * (SLOT_S / 60)          # minutes
    i = np.searchsorted(b, fs, side="right")                             # first window closing after the faulted start
    ii = np.minimum(i, max(len(ts) - 1, 0))
    matched = (i < len(ts)) & (a[ii] < fe) if len(ts) else np.zeros(len(fs), bool)
    no_reading_at_start = int(np.isnan(g_f[ts]).sum()) if len(ts) else 0
    return {"n_true": int(len(ts)), "n_fault": int(len(fs)), "missed": int((~detected).sum()), "false": int((~matched).sum()),
            "delay_median_min": float(np.median(delays)) if len(delays) else np.nan,
            "delay_mean_min": float(np.mean(delays)) if len(delays) else np.nan,
            "late_pct": float((delays > 0).mean() * 100) if len(delays) else np.nan,
            "no_reading_at_start": no_reading_at_start}


def risk_indices(g):
    """Kovatchev LBGI / HBGI. f(BG) = 1.509 * ((ln BG)^1.084 - 5.381); r = 10 f^2; LBGI = mean r where f < 0, HBGI where f > 0."""
    x = g[~np.isnan(g)]
    f = 1.509 * (np.log(x) ** 1.084 - 5.381)
    r = 10 * f ** 2
    return float(np.mean(np.where(f < 0, r, 0))), float(np.mean(np.where(f > 0, r, 0)))


def glucose_summary(g, prefix=""):
    """Time in range 70-180, below 70 / 54, above 180 / 250 (percent of readings), mean, CV, LBGI, HBGI."""
    x = g[~np.isnan(g)]
    lbgi, hbgi = risk_indices(x)
    return {prefix + "tir_pct": float(((x >= 70) & (x <= 180)).mean() * 100), prefix + "tbr70_pct": float((x < 70).mean() * 100),
            prefix + "tbr54_pct": float((x < 54).mean() * 100), prefix + "tar180_pct": float((x > 180).mean() * 100),
            prefix + "tar250_pct": float((x > 250).mean() * 100), prefix + "mean_mgdl": float(x.mean()),
            prefix + "cv_pct": float(x.std() / x.mean() * 100), prefix + "lbgi": lbgi, prefix + "hbgi": hbgi}


def correction_dose(G, isf, target, above, iob):
    """Correction dose in units: (G - target) / ISF minus IOB, floored at 0, only when G is above the 'correct above' level."""
    return np.where(G > above, np.maximum((G - target) / isf - iob, 0.0), 0.0)


def dose_outcomes(p, truth, faulted, prefix=""):
    """Compare correction doses from the true and the faulted glucose at each wizard decision."""
    out = {}
    have = ~np.isnan(faulted)
    out[prefix + "n_dec"] = int(len(truth))
    out[prefix + "no_reading_pct"] = float((~have).mean() * 100) if len(truth) else np.nan
    if have.sum() == 0:
        for k in ["skipped_pct", "skipped_of_needed_pct", "spurious_pct", "changed_05_pct", "changed_1_pct", "under_1_pct", "over_1_pct",
                  "delta_mean_u", "delta_median_u", "abs_delta_median_u", "skipped_n"]:
            out[prefix + k] = np.nan
        return out, np.zeros(0)
    d_true = correction_dose(truth[have], p["w_isf"][have], p["w_target"][have], p["w_above"][have], p["w_iob"][have])
    d_f = correction_dose(faulted[have], p["w_isf"][have], p["w_target"][have], p["w_above"][have], p["w_iob"][have])
    delta = d_f - d_true
    needed = d_true > SKIP_U
    skipped = needed & (d_f == 0)
    n = len(delta)
    out.update({prefix + "skipped_pct": float(skipped.mean() * 100), prefix + "skipped_n": int(skipped.sum()),
                prefix + "skipped_of_needed_pct": float(skipped.sum() / needed.sum() * 100) if needed.any() else np.nan,
                prefix + "spurious_pct": float(((d_true == 0) & (d_f > SKIP_U)).mean() * 100),
                prefix + "changed_05_pct": float((np.abs(delta) > CHANGE_U[0]).mean() * 100),
                prefix + "changed_1_pct": float((np.abs(delta) > CHANGE_U[1]).mean() * 100),
                prefix + "under_1_pct": float((delta < -CHANGE_U[1]).mean() * 100), prefix + "over_1_pct": float((delta > CHANGE_U[1]).mean() * 100),
                prefix + "delta_mean_u": float(delta.mean()), prefix + "delta_median_u": float(np.median(delta)),
                prefix + "abs_delta_median_u": float(np.median(np.abs(delta)))})
    return out, delta


def evaluate(p, true_eps, g_f, want_delta=False, sens=False):
    """All outcomes of one faulted trace for one participant."""
    out = {}
    delta = None
    if len(p["w_slot"]):
        truth = p["g"][p["w_slot"]]
        faulted = g_f[p["w_slot"]]
        d, delta = dose_outcomes(p, truth, faulted)
        out.update(d)
        if sens and p["w_meter"].any():            # sensitivity: the typed meter value is the truth
            m = p["w_meter"]
            q = {k: p[k][m] for k in ["w_slot", "w_isf", "w_target", "w_above", "w_iob", "w_bg", "w_meter"]}
            d2, _ = dose_outcomes(q, p["w_bg"][m], faulted[m], prefix="mt_")
            out.update(d2)
    for name, thr, side in THRESHOLDS:
        fs, fe = find_episodes(episode_state(g_f, thr, side))
        r = match_episodes(true_eps[name][0], true_eps[name][1], fs, fe, g_f)
        days = p["n_days"]
        out.update({f"{name}_true_per_day": r["n_true"] / days, f"{name}_fault_per_day": r["n_fault"] / days,
                    f"{name}_false_per_day": r["false"] / days, f"{name}_missed_per_day": r["missed"] / days,
                    f"{name}_missed_pct": r["missed"] / r["n_true"] * 100 if r["n_true"] else np.nan,
                    f"{name}_delay_median_min": r["delay_median_min"], f"{name}_delay_mean_min": r["delay_mean_min"],
                    f"{name}_late_pct": r["late_pct"], f"{name}_no_reading_at_start_per_day": r["no_reading_at_start"] / days,
                    f"{name}_no_reading_at_start_pct": r["no_reading_at_start"] / r["n_true"] * 100 if r["n_true"] else np.nan})
    out.update(glucose_summary(g_f))
    if len(p["w_slot"]):
        out["skipped_per_day"] = out["skipped_n"] / p["n_days"]
    return out, (delta if want_delta else None)


def settings():
    """The list of (family, size, n_draws) to run. With --lookup-only, the constant-bias family alone."""
    s = [("bias", b, 1) for b in BIAS_LEVELS]
    if LOOKUP_ONLY:
        return s
    s += [("noise_white", sd, N_DRAWS) for sd in NOISE_SD] + [("noise_ar", sd, N_DRAWS) for sd in NOISE_SD]
    s += [("drift", d, 1) for d in DRIFT_PCT] + [("dropout", d, N_DRAWS) for d in DROPOUT_PCT]
    s += [("lag", l, 1) for l in LAG_MIN] + [("mixed", 0, N_DRAWS)]
    return s


def run_all(parts_list):
    """Loop over participants, fault settings and draws. Returns the long results table and pooled dose deltas."""
    rows, deltas, true_rows = [], {b: [] for b in HEADLINE_BIAS}, []
    for i, p in enumerate(parts_list):
        true_eps = {name: find_episodes(episode_state(p["g"], thr, side)) for name, thr, side in THRESHOLDS}
        tr = {"PtID": p["PtID"], "n_days": p["n_days"], "n_readings": p["n_readings"], "n_decisions": int(len(p["w_slot"])),
              "n_meter_truth_decisions": int(p["w_meter"].sum()) if len(p["w_slot"]) else 0}
        tr.update({f"{name}_episodes": int(len(true_eps[name][0])) for name in true_eps})
        tr.update(glucose_summary(p["g"], prefix="true_"))
        true_rows.append(tr)
        for family, size, n_draws in settings():
            for draw in range(n_draws):
                rng = np.random.default_rng([SEED, p["PtID"], FAMILIES.index(family), int(size) + 100, draw])
                g_f = apply_fault(p, family, size, rng)
                want = family == "bias" and size in HEADLINE_BIAS
                out, delta = evaluate(p, true_eps, g_f, want_delta=want, sens=(family == "bias" and size in SENS_BIAS))
                out.update({"PtID": p["PtID"], "family": family, "size": size, "draw": draw})
                rows.append(out)
                if want and delta is not None:
                    deltas[size].append(delta)
        if i % 25 == 0:
            log(f"participant {i + 1}/{len(parts_list)} done")
    res = pd.DataFrame(rows)
    deltas = {b: (np.concatenate(v) if v else np.zeros(0)) for b, v in deltas.items()}
    return res, pd.DataFrame(true_rows), deltas


# --------------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------------
def clean(o):
    """Make a nested dict JSON-safe: numpy numbers to Python numbers, NaN to null, tuple keys to strings."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def per_participant(res):
    """Mean over Monte Carlo draws, one row per participant and setting."""
    return res.groupby(["family", "size", "PtID"]).mean(numeric_only=True).drop(columns="draw").reset_index()


def summarise(df, cols):
    """Median, IQR, mean and n across participants for each column."""
    out = {}
    for c in cols:
        s = df[c].dropna()
        out[c] = {"median": float(s.median()), "q1": float(s.quantile(0.25)), "q3": float(s.quantile(0.75)),
                  "mean": float(s.mean()), "n": int(len(s))} if len(s) else {"median": np.nan, "q1": np.nan, "q3": np.nan, "mean": np.nan, "n": 0}
    return out


def bootstrap_ci(df, cols, n_boot=N_BOOT, seed=SEED):
    """Participant bootstrap of the median: resample participants, recompute the median, take the 2.5-97.5 percentiles."""
    rng = np.random.default_rng(seed)
    x = df[cols].to_numpy(np.float64)
    n = len(x)
    idx = rng.integers(0, n, size=(n_boot, n))
    meds = np.nanmedian(x[idx], axis=1)                                   # n_boot x len(cols)
    lo, hi = np.nanpercentile(meds, [2.5, 97.5], axis=0)
    return {c: {"median": float(np.nanmedian(x[:, j])), "ci95": [float(lo[j]), float(hi[j])]} for j, c in enumerate(cols)}


OUTCOME_COLS = ["skipped_pct", "skipped_of_needed_pct", "spurious_pct", "changed_05_pct", "changed_1_pct", "under_1_pct", "over_1_pct",
                "delta_mean_u", "delta_median_u", "abs_delta_median_u", "skipped_per_day", "no_reading_pct",
                "low70_true_per_day", "low70_fault_per_day", "low70_false_per_day", "low70_missed_per_day", "low70_missed_pct", "low70_delay_median_min", "low70_late_pct",
                "low54_fault_per_day", "low54_false_per_day", "low54_missed_per_day", "low54_missed_pct", "low54_delay_median_min",
                "high180_true_per_day", "high180_fault_per_day", "high180_false_per_day", "high180_missed_per_day", "high180_missed_pct", "high180_delay_median_min",
                "high200_true_per_day", "high200_fault_per_day", "high200_false_per_day", "high200_missed_per_day", "high200_missed_pct", "high200_delay_median_min",
                "low70_no_reading_at_start_pct", "low54_no_reading_at_start_pct",
                "tir_pct", "tbr70_pct", "tbr54_pct", "tar180_pct", "tar250_pct", "mean_mgdl", "cv_pct", "lbgi", "hbgi"]
CI_COLS = ["skipped_pct", "changed_1_pct", "spurious_pct", "low70_false_per_day", "low70_missed_per_day", "low70_missed_pct",
           "high180_false_per_day", "high180_missed_per_day", "high200_missed_per_day", "tir_pct", "tbr70_pct", "lbgi", "hbgi"]


# --------------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"   # categorical slots 1-3 (same palette as explore_raw_data.py)
RAMP = ["#86b6ef", "#2a78d6", "#104281"]
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 9,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 9.5, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 8.5,
    "lines.linewidth": 1.8, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def save(fig, name):
    """Save a figure into the figures folder."""
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


def band(ax, x, agg, col, color, label):
    """Median line with an IQR band, read from the lookup table."""
    ax.fill_between(x, agg[col + "_q1"], agg[col + "_q3"], color=color, alpha=0.18, linewidth=0)
    ax.plot(x, agg[col + "_median"], color=color, label=label)


def mark_levels(ax):
    """Dotted lines at the three headline low-bias levels."""
    for b in (-10, -20, -30):
        ax.axvline(b, color=AXIS, lw=0.8, ls=":")


def fig25(lk):
    """Decision impact vs constant bias, four panels."""
    x = lk.bias_pct.to_numpy()
    fig, axes = plt.subplots(2, 2, figsize=(6, 5), sharex=True)
    panels = [("skipped_pct", "Corrections skipped, % of decisions", C_ORANGE), ("changed_1_pct", "Dose changed by > 1 U, % of decisions", C_BLUE),
              ("low70_false_per_day", "False low alerts (< 70 mg/dL) per day", C_ORANGE), ("low70_missed_per_day", "Missed low alerts (< 70 mg/dL) per day", C_BLUE)]
    for ax, (col, title, color) in zip(axes.ravel(), panels):
        band(ax, x, lk, col, color, title)
        mark_levels(ax)
        ax.set_title(title)
        ax.set_ylim(bottom=0)
        ax.set_xlim(-40, 40)
        ax.set_xticks([-40, -30, -20, -10, 0, 10, 20, 30, 40])
    for ax in axes[1]:
        ax.set_xlabel("Sensor bias, % of true glucose")
    fig.suptitle("Decision impact of a constant sensor bias (negative = reads low). Line = median person, band = IQR", x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "25_decision_impact_vs_bias.png")


def fig26(fam):
    """Fault families compared at a matched size: dot = median, line = IQR."""
    labels = {("bias", -20): "Bias -20 %", ("noise_white", 10): "White noise SD 10", ("noise_ar", 10): "AR(1) noise SD 10",
              ("drift", 20): "Drift to -20 % by day 7", ("dropout", 5): "Dropouts 5 % of time", ("lag", 10): "Lag 10 min", ("mixed", 0): "Mixed: -20 % + AR noise 10"}
    panels = [("skipped_pct", "Corrections skipped\n(% of decisions)"), ("changed_1_pct", "Dose changed > 1 U\n(% of decisions)"),
              ("low70_false_per_day", "False low alerts\n(per day)"), ("low70_missed_pct", "Missed low episodes\n(% of true episodes)")]
    fig, axes = plt.subplots(1, 4, figsize=(6.4, 3.2), sharey=True)
    y = np.arange(len(MATCHED))[::-1]
    for ax, (col, title) in zip(axes, panels):
        for yi, key in zip(y, MATCHED):
            s = fam[key][col]
            ax.plot([s["q1"], s["q3"]], [yi, yi], color=C_BLUE, lw=2, alpha=0.5)
            ax.plot(s["median"], yi, "o", color=C_BLUE, markersize=5)
        ax.set_title(title, fontsize=8.5)
        ax.grid(axis="x", color=GRID)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(left=0)
    axes[0].set_yticks(y, [labels[k] for k in MATCHED], fontsize=8.5)
    fig.suptitle("Fault families at a matched size: dot = median person, line = IQR", x=0.01, ha="left", fontsize=10, fontweight="semibold", color=INK)
    fig.tight_layout()
    save(fig, "26_fault_families.png")


def fig27(deltas, lk):
    """Distribution of the correction-dose change at -10/-20/-30 % bias, with the skipped share."""
    fig, ax = plt.subplots(figsize=(6, 3.4))
    levels = [-10, -20, -30]
    data = [np.clip(deltas[b], -6, 2) for b in levels]
    parts = ax.violinplot(data, positions=range(len(levels)), showmedians=True, showextrema=False, widths=0.8)
    for body, col in zip(parts["bodies"], RAMP):
        body.set_facecolor(col); body.set_alpha(0.75); body.set_edgecolor("none")
    parts["cmedians"].set_color(INK)
    for i, b in enumerate(levels):
        row = lk[lk.bias_pct == b].iloc[0]
        med = float(np.median(deltas[b]))
        ax.text(i, 2.5, f"median {med:+.2f} U\nskipped {row['skipped_pct_median']:.0f} % of decisions\n(> 1 U less: {row['under_1_pct_median']:.0f} %)",
                ha="center", va="top", fontsize=8, color=INK2, linespacing=1.3)
    ax.axhline(0, color=AXIS, lw=0.8)
    ax.set_xticks(range(len(levels)), [f"{b} %" for b in levels])
    ax.set_xlabel("Sensor bias (reads low)")
    ax.set_ylabel("Faulted dose minus true dose (units)")
    ax.set_ylim(-6.3, 2.6)
    ax.set_title(f"Correction-dose change per bolus-calculator decision ({len(deltas[-10]):,} decisions pooled; clipped at -6 U)", fontsize=9)
    fig.tight_layout()
    save(fig, "27_dose_change_distribution.png")


def fig28(lk, true_agg):
    """LBGI/HBGI and TIR/TBR/TAR vs bias, with the true values marked."""
    x = lk.bias_pct.to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.2))
    ax = axes[0]
    band(ax, x, lk, "lbgi", C_ORANGE, "LBGI (low risk)")
    band(ax, x, lk, "hbgi", C_BLUE, "HBGI (high risk)")
    ax.axhline(true_agg["true_lbgi"]["median"], color=C_ORANGE, lw=0.9, ls="--")
    ax.axhline(true_agg["true_hbgi"]["median"], color=C_BLUE, lw=0.9, ls="--")
    ax.set_title("Risk indices on the faulted trace")
    ax.set_ylabel("Index value (unitless)")
    ax.legend(loc="upper center")
    ax = axes[1]
    band(ax, x, lk, "tir_pct", C_AQUA, "Time 70-180 (TIR)")
    band(ax, x, lk, "tbr70_pct", C_ORANGE, "Time below 70 (TBR)")
    band(ax, x, lk, "tar180_pct", C_BLUE, "Time above 180 (TAR)")
    for k, col in [("true_tir_pct", C_AQUA), ("true_tbr70_pct", C_ORANGE), ("true_tar180_pct", C_BLUE)]:
        ax.axhline(true_agg[k]["median"], color=col, lw=0.9, ls="--")
    ax.set_title("Time in ranges on the faulted trace")
    ax.set_ylabel("% of readings")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    for ax in axes:
        mark_levels(ax)
        ax.set_xlim(-40, 40)
        ax.set_xticks([-40, -20, 0, 20, 40])
        ax.set_xlabel("Sensor bias, % (negative = reads low)")
        ax.set_ylim(bottom=0)
    fig.suptitle("Dashed = true trace (median person). Line = median, band = IQR", x=0.01, ha="left", fontsize=10, fontweight="semibold", color=INK)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    save(fig, "28_risk_indices_vs_bias.png")


# --------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------
def main():
    if LOOKUP_ONLY:
        log(f"lookup-only run: bias {LOOKUP_MIN} to {LOOKUP_MAX} % in {LOOKUP_STEP} % steps ({len(BIAS_LEVELS)} levels) -> {LOOKUP_OUT}")
        os.makedirs(os.path.dirname(os.path.abspath(LOOKUP_OUT)), exist_ok=True)
    else:
        os.makedirs(FIG, exist_ok=True)
    cgm, wz, meter, parts = load_tables()
    wizard, w_info = prepare_wizard(wz, cgm, meter, parts)
    log("wizard decisions:", w_info)
    pids = sorted(cgm.PtID.unique())
    if QUICK:
        pids = pids[:20]
    w_groups = {int(k): v for k, v in wizard.groupby("PtID")}
    keep = set(int(x) for x in pids)
    parts_list = [build_participant(pid, c, w_groups.get(int(pid), wizard.iloc[0:0])) for pid, c in cgm.groupby("PtID") if int(pid) in keep]
    log(f"prepared {len(parts_list)} participants; grid collisions {sum(p['collisions'] for p in parts_list)} readings; "
        f"decisions dropped at collisions {sum(p['w_dropped'] for p in parts_list)}")

    res, true_df, deltas = run_all(parts_list)
    log("evaluations:", len(res))
    pt = per_participant(res)

    # lookup table over bias levels
    bias = pt[pt.family == "bias"]
    rows = []
    for b in BIAS_LEVELS:
        s = summarise(bias[bias["size"] == b], OUTCOME_COLS)
        row = {"bias_pct": b}
        for c in OUTCOME_COLS:
            for k in ["median", "q1", "q3", "mean", "n"]:
                row[f"{c}_{k}"] = s[c][k]
        rows.append(row)
    lk = pd.DataFrame(rows)
    lk.to_csv(LOOKUP_OUT, index=False, float_format="%.4f")
    log("wrote", LOOKUP_OUT)
    if LOOKUP_ONLY:
        log("lookup-only run: skipping the other fault families, figures, participants CSV and stats JSON")
        log("runtime", round(time.time() - T0, 1), "s")
        return

    # bootstrap CIs at the headline levels
    ci = {str(b): bootstrap_ci(bias[bias["size"] == b], CI_COLS) for b in HEADLINE_BIAS}
    # fault families (matched size and all settings)
    fam = {}
    for (family, size), g in pt.groupby(["family", "size"]):
        fam[(family, size)] = summarise(g, OUTCOME_COLS)
    fam_json = {f"{family}:{size}": v for (family, size), v in fam.items()}
    # meter-as-truth sensitivity
    mt_cols = [c for c in pt.columns if c.startswith("mt_")]
    sens = {str(b): summarise(bias[bias["size"] == b], mt_cols) for b in SENS_BIAS}
    # true trace summary
    true_cols = [c for c in true_df.columns if c != "PtID"]
    true_agg = summarise(true_df, true_cols)
    # version-1 link
    v1_path = os.path.join(OUT, "simulation_stats.json")
    v1 = None
    if os.path.exists(v1_path):
        with open(v1_path, encoding="utf-8") as f:
            v1s = json.load(f)
        v1 = {}
        for r in v1s["by_bias"]:
            b = -r["bias_pct"]
            if b in (-10, -20, -30):
                row = lk[lk.bias_pct == b].iloc[0]
                v1[str(b)] = {"v1_false_low_readings_per_day": r["false_low_alerts"]["per_person_per_day"]["median"],
                              "v1_missed_high200_readings_per_day": r["missed_high_alerts"]["per_person_per_day"]["median"],
                              "v2_false_low70_episodes_per_day": float(row["low70_false_per_day_median"]),
                              "v2_missed_high200_episodes_per_day": float(row["high200_missed_per_day_median"]),
                              "v2_skipped_corrections_per_day": float(row["skipped_per_day_median"])}
    # who is hurt most: outcomes at -20 % bias vs the person's own glucose pattern (computed here; participant_metrics.csv was not available)
    b20 = bias[bias["size"] == -20][["PtID", "skipped_pct", "low70_false_per_day", "changed_1_pct"]].merge(true_df, on="PtID")
    b20 = b20.merge(parts[["PtID", "arm", "age", "sex", "hba1c_randomisation"]], on="PtID", how="left")
    hurt = {}
    for y in ["skipped_pct", "low70_false_per_day"]:
        for x in ["true_tbr70_pct", "true_tar180_pct", "true_cv_pct", "true_mean_mgdl"]:
            d = b20[[x, y]].dropna()
            rho, pval = spearmanr(d[x], d[y])
            hurt[f"{y}_vs_{x}"] = {"spearman_rho": float(rho), "p": float(pval), "n": int(len(d))}
    # the same correlations against another agent's per-participant table, when it exists (analysis/participant_metrics.csv)
    hurt_pm, pm_path = None, os.path.join(OUT, "participant_metrics.csv")
    pm_cols = ["pct_below_70", "pct_above_180", "cv_pct", "mean_glucose"]
    if os.path.exists(pm_path):
        pm = pd.read_csv(pm_path)
        have = [c for c in pm_cols if c in pm.columns]
        if have and "PtID" in pm.columns:
            mm = b20.merge(pm[["PtID"] + have], on="PtID", how="inner", suffixes=("", "_pm"))
            hurt_pm = {"source": pm_path, "n_merged": int(len(mm))}
            for y in ["skipped_pct", "low70_false_per_day"]:
                for x in have:
                    d = mm[[x, y]].dropna()
                    rho, pval = spearmanr(d[x], d[y])
                    hurt_pm[f"{y}_vs_{x}"] = {"spearman_rho": float(rho), "p": float(pval), "n": int(len(d))}
            log("participant_metrics.csv found; correlations recomputed against its columns:", have)
    b20.to_csv(os.path.join(OUT, "simulation_v2_participants.csv"), index=False, float_format="%.4f")
    log("wrote", os.path.join(OUT, "simulation_v2_participants.csv"))

    fig25(lk)
    fig26(fam)
    fig27(deltas, lk)
    fig28(lk, true_agg)

    pooled = {str(b): {"n": int(len(deltas[b])), "median_u": float(np.median(deltas[b])), "q1_u": float(np.percentile(deltas[b], 25)),
                       "q3_u": float(np.percentile(deltas[b], 75)), "p10_u": float(np.percentile(deltas[b], 10)), "mean_u": float(np.mean(deltas[b]))}
              for b in HEADLINE_BIAS if len(deltas[b])}
    stats = {
        "method": {
            "grid": f"one slot per {SLOT_S} s; first reading per slot; NaN where there is no reading",
            "decision_1": "wizard records in the window with a typed glucose, ISF and target; truth = CGM reading within 5 min; dose = max(0, (G - target)/ISF - IOB) when G > 'correct above' level",
            "decision_2_3": f"episodes: >= {EPISODE_MIN_SLOTS} readings (15 min) beyond the threshold start one; >= 3 readings back in range (or no reading) end it; thresholds {[t[1] for t in THRESHOLDS]}",
            "matching": f"a faulted alert within +/- {MATCH_SLOTS * 5} min of a true start, or inside the true episode, detects it; others are false alerts",
            "faults": {"bias_pct": BIAS_LEVELS, "noise_sd_mgdl": NOISE_SD, "ar1_phi": AR_PHI, "drift_pct_at_day7": DRIFT_PCT, "dropout_pct": DROPOUT_PCT,
                       "gap_min": [GAP_MIN_SLOTS * 5, GAP_MAX_SLOTS * 5], "lag_min": LAG_MIN, "mixed": {"bias_pct": MIXED_BIAS, "ar_sd": MIXED_SD},
                       "draws": N_DRAWS, "seed": SEED, "device_clip": [DEVICE_MIN, DEVICE_MAX]},
            "risk_indices": "Kovatchev: f = 1.509 * ((ln BG)^1.084 - 5.381), r = 10 f^2; LBGI = mean(r | f < 0), HBGI = mean(r | f > 0)",
            "meter_truth_sensitivity": "truth = typed meter value, faulted = CGM reading * (1 + bias); subset rule in data.wizard.meter_truth_subset",
            "aggregation": "mean over draws per participant, then median (IQR) across participants; bootstrap CI resamples participants (1000)",
            "quick_mode": QUICK,
        },
        "data": {"participants": int(len(parts_list)), "cgm_readings": int(true_df.n_readings.sum()), "grid_collisions": int(sum(p["collisions"] for p in parts_list)),
                 "participant_days": int(true_df.n_days.sum()), "wizard": w_info, "decisions_analysed": int(true_df.n_decisions.sum()),
                 "meter_truth_decisions": int(true_df.n_meter_truth_decisions.sum()),
                 "true_episodes": {name: int(true_df[f"{name}_episodes"].sum()) for name, _, _ in THRESHOLDS}},
        "true_trace_summary": true_agg,
        "lookup_bias_csv": os.path.basename(LOOKUP_OUT),
        "headline_bias": {str(b): {c: lk.loc[lk.bias_pct == b, [f"{c}_median", f"{c}_q1", f"{c}_q3"]].iloc[0].round(4).tolist() for c in OUTCOME_COLS} for b in HEADLINE_BIAS},
        "bootstrap_ci_headline": ci,
        "pooled_dose_change": pooled,
        "fault_families": fam_json,
        "meter_truth_sensitivity": sens,
        "v1_link": v1,
        "who_is_hurt_most_at_minus20": hurt,
        "who_is_hurt_most_at_minus20_vs_participant_metrics_csv": hurt_pm,
        "runtime_s": round(time.time() - T0, 1),
    }
    with open(os.path.join(OUT, "simulation_v2_stats.json"), "w", encoding="utf-8") as f:
        json.dump(clean(stats), f, indent=1)
    log("wrote", os.path.join(OUT, "simulation_v2_stats.json"))
    # short console summary
    for b in HEADLINE_BIAS:
        row = lk[lk.bias_pct == b].iloc[0]
        log(f"bias {b:+d}%: skipped {row['skipped_pct_median']:.1f} % ({row['skipped_pct_q1']:.1f}-{row['skipped_pct_q3']:.1f}), "
            f"changed>1U {row['changed_1_pct_median']:.1f} %, false low/day {row['low70_false_per_day_median']:.2f} "
            f"({row['low70_false_per_day_q1']:.2f}-{row['low70_false_per_day_q3']:.2f}), missed low/day {row['low70_missed_per_day_median']:.3f}, "
            f"TIR {row['tir_pct_median']:.1f}, LBGI {row['lbgi_median']:.2f}, HBGI {row['hbgi_median']:.2f}")
    log("runtime", stats["runtime_s"], "s")


if __name__ == "__main__":
    main()
