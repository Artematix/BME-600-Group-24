# Paper: Results revised, all other sections drafted, PDF build

Date: 2026-11-21
Who: manager (all prose, cuts, reference numbering script) + agents (exact values list, number re-check, fresh-reader check, test layout, PDF builder, Appendix A)
Asked by: Artemy

## Asked
- Artemy read the Results line by line and gave about 25 edits. He asked not to have to repeat them in other sections.
- Use the team's working draft of the paper for the remaining sections. Fill what is missing (Conclusion, parts of Discussion and Abstract).
- Do not write "AI-Assisted Work" or "Author Contributions".
- Later: do not cut for length, the Conclusion is too short, push the results.

## Done
- `docs/paper/PAPER.md`: every section has text except the two statements the team writes.
  - Results, third version. All edits applied. Bracketed percentages replaced by small raised letters that point to Table S3.
  - Methods, Introduction, Abstract, Discussion, Conclusion and the data statement. They build on the team's working draft, put into the paper's language rules.
- `docs/paper/OUTLINE.md`: 14 sentence rules from Artemy's read, and a new number rule (one form per number).
- `docs/paper/tables/tableS3_exact_values.md`: the exact value behind each raised letter, with source file and field.
- `docs/paper/tables/appendixA_datasets.md`: more detail on the data sources and responsible use (supplement).
- `docs/paper/build/`: `build_numbered.py` builds the PDF. It renumbers citations in order of first use and prints the reference list. The PDF itself is not in git.
- `docs/paper/CHECKS_RESULTS_PROSE_v2.md`, `CHECKS_STYLE_v1.md`, `CHECKS_NEW_SECTIONS.md`: the check reports.
- Figure 1 labels changed (no semicolons, "report pairs").

## Decisions
- Pairs read from report texts are now called "report pairs". Trial pairs stay "pairs".
- The main accuracy analysis uses all 226 participants. The arm that checked with a meter routinely (77 participants) is the check.
- Two references were added from memory and are marked "not opened" in `REFERENCES.md` ([110], [111]). They must be opened and confirmed.
- Layout of the test PDF: 10 pt, 0.75 inch margins. The rubric sets no font or margins.

## Open questions / next
- Length. The PDF is at the 10-page limit before the two team statements are added. Artemy chose not to cut text. Smaller figures in the build are the fallback.
- The rubric check and the fresh-reader check of the new sections did not finish (network and login errors). To redo.
- The fixes from `CHECKS_NEW_SECTIONS.md` are not all applied yet.
- The rubric does not say whether a supplement counts toward the 10 pages.
