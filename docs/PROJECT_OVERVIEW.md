# Project overview

Last updated: 2026-11-21

## The problem (why we care)

- CGMs (continuous glucose monitors) read blood sugar every 5 minutes. People with diabetes dose insulin from them.
- In 2025 the FDA recalled about 3 million Abbott FreeStyle Libre 3 sensors. They read too LOW.
- Abbott reported 860 serious injuries and 7 deaths to the FDA. People ate sugar they did not need, or skipped insulin.
- Our question: how wrong does a glucose sensor have to be before a treatment decision goes wrong, and how wrong do sensors actually get, both when they fail and when they work?

## Two phases

### Phase 1. FDA report mining (done; guides Phase 2)
- Pulled FDA recall records and MAUDE problem reports for CGM sensors. MAUDE = the FDA database of medical device problem reports.
- Used the openFDA API (the FDA's public data service). No web scraping.
- Counted reports by problem type, brand, year and country.
- Done 2026-10-30: sorted report texts by what went wrong, using text patterns and a local LLM (large language model, an AI text tool). Done 2026-11-06: compared brands, and ran the patterns alone over all 3.38 million reports.
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
| Phase 1: reading the report texts | Done 2026-10-30. Patterns + local open model (prompt v3, kappa 0.77 / 0.75 on a 287-report gold set) read all 124,599 report texts in 9.6 h. Results: `fda-maude/results/text/TEXT_RESULTS.md`. Teammate check of 100 gold reports done 2026-11-08, no issues. |
| Phase 1: brand comparison (Abbott vs Dexcom complaint texts, age, sex) | Done 2026-11-06. See `fda-maude/results/text/BRAND_COMPARISON.md`. |
| Phase 1: patterns alone over all 3.38 million reports (regex v2) | Done 2026-11-06. See `fda-maude/results/text/REGEX_V2_FULL_CORPUS.md`. |
| Phase 1: field inventory (which MAUDE fields are filled; what the texts say beyond the form) | Done 2026-11-08. See `fda-maude/results/FIELD_INVENTORY.md`. Verdict: do not run the model on the malfunction reports. |
| Phase 2: accuracy by glucose range | Done to standard (CIs, iCGM table, misclassification, Bland-Altman). See `analysis/ACCURACY_V2.md`. |
| Phase 2: error drivers (lag, wear day, rate of change, night) | Done. Primary uncertainty answered. See `analysis/ERROR_DRIVERS.md`. |
| Phase 2: wear day 1 (settling in vs bad sensors pulled early) | Done 2026-11-06. See `analysis/WEAR_DAY.md`. |
| Phase 2: subgroups and demographics | Done. See `analysis/SUBGROUPS.md`. |
| Phase 2: deep demographics check + sex follow-up | Done 2026-11-06. See `analysis/DEMOGRAPHICS_DEEP.md` and `analysis/DEMOGRAPHICS_FOLLOWUP.md`. |
| Phase 2: fault simulation | Version 2 done (decisions, six fault families, lookup table). See `analysis/SIMULATION_V2.md`. |
| Phase 2: three-fault simulation (the faults the FDA reports describe, in episodes) | Done 2026-11-20. See `analysis/SIMULATION_THREE_FAULTS.md`. |
| Checks for the paper: trial errors against reported errors; low detection with a 15-minute window; precision of the text patterns; recall count and date | Done 2026-11-21. See `analysis/TAIL_COMPARISON.md`, `analysis/LOW_DETECTION_WINDOW.md`, `fda-maude/results/text/PATTERN_PRECISION.md`, `fda-maude/results/RECALL_COUNT_CHECK.md`, `fda-maude/results/RECALL_DATE_CHECK.md`. |
| Final paper | Outline, five figures and three tables built 2026-11-21 (`docs/paper/`). Full draft written 2026-11-21 (`docs/paper/PAPER.md`, PDF: `docs/paper/PAPER.pdf`, 10 pages). All sections have text except AI-Assisted Work and Author Contributions, which the team writes. Open: rubric check, two references to confirm, citations to confirm. |
| Findings memo and paper checklist | Done 2026-10-30; updated 2026-11-08 with the 2026-11-06 memos. See `analysis/FINDINGS.md`. |
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

### Phase 1 text-step key numbers (what the report texts say)

| What | Value |
|---|---|
| Report texts read | 124,599 (118,462 death or injury + 6,137 sampled malfunctions) |
| Reports stating both the sensor and the meter value | 18,445 |
| Typical reads-low error in complaints (median) | Abbott -77 %, Dexcom -68 % |
| Direction of Dexcom complaints | 55 % read high; most of those hid a true low under 70 |
| Reported reads-low errors beyond the 20 % tipping point | 97 to 98 % |
| Abbott complaints naming wear day 1 | 13 % (flat expectation 7 %) |
| Maker-stated Parkes zone vs the zone we computed | agree 87 %, within one zone 97 % |
| What the reported Abbott errors do in the simulation (median person) | 49 % of corrections skipped, 96 % of highs hidden, "below 70" shown 80 % of the day |
| Sensor-meter pairs found by patterns alone in malfunction-only reports (no death or injury code; never read by the model) | 191,112 |
| Typical error in those malfunction-only pairs | median -66 %; 75 % read low; true glucose under 70 in only 5 % |
| Brand failure modes in serious wrong-reading pairs: hidden low (true glucose under 70) | Dexcom 46 % vs Abbott 28 % |
| Brand failure modes: false low (sensor under 70, meter not) | Abbott 36 % vs Dexcom 17 % |

- Reported errors are the harmful tail, not typical sensors. Medtronic text results carry a caution label.
- The brands' errors are equally large (median 86 vs 87 %). Gaps in FDA outcome codes, fingerstick mentions and filled age are reporting style, not harm.

### Phase 2 key numbers (verified fingerstick pairs: meter log, not calibration, in study window)

| What | Value |
|---|---|
| Verified pairs, REPLACE-BG | 168,990 pairs, 226 people |
| MARD (average percent error), REPLACE-BG | 13.3 % (95 % CI 12.7 to 13.9) |
| True lows (below 70) the sensor did not show as low | 28 % (CI 24 to 33) in the CGM+BGM arm (77 people); 31 % for all 226 |
| Sensor lows not confirmed by the meter | 38 % in the CGM+BGM arm; 41 % for all 226 |
| Low-range bias after lag correction, below 54 | reads 6.5 % low (CI 5.1 to 7.9) |
| Sensor lag | 5 to 7 minutes |
| MARD wear day 1 vs day 7 (day 1 = the sensor settling in) | 15.2 % vs 11.8 % |
| Share of the day-1 excess that is settling, not bad sensors pulled early | 92 % (CI 85 to 100); the extra error halves every 24 h; flat from day 5 |
| Sex gap in the low range (modest; absent in one study arm) | sensor reads about 2.5 mg/dL lower in women than in men; changes no insulin dose, moves only the 70 alert line |
| Low bias that skips 7 % of insulin corrections and hides half of highs | 20 % |
| Shanghai MARD | 13.9 %, reads about 7 % low |

- Why the MARD changed from the midterm's 10.4 %: a third of the old pairs were calibration fingersticks, and many "meter" rows were CGM values typed into the pump. Both made the sensor look better than it is. Details: `analysis/PREPROCESSING.md`.
- Demographics (age, sex, BMI, HbA1c, duration, arm, and 60 more traits; 680 pre-planned tests) do not predict sensor error. Glucose pattern does, weakly. One modest exception: the low-range sex gap above.
- Both cohorts are narrow: adults only. REPLACE-BG is 94 % White. Shanghai is all Chinese adults recruited through two hospitals.

## Next steps (to Dec 4 2026)

- Pushed 2026-11-20 (commit `0baa650`). The three-fault simulation files were made after that push and are not pushed yet.
- Second pass for more findings in the trial data (asked for 2026-10-30): deep demographics, sex follow-up and wear-day memos done 2026-11-06 and folded into `analysis/FINDINGS.md`.
- Decide on the inventory memo's ranked suggestions (`fda-maude/results/FIELD_INVENTORY.md`): use the unused maker-evaluation and device-returned fields; add two dropped raw fields (10-minute clean re-run); two 100-report human reads instead of a bigger model run.
- Open housekeeping: optional -12 % marker on figure 25; delete or keep the 19 GB `fda-maude/raw/bulk_zips/`.
- Teammate check of 100 gold-set reports: done 2026-11-08, no issues (`fda-maude/gold/GOLD_SET.md`).
- Draft report sections Nov 6-13 from `analysis/FINDINGS.md`. Final repo Nov 15. Presentation Nov 30. Due Dec 4.
- Team update for the group, built 2026-11-09 (Word + PDF, 3 pages + 3 figure pages, every number checked against its source): `docs/team-docs/2026-11-09_team-update-and-paper-plan.docx`. Local only.

## Open questions

- Answered 2026-11-06: which real-world error sizes to highlight from the report texts? Two failure modes, not one size. The 3.3 million malfunction-only reports are one fault: a false low of 60 to 80 % at normal or high true glucose. Serious reports are the other two: hidden lows, and sensors pinned at their floor at very high true glucose. `fda-maude/results/text/REGEX_V2_FULL_CORPUS.md`.
- Answered 2026-11-06: does the wear-day pattern in Abbott complaints match the day-1 effect in trial data? The trial's day-1 effect is every sensor settling in (92 %), not bad sensors. Day 1 has 1.5 times the large errors and twice the false lows, so a day-1 complaint cluster is expected even without a defect. `analysis/WEAR_DAY.md`.
- Decided 2026-11-09: simulate three faults (false low at true glucose 70 to 250; hidden low under 54; floor-pinned sensor over 250) next to the constant bias. Done 2026-11-20 with episodes of 2, 6 and 12 hours and a rule of 15 g sugar when the sensor shows under 70. Result for one 6-hour episode, median person: a false low gives 20 unneeded sugar treatments (an upper bound; the model does not let sugar change glucose); a hidden low gives 34 minutes truly under 54 with the sensor showing 70 or above, which a constant low bias never produces; a floor-pinned sensor withholds 1.3 units of insulin. `analysis/SIMULATION_THREE_FAULTS.md`.
- Human read of about 100 malfunction-only and 100 injury reports from the two extreme error bands, to settle whether the harm gradient is real or coding style.

## Decided

- 2026-10-14: meter pairs are the headline accuracy set. Calibration pairs are reported alongside.
- 2026-10-19: openFDA API for MAUDE, no web scraping. See `docs/plans/2026-10-19_maude-robot-plan.md`.
- 2026-10-27: one shared preprocessing module and cache for every analysis script.
- 2026-10-30: headline pair set = verified fingersticks, all participants; CGM+BGM arm as the plan-promised check. Headline high threshold 180, with 200 as a check. Simulation counts decisions, not readings; version 1 kept as illustration only. Text step: codes, then patterns, then a local open model with a fixed form, validated on a gold set.
