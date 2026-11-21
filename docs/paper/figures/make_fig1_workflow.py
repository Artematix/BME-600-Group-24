"""Figure 1 of the paper: the workflow (three data sources -> five findings).

Run from the repo root:
    python -B docs/paper/figures/make_fig1_workflow.py

Writes, next to this file:
    fig1_workflow.png   (300 dpi, 6.5 inches wide)
    fig1_workflow.pdf

No data is read. Every number is typed in the TEXT block below.
Each number comes from docs/paper/FACT_SHEET.md (see CAPTION_fig1.md for the lines).

How the drawing works, in short:
- All sizes are in inches. The figure is 6.5 inches wide. Its height is worked out
  from the text, so no text is ever clipped.
- Each box wraps its own text to its own width. Smallest font: 8 pt.
- "~" in a text means "keep these two words on one line".
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent

# --------------------------------------------------------------------------
# TEXT (edit here). head = bold first line. tag = bold finding number.
# --------------------------------------------------------------------------
TEXT = {
    # Column 1: FDA problem reports
    "F1": dict(head="FDA problem reports", body="3,382,071 reports about~CGMs"),
    "F2": dict(body="Count the coded fields"),
    "F3": dict(body="Read 124,599 report texts (text patterns, then a local language "
                    "model, checked against 287~reference reports)"),
    "F3b": dict(body="Then run the text patterns alone over all 3,382,071~reports"),
    "F4": dict(body="207,771 report pairs (reports that state both the sensor value "
                    "and the meter value)"),
    "R3": dict(tag="R3", body="How far off the sensor was in reported failures, "
                              "and three~faults"),
    # Column 2: REPLACE-BG trial
    "TS": dict(head="REPLACE-BG trial",
               body="226 adults with type~1 diabetes, Dexcom~G4 sensor"),
    "TR": dict(body="Glucose traces and 159,878 dose-calculator decisions"),
    "T2": dict(body="168,990 sensor-meter pairs"),
    "T3": dict(body="Accuracy by glucose range, by wear day, and 680~tests of "
                    "participant traits"),
    "SA": dict(head="Simulation A",
               body="A sensor that steadily reads 0~to~80~% too~low"),
    "SB": dict(head="Simulation B",
               body="The three reported faults, in periods of 2,~6 and 12~hours"),
    "R1": dict(tag="R1", body="At what error decisions change"),
    "R2": dict(tag="R2", body="Accuracy of a working sensor"),
    "R4": dict(tag="R4", body="What each fault changes"),
    # Column 3: Shanghai data
    "H1": dict(head="Shanghai data",
               body="98 patients, a~different sensor, 4,012~pairs"),
    "H2": dict(body="Accuracy, as a second population"),
    "R5": dict(tag="R5", body="What predicts error"),
}
# Label on the arrow from R3 into Simulation B (one line).
# The brief said "fault types and sizes". The paper rule says: do not use
# "size" alone, say "how far off". To go back, change this one string.
ARROW_LABEL = "fault types and how far off"

# Three places where the text differs from the first brief, and why:
# - F3b is an added step. 191,112 of the 207,771 pairs come from the text
#   patterns run alone over all reports, not from the 124,599 texts read
#   (FACT_SHEET.md section B, MAUDE steps 9 and 10).
# - TR says "decisions", not "records". The fact sheet counts 232,329
#   calculator records; 159,878 of them are usable decisions (section C3).
# - 207,771 is a sum: 7,470 + 9,189 + 191,112 (section B, MAUDE steps 8, 10).

# --------------------------------------------------------------------------
# Look
# --------------------------------------------------------------------------
W = 6.5                 # figure width, inches
MARGIN = 0.04           # empty rim around the drawing
FS = 8.0                # body text, points (the smallest font in the figure)
FS_HEAD = 8.6           # bold first line of a source box
LINE = FS * 1.18 / 72   # distance between two text lines, inches
CAP = 0.72 * FS / 72    # height of a capital letter, inches
PAD_X = 0.05            # space between box edge and text, left and right
PAD_Y = 0.055           # the same, top and bottom
GAP = 0.15              # space between two boxes in a column (one arrow)

C_FDA, C_TRIAL, C_SHANGHAI = "#E69F00", "#0072B2", "#009E73"
C_TEXT, C_ARROW = "#1A1A1A", "#3F3F3F"


def tint(hex_colour, share):
    """Mix a colour with white. share = how much of the colour is kept (0 to 1)."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(255 - share * (255 - v)) for v in (r, g, b))


#        kind: (fill, edge, edge width)
STYLE = {
    "fda_src": (tint(C_FDA, 0.42), C_FDA, 1.1),
    "fda": (tint(C_FDA, 0.17), C_FDA, 0.9),
    "trial_src": (tint(C_TRIAL, 0.30), C_TRIAL, 1.1),
    "trial": (tint(C_TRIAL, 0.12), C_TRIAL, 0.9),
    "sh_src": (tint(C_SHANGHAI, 0.32), C_SHANGHAI, 1.1),
    "sh": (tint(C_SHANGHAI, 0.13), C_SHANGHAI, 0.9),
    "sim": ("#EBEBEB", "#8A8A8A", 0.9),
    "finding": ("#FFFFFF", "#1F1F1F", 1.4),
}

# Left and right edge of each column, inches.
# F = FDA reports. SB, SA, T = the three parts of the trial column
# (Simulation B, Simulation A, accuracy). H = Shanghai.
X = {
    "F": (0.04, 1.74),
    "SB": (1.94, 2.93),
    "SA": (3.00, 3.99),
    "T": (4.08, 5.38),
    "H": (5.47, 6.46),
}
X_R2 = (4.08, 5.06)      # R2 and R5 share the bottom right corner
X_R5 = (5.16, 6.46)
ELBOW_DROP = 0.13        # R3 -> Simulation B: how far the arrow goes down first
ELBOW_IN = 0.10          # ... and how far above the bottom of Simulation B it enters


def pick_font():
    for name in ("Arial", "Helvetica", "Liberation Sans"):
        try:
            font_manager.findfont(name, fallback_to_default=False)
            return name
        except Exception:
            continue
    return "DejaVu Sans"


FONT = pick_font()
plt.rcParams["pdf.fonttype"] = 42   # keep real fonts inside the PDF
plt.rcParams["ps.fonttype"] = 42

FP_BODY = FontProperties(family=FONT, size=FS)
FP_BOLD = FontProperties(family=FONT, size=FS, weight="bold")
FP_HEAD = FontProperties(family=FONT, size=FS_HEAD, weight="bold")
FP_LABEL = FontProperties(family=FONT, size=FS, style="italic")

_probe = plt.figure(figsize=(W, 1), dpi=300)
_renderer = _probe.canvas.get_renderer()


def text_width(s, fp):
    """Width of a text in inches."""
    w, _, _ = _renderer.get_text_width_height_descent(s.replace("~", " "), fp, False)
    return w / _probe.dpi


SPACE = text_width("a a", FP_BODY) - text_width("aa", FP_BODY)


def greedy(words, max_w, first_indent):
    lines, cur = [], []
    for word in words:
        trial = cur + [word]
        indent = first_indent if not lines else 0.0
        if cur and indent + text_width(" ".join(trial), FP_BODY) > max_w:
            lines.append(cur)
            cur = [word]
        else:
            cur = trial
    lines.append(cur)
    return [" ".join(line) for line in lines]


def wrap(body, max_w, first_indent=0.0):
    """Wrap to the box width, then even out the line lengths."""
    words = body.split(" ")
    best = greedy(words, max_w, first_indent)
    n = len(best)
    w = max_w
    while w > 0.3:
        w -= 0.02
        cand = greedy(words, w, first_indent)
        if len(cand) != n:
            break
        best = cand
    return best


class Box:
    def __init__(self, key, xr, kind):
        self.key, self.kind = key, kind
        self.x0, self.x1 = xr
        spec = TEXT[key]
        self.head = spec.get("head")
        self.tag = spec.get("tag")
        inner = (self.x1 - self.x0) - 2 * PAD_X
        self.tag_w = text_width(self.tag, FP_BOLD) + SPACE if self.tag else 0.0
        self.lines = wrap(spec["body"], inner, self.tag_w)
        n = len(self.lines) + (1 if self.head else 0)
        self.h = 2 * PAD_Y + (n - 1) * LINE + CAP + 0.2 * FS / 72
        self.y0 = None
        # self-check: nothing wider than the box
        widths = [text_width(s, FP_BODY) for s in self.lines]
        widths[0] += self.tag_w
        if self.head:
            widths.append(text_width(self.head, FP_HEAD))
        if max(widths) > inner + 1e-6:
            raise ValueError(f"text too wide for box {key}")

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def y1(self):
        return self.y0 + self.h

    @property
    def cy(self):
        return self.y0 + self.h / 2

    def draw(self, ax):
        fill, edge, lw = STYLE[self.kind]
        ax.add_patch(FancyBboxPatch(
            (self.x0, self.y0), self.x1 - self.x0, self.h,
            boxstyle="round,pad=0,rounding_size=0.045",
            facecolor=fill, edgecolor=edge, linewidth=lw, zorder=2))
        n = len(self.lines) + (1 if self.head else 0)
        base = self.cy + ((n - 1) * LINE + CAP) / 2 - CAP   # baseline of line 1
        k = 0
        if self.head:
            ax.text(self.cx, base, self.head, ha="center", va="baseline",
                    fontproperties=FP_HEAD, color=C_TEXT, zorder=3)
            k = 1
        for i, line in enumerate(self.lines):
            y = base - (k + i) * LINE
            shown = line.replace("~", " ")
            if i == 0 and self.tag:
                total = self.tag_w + text_width(shown, FP_BODY)
                x = self.cx - total / 2
                ax.text(x, y, self.tag, ha="left", va="baseline",
                        fontproperties=FP_BOLD, color=C_TEXT, zorder=3)
                ax.text(x + self.tag_w, y, shown, ha="left", va="baseline",
                        fontproperties=FP_BODY, color=C_TEXT, zorder=3)
            else:
                ax.text(self.cx, y, shown, ha="center", va="baseline",
                        fontproperties=FP_BODY, color=C_TEXT, zorder=3)


def arrow(ax, p0, p1):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>,head_length=0.55,head_width=0.26",
        mutation_scale=9, linewidth=0.9, color=C_ARROW,
        shrinkA=0, shrinkB=0, zorder=1))


def down(ax, a, b, x=None):
    """Straight arrow from the bottom of box a down to the top of box b."""
    xa = a.cx if x is None else x
    for box in (a, b):
        if not box.x0 + 0.06 <= xa <= box.x1 - 0.06:
            raise ValueError(f"arrow {a.key} -> {b.key} misses box {box.key}")
    arrow(ax, (xa, a.y0), (xa, b.y1))


def check_no_overlap(boxes):
    """Self-check: no two boxes touch, and every box is inside the figure."""
    items = list(boxes.values())
    for i, p in enumerate(items):
        if p.x0 < 0 or p.x1 > W or p.y0 < 0:
            raise ValueError(f"box {p.key} leaves the figure")
        for q in items[i + 1:]:
            apart = (p.x1 + 0.05 <= q.x0 or q.x1 + 0.05 <= p.x0
                     or p.y1 + 0.05 <= q.y0 or q.y1 + 0.05 <= p.y0)
            if not apart:
                raise ValueError(f"boxes {p.key} and {q.key} overlap")


def build():
    b = {}
    # Column 1
    b["F1"] = Box("F1", X["F"], "fda_src")
    for key in ("F2", "F3", "F3b", "F4"):
        b[key] = Box(key, X["F"], "fda")
    b["R3"] = Box("R3", X["F"], "finding")
    # Column 2
    b["TS"] = Box("TS", (X["SB"][0], X["T"][1]), "trial_src")
    b["TR"] = Box("TR", (X["SB"][0], X["SA"][1]), "trial")
    b["T2"] = Box("T2", X["T"], "trial")
    b["T3"] = Box("T3", X["T"], "trial")
    b["SB"] = Box("SB", X["SB"], "sim")
    b["SA"] = Box("SA", X["SA"], "sim")
    b["R4"] = Box("R4", X["SB"], "finding")
    b["R1"] = Box("R1", X["SA"], "finding")
    b["R2"] = Box("R2", X_R2, "finding")
    # Column 3
    b["H1"] = Box("H1", X["H"], "sh_src")
    b["H2"] = Box("H2", X["H"], "sh")
    b["R5"] = Box("R5", X_R5, "finding")

    # ---- heights that must match ----
    row_find = max(b[k].h for k in ("R4", "R1", "R2", "R5"))
    for k in ("R4", "R1", "R2", "R5"):
        b[k].h = row_find
    row_last = max(b[k].h for k in ("SB", "SA", "T3", "H2"))
    for k in ("SB", "SA", "T3", "H2"):
        b[k].h = row_last
    b["TR"].h = b["T2"].h = max(b["TR"].h, b["T2"].h)

    # ---- vertical positions (y = 0 is the bottom of the figure) ----
    f_keys = ["F1", "F2", "F3", "F3b", "F4", "R3"]
    y_find = MARGIN                                  # bottom row: R4 R1 R2 R5
    y_last = y_find + row_find + GAP                 # last step above a finding
    y_r3 = y_last + ELBOW_IN + ELBOW_DROP            # bottom of R3
    fig_h = y_r3 + sum(b[k].h for k in f_keys) + GAP * (len(f_keys) - 1) + MARGIN
    top = fig_h - MARGIN

    y = top
    for k in f_keys:                                 # column 1, top to bottom
        b[k].y0 = y - b[k].h
        y = b[k].y0 - GAP
    for k in ("R4", "R1", "R2", "R5"):
        b[k].y0 = y_find
    for k in ("SB", "SA", "T3", "H2"):
        b[k].y0 = y_last
    for k in ("TS", "H1"):
        b[k].y0 = top - b[k].h
    # the two trial data boxes: half way between the source and the next step
    mid = (b["TS"].y0 + max(b["SB"].y1, b["T3"].y1)) / 2
    for k in ("TR", "T2"):
        b[k].y0 = mid - b[k].h / 2
    check_no_overlap(b)
    return b, fig_h


def main():
    b, fig_h = build()
    fig = plt.figure(figsize=(W, fig_h), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    for box in b.values():
        box.draw(ax)

    # column 1
    xf = b["F1"].cx
    for a, c in (("F1", "F2"), ("F2", "F3"), ("F3", "F3b"), ("F3b", "F4"), ("F4", "R3")):
        down(ax, b[a], b[c], x=xf)
    # column 2
    down(ax, b["TS"], b["TR"], x=b["TR"].cx)
    down(ax, b["TS"], b["T2"], x=b["T2"].cx)
    down(ax, b["TR"], b["SB"], x=b["SB"].cx)
    down(ax, b["TR"], b["SA"], x=b["SA"].cx)
    down(ax, b["T2"], b["T3"])
    down(ax, b["SB"], b["R4"])
    down(ax, b["SA"], b["R1"])
    down(ax, b["T3"], b["R2"], x=b["R2"].cx)
    down(ax, b["T3"], b["R5"], x=(b["R5"].x0 + b["T3"].x1) / 2)
    # column 3
    down(ax, b["H1"], b["H2"])
    down(ax, b["H2"], b["R5"])

    # R3 -> Simulation B: down, then right. The label sits under the arrow.
    y_in = b["SB"].y0 + ELBOW_IN
    ax.add_patch(FancyArrowPatch(
        (xf, b["R3"].y0), (b["SB"].x0, y_in),
        connectionstyle="angle,angleA=-90,angleB=180,rad=0",
        arrowstyle="-|>,head_length=0.55,head_width=0.26",
        mutation_scale=9, linewidth=0.9, color=C_ARROW,
        shrinkA=0, shrinkB=0, zorder=1))
    x_lab = b["SB"].x0 - 0.09
    if x_lab - text_width(ARROW_LABEL, FP_LABEL) < b["R3"].x0:
        raise ValueError("arrow label too wide")
    ax.text(x_lab, y_in - 0.05 - CAP, ARROW_LABEL, ha="right", va="baseline",
            fontproperties=FP_LABEL, color=C_TEXT, zorder=3)

    fig.savefig(OUT_DIR / "fig1_workflow.png", dpi=300)
    fig.savefig(OUT_DIR / "fig1_workflow.pdf")
    print(f"font: {FONT}; size: {W} x {fig_h:.2f} inches; smallest text: {FS} pt")
    for k, box in b.items():
        print(f"  {k:4s} lines={len(box.lines) + (1 if box.head else 0)} "
              f"x={box.x0:.2f}-{box.x1:.2f} y={box.y0:.2f}-{box.y1:.2f}")


if __name__ == "__main__":
    main()
