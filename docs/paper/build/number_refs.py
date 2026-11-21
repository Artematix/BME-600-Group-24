"""Renumber the citations of PAPER.md in order of first use (IEEE style) and build the reference list.

Run from the repo root:  python -B docs/paper/build/number_refs.py
Reads:  docs/paper/PAPER.md, docs/paper/REFERENCES.md, docs/paper/tables/appendixA_datasets.md  (never changed)
Writes: docs/paper/build/PAPER_numbered.md, appendixA_numbered.md, REFERENCE_MAP.md

PAPER.md keeps the working numbers of REFERENCES.md. Only the copies in build/ get the new numbers.
"""
import re
from pathlib import Path

BUILD = Path(__file__).resolve().parent
PAPER_DIR = BUILD.parent
CITE = re.compile(r"\[(\d{1,3})\]")
NOTES_MARK = "<!-- notes, not for the paper -->"


def load_references():
    """Return {working number: (reference text, link)} from both layouts used in REFERENCES.md."""
    lines = (PAPER_DIR / "REFERENCES.md").read_text(encoding="utf-8").split("\n")
    refs = {}
    for i, line in enumerate(lines):
        m = re.match(r"^\*\*\[(\d+)\]\*\*\s+(.*)$", line)
        if m:
            link = ""
            for nxt in lines[i + 1:i + 4]:
                lm = re.match(r"^- Link:\s*(\S+)", nxt)
                if lm:
                    link = lm.group(1)
                    break
            refs[int(m.group(1))] = (m.group(2).strip(), link)
            continue
        m = re.match(r"^\|\s*\[(\d+)\]\s*\|\s*(.*?)\s*\|\s*(\S*)\s*\|", line)
        if m and int(m.group(1)) not in refs:
            refs[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())
    return refs


def clean(text, link):
    """Drop working notes and give web sources their address."""
    text = re.sub(r"\s*Midterm refs? \[\d+\](?: to \[\d+\])?\.?", "", text)
    text = re.sub(r"\s*These are refs \[\d+\] to \[\d+\] of the midterm plan\.?", "", text)
    text = text.strip()
    is_web = "[Online]" in text or "Accessed:" in text
    if is_web and link.startswith("http"):
        text = text.replace(" [Online].", "").rstrip()
        if not text.endswith("."):
            text += "."
        text += " [Online]. Available: " + link
    return text


def main():
    paper = (PAPER_DIR / "PAPER.md").read_text(encoding="utf-8")
    a = paper.index("## References")
    b = paper.index("## Supplementary material")
    body, supp = paper[:a], paper[b:]

    app_path = PAPER_DIR / "tables" / "appendixA_datasets.md"
    appendix = app_path.read_text(encoding="utf-8") if app_path.exists() else ""
    if NOTES_MARK in appendix:
        appendix = appendix[:appendix.index(NOTES_MARK)]

    order = []
    for part in (body, appendix, supp):
        for m in CITE.finditer(part):
            n = int(m.group(1))
            if n not in order:
                order.append(n)
    new = {old: k + 1 for k, old in enumerate(order)}
    swap = lambda m: "[%d]" % new[int(m.group(1))]

    refs = load_references()
    missing = [n for n in order if n not in refs]
    ref_lines, map_rows = [], []
    for old in order:
        text = clean(*refs[old]) if old in refs else "MISSING REFERENCE (working number %d)" % old
        ref_lines.append("[%d] %s" % (new[old], text))
        map_rows.append("| %d | %d | %s |" % (new[old], old, text[:70].replace("|", "/")))

    supp_new = CITE.sub(swap, supp).replace("tables/appendixA_datasets.md", "build/appendixA_numbered.md")
    out = CITE.sub(swap, body) + "## References\n\n" + "\n\n".join(ref_lines) + "\n\n" + supp_new
    (BUILD / "PAPER_numbered.md").write_text(out, encoding="utf-8", newline="\n")
    if appendix:
        (BUILD / "appendixA_numbered.md").write_text(CITE.sub(swap, appendix), encoding="utf-8", newline="\n")
    (BUILD / "REFERENCE_MAP.md").write_text(
        "# Reference numbers\n\nNew number = order of first use in the paper. Working number = the number in `docs/paper/REFERENCES.md`.\n\n"
        "| New | Working | Reference (first words) |\n|---|---|---|\n" + "\n".join(map_rows) + "\n",
        encoding="utf-8", newline="\n")
    print("references in the list:", len(order), "| missing entries:", missing or "none")
    return len(order), missing


if __name__ == "__main__":
    main()
