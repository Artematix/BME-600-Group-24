"""
make_fig5_three_faults.py - Figure 5 of the final paper (BMEN 600 Group 24).

What the figure shows
  Top row     one real six-hour example for each of the three sensor faults (false low, hidden low, floor-pinned).
  Bottom row  what each fault changes in six hours, for the typical participant. Four outcomes, three bars each.

Words
  sensor        = the CGM (continuous glucose monitor), a skin sensor that reads glucose every 5 minutes.
  true glucose  = the recorded trial trace. Sensor shows = what the faulty sensor would display.
  episode       = six hours in which the sensor has the fault. It starts when the true glucose is inside the fault's range.
  typical participant = the median across participants. Middle half of participants = quartile 1 to quartile 3.

Where the numbers come from
  Bars and whiskers  analysis/simulation_three_faults_lookup.csv, rows with episode_hours = 6 and size_case = main.
                     No bar value is typed in by hand.
  Example traces     the raw trial data, through the simulation's own code (analysis/simulation_three_faults.py).
                     The fault rules are imported from there, not written again. The script draws the same
                     episode starts as the simulation (same seed), then picks one episode per fault by a fixed rule.

Rule for picking the example of each fault (see pick_example)
  1. Start from the six-hour episodes the simulation itself drew, main fault size.
  2. Keep episodes with all 72 five-minute readings, and with no recorded reading at the display limits
     (39 or 401 mg/dL), where the recorded value is cut off.
  3. Take the episode whose outcomes are closest to the typical participant's values in the lookup file.
     Outcomes used: hours the fault acted, unneeded sugar prompts, minutes above 180 mg/dL not shown,
     minutes under 54 mg/dL not shown. Distance = sum of |episode - typical| / typical over the outcomes
     whose typical value is not zero.
  4. Ties: the fewest separate fault stretches, then the average true glucose closest to the middle of the tied episodes.
  No participant id is printed or saved.

  The script rebuilds every simulated episode and stops if its medians differ from the lookup file.

Usage (from the repo root; about 10 seconds with the data cache in analysis/cache)
  python -B docs/paper/figures/make_fig5_three_faults.py "Uncommitted Data/Raw Data Dump"
  Argument 1 = raw data folder (default: the path above). Argument 2 (optional) = cache folder (default analysis/cache).

Outputs (next to this script): fig5_three_faults.png (300 dpi) and fig5_three_faults.pdf. Size 7.0 x 5.35 inches.
The numbers printed on the figure are also listed at the end of the run.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ANALYSIS = os.path.join(REPO, "analysis")
ARGS = sys.argv[1:]
if ARGS and ARGS[0] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)
DATA = os.path.abspath(ARGS[0]) if ARGS else os.path.join(REPO, "Uncommitted Data", "Raw Data Dump")
CACHE = os.path.abspath(ARGS[1]) if len(ARGS) > 1 else os.path.join(ANALYSIS, "cache")

# The simulation modules read the data folder from the command line at import. Hand them full paths.
sys.argv = [sys.argv[0], DATA, ANALYSIS, CACHE]
sys.path.insert(0, ANALYSIS)
import numpy as np
import pandas as pd
import simulation_three_faults as sim            # the simulation: fault rules, sugar rule, seed, episode starts

v2 = sim.v2                                      # version 2 of the simulation: data loading and the 5-minute grid
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

plt.rcdefaults()                                 # the simulation modules set their own plot style at import; drop it
sys.path.insert(0, HERE)
import make_paper_figures as paper               # shared style of Figures 2 to 4 (fonts, sizes, colours, save)

FILES = {
    "lookup": os.path.join(ANALYSIS, "simulation_three_faults_lookup.csv"),
    "stats": os.path.join(ANALYSIS, "simulation_three_faults_stats.json"),
}
HOURS = 6                                        # episode length shown in the figure
LENGTH = HOURS * sim.SLOTS_PER_H                 # 72 five-minute readings
CASE = "main"                                    # main fault size
C_TRUE = "#000000"                               # true glucose
C_SENSOR = "#D55E00"                             # what the faulty sensor shows (the orange of Figures 2 to 4); also the bars
LW_TRUE, LW_SENSOR = 1.2, 2.8                    # the sensor line is wider, so both stay visible where they lie on each other
TARGET = (70, 180)                               # target range, mg/dL
Y_MAX = 400
WIDTH = 7.0                                      # inches: full page width (Figures 2 to 4 are 6.5 inches wide)
FS, FS_TITLE, INK, INK2, ZONE = paper.FS, paper.FS_TITLE, paper.INK, paper.INK2, paper.ZONE      # 8.5 pt is the smallest text

# One entry per fault, in the order of the panels: title, line under the title, extra threshold line (mg/dL).
PANELS = [("false_low", "False low", "glucose is not low,\nsensor shows a low", None),
          ("hidden_low", "Hidden low", "glucose is very low,\nsensor shows normal", 54),
          ("floor_pinned", "Floor-pinned", "glucose is very high,\nsensor shows LO", 250)]
BAR_LABELS = {"false_low": "False\nlow", "hidden_low": "Hidden\nlow", "floor_pinned": "Floor-\npinned"}
# Bottom row: lookup column, title, unit line.
BARS = [("sugar_unneeded_n_per_episode", "Unneeded prompts\nto eat sugar", "prompts in six hours"),
        ("dose_lower_u_per_episode", "Insulin\nnot given", "units in six hours"),
        ("min_over180_not_shown_per_episode", "High glucose\nnot shown", "minutes above 180 mg/dL"),
        ("min_under54_no_alert_per_episode", "Very low glucose\nnot shown", "minutes under 54 mg/dL")]
# Outcomes that can be counted on one trace: name here -> lookup column. Used to pick the examples.
TRACE_OUTCOMES = {"hours_acted": "affected_h_per_episode", "sugar_prompts": "sugar_unneeded_n_per_episode",
                  "min_over180_hidden": "min_over180_not_shown_per_episode", "min_under54_hidden": "min_under54_no_alert_per_episode"}


def stop(message):
    sys.exit("STOP: " + message)


# --------------------------------------------------------------------------
# Numbers
# --------------------------------------------------------------------------
def load_numbers():
    missing = [p for p in FILES.values() if not os.path.exists(p)]
    if missing:
        stop("result files are missing:\n  " + "\n  ".join(missing))
    lookup = pd.read_csv(FILES["lookup"])
    with open(FILES["stats"], encoding="utf-8") as f:
        stats = json.load(f)
    return lookup[lookup["episode_hours"] == HOURS], stats


def lookup_row(lookup, fault):
    row = lookup[(lookup["fault"] == fault) & (lookup["size_case"] == CASE)]
    if len(row) != 1:
        stop(f"the lookup file does not hold exactly one row for {fault}, {HOURS} hours, {CASE} size.")
    return row.iloc[0]


def check_settings(stats, sizes):
    """The simulation code imported here must be the code that wrote the result files."""
    s = stats["settings"]
    if sim.QUICK or s["quick_mode"] or s["seed"] != sim.SEED or s["planned_starts_per_participant_fault_length"] != sim.N_STARTS:
        stop("seed, number of starts or quick mode differ between the simulation code and its stats file.")
    for fault, *_ in PANELS:
        now, saved = sizes[fault]["cases"][CASE], stats["fault_sizes"][fault]["cases"][CASE]
        if any(now.get(k) != saved.get(k) for k in ("error_pct", "shown_mgdl")):
            stop(f"the {fault} size in the FDA tables ({now}) is not the size in the stats file ({saved}).")


# --------------------------------------------------------------------------
# Example traces: the simulation's own episodes, one picked per fault
# --------------------------------------------------------------------------
def simulated_episodes(sizes):
    """Every six-hour episode the simulation drew, with the outcomes that can be counted on its trace.

    The fault rules and the sugar rule are the simulation's functions. The lines that draw the starts and the
    two "minutes not shown" tests repeat run_participant() in simulation_three_faults.py word for word.
    Returns (one row per episode, the participants' traces).
    """
    cgm, wizard, _, _ = v2.load_tables()
    people, rows = {}, []
    for pid, c in cgm.groupby("PtID"):
        p = v2.build_participant(pid, c, wizard.iloc[0:0])          # the trace on the 5-minute grid; no dose records needed
        g, has, n = p["g"], p["has"], len(p["g"])
        people[int(pid)] = (g, has)
        for fi, fault in enumerate(sim.FAULTS):
            in_range = sim.fault_range(fault, g, has)
            eligible = np.flatnonzero(in_range[:max(n - LENGTH + 1, 0)])
            if len(eligible) == 0:
                continue
            rng = np.random.default_rng([sim.SEED, int(pid), fi, HOURS])
            n_ep = min(sim.N_STARTS, len(eligible))
            s = np.sort(rng.choice(eligible, n_ep, replace=False))
            win = s[:, None] + np.arange(LENGTH)
            shown, acts = sim.shown_under(dict(sizes[fault]["cases"][CASE], kind="fault"), g, in_range, has)
            with np.errstate(invalid="ignore"):
                under54_hidden = has & (g < 54) & (shown >= 70)
                over180_hidden = has & (g > 180) & ~(shown > 180)
            a, true = acts[win], g[win]                             # rows = episodes, columns = the 72 readings
            rows.append(pd.DataFrame({
                "fault": fault, "pid": int(pid), "start": s,
                "hours_acted": sim.window_sum(acts, s, LENGTH) / sim.SLOTS_PER_H,
                "sugar_prompts": sim.sugar_unneeded(shown[win], true),
                "min_over180_hidden": sim.window_sum(over180_hidden, s, LENGTH) * 5,
                "min_under54_hidden": sim.window_sum(under54_hidden, s, LENGTH) * 5,
                "readings": sim.window_sum(has, s, LENGTH),
                "stretches": a[:, 0].astype(int) + (a[:, 1:] & ~a[:, :-1]).sum(axis=1),          # separate runs of faulty readings
                "g_mean": np.where(has[win].all(axis=1), np.nansum(true, axis=1) / LENGTH, np.nan),
                "g_min": np.nanmin(true, axis=1), "g_max": np.nanmax(true, axis=1)}))
    return pd.concat(rows, ignore_index=True), people


def check_same_episodes(episodes, lookup):
    """Per participant, then the median across participants, must give the medians of the lookup file."""
    for fault, *_ in PANELS:
        mine = episodes[episodes["fault"] == fault].groupby("pid")[list(TRACE_OUTCOMES)].mean().median()
        row = lookup_row(lookup, fault)
        for name, col in TRACE_OUTCOMES.items():
            if abs(mine[name] - row[col + "_median"]) > 5e-4:
                stop(f"{fault}, {name}: the episodes rebuilt here give {mine[name]:.4f}, the lookup file holds {row[col + '_median']:.4f}.")


def pick_example(episodes, lookup, fault):
    """The fixed rule of the docstring. Returns the picked row."""
    row = lookup_row(lookup, fault)
    typical = {name: float(row[col + "_median"]) for name, col in TRACE_OUTCOMES.items()}
    d = episodes[(episodes["fault"] == fault) & (episodes["readings"] == LENGTH)
                 & (episodes["g_min"] > v2.DEVICE_MIN) & (episodes["g_max"] < v2.DEVICE_MAX)].copy()
    if d.empty:
        stop(f"no complete six-hour episode for {fault}.")
    d["distance"] = sum((d[name] - t).abs() / t for name, t in typical.items() if t > 0)
    d = d[d["distance"] <= d["distance"].min() + 1e-9]
    d = d[d["stretches"] == d["stretches"].min()]
    d["from_middle"] = (d["g_mean"] - d["g_mean"].median()).abs()
    return d.sort_values(["from_middle", "pid", "start"]).iloc[0]


def example_trace(pick, people, sizes):
    """True glucose, shown glucose and the faulty readings of one picked episode."""
    g, has = people[int(pick["pid"])]
    fault = pick["fault"]
    in_range = sim.fault_range(fault, g, has)
    shown, acts = sim.shown_under(dict(sizes[fault]["cases"][CASE], kind="fault"), g, in_range, has)
    sl = slice(int(pick["start"]), int(pick["start"]) + LENGTH)
    return {"hours": np.arange(LENGTH) / sim.SLOTS_PER_H, "true": g[sl], "shown": shown[sl], "acts": acts[sl],
            "outcomes": {name: float(pick[name]) for name in TRACE_OUTCOMES}, "stretches": int(pick["stretches"])}


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------
def data_box(fig, ax, artist):
    """The box of a text in data units."""
    return artist.get_window_extent(fig.canvas.get_renderer()).transformed(ax.transData.inverted())


def mgdl_per_point(fig, ax):
    inv = ax.transData.inverted()
    return abs(inv.transform((0, fig.dpi / 72))[1] - inv.transform((0, 0))[1])


def header(ax, title, below):
    """Bold title above a panel, with plain lines under it."""
    lines = below.count("\n") + 1
    ax.annotate(below, xy=(0, 1), xycoords="axes fraction", xytext=(0, 6), textcoords="offset points", ha="left", va="bottom",
                fontsize=FS, linespacing=1.3, annotation_clip=False)
    ax.annotate(title, xy=(0, 1), xycoords="axes fraction", xytext=(0, 6 + lines * FS * 1.3 + 3.5), textcoords="offset points",
                ha="left", va="bottom", fontsize=FS_TITLE, fontweight="bold", linespacing=1.25, annotation_clip=False)


def label_beside_line(fig, ax, text, hours, values, side, lw, x_left=0.15, gap_pt=2.5):
    """Direct label for one line: at the left, above or below the line over the label's whole width."""
    t = ax.text(x_left, 0, text, ha="left", va="bottom" if side == "above" else "top", fontsize=FS, zorder=6)
    width = data_box(fig, ax, t).width
    under = (hours >= x_left - 0.1) & (hours <= x_left + width + 0.1)
    gap = (gap_pt + lw / 2) * mgdl_per_point(fig, ax)
    t.set_y(values[under].max() + gap if side == "above" else values[under].min() - gap)
    box = data_box(fig, ax, t)
    if box.y0 < 0 or box.y1 > Y_MAX:
        stop(f"no room for the label '{text}' next to its line.")
    return t


def label_in_free_spot(fig, ax, text, lines, y_low, y_high, x_low=0.0, x_high=HOURS):
    """Put a text between y_low and y_high at the place that is farthest from every line."""
    t = ax.text(0, 0, text, ha="center", va="center", fontsize=FS, color=INK2, zorder=6)
    box = data_box(fig, ax, t)
    w, h = box.width, box.height
    edge = 2.0 * mgdl_per_point(fig, ax)
    best = None
    for cx in np.arange(x_low + w / 2 + 0.1, x_high - w / 2 - 0.1 + 1e-9, 0.05):
        for cy in np.arange(y_low + h / 2 + edge, y_high - h / 2 - edge + 1e-9, 1.0):
            clear = np.inf
            for hours, values in lines:
                near = (hours[1:] >= cx - w / 2 - 0.25) & (hours[:-1] <= cx + w / 2 + 0.25)    # line pieces over the text
                if near.any():
                    low, high = np.minimum(values[:-1], values[1:])[near], np.maximum(values[:-1], values[1:])[near]
                    clear = min(clear, np.maximum(low - (cy + h / 2), (cy - h / 2) - high).min())
            if best is None or clear > best[0] + 1e-9:
                best = (clear, cx, cy)
    if best is None or best[0] <= 0:
        stop(f"no free place for the label '{text}'.")
    t.set_position((best[1], best[2]))
    return t


def bar_text(value):
    """Value above a bar: no decimals from 10, one decimal under 10, plain 0 for zero."""
    return "0" if value == 0 else (f"{value:.0f}" if value >= 10 else f"{value:.1f}")


# --------------------------------------------------------------------------
# Figure 5
# --------------------------------------------------------------------------
def figure5(lookup, examples):
    W, H = WIDTH, 5.35                                          # inches
    fig = plt.figure(figsize=(W, H))
    left, right = 0.62, 0.10                                    # inches

    def axes_at(x, y, w, h):
        return fig.add_axes([x / W, y / H, w / W, h / H])

    # ---- Top row: one real six-hour example per fault ----
    gap, h_top = 0.36, 1.80
    w_top = (W - left - right - 2 * gap) / 3
    y_top = H - 0.66 - h_top
    step = 1 / sim.SLOTS_PER_H
    for i, (fault, title, words, line) in enumerate(PANELS):
        ax = axes_at(left + i * (w_top + gap), y_top, w_top, h_top)
        ex = examples[fault]
        hours, true, shown, acts = ex["hours"], ex["true"], ex["shown"], ex["acts"]
        ax.set_xlim(0, HOURS)
        ax.set_ylim(0, Y_MAX)
        ax.axhspan(*TARGET, color=ZONE, lw=0, zorder=0)
        edges = np.flatnonzero(np.diff(np.concatenate(([0], acts.astype(int), [0]))))          # starts and ends of the faulty stretches
        for a, b in zip(edges[::2], edges[1::2]):
            ax.axvspan(max(hours[a] - step / 2, 0), min(hours[b - 1] + step / 2, HOURS), color=C_SENSOR, alpha=0.13, lw=0, zorder=0.5)
        if line is not None:
            ax.axhline(line, color=INK2, lw=0.7, ls=(0, (4, 2.5)), zorder=1)
        ax.plot(hours, shown, color=C_SENSOR, lw=LW_SENSOR, solid_capstyle="round", solid_joinstyle="round", zorder=3, clip_on=False)
        ax.plot(hours, true, color=C_TRUE, lw=LW_TRUE, solid_capstyle="round", solid_joinstyle="round", zorder=4, clip_on=False)
        ax.set_xticks(np.arange(0, HOURS + 1, 2))
        ax.set_xticks(np.arange(0, HOURS + 1, 1), minor=True)
        ticks = list(range(0, Y_MAX + 1, 100))
        if i == 0:
            ax.set_yticks(ticks)
            ax.set_ylabel("Glucose (mg/dL)")
        else:                                                   # same scale as the first panel; only the extra line is numbered
            ax.set_yticks(ticks + [line])
            ax.set_yticklabels([""] * len(ticks) + [str(line)])
        header(ax, title, words)
        if i == 1:
            ax.set_xlabel("Hours since the fault began")
        if i == 0:
            fig.canvas.draw()
            label_beside_line(fig, ax, "true glucose", hours, true, "above", LW_TRUE)
            label_beside_line(fig, ax, "sensor shows", hours, shown, "below", LW_SENSOR)
            label_in_free_spot(fig, ax, "target range", [(hours, true), (hours, shown)], *TARGET)
        paper.note(5, f"example, {title}", ", ".join(f"{k} {v:g}" for k, v in ex["outcomes"].items()) + f", fault stretches {ex['stretches']}",
                   "raw trial trace through simulation_three_faults.py (rule: pick_example)")

    # ---- Bottom row: what each fault changes in six hours ----
    gap, h_bot, y_bot = 0.36, 1.22, 0.42
    w_bot = (W - left - right - 3 * gap) / 4
    pos = np.arange(len(PANELS))
    for j, (col, title, unit) in enumerate(BARS):
        ax = axes_at(left + j * (w_bot + gap), y_bot, w_bot, h_bot)
        rows = [lookup_row(lookup, fault) for fault, *_ in PANELS]
        med = np.array([r[col + "_median"] for r in rows], float)
        q1, q3 = np.array([r[col + "_q1"] for r in rows], float), np.array([r[col + "_q3"] for r in rows], float)
        have = ~np.isnan(med)                                   # a value that was never computed gets no bar
        ax.bar(pos[have], med[have], width=0.58, color=C_SENSOR, lw=0, zorder=2)
        spread = have & (q3 > q1)
        ax.errorbar(pos[spread], med[spread], yerr=[(med - q1)[spread], (q3 - med)[spread]], fmt="none", ecolor=INK, elinewidth=0.9,
                    capsize=2.6, capthick=0.9, zorder=3)
        for k, (fault, name, *_) in enumerate(PANELS):
            if not have[k]:
                print(f"NOT DRAWN: {name}, {col} is not in the lookup file.")
                continue
            ax.annotate(bar_text(med[k]), xy=(pos[k], max(med[k], q3[k])), xytext=(0, 3), textcoords="offset points", ha="center",
                        va="bottom", fontsize=FS, zorder=4,
                        bbox=dict(boxstyle="square,pad=0.2", facecolor=paper.SURFACE, edgecolor="none"))     # no grid line through the number
            n = int(rows[k]["participants_with_decisions" if col.startswith("dose") else "participants"])
            paper.note(5, f"bar, {title.replace(chr(10), ' ')}, {name}", f"{bar_text(med[k])} (exact {med[k]:g}; whisker {q1[k]:g} to {q3[k]:g}; {n} participants)",
                       f"simulation_three_faults_lookup.csv: {col}_median, _q1, _q3 (fault {fault}, episode_hours {HOURS}, size_case {CASE})")
        ax.set_xticks(pos)
        ax.set_xticklabels([BAR_LABELS[fault] for fault, *_ in PANELS], linespacing=1.25)
        ax.tick_params(axis="x", length=0)
        ax.set_xlim(-0.5, len(PANELS) - 0.5)
        ax.set_ylim(0, np.nanmax(q3) * 1.27)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}")
        ax.grid(axis="y")
        header(ax, title, unit)

    paper.save(fig, "fig5_three_faults")


def main():
    lookup, stats = load_numbers()
    sizes, _ = sim.read_fda_sizes()
    check_settings(stats, sizes)
    episodes, people = simulated_episodes(sizes)
    check_same_episodes(episodes, lookup)
    examples = {}
    for fault, *_ in PANELS:
        examples[fault] = example_trace(pick_example(episodes, lookup, fault), people, sizes)
    figure5(lookup, examples)
    print("\nNumbers on the figure (figure | what | text | source):")
    for row in paper.PRINTED:
        print(" | ".join(str(c) for c in row))


if __name__ == "__main__":
    main()
