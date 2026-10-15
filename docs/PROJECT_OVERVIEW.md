# Project overview

Last updated: 2026-10-09

## The problem (why we care)

- CGMs (continuous glucose monitors) read blood sugar every 5 minutes. People with diabetes dose insulin from them.
- In 2025 the FDA recalled ~3 million Abbott FreeStyle Libre 3 sensors. They read too LOW.
- Result: 860 serious injuries, 7 deaths. People ate sugar they didn't need, or skipped insulin.
- Our question: how wrong does a sensor have to be before it changes a treatment decision?

## Two phases

### Phase 1. FDA report mining (preliminary, guides Phase 2)
- Pull FDA recall records and MAUDE problem reports for CGM sensors.
- Sort them by what went wrong, using an LLM. Count by type, brand, time.
- Output: a list of real sensor failure types and how common / harmful each is.
- Teammates use this to (a) decide what to simulate in Phase 2 and (b) write insights.
- Big enough to be its own section of the report. Scope stays open until we see the data.
- Details: `fda-maude/README.md`.

### Phase 2. Sensor accuracy + failure simulation (main)
- Compare CGM readings to fingerstick readings (the "truth") in real data.
- Measure error by range: low / normal / high blood sugar.
- Then simulate failing sensors on the real traces. Many possible faults:
  constant low bias, drift over wear days, extra noise, dropouts, lag, pressure lows, etc.
  Phase 1 tells us which ones matter. "Reads too low by X%" is just one example.
- Measure how treatment decisions change under each fault.
- No machine learning needed. Stats + simulation.

## Data we have

| Dataset | What | Status | Role |
|---|---|---|---|
| REPLACE-BG | 226 adults, type 1, Dexcom G4, 26 weeks, 14.8M CGM rows (13.7M in study window), 475,502 meter pairs | Downloaded, explored | PRIMARY |
| Shanghai T1DM/T2DM | 112 patients, flash CGM, ~2 weeks each, 4k pairs | Downloaded, explored | Comparator only (too few low readings) |
| OhioT1DM | 12 patients, 8 weeks | Not downloaded. Needs data agreement | Maybe later |

Data lives in `Uncommitted Data/Raw Data Dump/`. Not in git. Each teammate needs their own copy.

## What the first exploration found (details: analysis/RESULTS.md)

- REPLACE-BG has thousands of low-range pairs. Enough to answer our question. Big uncertainty from README is resolved.
- Shanghai has only 37 low-range pairs. Not enough on its own.
- Both sensors read a bit low in normal/high range. Same direction as the recall fault. Good for us.
- Pitfall: in the low range, the error direction flips depending on how you group the data. Must handle carefully.
- Pitfall: 7% of REPLACE-BG CGM rows are from before the study started. Must filter.
- Both cohorts are narrow (adults only, REPLACE-BG 94% White, Shanghai all Chinese adults recruited through hospitals).

## Deadline (from team docs, see docs/team-docs/)

| Date | What |
|---|---|
| Oct 13, 1 PM | Online team meeting. Polish draft. |
| **Oct 16, 11:59 PM** | **Midterm Research Plan due.** Max 6 pages PDF + GitHub link. 15% of grade. |

- Required sections: Intro, Background (6+ scholarly sources), Dataset, Methods, Preliminary Results (real figure), Teamwork. Plus data/code availability, AI-use statement, author contributions, IEEE references.
- Repo must have: README with research question + data access + file map + how to run; working code that makes the figure; clean layout.
- Draft so far: Intro, Background, Dataset written. Methods, Results, Teamwork empty. Many placeholders.

## Problems found in team docs (must fix before Oct 16)

- Research question conflict. The draft asks about "people affected by the recalled sensors, demographics and time of day". No such dataset exists. The README asks about sensor error by range + a fault simulation. We have data for the README version. Team must pick one. Recommendation: README version.
- Factual errors: draft says sensors read "high or low" (FDA: low only). Notes say "insulin sensor" (it measures glucose). "Diabetes = autoimmune" is only true for type 1.
- Injury count: 736 vs 860. Use the latest FDA number and cite it.
- References are APA. Course wants IEEE. Only 3 scholarly sources; need 6+.
- Team size: assignment says 3-4, we have 5. Ask instructor.

## Status

| Item | State |
|---|---|
| Repo organized, manager rules, logging | Done 2026-10-07 |
| First data exploration | Done. Figure 09 fixed and Parkes error grid added 2026-10-09. See analysis/REPRODUCIBILITY.md |
| Team docs summarized | Done 2026-10-07, 6 PDFs, see docs/team-docs/ |
| Research plan (deliverable 1) | Final draft 2026-10-14: docs/plans/2026-10-14_midterm-research-plan.pdf. Change-notes version for the team: ..._change-notes.docx. Team to fill [CONFIRM]/[DATE] items, then submit Oct 16 |
| Phase 1: FDA/MAUDE mining | Not started, folder + plan exist |
| Phase 2: fault simulation | First version done 2026-10-09 (constant low bias 10/20/30%). See analysis/SIMULATION_RESULTS.md. More fault types wait on Phase 1 |

## Open questions

- Parkes grid zone borders were typed from memory of the paper. Check against the PDF before the report.

- Does Phase 1 (FDA mining) stay in the plan? The lead's research description does not mention it.

- Which treatment rules to simulate: fixed thresholds (70/180), real pump dose-calculator events, or both?
- Headline accuracy set: decided 2026-10-14. Meter pairs are primary; calibration pairs reported alongside.

- Which treatment decision rules do we simulate? (e.g. "treat hypo if CGM < 70", "correction bolus if CGM > 180")
- Which sensor fault types do we simulate? Wait for Phase 1 results.
- Robot vs openFDA API for MAUDE?
- Do we need OhioT1DM at all?
