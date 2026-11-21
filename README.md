# BMEN 600 Group 24: How accurate are glucose sensors, and what goes wrong?

We measure how far continuous glucose monitor (CGM) readings sit from fingerstick readings in each glucose range, using public data, and we mine FDA reports of CGM failures to see which faults happen in real life.

| Item | Value |
|---|---|
| Team | Myleni Zatorre de Oliveira, Mahlaqa Mubasher, Laaraib Anwar, Mirha Kanwal, Artemy Gavrilov (BMEN 600, Group 24) |
| Midterm research plan (submitted) | [`docs/plans/2026-10-23_midterm-research-plan.pdf`](docs/plans/2026-10-23_midterm-research-plan.pdf) |
| Presentation | November 30, 2026 |
| Final project | due Friday, December 4, 2026, 11:59 PM |

**Start here:** the [midterm plan PDF](docs/plans/2026-10-23_midterm-research-plan.pdf) → [Key results](#key-results-so-far) → [How to reproduce](#how-to-reproduce) → [Which file makes what](#which-file-makes-what).

## Research question

> From the submitted plan (Section I): "This study investigates how the magnitude and direction of CGM measurement errors vary across glycemic ranges and how frequently these errors result in glucose misclassification at the 70 and 180 mg/dL thresholds."

Magnitude and direction mean how big the error is and whether the sensor reads too high or too low. Misclassification means the sensor puts a reading on the wrong side of 70 or 180 mg/dL, so a low, in-range or high value lands in the wrong group.

## Background

A CGM is a small sensor worn on the skin that reads glucose every few minutes, and people with diabetes use it to decide when to eat sugar or take insulin. In November 2025 Abbott recalled about 3 million FreeStyle Libre 3 / 3 Plus sensors because they read too low; by January 2026 the FDA listed 860 serious injuries and 7 deaths. We cannot test the recalled sensors ourselves, so we use public datasets in which other CGMs were worn together with fingerstick tests, and a fingerstick (a blood drop on a meter) is our reference, or "true", value. We also count FDA problem reports and recalls for all CGMs, which shows which faults happen in real life and which ones are worth simulating.

## Status (2026-10-30)

Phase 1, the structured mining of FDA reports and recalls, was finished on 2026-10-22. Its second step, finished on 2026-10-30, read 124,599 report texts with a pattern layer and a local open-source language model, checked against a reference set of 287 reports labelled by one AI reviewer (a teammate checked 100 of them); the results are in [`fda-maude/results/text/TEXT_RESULTS.md`](fda-maude/results/text/TEXT_RESULTS.md). A manufacturer comparison and a pattern-only pass over all 3.38 million reports followed on 2026-11-06. Phase 2 is done: accuracy by glucose range, error drivers (lag, wear day, rate of change, time of day), subgroups and fault simulation version 2, all with confidence intervals, are written up in [`analysis/FINDINGS.md`](analysis/FINDINGS.md). A simulation of the three fault types found in the reports was added on 2026-11-20 ([`analysis/SIMULATION_THREE_FAULTS.md`](analysis/SIMULATION_THREE_FAULTS.md)). What remains is the paper itself (presentation Nov 30, final due Dec 4).

## Key results so far

Terms: MAUDE = FDA database of medical device problem reports. Pair = one CGM reading matched to one fingerstick taken at about the same time; a verified pair is one where the fingerstick came from the meter's own log and was not used to calibrate the sensor. Bias = average of (CGM minus fingerstick) as a percent, where minus means the sensor reads too low. MARD = mean absolute relative difference, the sensor's average percent error (lower is better). CI = 95 % confidence interval, the range the true value most likely sits in.

### Phase 1: FDA reports and recalls

Snapshot: FDA data last updated 2026-10-07, pulled 2026-10-19. The structured analysis (counts by problem type, maker, year and country) is done; the full write-up is [`fda-maude/results/report/report_results.md`](fda-maude/results/report/report_results.md). The report texts themselves were then read with a pattern layer and a local open-source language model, which pull out the error size, wear day and fault type each report states. Their output was checked against a reference set of 287 reports labelled by one AI reviewer; the results are in [`fda-maude/results/text/TEXT_RESULTS.md`](fda-maude/results/text/TEXT_RESULTS.md). Report counts are safety signals, not failure rates, because reporting is voluntary and brands file reports differently.

| What | Value |
|---|---|
| All CGM reports in MAUDE (13 product codes, 1992-03 to 2026-09) | 3,382,071 |
| Death + injury reports | 123,607 (623 deaths, 122,984 injuries) |
| Top problem family in death + injury reports | Wrong readings: 33.1 % |
| Death + injury reports listing hypoglycemia (low sugar) as a patient problem | 40.8 % |
| Libre 3 / 3 Plus death + injury reports, all time | 18,292 |
| ... received on or after the recall start (Nov 24, 2025) | 6,785 (71 deaths, 6,714 injuries) |
| ... of these, with the FDA problem term "Low Readings" | 2,638 |

### Phase 2: accuracy on verified fingerstick pairs

The headline set is 168,990 verified pairs from all 226 REPLACE-BG adults (Dexcom G4). The plan's promised sample, the CGM+BGM arm (77 people, 33,467 pairs), gives the same picture within 1 point; the range, missed-low, unconfirmed-low and wrong-side rows below come from that arm, and the missed-low rate is 31 % on all 226 people. Full memo with every source file: [`analysis/FINDINGS.md`](analysis/FINDINGS.md).

| What | Value (95 % CI) |
|---|---|
| Overall MARD | 13.3 % (12.7 to 13.9) |
| MARD below 54 mg/dL vs above 250 mg/dL | 19.1 % (18.0 to 20.4) vs 10.2 % (9.5 to 11.4) |
| Meter-confirmed lows (below 70 mg/dL) that the sensor did not show as low | 28 % (24 to 33) |
| Sensor-shown lows not confirmed by the meter | 38 % |
| Pairs on the wrong side of the 70 or 180 mg/dL line | 15.0 % (13.6 to 16.6) |
| Bias below 54 mg/dL after correcting for sensor lag | reads 6.5 % low (5.1 to 7.9) |
| Sensor lag (how far the sensor trails blood glucose) | 5 to 7 minutes |
| MARD on wear day 1 vs day 7 | 15.2 % (14.6 to 15.9) vs 11.8 % (11.2 to 12.5); 86 % of people worse on day 1 |
| Shanghai comparator (FreeStyle Libre H, 4,012 pairs, 98 patients) | MARD 13.9 % (12.2 to 16.1); reads 7.4 % low |

The sensor is least reliable exactly where a reading changes what the patient does, in the low range. The low-range bias survives lag correction, and an exploratory split puts most of it on wear day 1. Age, sex, BMI, HbA1c, diabetes duration and study arm do not predict a person's error; the person's glucose pattern does (glucose swings and time below 70 mg/dL each correlate with MARD at 0.33). The midterm plan reported MARD 10.4 %; after it we found that about a third of the reference fingersticks had been used to calibrate the sensor and that many "fingerstick" rows were sensor values typed into insulin pumps, and removing both leaves the 168,990 verified pairs, raises MARD to 13.3 %, and leaves the direction of every finding unchanged.

Fault simulation, version 2: we replayed 159,878 real insulin-dose decisions from 203 people with a constant bias added to the sensor reading. A sensor that reads 20 % low skips 7.2 % of correction doses (CI 6.6 to 8.2), changes 16.7 % of doses by more than one unit, hides 51 % of high episodes above 180 mg/dL and adds 0.86 false low alerts per person per day. A 10 % low reading changes almost no dose; doses start to change near 12 % low bias. Across six fault types, a constant low bias hurts dose decisions most, and noise is the only fault that hides low episodes. The midterm's version 1 counted readings instead of decisions and is kept as history in [`analysis/SIMULATION_RESULTS.md`](analysis/SIMULATION_RESULTS.md).

Figures chosen for the paper, all in `analysis/figures/`: `15_misclassification_70_180.png` (main finding), `13_accuracy_by_range_setA.png`, `18_low_range_bias_lag_corrected.png`, `20_wear_day_and_time_of_day.png`, `25_decision_impact_vs_bias.png` and `26_fault_families.png`.

## Which file makes what

The midterm plan PDF uses these labels. Table I (data sources and sizes) comes from `analysis/summary_stats.json` and `fda-maude/results/report/report_results.md`. Fig. 1 (pairs, bias and MARD by glucose range, on the midterm pair set) is `analysis/figures/09_accuracy_by_range.png`, and Table B1 (pair counts, bias, MARD, Parkes zones) is in `analysis/summary_stats.json`; both come from `explore_raw_data.py`, and the paper uses figure 13 instead. Fig. B1 (simulated low bias, version 1) is `analysis/figures/12_decision_flips.png` from `bias_simulation.py`. Fig. B2 (monthly death + injury reports with "Low Readings", by maker) is `fda-maude/results/report/figures/fig4_low_readings_monthly.png` from `report_results.py`. The Gantt chart in Section VI was made from the team's Excel timeline and is not in the repo. Names that differ between the plan PDF and the repo: `maude_pull.py` is `fda-maude/scripts/maude_robot.py`, `analysis/requirements.txt` is `requirements.txt` at the repo root, and the plan's "Table 2 and Figures 1-3" are Table B1, Fig. 1, Fig. B1 and Fig. B2 (labels from an earlier draft).

## Datasets

| Dataset | Source | Who and size | Terms | Accessed | Put it in |
|---|---|---|---|---|---|
| REPLACE-BG | Jaeb Center for Health Research, [public dataset 546](https://public.jaeb.org/dataset/546). Paper: Aleppo et al. 2017, [doi:10.2337/dc16-2482](https://doi.org/10.2337/dc16-2482) | 226 US adults with type 1 diabetes, 14 sites, 2015-16. Dexcom G4, 26 weeks. 13.7 M CGM readings in the study window, 580,577 meter readings. 837 MB. | Jaeb terms of use. No redistribution. | Oct 7, 2026 | `Uncommitted Data/Raw Data Dump/Replace-BG Dataset/Data Tables/` |
| ShanghaiT1DM / T2DM | Figshare, Zhao et al., [doi:10.6084/m9.figshare.c.6310860](https://doi.org/10.6084/m9.figshare.c.6310860). Paper: [doi:10.1038/s41597-023-01940-7](https://doi.org/10.1038/s41597-023-01940-7) | 112 adults (12 type 1, 100 type 2) from two Shanghai hospitals. FreeStyle Libre H, about 2 weeks. 127,982 CGM readings. | CC BY 4.0 (reuse allowed with credit) | Oct 7, 2026 | `Uncommitted Data/Raw Data Dump/Shanghai/<one sub-folder>/` |
| FDA MAUDE + recalls | [openFDA API](https://open.fda.gov/apis/device/event/) (device event, recall and enforcement endpoints) | All reports for 13 CGM product codes. 3,382,071 reports, 95 recall records. | Public US government data | Pulled Oct 19, 2026 (FDA data to Oct 7, 2026) | made by `maude_robot.py` in `fda-maude/raw/` and `fda-maude/clean/` |

Raw data is not in this repo, because of its size (about 919 MB for the CGM data, about 590 MB for MAUDE downloads) and Jaeb's no-redistribution terms. The Shanghai files need one extra folder level, as unzipped from Figshare; the full layout is in [`analysis/REPRODUCIBILITY.md`](analysis/REPRODUCIBILITY.md).

## How to reproduce

### 1. Set up

Install Python 3.11, then from the repo root run `py -3.11 -m pip install -r requirements.txt` (Mac / Linux: `python3 -m pip install -r requirements.txt`). The pinned packages are pandas, numpy, matplotlib, pyarrow, openpyxl, xlrd, scipy, statsmodels, requests, scikit-learn and ollama, at the versions that made the committed outputs. On Windows, plain `python` may be an older Python, so use `py -3.11` unless `python --version` says 3.11.

Git does not give you the data. Every Phase 2 script needs `Uncommitted Data/Raw Data Dump/` (REPLACE-BG + Shanghai, 919 MB; download it from the Datasets table or ask the team) and `analysis/cache/` (407 MB of cleaned tables in parquet, a fast binary format, which `preprocess.py` builds from the raw data in about 47 s). `report_results.py` needs `fda-maude/clean/serious.csv.gz` (31.7 MB; ask the team or re-pull as below). `fda-maude/raw/` (367 MB) and the rest of `fda-maude/clean/` (194 MB) are only needed to resume or extend the robot, and an `OPENFDA_API_KEY` environment variable (a free key from openFDA) only for new big pulls, because it raises the daily call limit.

### 2. Run (from the repo root; Mac / Linux: `python3` in place of `py -3.11`)

Phase 2 scripts take the data folder and the output folder as arguments and write to `analysis/` and `analysis/figures/`. Times are with the cache ready; the first run of any script builds the cache tables it needs (about 50 s more, once).

| Phase | Command | Time | Writes |
|---|---|---|---|
| 2 | `py -3.11 analysis/preprocess.py "Uncommitted Data/Raw Data Dump" analysis/cache --rebuild` | 47 s | the cache: 14 parquet tables and `manifest.json` |
| 2 | `py -3.11 analysis/accuracy_v2.py "Uncommitted Data/Raw Data Dump" analysis` | 5 s | figures 13-16, `accuracy_v2_stats.json` |
| 2 | `py -3.11 analysis/error_drivers.py "Uncommitted Data/Raw Data Dump" analysis` | 26 s | figures 17-20, `error_drivers_stats.json` |
| 2 | `py -3.11 analysis/subgroups.py "Uncommitted Data/Raw Data Dump" analysis` | 8 s | figures 21-24, `subgroups_stats.json`, `participant_metrics.csv` |
| 2 | `py -3.11 analysis/simulation_v2.py "Uncommitted Data/Raw Data Dump" analysis` | 102 s | figures 25-28, `simulation_v2_stats.json`, `simulation_v2_lookup.csv`, `simulation_v2_participants.csv` |
| 2, October first pass | `py -3.11 analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis` | 5 s | figures 01-11, `summary_stats.json` (midterm numbers, kept as history) |
| 2, October first pass | `py -3.11 analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis` | 4 s | figure 12, `simulation_stats.json` (midterm numbers, kept as history) |
| 1 | `py -3.11 fda-maude/scripts/report_results.py` | about 35 s, no internet | `fda-maude/results/report/report_results.md`, `figures/fig1-fig6`, `tables/a_*` to `i_*` |
| 1 | `py -3.11 fda-maude/scripts/country_spread.py report` | about 4 s, no internet | `tables/k_country_*.csv`, `figures/fig7_foreign_countries.png` |
| 1, new pull | `py -3.11 fda-maude/scripts/maude_robot.py counts`, then `serious`, then `clean --tiers serious` | about 360 API calls, no key needed; guess: 30 min | `fda-maude/raw/`, `fda-maude/clean/serious.csv.gz`, `fda-maude/results/counts/` |

Existing outputs are overwritten, and `--help` on any script prints its usage. A new MAUDE pull will not give our exact numbers, because the FDA adds reports every week; our snapshot is FDA data of 2026-10-07, pulled 2026-10-19. The full robot guide is [`fda-maude/README.md`](fda-maude/README.md), and the Phase 2 details (data layout, last verified run) are in [`analysis/REPRODUCIBILITY.md`](analysis/REPRODUCIBILITY.md).

Checks done: on 2026-10-30 the cache was rebuilt and all six Phase 2 scripts were run in sequence (151 s in total); every stats file matched the previous run value by value, apart from runtime fields, and all 28 figures were byte-identical. Later that day the titles of figures 13, 17 and 20 were edited and the two scripts rerun, with every stats value unchanged. On 2026-10-23 the Phase 1 report was rerun in a fresh copy of the repo with a new Python install, and all 7 figures and all tables came out byte-identical.

## File map

Local only = gitignored, not on GitHub.

```
README.md                    this file
requirements.txt             pinned Python packages for all scripts
CLAUDE.md                    instructions for the AI assistant used to manage the repo
docs/
  PROJECT_OVERVIEW.md, WRITING_RULES.md   status, key numbers and open questions; plain-language rules for all project writing
  plans/, rubrics/           dated plans (index: plans/README.md; 2026-10-23_midterm-research-plan.pdf is the submitted plan); course rubrics (local only)
analysis/                    Phase 2: accuracy, error drivers, subgroups, fault simulation
  preprocess.py              shared loader: cleans both datasets, builds the pairs and the parquet cache (cache/, local only)
  accuracy_v2.py             accuracy by range, iCGM table, misclassification, Bland-Altman; figures 13-16
  error_drivers.py           lag, low-range bias after lag correction, rate of change, wear day, night; figures 17-20
  subgroups.py               who gets worse accuracy; figures 21-24
  simulation_v2.py           fault simulation v2 on real dose decisions; figures 25-28
  explore_raw_data.py, bias_simulation.py   October first pass: pairs and accuracy (figures 01-11), fault simulation v1 (figure 12)
  *_stats.json               every number each script prints (one file per script)
  participant_metrics.csv    one row per REPLACE-BG participant: accuracy, glucose pattern, demographics
  simulation_v2_lookup.csv   decision impact for each bias from -40 to +40 %, for joining to Phase 1 error sizes
  FINDINGS.md                findings memo for the paper: main finding, ranked supporting findings, checklists, figure list
  METHODOLOGY.md             dated log of Phase 2 method decisions and why
  METHODS_REVIEW.md          each method against the current research standard: keep, add, change or skip
  PREPROCESSING.md           cleaning rules, pair rules, cache contents, checks
  ACCURACY_V2.md, ERROR_DRIVERS.md, SUBGROUPS.md, SIMULATION_V2.md   results of the four v2 scripts, plain language
  RESULTS.md, SIMULATION_RESULTS.md   October first-pass results (history)
  REPRODUCIBILITY.md         run steps, data layout, last verified run
  figures/                   01-28 PNG figures
fda-maude/                   Phase 1: FDA MAUDE + recall mining
  README.md                  how the robot works, how to run, cleaning rules, the text step
  METHODOLOGY.md             dated log of Phase 1 method decisions for the text step
  OPTIONS.md                 options weighed for reading the report texts (research note)
  DATA_NOTES.md              what is in the MAUDE pull: fields, texts, quirks
  access-check/              4 tests of FDA data access, done before building the robot
  scripts/
    maude_robot.py           downloads from openFDA and cleans (the plan calls it maude_pull.py); settings in config.json
    report_results.py, country_spread.py   report tables and figures fig1-fig6, report_results.md; country tables and fig7
    extract_regex.py         pattern layer: fixed text patterns read the maker templates in each report
    llm_extract.py           model layer: a local open-source language model fills a fixed form per report
  prompts/                   the form and instructions given to the model, one frozen set per version
  gold/                      287 reports labelled by one AI reviewer, and the labelling rules; the yardstick for the text step
  results/
    PULL_SUMMARY.md, counts/, recalls_cgm.csv, recall_harm_manual.csv   pull summary and checks; 11 count tables; 95 recall records (32 events); recall harm typed in from FDA pages
    report/                  main Phase 1 results: report_results.md, country_spread.md, figures fig1-fig7, 42 tables
    text/                    text-step outputs: pilot notes, gold-set runs, run set
  raw/, clean/               robot downloads (367 MB) and one row per report (225 MB). Local only
logs/                        work log, one dated file per session
Uncommitted Data/            raw CGM datasets. Local only
```

## Responsible use

All data is public and de-identified, and we never try to re-identify anyone. We follow each source's terms: REPLACE-BG (Jaeb) may not be redistributed, so only code and summary numbers are in this repo, and Shanghai is credited under CC BY 4.0. We do not quote personal details from MAUDE report texts. MAUDE counts are safety signals, not failure rates, because reports can be missing, late or duplicated. Both cohorts are narrow (all adults; REPLACE-BG is 94 % White, US and well controlled; Shanghai is Chinese hospital patients), so the results may not apply to children or other groups. Neither dataset uses the recalled Libre 3 sensor, so we cannot measure its accuracy directly.

## AI-assisted work

Tool: Claude (Anthropic), used through Claude Code. It was used for literature search and summaries (every reference checked against the original paper, unsupported ones removed), for writing and debugging the analysis scripts (run on the real data; record counts, value ranges and matched pairs checked independently; Parkes zone borders checked at 24 test points; every rerun compared value by value with the previous outputs), for organising the repo and drafting plain-language docs (every number traced to a script output, the `*_stats.json` files and `fda-maude/results/report/tables/`; Phase 1 outputs regenerated in a clean copy, byte-identical), and for editing report writing for clarity and drawing the Gantt chart from the team's Excel timeline (reviewed by the team).

No AI model touches the Phase 2 data inside our scripts. In Phase 1 the structured results group the 391 FDA problem terms into 8 families with a fixed, readable table (`fda-maude/results/report/tables/d_problem_family_mapping.csv`). The text step uses a local open-source language model, run on our own computer, to fill a fixed form from each report; its model, prompt and scores against the 287-report gold set will be described when the results are in. Research questions, methods and interpretation are the team's decisions.
