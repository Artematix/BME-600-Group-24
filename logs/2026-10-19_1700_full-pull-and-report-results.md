# Full pull launched + report-ready results

Date: 2026-10-19 17:00
Who: manager + 2 general-purpose agents (full pull; report results)
Asked by: Artemy

## Asked
- Use the new free API key and run the full pull (all 3.38 M CGM reports).
- Give all useful results so far for the report draft.

## Done
- API key saved as Windows user env var OPENFDA_API_KEY. Never in the repo. Robot sends it in a header and scrubs logs (0 hits checked).
- Tier 3 sample finished: 5,193 malfunction reports (clean/sample.csv.gz).
- Tier 5 `full` command added (4 workers). Running as a detached process. ~3.5 M reports/hour. Manager spot-check: narratives present.
- fda-maude/results/report/: report_results.md, 6 figures, 31 tables. Script: fda-maude/scripts/report_results.py. Uses tier 1 counts, tier 2 serious, recalls only.

## Decisions
- Full pull approved by Artemy (earlier recommendation was targeted text pulls instead).
- Report numbers do not wait for the full pull. Counts already cover all reports.

## Findings worth remembering
- Libre: 7-14 injuries per 100 reports. Dexcom: 1-2. guess: partly company filing habits.
- Libre 3 serious reports spike by EVENT date in Dec 2025 (779) and Aug 2024. Corrects earlier "no spike" note, which was for all reports.
- Dexcom "Low Readings" code barely used before mid-2025. guess: coding change.

## Open questions / next
- After the full pull ends: `py -3.11 scripts/maude_robot.py clean --tiers full` (from fda-maude/).
- LLM labelling plan. Commit when Artemy asks.
