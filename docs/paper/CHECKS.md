# Checks of ten outline numbers (2026-11-21)
Every number below was read from the source file named in its block. Sensor = the CGM (continuous glucose monitor). Meter = fingerstick meter. Pair = one sensor value matched to one meter value. Median person = the middle participant. Middle half = first to third quartile across participants. "derived" = worked out from numbers in the file.

## 1. Meter as the true value: what are 1.4 %, 4.2 % and 12.3 % shares of?
| Sensor | What is counted | Share of all calculator decisions (middle half) | Share of needed corrections (middle half) |
|---|---|---|---|
| No added error | correction withheld | 1.4 % (0 to 3.5) | 2.1 % (0 to 7.0) |
| No added error | dose changed by more than 1 U | 4.2 % (1.4 to 10.5) | does not exist |
| Reads 20 % too low | correction withheld | 12.3 % (7.3 to 21.7) | 23.8 % (13.6 to 34.5) |
- Answer: all three are shares of all calculator decisions, not of needed corrections. Each is the median person's share (67 people, 15,034 decisions). "Needed" = the dose with the true glucose is above 0.5 units.
- Pooled counts (derived: mean per person x 67 people): 346 of 15,034 decisions lose their correction with no added error (2.3 %). 1,944 of 15,034 at 20 % too low (12.9 %). The number of needed corrections in this subset: not found.
- Source: `analysis/simulation_v2_stats.json` -> meter_truth_sensitivity -> "0" and "-20" -> mt_skipped_pct, mt_skipped_of_needed_pct, mt_changed_1_pct. Rule: `analysis/simulation_v2.py:410-417`.

## 2. Lookup rows for a sensor that reads 12 % and 20 % too low
| Column | 12 % too low: median (Q1 to Q3) | 20 % too low: median (Q1 to Q3) | Participants |
|---|---|---|---|
| skipped_of_needed_pct | 1.24 (0.31 to 3.48) | 13.47 (7.76 to 21.32) | 202 |
| skipped_pct | 0.69 (0.11 to 2.03) | 7.25 (4.32 to 10.95) | 203 |
| high180_missed_pct | 32.57 (26.90 to 38.75) | 50.78 (43.40 to 58.66) | 226 |
- skipped_of_needed_pct = % of a person's needed corrections that are withheld. skipped_pct = % of a person's calculator decisions. high180_missed_pct = % of a person's high episodes (over 180 mg/dL) not shown as high.
- Bases: 159,878 decisions from 203 people. 120,363 high episodes from 226 people. One of the 203 has no needed correction, so that share rests on 202 (`analysis/simulation_v2.py:414`). Total number of needed corrections: not found (the file holds per-person shares only).
- Source: `analysis/simulation_v2_lookup_extended.csv`, rows bias_pct -12 and -20, columns ending `_median`, `_q1`, `_q3`, `_n`.

## 3. The 20/20 rule
- A pair passes when the meter is under 100 mg/dL and the sensor is within 20 mg/dL of it. Or when the meter is 100 mg/dL or above and the sensor is within 20 % of it. Exactly 20 counts as within. The cut point uses the meter value.
- 83.8 % of the 168,990 pairs (226 people) pass. That is 141,698 pairs (derived). 95 % interval 82.7 to 84.9. It is not the FDA iCGM line "within 20 % at every glucose level": that one is 81.7 % of the same 168,990 pairs.
- Source: `analysis/accuracy_v2.py:124-127`; `analysis/accuracy_v2_stats.json` -> sets.B.overall.within_20_20_pct and bin_rules.within_k_k.

## 4. Reported errors when the sensor read low: which median is which
| Group | All pairs | Median over all pairs | Pairs where the sensor read lower | Median over those pairs only |
|---|---|---|---|---|
| Abbott serious | 7,470 | 47.1 % too low | 4,315 (57.8 % of 7,470) | 76.8 % too low |
| Dexcom serious | 9,189 | 44.1 % too high | 4,029 (43.8 % of 9,189) | 69.2 % too low |
| Malfunction-only | 191,112 | 65.7 % too low | 142,817 (74.7 % of 191,112) | 69.4 % too low |
- So 77, 69 and 69.4 are all medians over reads-low pairs only. 65.7 (the "66") is the median over all malfunction-only pairs, low and high together. Pairs with equal values are in neither group: 29 Abbott, 72 Dexcom, 0 malfunction-only.
- Other pair sets give a slightly different Dexcom value: 68 % (`TEXT_RESULTS.md`, 4,160 pairs) and 67 % (pattern-read pairs). 69 % is the one that belongs to the 9,189 pairs.
- Source: `fda-maude/results/text/tables/g_brand_error_sizes.csv` (tier serious, median_pct); `h_malf_vs_serious_errors.csv` (row All / malfunction: median_pct, median_pct_reads_low); `analysis/tail_comparison_stats.json` -> median_reported_error_in_trial.

## 5. "97 to 98 % of pairs beyond 20 %"
- Answer: yes. It is the share of all pairs of that maker, in either direction, where the sensor is 20 % or more away from the meter. The code rule is "20 % or more", not "more than 20 %".
- Abbott serious: 7,301 of 7,470 pairs (97.7 %). 4,240 too low and 3,061 too high.
- Dexcom serious: 8,914 of 9,189 pairs (97.0 %). 3,917 too low and 4,997 too high.
- Source: `g_brand_error_sizes.csv` (pct_abs_err_over_20, rows "all pairs"); rule `fda-maude/scripts/text_results.py:519`; counts `analysis/tail_comparison_stats.json` -> errors_at_or_beyond.reports (thresholds -20 and +20).

## 6. Lag-corrected error under 54 mg/dL
- Direction confirmed: the sensor is below the meter, 6.5 % too low (6.48). Interval confirmed: 95 % interval 5.1 to 7.9, from a bootstrap (random re-draws) over participants, 1,000 draws, seed 20261027.
- Pairs: 2,365 from 202 people, not 2,133. `ERROR_DRIVERS.md:13` prints 2,133 (197 people). That is the count before the lag correction. The script sorts pairs into ranges again after the correction. The stats file and `ERROR_DRIVERS.md:128` say 2,365. 2,365 is right.
- "Under 54" here means the average of the sensor value and the meter value is under 54. It does not mean "the meter is under 54". Sorted by the meter alone (meter under 54; 2,174 pairs) the sensor reads 29.8 % too high (95 % interval 25.2 to 35.8). The memo explains why the average is used (`ERROR_DRIVERS.md:124`).
- Source: `analysis/error_drivers_stats.json` -> lag_correction.all_participants.after["<54"] and regression_to_the_mean["<54"]; `analysis/error_drivers.py:384,391`.

## 7. "25 % of participants had at least one error of 69 % too low or worse"
- Threshold: an error of -69.0 % or lower. That is a sensor value 69 % or more below the meter. It is a fixed line (the rounded false-low size).
- 26 randomised weeks: 57 of 225 participants (25.3 %; 95 % interval 19.6 to 31.1). They had 159 such pairs out of 137,662 (0.12 %). The base is 225 because one of the 226 has no pair in that phase. Whole study, run-in included: 67 of 226 participants (29.6 %); 179 of 168,990 pairs (0.11 %, 1 check in 944).
- Source: `analysis/tail_comparison_stats.json` -> errors_at_or_beyond.trial_randomised and trial_all, threshold_pct -69.0; `analysis/TAIL_COMPARISON.md:17,35`.

## 8. The 680 trait tests
- Tests: 680 (407 single-trait + 133 interaction + 140 worst-quartile). Raw p under 0.05: 69 of 680 (34 expected by chance). Left after the Benjamini-Hochberg correction (a correction for running many tests): 1 of 680.
- The one left is sex against low-range error, corrected p 0.016. Women: 6.4 % too low (median of 76 women). Men: 2.2 % too low (median of 74 men). Difference: 4.2 points (4.16), 95 % interval 2.0 to 6.0. Low range = pairs where the average of sensor and meter is under 70. Only people with 20 or more such pairs are tested: 150 of 226.
- The interval for the same gap appears three ways: 2.0 to 6.0 (the test's own record), 1.9 to 6.2 (follow-up block, same file), 2.0 to 6.3 (`analysis/demographics_followup_stats.json`). guess: each is a separate random bootstrap run.
- Source: `analysis/demographics_deep_stats.json` -> bh_summary.replace_bg and univariate.low_bias_pct[0].

## 9. Wear day 1 in Abbott reports
- "Expected" = 1 in 14 = 7.1 %. It assumes every day of a 14-day sensor is equally likely. No other method was used. Counts: 891 of the 6,627 Abbott death-or-injury reports that name a wear day name day 1 (13.4 %). The 6,627 are 8.9 % of the 74,657 Abbott death-or-injury reports read. 25 of the 6,627 name day 15 or later.
- Other bases give other numbers: Abbott wrong-reading reports only, 15.8 % of 2,197. Abbott malfunction sample, 34.5 % of 217 (weighted).
- Source: `fda-maude/results/text/tables/d_wear_day_summary.csv` and `d_wear_day_distribution.csv`; rule `fda-maude/scripts/text_results.py:73,624`; `BRAND_COMPARISON.md:110-111`.

## 10. Age and sex in the FDA reports: the base of each number
| Number in the outline | Base it really has | Count | Right? |
|---|---|---|---|
| Age filled 49.1 %; sex filled 41.2 % | the 39,667 serious wrong-reading reports | 19,462; 16,356 | yes |
| Dexcom fills age in 93 % | Dexcom's 14,911 of the 39,667 | 13,892 (93.2 %) | yes |
| Abbott fills age in 7 % | all 724,461 Abbott reports, any event type | 48,985 (6.8 %) | wrong base. On the 39,667 base: 4,391 of 22,935 (19.1 %) |
| Race or ethnicity 0.3 % | all 3,382,071 reports | race 0.26 %, ethnicity 0.34 % | wrong base. Inside the 39,667: not found. In all 123,607 serious reports: race 3.0 %, ethnicity 2.0 % |
| Median age 54; 12 % under 18 | the 19,462 with an age | 2,286 under 18 (11.7 %) | yes |
| 51 % female | the 16,356 with a sex | 51.1 % | yes |
| 17.5 % under 18; 28 % aged 65 or over | all reports with an age | 433,140 and 686,344 of 2,480,851 (27.7 %) | yes |
- "All reports with an age" = all 3,382,071 CGM reports of every event type (malfunction, injury, death) that hold a usable age: about 2.48 million (73 %). 2,328,174 of them are Dexcom reports.
- Two tables count "with an age" a little differently: 2,480,851 (`h_age_groups.csv`) and 2,479,918 (`demographics_age_sex.csv`). Both give 17.5 % and 27.7 %. Reason for the gap: not found.
- Source: `fda-maude/results/text/tables/g_demographics_fill.csv`, `g_demographics_age_sex_by_brand.csv`; `fda-maude/results/inventory/demographics_fill_rates.csv`, `demographics_age_sex.csv`; `fda-maude/results/report/tables/h_age_groups.csv`.

## Changes needed in the outline
- Message line 3, first list: "-66 to -77 %" should be "69 to 77 % too low". 66 is the median of all malfunction-only pairs. The second list and R3.2 are right; their [check] notes can go.
- R1.1: the share "of the corrections that were needed" rests on 202 participants, not 203.
- R1.2 (meter check) and R2.3 (last bullet): 12.3 %, 7.2 %, 1.4 % and 4.2 % are shares of all calculator decisions. "Withheld 1.4 % of corrections" is wrong wording. By the outline's own rule use the needed-correction shares: 23.8 % against 13.5 % (R1.2) and 2.1 % (R2.3). Keep 4.2 % as "of calculator decisions".
- R2.1: write the 20/20 rule out: within 20 mg/dL when the meter is under 100 mg/dL, within 20 % at 100 or above.
- R2.2: "when the meter is under 54" and "over 250" are wrong for both MARD and the 6.5 %. The ranges use the average of sensor and meter. The 6.5 % rests on 2,365 pairs (`docs/paper/FACT_SHEET.md:265` also says 2,133).
- R3.2: write "20 % or more away from the meter, in either direction". For the 26-week line the base is 225 participants (57 of 225). R5.1: write "Abbott death or injury reports" (891 of 6,627).
- R5.3: Abbott "7 of 100" is on the wrong base; on the stated base (39,667) it is 19 of 100. Race "3 in 1,000" is a share of all 3.38 million reports, not of the 39,667. Move it to the "all reports" lines or drop it.
