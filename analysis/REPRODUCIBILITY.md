# Reproducibility check: analysis/explore_raw_data.py

Terms: CGM = continuous glucose monitor (a skin sensor). Fingerstick = blood drop tested on a meter, used as the "true" value. MARD = the sensor's average percent error. Bias = average of (CGM minus fingerstick).

## How to run

1. Install Python 3.11 (any normal install; the Windows Store build works).
2. Install the packages. From the repo root:
   `python -m pip install -r analysis/requirements.txt`
3. Put the raw data in `Uncommitted Data/Raw Data Dump/`. It must contain two sub-folders:
   - `Replace-BG Dataset/Data Tables/` (30 pipe-delimited `.txt` files, 837 MB)
   - `Shanghai/` (125 Excel files plus 2 summary workbooks)
   This folder is 919 MB and is NOT in git. Ask the team for a copy.
4. Run, from the repo root:
   - PowerShell: `$env:PYTHONUTF8 = "1"; python analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis`
   - Git Bash / Linux / Mac: `PYTHONUTF8=1 (no longer needed: the final print line was removed on 2026-10-07) python analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis`
   - On Windows do NOT use `python -I`. It breaks the pandas import on the Store build.

| Item | Value |
|---|---|
| Runtime | 32 seconds (SSD laptop). 18 s of that is loading the 837 MB CGM table. |
| Memory | Needs several GB of free RAM. The whole CGM table (14.9 million rows) is held in memory. |
| Packages | pandas, numpy, matplotlib, openpyxl (for .xlsx), xlrd (for .xls). Listed in `analysis/requirements.txt`. |
| Outputs | `analysis/figures/01..11_*.png` (11 files) and `analysis/summary_stats.json`. Existing files are overwritten. Figure 12 is made by a different script (`bias_simulation.py`), not this one. |
| Also prints | A log to the screen, then the full JSON (about 1,100 lines). |

## Last verified run

| Item | Value |
|---|---|
| Date | 2026-10-09, 3 runs (13:35, 13:38 and 13:39 local time) |
| Machine | Windows 11, Python 3.11 (Store build), same packages as the 2026-10-07 run |
| Result | All 3 runs clean. Exit code 0. 31-32 s each. No warnings. Plain `python`, output sent to a log file. No `PYTHONUTF8` needed. |
| Outputs | 11 figures (01 to 11) and `summary_stats.json` written. |
| Script changed? | Yes, on 2026-10-09. (1) Figure 09 rebuilt: bias is now grouped by the average of CGM and reference; value labels on bars; bars with fewer than 50 pairs are hatched; units on every axis. (2) New figure 11: Parkes error grid. (3) `summary_stats.json` gains `parkes_pct` and `overall.by_avg_range` for each of the 3 pairings. Pairing code and all other figures unchanged. |
| Numbers match RESULTS.md? | Yes for the spot checks: 120,202 calibration pairs (MARD 14.1 %), 475,502 meter pairs (MARD 10.4 %), 4,012 Shanghai pairs (MARD 13.9 %). Parkes zones for meter pairs: A 88.1 %, B 10.9 %, C 0.8 %, D 0.1 %, E 0.01 %. |

Earlier run, 2026-10-07: 2 runs, same outputs byte-for-byte (md5). Run 1 crashed on the final print line (fixed the same day). Run 2 clean, 31 s.

## Figure recommendation for the report

Research question: how accurate is the CGM vs fingerstick by glucose range, and how big an error changes treatment.

| Rank | Figure | Why |
|---|---|---|
| 1 | `figures/09_accuracy_by_range.png` | Answers the first half of the question: pair count, bias and MARD in 5 glucose ranges, for both datasets. Error roughly doubles below 70 mg/dL. Bias is grouped by the average of CGM and reference, so it is not distorted by the binning method. |
| 2 | `figures/11_parkes_error_grid.png` | Answers the second half: how big an error changes treatment. Each pair sits in a zone. A and B = no change to treatment. C, D, E = could cause a wrong treatment. Zone percentages are printed on the figure. |
| 3 | `figures/08_cgm_vs_reference_scatter.png` | Raw CGM-vs-fingerstick agreement. Now mostly covered by figure 11, which adds the zones. |

Not recommended for this section: figures 01-07 describe who is in the data, not accuracy. Figure 10 (per-person MARD) is good but secondary.

## Fixes needed

Script:
- The last line of the script prints the full JSON to the screen. It contains Chinese column names. On Windows, when output goes to a file, Python uses an old text encoding and crashes (`UnicodeEncodeError`). All outputs are already saved by then, so nothing is lost, but the exit code is 1. Workaround: set `PYTHONUTF8=1 (no longer needed: the final print line was removed on 2026-10-07)` (see "How to run"). Proper fix (not done, outside my brief): delete line 668 (`print(json.dumps(...))`) or add `ensure_ascii=True`.
- No change was made to the script in this check.

Figure 09: all 3 points below were fixed on 2026-10-09.
- (Fixed) The title said the CGM "reads high" below 54 mg/dL. That was a maths effect of grouping by reference value. Bias is now grouped by the average of the two readings. The low bins now show the sensor reading low. A note on the figure explains the grouping.
- (Fixed) Value labels added to the bias and MARD bars.
- (Fixed) Bars with fewer than 50 pairs are hatched and labelled "n=".
- Still to check: the 3 panels are wide (12.5 in). At 6 in report width the value labels will be small. Keep the full-width figure if the report allows it.

Figure 08 before it goes in the report:
- Three panels side by side will be very small on a one-page report. guess: keep only the first panel (REPLACE-BG calibrations) or the first and third.
- The "dotted: +/-20 %" note is only in the right panel. Move it to the caption.
- The flat rows of dots at 39 and 401 mg/dL are the sensor's display limits (it cannot show values outside 39-401). Say so in the caption.
- The 70 and 180 mg/dL lines have no labels. Label them "hypo threshold" and "high threshold".

Missing figure: fixed on 2026-10-09.
- Figure 11 is a Parkes (consensus) error grid, type 1 diabetes version. Left panel: REPLACE-BG meter pairs. Right panel: Shanghai. Zone percentages are computed on all pairs and printed on each panel. Dots are a random 40,000-pair sample per panel.
- The zone borders are typed in from Pfutzner et al. 2013 (J Diabetes Sci Technol 7:1275). They were checked by hand at 24 test points. Worth a second check against the paper before the report.
