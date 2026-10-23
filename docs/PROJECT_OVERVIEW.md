# Project overview

Last updated: 2026-10-23

## The problem (why we care)

- CGMs (continuous glucose monitors) read blood sugar every 5 minutes. People with diabetes dose insulin from them.
- In 2025 the FDA recalled about 3 million Abbott FreeStyle Libre 3 sensors. They read too LOW.
- Abbott reported 860 serious injuries and 7 deaths to the FDA. People ate sugar they did not need, or skipped insulin.
- Our question: how wrong does a sensor have to be before it changes a treatment decision?

## Two phases

### Phase 1. FDA report mining (done; guides Phase 2)
- Pulled FDA recall records and MAUDE problem reports for CGM sensors. MAUDE = the FDA database of medical device problem reports.
- Used the openFDA API (the FDA's public data service). No web scraping.
- Counted reports by problem type, brand, year and country.
- Planned: sort report texts by what went wrong, using an LLM (large language model, an AI text tool).
- Details: `fda-maude/README.md`. Results: `fda-maude/results/report/report_results.md`.

### Phase 2. Sensor accuracy + failure simulation (main)
- Compare CGM readings to fingerstick readings (the "truth") in real data.
- Measure error by range: low / normal / high blood sugar.
- Then simulate failing sensors on the real traces. Many possible faults: constant low bias, drift over wear days, extra noise, dropouts, lag, pressure lows.
- Phase 1 tells us which faults matter. "Reads too low by X %" is one example.
- Measure how treatment decisions change under each fault.
- No machine learning needed. Stats + simulation.

## Data we use

| Dataset | What | Role |
|---|---|---|
| REPLACE-BG | 226 adults, type 1, Dexcom G4, 26 weeks, 14.8M CGM rows, 475,502 meter pairs | Primary |
| Shanghai T1DM/T2DM | 112 patients, Abbott flash CGM, about 2 weeks each, 4,012 pairs | Comparator only (too few low readings) |
| FDA MAUDE + recalls | 3.4 million CGM problem reports, 32 recall events | Phase 1 |

- Raw CGM data lives in `Uncommitted Data/Raw Data Dump/`. Not in git. Each teammate needs their own copy.
- Raw MAUDE downloads (`fda-maude/raw/`, `fda-maude/clean/`) are not in git either. The robot script can re-create them.

## Status

| Item | State |
|---|---|
| Phase 1: FDA/MAUDE mining | Done. Full pull, report and country analysis finished 2026-10-22. |
| Phase 1: LLM sorting of report texts | Planned |
| Phase 2: accuracy by glucose range | First results done. See `analysis/RESULTS.md`. |
| Phase 2: fault simulation | Version 1 done (constant low bias 10/20/30 %). See `analysis/SIMULATION_RESULTS.md`. |
| Midterm research plan | Submitted. File: `docs/plans/2026-10-23_midterm-research-plan.pdf` |
| Final project | Due Dec 4 2026, 11:59 PM. One PDF + GitHub link. |

### Phase 1 key numbers

| What | Value |
|---|---|
| All CGM reports in MAUDE (1992-03 to 2026-09) | 3,382,071 |
| Death + injury reports | 123,607 |
| of these, deaths | 623 |
| Top problem type in death + injury reports | Wrong readings (33.1 %) |
| Recall events | 32 |
| of these, Class I (most serious) | 7 |
| Share of all reports from the US | 63.8 % |

- Report counts are NOT failure rates. Brands differ in how they file reports.

### Phase 2 key numbers

| What | REPLACE-BG (Dexcom G4) | Shanghai (Abbott) |
|---|---|---|
| MARD, meter pairs (average percent error) | 10.4 % | 13.9 % |
| Meter pairs below 70 mg/dL | 20,110 | 37 |

- Pitfall: in the low range, the error direction flips depending on how the pairs are grouped. We group by the average of CGM and reference.
- Pitfall: 7 % of REPLACE-BG CGM rows are from before the study started. They are filtered out.
- Both cohorts are narrow: adults only. REPLACE-BG is 94 % White. Shanghai is all Chinese adults recruited through two hospitals.

## Next steps (to Dec 4 2026)

- Pick the fault types to simulate, from the Phase 1 results.
- Simulation version 2: more fault types and more realistic treatment rules.
- Rerun both analysis scripts on the machine with the data (see `analysis/REPRODUCIBILITY.md`).
- Write the final project paper.

## Open questions

- Which treatment rules to simulate: fixed thresholds (e.g. treat low if CGM < 70, correction dose if CGM > 180), real pump dose-calculator events, or both?
- Which sensor fault types to simulate? Decided by Phase 1 results.

## Decided

- 2026-10-14: meter pairs are the headline accuracy set. Calibration pairs are reported alongside.
- 2026-10-19: openFDA API for MAUDE, no web scraping. See `docs/plans/2026-10-19_maude-robot-plan.md`.
