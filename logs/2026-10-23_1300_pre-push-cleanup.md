# 2026-10-23 13:00 - Pre-push cleanup and README rewrite

## Asked
- Clean the repo for a public push (the instructor reads it). Match the midterm rubric. Make it easy to continue on a new computer.
- Remove the unused dataset (OhioT1DM). Make the README clear and the run steps correct.
- Earlier the same session: figure 12 (layout, legend box), MAUDE fig4 (legend box), figure 09 (grey note removed, A/B/C panel titles).

## Who did it
- Agents: file audit, clean-copy reproduction test, rubric check, plan PDF check, fda-maude fixes, analysis/docs/logs fixes, README rewrite.
- Manager: file moves, README trims, final scan, this log.

## Produced / changed
- README.md rewritten: research question from the submitted plan, status, key results, "which file makes what", datasets, reproduce steps, files git does not give you, file map.
- requirements.txt (root, pinned, includes requests). analysis/requirements.txt removed.
- Phase 1 (fda-maude/scripts, results, access-check) added to the push for the first time. Status text updated to "done".
- Submitted midterm plan: docs/plans/2026-10-23_midterm-research-plan.pdf. Old 2026-10-14 drafts removed from the tree.
- Removed: analysis/RESULTS_detailed.md (superseded). Change-notes .docx kept local (gitignored).
- docs/rubrics/ gitignored (course documents).
- Scripts: clear "data not found" and --help messages. No analysis logic changed.
- Logs and PROJECT_OVERVIEW.md: internal critique of team drafts removed or made neutral.

## Checks
- Phase 1 report rerun in a fresh copy with a new venv: all figures and tables byte-identical.
- Phase 2 scripts not rerun: raw data is on the new computer. Figures 09 and 12 were edited from saved outputs.

## Decisions
- Bias above 70 mg/dL is shown under both groupings. The plan's "1-4 %" (Dexcom) is by reference value; "7-8 %" (Libre H) is by average.
- No contributions table in the README (it belongs in the report PDF).

## Open
- Rerun both Phase 2 scripts on the new computer and confirm numbers match.
- Plan PDF names `maude_pull.py` and "Table 2 / Figures 1-3". The README maps these to real files.
