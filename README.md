# BMEN 600 Group 24: How accurate are glucose sensors, and what goes wrong?

We measure how far continuous glucose monitor (CGM) readings are from fingerstick readings in each glucose range, using public data, and we mine FDA reports of CGM failures.

| Item | Value |
|---|---|
| Team | Myleni Zatorre de Oliveira, Mahlaqa Mubasher, Laaraib Anwar, Mirha Kanwal, Artemy Gavrilov |
| Course | BMEN 600, Group 24 |
| Midterm research plan (submitted) | [`docs/plans/2026-10-23_midterm-research-plan.pdf`](docs/plans/2026-10-23_midterm-research-plan.pdf) |
| Final project | due Friday, December 4, 2026, 11:59 PM |

**Start here:** the [midterm plan PDF](docs/plans/2026-10-23_midterm-research-plan.pdf) → [Key results](#key-results-so-far) → [How to reproduce](#how-to-reproduce) → [Which file makes what](#which-file-makes-what).

## Research question

From the submitted plan (Section I):

> "This study investigates how the magnitude and direction of CGM measurement errors vary across glycemic ranges and how frequently these errors result in glucose misclassification at the 70 and 180 mg/dL thresholds."

- Magnitude and direction = how big the error is, and whether the sensor reads too high or too low.
- Misclassification = the sensor puts a reading on the wrong side of 70 or 180 mg/dL (low / in range / high).

## Background

- A CGM is a small sensor worn on the skin. It reads glucose every few minutes. People with diabetes use it to decide when to eat sugar or take insulin.
- In November 2025 Abbott recalled about 3 million FreeStyle Libre 3 / 3 Plus sensors. They read too LOW. By January 2026 the FDA listed 860 serious injuries and 7 deaths.
- We cannot test the recalled sensors. So we use public datasets where other CGMs were worn together with fingerstick tests. A fingerstick (blood drop on a meter) is our reference ("true") value.
- We also count FDA problem reports and recalls for all CGMs. This shows which faults happen in real life, and tells us which faults to simulate.

## Status (2026-10-23)

| Part | What | State |
|---|---|---|
| Phase 1 | FDA MAUDE reports + recalls: pull, clean, count, report | Done (2026-10-22) |
| Phase 1 | AI (LLM) sorting of report free text | Planned |
| Phase 2, part A | CGM accuracy vs fingerstick, by glucose range | First results done. Not lag-corrected. |
| Phase 2, part B | Fault simulation, version 1 (constant low bias 10 / 20 / 30 %) | Done |
| Next (to Dec 4) | Per-person confidence intervals (bootstrapping), mixed-effects models, more fault types (picked from Phase 1), final paper | To do |

## Key results so far

Terms:
- MAUDE = FDA database of medical device problem reports.
- Pair = one CGM reading matched to one fingerstick taken at about the same time.
- Bias = average of (CGM minus fingerstick), as a percent. Minus = the sensor reads too low.
- MARD = mean absolute relative difference: the sensor's average percent error. Lower is better.

### Phase 1: FDA reports and recalls

Snapshot: FDA data last updated 2026-10-07, pulled 2026-10-19.

| What | Value |
|---|---|
| All CGM reports in MAUDE (13 product codes, 1992-03 to 2026-09) | 3,382,071 |
| Death + injury reports | 123,607 (623 deaths, 122,984 injuries) |
| Top problem family in death + injury reports | Wrong readings: 33.1 % |
| Death + injury reports listing hypoglycemia (low sugar) as a patient problem | 40.8 % |
| CGM recall events since 2008 | 32 from 6 firms (7 Class I = most serious) |
| Libre 3 / 3 Plus death + injury reports, all time | 18,292 |
| ... received on or after the recall start (Nov 24, 2025) | 6,785 (71 deaths, 6,714 injuries) |
| ... of these, with the FDA problem term "Low Readings" | 2,638 |
| Share of all reports from the US | 63.8 % |

- Report counts are NOT failure rates. Reporting is voluntary, and brands file reports differently.
- Full write-up: [`fda-maude/results/report/report_results.md`](fda-maude/results/report/report_results.md) and [`country_spread.md`](fda-maude/results/report/country_spread.md).

### Phase 2: accuracy (from `analysis/summary_stats.json`)

| | REPLACE-BG meter pairs | REPLACE-BG calibration pairs | Shanghai |
|---|---|---|---|
| Sensor | Dexcom G4 | Dexcom G4 | FreeStyle Libre H |
| People | 226 | 226 | 112 |
| Pairs | 475,502 | 120,202 | 4,012 |
| Pairs below 70 mg/dL | 20,110 (4.2 %) | 6,589 (5.5 %) | 37 (0.9 %) |
| Overall bias | -1.3 % | -2.8 % | -7.4 % |
| Overall MARD | 10.4 % | 14.1 % | 13.9 % |
| MARD, 54-69 mg/dL / below 54 mg/dL | 18.7 % / 41.8 % | 19.8 % / 30.6 % | too few pairs |
| Parkes error grid zones A / B / C+D+E | 88.1 / 10.9 / 0.9 % | 79.9 / 19.4 / 0.7 % | 74.7 / 25.1 / 0.3 % |

- Meter pairs are the main (headline) set. Only REPLACE-BG has enough low-sugar pairs, so it is our main dataset.
- Parkes error grid = a chart with zones. A and B = the error would not change treatment. C, D, E = it could.

Bias above 70 mg/dL, by how pairs are put into glucose ranges ("grouping"):

| Grouping | Dexcom G4, meter pairs | Dexcom G4, calibration pairs | Libre H (Shanghai) |
|---|---|---|---|
| By reference (fingerstick) value | 0.9 to 4.0 % low | 3.1 to 4.5 % low | 5.7 to 13.0 % low |
| By average of CGM and reference (used for bias in Fig. 1) | 0.4 to 1.3 % low | 3.5 % low to 1.8 % high | 6.9 to 8.3 % low |

- Below 70 mg/dL, grouping by reference value alone makes sensors look like they read high. This is a statistics effect (regression to the mean), so we group bias by the average instead. Then the Dexcom G4 reads 5 to 11 % too low below 70 mg/dL.
- The plan PDF's "1-4 %" (Dexcom) is the reference grouping. Its "7-8 %" (Libre H) is the average grouping. Details: [`analysis/RESULTS.md`](analysis/RESULTS.md) section 6.

### Phase 2: fault simulation v1 (from `analysis/simulation_stats.json`)

Every REPLACE-BG CGM reading (13.7 million, 226 people) was lowered by a fixed percent. Simulation rules: low below 70 mg/dL, high above 200 mg/dL. (The research question uses 180; version 2 will use it.)

| Sensor reads low by | "Above 200" readings pushed below 200 | New false "below 70" readings, % of all readings |
|---|---|---|
| 10 % | 31.7 % | 2.6 % |
| 20 % | 60.1 % | 6.9 % |
| 30 % | 80.9 % | 13.4 % |

- These are reading-level changes, not real treatment decisions. Details: [`analysis/SIMULATION_RESULTS.md`](analysis/SIMULATION_RESULTS.md).

## Which file makes what

Figure and table labels are the ones in the plan PDF. Run all commands from the repo root.

| In the plan PDF | What it shows | Repo file | Made by |
|---|---|---|---|
| Table I | Data sources and sizes | numbers from `analysis/summary_stats.json` and `fda-maude/results/report/report_results.md` | `explore_raw_data.py`, `report_results.py` |
| Fig. 1 | Pairs, bias, MARD by glucose range | `analysis/figures/09_accuracy_by_range.png` | `explore_raw_data.py` |
| Table B1 | Pair counts, bias, MARD, Parkes zones | `analysis/summary_stats.json` (`pairs_bgm_vs_cgm`, `pairs_calibration_vs_cgm`, `pairs_cbg_vs_cgm`) | `explore_raw_data.py` |
| Fig. B1 | Simulated low bias: flips per person per day | `analysis/figures/12_decision_flips.png`, `analysis/simulation_stats.json` | `bias_simulation.py` |
| Fig. B2 | Monthly death + injury reports with "Low Readings", by maker | `fda-maude/results/report/figures/fig4_low_readings_monthly.png` (data: `tables/f_low_readings_serious_per_month_by_manufacturer.csv`) | `report_results.py` |
| Gantt chart (Section VI) | Project timeline | not in the repo | made from the team's Excel timeline |

Other figures in the repo:

| Files | What | Made by |
|---|---|---|
| `analysis/figures/01` to `07` | Who is in the data; CGM glucose, time in range, coverage | `explore_raw_data.py` |
| `analysis/figures/08`, `10`, `11` | CGM vs reference scatter, per-person MARD, Parkes error grid | `explore_raw_data.py` |
| `fda-maude/results/report/figures/fig1` to `fig6` + `tables/a_*` to `i_*` | Reports per year, problem families, Libre 3 timeline, recalls, ages | `report_results.py` |
| `fda-maude/results/report/figures/fig7` + `tables/k_country_*` | Reports by country | `country_spread.py report` |

Names in the plan PDF that differ from the repo:

| Plan PDF says | Real file |
|---|---|
| `maude_pull.py` | `fda-maude/scripts/maude_robot.py` |
| `analysis/requirements.txt` | `requirements.txt` (repo root) |
| "Table 2 and Figures 1-3" | Table B1, Fig. 1, Fig. B1, Fig. B2 (labels from an earlier draft) |

## Datasets

| Dataset | Source | Who and size | Terms | Accessed | Put it in |
|---|---|---|---|---|---|
| REPLACE-BG | Jaeb Center for Health Research, [public dataset 546](https://public.jaeb.org/dataset/546). Paper: Aleppo et al. 2017, [doi:10.2337/dc16-2482](https://doi.org/10.2337/dc16-2482) | 226 US adults with type 1 diabetes, 14 sites, 2015-16. Dexcom G4, 26 weeks. 13.7 M CGM readings in the study window, 580,577 meter readings. 837 MB. | Jaeb terms of use. No redistribution. | Oct 7, 2026 | `Uncommitted Data/Raw Data Dump/Replace-BG Dataset/Data Tables/` |
| ShanghaiT1DM / T2DM | Figshare, Zhao et al., [doi:10.6084/m9.figshare.c.6310860](https://doi.org/10.6084/m9.figshare.c.6310860). Paper: [doi:10.1038/s41597-023-01940-7](https://doi.org/10.1038/s41597-023-01940-7) | 112 adults (12 type 1, 100 type 2) from two Shanghai hospitals. FreeStyle Libre H, about 2 weeks. 127,982 CGM readings. | CC BY 4.0 (reuse allowed with credit) | Oct 7, 2026 | `Uncommitted Data/Raw Data Dump/Shanghai/<one sub-folder>/` |
| FDA MAUDE + recalls | [openFDA API](https://open.fda.gov/apis/device/event/) (device event, recall and enforcement endpoints) | All reports for 13 CGM product codes. 3,382,071 reports, 95 recall records. | Public US government data | Pulled Oct 19, 2026 (FDA data to Oct 7, 2026) | made by `maude_robot.py` in `fda-maude/raw/` and `fda-maude/clean/` |

- Raw data is NOT in this repo. Reasons: size (about 919 MB for the CGM data, about 590 MB for MAUDE downloads) and Jaeb's no-redistribution terms.
- The Shanghai files need one extra folder level, as unzipped from Figshare. Full layout: [`analysis/REPRODUCIBILITY.md`](analysis/REPRODUCIBILITY.md).

## How to reproduce

### 1. Set up

| Step | Windows | Mac / Linux |
|---|---|---|
| Python 3.11 | `py -3.11` | `python3` (must be 3.11) |
| Packages (pinned) | `py -3.11 -m pip install -r requirements.txt` | `python3 -m pip install -r requirements.txt` |

- Packages: pandas, numpy, matplotlib, openpyxl, xlrd, requests. Versions are the ones that made the committed outputs.
- On Windows, plain `python` may be an older Python. Use `py -3.11`.

### 2. Files git does not give you

| What | Size | Needed for | How to get it |
|---|---|---|---|
| `Uncommitted Data/Raw Data Dump/` (REPLACE-BG + Shanghai) | 919 MB | both Phase 2 scripts (REQUIRED) | download (Datasets table) or ask the team |
| `fda-maude/clean/serious.csv.gz` | 31.7 MB | `report_results.py` (REQUIRED) | ask the team, or re-pull (below) |
| rest of `fda-maude/clean/` (`full.csv.gz`, `sample.csv.gz`) | 194 MB | later work only | optional |
| `fda-maude/raw/` | 367 MB | only to resume or extend the robot | optional |
| `OPENFDA_API_KEY` environment variable | - | new big pulls (raises the daily call limit) | free key from openFDA |

- Everything else the scripts read is in git (count tables, recall tables, country cache).

### 3. Run (from the repo root; Mac / Linux: `python3` in place of `py -3.11`)

| Phase | Command | Time | Writes |
|---|---|---|---|
| 2 | `py -3.11 analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis` | about 30-35 s, several GB RAM | `analysis/figures/01..11_*.png`, `analysis/summary_stats.json` |
| 2 | `py -3.11 analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis` | about 25 s | `analysis/figures/12_decision_flips.png`, `analysis/simulation_stats.json` |
| 1 | `py -3.11 fda-maude/scripts/report_results.py` | about 35 s, no internet | `fda-maude/results/report/report_results.md`, `figures/fig1-fig6`, `tables/a_*` to `i_*` |
| 1 | `py -3.11 fda-maude/scripts/country_spread.py report` | about 4 s, no internet | `tables/k_country_*.csv`, `figures/fig7_foreign_countries.png` |
| 1 (new pull) | `py -3.11 fda-maude/scripts/maude_robot.py counts`, then `serious`, then `clean --tiers serious` | about 360 API calls, no key needed. guess: 30 min | `fda-maude/raw/`, `fda-maude/clean/serious.csv.gz`, `fda-maude/results/counts/` |

- Existing outputs are overwritten. `--help` on any script prints its usage.
- A new MAUDE pull will NOT give our exact numbers. FDA adds reports every week. Our snapshot: FDA data of 2026-10-07, pulled 2026-10-19.
- Full robot guide (all tiers, API key, resume): [`fda-maude/README.md`](fda-maude/README.md). Phase 2 details: [`analysis/REPRODUCIBILITY.md`](analysis/REPRODUCIBILITY.md).

Checks done:
- 2026-10-23: Phase 1 report rerun in a fresh copy of the repo with a new Python install. All 7 figures and all tables came out byte-identical.
- 2026-10-09: last full run of both Phase 2 scripts, clean, numbers matched. Since then only figure layout and help/error messages changed. Figures 09 and 12 were redrawn from the saved stats files; a full rerun on the data machine is pending.

## File map

Local only = gitignored, not on GitHub.

```
README.md                    this file
requirements.txt             pinned Python packages for all scripts
CLAUDE.md                    instructions for the AI assistant used to manage the repo
docs/
  PROJECT_OVERVIEW.md        status, key numbers, next steps, open questions
  WRITING_RULES.md           plain-language rules for all project writing
  plans/                     dated plans (index: plans/README.md)
    2026-10-23_midterm-research-plan.pdf   submitted midterm research plan
    2026-10-19_maude-robot-plan.md         plan for the Phase 1 download robot
    2026-10-07_*.md                        early plan, team brief, source list
  rubrics/                   course rubrics. Local only
analysis/                    Phase 2: accuracy + fault simulation
  explore_raw_data.py        loads both datasets, makes pairs, accuracy, figures 01-11
  bias_simulation.py         fault simulation v1, figure 12
  summary_stats.json         every number from explore_raw_data.py
  simulation_stats.json      every number from bias_simulation.py
  RESULTS.md                 accuracy results, plain language
  SIMULATION_RESULTS.md      simulation results, plain language
  REPRODUCIBILITY.md         run steps, data layout, last verified run
  figures/                   01-12 PNG figures
fda-maude/                   Phase 1: FDA MAUDE + recall mining
  README.md                  how the robot works, how to run, cleaning rules
  access-check/              4 tests of FDA data access, done before building the robot
  scripts/
    maude_robot.py           downloads from openFDA and cleans (the plan calls it maude_pull.py)
    report_results.py        report tables, figures fig1-fig6, report_results.md
    country_spread.py        country tables and fig7
    config.json              robot settings: product codes, call limits, sample seed
  results/
    PULL_SUMMARY.md          what was pulled, headline numbers, checks
    counts/                  11 count tables from FDA
    recalls_cgm.csv          95 recall records (32 recall events)
    recall_harm_manual.csv   recall injuries/deaths typed in from FDA pages
    report/
      report_results.md      main Phase 1 results
      country_spread.md      country results (written by hand from script output)
      figures/               fig1-fig7
      tables/                42 CSVs (a_* to i_*, k_country_*)
  raw/                       robot downloads, 367 MB. Local only
  clean/                     one row per report, 225 MB. Local only
logs/                        work log, one dated file per session
Uncommitted Data/            raw CGM datasets. Local only
```

## Responsible use

- All data is public and de-identified. We never try to re-identify anyone.
- We follow each source's terms. REPLACE-BG (Jaeb) may not be redistributed, so only code and summary numbers are in this repo. Shanghai is credited under CC BY 4.0.
- We do not quote personal details from MAUDE report texts.
- MAUDE counts are safety signals, not failure rates. Reports can be missing, late or duplicated.
- Cohorts are narrow. All adults. REPLACE-BG is 94 % White, US, well controlled. Shanghai is Chinese hospital patients. Results may not apply to children or other groups.
- Neither dataset uses the recalled Libre 3 sensor. We cannot measure its accuracy directly.

## AI-assisted work

Tool: Claude (Anthropic), used through Claude Code.

| Used for | How we checked it |
|---|---|
| Literature search and summaries | Every reference checked against the original paper. Unsupported ones removed. |
| Writing and debugging the analysis scripts | Scripts run on the real data. Record counts, value ranges and matched pairs checked independently. Parkes zone borders checked at 24 test points. |
| Organising the repo and drafting plain-language docs | Every number in the docs traced to a script output (`summary_stats.json`, `simulation_stats.json`, `fda-maude/results/report/tables/`). Phase 1 outputs regenerated in a clean copy (byte-identical). |
| Editing report writing for clarity; Gantt chart from the team's Excel timeline | Reviewed by the team. |

- So far no AI model reads or labels the data inside our scripts. Phase 1 groups the 391 FDA problem terms into 8 families with a fixed, readable table (`fda-maude/results/report/tables/d_problem_family_mapping.csv`), plus simple keyword counts.
- The planned AI sorting of MAUDE report texts will be described (model, prompt, spot checks) when it is done.
- Research questions, methods and interpretation are the team's decisions.
