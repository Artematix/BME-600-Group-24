# Phase 2 findings memo (2026-10-30)

For the writing team (sections drafted Nov 6-13). Every number comes from a named file in `analysis/` or `fda-maude/`. Nothing was recomputed. Open the source file for the full table before pasting a number into the paper.

Updated 2026-11-08. Five memos dated 2026-11-06 are folded in: findings 9 to 12 (section 2), the pointer list in section 6.2, the figure rows for 29-35 and t7-t13 (section 8), paper sentences 11 to 15 (section 9) and the open items in section 10. The field-inventory memo `fda-maude/results/FIELD_INVENTORY.md` was finished 2026-11-08 (see section 6.2).

Terms used throughout:
- CGM = continuous glucose monitor (the skin sensor). Meter = fingerstick blood glucose meter, treated as the truth.
- Pair = one CGM reading matched in time to one meter value. Verified pair = the meter value came from the meter's own log and was not used to calibrate the sensor.
- Set B = all verified pairs, 226 people, 168,990 pairs (headline set). Set A = Set B limited to the CGM+BGM arm after randomisation, 77 people, 33,467 pairs (the plan's promised primary sample). Set C = CGM-only arm, 148 people, 104,195 pairs.
- Bias = average of (CGM minus meter). Negative = the sensor reads low. MARD = mean absolute relative difference, the average percent error.
- CI = 95 % confidence interval, from resampling participants (not pairs). IQR = interquartile range, the middle half of people.
- Parkes grid = chart that sorts errors into harmless (A, B) and dangerous (C, D, E) zones. iCGM = the FDA accuracy rule for CGMs (21 CFR 862.1355).
- LBGI = low blood glucose risk index (higher = more risk from lows). TIR = time in range, the share of readings at 70-180 mg/dL.
- Lag = the sensor trails blood glucose by some minutes. Wear day = days since the sensor was put on.
- Bolus calculator = the pump feature that turns a typed glucose value into an insulin dose. ISF = insulin sensitivity factor, the patient's own pump setting.
- MAUDE = FDA database of device problem reports (Phase 1). BH = Benjamini-Hochberg, a correction for running many tests. CV = coefficient of variation, how much a person's glucose swings.

## 1. Main finding

**In real home use the sensor was least reliable exactly where a reading changes what the patient does: it missed 28 % of true lows below 70 mg/dL (95 % CI 24 to 33 %), and 38 % of the lows it showed were not confirmed by the meter.**

| Number (Set A unless stated) | Value (95 % CI) | Source |
|---|---|---|
| Meter-confirmed lows (<70) that the sensor showed as not low ("missed lows") | 28.2 % (24.4 to 32.8); 689 of 2,440 pairs | `ACCURACY_V2.md` s7 |
| Same rate in Set B / Set C | 31 % / 33 % | `ACCURACY_V2.md` s7 |
| Sensor-shown lows confirmed by the meter (PPV) | 62.1 % (57.8 to 66.5); 1,751 of 2,818, so 38 % were not confirmed | `ACCURACY_V2.md` s7 |
| Lows detected at 70 / at 54 mg/dL (sensitivity) | 71.8 % (67.2 to 75.6) / 51.8 % (45.7 to 56.7) | `ACCURACY_V2.md` s7 |
| Any pair on the wrong side of 70 or 180; missed highs | 15.0 % (13.6 to 16.6); 18.1 % (15.6 to 20.9) | `ACCURACY_V2.md` s7 |
| MARD below 54 vs above 250 mg/dL (by average of both devices) | 19.1 % (18.0 to 20.4) vs 10.2 % (9.5 to 11.4) | `ACCURACY_V2.md` s5a |

Figure: `figures/15_misclassification_70_180.png`, with figure 13 for the range gradient.

Why this and not the other candidates:
- Not the 20 % tipping point (simulation). That says what a constant bias WOULD do. This is measured on real pairs, holds in all three pair sets (28 / 31 / 33 %), and has a CI. The tipping point is supporting finding 1 and supplies the "how much error" half of the question.
- Not the low bias after lag correction, or its concentration on wear day 1. That answers the plan's primary uncertainty (supporting finding 2). But a 4 to 7 % average bias is not by itself a changed decision, and the wear-day split was exploratory, so by our own rules (`METHODOLOGY.md` step 3) it cannot be the headline.
- Not "glucose pattern, not demographics". A null result plus a correlation of 0.33. It answers neither half of the research question. It is supporting finding 5 and a Discussion point.

Link to Phase 1: in serious FDA reports, wrong readings are the top device problem (33.1 %) and hypoglycaemia the top patient problem (40.8 %) (`fda-maude/results/report/report_results.md` d, e). Phase 2 shows the trial sensor's threshold errors also concentrate at the low line.
Honesty note: the G4's low-line errors run both ways (689 missed lows, 1,067 false lows). The Libre 3 recall was one way (false lows). Both are "wrong readings that cross 70 mg/dL". The simulation covers the recall direction; the real pairs cover the G4's own pattern.

## 2. Supporting findings, ranked

**1. Insulin-dose decisions start to change at about 12 % low bias and are clearly changed at 20 %; 10 % does almost nothing to doses.**
- Median person: at -10 %, 0.2 % of corrections skipped and 0 % changed by more than 1 unit. At -20 %, 7.2 % skipped (CI 6.6 to 8.2), 16.7 % changed by more than 1 unit (CI 11.1 to 22.9), 51 % of high episodes above 180 hidden (IQR 43 to 59), 0.86 false low alerts per day (CI 0.81 to 0.91). At -30 %, 20.0 % skipped (CI 18.8 to 21.1), 36.0 % changed (CI 30.3 to 40.9). Even -10 % hides 28 % of high episodes and adds 0.40 false lows per day. `SIMULATION_V2.md` s5. Figure 25.
- Method: 159,878 real bolus-calculator decisions from 203 people, each with the patient's own ISF and target. The dose rule matches the pump's own number within 0.15 units in 90 % of records. Why 10 % is small: 10 % of 200 mg/dL is 20 mg/dL, which is 0.4 units at a typical ISF of 50.
- Limit: the "true" glucose is the CGM trace itself; with a fingerstick as truth (67 people) the real G4 already changes 4.2 % of corrections by more than 1 unit, and -20 % bias skips 12.3 % (`SIMULATION_V2.md` s7). A constant bias is a model, not the real error pattern.

**2. The low-glucose bias is real: it survives lag correction and the removal of calibration pairs, and it grows slightly.**
- Lag-corrected (CGM reading 5 min after the fingerstick), binned by the average of both devices: -6.5 % below 54 (CI -7.9 to -5.1; 2,133 pairs) and -4.1 % at 54-69 (CI -4.9 to -3.2; 7,816 pairs). Uncorrected: -5.1 % and -2.8 %. Same in the CGM+BGM arm: -6.5 % and -4.8 %. In mg/dL it is small: -4.6 and -3.9. `ERROR_DRIVERS.md` s1. Figure 18.
- Method: re-pair each fingerstick with the CGM reading 5 minutes later (the best shift); all pairs are verified pairs. Adding simulated meter noise pushes the bias toward zero, so meter error cannot create it (`ACCURACY_V2.md` s9).
- Limit: the reference is a home meter; the mg/dL size is within meter noise for a single reading. This is the plan's "primary uncertainty", now answered: yes, it persists.

**3. The sensor trails blood by 5 to 7 minutes, and the "rate of change" effect is that lag, not a separate fault.**
- Best shift 5 min on real readings (98 % of bootstrap draws), 7 min on the interpolated trace; per person median 7 min (IQR 5 to 9). MARD falls from 13.2 % to 12.2 % with the shift. Fast-falling bias +12.7 % (CI 11.6 to 13.9) becomes +0.7 % (CI -0.2 to 1.7); fast-rising -9.4 % (CI -10.5 to -8.2) becomes +0.4 % (CI -0.6 to 1.6). `ERROR_DRIVERS.md` s3-4. Figures 17, 19.
- Method: re-pair at shifts of -5 to 20 minutes; 163,174 pairs with a reading at every shift.
- Limit: meter and receiver clocks differ by 1 to 2 minutes; the patient sees the unshifted value, so headline accuracy stays unshifted.

**4. Wear day 1 is the worst day, and the low-range bias sits almost entirely on day 1 (exploratory).**
- MARD 15.2 % on day 1 (CI 14.6 to 15.9) vs 11.8 % on day 7 (CI 11.2 to 12.5); 86 % of people are worse on day 1 (per-person median +2.2 points, IQR 0.9 to 3.4). Below 54 mg/dL: day 1 -12.3 % (CI -14.5 to -10.1; 513 pairs, 146 people), days 2-6 -2.3 % (CI -4.1 to -0.6), day 7 -0.6 % (CI -4.6 to 3.2). At 54-69: day 1 -9.0 % (CI -10.8 to -7.2). In the mixed model day 1 adds +2.3 points (CI 2.1 to 2.6). `ERROR_DRIVERS.md` s5, s7. Figure 20.
- Method: sensor sessions inferred from gaps of 115 min or more and confirmed by a start-up calibration (150,690 pairs); 41.7 % of sessions end at 6.5-7.1 days, matching the 7-day sensor life (`PREPROCESSING.md` s4).
- Limit: no sensor-start marker exists; the day-1 low-range split was not pre-specified. Answered 2026-11-06: the day-1 effect is the sensor settling in, not bad sensors (finding 9). The wear day of real complaints is in section 6.1 (Abbott names day 1 in 13.4 %).

**5. Who gets worse accuracy? Nobody in particular. Error follows the person's glucose pattern, not who they are.**
- Per-person MARD median 12.3 % (IQR 10.7 to 14.3), 226 people; low-range MARD 17.6 % (IQR 15.5 to 19.4), 150 people. Age, sex, BMI, HbA1c, diabetes duration and study arm: none passes BH (smallest adjusted p 0.15); the six-term model explains 2 % of the spread. Glucose CV and time below 70 each correlate with MARD at rho 0.33 (CI 0.20 to 0.44). The +5-point low-range penalty is the same in every group (differences within -1.1 to +1.2). `SUBGROUPS.md` s2-4, s7. Figures 21, 22, 23.
- Method: participant as the unit; pre-specified list reported one by one with CIs; exploratory list (22 tests) BH-corrected.
- Limit: narrow cohort (adults, 94 % White, all on pumps); two-group splits can only detect 1.7 to 2.2 points. Race, income and education described, not tested (14 non-White people). Re-tested with 680 pre-registered tests in finding 10: still null, with one modest exception (sex, low-range bias only).

**6. A low-reading sensor hides itself: the usual summary metrics improve while real risk of lows rises.**
- At -20 % bias, TIR rises from 63.3 % to 74.8 %, time below 70 from 3.5 % to 10.1 %, LBGI from 0.95 to 2.33 (CI 2.16 to 2.53), while the high-glucose index HBGI falls from 7.25 to 3.09. `SIMULATION_V2.md` s5. Figure 28.
- Method: Kovatchev risk indices on the faulted 5-minute trace. Limit: constant bias on a CGM trace, as in finding 1.

**7. Across fault types, a constant low bias hurts dose decisions most; noise is the only fault that hides low episodes.**
- At a matched size: bias -20 % skips 7.2 % of corrections; drift to -20 % by day 7 skips 1.8 % (IQR 0.8 to 3.3); noise with SD 10 mg/dL skips 0 % but misses 13 to 14 % of low episodes (white 14.4 %, IQR 12.3 to 18.2; autocorrelated 12.9 %, IQR 10.7 to 15.6) by breaking them into pieces shorter than 15 min; 5 % dropouts miss 3.6 % (IQR 3.3 to 4.1); a 10-min lag only delays every alert by 10 min. `SIMULATION_V2.md` s6. Figure 26.
- Method: six fault families, 10 random draws per person. Limit: fault sizes were chosen, not measured; Phase 1 text extraction will say which sizes occur in real reports (pending).

**8. Against the FDA iCGM benchmark the G4 fails all seven criteria, two of them narrowly (benchmark only).**
- Below 70 within 15 mg/dL: 69.6 % (lower bound 66.1; needs above 85). 70-180 within 15 %: 69.8 % (bound 67.3; needs 70). Above 180 within 15 %: 78.4 % (bound 76.0; needs 80). All pairs within 20 %: 81.5 % (bound 79.3; needs 87), so 18.5 % of readings were more than 20 % off. `ACCURACY_V2.md` s6. Figure 14.
- Method: binned by the CGM value with a lower one-sided 95 % bound, as the rule does. Limit: the G4 (2012-2015) predates the 2018 rule, and our reference is a home meter, not lab blood. Published home-use MARDs with meter references run 14 % (`ACCURACY_V2.md` s10), so 13.8 % is in line.

Findings 9 to 12 were added 2026-11-08 from the memos dated 2026-11-06. Findings 9 and 10 are Phase 2 (trial data). Findings 11 and 12 are Phase 1 (FDA report texts) and carry the MAUDE caveat: report counts are not failure rates.

**9. Wear day 1 is bad because every sensor is settling in, not because bad sensors get pulled early. The extra error halves every 24 hours and is flat from day 5. (Answers the open question in finding 4.)**
- Settling = the same sensor reads worse on its first day than later. Selection = bad sensors are pulled early, so day 1 holds more of them. Split of the 3.3-point day-1 excess over day 7: settling 3.0 points (92 %, CI 85 to 100), selection 0.25 points (8 %, CI 0.5 to 15). The same sensors that lasted 7 days read MARD 15.1 % on day 1, 13.1 % on day 2 and 12.0 % on days 5 to 7; 81 % of people show it on their own sensors. `WEAR_DAY.md` s1, s4, s9. Figure 33.
- Sensors pulled on day 1 do read worse (19.4 % vs 15.1 %, +4.3 points, CI 2.2 to 6.6), but they are 7 % of sessions and 3.5 % of day-1 pairs. Dropping every session that did not reach day 7 moves day-1 MARD only from 15.3 % to 15.1 %. `WEAR_DAY.md` s3.
- Speed: the extra error halves about every 24 h (time constant 34 h, CI 25 to 48). Two thirds is gone after day 1; within half a point of the final level by about 72 h (CI 53 to 100); flat from day 5. `WEAR_DAY.md` s4.
- Day 1 is noisier, not biased: bias -0.9 % vs -0.5 % on day 7, but errors over 20 % are 1.5 times as common (23.5 % of pairs vs 15.3 %), in both directions. Only in the low range (below 70) is day 1 biased: a new sensor reads about 10 % low there, fading from -14 % in its first 6 h to -7 % at 18 to 24 h, and gone by day 2. That is why day 1 has twice the false lows and no more missed lows. `WEAR_DAY.md` s5, s7.
- Calibration timing does not explain it: day 1 is worse at every time since the last calibration, and the error just before each calibration is 19.3 % on day 1 vs 11.9 % on day 7. `WEAR_DAY.md` s6. Figure 34.
- Link to Phase 1: a day-1 cluster of complaints is expected even when no sensor is defective, because day 1 has 1.5 times the large errors and twice the false lows. Abbott complaints name day 1 in 13.4 % (flat expectation 7.1 %); Dexcom complaints show no day-1 peak although the trial's Dexcom sensor is clearly worst on day 1. Complaint timing is not an error rate. guess (the memo's): the calibration-related part of the G4's settling does not transfer to the factory-calibrated Libre 3; the low-range "reads low on day 1" part may. `WEAR_DAY.md` s8.
- Method: sessions inferred from gaps and start-up calibrations; the same sensor compared across its own days; 1,000 participant bootstrap draws. Limit: sessions are inferred, not read from a sensor ID (the raw-session version gives 12 % selection instead of 8 %, same conclusion); a restart looks like a replacement; fingersticks are not random (sensors pulled on day 1 were checked 60 % more often per hour). `WEAR_DAY.md` s2, s10.

**10. Who the person is does not predict sensor error, now tested hard. One modest exception: in the low range the sensor reads about 2.5 mg/dL lower in women than in men.**
- Pre-registered = every test was listed before any ran. 680 tests on 226 people: 67 traits x 7 error measures, 18 pairs of traits (133 interaction tests), 140 worst-quartile tests. 69 had raw p below 0.05; 34 would be expected by chance; one passed the BH correction. Every 2x2 group median sits between 11.3 and 13.0 % MARD. `DEMOGRAPHICS_DEEP.md` summary, s13. Figures 29, 30.
- Location: clinic site holds 3.5 % of the MARD spread (ICC 0.035; ICC = the share of the person-to-person spread that sits between sites; permutation p 0.10), and 1.3 % once glucose pattern is in the model. `DEMOGRAPHICS_DEEP.md` s7, s13. Figure 31.
- Flexible models (random forest, gradient boosting, ridge) cannot predict a person's MARD from demographics (out-of-fold R-squared below zero in every run; R-squared = the share of the spread a model predicts, 0 = nothing). Glucose pattern alone reaches 0.03 (0.14 for the missed-low rate); adding demographics makes every model worse. Mediation chains (trait -> glucose pattern -> MARD) exist but are tiny: younger age -> more swings -> higher MARD is -0.07 SD (CI -0.12 to -0.03), about 0.3 MARD points per 14 years. Shanghai (76 patients): nothing in 60 tests. `DEMOGRAPHICS_DEEP.md` summary, s14. Figure 32.
- The exception (modest). Low-range bias -6.4 % in women vs -2.2 % in men; men minus women +4.2 points (CI +2.0 to +6.3); about 2.5 mg/dL at 60 mg/dL. Low-range MARD is identical by sex (17.5 vs 17.6 %). It is a sensor pattern, not a glucose pattern: women and men go low equally often and equally deep by fingerstick, and matching pairs on glucose level and trend leaves the gap at +3.7 (CI +1.9 to +5.6). Nothing held in the data explains it: weight, BMI, height, HbA1c, age and insulin dose per kg leave the sex term at +4.0 (CI +0.9 to +7.0); not lag, wear day, time of day, trend or testing habits; haematocrit and sensor site are not in the data. `DEMOGRAPHICS_FOLLOWUP.md` summary, s4-5, s11. Figure 35.
- Why modest: the gap is absent in the randomised CGM+BGM arm (+0.6, CI -2.5 to +3.5; 24 women, 12 men), though present in the blinded run-in where nobody could see the sensor (pooled +5.8, CI +2.0 to +9.9). Outside checks are weak: Shanghai has 50 low pairs (uninformative); MAUDE Dexcom complaints point the same way by a few points (women's reports "reads low" 49 % vs 45 %); no published paper reports a sex difference in CGM low-range bias. `DEMOGRAPHICS_FOLLOWUP.md` s6-7, s9-10, s12.
- Does it matter: no dose changes and no skipped corrections (a 4-point bias is far below the 10 to 12 % where the dose rule starts to move). It moves only the 70 mg/dL alert line: near 70, women's sensors show 5 points more false lows (36 vs 31 %) and miss 5 points fewer true lows (37 vs 42 %). `DEMOGRAPHICS_FOLLOWUP.md` s8.
- Paper sentence (from the memo): "In the low range the sensor read about 2.5 mg/dL lower in women than in men (bias -6.4 vs -2.2 %, difference +4.2 points, CI +2.0 to +6.3); the gap survived matching on glucose level and trend and adjustment for body size, was absent in one small study arm, has no known mechanism, and is too small to change a dose."
- Limit: 680 tests in one family is harsh, so a real effect under about 1.5 MARD points could be missed; groups under 10 people were not tested; home-meter reference, so a meter effect by sex (for example haematocrit) cannot be ruled out. `DEMOGRAPHICS_DEEP.md` s15; `DEMOGRAPHICS_FOLLOWUP.md` s12.

**11. Abbott and Dexcom complaints are equally far off, but they fail at different glucose levels: Abbott shows false lows while the true glucose is high; Dexcom shows normal numbers while the true glucose is low. (Phase 1)**
- Set: 39,667 serious wrong-reading reports (Abbott 22,935; Dexcom 14,911; Senseonics 1,014; Medtronic 757, caution label); 17,573 of them state both the sensor and the meter value. `BRAND_COMPARISON.md` summary, s2.
- Size: median absolute error 86 % (Abbott) vs 87 % (Dexcom) of the meter value; no difference. Senseonics errors are smaller (66 %). `BRAND_COMPARISON.md` s3. Figure t7.
- Where the true glucose was (the biggest real difference): meter under 70 (a hidden low) in 46 % of Dexcom pairs vs 28 % of Abbott pairs (-18 points, CI -19 to -16). Sensor under 70 while the meter was not (a false low) in 36 % of Abbott pairs vs 17 % of Dexcom pairs; the typical Abbott pair is sensor 60, meter 318 mg/dL. Holds in every period and in both Abbott text forms. Medtronic (caution) looks like Dexcom. `BRAND_COMPARISON.md` s4, s9. Figure t8.
- Direction: Abbott pairs read low in 58 %, Dexcom in 44 % (14 points apart, CI 12 to 15), in 7 of 9 years and outside the recall windows. The gap shrinks to 4 points after the Nov 2025 recall and 2 points in 2026 (64 vs 62 %), because each brand's newest sensor leans low (Libre 3: 67 % read low; G7: 55 %). So "reads low" is a current-generation fault for both brands, not an Abbott fault. `BRAND_COMPARISON.md` s3, s6, s9. Figure t9.
- Most other brand gaps are reporting style, not failure: FDA outcome code "Required Intervention" 81 % (Abbott) vs 4 % (Dexcom), "Other" 91 % for Dexcom; fingerstick mentioned 53 vs 81 %; age filled 19 vs 93 %; stated Parkes zones (Abbott only C to E). Deaths, which both must code the same way, do not differ (0.2 vs 0.1 %). `BRAND_COMPARISON.md` s5, s9.
- Age and sex in MAUDE: age filled in 49 % and sex in 41 % of reports, almost all Dexcom; median age 54; children under 18 are 12 %; 51 % female. Children's complaints read low more often (55 % vs 43 % for 65+) and end in hypoglycaemia more often (20 % vs 11 %). Sex makes no practical difference. `BRAND_COMPARISON.md` s8. Figure t10.
- Limit: complaint reports, not failure rates; brand counts follow how many sensors are worn, how each maker writes, and recall news. Medtronic is undercounted and had the weakest validation (kappa about 0.6). "LO" and "HI" display words are not pairs, so the most extreme reads-low cases are undercounted (more for Abbott). The model's outcome field has known weak spots; a teammate check of 100 gold-set reports was done 2026-11-08 (no issues). The post-recall window is still filling. `BRAND_COMPARISON.md` s10.

**12. The 3.3 million malfunction-only reports hold one fault: a false low of 60 to 80 % at normal or high true glucose. Serious reports hold the two other failures: hidden lows, and sensors pinned at their floor while the true glucose is very high. (Phase 1, patterns only)**
- Malfunction-only report = filed as a device problem with no death or injury code; 3.3 million of the 3.38 million CGM reports. Patterns = fixed text rules, no AI. The patterns now find 89 % of the pairs the language model found (was 73 %; Abbott 63 -> 88 %, Dexcom 81 -> 91 %); where both find a pair they agree exactly in 88 %; wear-day recall 71 -> 95 %. `REGEX_V2_FULL_CORPUS.md` s2. Figure t11.
- Over all 3,382,071 reports: 209,388 pairs; 191,112 in malfunction-only reports (never read by the model) and 18,237 in death or injury reports. 85 % of the malfunction pairs are Abbott template reports (the maker's fixed-form complaint text), 81 % from 2025-2026. `REGEX_V2_FULL_CORPUS.md` s5.
- Malfunction-only pairs are one failure: median error -66 %, 75 % read low, true glucose under 70 in only 5 %. Death or injury pairs are two failures: hidden lows (true glucose under 70 in 38 %; sensor reads normal or high) and extreme false lows at very high true glucose (sensor at LOW or under 40 while the meter is over 250). Their absolute error is bigger (median 85 % vs 72 %) but the direction, not the size, is what differs. `REGEX_V2_FULL_CORPUS.md` s6. Figure t12.
- Harm gradient: the share of pairs filed as death or injury is U-shaped against the error (high at both ends, low in the middle) in both brands. Lowest in the common -80 to -50 % band (Abbott 1 to 4 %, Dexcom 10 to 17 %); highest with the sensor near its floor against a high true value (-100 to -90 %: Abbott 42 %, Dexcom 79 %) and with the sensor reading 2 to 3 times the true value, a hidden low (over 200 %: Abbott 12 %, Dexcom 76 %). Partly real (same shape in both brands; both ends match how harm happens), partly coding (Abbott 4 % vs Dexcom 28 % of pairs coded serious is reporting style; the small-error peak is a reporting artefact). Harm words in malfunction-only texts stay at about 1 % in every band, so the malfunction pile is not hiding coded harm. `REGEX_V2_FULL_CORPUS.md` s7. Figure t13.
- What it does to the question: it sharpens from "how big is the error?" to "where on the glucose scale, and in which direction?". The constant-bias lookup (section 6.1) covers the malfunction fault; the two serious faults need a simulation that fixes the true glucose band (under 54, over 250), not the bias size. Suggested, not decided: see section 10. `REGEX_V2_FULL_CORPUS.md` s9.
- Limit: the patterns have no understanding; precision is estimated (88 to 91 % agreement with the model), not measured against a gold set; about 1 in 5 serious prose pairs joins numbers from two moments. Bounds and display words ("LO") are left out, so the most extreme reads-low cases are undercounted. Brand and era are mixed (Abbott 2025-2026 templates, Dexcom 2019-2021 prose). Event type is the reporter's choice; harm words are words, not confirmed outcomes. `REGEX_V2_FULL_CORPUS.md` s11.

## 3. What changed since the midterm plan, and why

Two sentences for the instructor: After the midterm we found that about a third of our reference fingersticks had been used to calibrate the sensor, and that many "fingersticks" in the data were sensor values typed into insulin pumps. Removing both leaves 168,990 verified pairs, raises MARD from 10.4 % to 13.3 %, leaves the direction of every finding unchanged, and makes the two study arms agree.

| Step (`ACCURACY_V2.md` s3) | Pairs | MARD % (CI) |
|---|---|---|
| Midterm headline: every meter-table pair, all days | 475,502 | 10.4 (9.9 to 10.9) |
| Keep the study window (day 0-329) | 460,634 | 10.2 (9.8 to 10.7) |
| Drop pump "BG" entries (contamination 1) | 285,166 | 11.9 (11.4 to 12.3) |
| Drop calibration fingersticks (contamination 2) = Set B | 168,990 | 13.3 (12.7 to 13.9) |
| CGM+BGM arm, randomised phase = Set A | 33,467 | 13.8 (12.3 to 15.7) |

- Contamination 1, pump entries: the meter table mixes meter-log rows with glucose values typed into the pump. In the CGM-only arm those are the sensor's own number (36.9 % match the CGM exactly; real fingersticks 2.2 %; their "MARD" is 4.7 %). They made up 45 % of the old "independent" pairs. `ACCURACY_V2.md` s3, `SUBGROUPS.md` s1.
- Contamination 2, calibration fingersticks: 155,636 meter pairs match a calibration value within 5 minutes. A fingerstick about to correct the sensor is not a fair test of it. `PREPROCESSING.md` s2, `METHODOLOGY.md` 2026-10-27.
- Arms now agree: 13.8 % (CGM+BGM) vs 13.1 % (CGM-only); per person -0.1 points (CI -0.9 to +0.7). The old +1.9-point arm gap was the typed values. Calibration pairs are close (14.1 %), so the midterm's "calibration pairs are much worse" story is dropped. `SUBGROUPS.md` s1, `ACCURACY_V2.md` s4.
- Midterm figure vs paper figure: midterm Fig. 1 showed MARD 41.8 % below 54 and 18.7 % at 54-69, binned by the meter value, on the contaminated set. Paper figure 13 shows 19.1 % and 16.4 %, binned by the average of both devices, on verified pairs. Binning by one device inflates low-range numbers (below 54 the bias reads +29.8 % by meter, -22.5 % by CGM, -5.2 % by average; `ERROR_DRIVERS.md` s8). The direction (worst in the low range, sensor reads low) is unchanged.
- Pipeline: one shared module (`preprocess.py`) builds a cached, versioned table set; the old scripts reproduce their numbers to the last digit (`PREPROCESSING.md` s6). The verified-pair flag (`is_verified_fingerstick`, `verified_pairs()`) is now built into the module; the four v2 scripts were switched to it and re-run, and every number and figure came out identical (`PREPROCESSING.md` s3b, s6).

## 4. Plan promises checklist (plan summary section 3)

| Plan promise | Status | How / why, and where the result lives |
|---|---|---|
| 1. Drop pre-enrolment rows, sensor-limit values, implausible meter values | Done differently | Pre-enrolment rows excluded (1,102,160). Clipped values (39 / 401) KEPT and flagged, not dropped: MARD 13.6 % without them vs 13.8 %. Meter values outside 20-599 excluded. `PREPROCESSING.md` s2-3; `ACCURACY_V2.md` s4 |
| 2. Pair meter to nearest CGM within 5 min; calibrations separately; Shanghai pairs | Done | Plus two new rules: reference must be a meter-log row and not a calibration. `PREPROCESSING.md` s2; `ACCURACY_V2.md` s2 |
| 3. CGM+BGM arm primary (77), CGM-only as sensitivity (149) | Done differently | Both computed (Sets A and C). Paper leads with Set B (226 people) because A and B agree and B has tighter CIs; A is the promised check. `ACCURACY_V2.md` s4; `METHODOLOGY.md` 2026-10-30 |
| 4. Error = CGM minus reference | Done | `ACCURACY_V2.md` |
| 5. Lag offsets 0 / 5 / 10 / 15 min | Done | Extended to -5 and 20 min plus a 1-min interpolated scan. `ERROR_DRIVERS.md` s3 |
| 6. Signed error, MARD, % within accuracy limits | Done | 15/15, 20/20, 40/40, median ARD, iCGM-style table. `ACCURACY_V2.md` s4, s6 |
| 7. Ranges <54, 54-69, 70-180, 181-250, >250 | Done | `ACCURACY_V2.md` s5 |
| 8. Compare by age, sex, diabetes type, HbA1c, BMI, duration, arm, wear day, rate of change | Done differently | All done with participant as unit and BH. Diabetes type only in Shanghai (REPLACE-BG is all type 1): T1DM 18.4 % vs T2DM 12.9 %, 10 T1DM patients. `SUBGROUPS.md`; `ERROR_DRIVERS.md` s4-5; `ACCURACY_V2.md` s11 |
| 9. Parkes error grid | Done | Set A zones 83.7 / 14.6 / 1.4 / 0.3 / 0.0 %. Clarke grid moved to appendix. `ACCURACY_V2.md` s4 |
| 10. Compare with published results and FDA iCGM criteria | Done | `ACCURACY_V2.md` s6, s10 |
| 11. Low-glucose bias binned by the average | Done | Plus the three-axis table. `ERROR_DRIVERS.md` s8 |
| 12. Bias simulation 10 / 20 / 30 %, rules 70 and 200, per person-day; sensitivity: smaller bias, noise, dosing records | Done differently | Version 2 counts decisions, not readings: real bolus-calculator records, bias -40 to +40 % in 2 % steps, plus noise, drift, dropouts, lag. 180 is the headline high line (the question's number); 200 reported as a check. `SIMULATION_V2.md` |
| 12b. Judge the simulation against iCGM criteria | Not done | iCGM thresholds are agreement percentages; the simulation outputs decision counts. The iCGM comparison is done on real pairs instead (figure 14). |
| 13. MAUDE: brand names, duplicates, 8 families, by maker / year / outcome / demographics, Libre 3 monthly | Done | `fda-maude/results/report/report_results.md`. Brand spellings grouped by keyword; 65 double-coded reports removed |
| 13b. MAUDE narrative review (plan p.6 "remaining work") | Done | Full model run 2026-10-30 (section 6.1). Brand comparison and a pattern-only pass over all 3.38 million reports 2026-11-06 (findings 11, 12; section 6.2). Teammate check of 100 gold-set reports done 2026-11-08, no issues. `fda-maude/METHODOLOGY.md` 2026-10-28 |
| 14. Participant-level bootstrap CIs, mixed-effects model, medians and IQR, pair types separate, with and without lag, ISO 15197 meter sensitivity, counts with every estimate | Done | CIs everywhere; one mixed model (`ERROR_DRIVERS.md` s7); ISO sensitivity (`ACCURACY_V2.md` s9) |
| 15. Python scripts explore_raw_data.py, bias_simulation.py, maude_pull.py, report_results.py | Done differently | New scripts: preprocess.py, accuracy_v2.py, error_drivers.py, subgroups.py, simulation_v2.py; maude_pull.py is now maude_robot.py. Old scripts still run and reproduce. `PREPROCESSING.md` s6 |
| 16. Primary outcomes: signed error, MARD, misclassification by range, changes under simulated bias | Done | `ACCURACY_V2.md` s5, s7; `SIMULATION_V2.md` s5 |

Tally: Done 11, Done differently 5, Not done 1 (12b). Also open from the plan's gap list: harm counts for Class I recalls other than Libre 3 are not typed in (`report_results.md` g).

## 5. Plan claims checklist (plan summary section 5)

| Claim in the plan | Verdict | New number and file |
|---|---|---|
| CGM errors can lead to inappropriate treatment decisions | Supported | -20 % bias skips 7.2 % of corrections; the real G4 already changes 4.2 % of corrections by more than 1 unit. `SIMULATION_V2.md` s5, s7 |
| Nov 2025 recall: about 3 million sensors, 860 injuries, 7 deaths | Supported | 2,990,939 units; 860 injuries and 7 deaths as of 2026-01-07. `report_results.md` g |
| Review of 22 studies: MARD 9.4 %, worse in hypoglycaemia | Supported in direction | Ours 13.3 % (home meter reference; home studies run 2 to 4 points higher). MARD 19.1 % below 54 vs 10.2 % above 250. `ACCURACY_V2.md` s5, s10 |
| MARD does not capture direction or outcomes | Supported | We add signed bias, misclassification rates and decision counts |
| Since the recall: 71 deaths, 6,714 injuries, 2,638 "Low Readings" | Supported exactly | 6,785 serious Libre 3 reports since 2025-11-24: 71 deaths, 6,714 injuries; 2,638 with "Low Readings". `report_results.md` f |
| Lag causes discrepancies during fast glucose change | Supported and sized | Lag 5 to 7 min; fast-falling bias +12.7 % becomes +0.7 % after correction. `ERROR_DRIVERS.md` s3-4 |
| Accuracy lowest in hypoglycaemia; risk rises as error grows | Supported | Sensitivity for lows 71.8 % at 70, 51.8 % at 54; LBGI 0.95 to 2.33 at -20 % bias. `ACCURACY_V2.md` s7; `SIMULATION_V2.md` s5 |
| Inaccuracies increased during hypoglycaemia (MARD 18.7 %, 41.8 %) | Changed | Direction holds; the numbers were inflated by binning by the meter value on contaminated pairs. By average on verified pairs: 16.4 % (54-69) and 19.1 % (<54). `ACCURACY_V2.md` s5a, s12 |
| Both datasets show negative bias above 70 mg/dL | Supported | G4: -1.3 % overall (CI -1.6 to -0.9), 1 to 2 % low above 180. Libre H: -7.4 % (CI -10.7 to -4.5). `ACCURACY_V2.md` s4, s11 |
| Low-glucose bias varies by grouping method, so bin by the average | Supported and sized | Below 54: +29.8 % by meter, -22.5 % by CGM, -5.2 % by average. `ERROR_DRIVERS.md` s8 |
| Simulated negative bias mostly causes missed highs | Changed | Per day at -20 %: 1.19 missed high episodes vs 0.86 false low alerts, plus 7.2 % skipped doses. Version 1 counted readings and was 15 to 30 times too large. `SIMULATION_V2.md` s5, s8 |
| Findings do not establish actual treatment decisions | Changed in part | Version 2 uses 159,878 real dosing decisions with the patient's own settings; outcomes are still simulated. `SIMULATION_V2.md` s3 |
| Primary uncertainty: does low bias persist after lag and calibration? | Answered: yes | -6.5 % below 54 (CI -7.9 to -5.1), -4.1 % at 54-69 (CI -4.9 to -3.2), lag-corrected, non-calibration pairs. `ERROR_DRIVERS.md` s1 |
| Second uncertainty: simulated flips vs real decisions, via insulin-dosing records | Done | Dose rule reproduces the pump's own correction within 0.15 units in 90 % of records. `SIMULATION_V2.md` s3 |
| CGM-only arm fingersticks are protocol-prompted, so CGM+BGM arm must be primary | Changed | With typed values removed the arms agree: 13.8 vs 13.1 %; per person -0.1 points (CI -0.9 to +0.7). Set A kept as the promised check. `SUBGROUPS.md` s1 |
| Fingersticks selected when the sensor looked wrong; meter error adds to MARD | Supported and sized | Meter error at the ISO limit adds at most 1.9 points and pushes the low bias toward zero. `ACCURACY_V2.md` s9 |
| MAUDE: wrong readings most common; reporting rose around recalls | Supported | 33.1 % of serious reports; peaks around Jul 2024 and Nov 2025 by both dates. `report_results.md` d, f |
| Findings cannot be attributed to the recalled Libre 3; MAUDE counts are signals, not rates | Unchanged | Still true. The text extraction will add reported error sizes, not rates (section 6) |

## 6. Phase 1 to Phase 2 bridge

What the structured MAUDE results say (`report_results.md` d, e; no AI involved):
- 3,382,071 CGM reports; 123,607 death or injury reports (623 deaths, 122,984 injuries).
- In serious reports the top device problem is wrong readings: 33.1 % (Dexcom 44.4 %, Abbott 31.0 %). Then no readings / sensor stopped 22.4 % and app or display 23.1 %.
- Top patient problems in serious reports: hypoglycaemia 40.8 %, loss of consciousness 27.8 %, hyperglycaemia 19.0 %.
- Libre 3 / 3 Plus: 18,292 serious reports all time; 6,785 since the Nov 24 2025 recall, 2,638 of them coded "Low Readings".

What the text extraction will add (`fda-maude/METHODOLOGY.md` 2026-10-26 and 2026-10-28):
- The size of the error in each report: the sensor value and the meter value stated in the text. The pattern layer reads both values from 96 % of Abbott malfunction reports in the 287-report sample; across all 123,607 serious reports it finds both in 7 % (Abbott), 28 % (Dexcom) and 5 % (Medtronic).
- The wear day of the failure (94 % of Abbott sample texts) and the Parkes zone the maker assigned (98 % of Abbott sample texts; about a quarter of Dexcom).
- Fault type (reads low, reads high, stuck, signal loss, early end), whether a fingerstick check was done, what the user did, and outcome severity.
- Tooling: regex for the templates, then a local open model (qwen2.5:7b-instruct) filling a fixed form, 250 to 300 reports per minute, about 9 hours for the serious tier. Any number not present word-for-word in the text is dropped (2 to 6 % of answers in the pilot). Gold set of 287 hand-labelled reports: reads low is the top fault (26 %), then signal loss (23 %).

How it joins `analysis/simulation_v2_lookup.csv` (41 rows, `bias_pct` from -40 to +40 in 2 % steps; each outcome has `_median`, `_q1`, `_q3`, `_mean`, `_n` columns, for example `skipped_pct`, `changed_1_pct`, `low70_false_per_day`, `low70_missed_pct`, `high180_missed_pct`, `tir_pct`, `lbgi`):
1. For each report with both values, error % = (sensor minus meter) / meter x 100.
2. Round to the nearest 2 %, clip to -40 to +40. Count reports per bin: that is the weight.
3. Weighted average of each lookup column = "expected decision impact of the errors people actually reported". Do it per maker and per fault type (reads low vs reads high).
4. Compare the wear day of reported failures with the trial's day-1 pattern (figure 20).
5. Compare maker-stated Parkes zones with the trial's zone shares (83.7 / 14.6 / 1.4 / 0.3 / 0.0 %, Set A).
Caveat to state: reported errors are the harmful tail, not typical sensors. The weighted result describes reported failures.

### 6.1 Text-extraction results (full run 2026-10-30; `fda-maude/results/text/TEXT_RESULTS.md`)
- Run: 124,599 report texts (118,462 serious + 6,137 sampled malfunctions) in 9.55 h, 0 errors, 3.5 % guard drops. 18,445 reports state both the sensor and the meter value (18,118 serious).
- Reported error sizes (sensor minus meter, median and IQR): Abbott serious -65 mg/dL (-278 to +95), -47 % (-80 to +144), 58 % read low; Dexcom serious +27 mg/dL (-207 to +77), +42 % (-63 to +169), 55 % read high. Reads-low pairs: Abbott median -77 % (sensor 60 vs meter 317 mg/dL), Dexcom -68 % (86 vs 414). Reads-high pairs hide a true low under 70 mg/dL in 62 to 70 % of cases. `TEXT_RESULTS.md` s4.
- Beyond the 20 % tipping point: 97 to 98 % of reported reads-low errors (96 to 97 % of all pairs are more than 20 % off). 78 to 94 % are beyond -40 %, the edge of the original lookup table, so the table was extended to -90 % (see the decision-impact bullet below). `TEXT_RESULTS.md` s8.
- Wear day: Abbott complaints name day 1 in 13.4 % (flat expectation 7.1 %; malfunction sample 34.5 %), the day the trial sensor was least accurate (finding 4); Dexcom shows no day-1 excess (7.1 % vs 10 %). Complaint timing is not a failure rate. `TEXT_RESULTS.md` s6.
- Maker-stated Parkes zones agree with the zone computed from the pair in 87 % (within one zone 97 %); stated zones are 95 to 100 % in C to E for Abbott, against 1.7 % C to E in the trial (Set A). `TEXT_RESULTS.md` s5.
- Weighted decision impact (median trial person; lookup extended to -90 % on 2026-10-30, `analysis/simulation_v2_lookup_extended.csv`): Abbott serious reads-low errors skip 49 % of correction doses, change 38 % of doses by more than 1 U, hide 96 % of high episodes, show "below 70" for 80 % of the day (true trace 3.5 %) and lift LBGI from 0.95 to 27; Dexcom serious 45 %, 37 %, 93 %, 69 %, LBGI 23; weighted malfunction sample 51 %, 39 %, 98 %, 76 %, 23; Libre 3 post-recall 49 %, 38 %, 96 %, 77 %, 25. False low alerts fall to 0.85 to 1.2 per day because the sensor sits below 70 nearly all day (one endless low episode), so time below 70 is the fairer measure there. Comparison, the old join clipped at -40 % (a floor): Abbott 31 %, 38 %, 1.75 false low alerts per day, 87 %, LBGI 5.9; Dexcom 30 %, 37 %, 1.69, 84 %; sample 32 %, 38 %, 1.77, 88 %; Libre 3 post-recall 31 %, 38 %, 1.74, 86 %. A constant -20 % bias gives 7.2 %, 16.7 %, 0.86, 51 %. The dose rule saturates at about -70 % (every needed correction skipped), so the new numbers are the simulation's full answer, not floors; 8 to 10 % of serious Abbott and Dexcom reads-low pairs are still beyond -90 %. Reported errors are the worst cases, not an average sensor. `TEXT_RESULTS.md` s8.
- Gold-set agreement (kappa, v3, 287 reports): fault type 0.77 (Abbott 0.88, Dexcom 0.71, Medtronic 0.63); outcome 0.75 (0.71 / 0.87 / 0.62); user action 0.77 (0.84 / 0.81 / 0.58); numbers 96 % exact. Teammate check of 100 gold-set reports done 2026-11-08, no issues. `fda-maude/results/text/VALIDATION.md`.

### 6.2 Two more Phase 1 text memos (2026-11-06)
- `fda-maude/results/text/BRAND_COMPARISON.md`: wrong-reading complaints by brand, patient age and sex. Finding 11. Tables `tables/g_*.csv`; figures t7 to t10.
- `fda-maude/results/text/REGEX_V2_FULL_CORPUS.md`: patterns alone over all 3,382,071 reports; malfunction-only vs serious pairs; the harm gradient. Finding 12. Tables `tables/h_*.csv`; figures t11 to t13. The per-report file `clean/regex_v2_full.csv.gz` is not in git.
- Both carry the same caveat as 6.1: MAUDE counts are reports, not failure rates; Medtronic rows carry a caution label.
- Update to join step 4 above: the trial's day-1 effect is the sensor settling in (finding 9), so the Abbott day-1 complaint excess is expected even without a defect.
- `fda-maude/results/FIELD_INVENTORY.md` (done 2026-11-08): which MAUDE fields are filled and what the texts say beyond the form. Unused fields worth using: maker evaluation result and device returned ("no defect found" in 81 % of returned devices; Abbott 98 %, Dexcom 75 %), country per report (filled 94.9 %). Age and sex fill is a maker habit (Dexcom 93 %, Abbott 7 %); filled MAUDE ages run older than the trial (28 % are 65+ vs 8 %) and include children (17 % vs 0 %). Text themes at scale over serious reports: device not returned 66 %, carer or family in the story 32 % (deaths 56 %), EMS or hospital 38 %, skin reaction 18 %, alarm failed 6 %. Verdict on reading the 3.26 M malfunction texts with the model: not worth it (46 % are 241 identical templates; regex v2 already read the numbers); do two 100-report human reads of the extreme error bands instead.

## 7. Null results and caveats the paper must state

- Narrow cohorts. REPLACE-BG: adults, 94 % White, 77 % with a degree, well-controlled pump users, no recent severe hypoglycaemia. Shanghai: older Chinese inpatients. `SUBGROUPS.md` s9.
- Device age. Dexcom G4 (2012-2015) and Libre H (2021); the recalled sensor is the Libre 3. Results transfer in kind, not in number. G4 software version is not stated in the data (guess: Software 505; to confirm from the trial paper). `ACCURACY_V2.md` s13; `PREPROCESSING.md` s5.
- Home-meter reference, not lab blood. Meter error at the ISO 15197 limit would add up to 1.9 MARD points; the Contour Next is far better than the limit (guess: under 1 point). `ACCURACY_V2.md` s9.
- Fingersticks are not random. People test when they feel low or doubt the sensor. Detection and misclassification rates describe tested moments, not all moments. `ACCURACY_V2.md` s7, s13.
- Sensor sessions are inferred from gaps (no sensor-start marker); wear-day results rest on the confirmed-session filter. 1,973 receiver clock changes are not corrected. `PREPROCESSING.md` s4, s7.
- Simulated decisions assume the patient types the sensor value and follows the calculator (68 % of CGM-only-arm typed values were within 5 % of the CGM; 45 % in the other arm). No meal or insulin-action model; no follow-through to a changed glucose. `SIMULATION_V2.md` s11.
- Nulls: sex, study arm, HbA1c, BMI, diabetes duration, 26 weeks of use, prior CGM use, pump brand, education, income, insurance, comorbidities: no difference after correction. The one exploratory hit (more listed conditions) vanished after adjusting for age and CV. `SUBGROUPS.md` s3, s5, s8. Re-tested hard with 680 pre-registered tests, 18 trait pairs, clinic site and flexible models: still null (finding 10). The one modest exception is the sex gap in low-range bias (about 2.5 mg/dL; absent in one arm; no dose change). Do not write "women's sensors are worse": low-range MARD is the same by sex.
- Night is not worse per person (median difference -0.2 points; 47 % of people worse at night). Only large errors (over 40 %) are twice as common at night, in both directions. Do not write "night is worse". `ERROR_DRIVERS.md` s6.
- Bland-Altman limits are wide: -67 to +57 mg/dL (Set A). A single reading can sit 50 to 65 mg/dL from the meter and be "normal" for this sensor; almost all of that spread is within person, not between people. `ACCURACY_V2.md` s8.
- Shanghai is a comparator only: 98 patients, 4,012 pairs, MARD 13.9 % (CI 12.2 to 16.1), reads 7.4 % low; low bins not estimable (6 and 44 pairs); 7.5 min timing slack; lag cannot be measured at 15-min readings. `ACCURACY_V2.md` s11; `ERROR_DRIVERS.md` s9.

## 8. Figures for the paper

| Figure | Caption in plain words | Section | Fix needed |
|---|---|---|---|
| 15_misclassification_70_180 | Share of fingerstick-confirmed lows, highs and in-range values that the sensor put on the wrong side of the line (Set A, 33,467 pairs, 77 people; whiskers = 95 % CI). | Results: main finding | Done 2026-10-30: bar added (37.9 %, CI 33.5 to 42.2) |
| 13_accuracy_by_range_setA | Pairs, bias and MARD by glucose range (average of sensor and meter), Set A; whiskers = 95 % CI. | Results: accuracy by range | Done 2026-10-30: subtitle says Set B matches within 1 point (largest gap 0.7 points) |
| 18_low_range_bias_lag_corrected | The sensor reads low below 70 mg/dL, and more so after lag correction (bars = mean bias, lines = 95 % CI, 167,847 verified pairs). | Results: primary uncertainty | None |
| 20_wear_day_and_time_of_day | Sensor error by wear day, by hours on day 1, and night vs day. Day 1 is worst. | Results: error drivers | Done 2026-10-30: title says "verified"; right panel titled "per person: no difference (median -0.2 points)" |
| 25_decision_impact_vs_bias | What a constant sensor bias does to real insulin-dose decisions and low alerts (line = median person, band = IQR). Doses start to change near 12 % low bias. | Results: simulation | Optional: vertical marker at -12 % (not done; figure t6 in `fda-maude/results/text/figures/` has the markers) |
| 26_fault_families | Six fault types at a matched size: bias hurts doses most; noise is the only fault that hides low episodes. | Results or Discussion | None |
| 33_wear_day_selection_vs_settling | Day-1 error split into sensors pulled early (left) and the same sensors settling in over their 7 days (right). Settling is 92 % of the day-1 excess. | Results: error drivers (pair with figure 20) | Caption must say sessions are inferred from gaps, not from a sensor ID |
| 34_wear_day_calibration | Error by time since the last calibration, day 1 vs day 7. Day 1 is worse at every point, so calibration timing is not the cause. | Appendix | None |
| 35_sex_low_range_bias | Low-range bias by sex in every split (glucose band, wear day, time of day, trend, arm). Men minus women about +4 points everywhere except the CGM+BGM arm. | Appendix, or Discussion if the sex sentence goes in | Caption must say: modest, about 2.5 mg/dL, absent in one arm, no dose change |
| 29_cohort_demographics | Who is in REPLACE-BG and Shanghai (age, sex, race, BMI, HbA1c and more). | Methods or appendix | None |
| 30_demographic_interactions | Pairs of traits together: every 2x2 group median sits between 11.3 and 13.0 % MARD. | Appendix (null result) | None |
| 31_site_effects | MARD by clinic site: 3.5 % of the spread, and it tracks each site's glucose pattern. | Appendix (null result) | None |
| 32_demographics_vs_glucose_pattern | Flexible models: demographics predict nothing (R-squared below zero); glucose pattern predicts a little. | Appendix (null result) or Discussion | None |
| t7_brand_error_sizes | Reported error size and direction by brand: Abbott and Dexcom equally far off; Abbott reads low more often. | Results: Phase 1 | Caption must say: complaint reports, not failure rates; Medtronic caution |
| t8_brand_meter_bands | Where the true glucose was, by brand: Dexcom hidden lows, Abbott false lows at high true glucose. | Results: Phase 1 (the brand failure modes) | Same caveat as t7 |
| t9_brand_by_year | Share reading low by brand and year, with the recall windows. The brands converge in 2026. | Appendix or Discussion | Post-recall window still filling; numbers will change |
| t10_demographics | Age and sex in MAUDE complaints: children read low and end in hypoglycaemia more often; sex makes no difference. | Appendix | Fields filled mostly in Dexcom reports (age 49 %, sex 41 %) |
| t11_regex_v2_recall | How many of the model's pairs the patterns find, by brand (73 to 89 %). | Methods appendix | None |
| t12_malfunction_vs_serious_errors | Error distribution in malfunction-only vs death/injury pairs: one fault vs two. | Results: Phase 1 | Caption must say: patterns only, precision estimated, not measured on a gold set |
| t13_harm_gradient | Share of pairs filed as death/injury by error band, both brands: U-shaped. | Results or Discussion | Caption must say: partly coding style; the small-error peak is a reporting artefact |

Appendix: 14 (iCGM benchmark), 16 (Bland-Altman), 17 (lag scan; title already says "verified"), 19 (rate of change), 21-24 (subgroups; figure 22 now says in its subtitle that no star is shown because nothing passed), 27 (dose-change distribution), 28 (TIR and LBGI vs bias; promote to main text if space allows, it makes the "hides itself" point), 29-32 (deep demographics, all null), 34 (calibration check), 35 (sex gap), t9-t11 (brand by year, MAUDE demographics, pattern recall).

## 9. Suggested paper sentences

1. On 168,990 verified fingerstick pairs from 226 adults, the Dexcom G4 had a MARD of 13.3 % (95 % CI 12.7 to 13.9). `ACCURACY_V2.md` s4.
2. Error was largest in the low range: MARD 19.1 % below 54 mg/dL (CI 18.0 to 20.4) against 10.2 % above 250 (CI 9.5 to 11.4). `ACCURACY_V2.md` s5a.
3. The sensor did not show 28.2 % of meter-confirmed lows as low (CI 24.4 to 32.8), and 38 % of the lows it showed were not confirmed (PPV 62.1 %, CI 57.8 to 66.5). `ACCURACY_V2.md` s7.
4. Overall, 15.0 % of pairs (CI 13.6 to 16.6) put the reading on the wrong side of the 70 or 180 mg/dL line. `ACCURACY_V2.md` s7.
5. After correcting for a 5-minute sensor lag, the sensor still read 6.5 % low below 54 mg/dL (CI 5.1 to 7.9) and 4.1 % low at 54-69 (CI 3.2 to 4.9). `ERROR_DRIVERS.md` s1.
6. The sensor trailed blood glucose by 5 to 7 minutes (per-person median 7, IQR 5 to 9); the apparent error during fast glucose change was almost entirely this lag. `ERROR_DRIVERS.md` s3-4.
7. Day 1 of wear had the highest error (MARD 15.2 %, CI 14.6 to 15.9) and day 7 the lowest (11.8 %, CI 11.2 to 12.5); 86 % of participants were worse on day 1. `ERROR_DRIVERS.md` s5.
8. No participant characteristic predicted sensor error after correction for multiple testing; glucose variability and time below 70 mg/dL did (Spearman rho 0.33, CI 0.20 to 0.44). `SUBGROUPS.md` s3-4.
9. A sensor reading 20 % low skipped 7.2 % of correction doses (CI 6.6 to 8.2), changed 16.7 % of doses by more than one unit (CI 11.1 to 22.9) and added 0.86 false low alerts per person per day (CI 0.81 to 0.91); a 10 % low reading changed almost no dose. `SIMULATION_V2.md` s5.
10. In serious FDA reports about CGMs, wrong readings were the most common device problem (33.1 %) and hypoglycaemia the most common patient problem (40.8 %). `report_results.md` d, e.
11. Wear day 1 is the sensor settling in, not a subset of bad sensors: the same sensor read about 2 points worse on its first day than on its second and 3 points worse than on day 7 (settling 92 % of the day-1 excess, CI 85 to 100); sensors pulled on day 1 were about 4 points worse but were 7 % of sessions. `WEAR_DAY.md` s9.
12. In the low range a new sensor read about 10 % low on its first day; this faded within the day and was gone by day 2, and it doubled false low readings on day 1, so a day-1 cluster of complaints is expected even when no sensor is defective. `WEAR_DAY.md` s9.
13. In the low range the sensor read about 2.5 mg/dL lower in women than in men (bias -6.4 vs -2.2 %, difference +4.2 points, CI +2.0 to +6.3); the gap survived matching on glucose level and trend and adjustment for body size, was absent in one small study arm, has no known mechanism, and is too small to change a dose. `DEMOGRAPHICS_FOLLOWUP.md` s11.
14. In serious FDA wrong-reading reports, Abbott and Dexcom errors were equally large (median 86 vs 87 % of the meter value) but failed at different glucose levels: the true glucose was under 70 mg/dL in 46 % of Dexcom pairs and 28 % of Abbott pairs, while the sensor showed a false low in 36 % of Abbott pairs and 17 % of Dexcom pairs; these are complaint shares, not failure rates. `BRAND_COMPARISON.md` s4, s9.
15. Across all 3.38 million CGM reports, text patterns found 191,112 sensor-meter pairs in reports filed as malfunction only; these showed one fault, a sensor reading about a third of the true value while the true glucose was normal or high (median error -66 %, 75 % read low, true glucose under 70 in 5 %). `REGEX_V2_FULL_CORPUS.md` s6.

## 10. Open items and suggestions (added 2026-11-08)

- Done 2026-11-20 (`SIMULATION_THREE_FAULTS.md`; episodes of 2, 6 and 12 hours; 15 g sugar when the sensor shows under 70). Decided 2026-11-09: simulate three faults instead of one constant bias, each fixed to a true-glucose band. (1) False low at true glucose 70 to 250 mg/dL (the malfunction pile; 60 to 80 % low). (2) Hidden low: the sensor reads normal or high while the true value is under 54. (3) Floor-pinned sensor (LOW or under 40) while the true value is over 250. The constant-bias lookup already covers fault 1 in size. `REGEX_V2_FULL_CORPUS.md` s9.
- Human read to settle the harm gradient: about 100 malfunction-only and 100 injury reports from the two extreme error bands (-100 to -90 % and over 200 %), to see whether the stories differ in what happened to the person or only in the FDA code. Also the same gradient inside one brand and year (Abbott 2025-2026), and by reporter type. `REGEX_V2_FULL_CORPUS.md` s7.
- The sex gap (finding 10) stays one sentence until an outside dataset checks it: laboratory reference, a newer sensor, both sexes well represented in the low range, haematocrit and sensor site recorded. `DEMOGRAPHICS_FOLLOWUP.md` s11.
- Teammate check of 100 gold-set reports: done 2026-11-08, no issues (`fda-maude/gold/GOLD_SET.md`).
- Not decided: the inventory memo's ranked suggestions (use the maker-evaluation and device-returned fields; add two dropped raw fields with a 10-minute clean re-run).
