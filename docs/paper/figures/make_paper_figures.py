"""
make_paper_figures.py - Figures 2, 3 and 4 of the final paper (BMEN 600 Group 24).

Every plotted value is read from a saved result file. No result is typed in by hand.
The script reads summary files only. It does not open the raw trial data or the report texts.

Words
  sensor = the CGM (continuous glucose monitor), a skin sensor that reads glucose every 5 minutes.
  meter  = the fingerstick meter, the reference.
  MARD   = the average distance between sensor and meter, ignoring direction, in % of the meter value.
  typical participant = the median across participants. Middle half of participants = the quartiles.

Figures
  Figure 2  fig2_decision_curve     what a sensor that reads too low does to decisions
  Figure 3  fig3_working_sensor     (a) MARD by glucose range, (b) true lows shown or not shown
  Figure 4  fig4_trial_vs_reports   errors of a working sensor and reported errors on one axis

Two sorting rules in Figure 3 (both as the result files define them)
  Panel (a) sorts each pair by the average of the sensor value and the meter value (by_avg_range).
  Panel (b) sorts by the meter value alone. "A low" on the sensor means under 70 mg/dL in both bars.

Input files (all in analysis/)
  simulation_v2_lookup_extended.csv    one row per error step; medians and quartiles across participants
  accuracy_v2_stats.json               accuracy of the working sensor (Set B = all 226 participants)
  tail_comparison_stats.json           trial errors against reported errors
  low_detection_window_stats.json      true lows shown or not shown, with a time window

Usage (from the repo root; a few seconds)
  python -B docs/paper/figures/make_paper_figures.py

Outputs (next to this script): a PNG at 300 dpi and a vector PDF for each figure.
The numbers on the figures and in their captions are also listed at the end of the run.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ANALYSIS = os.path.join(REPO, "analysis")
FILES = {
    "lookup": os.path.join(ANALYSIS, "simulation_v2_lookup_extended.csv"),
    "accuracy": os.path.join(ANALYSIS, "accuracy_v2_stats.json"),
    "tail": os.path.join(ANALYSIS, "tail_comparison_stats.json"),
    "lows": os.path.join(ANALYSIS, "low_detection_window_stats.json"),
}

# --------------------------------------------------------------------------
# Shared style
# --------------------------------------------------------------------------
WIDTH = 6.5                      # inches: one text column of a letter page
DPI = 300
FS = 8.5                         # smallest text is 8 pt at this width
FS_SMALL = 8.0
FS_TITLE = 9.0
C_TRIAL = "#0072B2"              # trial / working sensor
C_ABBOTT = "#E69F00"
C_DEXCOM = "#009E73"
C_MALF = "#7F7F7F"               # malfunction-only reports
C_WITHHELD = "#D55E00"           # insulin corrections withheld
C_HIGH = "#000000"               # high episodes not shown
C_TRIAL_TINT = "#80B9D9"         # lighter step of the trial blue (second part of a stacked bar)
C_EMPTY = "#DEDEDE"              # "not shown" part of a stacked bar
C_REPORTED = "#F0D7E5"           # band of reported failures (Figure 2): one accent, not a maker colour
INK = "#1A1A1A"                  # main text
INK2 = "#4A4A4A"                 # notes
GRID = "#E2E2E2"
ZONE = "#ECECEC"                 # light shaded zones and bands
SURFACE = "#FFFFFF"

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"], "font.size": FS,
    "axes.labelsize": FS_TITLE, "axes.titlesize": FS_TITLE, "xtick.labelsize": FS, "ytick.labelsize": FS,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "xtick.labelcolor": INK, "ytick.labelcolor": INK,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.width": 0.5,
    "xtick.major.size": 3, "ytick.major.size": 3, "xtick.minor.size": 2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.5,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "pdf.fonttype": 42, "ps.fonttype": 42,          # keep the text as real fonts in the PDF
    "axes.unicode_minus": True,
})

PRINTED = []                     # (figure, what, text on the figure, source) - listed at the end of the run


def note(fig, what, text, source):
    PRINTED.append((fig, what, text, source))


def load():
    missing = [p for p in FILES.values() if not os.path.exists(p)]
    if missing:
        sys.exit("STOP: result files are missing:\n  " + "\n  ".join(missing))
    out = {"lookup": pd.read_csv(FILES["lookup"])}
    for key in ("accuracy", "tail", "lows"):
        with open(FILES[key], encoding="utf-8") as f:
            out[key] = json.load(f)
    return out


def save(fig, name):
    for ext in ("png", "pdf"):
        path = os.path.join(HERE, f"{name}.{ext}")
        fig.savefig(path, dpi=DPI)                  # no tight box: the figure stays exactly 6.5 inches wide
        print("wrote", os.path.relpath(path, REPO).replace("\\", "/"))
    plt.close(fig)


def count(n):
    return f"{int(n):,}"


def error_words(value, digits=0):
    """A signed error in % as words: -69.2 -> '69 % too low'."""
    return f"{abs(value):.{digits}f} % too {'low' if value < 0 else 'high'}"


REPORT_GROUPS = [("abbott_serious", "Abbott serious"), ("dexcom_serious", "Dexcom serious"), ("malfunction", "malfunction-only")]


def reported_medians(tail):
    """Median error of the report pairs, per group and direction."""
    return {(r["group"], r["direction"]): r["median_reported_error_pct"] for r in tail["median_reported_error_in_trial"]}


# --------------------------------------------------------------------------
# Figure 2: what a sensor that reads too low does to decisions
# --------------------------------------------------------------------------
def figure2(src):
    lookup, acc, tail = src["lookup"], src["accuracy"], src["tail"]
    x_max = 80                                                   # axis end: the sensor reads 80 % too low
    d = lookup[(lookup["bias_pct"] <= 0) & (lookup["bias_pct"] >= -x_max)].sort_values("bias_pct", ascending=False)
    if len(d) < 2 or d["bias_pct"].max() != 0 or d["bias_pct"].min() != -x_max:
        sys.exit("STOP: the lookup file does not cover an error of 0 to -80 %.")
    x = -d["bias_pct"].to_numpy(float)                           # how much too low the sensor reads

    margin = min(abs(m) for m in tail["figure_38"]["marks_pct"])                 # 12: where doses begin to change
    working = acc["sets"]["B"]["overall"]["bias_pct"]["value"]                   # average error of the working sensor
    med = reported_medians(tail)
    reported = {key: med[(key, "reads low")] for key, _ in REPORT_GROUPS}        # typical report that reads low, per group
    band_lo, band_hi = min(-v for v in reported.values()), max(-v for v in reported.values())
    if not (working < 0 and margin < band_lo < band_hi <= x_max):
        sys.exit("STOP: the marks are not where the layout expects them (all too low, reports right of the dose margin).")

    fig = plt.figure(figsize=(WIDTH, 3.7))
    ax = fig.add_axes([0.095, 0.146, 0.885, 0.757])              # the plot area is 5.75 by 2.8 inches
    ax.axvspan(0, margin, color=ZONE, lw=0, zorder=0)
    ax.axvspan(band_lo, band_hi, color=C_REPORTED, lw=0, zorder=0)
    for col, color in (("high180_missed_pct", C_HIGH), ("skipped_of_needed_pct", C_WITHHELD)):
        ax.fill_between(x, d[f"{col}_q1"], d[f"{col}_q3"], color=color, alpha=0.17, lw=0, zorder=2)
        ax.plot(x, d[f"{col}_median"], color=color, lw=2, solid_capstyle="round", solid_joinstyle="round", zorder=4, clip_on=False)

    # The two marks are named above the plot, in one row, so the names do not cross the curves.
    tr = ax.get_xaxis_transform()                                # x in data units, y as a share of the plot height
    row = 1.06
    ax.plot([-working, -working], [0, row + 0.035], transform=tr, color=C_TRIAL, lw=1.3, zorder=3, clip_on=False, solid_capstyle="butt")
    ax.text(-working + 0.9, row, "Working sensor", transform=tr, ha="left", va="center", fontsize=FS)
    ax.text((band_lo + band_hi) / 2, row, "Reported failures", transform=tr, ha="center", va="center", fontsize=FS)

    # Each curve is named next to its own band, on the outer side. The place follows the band, so the name cannot touch it.
    # All names sit half way between two grid lines.
    half, gap = 2.5, 1.8                                         # half a line of text (y units); clear space to the band (x units)
    y_high, y_withheld = 90.0, 50.0
    x_high = float(np.interp(y_high - half, d["high180_missed_pct_q3"], x)) - gap
    x_withheld = float(np.interp(y_withheld + half, d["skipped_of_needed_pct_q1"], x)) + gap
    ax.text(x_high, y_high, "High episodes not shown", ha="right", va="center", fontsize=FS)
    ax.text(x_withheld, y_withheld, "Insulin corrections withheld", ha="left", va="center", fontsize=FS)
    ax.text((abs(working) + margin) / 2, 70.0, "Dose\nmargin", ha="center", va="center", fontsize=FS, linespacing=1.3)

    ax.set_xlim(0, x_max)
    ax.set_ylim(0, 100)
    ax.set_xticks(sorted({0, margin, 20, 40, 60, 80}))
    ax.set_xticks(np.arange(0, x_max + 1, 10), minor=True)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.grid(axis="y")
    ax.set_xlabel("Sensor reads this much too low (% of true glucose)")
    ax.set_ylabel("Share (%)")
    save(fig, "fig2_decision_curve")

    pairs = {(r["group"], r["direction"]): r["n_report_pairs"] for r in tail["median_reported_error_in_trial"]}
    note(2, "working-sensor line (value in the caption)", f"{abs(working):.1f} % too low", "accuracy_v2_stats.json: sets.B.overall.bias_pct.value")
    note(2, "reported-failures band, edges", f"{band_lo:.1f} to {band_hi:.1f} % too low", "lowest and highest of the three values below")
    for key, name in REPORT_GROUPS:
        value = reported[key]
        note(2, f"typical {name} report that reads low (caption)",
             f"{error_words(value)} (exact {abs(value):.1f}; {count(pairs[(key, 'reads low')])} pairs that read low)",
             f"tail_comparison_stats.json: median_reported_error_in_trial ({key}, reads low): median_reported_error_pct, n_report_pairs")
    note(2, "dose margin, right edge", f"{margin:g}", "tail_comparison_stats.json: figure_38.marks_pct")
    for col in ("skipped_of_needed_pct", "high180_missed_pct"):
        at = {int(-b): round(float(v), 1) for b, v in zip(d["bias_pct"], d[f"{col}_median"]) if -b in (2, 12, 20, 40, 70)}
        note(2, f"curve {col}_median at 2/12/20/40/70 % too low", str(at),
             f"simulation_v2_lookup_extended.csv: {col}_median, _q1, _q3 (participants: {int(d[f'{col}_n'].iloc[0])})")


# --------------------------------------------------------------------------
# Figure 3: the working sensor
# --------------------------------------------------------------------------
RANGES = [("<54", "Under\n54"), ("54-69", "54 to\n69"), ("70-180", "70 to\n180"), ("181-250", "181 to\n250"), (">250", "Over\n250")]


def text_fits(fig, ax, artist, x_left, x_right, pad_px=6):
    """True if a text artist is narrower than the bar part between x_left and x_right (data units)."""
    box = artist.get_window_extent(fig.canvas.get_renderer())
    px = ax.transData.transform((x_right, 0))[0] - ax.transData.transform((x_left, 0))[0]
    return box.width + 2 * pad_px <= px


def figure3(src):
    acc, lows = src["accuracy"], src["lows"]
    set_b = acc["sets"]["B"]
    fig = plt.figure(figsize=(WIDTH, 3.4))
    title_y = 0.972

    # ---- Panel (a): MARD by glucose range ----
    ax = fig.add_axes([0.085, 0.225, 0.335, 0.675])
    rows = [set_b["by_avg_range"][key]["mard_pct"] for key, _ in RANGES]
    val = np.array([r["value"] for r in rows])
    lo, hi = np.array([r["ci_low"] for r in rows]), np.array([r["ci_high"] for r in rows])
    pos = np.arange(len(RANGES))
    ax.bar(pos, val, width=0.62, color=C_TRIAL, lw=0, zorder=2)
    ax.errorbar(pos, val, yerr=[val - lo, hi - val], fmt="none", ecolor=INK, elinewidth=0.9, capsize=2.6, capthick=0.9, zorder=3)
    for i, key in enumerate(k for k, _ in RANGES):
        ax.text(pos[i], hi[i] + 0.45, f"{val[i]:.1f}", ha="center", va="bottom", fontsize=FS)
        note(3, f"(a) MARD, range {key}", f"{val[i]:.1f} (whisker {lo[i]:.1f} to {hi[i]:.1f})",
             f"accuracy_v2_stats.json: sets.B.by_avg_range['{key}'].mard_pct (value, ci_low, ci_high)")
    ax.set_xticks(pos)
    ax.set_xticklabels([label for _, label in RANGES], linespacing=1.25)
    ax.tick_params(axis="x", length=0)
    ax.set_xlim(-0.55, len(RANGES) - 0.45)
    ax.set_ylim(0, 25.5)
    ax.set_yticks(np.arange(0, 21, 5))
    ax.grid(axis="y")
    ax.set_xlabel("Glucose range (average of\nsensor and meter, mg/dL)", linespacing=1.3)   # the file sorts each pair by this average
    ax.set_ylabel("MARD (% of the meter value)")
    base = f"{set_b['overall']['n_participants']} participants,\n{count(set_b['overall']['n_pairs'])} sensor-meter pairs.\nWhiskers: 95 % interval."
    ax.text(0.99, 0.985, base, transform=ax.transAxes, ha="right", va="top", fontsize=FS_SMALL, color=INK2, linespacing=1.4)
    fig.text(0.085, title_y, "(a) MARD by glucose range", ha="left", va="top", fontsize=FS_TITLE, fontweight="bold")
    note(3, "(a) base", f"{set_b['overall']['n_participants']} participants, {count(set_b['overall']['n_pairs'])} pairs",
         "accuracy_v2_stats.json: sets.B.overall.n_participants, n_pairs")

    # ---- Panel (b): true lows shown or not shown ----
    bx = fig.add_axes([0.505, 0.165, 0.468, 0.52])
    true_lows = lows["sets"]["all_226"]["true_lows"]
    bars = [("meter_under_70_sensor_under_70", 1.38), ("meter_under_54_sensor_under_70", 0.42)]     # file key, bar centre
    height = 0.30
    parts = [("Sensor showed a low at that moment", C_TRIAL, SURFACE),
             ("Sensor showed a low within 15 minutes", C_TRIAL_TINT, INK),
             ("Not shown", C_EMPTY, INK)]
    fig.canvas.draw()
    for key, yc in bars:
        block = true_lows[key]
        if block["sensor_threshold_mgdl"] != 70:
            sys.exit("STOP: panel (b) expects 'a low' on the sensor to mean under 70 mg/dL in both bars.")
        at_moment, window = block["rules"]["matched"], block["rules"]["within_15"]
        n = at_moment["counted"]
        if window["counted"] != n:
            sys.exit("STOP: the two counting rules of panel (b) do not share one count base.")
        shares = [at_moment["shown_pct"]["value"],
                  window["shown_pct"]["value"] - at_moment["shown_pct"]["value"],     # shown within 15 minutes, but not at that moment
                  window["not_shown_pct"]["value"]]
        left = 0.0
        for (label, color, ink), share in zip(parts, shares):
            bx.barh(yc, share, left=left, height=height, color=color, lw=0, zorder=2)
            txt = bx.text(left + share / 2, yc, f"{share:.1f}", ha="center", va="center", fontsize=FS, color=ink, zorder=3)
            if not text_fits(fig, bx, txt, left, left + share):
                txt.set_position((left + share / 2, yc + height / 2 + 0.03))
                txt.set_va("bottom")
                txt.set_color(INK)
            left += share
        for edge in np.cumsum(shares)[:-1]:                                            # white gaps between the parts
            bx.plot([edge, edge], [yc - height / 2, yc + height / 2], color=SURFACE, lw=1.6, zorder=2.5, solid_capstyle="butt")
        bx.text(0, yc + height / 2 + 0.07, f"Meter under {block['meter_threshold_mgdl']} mg/dL", ha="left", va="bottom",
                fontsize=FS, fontweight="bold")
        bx.text(100, yc + height / 2 + 0.07, f"n = {count(n)} meter checks", ha="right", va="bottom", fontsize=FS, color=INK2)
        # bracket under the two right parts: together they are the lows not shown at that moment
        yb = yc - height / 2 - 0.06
        bx.plot([shares[0] + 0.6, shares[0] + 0.6, 100, 100], [yb + 0.035, yb, yb, yb + 0.035], color=INK2, lw=0.7, zorder=2,
                solid_capstyle="butt", solid_joinstyle="miter")
        missed = at_moment["not_shown_pct"]["value"]
        bx.text(100, yb - 0.045, f"{missed:.1f} % of these checks: not shown at that moment", ha="right", va="top", fontsize=FS_SMALL, color=INK)
        short = key.replace("meter_under_", "meter<").replace("_sensor_under_", ", sensor<")
        for (label, _, _), share, field in zip(parts, shares, ("rules.matched.shown_pct.value",
                                                               "rules.within_15.shown_pct.value minus rules.matched.shown_pct.value",
                                                               "rules.within_15.not_shown_pct.value")):
            note(3, f"(b) {short}: {label}", f"{share:.1f}", f"low_detection_window_stats.json: sets.all_226.true_lows.{key}.{field}")
        note(3, f"(b) {short}: not shown at that moment", f"{missed:.1f} %",
             f"low_detection_window_stats.json: sets.all_226.true_lows.{key}.rules.matched.not_shown_pct.value")
        note(3, f"(b) {short}: n meter checks", count(n), f"low_detection_window_stats.json: sets.all_226.true_lows.{key}.rules.matched.counted")
    bx.set_xlim(0, 100)
    bx.set_ylim(0, 1.80)
    bx.set_yticks([])
    bx.spines["left"].set_visible(False)
    bx.set_xticks(np.arange(0, 101, 25))
    bx.set_xlabel("Share of these meter checks (%)")
    handles = [Patch(facecolor=color, edgecolor="none", label=label) for label, color, _ in parts]
    bx.legend(handles=handles, loc="lower left", bbox_to_anchor=(-0.005, 1.035), frameon=False, fontsize=FS, handlelength=1.1,
              handleheight=0.9, handletextpad=0.6, labelspacing=0.32, borderpad=0, borderaxespad=0)
    fig.text(0.505, title_y, "(b) When the meter showed a low,\nwhat did the sensor show?", ha="left", va="top", fontsize=FS_TITLE,
             fontweight="bold", linespacing=1.3)
    save(fig, "fig3_working_sensor")


# --------------------------------------------------------------------------
# Figure 4: errors of a working sensor and reported errors on one axis
# --------------------------------------------------------------------------
def figure4(src):
    tail = src["tail"]
    fb, sets = tail["figure_38"], tail["pair_sets"]
    edges = np.asarray(fb["bin_edges_pct"], float)
    step = fb["bin_width_pct"]
    x_min, x_max = edges[0], edges[-1]
    over_left = x_max + step                                       # the last bar stands one bar width apart from the steps
    central = tail["inside_trial_central_95"]["trial_all"]
    lo, hi = central["range_low_pct"]["value"], central["range_high_pct"]["value"]
    med = reported_medians(tail)
    panels = [("trial_all", C_TRIAL, "Trial: working sensor"), ("abbott_serious", C_ABBOTT, "Abbott serious reports"),
              ("dexcom_serious", C_DEXCOM, "Dexcom serious reports"), ("malfunction", C_MALF, "Malfunction-only reports")]
    shares = {key: np.asarray(fb["sets"][key]["share_per_bin_pct"], float) for key, _, _ in panels}
    beyond = {key: fb["sets"][key]["share_above_drawn_range_pct"] for key, _, _ in panels}     # the last bar: over 200 % too high
    for key, _, name in panels:
        if fb["sets"][key]["share_below_drawn_range_pct"] > 0:
            sys.exit("STOP: some pairs lie left of the drawn range; the figure has no bar for them.")
        if abs(shares[key].sum() + beyond[key] - 100) > 0.05:
            sys.exit(f"STOP: the bars of the panel '{name}' do not add to 100 %.")
    # One scale for all panels. The labels use the top 30 % of a panel, so the tallest step stays under 70 %. The tallest last bar must fit too.
    top = max(max(s.max() for s in shares.values()) / 0.70, max(beyond.values()) * 1.10)

    fig, axes = plt.subplots(len(panels), 1, figsize=(WIDTH, 5.7), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.095, right=0.935, top=0.96, bottom=0.085, hspace=0.36)   # room on the right for the last tick label
    for ax, (key, color, name) in zip(axes, panels):
        tr = ax.get_xaxis_transform()                              # x in data units, y as a share of the panel height
        base = f"{count(sets[key]['n_pairs'])} pairs"
        ax.axvspan(lo, hi, color=ZONE, lw=0, zorder=0)
        ax.bar(list(edges[:-1]) + [over_left], list(shares[key]) + [beyond[key]], width=step, align="edge", color=color,
               edgecolor=SURFACE, linewidth=0.25, zorder=2)
        ax.axvline(0, color=INK, lw=0.6, zorder=3)
        ax.text(0, 1.035, name, transform=ax.transAxes, ha="left", va="bottom", fontsize=FS_TITLE, fontweight="bold")
        ax.text(1, 1.035, base, transform=ax.transAxes, ha="right", va="bottom", fontsize=FS, color=INK2)
        note(4, f"{name}: count base", base, f"tail_comparison_stats.json: pair_sets.{key}.n_pairs")
        note(4, f"{name}: last bar, over {x_max:.0f} % too high", f"{beyond[key]:.2f} % of the pairs (all bars together: {shares[key].sum() + beyond[key]:.2f} %)",
             f"tail_comparison_stats.json: figure_38.sets.{key}.share_above_drawn_range_pct")
        if key == "trial_all":                                     # the zero line and the grey band are named once, here
            ax.text(3, 0.91, "no error", transform=tr, ha="left", va="center", fontsize=FS)
            ax.plot([hi - 9, hi + 4], [0.56, 0.56], transform=tr, color=INK2, lw=0.6, zorder=3, solid_capstyle="butt")
            ax.plot([hi - 9], [0.56], transform=tr, ls="", marker="o", ms=2.6, color=INK2, zorder=3)
            ax.text(hi + 6, 0.56, "95 % of working-sensor readings", transform=tr, ha="left", va="center", fontsize=FS)
            note(4, "trial participants (caption)", str(sets[key]["n_participants"]), f"tail_comparison_stats.json: pair_sets.{key}.n_participants")
            note(4, "grey band (edges in the caption)", f"{error_words(lo)} to {error_words(hi)}",
                 "tail_comparison_stats.json: inside_trial_central_95.trial_all.range_low_pct.value, range_high_pct.value")
        else:
            m_lo = med[(key, "reads low")]
            inside = central["groups"][key]["share_inside_pct"]["value"]
            ax.plot([m_lo], [0.80], transform=tr, ls="", marker="v", ms=6.5, color=INK, mec=SURFACE, mew=0.8, zorder=4)
            ax.text(m_lo, 0.98, error_words(m_lo), transform=tr, ha="center", va="top", fontsize=FS)
            note(4, f"{name}: triangle", error_words(m_lo), f"tail_comparison_stats.json: median_reported_error_in_trial ({key}, reads low)")
            note(4, f"{name}: inside the grey band (caption)", f"{inside:.1f} %",
                 f"tail_comparison_stats.json: inside_trial_central_95.trial_all.groups.{key}.share_inside_pct.value")
    last = axes[-1]
    last.set_xlim(x_min, over_left + step)
    last.set_ylim(0, top)
    regular = [float(v) for v in np.arange(x_min, x_max, 50)]
    last.set_xticks(regular + [over_left + step / 2])
    last.set_xticklabels(["0" if v == 0 else f"{v:+.0f}".replace("-", "−") for v in regular] + [f"+{x_max:.0f} or more"])
    last.set_yticks(np.arange(0, top, 5))
    y_words = -0.36                                                # one line under the tick labels: the axis name and the two directions
    last.text(0.5, y_words, "Sensor error against the meter (%)", transform=last.transAxes, ha="center", va="center", fontsize=FS_TITLE)
    for x0, x1, x_text, ha, words in ((0.0, 0.035, 0.045, "left", "sensor reads too low"), (1.0, 0.965, 0.955, "right", "sensor reads too high")):
        last.annotate("", xy=(x0, y_words), xytext=(x1, y_words), xycoords="axes fraction", textcoords="axes fraction",
                      arrowprops=dict(arrowstyle="->", lw=0.8, color=INK2, shrinkA=0, shrinkB=0), annotation_clip=False)
        last.text(x_text, y_words, words, transform=last.transAxes, ha=ha, va="center", fontsize=FS, color=INK2)
    fig.supylabel("Share of pairs (%)", fontsize=FS_TITLE, x=0.012)
    save(fig, "fig4_trial_vs_reports")
    note(4, "width of one step (caption)", f"{step:g} points of error", "tail_comparison_stats.json: figure_38.bin_width_pct")


def range_table(acc):
    """MARD by glucose range under each sorting rule the stats file holds. Printed only; nothing is plotted from it."""
    blocks = [("B", "by_avg_range", "average of sensor and meter"), ("B", "by_cgm_range", "sensor value alone"),
              ("A", "by_avg_range", "average of sensor and meter"), ("A", "by_ref_range_for_reconciliation", "meter value alone")]
    print("\nMARD by range, by sorting rule (set | participants in the set | rule | range: MARD %, pairs):")
    for key, block, rule in blocks:
        s = acc["sets"][key]
        if block not in s:
            print(f"{key} | {s['overall']['n_participants']} | {rule} | not in the file")
            continue
        cells = "; ".join(f"{label.replace(chr(10), ' ')}: {s[block][b]['mard_pct']['value']:.1f}, {count(s[block][b]['n_pairs'])}" for b, label in RANGES)
        print(f"{key} | {s['overall']['n_participants']} | {rule} ({block}) | {cells}")
    with_meter_rule = [k for k, s in acc["sets"].items() if any("ref_range" in name for name in s)]
    print("Sets that hold meter-only ranges:", ", ".join(with_meter_rule) if with_meter_rule else "none")


def main():
    src = load()
    figure2(src)
    figure3(src)
    figure4(src)
    print("\nNumbers on the figures and in their captions (figure | what | text | source):")
    for row in PRINTED:
        print(" | ".join(str(c) for c in row))
    range_table(src["accuracy"])


if __name__ == "__main__":
    main()
