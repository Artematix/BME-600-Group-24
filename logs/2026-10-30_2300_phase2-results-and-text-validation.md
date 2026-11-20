# Phase 2 results in, text validation running

Date: 2026-10-30 23:00
Who: manager + agents
Asked by: Artemy (continuation of the 2026-10-26 kickoff)

## Asked
- Finish the four analyses, keep the research logs, validate the text pipeline, start the full extraction run.

## Done
- analysis/ACCURACY_V2.md, ERROR_DRIVERS.md, SUBGROUPS.md, SIMULATION_V2.md with scripts, stats JSON and figures 13-28.
- Data problem found by two agents independently: pump-stored "BG" entries are CGM values typed into the pump, not fingersticks. Headline pair set is now verified fingersticks only: 168,990 pairs, 226 people, MARD 13.3 % (was 10.4 % at the midterm).
- Primary uncertainty answered: low-range bias persists after lag correction (6.5 % low below 54) and is concentrated on wear day 1.
- Subgroups: no demographic predicts error; glucose pattern does. Honest nulls recorded.
- Simulation v2: decisions not readings. 20 % low bias skips 7 % of corrections and hides half of high episodes; 10 % does almost nothing to doses.
- Text pilot: 300 reports/min on the GPU; Abbott templates give values, zones, wear days; gold set of 287 built.
- All decisions and reasons: analysis/METHODOLOGY.md and fda-maude/METHODOLOGY.md.

## Also done (2026-10-31 morning)
- preprocess.py: is_verified_fingerstick flag and verified_pairs(); all six scripts re-run, 29,584 stats values identical, 28 figures byte-identical.
- analysis/FINDINGS.md: main finding = sensor missed 28 % of true lows (CI 24-33) and 38 % of shown lows were unconfirmed. Plan promises: 10 done, 5 done differently, 1 not done, 1 in progress.
- Figures 13, 17, 20 titles fixed. requirements.txt pinned to installed versions + scipy, statsmodels, scikit-learn, ollama.
- README rewritten (170 lines) with verified-pair results and new file map. docs/PROJECT_OVERVIEW.md updated.
- Text step: prompt v3 met targets (fault kappa 0.77, outcome 0.745, numbers 96 %). Full run on 124,599 reports started 08:24, ETA about 17:00. Results agent waiting on it.

## Running
- Full extraction run (detached process) and the results agent that will write fda-maude/results/text/TEXT_RESULTS.md and fill FINDINGS.md section 6.

## Decisions
- Headline threshold 180; 200 as a check. Headline pair set = verified fingersticks, all participants; CGM+BGM arm as the plan-promised check.
- Version 1 simulation kept only as an illustration.

## Open questions / next
- Nothing pushed yet. Push list to be shown to Artemy.
- Human check of 100 gold reports by a teammate.
- Phase 1 text results and the join to the simulation lookup table.
