"""Build the whole paper draft as one PDF and count its pages.

Run:    python -B docs/paper/build/build_paper.py
        (add --png to also save one image per page in docs/paper/build/preview/)
Reads:  docs/paper/PAPER.md, docs/paper/tables/*.md, docs/paper/figures/*.png  (never changed)
Writes: docs/paper/build/paper_draft.pdf, paper_draft.tex, paper_draft.log, PAGE_COUNT_PAPER.md

Layout: Letter page, one column, Times, 10 pt, 0.75 inch margins, single spacing.
The script works while sections are still empty. An empty section prints its
heading and the line "To be added by the team."
"""
import datetime
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

import paperlib as lib

BUILD = lib.BUILD_DIR
FONT_PT, MARGIN_IN = 10, 0.75
TEXTW_IN = lib.PAGE_W_IN - 2 * MARGIN_IN
TEXTH_IN = lib.PAGE_H_IN - 2 * MARGIN_IN
PAGE_LIMIT = 10
FIG_SCALE = 0.8          # figures in the main text as a share of their natural width (set by --fig-scale)
GROUP = "BMEN 600 Group 24"
AUTHORS = "Authors: to be added"
GITHUB = "https://github.com/Artematix/BME-600-Group-24"
NO_TITLE = "Title to be decided"
LANDSCAPE_COLS = 7        # a supplement table with this many columns goes on landscape pages
# Supplement tables that live in their own file. A bullet under
# "## Supplementary material" in PAPER.md that names a file takes priority.
DEFAULT_SUPP = {"S1": "tables/tableS1_analyses.md", "S2": "tables/tableS2_three_faults.md"}
LABEL = re.compile(r"^\s*((?:Table|Figure)\s+S\d+|Appendix\s+\w+)", re.I)
# Parts of a supplement file that are notes for the writers and are never printed.
WORKING_PARTS = ("notes for", "where the numbers come from", "which analyses")
WORDS_PER_PAGE = 1050     # plain text on one full page in this layout (measured in test_layout)
EXPECTED = ["abstract", "introduction", "methods", "results", "discussion", "conclusion",
            "data and code", "ai-assisted", "author contributions"]


# ---------------------------------------------------------------- reading the paper
def split_paper(blocks):
    """Title, the blocks above the first section, and the sections (name, blocks)."""
    title, pre, sections = None, [], []
    for b in blocks:
        if b["kind"] == "heading" and b["level"] == 1 and title is None and not sections:
            title = b["text"]
        elif b["kind"] == "heading" and b["level"] == 2:
            sections.append((b["text"], []))
        elif sections:
            sections[-1][1].append(b)
        else:
            pre.append(b)
    return title, pre, sections


def is_empty(blocks):
    return all(b["kind"] == "heading" or (b["kind"] == "para" and lib.is_placeholder(b["text"]))
               for b in blocks)


def strip_paths(text):
    """Drop a bracket that only names a file, like (`tables/x.md`)."""
    text = re.sub(r"\s*\((?:[^()`]*`[^`]*`)+[^()]*\)", "", text)
    return text


def unit_from_file(path, notes):
    """A supplement table kept in its own file: title, text above, table, notes."""
    blocks = lib.parse_blocks(lib.read_markdown(path))
    title = next((b["text"] for b in blocks if b["kind"] == "heading" and b["level"] == 1),
                 path.stem)
    ti = next((i for i, b in enumerate(blocks) if b["kind"] == "table"), None)
    before = blocks[:ti] if ti is not None else blocks
    mark = next((i for i, b in enumerate(before) if b["kind"] == "para"
                 and b["text"].lower().startswith("text to print above the table")), None)
    if mark is not None:
        intro = [b for b in before[mark + 1:] if b["kind"] == "para"]
        rest = before[mark]["text"].split(":", 1)[1].strip() if ":" in before[mark]["text"] else ""
        if rest:
            intro.insert(0, dict(kind="para", text=rest))
    else:
        intro = [b for b in before if b["kind"] == "para"]
        if intro:
            notes.append("%s has no line \"Text to print above the table:\". The text between "
                         "its title and its table was printed as it is." % path.name)
    foot, i = [], 0
    while i < len(blocks):
        b = blocks[i]
        if b["kind"] == "heading" and b["level"] == 2 and b["text"].strip().lower() == "notes":
            i += 1
            while i < len(blocks) and not (blocks[i]["kind"] == "heading" and blocks[i]["level"] <= 2):
                foot.append(blocks[i])
                i += 1
        else:
            i += 1
    return dict(title=title, intro=intro, table=blocks[ti] if ti is not None else None,
                notes=foot, notes_label=bool(foot))


def unit_from_blocks(title, blocks):
    """A supplement table written inside PAPER.md under a ### heading."""
    ti = next((i for i, b in enumerate(blocks) if b["kind"] == "table"), None)
    if ti is None:
        return dict(title=title, intro=blocks, table=None, notes=[], notes_label=False)
    return dict(title=title, intro=blocks[:ti], table=blocks[ti], notes=blocks[ti + 1:],
                notes_label=False)


def unit_from_whole_file(path, notes):
    """A supplement part that is not one table (an appendix). The whole file is printed."""
    blocks = lib.parse_blocks(lib.read_markdown(path))
    title = next((b["text"] for b in blocks if b["kind"] == "heading" and b["level"] == 1),
                 path.stem)
    body, skip = [], False
    for b in blocks:
        if b["kind"] == "heading":
            if b["level"] == 1:
                continue
            if b["level"] == 2:
                skip = b["text"].strip().lower().startswith(WORKING_PARTS)
            if not skip:
                body.append(dict(b, level=b["level"] + 2))
        elif not skip:
            body.append(b)
    notes.append("%s was printed in full from %s. Check that it holds no working notes."
                 % (title.split(".")[0], path.name))
    return dict(title=title, intro=body, table=None, notes=[], notes_label=False)


def supplement_units(blocks, notes):
    """The list under the heading (file paths removed) and the parts, in order."""
    first_sub = next((i for i, b in enumerate(blocks)
                      if b["kind"] == "heading" and b["level"] == 3), len(blocks))
    lead = blocks[:first_sub]
    subs = []
    for b in blocks[first_sub:]:
        if b["kind"] == "heading" and b["level"] == 3:
            subs.append((b["text"], []))
        else:
            subs[-1][1].append(b)
    entries = []              # (label, file or None), in the order of the list
    for b in lead:
        if b["kind"] != "list":
            continue
        for it in b["items"]:
            m = LABEL.match(lib.plain(it["text"]))
            p = re.search(r"`([^`]+\.md)`", it["text"])
            if m:
                entries.append((re.sub(r"\s+", " ", m.group(1)), p.group(1) if p else None))
            it["text"] = strip_paths(it["text"])
    named = {label.lower() for label, _ in entries}
    for key, path in DEFAULT_SUPP.items():
        if ("table " + key).lower() not in named:
            entries.append(("Table " + key, path))
    lead = [b for b in lead if not (b["kind"] == "para" and lib.is_placeholder(b["text"]))]
    for b in lead:
        if b["kind"] == "para":
            b["text"] = strip_paths(b["text"])
    units, used = [], set()
    for label, path in entries:
        sub = next((x for x in subs if re.match(re.escape(label) + r"\b", x[0], re.I)), None)
        f = lib.PAPER_DIR / path if path else None
        if sub is not None:
            units.append(unit_from_blocks(sub[0], sub[1]))
            used.add(sub[0])
        elif f is not None and f.exists():
            units.append(unit_from_file(f, notes) if label.lower().startswith("table")
                         else unit_from_whole_file(f, notes))
        else:
            why = "its file %s was not found" % path if path else "no text for it was found"
            notes.append("%s is named in the supplement list, but %s. It is not in the PDF."
                         % (label, why))
    for name, blks in subs:
        if name not in used:
            units.append(unit_from_blocks(name, blks))
    return lead, units


# ---------------------------------------------------------------- LaTeX
def title_page(title, authors):
    return "\n".join([
        "\\begin{titlepage}", "\\centering", "\\vspace*{2.3in}",
        "{\\LARGE\\bfseries %s\\par}" % lib.inline(title), "\\vspace{0.6in}",
        "{\\Large %s\\par}" % lib.inline(GROUP), "\\vspace{0.3in}",
        "{\\large %s\\par}" % lib.inline(authors), "\\vspace{0.6in}",
        "{\\large %s\\par}" % lib.tex_url(GITHUB), "\\end{titlepage}"])


def render_unit(u, k, lead_tex):
    t = u["table"]
    land = t is not None and len(t["header"]) >= LANDSCAPE_COLS
    width = TEXTH_IN if land else TEXTW_IN
    ctx = lib.Ctx(width, BUILD)
    out = ["\\begin{landscape}" if land else "\\clearpage"]
    if lead_tex:
        out.append(lead_tex)
    out.append(lib.tex_heading(3, u["title"], "supp:%d" % k))
    if u["intro"]:
        out.append(lib.render_blocks(u["intro"], ctx))
    if t is not None:
        out.append(lib.tex_longtable(t["header"], t["rows"], width))
        if t.get("note"):
            out.append("{\\noindent\\itshape\\footnotesize %s\\par}" % lib.inline(t["note"]))
    if u["notes"]:
        if u["notes_label"]:
            out.append("\\smallskip\\noindent\\textbf{Notes}\\par")
        out.append("{\\footnotesize\n" + lib.render_blocks(u["notes"], ctx) + "\\par}")
    if land:
        out.append("\\end{landscape}")
    return "\n\n".join(out), land


def build_tex(notes):
    blocks = lib.parse_blocks(lib.read_markdown(lib.PAPER))
    title, pre, sections = split_paper(blocks)
    if not title or title.strip().lower().startswith("[title"):
        title = NO_TITLE
    authors = AUTHORS
    for b in pre:
        text = lib.plain(b.get("text", "")).strip()
        if b["kind"] == "para" and text.lower().startswith("authors:"):
            authors = text
        elif b["kind"] == "para" and text.lower().startswith("draft state"):
            pass                                    # working note, never printed
        else:
            notes.append("Not printed (it stands above the first section): \"%s...\""
                         % text[:60])
    main = [(n, b) for n, b in sections
            if not n.lower().startswith(("references", "supplement"))]
    refs = next((b for n, b in sections if n.lower().startswith("references")), [])
    supp_name, supp = next(((n, b) for n, b in sections if n.lower().startswith("supplement")),
                           ("Supplementary material", []))
    for word in EXPECTED:
        if not any(word in n.lower() for n, _ in main):
            notes.append("No section with \"%s\" in its heading was found in PAPER.md." % word)

    ctx = lib.Ctx(TEXTW_IN, BUILD, figscale=FIG_SCALE)
    doc = [lib.preamble(FONT_PT, MARGIN_IN), "\\begin{document}", title_page(title, authors)]
    info = []                 # (label, name, words, empty) for the report
    for k, (name, blks) in enumerate(main):
        doc.append(lib.tex_heading(2, name, "sec:%d" % k))
        empty = is_empty(blks)
        doc.append("\\textit{%s}\n" % lib.EMPTY_LINE if empty else lib.render_blocks(blks, ctx))
        info.append(("sec:%d" % k, name, lib.words_in(blks), empty))
    doc.append("\\clearpage")
    doc.append(lib.tex_heading(2, "References", "sec:refs"))
    refs_empty = is_empty(refs)
    doc.append("\\textit{%s}\n" % lib.EMPTY_LINE if refs_empty
               else lib.render_blocks(refs, ctx, refs_ok=True))
    info.append(("sec:refs", "References", None, refs_empty))

    lead, units = supplement_units(supp, notes)
    lead_tex = lib.tex_heading(2, supp_name, "sec:supp")
    if lead:
        lead_tex += "\n\n" + lib.render_blocks(lead, ctx)
    info.append(("sec:supp", supp_name, None, False))
    land = []
    if not units:
        doc.append("\\clearpage\n" + lead_tex)
    for k, u in enumerate(units):
        tex, is_land = render_unit(u, k, lead_tex if k == 0 else "")
        doc.append(tex)
        info.append(("supp:%d" % k, u["title"], None, False))
        land.append(is_land)
    doc.append("\\end{document}\n")
    notes.extend(ctx.warnings)
    return "\n\n".join(doc), info, land, title


# ---------------------------------------------------------------- build and count
def save_pdf(tmp_pdf, land_ranges, notes, now):
    """Turn the landscape pages upright and save the final PDF."""
    doc = fitz.open(tmp_pdf)
    for a, b in land_ranges:
        for idx in range(a, min(b, doc.page_count - 1) + 1):
            doc[idx].set_rotation(90)
    final = BUILD / "paper_draft.pdf"
    try:
        doc.save(final, garbage=3, deflate=True)
    except Exception:                        # the old PDF is open in a viewer
        final = BUILD / ("paper_draft_%s.pdf" % now.strftime("%H%M%S"))
        doc.save(final, garbage=3, deflate=True)
        notes.append("paper_draft.pdf was open in another program, so the new PDF is %s. "
                     "Close the old one and run again." % final.name)
    return doc, final


def main():
    now = datetime.datetime.now()
    saved = datetime.datetime.fromtimestamp(lib.PAPER.stat().st_mtime)
    notes = []
    tex, info, land, title = build_tex(notes)
    tex_path = BUILD / "paper_draft.tex"
    tex_path.write_text(tex, encoding="utf-8", newline="\n")
    res = lib.run_latex(tex_path, runs=2, jobname="paper_draft_tmp")
    pages = lib.aux_pages(BUILD / "paper_draft_tmp.aux")

    # Printed page numbers start at 1 on the page after the title page.
    # So the page in the PDF file is the printed number plus 1.
    supp_starts = [pages[lab] for lab, _, _, _ in info if lab.startswith("supp:")]
    total = fitz.open(res["pdf"]).page_count
    land_ranges = []
    for k, is_land in enumerate(land):
        if is_land:
            end = supp_starts[k + 1] - 1 if k + 1 < len(supp_starts) else total - 1
            land_ranges.append((supp_starts[k], end))
    doc, final = save_pdf(res["pdf"], land_ranges, notes, now)

    counted = pages["sec:refs"] - 1
    fill = lib.content_bottom(doc[counted], MARGIN_IN) if counted >= 1 else 0.0
    refs_pages = pages["sec:supp"] - pages["sec:refs"]
    supp_pages = total - 1 - (pages["sec:supp"] - 1)
    if res["missing"]:
        notes.append("The font cannot print these characters, so they are missing in the PDF: "
                     + " ".join(res["missing"]))
    wide = [x for x in res["overfull"] if x > 3]
    if wide:
        notes.append("%d line%s past the right margin (the worst by %.0f pt). "
                     "Look for a long word, link or file name."
                     % (len(wide), " runs" if len(wide) == 1 else "s run", max(wide)))
    if res["float_too_large"]:
        notes.append("%d figure or table is taller than a page." % res["float_too_large"])
    doc.close()

    for ext in (".aux", ".out", ".pdf"):
        f = BUILD / ("paper_draft_tmp" + ext)
        if f.exists():
            f.unlink()
    (BUILD / "paper_draft_tmp.log").replace(BUILD / "paper_draft.log")

    over = counted - PAGE_LIMIT
    if over > 0:
        verdict = "Over the limit by %d page%s." % (over, "" if over == 1 else "s")
    elif over == 0:
        verdict = "At the limit. Only the rest of the last counted page is free."
    else:
        verdict = ("Within the limit. %d whole page%s free, plus the rest of the last counted page."
                   % (-over, " is" if over == -1 else "s are"))
    room = max(0.0, (PAGE_LIMIT - counted) + (1 - fill)) * WORDS_PER_PAGE
    empty = [name for _, name, _, e in info if e]
    L = ["# Page count of the paper draft",
         "Built on %s at %s from `docs/paper/PAPER.md` (saved at %s). PDF: `docs/paper/build/%s`."
         % (now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), saved.strftime("%H:%M"), final.name),
         "",
         "Title: %s" % title,
         "",
         "## The count that matters",
         "| What | Value |",
         "|---|---|",
         "| Pages that count (Abstract to the end of Author Contributions) | %d |" % counted,
         "| Page limit | %d |" % PAGE_LIMIT,
         "| How full the last counted page is | %.0f %% |" % (100 * fill),
         "| Room left before the limit, in words of plain text (about) | %d |"
         % (round(room / 10.0) * 10),
         "| All pages in the PDF | %d |" % total,
         "| Title page (not counted) | 1 |",
         "| References (not counted) | %d |" % refs_pages,
         "| Supplement (not counted) | %d |" % supp_pages,
         "",
         verdict + (" %d section%s still empty, so the count will grow."
                    % (len(empty), " is" if len(empty) == 1 else "s are") if empty else ""),
         "The number printed at the bottom of a page is the count up to that page. "
         "The title page has no number.",
         "",
         "## Where each section starts",
         "| Section | Page number printed | Page in the PDF file | Words | State |",
         "|---|---|---|---|---|",
         "| Title page | none | 1 | | |"]
    for lab, name, words, is_e in info:
        p = pages[lab]
        L.append("| %s | %d | %d | %s | %s |" % (
            name, p, p + 1, "" if words is None else "{:,}".format(words),
            "empty" if is_e else ("written" if words is not None or lab == "sec:refs" else "")))
    L += ["", "## Sections still empty"]
    L += ["- " + n for n in empty] or ["- None."]
    L += ["", "## Things to check"]
    L += ["- " + n for n in notes] or ["- Nothing found."]
    text = "\n".join(L) + "\n"
    (BUILD / "PAGE_COUNT_PAPER.md").write_text(text, encoding="utf-8", newline="\n")
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))

    if "--png" in sys.argv:
        out = BUILD / "preview"
        out.mkdir(exist_ok=True)
        for f in out.glob("page_*.png"):
            f.unlink()
        pdf = fitz.open(final)
        for i, page in enumerate(pdf):
            page.get_pixmap(dpi=80).save(out / ("page_%02d.png" % (i + 1)))
        print("Page images: %s" % out)


if __name__ == "__main__":
    main()
