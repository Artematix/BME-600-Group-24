# Check of the Results prose (section 3 of PAPER.md), 2026-11-21

Every number and factual claim in section 3 of `docs/paper/PAPER.md` was compared with the project's own files. Nothing was re-run. `PAPER.md` was not changed.

- Checked: 80 table rows. They hold about 165 numbers and claims.
- Result: 4 must fix, 13 should fix, 6 claims without a source. All other rows are right.
- Where a memo and a stats file (JSON) both hold a number, the JSON was read. They agree for every number used in section 3.
- Words: pair = one sensor value with the meter value for the same moment. Median = the middle value. Base = the group a share is a share of. "derived" = worked out from counts in the source. M1, S1 = item 1 of the must fix or should fix list.
- Short names, `analysis/`: LOOKX = simulation_v2_lookup_extended.csv (row = the error in %). S2J = simulation_v2_stats.json. SIM2 = SIMULATION_V2.md. ACCJ = accuracy_v2_stats.json. SORT = ACCURACY_BY_RANGE_SORTING.md. LDW = LOW_DETECTION_WINDOW.md. TAIL = TAIL_COMPARISON.md. TAILJ = tail_comparison_stats.json. ED = ERROR_DRIVERS.md. EDJ = error_drivers_stats.json. WDJ = wear_day_stats.json. SIM3 = SIMULATION_THREE_FAULTS.md. S3J = simulation_three_faults_stats.json (`results`, 6 hours, main size). DDJ = demographics_deep_stats.json. DF = DEMOGRAPHICS_FOLLOWUP.md.
- Short names, `fda-maude/results/`: RR = report/report_results.md. AGE = report/tables/h_age_groups.csv. INV = inventory/. In `text/`: BC = BRAND_COMPARISON.md, TR = TEXT_RESULTS.md, RX = REGEX_V2_FULL_CORPUS.md. In `text/tables/`: BRAND = g_brand_error_sizes.csv, MALF = h_malf_vs_serious_errors.csv, WEAR = d_wear_day_distribution.csv and d_wear_day_summary.csv, FILL = g_demographics_fill.csv. REFS = `docs/paper/REFERENCES.md`.

## 1. Must fix

1. Section 3.3, last paragraph: "Malfunction-only reports are nearly all false lows".
   - Wrong. False lows are 110,119 of the 191,112 malfunction-only pairs. That is 57.6 %, about 6 in 10. Source: TAILJ `fault_shares[0].malfunction`; MALF `pct_false_low_70`.
   - Write: "In malfunction-only reports the false low is the main fault: about 6 in 10 pairs are false lows (57.6 %), and fewer than 1 in 20 are hidden lows (4.5 %)."
2. Section 3.5: "At 60 mg/dL that gap is about 2.5 mg/dL, which changes no dose and no alert."
   - Wrong for alerts. The follow-up memo says: no dose changes, but alerts do. In the lookup, women get 0.28 false low alerts per day and men 0.11 (an upper limit). Near 70 mg/dL women's sensors show more false lows (36 % against 31 %) and miss fewer true lows (37 % against 42 %). Source: DF:15, 198, 205, 236.
   - Write: "... about 2.5 mg/dL. It changes no dose. It shifts the low alert a little: at most about one more false low alert every six days for women."
3. Section 3.5, first sentence: "Besides the glucose range, the day of wear was the one thing that clearly moved the sensor's accuracy."
   - Wrong by the project's own model. Fast-changing glucose moved the error more: +6.3 points (falling fast) and +6.1 (rising fast), against +2.3 for the first day of wear. MARD was 18.3 % and 17.9 % when glucose moved fast, against 12.3 % when stable. This is the sensor's delay; it goes away after the 5-minute correction. Source: ED:70-74, 114-116.
   - Write: "Besides the glucose range and the sensor's delay when glucose moves fast, the day of wear was the one thing that clearly moved the sensor's accuracy."
4. Section 3.3: "The typical malfunction-only pair is one of these, with the meter at 178 and the sensor at 63."
   - Wrong base. Two paragraphs earlier "typical" is defined as the median of the pairs that read low (69 % too low). 178 and 63 are medians over all 191,112 malfunction-only pairs, low and high together. They are two separate medians, not one pair. 63 against 178 is 65 % too low, not 69 %. Source: MALF row All / malfunction.
   - Write: "Over all malfunction-only pairs the median meter value was 178 and the median sensor value 63. That is a false low."

## 2. Should fix

1. 3.3 "86 to 97 times in 100": the Dexcom value is 85.48 % (3,592 of 4,202). Write "85 to 97".
2. 3.3 "about 1 in 900": 159 of 137,662 is 1 in 866. Write "about 1 in 870". (1 in 944 is the whole-study number.)
3. 3.3 (c) "meter at 45 and the sensor at 144": these are two separate medians over the 8,644 serious pairs of all makers that read too high. It is not one pair. 144 against 45 is 220 % too high, but the median error of these pairs is 164 % too high (the size used in 3.4: 50 shows 132). 68 % of the 8,644 are hidden lows. Write "the median meter value was 45 and the median sensor value 144".
4. 3.3 heading and second paragraph: "typically 69 to 77 % too low" holds only for pairs that read low. Say how many read low: 58 % of Abbott, 44 % of Dexcom, 75 % of malfunction-only pairs. More than half of the Dexcom serious pairs (55 %) read too high.
5. 3.3 "gives three faults": about 4 in 10 pairs in each group are none of the three (derived: Abbott 38 %, Dexcom 44 %, malfunction-only 38 %). Say it in one clause.
6. 3.3 floor-pinned, 'prints as "LO"': the counted pairs state a number of 40 or below. Reports that state the word "LO" are not pairs (TAIL:68, 82).
7. 3.4 (e) "lost in about every second episode": 0.48 is a count of alerts per episode, not a share of episodes. Write "about one alert was lost for every two episodes".
8. 3.2 (l) "none of the seven accuracy criteria": the FDA rule has 11 lettered criteria (REFS:262-272). Seven were tested and all fail. Two more ("no such pair") also fail: 101 and 125 pairs. The rule asks for a lab reference, not a home meter (REFS:260). The citation still reads "[ref]"; it is REFS [28].
9. 3.5 "The reports agree": only Abbott is given. Dexcom serious reports show no first-day excess (81 of 1,140 = 7.1 %, against an even 10 %). The memo calls the Abbott excess "a template feature as much as a sensor feature" (BC:117). Only 8.9 % of Abbott serious reports name a day.
10. 3.5 (g) "92 %": this split uses rebuilt sensor sessions with MARD 15.3 % and 12.0 % (WDJ), not the 15.2 % and 11.8 % of the sentence before. Small.
11. 3.5 (m) "a similar overall picture": MARD is similar (13.9 against 13.3 %). The average error is not (7.4 % too low against 1.3 %). The 98 are hospital in-patients; 88 have type 2 diabetes.
12. 3.5 "differed little by age or sex": true for the size of the error. The direction did differ by age: children's pairs read low in 55 %, pairs of people aged 65 or over in 43 % (BC:290-295).
13. 3.1 meter check: the 23.8 % comes from 67 people of one study arm. The 13.5 % it is set against comes from 202 people of both arms. With the meter as the true value the sensor already withholds 2.1 % with no error added.

## 3. All numbers checked

| Number or claim | Source file and line | Value in the source | Verdict |
|---|---|---|---|
| 3.1 "200 mg/dL ... 12 % too low ... shows 176" | arithmetic | 200 x 0.88 = 176 | right |
| 3.1 "159,878 ... decisions ... 203 participants" | S2J `data.decisions_analysed`; SIM2:26 | 159,878; 203 | right |
| 3.1 "up to 8 % too low ... lost no corrections" | LOOKX rows -2 to -8, `skipped_of_needed_pct_median` | 0 at each step (median person) | right |
| 3.1 "12 % ... 1 in 80 ... (1.2 %)" | LOOKX row -12, same column | 1.24 % of needed corrections; 202 people | right |
| 3.1 "20 % ... 1 in 7 (13.5 %, ... 7.8 and 21.3 %)" | LOOKX row -20 | 13.47 (7.76 to 21.32); 1 in 7.4 | right |
| 3.1 "At 70 % too low they lost all of them" | LOOKX row -70; SIM2:166 | median 100 % | right |
| 3.1 heading "about 12 % too low" | SIM2:85; LOOKX rows -10, -12 | 0.34 % at 10 %; 1.24 % at 12 % | right |
| 3.1 "high line is at 180" | SIM2:40, 143 | 180; 176 is under it | right |
| 3.1 "2 % ... 1 high episode in 18 ... (5.6 %)" | LOOKX row -2, `high180_missed_pct_median` | 5.58 % of high episodes; 226 people | right |
| 3.1 "12 % ... 1 in 3 (32.6 %)" | LOOKX row -12 | 32.57 | right |
| 3.1 "20 % ... half (50.8 %, ... 43.4 to 58.7 %)" | LOOKX row -20 | 50.78 (43.40 to 58.66) | right |
| 3.1 (k) "one every ten days ... almost one a day" | LOOKX rows -2, -20, `low70_false_per_day_median`; SIM2:64 | 0.10 and 0.86 per day | right |
| 3.1 "200 ... 59 % ... against 51 %" | LOOKX row -20, `high200_missed_pct_median`; SIM2:143 | 59.1 against 50.8 | right |
| 3.1 "15,034 decisions from 67 participants" | S2J `data.meter_truth_decisions`; SIM2:115 | 15,034; 67 | right |
| 3.1 "1 in 4 of the needed corrections (23.8 %)" | S2J `meter_truth_sensitivity["-20"].mt_skipped_of_needed_pct` | 23.81 (13.6 to 34.5); a share of needed corrections | right; see S13 |
| 3.1 "the main run gave 1 in 7" | LOOKX row -20 | 13.5 % | right; see S13 |
| 3.2 "168,990 ... pairs from 226 participants" | ACCJ `sets.B.overall` | 168,990; 226 | right |
| 3.2 "1.3 % too low on average (... 0.9 to 1.6 %)" | ACCJ `sets.B.overall.bias_pct` | mean -1.28 (-1.65 to -0.87) | right |
| 3.2 "150 ... reading of 148"; "a tenth"; "20 mg/dL at a true 150" | arithmetic | 150 x 0.987 = 148; 1.3 / 12 = 0.11; 150 x 0.133 = 20 | right |
| 3.2 "13.3 % ... (the MARD, ... 12.7 to 13.9 %)" | ACCJ `sets.B.overall.mard_pct` | mean 13.25 (12.70 to 13.91) | right |
| 3.2 (l) "closest published MARD ... 11.3 %, ... home use against a meter" | REFS:184-187 | 11.3 %; home use; Contour Next meter; 51 adults | right. ACCJ `published_mard` wrongly says "clinic" |
| 3.2 (l) "meets none of the seven accuracy criteria" | ACCJ `sets.B.icgm.rules` | 7 of 7 fail | right; see S8 |
| 3.2 "29.8 % too high ... under 54"; "22.5 % too low" | SORT:23, 32 | 29.8 (sorted by meter); 22.5 (by sensor) | right |
| 3.2 "1.4 to 2.8 times" | SORT:58 | 1.39 (average), 1.95 (sensor), 2.80 (meter) | right |
| 3.2 "10,104 checks ... 3,177 ... 3 in 10 (31.4 %, ... 29.3 to 33.7 %)" | LDW:27; TAILJ `fault_shares[2].trial_all` | 3,177 of 10,104 = 31.44 (29.32 to 33.67) | right |
| 3.2 "5 to 7 minutes behind the blood" | ED:58 | 5 min (real readings); 7 min (smoothed trace) | right |
| 3.2 "Clinic studies ... within 15 minutes" | REFS:597; LDW:8 | one study with a 15-minute window | right; see list 4 |
| 3.2 "2 in 10 ... still not shown (18.5 %)" | LDW:28 | 1,872 of 10,104 = 18.53 | right |
| 3.2 "1 reading in 9 was 20 % or more too low (10.8 %)" | TAILJ `errors_at_or_beyond.trial_all`, -20 | 18,209 of 168,990 = 10.78; 1 in 9.3 | right |
| 3.3 "123,607 serious reports" | RR:88 | 123,607 | right |
| 3.3 "most common problem ... 1 in 3 (33.1 %)" | RR:72, 84 | 33.1 % of serious reports (FDA problem codes); next kind 28.1 % | right |
| 3.3 "7,470 ... 9,189 ... 191,112" pairs | BC:34-35; RX:8; TAILJ `pair_sets` | same | right |
| 3.3 "meter 200 ... showed 46 ... 77 %"; "62 ... 69 %" | BRAND rows serious / Abbott and Dexcom / sensor below meter | -76.8 % (4,315 pairs); -69.2 % (4,029); 200 x 0.232 = 46; 200 x 0.308 = 62 | right; see S4 |
| 3.3 "malfunction-only pair was also 69 % too low" | MALF row All / malfunction, `median_pct_reads_low` | -69.4 (142,817 pairs) | right |
| 3.3 "about six times the 12 %" | arithmetic | 69 / 12 = 5.8; 77 / 12 = 6.4 | right |
| 3.3 (a) "other pairs read too high, most ... by more than 100 %" | TAILJ `errors_at_or_beyond.reports`, +100 | of the pairs that read high: 2,359 of 3,126 Abbott (75 %); 3,537 of 5,088 Dexcom (70 %); 36,626 of 48,295 malfunction-only (76 %) | right |
| 3.3 "159 of 137,662 ... about 1 in 900" | TAILJ `errors_at_or_beyond.trial_randomised`, -69 | 159 of 137,662 = 1 in 866 | rounding; see S2 |
| 3.3 "225 participants, 57 ... 1 in 4" | same row | 57 of 225 = 25.3 % | right |
| 3.3 "3 to 11 % ... (from 35 % too low to 40 % too high)" | TAILJ `inside_trial_central_95.trial_all` | 3.25, 6.63, 11.45 %; -35.3 to +40.4 | right |
| 3.3 (c) "meter at 178 and the sensor at 63" | MALF row All / malfunction | medians over all 191,112 pairs | wrong base; see M4 |
| 3.3 (c) "meter at 45 and the sensor at 144" | BRAND row serious / All / sensor above meter; SIM3:34 | two medians over 8,644 pairs | right; see S3 |
| 3.3 "3 times in 100 ... 32 to 60" | TAILJ `fault_shares[0]` | 3.02; 31.9, 49.5, 60.4 | right |
| 3.3 "31 times in 100 ... 86 to 97" | TAILJ `fault_shares[2]` | 31.4; 85.48, 92.7, 97.0 | rounding; see S1 |
| 3.3 "2 of 20,655 ... 7 to 8 times in 100" | TAILJ `fault_shares[4]` | 2 of 20,655; 7.31, 7.56, 7.99 | right; see S6 |
| 3.3 (b) "Malfunction-only ... nearly all false lows" | TAILJ `fault_shares[0].malfunction`; MALF | 110,119 of 191,112 = 57.6 % | wrong; see M1 |
| 3.3 (b) "4 in 10 Dexcom pairs and 1 in 4 Abbott pairs" | BRAND `pct_missed_low_70`, rows all pairs; TAILJ `fault_shares[2]` | 3,592 of 9,189 = 39.1 %; 1,946 of 7,470 = 26.1 % | right (same 9,189 and 7,470) |
| 3.4 "150 mg/dL ... 69 % lower, here 46" | S3J `fault_sizes.false_low` | -69.4 %; 150 x 0.306 = 46 | right |
| 3.4 "15 g ... after 15 minutes" | S3J `settings.sugar_rule`; REFS:642 | 15 g; 15 min | right |
| 3.4 (d) "about 20 times" | S3J `false_low`, `sugar_unneeded_n_per_episode`; SIM3:64 | 20.3 (19.4 to 21.2), median person | right |
| 3.4 (d) "nearly once every 15 minutes ... about 300 g" | SIM3:62, 65 | 20.3 in 5.26 h = one per 15.5 min; 304 g | right |
| 3.4 (d) "half a unit ... not given" | S3J `false_low`, `dose_lower_u_per_episode` | 0.52 units (203 people) | right |
| 3.4 (d) "83 minutes" | S3J `false_low`, `min_over180_not_shown_per_episode` | 83.4 | right |
| 3.4 (d) "66 % too low ... (18.5)" | S3J `false_low["6"]["bias_-66"]`; SIM3:80 | 18.5, against 20.3 for the fault | right |
| 3.4 "50 mg/dL ... here 132" | S3J `fault_sizes.hidden_low` | +163.6 %; 50 x 2.636 = 132 | right |
| 3.4 "34 minutes ... (23 to 45)" | S3J `hidden_low`, `min_under54_no_alert_per_episode` | 33.7 (23.1 to 45.1); 225 people | right |
| 3.4 (e) "lost in about every second episode" | S3J `hidden_low`, `low54_missed_n_per_episode`; SIM3:70 | 0.48 alerts per episode (0.42 to 0.56) | right; see S7 |
| 3.4 "can never hide a low" | SIM3:89-90 | 0 under every steady low error | right |
| 3.4 (f) "above 250 for about 2 of the 6 hours ... about 5" | S3J `affected_h_per_episode` | 1.92 h (floor-pinned); 5.26 h (false low) | right |
| 3.4 (f) "1.3 units ... two and a half times" | S3J `floor_pinned`, `dose_lower_u_per_episode` | 1.29; 1.29 / 0.52 = 2.5 | right |
| 3.4 (f) "0.64 units against 0.10" | S3J `dose_lower_u_per_hour`; SIM3:114-115 | 0.639 and 0.104 (median person's own hourly rate) | right |
| 3.5 "day of wear was the one thing" | ED:70-74, 114-116 | fast change +6.3 and +6.1 points; first day +2.3 | wrong; see M3 |
| 3.5 "15.2 % on the first day ... 11.8 % on the seventh" | EDJ `wear_day.by_wear_day` | 15.25; 11.81 | right |
| 3.5 (g) "halved about every 24 hours" | WDJ `half_life_h`; `analysis/WEAR_DAY.md`:14 | 23.9 h | right |
| 3.5 (g) "92 %, ... 85 to 100 %" | WDJ `selection.decomposition` | 92.4 (85.0 to 99.5) | right; see S10 |
| 3.5 "6,627 ... 891 ... (13 %)" | WEAR rows serious / Abbott | 891 of 6,627 = 13.4 % | right; see S9 |
| 3.5 (h) "14 days ... would give 7 %" | WEAR `sensor_life_days`; TR:116 | 14; 1 / 14 = 7.1 %. The memo calls 14 "a simplification": 15-day sensors exist and 25 of the 6,627 reports name day 15 or later. With 15 days it is 6.7 % | right (7 % either way) |
| 3.5 (j) "680 ... 34 ... 69 ... 1 remained" | DDJ `bh_summary.replace_bg` | 680; 34.0; 69; 1 | right |
| 3.5 "6.4 % ... women ... 2.2 % ... men (4.2 points, ... 2.0 to 6.0)" | DDJ `univariate.low_bias_pct[0]` | medians: -6.41 (76 women), -2.24 (74 men); 4.16 (2.02 to 6.02) | right |
| 3.5 "At 60 mg/dL ... about 2.5 mg/dL" | arithmetic; DF:15 | 60 x 0.042 = 2.5 | right |
| 3.5 "changes no dose" | DF:15, 198 | no dose change | right |
| 3.5 "and no alert" | DF:15, 198, 236 | alerts do change | wrong; see M2 |
| 3.5 (m) "98 Chinese patients, MARD ... 13.9 % ... 7 % too low" | ACCJ `sets.S.overall` | 98 of 112 patients; 13.89; -7.44 | right; see S11 |
| 3.5 (i) "2.48 million ... 1 in 6 ... (17.5 %)" | AGE | 433,140 of 2,480,851 = 17.5 %; 1 in 5.7 | right |
| 3.5 (i) "more than 1 in 4 ... 65 or over (28 %)" | AGE | 686,344 of 2,480,851 = 27.7 % | right |
| 3.5 "The trial had no children" | `analysis/DEMOGRAPHICS_DEEP.md`:26 | age range 19 to 78 | right |
| 3.5 (i) "1 participant in 12 was 65 or over" | INV demographics_trial_side_by_side.csv | 8.4 % of 226 = 19 people | right |
| 3.5 "differed little by age or sex" | BC:295, 314 | every difference "negligible" in size | right; see S12 |
| 3.5 "39,667 ... only half record an age" | FILL row serious / All | 49.1 % of 39,667 | right |
| 3.5 (i) "race or ethnicity ... 3 of every 1,000" | INV demographics_fill_rates.csv, row all reports | race 0.3 %; ethnicity 0.3 % of 3,382,071 | right |
| 3.5 "six other kinds of simulated fault"; rate of change, time of day, site, country | SIM2:47-52; `docs/paper/tables/tableS1_full.md`:46, 93 | 6 fault kinds besides the steady error; each analysis is listed | right |

## 4. Claims with no source found

- 3.1 "Many high-glucose episodes sit only a little above that line." No count of how far episodes sit above 180 was found. (It fits the 5.6 % at a 2 % error.)
- 3.1 and 3.2: the total number of needed corrections (the base of "1 in 80", "1 in 7", "1 in 4"). The files hold each person's share only.
- 3.2 "Clinic studies ... any sensor reading within 15 minutes". One study in REFS states a 15-minute window (REFS:597). "Studies" and "before or after" have no second source. LDW:7-8 says this was not re-checked.
- 3.2 (l) "for this sensor": the cited paper does not name the software version. REFS:186 marks the match as a guess.
- 3.4 "A real person would stop or check with a meter long before that." SIM3:137 says "would likely". It is a guess in the source.
- 3.4 "the curve in Figure 2 already covers it." The Figure 2 run has no sugar count (LOOKX has no sugar column). The 18.5 comes from the three-fault run's own comparison row.
