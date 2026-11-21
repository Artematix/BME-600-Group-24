"""Shared code for the paper builds.

Reads the paper Markdown (PAPER.md and the table files) and turns it into LaTeX.
Used by build_paper.py (whole paper) and test_layout/build_layout.py (test layouts).
Nothing here changes a source file.

Tool chain: xelatex (MiKTeX) with the Times New Roman font of Windows.
"""
import os
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageFont

BUILD_DIR = Path(__file__).resolve().parent
PAPER_DIR = BUILD_DIR.parent
PAPER = PAPER_DIR / "PAPER.md"

ENGINE = "xelatex"
PAGE_W_IN, PAGE_H_IN = 8.5, 11.0
TABLE_PT = 8.0            # font size inside tables
COLSEP_PT = 3.5           # half of the gap between two table columns
LONG_TABLE_ROWS = 12      # a table in the text with more rows may break across pages
EMPTY_LINE = "To be added by the team."


# ====================================================================== reading
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,3}[.)])\s+(.*)$")
REF_ITEM = re.compile(r"^\*{0,2}\[(\d+)\]\*{0,2}\s+(.*)$")
IMAGE = re.compile(r"^!\[(.*?)\]\((.*?)\)\s*$")
RULE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
CAPTION = re.compile(r"^\*(Table|Figure|Fig\.)\s")
PLACEHOLDER = re.compile(
    r"^\((not written|built from|being built|to be written|to be added|todo|tbd)\b.*\)$", re.I)


def read_markdown(path):
    """Lines of a Markdown file, without HTML comments."""
    text = Path(path).read_text(encoding="utf-8-sig")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return [ln.rstrip().expandtabs(4) for ln in text.splitlines()]


def is_italic_line(s):
    return (len(s) > 2 and s[0] == "*" and s[-1] == "*"
            and not s.startswith("**") and not s.endswith("**"))


def is_placeholder(text):
    return bool(PLACEHOLDER.match(text.strip()))


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def is_separator(row):
    return all(re.fullmatch(r":?-+:?", c) for c in row) and len(row) > 0


def is_group_row(row):
    """A row like | | **FDA reports** | | | is a group heading inside a table."""
    filled = [c for c in row if c]
    return (len(row) > 1 and len(filled) == 1 and not row[0]
            and filled[0].startswith("**") and filled[0].endswith("**"))


def parse_blocks(lines):
    """Turn Markdown lines into a list of blocks (dicts with a 'kind')."""
    blocks, n, i = [], len(lines), 0

    def skip_blank(j):
        while j < n and not lines[j].strip():
            j += 1
        return j

    def starts_block(raw):
        s = raw.strip()
        return bool(HEADING.match(s) or s.startswith(("```", "|", "![", ">"))
                    or LIST_ITEM.match(raw) or RULE.match(s))

    def read_table(j, title):
        rows = []
        while j < n and lines[j].strip().startswith("|"):
            rows.append(split_row(lines[j]))
            j += 1
        rows = [r for r in rows if not is_separator(r)]
        if not rows:
            return j
        header = rows[0]
        k = len(header)
        body = [(r + [""] * k)[:k] for r in rows[1:]]
        note = None
        for _ in range(2):          # an italic line under the table: its caption or its note
            j2 = skip_blank(j)
            if j2 >= n or not is_italic_line(lines[j2].strip()):
                break
            s2 = lines[j2].strip()
            j3 = skip_blank(j2 + 1)
            next_is_table = j3 < n and lines[j3].strip().startswith("|")
            if CAPTION.match(s2):
                if title is None and s2.startswith("*Table") and not next_is_table:
                    title, j = s2[1:-1], j2 + 1      # caption written under the table
                    continue
                break
            if note is None:
                note, j = s2[1:-1], j2 + 1
        blocks.append(dict(kind="table", title=title, header=header, rows=body, note=note))
        return j

    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s or RULE.match(s):
            i += 1
            continue
        m = HEADING.match(s)
        if m:
            blocks.append(dict(kind="heading", level=len(m.group(1)), text=m.group(2).strip()))
            i += 1
            continue
        if s.startswith("```"):
            j, code = i + 1, []
            while j < n and not lines[j].strip().startswith("```"):
                code.append(lines[j])
                j += 1
            blocks.append(dict(kind="code", text="\n".join(code)))
            i = j + 1
            continue
        m = IMAGE.match(s)
        if m:
            j, cap, nxt = skip_blank(i + 1), None, i + 1
            if j < n and is_italic_line(lines[j].strip()) and not lines[j].strip().startswith("*Table"):
                cap, nxt = lines[j].strip()[1:-1], j + 1
            blocks.append(dict(kind="figure", path=m.group(2).strip(), caption=cap))
            i = nxt
            continue
        if s.startswith("|"):
            i = read_table(i, None)
            continue
        if is_italic_line(s) and s.startswith("*Table"):
            j = skip_blank(i + 1)
            if j < n and lines[j].strip().startswith("|"):
                i = read_table(j, s[1:-1])
                continue
        if REF_ITEM.match(s):
            items = []
            while i < n:
                s2 = lines[i].strip()
                m2 = REF_ITEM.match(s2)
                if m2:
                    items.append([m2.group(1), m2.group(2)])
                    i += 1
                elif not s2:
                    j = skip_blank(i)
                    if j < n and REF_ITEM.match(lines[j].strip()):
                        i = j
                    else:
                        break
                elif starts_block(lines[i]):
                    break
                else:
                    items[-1][1] += " " + s2
                    i += 1
            blocks.append(dict(kind="refs", items=items))
            continue
        if LIST_ITEM.match(raw):
            items = []
            while i < n:
                raw2 = lines[i]
                s2 = raw2.strip()
                m2 = LIST_ITEM.match(raw2)
                if m2:
                    items.append(dict(indent=len(m2.group(1)), ordered=m2.group(2)[0].isdigit(),
                                      text=m2.group(3)))
                    i += 1
                elif not s2:
                    j = skip_blank(i)
                    if j < n and LIST_ITEM.match(lines[j]):
                        i = j
                    else:
                        break
                elif HEADING.match(s2) or s2.startswith(("```", "|", "![")):
                    break
                else:
                    items[-1]["text"] += " " + s2
                    i += 1
            blocks.append(dict(kind="list", items=items))
            continue
        if s.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(dict(kind="quote", text=" ".join(quote)))
            continue
        para = [s]
        i += 1
        while i < n and lines[i].strip() and not starts_block(lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append(dict(kind="para", text=" ".join(para)))
    return blocks


def plain(text):
    """Text without Markdown marks, for counting and for width guesses."""
    text = re.sub(r"<[^>]+>", " ", text)
    return text.replace("**", "").replace("`", "").replace("*", "")


def count_words(text):
    return sum(1 for t in plain(text).split() if re.search(r"\w", t))


def words_in(blocks):
    """Words of running text in a list of blocks (no headings, captions or tables)."""
    total = 0
    for b in blocks:
        if b["kind"] in ("para", "quote") and not is_placeholder(b["text"]):
            total += count_words(b["text"])
        elif b["kind"] == "list":
            total += sum(count_words(it["text"]) for it in b["items"])
    return total


# ====================================================================== inline text
ESC = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
       "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
       "^": r"\textasciicircum{}"}


def esc(s):
    return re.sub(r"[\\&%$#_{}~^]", lambda m: ESC[m.group()], s)


def tex_code(s):
    t = esc(s).replace("/", "/\\allowbreak{}").replace("\\_", "\\_\\allowbreak{}")
    return "\\texttt{" + t + "}"


def tex_url(u):
    u = (u.replace("\\", "/").replace("%", "\\%").replace("#", "\\#")
          .replace("{", "\\%7B").replace("}", "\\%7D"))
    return "\\url{" + u + "}"


def inline(text):
    """One piece of Markdown text as LaTeX: bold, italics, code, links, raised letters."""
    stash = []

    def keep(tex):
        stash.append(tex)
        return "\x00%d\x00" % (len(stash) - 1)

    def bare_url(m):
        u, tail = m.group(0), ""
        while u and (u[-1] in ".,;:!?*'\"" or (u[-1] == ")" and u.count("(") < u.count(")"))
                     or (u[-1] == "]" and u.count("[") < u.count("]"))):
            u, tail = u[:-1], u[-1] + tail
        return keep(tex_url(u)) + tail

    text = re.sub(r"`([^`]+)`", lambda m: keep(tex_code(m.group(1))), text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
                  lambda m: keep("\\href{%s}{%s}" % (tex_url(m.group(2))[5:-1], inline(m.group(1)))),
                  text)
    text = re.sub(r"<(https?://[^>\s]+)>", lambda m: keep(tex_url(m.group(1))), text)
    text = re.sub(r"https?://[^\s<>\x00]+", bare_url, text)
    text = re.sub(r"<sup>(.*?)</sup>",
                  lambda m: keep("\\textsuperscript{%s}" % esc(m.group(1))), text)
    text = re.sub(r"<sub>(.*?)</sub>",
                  lambda m: keep("\\textsubscript{%s}" % esc(m.group(1))), text)
    text = re.sub(r"<br\s*/?>", lambda m: keep("\\newline{}"), text)
    text = esc(text)
    text = text.replace("\u00a0", "~").replace("\u2011", "\\mbox{-}")
    text = re.sub("[\u200b\u200c\u200d\ufeff]", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![*\\\w])\*(?=\S)(.+?)(?<=\S)\*(?![*\w])", r"\\textit{\1}", text)
    text = re.sub(r'"([^"]*)"', r"``\1''", text)
    text = re.sub(r"(?<!\w)'([^']+)'(?!\w)", r"`\1'", text)
    text = re.sub(r"(\d) \\%", r"\1~\\%", text)
    for _ in range(3):                     # stashed pieces can sit inside each other
        text = re.sub("\x00(\\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


# ====================================================================== tables
_FONTS = {}


def text_width_in(text, font_pt, bold=False):
    """Width of a piece of text in inches, measured with the Times font file."""
    key = "timesbd.ttf" if bold else "times.ttf"
    if key not in _FONTS:
        try:
            _FONTS[key] = ImageFont.truetype(key, 200)
        except OSError:
            _FONTS[key] = None
    font = _FONTS[key]
    em = font.getlength(text) / 200.0 if font else 0.5 * len(text) * (1.06 if bold else 1.0)
    return em * font_pt / 72.0


def col_widths(header, rows, total_in, font_pt=TABLE_PT, colsep_pt=COLSEP_PT):
    """Column widths in inches, chosen so that the table is as short as possible."""
    ncol = len(header)
    body = [r for r in rows if not is_group_row(r)]
    avail = total_in - (ncol - 1) * 2 * colsep_pt / 72.0
    pad = 2.0 / 72.0

    def pieces(text):                      # a line can break at a space, a hyphen or a slash
        return re.findall(r"[^\s\-/]+[\-/]?", text) or [""]

    table = [[(plain(c), True) for c in header]] + [[(plain(c), False) for c in r] for r in body]
    full = [[text_width_in(t, font_pt, bold) for t, bold in row] for row in table]
    least = [max(max(text_width_in(w, font_pt, bold) for w in pieces(row[c][0]))
                 for row in table for bold in [row[c][1]]) + pad for c in range(ncol)]
    natural = [max(row[c] for row in full) + pad for c in range(ncol)]
    least = [min(a, b) for a, b in zip(least, natural)]
    if sum(least) >= avail:
        return [avail * x / sum(least) for x in least]

    def height(ws):                        # smooth guess of the table height, in lines
        total = 0.0
        for row in full:
            total += sum(max(1.0, 1.1 * t / w) ** 8 for t, w in zip(row, ws)) ** 0.125
        return total

    widths, step = least[:], 0.02
    budget, h = avail - sum(widths), height(least)
    while budget >= step:
        best, best_h = None, h - 1e-9
        for c in range(ncol):
            if widths[c] >= natural[c]:
                continue
            widths[c] += step
            hc = height(widths)
            widths[c] -= step
            if hc < best_h:
                best, best_h = c, hc
        if best is None:
            break
        widths[best] += step
        budget -= step
        h = best_h
    return widths


def _cell(text):
    t = inline(text)
    return "{}" + t if t.startswith("[") else t


def tabular_parts(header, rows, total_in, font_pt=TABLE_PT):
    """Column spec, header line and body lines of a table."""
    widths = col_widths(header, rows, total_in, font_pt)
    ncol = len(header)
    spec = "@{}" + "".join(">{\\RaggedRight\\arraybackslash}p{%.3fin}" % w for w in widths) + "@{}"
    head = " & ".join("\\textbf{%s}" % inline(c) for c in header) + " \\\\"
    lines = []
    for r in rows:
        if is_group_row(r):
            label = next(c for c in r if c)
            lines.append("\\multicolumn{%d}{@{}l@{}}{%s} \\\\" % (ncol, inline(label)))
        else:
            lines.append(" & ".join(_cell(c) for c in r) + " \\\\")
    return spec, head, "\n\\addlinespace[2pt]\n".join(lines)


def font_cmd(font_pt=TABLE_PT):
    return "\\fontsize{%g}{%g}\\selectfont\\setlength{\\tabcolsep}{%gpt}" % (
        font_pt, font_pt + 1.5, COLSEP_PT)


def tex_longtable(header, rows, total_in, font_pt=TABLE_PT):
    """A table that may break across pages. The header repeats on each page."""
    spec, head, body = tabular_parts(header, rows, total_in, font_pt)
    return ("{" + font_cmd(font_pt) + "\\setlength{\\LTleft}{0pt}\\setlength{\\LTright}{0pt}"
            "\\setlength{\\LTpre}{4pt}\\setlength{\\LTpost}{4pt}\n"
            "\\begin{longtable}{" + spec + "}\n\\toprule\n" + head + "\n\\midrule\n\\endhead\n"
            "\\bottomrule\n\\endfoot\n" + body + "\n\\end{longtable}\n}")


# ====================================================================== blocks to LaTeX
class Ctx:
    """Settings and counters for one document."""

    def __init__(self, textw_in, cwd, figscale=1.0, place="[!htbp]", skip_floats=False):
        self.textw_in = textw_in
        self.cwd = Path(cwd)
        self.figscale = figscale
        self.place = place
        self.skip_floats = skip_floats
        self.nfig = 0
        self.ntab = 0
        self.warnings = []


def figure_size_in(path):
    """Natural width and height of an image file, in inches."""
    im = Image.open(PAPER_DIR / path)
    dpi = im.info.get("dpi", (300, 300))
    return im.size[0] / float(dpi[0]), im.size[1] / float(dpi[1])


def tex_figure(b, ctx):
    ctx.nfig += 1
    src = PAPER_DIR / b["path"]
    if src.exists():
        nat_w, _ = figure_size_in(b["path"])
        w = min(nat_w, ctx.textw_in) * ctx.figscale
        rel = os.path.relpath(src, ctx.cwd).replace("\\", "/")
        pic = "\\includegraphics[width=%.4fin]{\\detokenize{%s}}" % (w, rel)
    else:
        ctx.warnings.append("Figure file not found: %s" % b["path"])
        pic = "\\fbox{Figure file not found: %s}" % tex_code(b["path"])
    cap = ""
    if b.get("caption"):
        cap = "\\vspace{6pt}\n{\\noindent\\itshape %s\\par}" % inline(b["caption"])
    return ("\\begin{figure}%s\n\\setbox\\measbox=\\vbox{\\hsize=\\textwidth\n"
            "{\\centering %s\\par}\n%s}\n\\meas{fig%d}\n\\box\\measbox\n\\end{figure}"
            % (ctx.place, pic, cap, ctx.nfig))


def tex_table(b, ctx):
    ctx.ntab += 1
    if len(b["rows"]) > LONG_TABLE_ROWS:
        title = "{\\noindent\\itshape %s\\par}\n" % inline(b["title"]) if b["title"] else ""
        note = "{\\noindent\\itshape\\footnotesize %s\\par}\n" % inline(b["note"]) if b["note"] else ""
        return title + tex_longtable(b["header"], b["rows"], ctx.textw_in) + "\n" + note
    spec, head, body = tabular_parts(b["header"], b["rows"], ctx.textw_in)
    parts = []
    if b["title"]:
        parts.append("{\\noindent\\itshape %s\\par}\n\\vspace{4pt}" % inline(b["title"]))
    parts.append("{" + font_cmd() + "\n\\noindent\\begin{tabular}{" + spec + "}\n\\toprule\n"
                 + head + "\n\\midrule\n" + body + "\n\\bottomrule\n\\end{tabular}\\par")
    if b["note"]:
        parts.append("\\vspace{3pt}\n\\noindent\\itshape %s\\par" % inline(b["note"]))
    parts.append("}")
    return ("\\begin{table}%s\n\\setbox\\measbox=\\vbox{\\hsize=\\textwidth\n%s}\n"
            "\\meas{table%d}\n\\box\\measbox\n\\end{table}"
            % (ctx.place if b["title"] else "[H]", "\n".join(parts), ctx.ntab))


LIST_OPT = "[itemsep=1pt,parsep=0pt,topsep=3pt,partopsep=0pt,leftmargin=*]"


def tex_list(b):
    out, stack = [], []
    for it in b["items"]:
        env = "enumerate" if it["ordered"] else "itemize"
        while stack and it["indent"] < stack[-1][0]:
            out.append("\\end{%s}" % stack.pop()[1])
        if stack and it["indent"] == stack[-1][0] and stack[-1][1] != env:
            out.append("\\end{%s}" % stack.pop()[1])
        if not stack or it["indent"] > stack[-1][0]:
            stack.append((it["indent"], env))
            out.append("\\begin{%s}%s" % (env, LIST_OPT))
        t = inline(it["text"])
        out.append("\\item " + ("{}" + t if t.startswith("[") else t))
    while stack:
        out.append("\\end{%s}" % stack.pop()[1])
    return "\n".join(out)


def tex_refs(b):
    out = ["{\\small\\RaggedRight",
           "\\begin{list}{}{\\setlength{\\leftmargin}{2.6em}\\setlength{\\labelwidth}{2.2em}"
           "\\setlength{\\labelsep}{0.4em}\\setlength{\\itemsep}{2pt}\\setlength{\\parsep}{0pt}"
           "\\setlength{\\topsep}{2pt}}"]
    for num, text in b["items"]:
        out.append("\\item[{[%s]}] %s" % (num, inline(text)))
    out.append("\\end{list}\\par}")
    return "\n".join(out)


HEAD_CMD = {1: "section", 2: "section", 3: "subsection", 4: "subsubsection"}


def tex_heading(level, text, label=None):
    cmd = HEAD_CMD.get(level, "paragraph")
    return "\\%s*{\\raggedright %s}%s" % (cmd, inline(text),
                                          "\\label{%s}" % label if label else "")


def render_blocks(blocks, ctx, refs_ok=False):
    """LaTeX for a list of blocks."""
    out = []
    for b in blocks:
        k = b["kind"]
        if k == "heading":
            out.append(tex_heading(b["level"], b["text"]))
        elif k == "para":
            out.append("\\textit{%s}" % EMPTY_LINE if is_placeholder(b["text"]) else inline(b["text"]))
        elif k == "figure":
            if not ctx.skip_floats:
                out.append(tex_figure(b, ctx))
        elif k == "table":
            if not ctx.skip_floats:
                out.append(tex_table(b, ctx))
        elif k == "list":
            out.append(tex_list(b))
        elif k == "refs":
            out.append(tex_refs(b) if refs_ok else
                       "\n\n".join("[%s] %s" % (num, inline(t)) for num, t in b["items"]))
        elif k == "code":
            out.append("{\\small\n\\begin{verbatim}\n" + b["text"] + "\n\\end{verbatim}\n}")
        elif k == "quote":
            out.append("\\begin{quote}\n%s\n\\end{quote}" % inline(b["text"]))
    return "\n\n".join(out) + "\n"


# ====================================================================== LaTeX document
PREAMBLE = r"""\documentclass[@@FONT@@pt,letterpaper]{article}
\usepackage{fontspec}
\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{\setmainfont{TeX Gyre Termes}}
\IfFontExistsTF{Consolas}{\setmonofont[Scale=0.88,HyphenChar=None]{Consolas}}{\setmonofont[Scale=0.85,HyphenChar=None]{Courier New}}
\usepackage[letterpaper,margin=@@MARGIN@@in]{geometry}
\usepackage{graphicx}
\usepackage{array,longtable,booktabs,ragged2e}
\usepackage{float,flafter,lscape,enumitem}
\PassOptionsToPackage{hyphens}{url}
\usepackage[hidelinks,pageanchor=false]{hyperref}
\urlstyle{same}
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.8}
\renewcommand{\textfraction}{0.1}
\renewcommand{\floatpagefraction}{0.8}
\setcounter{topnumber}{2}\setcounter{bottomnumber}{2}\setcounter{totalnumber}{3}
\clubpenalty=10000 \widowpenalty=10000
\emergencystretch=8em
\newbox\measbox
\newcommand{\meas}[1]{\typeout{MEAS #1 \the\dimexpr\ht\measbox+\dp\measbox\relax}}
"""


def preamble(font_pt, margin_in):
    return PREAMBLE.replace("@@FONT@@", "%g" % font_pt).replace("@@MARGIN@@", "%g" % margin_in)


def run_latex(tex_path, runs=1, jobname=None):
    """Run xelatex. Returns the PDF path and what the log says."""
    tex_path = Path(tex_path)
    job = jobname or tex_path.stem
    cmd = [ENGINE, "-interaction=nonstopmode", "-halt-on-error", "--disable-installer",
           "-jobname=" + job, tex_path.name]
    log_path = tex_path.with_name(job + ".log")
    pdf_path = tex_path.with_name(job + ".pdf")
    for _ in range(runs):
        try:
            r = subprocess.run(cmd, cwd=tex_path.parent, capture_output=True)
        except FileNotFoundError:
            raise SystemExit("Cannot find '%s'. Install MiKTeX and try again." % ENGINE)
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        if r.returncode != 0 or not pdf_path.exists():
            err = re.findall(r"^!.*(?:\n.*){0,6}", log, flags=re.M)
            raise SystemExit("%s failed for %s. See %s\n%s"
                             % (ENGINE, tex_path.name, log_path, "\n".join(err[:3]) or log[-1500:]))
    flat = log.replace("\n", "")
    return dict(
        pdf=pdf_path, log=log,
        meas={m.group(1): float(m.group(2)) for m in re.finditer(r"MEAS (\w+) ([\d.]+)pt", log)},
        overfull=[float(x) for x in re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)", log)],
        missing=sorted(set(re.findall(r"Missing character: There is no (\S+) in font", log))),
        float_too_large=len(re.findall(r"Float too large for page", flat)),
    )


def aux_pages(aux_path):
    """Page number of every \\label, read from the .aux file."""
    text = Path(aux_path).read_text(encoding="utf-8", errors="replace")
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{[^{}]*\}\{(\d+)\}", text)}


def content_bottom(page, margin_in):
    """How far down the page the content goes, as a share of the text height (0 to 1)."""
    top = margin_in * 72
    text_h = page.rect.height - 2 * top
    bottom = top + text_h
    ymax = top
    for blk in page.get_text("dict")["blocks"]:
        if blk["type"] != 0:
            continue
        for line in blk["lines"]:
            if line["bbox"][1] > bottom + 2 or not line["spans"]:      # page number
                continue
            ymax = max(ymax, min(line["bbox"][3], bottom))
    for im in page.get_image_info():
        ymax = max(ymax, min(im["bbox"][3], bottom))
    return (ymax - top) / text_h
