# Reproducibility: the Phase 2 analysis scripts

Terms: CGM = continuous glucose monitor (a skin sensor). Fingerstick = blood drop tested on a meter, used as the "true" value. MARD = the sensor's average percent error. Bias = average of (CGM minus fingerstick).

Two scripts, both in `analysis/`:

| Script | Makes |
|---|---|
| `explore_raw_data.py` | `analysis/figures/01..11_*.png` (11 figures) and `analysis/summary_stats.json` |
| `bias_simulation.py` | `analysis/figures/12_decision_flips.png` and `analysis/simulation_stats.json` |

## How to run

1. Install Python 3.11.
2. Install the packages. From the repo root:
   - Windows: `py -3.11 -m pip install -r requirements.txt`
   - Mac / Linux: `python3 -m pip install -r requirements.txt`
3. Put the raw data in `Uncommitted Data/Raw Data Dump/`. It is 919 MB and NOT in git. Ask the team for a copy, or download it (REPLACE-BG from Jaeb, Shanghai from Figshare). The layout must be:

```
Uncommitted Data/Raw Data Dump/
  Replace-BG Dataset/
    Data Tables/                      30 pipe-delimited .txt files (837 MB)
      HPtRoster.txt                   the scripts read these 7
      HScreening.txt
      HLocalHbA1c.txt
      HDeviceUploads.txt
      HMedicalCondition.txt
      HDeviceCGM.txt
      HDeviceBGM.txt
  Shanghai/
    <one sub-folder, any name>/       extra level, as unzipped from Figshare
      Shanghai_T1DM_Summary.xlsx
      Shanghai_T2DM_Summary.xlsx
      Shanghai_T1DM/                  one Excel file per patient visit
      Shanghai_T2DM/                  one Excel file per patient visit
```

   - The extra sub-folder inside `Shanghai/` is required. Do not unzip the files flat into `Shanghai/`.
   - The sub-folder name does not matter. The script finds it with a wildcard.

4. Run, from the repo root:

| System | Command |
|---|---|
| Windows | `py -3.11 analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis` |
| Windows | `py -3.11 analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis` |
| Mac / Linux | `python3 analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis` |
| Mac / Linux | `python3 analysis/bias_simulation.py "Uncommitted Data/Raw Data Dump" analysis` |

- Argument 1 = data folder. Argument 2 = output folder. The values above are also the defaults.
- `-h` or `--help` prints the usage text.
- If a data file is missing, the script prints one line with the path it expected, then stops.
- Existing output files are overwritten.

| Item | Value |
|---|---|
| Runtime, explore_raw_data.py | about 30-35 seconds (SSD laptop). About 18 s of that is loading the 837 MB CGM table. |
| Runtime, bias_simulation.py | about 25 seconds |
| Memory | Several GB of free RAM. The whole CGM table (14.9 million rows) is held in memory. |
| Packages | pandas, numpy, matplotlib, openpyxl (reads .xlsx), xlrd (reads old .xls). Pinned in the root `requirements.txt`. |
| Screen output | A progress log with timings. |

## Last verified run

| Item | Value |
|---|---|
| Date | 2026-10-09, 3 runs of explore_raw_data.py (13:35, 13:38, 13:39 local time). bias_simulation.py first run the same day. |
| Machine | Windows 11, Python 3.11 |
| Result | All runs clean. Exit code 0. 31-32 s each. No warnings. |
| Outputs | 11 figures (01 to 11) and `summary_stats.json`. |
| Changes verified by that run | (1) Figure 09 rebuilt: bias grouped by the average of CGM and reference; value labels on bars; bars with fewer than 50 pairs hatched; units on every axis. (2) New figure 11: Parkes error grid. (3) `summary_stats.json` gains `parkes_pct` and `overall.by_avg_range` for each of the 3 pairings. |
| Numbers match RESULTS.md? | Yes for the spot checks: 120,202 calibration pairs (MARD 14.1 %), 475,502 meter pairs (MARD 10.4 %), 4,012 Shanghai pairs (MARD 13.9 %). Parkes zones for meter pairs: A 88.1 %, B 10.9 %, C 0.8 %, D 0.1 %, E 0.01 %. |

Earlier run, 2026-10-07: 2 runs, same outputs byte-for-byte (md5 checksum).

## Edited after the last verified run (rerun pending)

Both scripts were edited after 2026-10-09. The edits change how figures look, not any number.

| Script | Edit |
|---|---|
| explore_raw_data.py | Figure 09: grey note text under the title removed. Panel titles now "A. ...", "B. ...", "C. ...". |
| bias_simulation.py | Figure 12: legend now in a white box. Footnote split into two short lines. |
| both | Clear "data not found" message and `--help`. Default data folder is now `Uncommitted Data/Raw Data Dump` in both. |

- The committed figures 09 and 12 were updated by hand-editing / redraw from the saved stats files. They were not made by a full run of the edited scripts.
- A full rerun on the machine that holds the raw data is still pending. After it, update the table above.
- guess: the rerun will give the same numbers, because no analysis code changed.

## Figure recommendation for the report

Research question: how accurate is the CGM vs fingerstick by glucose range, and how big an error changes treatment.

| Rank | Figure | Why |
|---|---|---|
| 1 | `figures/09_accuracy_by_range.png` | Answers the first half of the question: pair count, bias and MARD in 5 glucose ranges, for both datasets. Error roughly doubles below 70 mg/dL. Bias is grouped by the average of CGM and reference, so it is not distorted by the grouping method. Say this in the caption. |
| 2 | `figures/11_parkes_error_grid.png` | Answers the second half: how big an error changes treatment. Each pair sits in a zone. A and B = no change to treatment. C, D, E = could cause a wrong treatment. Zone percentages are printed on the figure. |
| 3 | `figures/08_cgm_vs_reference_scatter.png` | Raw CGM-vs-fingerstick agreement. Mostly covered by figure 11, which adds the zones. |

Not recommended for this section: figures 01-07 describe who is in the data, not accuracy. Figure 10 (per-person MARD) is good but secondary.

## Figure notes

Figure 09 (fixed on 2026-10-09):
- Bias is grouped by the average of the two readings. Grouping by reference value made the sensor look like it "reads high" below 54 mg/dL. That was a maths effect, not a sensor fact.
- Value labels on the bias and MARD bars.
- Bars with fewer than 50 pairs are hatched and labelled "n=".
- Still to check: the 3 panels are wide (12.5 in). At 6 in report width the labels will be small.

Figure 08, before it goes in a report:
- Three panels side by side will be small. guess: keep only the first panel (REPLACE-BG calibrations) or the first and third.
- The "dotted: +/-20 %" note is only in the right panel. Move it to the caption.
- The flat rows of dots at 39 and 401 mg/dL are the sensor's display limits (it cannot show values outside 39-401). Say so in the caption.
- The 70 and 180 mg/dL lines have no labels. Label them "hypo threshold" and "high threshold".

Figure 11 (added 2026-10-09):
- Parkes (consensus) error grid, type 1 diabetes version. Left panel: REPLACE-BG meter pairs. Right panel: Shanghai.
- Zone percentages are computed on all pairs. Dots are a random 40,000-pair sample per panel.
- Zone borders are from Pfutzner et al. 2013 (J Diabetes Sci Technol 7:1275). Checked by hand at 24 test points.
