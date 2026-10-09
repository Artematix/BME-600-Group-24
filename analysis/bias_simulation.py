"""
Decision-flip simulation, version 1, for BMEN 600 Group 24.

Question: how big does a CGM sensor error need to be before it changes a
treatment decision?

Method (kept simple on purpose)
  1. Load every REPLACE-BG CGM reading (Dexcom G4, one reading per 5 min).
     Drop calibration rows, readings outside each person's study window
     (day 0 to day 329), and duplicate person+timestamp rows.
  2. Apply two simple decision rules to each reading:
       Rule L ("treat low sugar"): CGM < 70 mg/dL  -> eat fast carbs.
       Rule H ("correction dose"): CGM > 200 mg/dL -> take correction insulin.
  3. The real reading gives the baseline decision. Then make the sensor read
     low by 10, 20, 30 percent (reading * 0.9, 0.8, 0.7) and re-apply the rules.
  4. Count "flips" per person and per bias level:
       false low alert  = Rule L fires on the biased reading but not the real one.
       missed high alert = Rule H fired on the real reading but not the biased one.
  5. Sanity check on the fingerstick-paired subset (meter reading within 5 min).
  6. One figure, one JSON file.

Usage (from the repo root)
  python analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis

Outputs
  analysis/figures/12_decision_flips.png
  analysis/simulation_stats.json
  stdout: progress log with timings
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

ROOT = sys.argv[1] if len(sys.argv) > 1 else "Uncommitted Data/Raw Data Dump"
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis"
FIG = os.path.join(OUT, "figures")
RB = os.path.join(ROOT, "Replace-BG Dataset", "Data Tables")

# --- first, simple choices (state them clearly; change later if the team decides) ---
LOW_T = 70            # mg/dL. Rule L fires when CGM < LOW_T.
HIGH_T = 200          # mg/dL. Rule H fires when CGM > HIGH_T.
BIAS_PCT = [0, 10, 20, 30]      # sensor reads low by this many percent
WINDOW_FIRST_DAY, WINDOW_LAST_DAY = 0, 329   # study window in days from enrolment
REF_MIN, REF_MAX = 20, 600      # meter values outside this are codes or unit errors
PAIR_TOL_S = 300                # fingerstick-to-CGM pairing tolerance, seconds

T0 = time.time()


def log(*a):
    """Print a progress line with elapsed seconds."""
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def seconds_from_enrol(days, tm):
    """Convert day-from-enrolment + 'HH:MM:SS' to seconds from enrolment."""
    parts = tm.str.split(":", expand=True).astype("int32")
    return days.astype("int64") * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]


def load_cgm():
    """Load CGM readings (not calibrations) inside the study window, no duplicates."""
    log("Loading HDeviceCGM.txt (837 MB) ...")
    df = pd.read_csv(
        os.path.join(RB, "HDeviceCGM.txt"), sep="|",
        usecols=["PtID", "DeviceDtTmDaysFromEnroll", "DeviceTm", "RecordType", "GlucoseValue"],
        dtype={"PtID": "int32", "DeviceDtTmDaysFromEnroll": "int32", "RecordType": "category",
               "GlucoseValue": "float32"},
    )
    n_all = len(df)
    df = df[df.RecordType == "CGM"].drop(columns="RecordType")
    n_cgm = len(df)
    df["t"] = seconds_from_enrol(df.DeviceDtTmDaysFromEnroll, df.DeviceTm)
    df = df.drop(columns="DeviceTm").rename(columns={"DeviceDtTmDaysFromEnroll": "day", "GlucoseValue": "g"})
    df = df[(df.day >= WINDOW_FIRST_DAY) & (df.day <= WINDOW_LAST_DAY)]
    n_window = len(df)
    df = df.drop_duplicates(["PtID", "t"]).reset_index(drop=True)
    info = {"rows_in_file": int(n_all), "cgm_readings": int(n_cgm),
            "in_study_window": int(n_window), "after_dropping_duplicates": int(len(df)),
            "participants": int(df.PtID.nunique())}
    log("CGM readings kept:", info)
    return df, info


def load_meter_pairs(cgm):
    """Pair each meter (fingerstick) reading with the nearest CGM reading within 5 min."""
    log("Loading HDeviceBGM.txt ...")
    bgm = pd.read_csv(os.path.join(RB, "HDeviceBGM.txt"), sep="|",
                      usecols=["PtID", "DeviceDtTmDaysFromEnroll", "DeviceTm", "RecordType", "GlucoseValue"])
    bgm = bgm[bgm.RecordType == "BGM"].copy()
    bgm["PtID"] = bgm.PtID.astype("int32")
    bgm["t"] = seconds_from_enrol(bgm.DeviceDtTmDaysFromEnroll, bgm.DeviceTm)
    bgm = bgm[(bgm.GlucoseValue >= REF_MIN) & (bgm.GlucoseValue < REF_MAX)]
    bgm = bgm[(bgm.DeviceDtTmDaysFromEnroll >= WINDOW_FIRST_DAY) & (bgm.DeviceDtTmDaysFromEnroll <= WINDOW_LAST_DAY)]
    bgm = bgm[["PtID", "t", "GlucoseValue"]].rename(columns={"GlucoseValue": "ref"}).sort_values("t")
    cgm_sorted = cgm[["PtID", "t", "g"]].sort_values("t")
    pairs = pd.merge_asof(bgm, cgm_sorted, on="t", by="PtID", direction="nearest", tolerance=PAIR_TOL_S)
    pairs = pairs.dropna(subset=["g"]).reset_index(drop=True)
    log("meter pairs:", len(pairs), "from", len(bgm), "meter readings")
    return pairs


# --------------------------------------------------------------------------
# Rules and flips
# --------------------------------------------------------------------------
def rule_low(g):
    """Rule L: treat low sugar when the reading is below LOW_T."""
    return g < LOW_T


def rule_high(g):
    """Rule H: take a correction dose when the reading is above HIGH_T."""
    return g > HIGH_T


def category(g):
    """Three baseline categories: 0 = below 70, 1 = 70-200, 2 = above 200."""
    return np.where(g < LOW_T, 0, np.where(g > HIGH_T, 2, 1))


def iqr_summary(s):
    """Median and interquartile range of a per-person series."""
    return {"median": float(s.median()), "q1": float(s.quantile(0.25)), "q3": float(s.quantile(0.75)),
            "mean": float(s.mean()), "n_people": int(len(s))}


def flips_for_bias(cgm, days_per_pt, bias_pct):
    """Count decision flips when every reading is lowered by bias_pct percent."""
    g = cgm.g.to_numpy()
    gb = g * (1 - bias_pct / 100)
    base_low, base_high = rule_low(g), rule_high(g)
    new_low = rule_low(gb) & ~base_low           # false low alert -> unnecessary carbs
    lost_high = base_high & ~rule_high(gb)       # missed correction dose
    n = len(g)
    per_pt = pd.DataFrame({"PtID": cgm.PtID.to_numpy(), "new_low": new_low, "lost_high": lost_high}).groupby("PtID").sum()
    per_pt = per_pt.join(days_per_pt)
    per_pt["new_low_per_day"] = per_pt.new_low / per_pt.days
    per_pt["lost_high_per_day"] = per_pt.lost_high / per_pt.days

    cat_base, cat_bias = category(g), category(gb)
    changed = cat_base != cat_bias
    cat_change = {}
    for k, name in enumerate(["below_70", "70_to_200", "above_200"]):
        m = cat_base == k
        cat_change[name] = {"n_readings": int(m.sum()),
                            "pct_changed_category": float(changed[m].mean() * 100) if m.any() else 0.0}
    return {
        "bias_pct": bias_pct,
        "n_readings": int(n),
        "baseline_low_alerts": int(base_low.sum()),
        "baseline_high_alerts": int(base_high.sum()),
        "false_low_alerts": {"n": int(new_low.sum()), "pct_of_readings": float(new_low.mean() * 100),
                             "per_person_per_day": iqr_summary(per_pt.new_low_per_day)},
        "missed_high_alerts": {"n": int(lost_high.sum()), "pct_of_readings": float(lost_high.mean() * 100),
                               "per_person_per_day": iqr_summary(per_pt.lost_high_per_day)},
        "baseline_category_changed": cat_change,
        # the readings that flip are exactly those in these bands (constant bias, fixed thresholds)
        "flip_band_rule_L_mgdl": [LOW_T, LOW_T / (1 - bias_pct / 100)] if bias_pct else None,
        "flip_band_rule_H_mgdl": [HIGH_T, HIGH_T / (1 - bias_pct / 100)] if bias_pct else None,
    }


def paired_check(pairs, bias_pct):
    """Sanity version on the fingerstick-paired subset.

    Two views:
      a) same flip count as the main run, on paired CGM readings only;
      b) biased CGM decision compared with the fingerstick decision (the 'truth').
    """
    g, ref = pairs.g.to_numpy(), pairs.ref.to_numpy()
    gb = g * (1 - bias_pct / 100)
    n = len(g)
    return {
        "bias_pct": bias_pct,
        "n_pairs": int(n),
        "false_low_alerts_pct_of_pairs": float((rule_low(gb) & ~rule_low(g)).mean() * 100),
        "missed_high_alerts_pct_of_pairs": float((rule_high(g) & ~rule_high(gb)).mean() * 100),
        "vs_fingerstick": {
            "cgm_low_but_fingerstick_not_low_pct": float((rule_low(gb) & ~rule_low(ref)).mean() * 100),
            "fingerstick_low_but_cgm_not_low_pct": float((rule_low(ref) & ~rule_low(gb)).mean() * 100),
            "fingerstick_high_but_cgm_not_high_pct": float((rule_high(ref) & ~rule_high(gb)).mean() * 100),
            "cgm_high_but_fingerstick_not_high_pct": float((rule_high(gb) & ~rule_high(ref)).mean() * 100),
            "pct_pairs_same_decision_both_rules": float(((rule_low(gb) == rule_low(ref)) & (rule_high(gb) == rule_high(ref))).mean() * 100),
        },
    }


# --------------------------------------------------------------------------
# Figure
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE = "#2a78d6", "#eb6834"          # categorical slots 1-2 (same palette as explore_raw_data.py)
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 9.5,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 10.5, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 2, "savefig.dpi": 200, "savefig.bbox": "tight",
})


def draw_figure(results, path):
    """Flips per person per day vs bias level, median line with IQR band."""
    x = [r["bias_pct"] for r in results]
    fig, ax = plt.subplots(figsize=(6, 3.7))
    series = [("false_low_alerts", "False low alerts\n(unneeded carbs)", C_ORANGE, "o"),
              ("missed_high_alerts", "Missed high alerts\n(missed insulin dose)", C_BLUE, "s")]
    for key, label, col, mk in series:
        med = [r[key]["per_person_per_day"]["median"] for r in results]
        q1 = [r[key]["per_person_per_day"]["q1"] for r in results]
        q3 = [r[key]["per_person_per_day"]["q3"] for r in results]
        ax.fill_between(x, q1, q3, color=col, alpha=0.18, linewidth=0)
        ax.plot(x, med, color=col, marker=mk, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.2,
                label=label.replace("\n", " "))
        ax.annotate(f"{med[-1]:.1f}/day", (x[-1], med[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK2)
    ax.set_xticks(x, [f"{v}%" for v in x])
    ax.set_xlim(-1, 34.5)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Sensor bias: reads low by (% of true value)")
    ax.set_ylabel("Flipped decisions per person per day")
    ax.set_title(f"Decision flips from a low-reading CGM (REPLACE-BG, {results[0]['n_readings'] / 1e6:.1f} M readings)")
    ax.legend(loc="upper left")
    ax.text(0, -0.26, f"Line = median person. Band = middle half of people (IQR). "
                      f"Rule L: CGM < {LOW_T} mg/dL -> carbs. Rule H: CGM > {HIGH_T} mg/dL -> insulin.",
            transform=ax.transAxes, fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    os.makedirs(FIG, exist_ok=True)
    cgm, load_info = load_cgm()
    days_per_pt = cgm.groupby("PtID").day.nunique().rename("days")
    log("days with data per person: median", float(days_per_pt.median()))

    results = []
    for b in BIAS_PCT:
        r = flips_for_bias(cgm, days_per_pt, b)
        results.append(r)
        log(f"bias {b:2d}%: false low {r['false_low_alerts']['pct_of_readings']:.3f}% of readings, "
            f"median {r['false_low_alerts']['per_person_per_day']['median']:.2f}/person/day; "
            f"missed high {r['missed_high_alerts']['pct_of_readings']:.3f}%, "
            f"median {r['missed_high_alerts']['per_person_per_day']['median']:.2f}/person/day")

    pairs = load_meter_pairs(cgm)
    paired = [paired_check(pairs, b) for b in BIAS_PCT]
    for p in paired:
        log(f"paired bias {p['bias_pct']:2d}%: false low {p['false_low_alerts_pct_of_pairs']:.2f}% of pairs, "
            f"missed high {p['missed_high_alerts_pct_of_pairs']:.2f}%; same decision as fingerstick "
            f"{p['vs_fingerstick']['pct_pairs_same_decision_both_rules']:.1f}%")

    draw_figure(results, os.path.join(FIG, "12_decision_flips.png"))

    stats = {
        "method": {
            "dataset": "REPLACE-BG HDeviceCGM, RecordType == CGM only",
            "study_window_days": [WINDOW_FIRST_DAY, WINDOW_LAST_DAY],
            "rule_L": f"treat low sugar when CGM < {LOW_T} mg/dL",
            "rule_H": f"correction insulin when CGM > {HIGH_T} mg/dL",
            "bias": "constant low bias, reading * (1 - bias/100)",
            "per_day_denominator": "days with at least one CGM reading in the window, per person",
            "paired_subset": f"meter reading matched to nearest CGM reading within {PAIR_TOL_S} s, reference {REF_MIN}-{REF_MAX} mg/dL",
        },
        "loading": load_info,
        "days_with_data_per_person": iqr_summary(days_per_pt),
        "by_bias": results,
        "paired_subset_by_bias": paired,
        "runtime_s": round(time.time() - T0, 1),
    }
    with open(os.path.join(OUT, "simulation_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    log("wrote", os.path.join(OUT, "simulation_stats.json"))


if __name__ == "__main__":
    main()
