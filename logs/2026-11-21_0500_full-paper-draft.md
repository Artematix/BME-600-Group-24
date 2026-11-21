# Paper: Results revised, all other sections drafted, checked and built as a PDF

Date: 2026-11-21
Who: manager (all prose, reference numbering script) + agents (exact values list, number checks, fresh-reader checks, rubric check, PDF builder, Appendix A)
Asked by: Artemy

## Asked
- Artemy read the Results line by line and gave about 25 edits. He asked not to have to repeat them in other sections.
- Use the team's working draft of the paper for the remaining sections, and fill what is missing.
- Do not write "AI-Assisted Work" or "Author Contributions".
- Later: do not cut text for length, the Conclusion is too short, save a PDF, push.

## Done
- `docs/paper/PAPER.md`: every section has text except the two statements the team writes. About 6,900 words.
- `docs/paper/PAPER.pdf`: the built paper. 10 counted pages, 39 references numbered in order of first use, then Appendix A and Tables S1 to S3.
- `docs/paper/PAPER_numbered.md`: the same text with the final reference numbers, for copying into Word.
- `docs/paper/OUTLINE.md`: 14 sentence rules from Artemy's read, and a new number rule (one form per number).
- `docs/paper/tables/tableS3_exact_values.md` and `appendixA_datasets.md`: new supplement parts.
- Checks, all applied: `CHECKS_RESULTS_PROSE_v2.md`, `CHECKS_STYLE_v1.md`, `CHECKS_NEW_SECTIONS.md` (91 statements), `CHECKS_RUBRIC.md` (38 rubric rows, 25 sentences).
- Build: `python -B docs/paper/build/build_numbered.py`. Page count: `docs/paper/PAGE_COUNT.md`.

## Decisions
- Pairs read from report texts are called "report pairs". Trial pairs stay "pairs".
- The main accuracy analysis uses all 226 participants. The routine-check arm (77 participants) is the check.
- No text was cut for length (Artemy). To stay inside 10 pages the PDF uses 10 pt text, 0.75 inch margins and figures at 80 % of their size.
- Citations from the team's draft were kept. Where our reference notes had a better-covered source, it was added next to theirs.

## Open questions / next
- Room for the two team statements: about 170 words at the current layout. More room needs smaller figures (75 % gives about 290 words) or a cut.
- The rubric does not say whether pages after the references (supplement) count toward the 10 pages. Ask the instructor.
- To confirm: references [110] and [111] (written from memory), six citations that our notes do not cover (rows 19 to 24 of `CHECKS_NEW_SECTIONS.md`), the download date 7 October 2026 for the trial and Shanghai data.
- Not explained in the text yet: why 14 of the 112 Shanghai patients have no pair.
- `analysis/REPRODUCIBILITY.md` does not list the three newest scripts yet.
- The graded commit id goes into the data statement at submission.
