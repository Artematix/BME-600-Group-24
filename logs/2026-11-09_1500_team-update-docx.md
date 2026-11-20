# Team update and paper plan (Word document)

Date: 2026-11-09 15:00 (finished 2026-11-10 00:20)
Who: manager (content, review) + 1 agent (number check, build, figure fixes)
Asked by: Artemy

## Asked
- Check the overview and paper structure. Turn it into a 2 to 3 page Word document for the group.
- Easy to digest. Plain, scientific wording. Methods skeleton, key data, figures, academic styling.

## Done
- `docs/team-docs/2026-11-09_team-update-and-paper-plan.docx` and `.pdf`. Body 3 pages, then 3 figure pages. Local only (gitignored).
- `docs/team-docs/build_team_update.py` rebuilds it (`--pdf` renders through Word).
- `docs/team-docs/2026-11-09_team-update_number-check.md`: 169 numbers, each traced to a source. 26 corrected.
- Order: status, question and findings, key data (4 tables), paper outline and Methods skeleton, limitations, next steps, figures.
- Two figure flaws fixed at the source (plot lines only; all numbers unchanged):
  `fda-maude/scripts/brand_comparison.py` (clipped axis label, t8), `analysis/wear_day.py` (title prefix and empty band, fig 33).
- Status notes corrected in `docs/PROJECT_OVERVIEW.md`, `analysis/FINDINGS.md`, `fda-maude/results/text/VALIDATION.md`.

## What the check found (why some numbers changed)
- Missed lows 28 % and unconfirmed sensor lows 38 % are the CGM+BGM arm (77 people). All 226 people: 31 % and 41 %.
- The 287-report reference set was labelled by one AI reviewer, not by hand. A teammate checked 100.
- "12 %" is where insulin corrections start to be withheld. A third of high episodes are already hidden there.
- Lookup at -40 % bias: 32.6 % of decisions withheld, 88.7 % of high episodes hidden (older notes said 31 and 87).
- Dexcom reads-low median in the brand set is -69 % (the text memo's -68 % is a different pair set).

## Decisions
- Figures go in an appendix after the 3-page body. They do not fit inside 2 to 3 pages.
- Research question restated in formal wording for the team. Same question.
- Three-fault simulation: approved in principle by Artemy 2026-11-09. Written as "planned". Not started.

## Open questions / next
- Which missed-low number leads in the paper: 28 % (arm that confirmed with a meter) or 31 % (everyone).
- Simulation waits on two choices: episode length (2, 6, 12 h suggested) and a sugar rule (15 g under 70 suggested).
- File paths in the document point to repo files that are not pushed yet. Push still waits for Artemy's word.
- Body text is 10 pt to hold 3 pages.
