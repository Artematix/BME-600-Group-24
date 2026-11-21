# Reproducibility: the Phase 2 analysis scripts (last verified 2026-10-30)

Terms: CGM = continuous glucose monitor (a skin sensor). Fingerstick = a blood drop tested on a meter, used as the "true" value. Verified fingerstick = a fingerstick from the meter's own log that was not used to calibrate the sensor (rule: `PREPROCESSING.md` section 3b). MARD = the sensor's average percent error. Cache = cleaned tables saved as parquet files (a fast binary table format) in `analysis/cache/`, not in git.

## 1. The scripts

Seven scripts, all in `analysis/`. Run them from the repo root with plain `python` (Python 3.11; on the Windows Store build do not use `python -I`). Argument 1 = data folder, argument 2 = output folder; the values shown are also the defaults. Optional argument 3 = cache folder (default `analysis/cache`). `-h` prints the usage text. Existing outputs are overwritten.

| Script | Command | Runtime | Reads | Writes |
|---|---|---|---|---|
| `preprocess.py` | `python analysis/preprocess.py "Uncommitted Data/Raw Data Dump" analysis/cache --rebuild` | 47 s (29 s is the 837 MB CGM file) | 15 REPLACE-BG tables (list in section 2) and the Shanghai workbooks | 14 parquet tables (407 MB) and `manifest.json` (version stamp, row counts) in `analysis/cache/` |
| `explore_raw_data.py` | `python analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis` | 5 s | cache: cgm, calibrations, bgm, pairs, participants, shanghai; 4 raw tables | figures 01-11, `summary_stats.json` |
| `bias_simulation.py` | `python analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis` | 4 s | cache: cgm, bgm, manifest | figure 12, `simulation_stats.json` |
| `accuracy_v2.py` | `python analysis/accuracy_v2.py "Uncommitted Data/Raw Data Dump" analysis` (optional argument 3: path of a markdown tables file) | 5 s | cache: pairs, participants | figures 13-16, `accuracy_v2_stats.json` |
| `error_drivers.py` | `python analysis/error_drivers.py "Uncommitted Data/Raw Data Dump" analysis` | 26 s | cache: pairs, participants, cgm, calibrations, bgm, shanghai | figures 17-20, `error_drivers_stats.json` |
| `subgroups.py` | `python analysis/subgroups.py "Uncommitted Data/Raw Data Dump" analysis` | 8 s | cache: pairs, participants, cgm, shanghai | figures 21-24, `subgroups_stats.json`, `participant_metrics.csv`, `cache/participant_metrics.parquet` |
| `simulation_v2.py` | `python analysis/simulation_v2.py "Uncommitted Data/Raw Data Dump" analysis` (`SIM_V2_QUICK=1` in the environment gives a 20-person test run) | 102 s | cache: cgm, pump wizard, bgm, participants | figures 25-28, `simulation_v2_stats.json`, `simulation_v2_lookup.csv`, `simulation_v2_participants.csv` |
| `simulation_v2.py`, extended lookup (added 2026-10-30) | `python analysis/simulation_v2.py "Uncommitted Data/Raw Data Dump" analysis --lookup-min -90 --lookup-max 90 --lookup-step 2 --lookup-only --lookup-out analysis/simulation_v2_lookup_extended.csv` | 53 s | cache: cgm, pump wizard, bgm, participants | `simulation_v2_lookup_extended.csv` only (91 bias rows, -90 to +90 %; the -40 to +40 rows are identical to the base file; `SIMULATION_V2.md` s13) |
| `demographics_deep.py` (added 2026-11-06) | `python analysis/demographics_deep.py "Uncommitted Data/Raw Data Dump" analysis` | 150 s | cache: pairs, participants, shanghai, `participant_metrics.parquet` (run `subgroups.py` first); 7 raw tables (HQuestHypoUnaware, HQuestHypoFear, HQuestDiabTech, HMedication, HMedicalCondition, HInsulin, HScreening via the cache) | figures 29-32, `demographics_deep_stats.json` (seed 600; 680 pre-registered tests, one BH family; `DEMOGRAPHICS_DEEP.md`) |
| `simulation_three_faults.py` (added 2026-11-20) | `python analysis/simulation_three_faults.py "Uncommitted Data/Raw Data Dump" analysis` (`SIM_3F_QUICK=1` gives a 20-person test run) | 23 s | cache: same tables as `simulation_v2.py`; FDA tables `fda-maude/results/text/tables/h_*.csv`, `g_brand_error_sizes.csv` | figures 36-37, `simulation_three_faults_stats.json`, `simulation_three_faults_lookup.csv` |
| `demographics_followup.py` (added 2026-11-06) | `python analysis/demographics_followup.py "Uncommitted Data/Raw Data Dump" analysis` (`--no-maude` skips the MAUDE block) | 24 s | cache: pairs, participants, cgm, pump (basal, bolus), shanghai, `participant_metrics.parquet` (run `subgroups.py` first); the 6 raw questionnaire / medication / condition / insulin tables via `demographics_deep.extra_predictors`, `Sample.txt`; `simulation_v2_lookup.csv`; MAUDE: `fda-maude/clean/text_extract_v3.jsonl`, `run_set.csv.gz`, `serious.csv.gz`, `sample_local.parquet` and `fda-maude/results/report/tables/d_problem_family_mapping.csv` (loaded through `fda-maude/scripts/text_results.py` and `brand_comparison.py`) | figure 35, `demographics_followup_stats.json` (seed 600; 66 + 3 + 5 pre-registered tests in three BH families, list written before the tests run; `DEMOGRAPHICS_FOLLOWUP.md`) |
| `wear_day.py` (added 2026-11-06) | `python analysis/wear_day.py "Uncommitted Data/Raw Data Dump" analysis` | 4 s | cache: pairs (verified set), cgm, calibrations, pairs_calibration; needs `scipy` | figures 33-34, `wear_day_stats.json` (seed 20261106; one shared participant bootstrap; glued sensor sessions, see `WEAR_DAY.md` s2) |

Runtimes are with the cache ready (SSD laptop, 2026-10-30). The first run of any script builds the cache tables it needs on its own (about 50 s more, once). Results are deterministic: fixed seeds (accuracy_v2 and subgroups 600; error_drivers and simulation_v2 20261027) and 1,000 to 2,000 bootstrap resamples.

Which pair set each script uses:

| Script | Pair set | Why |
|---|---|---|
| explore_raw_data, bias_simulation | all meter pairs: pump BG entries and calibration fingersticks included (475,502 pairs, MARD 10.4 %) | the midterm numbers (RESULTS.md, SIMULATION_RESULTS.md); kept as history, do not change |
| accuracy_v2, error_drivers, subgroups | verified fingerstick pairs in the study window, flag `is_verified_fingerstick` from `preprocess.py` (168,990 pairs, 226 people, MARD 13.3 %) | the headline set for the paper |
| simulation_v2 | the CGM trace and the pump's bolus-calculator records; its meter-as-truth check uses meter-log rows (`from_meter_log`) and drops calibration rows itself | decisions, not pairs |

## 2. Set-up

1. Install Python 3.11.
2. From the repo root: `python -m pip install -r requirements.txt` (pandas, numpy, matplotlib, pyarrow, openpyxl, xlrd). `error_drivers.py` and `subgroups.py` also need `statsmodels` and `scipy`, which `requirements.txt` does not list yet (installed here: statsmodels 0.14.6, scipy 1.16.3): `python -m pip install statsmodels scipy`.
3. Put the raw data in `Uncommitted Data/Raw Data Dump/` (919 MB, NOT in git; ask the team for a copy, or download REPLACE-BG from Jaeb and Shanghai from Figshare). Layout:

```
Uncommitted Data/Raw Data Dump/
  Replace-BG Dataset/
    Data Tables/                  30 pipe-delimited .txt files (837 MB). The scripts read 15:
      HDeviceCGM.txt              CGM readings and calibrations (the big one)
      HDeviceBGM.txt HDeviceUploads.txt HDeviceBolus.txt HDeviceBasal.txt HDeviceWizard.txt
      HPtRoster.txt HScreening.txt HPostRandPtFinalStatus.txt HInitialStudyCGM.txt HInsulin.txt
      HFollowUp.txt HLocalHbA1c.txt Sample.txt HMedicalCondition.txt
  Shanghai/
    <one sub-folder, any name>/   extra level, as unzipped from Figshare (required; the name does not matter)
      Shanghai_T1DM_Summary.xlsx
      Shanghai_T2DM_Summary.xlsx
      Shanghai_T1DM/              one Excel file per patient visit
      Shanghai_T2DM/
```

4. Build the cache (section 3), then run any script. If a data file is missing, the script prints the path it expected and stops.
5. Memory: the CGM table (14.8 million rows) is held in RAM, about 1 GB; have several GB free.

## 3. Cache rebuild

| Item | Value |
|---|---|
| Command | `python analysis/preprocess.py "Uncommitted Data/Raw Data Dump" analysis/cache --rebuild` |
| When | On a new machine, and after any rule change in `preprocess.py`. Every rule change must bump `CACHE_VERSION` there; the scripts then rebuild an old cache on their own, `--rebuild` only does it right away. |
| Runtime, size | 47 s; 407 MB in `analysis/cache/` (gitignored). The CGM table then loads in about 1 s. |
| Check | The last log line says `all tables ready`. The pairs line must read `verified fingerstick pairs in window: 168990 from 226 people`. All counts: `analysis/cache/manifest.json` or `pp.read_manifest()`. |
| Current version | `2026-10-30.1` (verified-fingerstick rule). Previous: `2026-10-27.1` (cache introduced). |

## 4. Last verified run: 2026-10-30

Machine: Windows 11, Python 3.11.9, pandas 2.3.3 (`requirements.txt` pins newer versions; every output was made with 2.3.3).
What changed that day: `preprocess.py` got the `from_meter_log` and `is_verified_fingerstick` flags and the `verified_pairs()` view (cache version 2026-10-30.1); `accuracy_v2.py`, `error_drivers.py`, `subgroups.py` and `simulation_v2.py` now use those flags instead of their own `source == "meter"` filter. Test: the cache was rebuilt, all six scripts were run in sequence (151 s in total), and every output file was compared value by value with the files written before the change.

| Script | Exit code | Runtime | Compared | Result |
|---|---|---|---|---|
| `preprocess.py --rebuild` | 0 | 47 s | manifest counts | 475,502 meter pairs; 319,866 independent; 285,166 in window from the meter log; 168,990 verified in window (226 people, MARD 13.25 %) |
| `explore_raw_data.py` | 0 | 5 s | `summary_stats.json` (946 values), figures 01-11 | all identical |
| `bias_simulation.py` | 0 | 4 s | `simulation_stats.json` (165 values), figure 12 | identical except `runtime_s` |
| `accuracy_v2.py` | 0 | 5 s | `accuracy_v2_stats.json` (5,157 values), figures 13-16 | identical except `runtime_s`, `generated`, `cache_version` |
| `error_drivers.py` | 0 | 26 s | `error_drivers_stats.json` (3,271 values), figures 17-20 | identical except `runtime_s`, `fit_seconds` |
| `subgroups.py` | 0 | 8 s | `subgroups_stats.json` (5,207 values), `participant_metrics.csv`, figures 21-24 | identical except `runtime_s`, `cache_version`; CSV byte-identical |
| `simulation_v2.py` | 0 | 102 s | `simulation_v2_stats.json` (14,838 values), 2 CSV files, figures 25-28 | identical except `runtime_s`; CSV files byte-identical |

All 28 figures are byte-identical to the previous run. No warnings in any log. To redo this check: copy `analysis/*.json`, `analysis/*.csv` and `analysis/figures/` aside, run the scripts, then compare value by value (timestamps, runtimes and the cache-version string are allowed to differ).

Earlier verified runs: 2026-10-27 (cache introduced: 14 values in `summary_stats.json` and 31 in `simulation_stats.json` moved in the last printed digit because of a deterministic duplicate-timestamp rule; see `PREPROCESSING.md` section 6), 2026-10-09 and 2026-10-07 (first-pass scripts, byte-identical repeats).

## 5. Figure index

| Figures | Script | Topic | Document |
|---|---|---|---|
| 01-07 | explore_raw_data | who is in the data (first pass) | RESULTS.md (history) |
| 08-11 | explore_raw_data | CGM vs fingerstick scatter, accuracy by range, per-person MARD, Parkes error grid; all pairs | RESULTS.md (history) |
| 12 | bias_simulation | decision flips under a fixed low bias (version 1) | SIMULATION_RESULTS.md (history) |
| 13-16 | accuracy_v2 | accuracy by range (set A), iCGM agreement, misclassification at 70 / 180, Bland-Altman | ACCURACY_V2.md |
| 17-20 | error_drivers | lag scan, low-range bias after lag correction, error by rate of change, wear day and time of day | ERROR_DRIVERS.md |
| 21-24 | subgroups | per-person MARD distribution, pre-specified forest plot, strongest association, exploratory forest plot | SUBGROUPS.md |
| 25-28 | simulation_v2 | decision impact vs bias, fault families, dose-change distribution, risk indices vs bias | SIMULATION_V2.md |
| 29-32 | demographics_deep | cohort demographics (both cohorts), 2x2 interaction tables, site effects and ICC, demographics vs glucose pattern and model comparison | DEMOGRAPHICS_DEEP.md |
| 35 | demographics_followup | sex gap in low-range bias: every split, pooled bias by glucose bin for women and men, matching and adjustment | DEMOGRAPHICS_FOLLOWUP.md |
| 36-37 | simulation_three_faults | the three FDA-based faults against a constant bias for one 6-hour episode; the same outcomes by episode length | SIMULATION_THREE_FAULTS.md |
| 33-34 | wear_day | day-1 error: discarded sensors vs settling (day-1 MARD by session length; error by hours since start), calibration timing | WEAR_DAY.md |

Figure caveats carried over from the first pass: the flat rows of dots at 39 and 401 mg/dL in figure 08 are the sensor's display limits, not data; bias in figures 09 and 13 is grouped by the average of CGM and reference, because grouping by the reference alone makes the sensor look as if it reads high below 54 mg/dL.
