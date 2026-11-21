"""
tail_comparison.py - how often does a normally working sensor make an error as large as the ones in
FDA problem reports? (BMEN 600 Group 24)

The paper has two sets of sensor errors:
  trial side   sensor vs fingerstick meter in normal use (REPLACE-BG trial, 226 adults, Dexcom G4).
  report side  sensor vs meter values written in FDA problem reports (MAUDE).
This script puts both on one axis and counts.

Words
  CGM    = continuous glucose monitor, a skin sensor that reads glucose every 5 minutes.
  pair   = one sensor value with the meter value taken at the same moment.
  error  = (sensor - meter) / meter x 100, in %. Negative = the sensor read low.
  95 % CI (confidence interval) = the range the true value most likely sits in. Here it comes from a
           bootstrap: the participants are re-drawn at random 2,000 times (fixed seed) and every count is redone.

Trial pairs: the verified fingerstick pairs of all 226 participants, built exactly as in accuracy_v2.py
(Set B, through preprocess.py and the cache). Two checks: the 77-person CGM+BGM arm in the randomised phase
(accuracy_v2 Set A), and all participants in the randomised phase only (the 26 trial weeks).

Report pairs, three groups, read from the per-pair files (not from the binned tables):
  Abbott and Dexcom death-or-injury reports: fda-maude/clean/text_extract_v3.jsonl, with the filters of
      fda-maude/scripts/brand_comparison.py (wrong-reading set, plausible values).
  Malfunction-only reports: fda-maude/clean/regex_v2_full.csv.gz, with the pair rule of
      fda-maude/scripts/report_regex_v2.py (both values stated).

Counts made
  1. Share of trial pairs with an error at or beyond fixed sizes (-20 ... -77 %, +20 ... +164 %).
  2. The same per 1,000 fingerstick checks, and the share of participants with at least one.
  3. Where the median reported error sits in the trial's error distribution (percentile).
  4. Share of report pairs inside the trial's central 95 % range of error.
  5. Fault shares defined the same way on both sides (false low, hidden low, floor reading).
  6. Summary of the error on both sides (median, quartiles, 2.5th and 97.5th percentiles).

Usage (from the repo root; plain `python`, about 15 seconds)
  python analysis/tail_comparison.py "Uncommitted Data/Raw Data Dump" analysis
  Argument 1 = raw data folder, argument 2 = output folder, argument 3 (optional) = cache folder.

Outputs (aggregates only; no per-participant or per-report files)
  <outdir>/tail_comparison_stats.json                 every number quoted in TAIL_COMPARISON.md
  <outdir>/figures/38_trial_vs_reported_error.png
  The tables of TAIL_COMPARISON.md are also printed at the end of the run.
"""
import json
import os
import sys
import time
import types
import warnings

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FDA = os.path.join(REPO, "fda-maude")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(FDA, "scripts"))

import numpy as np
import pandas as pd
import brand_comparison as bc    # FDA side: builds the death-or-injury pair set. Imported first: each module sets a plot style on import
import preprocess as pp          # trial side: shared cache and the verified pair set
import accuracy_v2 as av2        # trial side: participant bootstrap (Booter), colours, JSON cleaner. Imported last so its plot style is the one in use
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

T0 = time.time()
SEED = av2.SEED                  # 600, the seed accuracy_v2.py uses
N_BOOT = 2000                    # bootstrap resamples (participants drawn with replacement)
THRESHOLDS = [-20, -40, -50, -60, -66, -69, -77, 20, 44, 100, 164]   # error sizes in %, taken from the FDA memos and the simulations
QS = [2.5, 25, 50, 75, 97.5]     # percentiles in the summary; 2.5 and 97.5 are the edges of the central 95 % range
MARKS = [-12, -20]               # vertical marks in the figure: a constant low bias starts to change insulin doses near -12 % and clearly changes them at -20 % (FINDINGS.md, SIMULATION_V2.md)
BIN_W = 5                        # figure: width of one error bin, in points of %
X_MIN, X_MAX = -100, 200         # figure: error range drawn
EXPECT = {"trial_pairs": 168990, "trial_people": 226, "trial_mard_pct": 13.3,          # preprocess.verified_pairs()
          "abbott_serious": 7470, "dexcom_serious": 9189,                              # BRAND_COMPARISON.md
          "malfunction": 191112}                                                       # REGEX_V2_FULL_CORPUS.md
FDA_FILES = {
    "jsonl": os.path.join(FDA, "clean", "text_extract_v3.jsonl"),          # model-read values, one row per report
    "run_set": os.path.join(FDA, "clean", "run_set.csv.gz"),               # brand, tier and FDA problem codes of those reports
    "regex": os.path.join(FDA, "clean", "regex_run_set.csv"),              # pattern layer of the run set (needed by brand_comparison)
    "family_map": os.path.join(FDA, "results", "report", "tables", "d_problem_family_mapping.csv"),
    "regex_full": os.path.join(FDA, "clean", "regex_v2_full.csv.gz"),      # pattern-read values, every MAUDE CGM report
}

# Fault shares defined the same way on both sides. Each rule returns (fault, base): the share is fault / base.
FAULTS = [
    ("false_low_meter_70_or_above", "False low: sensor under 70 while the meter is 70 or above", "pairs with meter 70 or above",
     lambda s, m: ((s < 70) & (m >= 70), m >= 70)),
    ("false_low_meter_70_to_250", "False low, strict: sensor under 70 while the meter is 70 to 250", "pairs with meter 70 to 250",
     lambda s, m: ((s < 70) & (m >= 70) & (m <= 250), (m >= 70) & (m <= 250))),
    ("hidden_low_meter_under_70", "Hidden low: sensor 70 or above while the meter is under 70", "pairs with meter under 70",
     lambda s, m: ((s >= 70) & (m < 70), m < 70)),
    ("hidden_low_meter_under_54", "Hidden low, strict: sensor 70 or above while the meter is under 54", "pairs with meter under 54",
     lambda s, m: ((s >= 70) & (m < 54), m < 54)),
    ("floor_reading_meter_over_250", "Floor reading: sensor 40 or below while the meter is over 250", "pairs with meter over 250",
     lambda s, m: ((s <= 40) & (m > 250), m > 250)),
]

# Colours: the project palette. Abbott blue, Dexcom orange, malfunction aqua as in the FDA figures; the trial in neutral grey.
C_TRIAL, C_ABBOTT, C_DEXCOM, C_MALF = av2.INK2, av2.C_BLUE, av2.C_ORANGE, av2.C_AQUA
C_BAND = "#eceae3"               # light band for the trial's central 95 % range


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def err_pct(s, m):
    """Error in % of the meter value. Negative = the sensor read low."""
    return 100.0 * (s - m) / m


def tail_mask(s, m, thr):
    """True where the error is at or beyond thr: at or below a negative thr, at or above a positive thr.

    Written as 100 x (sensor - meter) against thr x meter. The trial values are whole numbers, so a pair
    that sits exactly on a threshold is counted exactly (no rounding from the division)."""
    d = 100.0 * (s - m)
    return d <= thr * m if thr < 0 else d >= thr * m


def side(thr):
    return "at or below" if thr < 0 else "at or above"


def ci3(r, scale=1.0):
    """Value and 95 % CI of a Booter result, optionally rescaled."""
    return {"value": r["value"] * scale, "ci_low": r["ci_low"] * scale, "ci_high": r["ci_high"] * scale}


def qkey(q):
    return f"p{q:g}"


# --------------------------------------------------------------------------
# Trial side
# --------------------------------------------------------------------------
class TrialSet:
    """One trial pair set with its participant bootstrap (accuracy_v2.Booter, 2,000 resamples, fixed seed)."""

    def __init__(self, df, label, short):
        self.label = label
        self.s = df.cgm.to_numpy(float)                    # sensor, mg/dL
        self.m = df.ref.to_numpy(float)                    # meter, mg/dL
        self.e = err_pct(self.s, self.m)
        self.n = len(df)
        self.ones = np.ones(self.n)
        self.bt = av2.Booter(df.PtID.to_numpy(), seed=SEED, n_boot=N_BOOT)
        per = df.groupby("PtID")
        span = per.day.max() - per.day.min()               # days from a person's first pair to the last one
        size = per.size()
        self.signed, self.boot_signed = self.quantiles(self.e)
        self.absolute, _ = self.quantiles(np.abs(self.e))
        self.info = {
            "label": label, "short": short, "n_pairs": int(self.n), "n_participants": int(self.bt.P),
            "mard_pct": float(df.abs_rel_err_pct.mean()), "bias_pct": float(df.rel_err_pct.mean()),
            "pairs_per_participant_median": float(size.median()), "pairs_per_participant_min_max": [int(size.min()), int(size.max())],
            "follow_up_days_median": float(span.median()), "follow_up_weeks_median": float(span.median() / 7.0),
            "follow_up_days_min_max": [int(span.min()), int(span.max())],
            "pair_time_tolerance_min": pp.METER_PAIR_TOL_S // 60,     # meter value matched to the nearest sensor reading within this many minutes
            "sensor_min_max_mgdl": [float(self.s.min()), float(self.s.max())], "meter_min_max_mgdl": [float(self.m.min()), float(self.m.max())],
        }

    def quantiles(self, values):
        """Pooled percentiles (QS) with a 95 % CI: the weighted percentile of each bootstrap resample."""
        v = np.asarray(values, float)
        point = np.percentile(v, QS)
        order = np.argsort(v, kind="stable")
        vs, cs = v[order], self.bt.codes[order]
        q = np.asarray(QS) / 100.0
        boot = np.empty((len(self.bt.W), len(QS)))
        for i, w in enumerate(self.bt.W):
            cw = np.cumsum(w[cs])
            boot[i] = vs[np.minimum(np.searchsorted(cw, q * cw[-1]), len(vs) - 1)]
        lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
        out = {qkey(qq): {"value": float(point[j]), "ci_low": float(lo[j]), "ci_high": float(hi[j])} for j, qq in enumerate(QS)}
        return out, boot

    def tail(self, thr):
        """Pairs with an error at or beyond thr: count, share, rate per 1,000 checks, participants with at least one."""
        k = tail_mask(self.s, self.m, thr).astype(float)
        n = int(k.sum())
        share = self.bt.ratio(k * 100.0, self.ones)
        has = (self.bt._sums(k) > 0).astype(float)          # 1 for a participant with at least one such pair
        has_boot = self.bt.W @ has / self.bt.P * 100.0      # every resample draws P participants
        return {"threshold_pct": float(thr), "side": side(thr), "n_pairs": n, "share_pct": ci3(share),
                "per_1000_checks": ci3(share, 10.0), "one_in_n_checks": (self.n / n) if n else None,
                "participants_with_at_least_one": int(has.sum()),
                "participants_share_pct": {"value": float(has.mean() * 100.0), "ci_low": float(np.percentile(has_boot, 2.5)),
                                           "ci_high": float(np.percentile(has_boot, 97.5))}}

    def summary(self):
        return {"n_pairs": int(self.n), "signed_error_pct": self.signed, "absolute_error_pct": self.absolute,
                "mean_absolute_error_pct": float(np.abs(self.e).mean()),
                "share_reads_low_pct": float((self.e < 0).mean() * 100.0), "share_reads_high_pct": float((self.e > 0).mean() * 100.0)}


def load_trial(root, cache):
    """The headline pair set of accuracy_v2.py (Set B) and two subsets, with the checks asked for."""
    pairs = pp.build_pairs(root, cache)
    part = pp.load_participants(root, cache)
    b = pairs["verified"].merge(part[["PtID", "arm", "randomisation_day"]], on="PtID", how="left")
    b["randomised"] = b.day >= b.randomisation_day                  # same rule as accuracy_v2.py
    mard = float(b.abs_rel_err_pct.mean())
    log(f"trial pairs: {len(b):,} from {b.PtID.nunique()} people, MARD {mard:.2f} %")
    if len(b) != EXPECT["trial_pairs"] or b.PtID.nunique() != EXPECT["trial_people"] or round(mard, 1) != EXPECT["trial_mard_pct"]:
        sys.exit(f"STOP: the trial pair set is not the expected one ({EXPECT['trial_pairs']:,} pairs, {EXPECT['trial_people']} people, "
                 f"MARD {EXPECT['trial_mard_pct']} %). Found {len(b):,} pairs, {b.PtID.nunique()} people, MARD {mard:.2f} %.")
    arm = b[(b.arm.astype(str) == "CGM+BGM") & b.randomised]        # accuracy_v2 Set A
    rand = b[b.randomised]
    return {"trial_all": TrialSet(b, "All verified fingerstick pairs (run-in and randomised phase)", "Trial, all pairs"),
            "trial_arm": TrialSet(arm, "Check: CGM+BGM arm, randomised phase", "Trial, arm check"),
            "trial_randomised": TrialSet(rand, "Check: all participants, randomised phase only (26 trial weeks)", "Trial, 26 weeks only")}


# --------------------------------------------------------------------------
# Report side
# --------------------------------------------------------------------------
def load_report_pairs():
    """The three report pair sets, from the per-pair files. Returns (groups, source notes)."""
    missing = [p for p in FDA_FILES.values() if not os.path.exists(p)]
    if missing:
        sys.exit("STOP: per-pair report files are missing:\n  " + "\n  ".join(missing) +
                 "\nThey are not in git; copy fda-maude/clean/ by hand. The binned tables in fda-maude/results/text/tables/ "
                 "(h_error_distribution.csv, g_brand_error_bins.csv) hold 10-point bins only and are not used by this script.")
    # 1. Death-or-injury pairs: the model-read values with the filters of brand_comparison.py.
    #    Wrong-reading set (by text or by FDA code), serious tier, sensor 20-600 and meter 20-1,500 mg/dL.
    #    The patient age and sex tables are not needed here, so they are not read (serious=None, sample_parquet=None).
    args = types.SimpleNamespace(jsonl=FDA_FILES["jsonl"], run_set=FDA_FILES["run_set"], regex=FDA_FILES["regex"],
                                 family_map=FDA_FILES["family_map"], serious=None, sample_parquet=None, max_rows=None)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        df = bc.build_frame(args)
        p, n_implausible = bc.pairs_from(df)
    pw = p[p["wr"] & (p["split"] == "serious")]
    # 2. Malfunction-only pairs: the pattern-read values. Same rule as report_regex_v2.load_full():
    #    a pair = both values stated; group = FDA event type Malfunction.
    rx = pd.read_csv(FDA_FILES["regex_full"], usecols=["event_group", "brand", "sensor_value", "meter_value"],
                     dtype={"event_group": "category", "brand": "category"})
    rxp = rx[rx.sensor_value.notna() & rx.meter_value.notna()]
    malf = rxp[rxp.event_group == "malfunction"]
    ser_rx = rxp[rxp.event_group.isin(["death", "injury"])]
    log(f"report pairs: death-or-injury (model-read) {len(pw):,}; malfunction-only (pattern-read) {len(malf):,}")

    def group(label, short, color, s, m, source, extra=None):
        s, m = np.asarray(s, float), np.asarray(m, float)
        return {"label": label, "short": short, "color": color, "s": s, "m": m, "e": err_pct(s, m), "source": source, "extra": extra or {}}

    a, d = pw[pw.brand == "Abbott"], pw[pw.brand == "Dexcom"]
    src_model = "fda-maude/clean/text_extract_v3.jsonl through brand_comparison.build_frame() and pairs_from(): serious tier, wrong-reading set, plausible values"
    src_regex = "fda-maude/clean/regex_v2_full.csv.gz: event group malfunction, both values stated (the rule of report_regex_v2.load_full())"
    groups = {
        "abbott_serious": group("FDA reports: Abbott, death or injury", "Abbott death or injury", C_ABBOTT, a.sensor, a.meter, src_model,
                                {"event_type_counts": a.event_type.value_counts().to_dict(), "pairs_with_equal_values": int((a.sensor == a.meter).sum())}),
        "dexcom_serious": group("FDA reports: Dexcom, death or injury", "Dexcom death or injury", C_DEXCOM, d.sensor, d.meter, src_model,
                                {"event_type_counts": d.event_type.value_counts().to_dict(), "pairs_with_equal_values": int((d.sensor == d.meter).sum())}),
        "malfunction": group("FDA reports: malfunction only (no harm coded)", "Malfunction only", C_MALF, malf.sensor_value, malf.meter_value, src_regex,
                             {"pairs_by_brand": {str(k): int(v) for k, v in malf.brand.value_counts().items() if v},
                              "abbott_share_pct": float((malf.brand == "Abbott").mean() * 100.0)}),
    }
    notes = {"per_pair_files_used": True, "binned_fallback_used": False, "files": {k: os.path.relpath(v, REPO).replace("\\", "/") for k, v in FDA_FILES.items()},
             "implausible_model_pairs_dropped": int(n_implausible),
             "all_serious_wrong_reading_pairs_model_read": int(len(pw)),
             "pattern_read_counts_of_the_serious_groups_for_reference": {"Abbott": int((ser_rx.brand == "Abbott").sum()), "Dexcom": int((ser_rx.brand == "Dexcom").sum())}}
    return groups, notes


def group_quantiles(v):
    return {qkey(q): float(x) for q, x in zip(QS, np.percentile(v, QS))}


def group_summary(g):
    e = g["e"]
    return {"n_pairs": int(len(e)), "signed_error_pct": group_quantiles(e), "absolute_error_pct": group_quantiles(np.abs(e)),
            "mean_absolute_error_pct": float(np.abs(e).mean()),
            "share_reads_low_pct": float((e < 0).mean() * 100.0), "share_reads_high_pct": float((e > 0).mean() * 100.0),
            "median_sensor_mgdl": float(np.median(g["s"])), "median_meter_mgdl": float(np.median(g["m"]))}


# --------------------------------------------------------------------------
# The six counts
# --------------------------------------------------------------------------
def tails_block(trials, groups):
    """Items 1 and 2: errors at or beyond each fixed size, on the trial side and on the report side."""
    out = {k: [t.tail(thr) for thr in THRESHOLDS] for k, t in trials.items()}
    out["reports"] = {}
    for gk, g in groups.items():
        rows = []
        for thr in THRESHOLDS:
            k = tail_mask(g["s"], g["m"], thr)
            rows.append({"threshold_pct": float(thr), "side": side(thr), "n_pairs": int(k.sum()), "share_pct": float(k.mean() * 100.0)})
        out["reports"][gk] = rows
    return out


def medians_block(trials, groups):
    """Item 3: the median reported error of each group and direction, and where it sits in the trial distribution."""
    rows = []
    for gk, g in groups.items():
        e = g["e"]
        for direction, mask in (("reads low", e < 0), ("reads high", e > 0)):
            med = float(np.median(e[mask]))
            row = {"group": gk, "label": g["short"], "direction": direction, "n_report_pairs": int(mask.sum()),
                   "share_of_group_pairs_pct": float(mask.mean() * 100.0), "median_reported_error_pct": med}
            for tk, t in trials.items():
                r = t.tail(med)                                   # trial pairs at least as extreme as the reported median
                pct = r["share_pct"]["value"] if med < 0 else 100.0 - r["share_pct"]["value"]
                row[tk] = {"trial_percentile": pct, "trial_pairs_this_extreme_or_more": r["n_pairs"],
                           "trial_share_this_extreme_or_more_pct": r["share_pct"], "one_in_n_checks": r["one_in_n_checks"],
                           "participants_with_at_least_one": r["participants_with_at_least_one"],
                           "participants_share_pct": r["participants_share_pct"]}
            rows.append(row)
    return rows


def central_block(trials, groups):
    """Item 4: share of report pairs inside the trial's central 95 % range (2.5th to 97.5th percentile of the error).

    The interval comes from the trial bootstrap: the range is redone in each resample, the report pairs stay fixed."""
    out = {}
    j_lo, j_hi = QS.index(2.5), QS.index(97.5)
    for tk, t in trials.items():
        lo, hi = t.signed["p2.5"]["value"], t.signed["p97.5"]["value"]
        lo_b, hi_b = t.boot_signed[:, j_lo], t.boot_signed[:, j_hi]
        res = {"range_low_pct": t.signed["p2.5"], "range_high_pct": t.signed["p97.5"], "groups": {}}
        for gk, g in groups.items():
            es = np.sort(g["e"])
            inside_b = (np.searchsorted(es, hi_b, "right") - np.searchsorted(es, lo_b, "left")) / len(es) * 100.0
            inside = (es >= lo) & (es <= hi)
            res["groups"][gk] = {"n_pairs": int(len(es)), "n_inside": int(inside.sum()),
                                 "share_inside_pct": {"value": float(inside.mean() * 100.0), "ci_low": float(np.percentile(inside_b, 2.5)),
                                                      "ci_high": float(np.percentile(inside_b, 97.5))},
                                 "share_below_range_pct": float((es < lo).mean() * 100.0), "share_above_range_pct": float((es > hi).mean() * 100.0)}
        out[tk] = res
    return out


def faults_block(trials, groups):
    """Item 5: the same fault rules on both sides."""
    rows = []
    for key, label, base_label, rule in FAULTS:
        row = {"fault": key, "label": label, "share_of": base_label}
        for tk, t in trials.items():
            fault, base = rule(t.s, t.m)
            r = t.bt.ratio(fault * 100.0, base.astype(float))
            row[tk] = {"n_fault": int(fault.sum()), "n_base": int(base.sum()), "share_pct": ci3(r), "participants_with_base_pairs": r["n_participants"]}
        for gk, g in groups.items():
            fault, base = rule(g["s"], g["m"])
            row[gk] = {"n_fault": int(fault.sum()), "n_base": int(base.sum()), "share_pct": float(fault.sum() / base.sum() * 100.0) if base.sum() else None}
        rows.append(row)
    return rows


# --------------------------------------------------------------------------
# Figure 38
# --------------------------------------------------------------------------
def figure_block(trial, groups):
    """Binned shares for the figure (share of each set's pairs per 5-point error bin) and the share beyond the drawn range."""
    edges = np.arange(X_MIN, X_MAX + BIN_W, BIN_W)
    out = {"bin_edges_pct": [float(x) for x in edges], "sets": {}}
    for key, e in [("trial_all", trial.e)] + [(gk, g["e"]) for gk, g in groups.items()]:
        share = np.histogram(e, bins=edges)[0] / len(e) * 100.0
        out["sets"][key] = {"share_per_bin_pct": [float(x) for x in share], "share_above_drawn_range_pct": float((e > X_MAX).mean() * 100.0),
                            "share_below_drawn_range_pct": float((e < X_MIN).mean() * 100.0)}
    return out


def figure(stats, groups, outdir):
    """Figure 38: four stacked histograms on one error axis (trial, then the three report groups)."""
    fb = stats["figure_38"]
    edges = np.asarray(fb["bin_edges_pct"])
    cen = stats["inside_trial_central_95"]["trial_all"]
    lo, hi = cen["range_low_pct"]["value"], cen["range_high_pct"]["value"]
    med = {(r["group"], r["direction"]): r["median_reported_error_pct"] for r in stats["median_reported_error_in_trial"]}
    t = stats["pair_sets"]["trial_all"]
    panels = [("trial_all", C_TRIAL, f"Trial, normal use (Dexcom G4): {t['n_pairs']:,} pairs from {t['n_participants']} people")]
    panels += [(gk, g["color"], f"{g['label']}: {stats['pair_sets'][gk]['n_pairs']:,} pairs") for gk, g in groups.items()]
    box = dict(facecolor=av2.SURFACE, edgecolor="none", pad=1.5)          # hides the grid line behind a label
    small = dict(fontsize=8.5, color=av2.INK2, linespacing=1.35, bbox=box)

    fig, axes = plt.subplots(len(panels), 1, figsize=(6.5, 7.4), sharex=True)
    for ax, (key, color, title) in zip(axes, panels):
        share = np.asarray(fb["sets"][key]["share_per_bin_pct"])
        top = share.max() * 1.34                           # head room above the tallest bar for the labels
        ax.axvspan(lo, hi, color=C_BAND, lw=0, zorder=0)
        ax.stairs(share, edges, fill=True, color=color, lw=0, zorder=2)
        for x in MARKS:
            ax.axvline(x, color=av2.INK, lw=0.9, ls=(0, (4, 2.5)), zorder=3)
        ax.set_ylim(0, top)
        ax.set_title(title, fontsize=9.5)
        ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, integer=True))
        above = fb["sets"][key]["share_above_drawn_range_pct"]
        if key == "trial_all":
            ax.text(-21.5, top * 0.97, "-20 %", ha="right", va="top", fontsize=8.5, color=av2.INK, bbox=dict(box, facecolor=C_BAND))
            ax.text(-10.5, top * 0.97, "-12 %", ha="left", va="top", fontsize=8.5, color=av2.INK, bbox=dict(box, facecolor=C_BAND))
            note = (f"grey band = middle 95 % of trial pairs\n({lo:+.0f} % to {hi:+.0f} %)\n"
                    f"{above:.2f} % of pairs above +{X_MAX} % (not drawn)")
            ax.text(0.485, 0.93, note, transform=ax.transAxes, ha="left", va="top", **small)
        else:
            inside = cen["groups"][key]["share_inside_pct"]["value"]
            m_lo, m_hi = med[(key, "reads low")], med[(key, "reads high")]
            y = top * 0.945
            ax.plot([m_lo, m_hi], [y, y], ls="", marker="v", ms=6.5, color=av2.INK, mec=av2.SURFACE, mew=0.8, zorder=4)
            ax.text(m_lo + 4, y, f"{m_lo:.0f} %", ha="left", va="center", fontsize=8.5, color=av2.INK, bbox=box)
            ax.text(m_hi - 4, y, f"{m_hi:+.0f} %", ha="right", va="center", fontsize=8.5, color=av2.INK, bbox=box)
            note = f"{inside:.1f} % of pairs inside the grey band\n{above:.0f} % of pairs above +{X_MAX} % (not drawn)"
            ax.text(0.485, 0.80, note, transform=ax.transAxes, ha="left", va="top", **small)
    axes[-1].set_xlim(X_MIN, X_MAX)
    axes[-1].set_xticks(np.arange(X_MIN, X_MAX + 1, 50))
    axes[-1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: "0" if x == 0 else f"{x:+.0f}"))
    axes[-1].set_xlabel("sensor error, % of the meter value (negative = the sensor read low)")
    fig.supylabel(f"share of the set's pairs in each {BIN_W}-point error bin (%)", fontsize=9.5, color=av2.INK2, x=0.015)
    fig.text(0.02, 0.993, "Sensor error in normal use and in FDA problem reports, on one axis", ha="left", va="top",
             fontsize=10.5, fontweight="semibold", color=av2.INK)
    fig.text(0.02, 0.962, "Each panel has its own vertical scale. Dashed lines: a constant low bias starts to change insulin doses\n"
             "near -12 % and clearly changes them at -20 % (simulation). Triangles: median reported error when the\n"
             "sensor read low and when it read high.", ha="left", va="top", fontsize=8.5, color=av2.INK2, linespacing=1.35)
    fig.tight_layout(rect=(0.02, 0, 1, 0.905), h_pad=1.0)
    path = os.path.join(outdir, "figures", "38_trial_vs_reported_error.png")
    fig.savefig(path, dpi=200)                             # 200 dpi like figures 25 to 37
    plt.close(fig)
    log("wrote", path)


# --------------------------------------------------------------------------
# Markdown tables (printed at the end; pasted into TAIL_COMPARISON.md)
# --------------------------------------------------------------------------
def f_pct(x):
    """A share in %, with more digits for small values."""
    if x is None:
        return "n/a"
    return f"{x:.1f}" if x >= 10 else f"{x:.2f}" if x >= 0.1 else f"{x:.3f}"


def f_ci(d):
    return f"{f_pct(d['value'])} ({f_pct(d['ci_low'])} to {f_pct(d['ci_high'])})"


def f_pctile(x):
    return f"{x:.3f}" if x < 1 else f"{x:.2f}"


def f_one_in(x):
    return "none found" if x is None else f"{x:,.0f}"


def f_err(x):
    return f"{x:+.0f}" if abs(x) >= 10 else f"{x:+.1f}"


def tables_markdown(st):
    """The tables of TAIL_COMPARISON.md, built from the stats only."""
    ps, L = st["pair_sets"], []
    gks = ["abbott_serious", "dexcom_serious", "malfunction"]
    n_all, n_rand = ps["trial_all"]["n_participants"], ps["trial_randomised"]["n_participants"]
    L.append("Pair sets\n")
    L.append("| Side | Pair set | Pairs | People | Pairs per person, median | Days from a person's first to last pair, median |")
    L.append("|---|---|---|---|---|---|")
    for tk in ("trial_all", "trial_arm", "trial_randomised"):
        p = ps[tk]
        L.append(f"| Trial | {p['label']} | {p['n_pairs']:,} | {p['n_participants']} | {p['pairs_per_participant_median']:.0f} | "
                 f"{p['follow_up_days_median']:.0f} (about {p['follow_up_weeks_median']:.0f} weeks) |")
    for gk in gks:
        L.append(f"| Reports | {ps[gk]['label']} | {ps[gk]['n_pairs']:,} | - | - | - |")

    L.append("\nTable 1. Errors at or beyond a fixed size\n")
    L.append(f"| Error | Trial pairs | Share of trial pairs, % (95 % CI) | Per 1,000 checks (95 % CI) | People with at least one: all pairs, of {n_all} | "
             f"People with at least one: 26 trial weeks only, of {n_rand} | Arm check: share, % | Abbott D/I, % | Dexcom D/I, % | Malfunction, % |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    tl = st["errors_at_or_beyond"]
    for i, thr in enumerate(THRESHOLDS):
        r, a, w = tl["trial_all"][i], tl["trial_arm"][i], tl["trial_randomised"][i]
        rep = " | ".join(f_pct(tl["reports"][gk][i]["share_pct"]) for gk in gks)
        L.append(f"| {thr:+d} % or {'lower' if thr < 0 else 'higher'} | {r['n_pairs']:,} | {f_ci(r['share_pct'])} | {f_ci(r['per_1000_checks'])} | "
                 f"{r['participants_with_at_least_one']} ({r['participants_share_pct']['value']:.0f} %) | "
                 f"{w['participants_with_at_least_one']} ({w['participants_share_pct']['value']:.0f} %) | {f_pct(a['share_pct']['value'])} | {rep} |")

    L.append("\nTable 2. Where the median reported error sits in the trial\n")
    L.append(f"| Report group | Direction | Report pairs | Median reported error, % | Trial percentile | Trial pairs this extreme or more | "
             f"Share of trial pairs, % (95 % CI) | 1 check in | People with at least one, of {n_all} | Arm check: share, % |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in st["median_reported_error_in_trial"]:
        t, a = r["trial_all"], r["trial_arm"]
        L.append(f"| {r['label']} | {r['direction']} | {r['n_report_pairs']:,} | {r['median_reported_error_pct']:+.1f} | {f_pctile(t['trial_percentile'])} | "
                 f"{t['trial_pairs_this_extreme_or_more']:,} | {f_ci(t['trial_share_this_extreme_or_more_pct'])} | {f_one_in(t['one_in_n_checks'])} | "
                 f"{t['participants_with_at_least_one']} ({t['participants_share_pct']['value']:.0f} %) | {f_pct(a['trial_share_this_extreme_or_more_pct']['value'])} |")

    L.append("\nTable 3. Summary of the error, and report pairs inside the trial's central 95 % range\n")
    L.append("| Set | Signed error, %: 2.5th | 25th | Median | 75th | 97.5th | Absolute error, %: 2.5th | 25th | Median | 75th | 97.5th | Pairs inside the trial range, % (interval) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    sm, cen = st["summary"], st["inside_trial_central_95"]["trial_all"]
    for key in ("trial_all", "trial_arm"):
        s = sm[key]
        L.append(f"| {ps[key]['short']} | " + " | ".join(f_err(s["signed_error_pct"][qkey(q)]["value"]) for q in QS) + " | "
                 + " | ".join(f"{s['absolute_error_pct'][qkey(q)]['value']:.1f}" for q in QS) + " | - |")
    for gk in gks:
        s = sm[gk]
        L.append(f"| {ps[gk]['short']} | " + " | ".join(f_err(s["signed_error_pct"][qkey(q)]) for q in QS) + " | "
                 + " | ".join(f"{s['absolute_error_pct'][qkey(q)]:.1f}" for q in QS) + f" | {f_ci(cen['groups'][gk]['share_inside_pct'])} |")
    s = sm["trial_all"]["signed_error_pct"]
    L.append(f"\nTrial central 95 % range: {s['p2.5']['value']:+.1f} % (95 % CI {s['p2.5']['ci_low']:+.1f} to {s['p2.5']['ci_high']:+.1f}) "
             f"to {s['p97.5']['value']:+.1f} % (95 % CI {s['p97.5']['ci_low']:+.1f} to {s['p97.5']['ci_high']:+.1f}).")

    L.append("\nTable 4. The same fault rule on both sides\n")
    L.append("| Fault | Share of | Trial: pairs | Trial, % (95 % CI) | Arm check, % | Abbott D/I, % (pairs) | Dexcom D/I, % (pairs) | Malfunction, % (pairs) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in st["fault_shares"]:
        t = r["trial_all"]
        rep = " | ".join(f"{f_pct(r[gk]['share_pct'])} ({r[gk]['n_fault']:,} of {r[gk]['n_base']:,})" for gk in gks)
        L.append(f"| {r['label']} | {r['share_of']} | {t['n_fault']:,} of {t['n_base']:,} | {f_ci(t['share_pct'])} | {f_pct(r['trial_arm']['share_pct']['value'])} | {rep} |")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(root, outdir, cache):
    os.makedirs(os.path.join(outdir, "figures"), exist_ok=True)
    trials = load_trial(root, cache)
    groups, notes = load_report_pairs()
    trial = trials["trial_all"]

    pair_sets = {k: t.info for k, t in trials.items()}
    for gk, g in groups.items():
        pair_sets[gk] = {"label": g["label"], "short": g["short"], "n_pairs": int(len(g["e"])), "source": g["source"], **g["extra"]}
    checks = {
        "trial_pairs": {"expected": EXPECT["trial_pairs"], "found": trial.n, "ok": trial.n == EXPECT["trial_pairs"]},
        "trial_participants": {"expected": EXPECT["trial_people"], "found": trial.bt.P, "ok": trial.bt.P == EXPECT["trial_people"]},
        "trial_mard_pct": {"expected": EXPECT["trial_mard_pct"], "found": trial.info["mard_pct"], "ok": round(trial.info["mard_pct"], 1) == EXPECT["trial_mard_pct"]},
    }
    for gk in groups:
        n = pair_sets[gk]["n_pairs"]
        checks[f"{gk}_pairs"] = {"expected": EXPECT[gk], "found": n, "difference": n - EXPECT[gk], "ok": n == EXPECT[gk]}
        if n != EXPECT[gk]:
            log(f"WARNING: {gk} has {n:,} pairs, the FDA memo states {EXPECT[gk]:,} (difference {n - EXPECT[gk]:+,})")

    stats = {
        "generated": time.strftime("%Y-%m-%d %H:%M"), "seed": SEED, "n_boot": N_BOOT, "cache_version": pp.CACHE_VERSION,
        "definitions": {
            "error": "(sensor - meter) / meter x 100, in %; negative = the sensor read low",
            "ci": f"trial values: 95 % CI = 2.5th to 97.5th percentile of {N_BOOT:,} bootstrap resamples of participants (seed {SEED}); report values have no CI (they are all the reports found, not a sample)",
            "trial_all": "verified fingerstick pairs, study window, all 226 participants, run-in and randomised phase (accuracy_v2.py Set B = preprocess.verified_pairs())",
            "trial_arm": "the same pairs, CGM+BGM arm, randomised phase only (accuracy_v2.py Set A)",
            "trial_randomised": "the same pairs, all participants, randomised phase only (the 26 trial weeks)",
            "report_pair": "a report whose text states both the sensor value and the meter value; first pair of the report",
            "per_1000_checks": "share of pairs x 10: such errors per 1,000 fingerstick checks",
            "participants_with_at_least_one": "participants with one or more such pairs in the set; the time base is follow_up_days_median of the set",
            "trial_percentile": "share of trial pairs with an error at or below the value (reads low), or 100 minus the share at or above it (reads high)",
            "reads_low_and_reads_high": "reads low = error below 0; reads high = error above 0; pairs with equal values are in neither",
            "central_95_range": "2.5th to 97.5th percentile of the signed error of the trial set",
            "thresholds": "fixed error sizes in %: -66 = median of malfunction-only pairs; -69 and +164 = false-low and hidden-low sizes of the three-fault simulation; -77 = Abbott reads-low median; +44 = Dexcom median",
        },
        "report_source": notes, "pair_sets": pair_sets, "checks": checks,
    }
    log("counts 1-2: errors at or beyond fixed sizes")
    stats["errors_at_or_beyond"] = tails_block(trials, groups)
    log("count 3: median reported error in the trial distribution")
    stats["median_reported_error_in_trial"] = medians_block(trials, groups)
    log("count 4: report pairs inside the trial's central 95 % range")
    stats["inside_trial_central_95"] = central_block(trials, groups)
    log("count 5: like-for-like fault shares")
    stats["fault_shares"] = faults_block(trials, groups)
    log("count 6: summary")
    stats["summary"] = {**{k: t.summary() for k, t in trials.items()}, **{gk: group_summary(g) for gk, g in groups.items()}}
    stats["figure_38"] = {"bin_width_pct": BIN_W, "marks_pct": MARKS, **figure_block(trial, groups)}
    stats = av2.clean(stats)
    figure(stats, groups, outdir)

    stats["runtime_s"] = round(time.time() - T0, 1)
    path = os.path.join(outdir, "tail_comparison_stats.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    log("wrote", path)
    print("\n" + tables_markdown(stats))
    log("done in", stats["runtime_s"], "s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: python analysis/tail_comparison.py "Uncommitted Data/Raw Data Dump" analysis [cache folder]')
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else pp.DEFAULT_CACHE)
