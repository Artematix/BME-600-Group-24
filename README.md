# BMEN 600 Project: Failing Glucose Sensors and Treatment Decisions

Team name: Group 24

Members: Myleni Zatorre de Oliveira, Mahlaqa Mubasher, Laaraib Anwar, Mirha Kanwal, Artemy Gavrilov

## Research question

How much error in a continuous glucose monitor reading is needed before it changes a patient's treatment decision, and how often do real sensors reach that level of error across the low, normal, and high glucose ranges?

## The problem, and what we do

- A continuous glucose monitor (CGM) is a small sensor worn under the skin that reads blood sugar every few minutes. People with diabetes decide when to take insulin or eat sugar based on these readings.
- In late 2025 the FDA recalled about 3 million Abbott FreeStyle Libre 3 sensors because they reported glucose values lower than the true level. By January 2026 the FDA had linked the defect to 860 serious injuries and 7 deaths.
- We use public datasets from other CGM sensors that come paired with fingerstick blood tests. A fingerstick is a blood drop on a test strip, and we treat it as the true value.
- First, we measure how far each sensor's readings were from the truth across the low, normal, and high glucose ranges. Then we add simulated faults to the real sensor traces and count how many treatment decisions change.

## Two phases

### Phase 1: FDA report mining (small, done first)

- MAUDE is the FDA's public database of medical device problem reports.
- We pull CGM sensor reports. We sort them by fault type, brand and month.
- Output: a table of real fault types. It tells Phase 2 which faults to simulate.

### Phase 2: accuracy by range, then fault simulation (main)

- Part A: match each CGM reading to a fingerstick. Measure error in the low, normal and high ranges.
- Part B: add faults to the real traces. First fault: every reading 10, 20 or 30 percent too low.
- Count "decision flips": the faulty trace says eat sugar (below 70 mg/dL) or take insulin (above 200) when the clean trace does not.

## Datasets

| Dataset | Source | Who and how big | How to get it |
|---|---|---|---|
| REPLACE-BG (US, 2015-16) | Jaeb Center for Health Research, public datasets page | 226 adults with type 1 diabetes. Dexcom G4. 26 weeks each. 14.8 million CGM readings. About 600,000 pairs. | Free. Registration may be needed. |
| Shanghai T1DM / T2DM (China, 2019-21) | Figshare, Zhao et al. 2023 | 112 hospital patients (12 type 1, 100 type 2). Abbott-type flash sensor. About 2 weeks each. 128,000 readings. 4,012 pairs. | Free. |
| OhioT1DM (US) | Ohio University (Marling and Bunescu) | 12 adults with type 1 diabetes. 8 weeks each. | Optional. Needs a signed data use agreement. Not used yet. |

- The data is NOT in this repo. It is about 919 MB, and each dataset has its own use terms.
- After download, put the files here. This folder is gitignored.
  - `Uncommitted Data/Raw Data Dump/Replace-BG Dataset/` (contains `Data Tables/` with 30 pipe-delimited `.txt` files)
  - `Uncommitted Data/Raw Data Dump/Shanghai/` (the Excel files)

## How to run

| Item | Value |
|---|---|
| Python | 3.11 |
| Install | `python -m pip install -r analysis/requirements.txt` (pandas, numpy, matplotlib, openpyxl, xlrd) |
| Run, from the repo root | `python analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis` |
| Runtime | About 31 seconds on an SSD laptop. Needs several GB of free RAM. |
| Outputs | `analysis/figures/01..11_*.png` (11 figures) and `analysis/summary_stats.json`. Existing files are overwritten. |
| Bias simulation (25 s) | `python analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis` |

- On Windows, do not use `python -I`. It breaks the pandas import on the Microsoft Store build.

## File map

```
README.md                  This file.
CLAUDE.md                  Notes for the AI assistant we use for project management.
docs/
  PROJECT_OVERVIEW.md      Repo map, status, open questions.
  WRITING_RULES.md         Plain-language rules for all project writing.
  plans/                   Team brief and research plan drafts.
analysis/                  Phase 2 code and outputs.
  explore_raw_data.py      Loads both datasets, measures accuracy, makes the figures.
  bias_simulation.py       Adds faults to real traces, counts decision flips.
  requirements.txt         Python packages.
  RESULTS.md               Findings from the first exploration.
  SIMULATION_RESULTS.md    Findings from the first fault simulation.
  REPRODUCIBILITY.md       Verified run notes.
  summary_stats.json       All computed numbers (exploration).
  simulation_stats.json    All computed numbers (simulation).
  figures/                 Output figures (PNG).
fda-maude/                 Phase 1: FDA report mining. Not started.
logs/                      Work log, one file per session.
Uncommitted Data/          Raw data. Local only, gitignored.
```

## Results so far

MARD = the sensor's average percent error. Lower is better. Bias = average of (sensor minus fingerstick).

- REPLACE-BG has enough low-sugar pairs: 6,600 to 20,000 below 70 mg/dL. Shanghai has 37.
- Both sensors read a bit too low above 70 mg/dL. Same direction as the recall fault.

| Sensor | Reads too low by |
|---|---|
| Dexcom G4 (REPLACE-BG) | 3 to 5 percent |
| Abbott-type flash (Shanghai) | 6 to 13 percent |

- MARD roughly doubles when sugar is low.

| Range | MARD |
|---|---|
| All readings | 10 to 14 percent |
| Below 70 mg/dL | 19 to 42 percent |

- People differ a lot. Per-person MARD in REPLACE-BG: 9 to 23 percent. Median 13.9 percent.
- Below 70 mg/dL the Dexcom G4 reads 5 to 11 percent too low, when pairs are grouped fairly (by the average of both readings).
- First simulation: a sensor reading 10 percent too low hides about a third of "above 200" readings, so a correction dose would be skipped.

Figures to look at:
- `analysis/figures/09_accuracy_by_range.png`: pair count, bias and MARD by glucose range, both datasets.
- `analysis/figures/11_parkes_error_grid.png`: error grid zones A to E. Zone A is safe. C, D and E can change treatment. 99.1 % of REPLACE-BG pairs sit in A or B.
- `analysis/figures/12_decision_flips.png`: decision flips per person per day when the sensor reads 10, 20, 30 % too low. Details in `analysis/SIMULATION_RESULTS.md`.

## Responsible use

- All data is public and de-identified.
- We follow each dataset's terms of use. We do not redistribute the raw data.
- Cohorts are narrow: adults only. REPLACE-BG is 94 percent White, US. Shanghai is Chinese hospital in-patients.
- So results may not apply to children, other ethnic groups, or other care settings.

## AI-assisted work

- We use Claude (an AI assistant) to help organise the repo, write analysis code, and draft summaries.
- All code is run and checked by the team.
- Results and their interpretation are the team's responsibility.

## Deadline

Midterm Research Plan due Friday, October 16, 2026, 11:59 PM.
