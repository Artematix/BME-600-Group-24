"""
Three-fault simulation for BMEN 600 Group 24.

Question: what happens to treatment decisions when a CGM sensor fails the way the FDA reports describe?

Version 2 (analysis/simulation_v2.py) tested a constant bias on the whole trace. The FDA report texts
show three faults that come in episodes and depend on the true glucose:
  1. False low     true glucose 70-250 mg/dL, the sensor reads far too low.
  2. Hidden low    true glucose under 54 mg/dL, the sensor reads normal or high.
  3. Floor-pinned  true glucose over 250 mg/dL, the sensor shows its lowest value.

What this script does
  - Reads the fault sizes from the FDA tables (fda-maude/results/text/tables/h_*.csv and g_*.csv).
  - For each participant, fault and episode length (2, 6, 12 hours) it draws random episode starts
    (fixed seed) at times when the true glucose is inside the fault's range.
  - One episode at a time. Inside the episode the fault changes every reading whose true glucose is
    inside the fault's range. All other readings show the true value.
  - Counts changed decisions per episode: sugar eaten without need, insulin correction doses withheld
    or reduced, low alerts not shown, false low alerts, high glucose not displayed as high.
  - Reference rows: a constant bias of -20, -40 and -66 % in the same episode windows, and no fault.

Everything else is reused from version 2 (imported, not changed): data loading and cache, the 5-minute
grid, "true glucose" = the recorded CGM trace, the dose calculator, the episode and alert rules, and the
per-participant then median-and-quartiles summary.

Usage (from the repo root; plain `python`)
  python analysis/simulation_three_faults.py "Uncommitted Data/Raw Data Dump" analysis
  Argument 1 = data folder, argument 2 = output folder, argument 3 (optional) = cache folder.
  Set the environment variable SIM_3F_QUICK=1 for a 20-participant test run with 50 starts.

Outputs (under the output folder; aggregates only, no per-participant files)
  simulation_three_faults_stats.json    every number quoted in SIMULATION_THREE_FAULTS.md
  simulation_three_faults_lookup.csv    one row per fault x episode length x size case
  figures/36_three_faults_outcomes.png, figures/37_three_faults_by_episode_length.png
"""
import json
import os
import sys
import time

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import pandas as pd
import simulation_v2 as v2      # reused: loaders, grid, dose rule, episode rules, summary, plot style
import matplotlib.pyplot as plt

OUT = v2.OUT
FDA_TABLES = os.path.join(os.path.dirname(HERE), "fda-maude", "results", "text", "tables")
QUICK = os.environ.get("SIM_3F_QUICK", "") == "1"

# --- settings -------------------------------------------------------------------
SEED = 20261120
SLOTS_PER_H = 3600 // v2.SLOT_S                 # 12 readings per hour
LENGTHS_H = [2, 6, 12]                          # episode lengths in hours
N_STARTS = 50 if QUICK else 200                 # random episode starts per participant, fault and length
PAD = 12                                        # 60 min of true trace kept on each side of an episode (alert matching needs context)
SEP = 8                                         # empty slots between episodes when they are checked in one pass
FLOOR = v2.DEVICE_MIN                           # 39 mg/dL: lowest value version 2 lets a sensor show
SUGAR_BELOW = 70                                # the person eats sugar when the sensor shows under this
SUGAR_G = 15                                    # grams of fast sugar per treatment
SUGAR_GAP_SLOTS = 3                             # at most one treatment every 15 min
DOSE_CHANGE_U = v2.CHANGE_U[0]                  # 0.5 U: a dose counts as reduced when it drops by more than this
REF_BIAS = [-20, -40, -66]                      # reference: constant bias, percent
FAULTS = ["false_low", "hidden_low", "floor_pinned"]
FAULT_LABEL = {"false_low": "False low", "hidden_low": "Hidden low", "floor_pinned": "Floor-pinned"}
FAULT_RANGE = {"false_low": "true glucose 70 to 250 mg/dL", "hidden_low": "true glucose under 54 mg/dL",
               "floor_pinned": "true glucose over 250 mg/dL"}
EP_THR = [t for t in v2.THRESHOLDS if t[0] in ("low70", "low54", "high180")]
OUTCOMES = ["sugar_unneeded_n", "sugar_unneeded_g", "dose_lower_n", "dose_withheld_n", "dose_lower_u",
            "insulin_true_low_n", "insulin_true_low_u", "low70_missed_n", "low54_missed_n", "min_under54_no_alert",
            "low70_false_n", "low54_false_n", "high180_missed_n", "min_over180_not_shown"]
DOSE_OUTCOMES = ["dose_lower_n", "dose_withheld_n", "dose_lower_u", "insulin_true_low_n", "insulin_true_low_u"]
OUTCOME_TEXT = {
    "sugar_unneeded_n": "sugar treatments taken while the true glucose was 70 or above (count)",
    "sugar_unneeded_g": "the same in grams (15 g each)",
    "dose_lower_n": "correction doses withheld or reduced: the dose fell by more than 0.5 U (count)",
    "dose_withheld_n": "correction doses withheld: true dose above 0.5 U, faulted dose 0 (count; part of dose_lower_n)",
    "dose_lower_u": "insulin not given, summed over all decisions with a lower dose (units)",
    "insulin_true_low_n": "decisions where the true glucose was under 70 and the fault raised the dose (count)",
    "insulin_true_low_u": "extra insulin at those decisions (units)",
    "low70_missed_n": "true low episodes under 70 with no low alert shown (count)",
    "low54_missed_n": "true low episodes under 54 with no under-54 alert shown (count)",
    "min_under54_no_alert": "minutes with true glucose under 54 while the sensor showed 70 or above",
    "low70_false_n": "low alerts under 70 shown with no true low episode (count)",
    "low54_false_n": "low alerts under 54 shown with no true episode under 54 (count)",
    "high180_missed_n": "true high episodes over 180 never shown as high (count)",
    "min_over180_not_shown": "minutes with true glucose over 180 while the sensor showed 180 or under",
}
log = v2.log


# --------------------------------------------------------------------------------
# Fault sizes from the FDA tables
# --------------------------------------------------------------------------------
def binned_quantile(lo, hi, counts, q):
    """Quantile of binned data. Linear inside the bin that holds it. Bins must be sorted from low to high."""
    cum = np.cumsum(counts)
    target = q * cum[-1]
    i = int(np.searchsorted(cum, target))
    before = cum[i - 1] if i else 0
    return float(lo[i] + (hi[i] - lo[i]) * (target - before) / counts[i])


def read_fda_sizes():
    """Fault sizes and the FDA numbers that support them. Every value is read from the FDA tables."""
    def need(name):
        path = os.path.join(FDA_TABLES, name)
        if not os.path.exists(path):
            sys.exit(f"FDA table not found: {path}. The fault sizes are read from it.")
        return pd.read_csv(path)

    h = need("h_malf_vs_serious_errors.csv")
    dist = need("h_error_distribution.csv")
    g = need("g_brand_error_sizes.csv")
    grad = need("h_harm_gradient.csv")

    def hrow(brand, group):
        return h[(h.brand == brand) & (h.group == group)].iloc[0]

    def grow(brand, pairs):
        return g[(g.tier == "serious") & (g.brand == brand) & (g.pairs == pairs)].iloc[0]

    malf, ser = hrow("All", "malfunction"), hrow("All", "serious")
    # False low. No table holds "meter 70 to 250 and sensor under 70" exactly. Nearest: malfunction-only pairs
    # where the sensor read below the meter. The table gives their median. Quartiles are interpolated from the
    # 10-point error bins of the same pairs.
    d = dist[(dist.brand == "All") & (dist.group == "malfunction") & dist.error_pct_bin.str.contains(" to ")].copy()
    d["lo"] = d.error_pct_bin.str.split(" to ").str[0].astype(float)
    d["hi"] = d.error_pct_bin.str.split(" to ").str[1].astype(float)
    d = d[d.hi <= 0].sort_values("lo")
    fl_q1, fl_q3 = (round(binned_quantile(d.lo.to_numpy(), d.hi.to_numpy(), d.pairs.to_numpy(), q), 1) for q in (0.25, 0.75))
    fl_med_binned = round(binned_quantile(d.lo.to_numpy(), d.hi.to_numpy(), d.pairs.to_numpy(), 0.5), 1)
    # Hidden low. No table holds "meter under 54 (or under 70) and sensor 70 or above" exactly. Nearest: serious
    # pairs where the sensor read above the meter.
    up = grow("All", "sensor above meter")
    # Floor-pinned. The sensor shows the floor. Sensitivity case: serious pairs where the sensor read below the meter.
    down = grow("All", "sensor below meter")
    near_floor = grad[(grad.direction == "both") & (grad.error_band == "-100 to -90")].set_index("brand")

    sizes = {
        "false_low": {
            "rule": "true glucose 70 to 250 mg/dL: sensor shows true x (1 + error), not below the floor",
            "cases": {"small": {"error_pct": fl_q3}, "main": {"error_pct": round(float(malf.median_pct_reads_low), 1)}, "large": {"error_pct": fl_q1}},
            "source": "h_malf_vs_serious_errors.csv, row All / malfunction, column median_pct_reads_low (median of malfunction-only pairs "
                      "where the sensor read below the meter). Quartiles: interpolated from the 10-point bins in h_error_distribution.csv "
                      "(All / malfunction, bins up to 0 %).",
            "exact_match": False,
            "note": "No table holds 'meter 70 to 250 and sensor reading low' exactly. This is the nearest documented group.",
        },
        "hidden_low": {
            "rule": "true glucose under 54 mg/dL: sensor shows true x (1 + error), not above the display maximum",
            "cases": {"small": {"error_pct": round(float(up.q1_pct), 1)}, "main": {"error_pct": round(float(up.median_pct), 1)},
                      "large": {"error_pct": round(float(up.q3_pct), 1)}},
            "source": "g_brand_error_sizes.csv, row serious / All / sensor above meter (median, q1, q3 of error in % of the meter value).",
            "exact_match": False,
            "note": "No table holds 'meter under 54' or 'meter under 70' with 'sensor 70 or above' exactly. This is the nearest documented group "
                    "(see fda_evidence.serious_sensor_above_meter for its meter values).",
        },
        "floor_pinned": {
            "rule": "true glucose over 250 mg/dL: sensor shows the floor",
            "cases": {"small": {"error_pct": round(float(down.median_pct), 1)}, "main": {"shown_mgdl": FLOOR}},
            "source": f"Floor = {FLOOR} mg/dL = DEVICE_MIN in analysis/simulation_v2.py (lowest value a sensor may show there). "
                      "REGEX_V2_FULL_CORPUS.md quotes 'LO (LESS THAN 40 MG/DL)'. Small case = not pinned: median error of serious pairs where "
                      "the sensor read below the meter (g_brand_error_sizes.csv, row serious / All / sensor below meter).",
            "exact_match": False,
            "note": "The floor is the lowest value a sensor can show, so there is no larger case.",
        },
    }
    for f in sizes.values():
        for c in f["cases"].values():
            c["label"] = f"shows {c['shown_mgdl']} mg/dL" if "shown_mgdl" in c else f"{c['error_pct']:+.1f} %"
    evidence = {
        "malfunction_pairs": {"n": int(malf.n_pairs), "median_error_pct": float(malf.median_pct), "reads_low_pct": float(malf.pct_reads_low),
                              "median_error_reads_low_pct": float(malf.median_pct_reads_low),
                              "reads_low_quartiles_from_bins_pct": [fl_q1, fl_q3], "reads_low_median_from_bins_pct": fl_med_binned,
                              "median_sensor_mgdl": float(malf.median_sensor_mgdl), "median_meter_mgdl": float(malf.median_meter_mgdl),
                              "meter_70_to_250_pct": round(float(malf.pct_meter_70_to_180 + malf.pct_meter_181_to_250), 1),
                              "meter_under_70_pct": float(malf.pct_meter_under_70), "false_low_pct": float(malf.pct_false_low_70)},
        "serious_pairs": {"n": int(ser.n_pairs), "meter_under_54_pct": float(ser.pct_meter_under_54), "meter_over_250_pct": float(ser.pct_meter_over_250),
                          "hidden_low_pct": float(ser.pct_missed_low_70), "false_low_pct": float(ser.pct_false_low_70)},
        "abbott_serious": {"n": int(hrow("Abbott", "serious").n_pairs), "median_error_reads_low_pct": float(hrow("Abbott", "serious").median_pct_reads_low),
                           "false_low_pct": float(hrow("Abbott", "serious").pct_false_low_70), "hidden_low_pct": float(hrow("Abbott", "serious").pct_missed_low_70)},
        "dexcom_serious": {"n": int(hrow("Dexcom", "serious").n_pairs), "meter_under_54_pct": float(hrow("Dexcom", "serious").pct_meter_under_54),
                           "hidden_low_pct": float(hrow("Dexcom", "serious").pct_missed_low_70), "false_low_pct": float(hrow("Dexcom", "serious").pct_false_low_70),
                           "median_error_sensor_above_meter_pct": round(float(grow("Dexcom", "sensor above meter").median_pct), 1)},
        "serious_sensor_above_meter": {"n": int(up.n_pairs), "median_error_pct": round(float(up.median_pct), 1), "q1_pct": round(float(up.q1_pct), 1),
                                       "q3_pct": round(float(up.q3_pct), 1), "median_sensor_mgdl": float(up.median_sensor_mgdl),
                                       "median_meter_mgdl": float(up.median_meter_mgdl), "meter_under_70_pct": round(float(up.pct_meter_under_70), 1)},
        "serious_sensor_below_meter": {"n": int(down.n_pairs), "median_error_pct": round(float(down.median_pct), 1), "q1_pct": round(float(down.q1_pct), 1),
                                       "q3_pct": round(float(down.q3_pct), 1), "median_sensor_mgdl": float(down.median_sensor_mgdl),
                                       "median_meter_mgdl": float(down.median_meter_mgdl), "meter_over_250_pct": round(float(down.pct_meter_over_250), 1)},
        "near_floor_band_minus100_to_minus90": {b: {"pairs": int(near_floor.loc[b, "pairs"]), "share_serious_pct": float(near_floor.loc[b, "share_serious_pct"]),
                                                    "brand_overall_share_serious_pct": float(near_floor.loc[b, "brand_overall_share_serious_pct"])}
                                                for b in ("Abbott", "Dexcom") if b in near_floor.index},
        "files": ["fda-maude/results/text/tables/h_malf_vs_serious_errors.csv", "fda-maude/results/text/tables/h_error_distribution.csv",
                  "fda-maude/results/text/tables/g_brand_error_sizes.csv", "fda-maude/results/text/tables/h_harm_gradient.csv",
                  "fda-maude/results/text/REGEX_V2_FULL_CORPUS.md", "fda-maude/results/text/BRAND_COMPARISON.md"],
    }
    return sizes, evidence


# --------------------------------------------------------------------------------
# Faults
# --------------------------------------------------------------------------------
def fault_range(fault, g, has):
    """Readings whose true glucose is inside the fault's range."""
    with np.errstate(invalid="ignore"):
        if fault == "false_low":
            return has & (g >= 70) & (g <= 250)
        if fault == "hidden_low":
            return has & (g < 54)
        return has & (g > 250)


def shown_under(case, g, in_range, has):
    """What the sensor would show at every reading if the case were active, and which readings it applies to.

    case: {"kind": "fault", "error_pct" or "shown_mgdl"} acts only inside the fault's range;
          {"kind": "bias", "error_pct"} acts on every reading; {"kind": "none"} changes nothing.
    """
    if case["kind"] == "none":
        return g, has
    applies = in_range if case["kind"] == "fault" else has
    if "shown_mgdl" in case:
        faulted = np.full(len(g), float(case["shown_mgdl"]))
    else:
        faulted = np.clip(g * (1 + case["error_pct"] / 100), v2.DEVICE_MIN, v2.DEVICE_MAX)
    return np.where(applies, faulted, g), applies


def window_sum(x, s, length):
    """Sum of a per-reading array inside each episode window [s, s + length)."""
    cs = np.concatenate(([0.0], np.cumsum(x, dtype=np.float64)))
    return cs[s + length] - cs[s]


def sugar_unneeded(shown, true):
    """Sugar rule on each episode (rows = episodes, columns = 5-min readings).

    The person eats 15 g when the sensor shows under 70, at most once every 15 min while it still shows
    under 70. Returns the number of treatments taken while the true glucose was 70 or above.
    """
    with np.errstate(invalid="ignore"):
        below = shown < SUGAR_BELOW
        not_low = true >= SUGAR_BELOW
    count = np.zeros(shown.shape[0])
    if not (below & not_low).any():
        return count
    last = np.full(shown.shape[0], -10 ** 6)
    for j in range(shown.shape[1]):
        treat = below[:, j] & (j - last >= SUGAR_GAP_SLOTS)
        last[treat] = j
        count += treat & not_low[:, j]
    return count


def join_episodes(seg):
    """Put all episode segments in one long trace with empty slots between them, so the version 2 episode functions run once."""
    return np.concatenate([seg, np.full((seg.shape[0], SEP), np.nan)], axis=1).ravel()


def run_participant(p, sizes):
    """All faults, lengths and cases for one participant. Returns one row per (fault, length, case)."""
    g, has, n = p["g"], p["has"], len(p["g"])
    pid = p["PtID"]
    has_dec = len(p["w_slot"]) > 0
    if has_dec:
        order = np.argsort(p["w_slot"], kind="stable")
        ws = p["w_slot"][order]
        isf, target, above, iob = (p[k][order] for k in ["w_isf", "w_target", "w_above", "w_iob"])
        g_dec = g[ws]
        d_true = v2.correction_dose(g_dec, isf, target, above, iob)
    rows = []
    for fi, fault in enumerate(FAULTS):
        in_range = fault_range(fault, g, has)
        cases = [(name, dict(c, kind="fault")) for name, c in sizes[fault]["cases"].items()]
        cases += [(f"bias_{b}", {"kind": "bias", "error_pct": b}) for b in REF_BIAS] + [("no_fault", {"kind": "none"})]
        for hours in LENGTHS_H:
            length = hours * SLOTS_PER_H
            eligible = np.flatnonzero(in_range[:max(n - length + 1, 0)])      # the whole episode must fit in the trace
            if len(eligible) == 0:
                continue
            rng = np.random.default_rng([SEED, pid, fi, hours])
            n_ep = min(N_STARTS, len(eligible))
            s = np.sort(rng.choice(eligible, n_ep, replace=False))
            win = s[:, None] + np.arange(length)                              # readings inside each episode
            width = length + 2 * PAD
            seg = s[:, None] - PAD + np.arange(width)                         # episode plus 60 min of context on each side
            ok = (seg >= 0) & (seg < n)
            seg = np.clip(seg, 0, n - 1)
            in_win = (np.arange(width) >= PAD) & (np.arange(width) < PAD + length)
            true_seg = np.where(ok, g[seg], np.nan)
            true_long = join_episodes(true_seg)
            true_eps = {name: v2.find_episodes(v2.episode_state(true_long, thr, side)) for name, thr, side in EP_THR}
            if has_dec:
                lo, hi = np.searchsorted(ws, s, side="left"), np.searchsorted(ws, s + length, side="left")
            for case_name, case in cases:
                shown, applies = shown_under(case, g, in_range, has)
                tot = {}
                affected_h = window_sum(applies, s, length).sum() / SLOTS_PER_H
                # sugar
                tot["sugar_unneeded_n"] = sugar_unneeded(shown[win], g[win]).sum()
                tot["sugar_unneeded_g"] = tot["sugar_unneeded_n"] * SUGAR_G
                # insulin correction doses at the wizard decisions inside the episodes
                if has_dec:
                    d_fault = v2.correction_dose(shown[ws], isf, target, above, iob)
                    delta = d_fault - d_true
                    lower = delta < -DOSE_CHANGE_U
                    withheld = (d_true > v2.SKIP_U) & (d_fault == 0)
                    raised_low = (g_dec < 70) & (delta > 0)
                    for key, x in [("dose_lower_n", lower), ("dose_withheld_n", withheld), ("dose_lower_u", np.maximum(-delta, 0)),
                                   ("insulin_true_low_n", raised_low), ("insulin_true_low_u", np.where(raised_low, delta, 0.0))]:
                        cs = np.concatenate(([0.0], np.cumsum(x, dtype=np.float64)))
                        tot[key] = (cs[hi] - cs[lo]).sum()
                    n_dec = float((hi - lo).sum())
                else:
                    for key in DOSE_OUTCOMES:
                        tot[key] = np.nan
                    n_dec = np.nan
                # minutes hidden
                with np.errstate(invalid="ignore"):
                    under54_hidden = has & (g < 54) & (shown >= 70)
                    over180_hidden = has & (g > 180) & ~(shown > 180)
                tot["min_under54_no_alert"] = window_sum(under54_hidden, s, length).sum() * 5
                tot["min_over180_not_shown"] = window_sum(over180_hidden, s, length).sum() * 5
                # alerts and episodes (version 2 rules), all episodes of this participant in one pass
                shown_long = join_episodes(np.where(in_win & ok, shown[seg], true_seg))
                for name, thr, side in EP_THR:
                    fs, fe = v2.find_episodes(v2.episode_state(shown_long, thr, side))
                    r = v2.match_episodes(true_eps[name][0], true_eps[name][1], fs, fe, shown_long)
                    tot[f"{name}_missed_n"] = r["missed"]
                    if name != "high180":
                        tot[f"{name}_false_n"] = r["false"]
                row = {"PtID": pid, "fault": fault, "hours": hours, "case": case_name, "episodes": n_ep, "eligible_starts": int(len(eligible)),
                       "affected_h_per_episode": affected_h / n_ep, "decisions_per_episode": n_dec / n_ep}
                for o in OUTCOMES:
                    row[o + "_per_episode"] = tot[o] / n_ep
                    row[o + "_per_hour"] = tot[o] / affected_h if affected_h > 0 else np.nan
                    row[o + "_total"] = tot[o]
                rows.append(row)
    return rows


# --------------------------------------------------------------------------------
# Figures (same style as the version 2 figures)
# --------------------------------------------------------------------------------
FAULT_COLOR = {"false_low": v2.C_BLUE, "hidden_low": v2.C_ORANGE, "floor_pinned": v2.C_AQUA}
MAIN_PANELS = [("sugar_unneeded_n", "Unneeded sugar treatments"), ("dose_lower_n", "Correction doses withheld\nor reduced"),
               ("low70_false_n", "False low alerts (< 70)"), ("low54_missed_n", "Low alerts (< 54) not shown"),
               ("min_under54_no_alert", "Minutes truly < 54,\nsensor shows 70 or above"), ("min_over180_not_shown", "Minutes truly > 180,\nnot shown as high")]


def fig36(agg, sizes):
    """The three faults and the reference bias side by side, main outcomes, 6-hour episode."""
    rows, y, labels, yy = [], 0.0, [], []
    for fault in FAULTS:
        rows.append((y, fault, "main", FAULT_COLOR[fault]))
        labels.append(f"{FAULT_LABEL[fault]} ({sizes[fault]['cases']['main']['label'].replace('-', chr(0x2212))})")
        yy.append(y)
        for b in REF_BIAS:
            y -= 1
            rows.append((y, fault, f"bias_{b}", v2.MUTED))
            labels.append(f"same windows, bias −{-b} %")
            yy.append(y)
        y -= 1.7
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 6.2), sharey=True)
    for ax, (col, title) in zip(axes.ravel(), MAIN_PANELS):
        for yi, fault, case, color in rows:
            st = agg[(fault, 6, case)][col + "_per_episode"]
            ax.plot([st["q1"], st["q3"]], [yi, yi], color=color, lw=2.2, alpha=0.5, solid_capstyle="round")
            ax.plot(st["median"], yi, "o", color=color, markersize=5.5, clip_on=False, zorder=3)
            if case == "main":
                for other in ("small", "large"):
                    if (fault, 6, other) in agg:
                        ax.plot(agg[(fault, 6, other)][col + "_per_episode"]["median"], yi, "|", color=v2.INK, markersize=9, markeredgewidth=1.2)
        ax.set_title(title, fontsize=8.5)
        ax.grid(axis="x", color=v2.GRID)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(left=0)
        ax.margins(x=0.08)
    for ax in axes[:, 0]:
        ax.set_yticks(yy, labels, fontsize=8)
    for ax in axes[1]:
        ax.set_xlabel("per 6-hour episode")
    fig.suptitle("Three FDA-based faults against a constant bias, one 6-hour episode\n"
                 "Dot = median person, line = IQR, black ticks = small and large size cases",
                 x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=v2.INK)
    fig.tight_layout()
    v2.save(fig, "36_three_faults_outcomes.png")


def fig37(agg):
    """Main outcomes per affected hour against episode length, one line per fault (main size)."""
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 5.4), sharex=True)
    for ax, (col, title) in zip(axes.ravel(), MAIN_PANELS):
        for fault in FAULTS:
            st = [agg[(fault, h, "main")][col + "_per_hour"] for h in LENGTHS_H]
            ax.fill_between(LENGTHS_H, [s["q1"] for s in st], [s["q3"] for s in st], color=FAULT_COLOR[fault], alpha=0.16, linewidth=0)
            ax.plot(LENGTHS_H, [s["median"] for s in st], "-o", color=FAULT_COLOR[fault], markersize=4.5, label=FAULT_LABEL[fault], clip_on=False, zorder=3)
        ax.set_title(title, fontsize=8.5)
        ax.set_ylim(bottom=0)
        ax.set_xticks(LENGTHS_H)
    for ax in axes[1]:
        ax.set_xlabel("Episode length, hours")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("Outcomes per affected hour by episode length (main fault size)\n"
                 "Affected hour = one hour of readings the fault changed. Line = median person, band = IQR",
                 x=0.01, ha="left", fontsize=9.5, fontweight="semibold", color=v2.INK)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    v2.save(fig, "37_three_faults_by_episode_length.png")


# --------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------
def main():
    os.makedirs(v2.FIG, exist_ok=True)
    sizes, evidence = read_fda_sizes()
    log("fault sizes:", {f: {c: v["label"] for c, v in s["cases"].items()} for f, s in sizes.items()})
    cgm, wz, meter, parts = v2.load_tables()
    wizard, _ = v2.prepare_wizard(wz, cgm, meter, parts)
    pids = sorted(cgm.PtID.unique())
    if QUICK:
        pids = pids[:20]
    keep = set(int(x) for x in pids)
    w_groups = {int(k): w for k, w in wizard.groupby("PtID")}
    plist = [v2.build_participant(pid, c, w_groups.get(int(pid), wizard.iloc[0:0])) for pid, c in cgm.groupby("PtID") if int(pid) in keep]
    log(f"prepared {len(plist)} participants")

    rows = []
    for i, p in enumerate(plist):
        rows += run_participant(p, sizes)
        if i % 25 == 0:
            log(f"participant {i + 1}/{len(plist)} done")
    res = pd.DataFrame(rows)                      # per participant; kept in memory only, never written
    log("participant x setting rows:", len(res))

    # median and quartiles across participants (version 2 summary)
    cols = ["affected_h_per_episode", "decisions_per_episode"] + [o + s for o in OUTCOMES for s in ("_per_episode", "_per_hour")]
    agg, lookup, results, episodes = {}, [], {}, {}
    for (fault, hours, case), grp in res.groupby(["fault", "hours", "case"], sort=False):
        st = v2.summarise(grp, cols)
        agg[(fault, hours, case)] = st
        results.setdefault(fault, {}).setdefault(str(hours), {})[case] = st
        if case == "no_fault":
            episodes.setdefault(fault, {})[str(hours)] = {
                "participants_with_episodes": int(len(grp)), "participants_without_an_eligible_start": int(len(plist) - len(grp)),
                "participants_with_fewer_than_planned": int((grp.episodes < N_STARTS).sum()), "episodes_total": int(grp.episodes.sum()),
                "episodes_per_participant_median": float(grp.episodes.median()), "episodes_per_participant_min": int(grp.episodes.min()),
                "eligible_starts_per_participant_median": float(grp.eligible_starts.median())}
        c = sizes[fault]["cases"].get(case)
        size = c["label"] if c else ("no fault" if case == "no_fault" else f"{int(case.split('_')[1]):+d} % on every reading")
        row = {"fault": fault, "episode_hours": hours, "size_case": case, "size": size, "participants": int(len(grp)),
               "participants_with_decisions": int(grp.decisions_per_episode.notna().sum()), "episodes_per_participant_median": float(grp.episodes.median())}
        for col in cols:
            for k in ("median", "q1", "q3"):
                row[f"{col}_{k}"] = st[col][k]
        lookup.append(row)
    case_order = {c: i for i, c in enumerate(["small", "main", "large"] + [f"bias_{b}" for b in REF_BIAS] + ["no_fault"])}
    lk = pd.DataFrame(lookup)
    lk = lk.sort_values(["fault", "episode_hours", "size_case"], key=lambda s: s.map({**{f: i for i, f in enumerate(FAULTS)}, **case_order}) if s.name != "episode_hours" else s)
    lk_path = os.path.join(OUT, "simulation_three_faults_lookup.csv")
    lk.to_csv(lk_path, index=False, float_format="%.4f")
    log("wrote", lk_path)

    # the three sanity checks
    tot = lambda q, names: float(res.loc[q, [o + "_total" for o in names]].fillna(0).abs().to_numpy().sum())
    check1 = tot(res.case == "no_fault", OUTCOMES)
    fault_rows = res.case.isin(["small", "main", "large"])
    check2a = tot((res.fault == "false_low") & fault_rows, ["low70_missed_n", "low54_missed_n", "min_under54_no_alert"])
    check2b = tot((res.fault == "hidden_low") & fault_rows, ["sugar_unneeded_n"])
    ref = agg[("false_low", 12, "bias_-20")]
    mine = {"false_low_alerts_under_70_per_day": ref["low70_false_n_per_hour"]["median"] * 24,
            "corrections_withheld_per_day": ref["dose_withheld_n_per_hour"]["median"] * 24,
            "high_episodes_over_180_not_shown_per_day": ref["high180_missed_n_per_hour"]["median"] * 24}
    v2_vals, v2_path = None, os.path.join(HERE, "simulation_v2_lookup.csv")
    if os.path.exists(v2_path):
        r = pd.read_csv(v2_path)
        r = r[r.bias_pct == -20].iloc[0]
        v2_vals = {"false_low_alerts_under_70_per_day": float(r["low70_false_per_day_median"]), "corrections_withheld_per_day": float(r["skipped_per_day_median"]),
                   "high_episodes_over_180_not_shown_per_day": float(r["high180_missed_per_day_median"])}
    sanity = {
        "1_no_fault_gives_zero": {"sum_of_all_outcomes_in_no_fault_rows": check1, "passed": check1 == 0},
        "2_false_low_no_missed_lows_and_hidden_low_no_unneeded_sugar": {"false_low_missed_low_alerts_and_hidden_minutes": check2a,
                                                                         "hidden_low_unneeded_sugar_treatments": check2b, "passed": check2a == 0 and check2b == 0},
        "3_reference_minus20_vs_version2": {"this_run_per_day": mine, "version_2_per_day": v2_vals,
                                            "how": "this run: -20 % bias in the 12-hour false-low windows, median per hour of readings x 24. "
                                                   "version 2: -20 % bias on the whole trace, median per day (simulation_v2_lookup.csv)."},
    }
    log("sanity:", json.dumps(v2.clean(sanity)))

    fig36(agg, sizes)
    fig37(agg)

    stats = {
        "settings": {
            "seed": SEED, "episode_lengths_h": LENGTHS_H, "planned_starts_per_participant_fault_length": N_STARTS,
            "start_rule": "random reading (no repeats) where the true glucose is inside the fault's range and the whole episode fits in the trace",
            "fault_ranges": FAULT_RANGE, "floor_mgdl": FLOOR, "display_range_mgdl": [v2.DEVICE_MIN, v2.DEVICE_MAX],
            "sugar_rule": {"sensor_below_mgdl": SUGAR_BELOW, "grams": SUGAR_G, "min_gap_min": SUGAR_GAP_SLOTS * 5, "unneeded_when_true_at_or_above_mgdl": SUGAR_BELOW,
                           "glucose_response_modelled": False},
            "dose_rule": "version 2 calculator at the version 2 decision times (wizard records inside the episode)",
            "dose_reduced_cutoff_u": DOSE_CHANGE_U, "dose_withheld_true_dose_above_u": v2.SKIP_U,
            "episode_rule": "version 2: 15 min beyond the threshold starts an episode; an alert within 30 min of a true start, or inside the true episode, counts as shown",
            "context_min_each_side": PAD * 5, "reference_bias_pct": REF_BIAS,
            "aggregation": "per participant: total over episodes / number of episodes (per episode) and / hours of readings the fault changed (per affected hour); "
                           "then median, q1, q3, mean across participants",
            "affected_hour": "one hour of readings that the fault applies to (fault: readings in the fault's glucose range inside the episode; bias and no fault: all readings in the episode)",
            "quick_mode": QUICK,
        },
        "fault_sizes": sizes,
        "fda_evidence": evidence,
        "data": {"participants": int(len(plist)), "participants_with_dose_decisions": int(sum(len(p["w_slot"]) > 0 for p in plist)),
                 "true_trace_min_mgdl": float(min(np.nanmin(p["g"]) for p in plist)), "true_trace_max_mgdl": float(max(np.nanmax(p["g"]) for p in plist)),
                 "episodes": episodes},
        "outcomes": OUTCOME_TEXT,
        "results": results,
        "sanity_checks": sanity,
        "lookup_csv": os.path.basename(lk_path),
        "runtime_s": round(time.time() - v2.T0, 1),
    }
    st_path = os.path.join(OUT, "simulation_three_faults_stats.json")
    with open(st_path, "w", encoding="utf-8") as f:
        json.dump(v2.clean(stats), f, indent=1)
    log("wrote", st_path)
    for fault in FAULTS:
        st = agg[(fault, 6, "main")]
        log(f"{fault} 6 h main: " + ", ".join(f"{o} {st[o + '_per_episode']['median']:.2f}" for o in OUTCOMES))
    log("runtime", stats["runtime_s"], "s")


if __name__ == "__main__":
    main()
