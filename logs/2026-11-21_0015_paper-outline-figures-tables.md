# Paper: outline, number checks, figures and tables

Date: 2026-11-20 evening to 2026-11-21 00:15
Who: manager (outline, word rules) + 12 agents (facts, checks, figures, tables)
Asked by: Artemy

## Asked
- Plan the final paper outline first, prose last. Avoid the usual AI writing faults.
- Artemy's review of the outline (2026-11-20): content fine; too many bare percentages; simple is not the same as short; define "display"; is R3.4 in the right place?

## Done
- `docs/paper/OUTLINE.md`: message, five findings, one block per paragraph, number rules, word list, gap list, objection list (13).
- `docs/paper/FACT_SHEET.md`, `docs/paper/REFERENCES.md` (113 references opened and checked).
- `docs/paper/CHECKS.md`: ten outline numbers checked against source files. Seven needed a wording or base fix.
- New small analyses: `analysis/TAIL_COMPARISON.md`, `analysis/LOW_DETECTION_WINDOW.md`, `fda-maude/results/text/PATTERN_PRECISION.md`, `fda-maude/results/RECALL_COUNT_CHECK.md`, `fda-maude/results/RECALL_DATE_CHECK.md`.
- Display items: `docs/paper/figures/fig1` to `fig4` (png + pdf, scripts, captions), `docs/paper/tables/table1` to `table3` (+ `table3_full.md`, 73 rows).

## Decisions
- Results lines rewritten by the number rules: sensor error as "reads X % too low"; shares as "1 in N (x %)"; one example in mg/dL per error.
- Report demographics moved from R3 to R5 (it supports "who the patient is"). Plain counts go in Table 1.
- Withheld corrections are given as a share of the corrections that were needed (1 in 7 at 20 % too low), not of all calculator uses (7 %).
- Reported error when reading low is 69 to 77 % too low. The old "66" was the median over all malfunction-only pairs.
- By-range accuracy sorts pairs by the average of sensor and meter. Sorted by the meter alone the sensor reads 29.8 % too high under 54. The paper claims the amount of disagreement at low glucose, not its direction.
- Recalls: 32 events (the 33rd, event 99765, is dosing software). Libre 3 recall classified Class I on 2026-01-13; public notice updated 2026-02-04.
- Reference set: labels by Claude Opus 5.5 (high setting); Artemy read 100 of 287 one by one, none changed.
- Pattern pairs: 97 of 100 right in an AI read. "Comparison device" in Abbott's report wording is treated as the meter (Artemy to confirm).

## Open questions / next
- Running: accuracy by range under three sortings (`analysis/ACCURACY_BY_RANGE_SORTING.md`).
- Artemy to confirm: the three wording changes above, event 99765 as not a sensor recall, "comparison device".
- Next: voice sample, then prose (Results, Methods, Discussion, Introduction, Abstract).
- Repo fix list (in the outline) not applied yet. Nothing committed or pushed.
