# Follow-up of the sex lead: in the low range the Dexcom G4 reads lower in women than in men (2026-11-06)

Script: `analysis/demographics_followup.py`. Numbers: `analysis/demographics_followup_stats.json`. Figure 35 in `analysis/figures/`. This follows `DEMOGRAPHICS_DEEP.md` section 12a (2026-11-06), where this was the one result out of 680 tests that passed correction.

Terms. Bias = mean of (CGM minus fingerstick) as a percent of the fingerstick; negative = the sensor reads low. Low range = pairs whose average of CGM and fingerstick is below 70 mg/dL. Per person = each person's mean bias on their own low pairs (20 or more pairs needed), then women and men are compared as two groups of people (Mann-Whitney test; the difference in medians gets a bootstrap CI). Pooled = all pairs thrown together, with a bootstrap that resamples people. CI = 95 % confidence interval. p = the chance of a result this big if there were no real difference. BH p = p corrected for the number of tests (Benjamini-Hochberg). ROC = rate of change of the CGM trace at the fingerstick time, mg/dL per minute. Lag correction = compare the fingerstick with the CGM reading taken 5 min later. Matching = compare women with men only inside pairs of the same glucose level and trend, then average those comparisons. Mixed model = a regression that knows which pairs belong to the same person. TDD = total daily insulin dose from the pump log (basal + bolus). Haematocrit = the share of blood that is red cells; it changes how some glucose sensors and meters read. Anchor = the original result, shown for reference and not counted again. n.t. = not testable.

Direction convention: every difference is MEN MINUS WOMEN. Positive = men's sensors read higher (less low) than women's.

## Summary in 6 lines
- Not chance. The gap (men minus women +4.2 points, CI +2.0 to +6.3) is in every low-range split: both glucose bands, wear days 2-7, day and night, flat and falling glucose, lag-corrected pairs, calibration pairs, and whether "low" is defined by the fingerstick or by the sensor. It is zero in the mid range (70-180) and reversed above 180 (-0.9). It fades out by 100 mg/dL.
- The sensor, not the person. Women and men go low equally often (3.4 vs 3.6 % of CGM time), equally deep by fingerstick (62.3 vs 61.5 mg/dL in low pairs), at the same hours and the same speed. Matching pairs on glucose level and trend leaves the gap at +3.7 (CI +1.9 to +5.6). The only "profile" differences are the CGM-measured ones (deeper CGM nadirs, more readings at the 39 floor in women), which is what a lower-reading sensor would produce.
- Nothing in the data explains it. Adjusting for weight, BMI, height, HbA1c, age and insulin dose per kg leaves the sex term at +4.0 (CI +0.9 to +7.0). Within each sex, none of these correlate with the bias. Neither dataset has haematocrit or any blood count.
- One real caveat: the gap is absent in the CGM+BGM arm after randomisation (+0.6, CI -2.5 to +3.5; 24 women, 12 men), and the sex x arm interaction has p 0.02. But the gap is present in the blinded run-in, where people could not see the sensor (pooled +5.8, CI +2.0 to +9.9), so it is not made by people choosing when to fingerstick.
- Outside checks are weak. Shanghai (Abbott flash sensor) has 50 low pairs: gap -18 (CI -39 to +10), uninformative. MAUDE Dexcom complaints point the same way but by a few points: women's reports are "reads low" in 49 % vs 45 %, hidden lows 36 % vs 38 %. No published paper reports a sex difference in CGM low-range bias; the one study that checked (Libre, children) found none.
- It is about 2.5 mg/dL at 60 mg/dL. It changes no insulin dose and skips no correction. It moves the 70 mg/dL alert line: near 70, women's sensors show 5 points more false lows (36 vs 31 %) and miss 5 points fewer true lows (37 vs 42 %). Verdict: a real, small, unexplained sensor difference. One sentence in the paper, filed under "needs a dataset with a lab reference and a newer sensor".

## 1. What was asked
The deep check found this gap and called it a lead, not a finding, because it was small, had no mechanism and was weaker in the randomised CGM+BGM arm. The project lead asked to chase it: decide whether it is real, what could explain it, and whether it matters. Rule for this memo: every test was listed before any test ran (section 2, stored in the JSON under `preregistration`), and every result is reported, null or not.

## 2. Pre-registered test list
Three BH families, because the three datasets answer different questions.

| Family | Block | Tests | What they ask |
|---|---|---|---|
| REPLACE-BG (66 tests) | A: splits | 23 splits of the low-range bias by sex + 1 sex x arm interaction | Where is the gap? |
| | B: profile and matching | 16 low-glucose profile measures by sex; 4 matched / adjusted gaps | Is it the person's glucose pattern? |
| | C: body and physiology | 9 adjusted sex terms; 12 within-sex correlations | Does body size, HbA1c, age or insulin dose explain it? |
| | F: decisions | 2 threshold-crossing shares near 70 mg/dL | Does it change what the person sees? |
| Shanghai (3 tests) | D | pooled bias by sex: average below 70, fingerstick below 70, 70-180 | Same gap with a different sensor? |
| MAUDE (5 tests) | E | reads-low share, reads-low depth, hidden low, meter below 70, false low | Same direction in complaints? |

Rules fixed in advance:
- Per-person test = 20 or more pairs per person, 10 or more people per sex. If a split has fewer qualifying people, the registered p comes from a mixed model on the pooled pairs and the estimate shown is the pooled gap with a participant-bootstrap CI. Both versions are reported for every split.
- Not counted: the anchor row, the mg/dL version of each split, the missed-low and false-low rates (already in the deep check's family), descriptive rows, and the post-hoc block (section 9).
- Seed 600, 2,000 bootstrap resamples, the same helpers as `demographics_deep.py`.

## 3. Block A: where is the gap?
Per-person low-range bias (%), medians, with the number of people and pairs. The anchor row reproduces the deep check exactly.

| Split | Women: bias (people; pairs) | Men: bias (people; pairs) | Men minus women (CI) | p | BH p |
|---|---|---|---|---|---|
| All verified pairs, average below 70 (anchor) | -6.4 (76; 5,198) | -2.2 (74; 4,824) | +4.2 (+2.0 to +6.3) | <0.001 | anchor |
| Average below 54 | -5.8 (18; 1,189) | -0.5 (13; 967) | +5.4 (-4.4 to +12.0) | 0.06 | 0.13 |
| Average 54-69 | -5.6 (70; 4,009) | -1.4 (65; 3,857) | +4.2 (+2.7 to +6.1) | <0.001 | 0.001 |
| Wear day 1 (confirmed sessions) | -11.1 (10; 1,069) | -6.8 (15; 966) | +4.3 (-8.1 to +11.1) | 0.56 | 0.69 |
| Wear days 2-7 | -3.6 (66; 3,524) | -0.2 (58; 3,396) | +3.4 (+1.4 to +5.4) | <0.001 | 0.001 |
| Night 00-06 | -5.1 (7; 747) | +0.7 (5; 607) | n.t. per person; pooled +3.8 (+0.2 to +7.0) | 0.06 | 0.13 |
| Daytime 06-24 | -6.2 (73; 4,451) | -1.6 (69; 4,217) | +4.6 (+2.4 to +6.1) | <0.001 | <0.001 |
| Glucose falling (ROC < -1) | +7.0 (9; 843) | +7.6 (6; 755) | n.t. per person; pooled +4.8 (+1.5 to +8.4) | 0.03 | 0.06 |
| Glucose flat (-1 to 1) | -7.5 (69; 3,756) | -3.2 (62; 3,576) | +4.3 (+1.6 to +6.6) | <0.001 | 0.001 |
| Glucose rising (> 1) | n.a. (0; 264) | n.a. (0; 266) | n.t. per person; pooled +1.6 (-3.2 to +6.6) | 0.41 | 0.56 |
| Lag-corrected (CGM 5 min later), average below 70 | -7.3 (79; 5,342) | -4.0 (75; 4,984) | +3.3 (+1.8 to +5.3) | <0.001 | <0.001 |
| Contour Next meter pairs | -6.4 (76; 5,198) | -2.2 (74; 4,820) | +4.2 (+2.0 to +6.3) | <0.001 | <0.001 |
| Precision Xtra meter pairs | 0 pairs | 4 pairs | n.t. | n.a. | n.a. |
| CGM-only arm, all days | -7.1 (45; 3,083) | -1.0 (56; 3,732) | +6.2 (+3.2 to +8.6) | <0.001 | <0.001 |
| CGM+BGM arm, all days | -5.4 (31; 2,115) | -3.5 (18; 1,092) | +1.8 (-1.5 to +3.4) | 0.27 | 0.40 |
| Run-in phase, both arms | -4.4 (24; 1,209) | -1.1 (19; 1,028) | +3.3 (-1.3 to +6.8) | 0.09 | 0.17 |
| Randomised phase, CGM-only arm | -7.5 (42; 2,357) | -1.4 (49; 3,005) | +6.1 (+3.3 to +8.8) | <0.001 | <0.001 |
| Randomised phase, CGM+BGM arm (the check set) | -4.8 (24; 1,632) | -4.3 (12; 791) | +0.6 (-2.5 to +3.5) | 0.65 | 0.75 |
| Calibration pairs below 70 (other pair source) | -11.9 (68; 3,768) | -7.6 (67; 3,934) | +4.3 (+1.8 to +9.8) | <0.001 | <0.001 |
| Low by fingerstick (fingerstick below 70) | +6.9 (75; 5,080) | +12.4 (81; 5,024) | +5.5 (+2.0 to +9.2) | 0.002 | 0.005 |
| Low by sensor (CGM below 70) | -15.0 (90; 6,234) | -12.6 (84; 5,490) | +2.4 (+0.4 to +4.7) | 0.02 | 0.04 |
| Mid range 70-180 | -1.8 (112; 48,744) | -1.8 (114; 50,800) | 0.0 (-0.8 to +1.1) | 0.30 | 0.45 |
| High range above 180 | -0.9 (111; 33,081) | -1.8 (112; 26,343) | -0.9 (-1.9 to -0.3) | 0.002 | 0.006 |
| All verified pairs | -1.6 (112; 87,023) | -1.9 (114; 81,967) | -0.3 (-0.8 to +0.4) | 0.97 | 0.97 |

- In mg/dL (medians, women / men): all low pairs -5.2 / -2.4; below 54 -4.3 / -1.6; 54-69 -4.9 / -2.3; wear days 2-7 -3.3 / -1.2; lag-corrected -5.4 / -3.2; calibration pairs -9.6 / -6.3; mid range -4.6 / -4.7; high range -5.3 / -7.8.
- Pooled pairs tell the same story with tighter numbers (women / men bias): all low pairs -5.0 / -1.4 (gap +3.6, CI +1.8 to +5.5); wear day 1 -11.5 / -7.9 (+3.7, CI +0.5 to +6.4); night -6.1 / -2.3; run-in -5.4 / 0.0 (+5.3, CI +2.2 to +8.8); randomised CGM+BGM -3.1 / -3.5 (-0.4, CI -3.2 to +2.1).
- Pooled bias by glucose bin (women / men): 45-49 mg/dL -9.6 / -3.7; 50-54 -6.8 / -4.9; 55-59 -6.8 / -2.5; 60-64 -4.1 / -1.0; 65-69 -3.1 / +0.6; 70-99 -1.7 / -0.2; 100-139 -1.0 / -1.3; 140-180 -1.2 / -1.3; 181-250 -0.8 / -1.6; above 250 -0.6 / -1.8 (figure 35b). So it is not a small everywhere gap: it is 3-6 points in every bin below 70, 1.5 points at 70-99, and zero or reversed from 100 up.
- Which device defines "low" does not matter. Binned by the fingerstick, both sexes read high (regression to the mean, ERROR_DRIVERS.md section 8) but women less so (+5.5). Binned by the sensor, both read low, women more so (+2.4). The gap is not an artefact of binning by the average.
- Lag correction, wear day, time of day, trend, calibration pairs: the gap stays at +3.3 to +4.8 everywhere it can be measured. Wear day 1 and below 54 have wide CIs because few people have 20 such pairs; their pooled gaps (+3.7, +3.9) match the rest.
- Meter type cannot be tested: 168,781 of 168,990 verified pairs are Contour Next.
- Study arm is the odd one out. CGM-only arm +6.2; CGM+BGM arm +1.8; in the randomised phase +6.1 vs +0.6. Sex x arm interaction: all days -4.4 (CI -8.0 to -0.7), p 0.02, BH 0.05; randomised phase only -6.1 (CI -10.2 to -2.1), p 0.003 (not registered). The check set has 24 women and 12 men. Section 9 tests the most likely explanation.

## 4. Block B: sensor or person?

### 4a. Do women and men go low differently? No.
Per person, medians. CGM-trace measures use 49,327 low episodes (3 or more readings below 70 in a row, 226 people). Pair measures use each person's verified low pairs (shares only for the 150 people whose bias was compared).

| Measure | Women (n) | Men (n) | Men minus women (CI) | p | BH p |
|---|---|---|---|---|---|
| % of CGM time below 70 | 3.4 (112) | 3.6 (114) | +0.2 (-0.7 to +0.7) | 0.84 | 0.90 |
| CGM low episodes per day | 0.93 (112) | 0.98 (114) | +0.05 (-0.15 to +0.23) | 0.57 | 0.69 |
| Mean lowest CGM value of the episodes (mg/dL) | 54.9 (112) | 55.7 (114) | +0.8 (0.0 to +1.4) | 0.05 | 0.11 |
| Mean episode length (min) | 45.5 (112) | 45.3 (114) | -0.2 (-3.5 to +2.3) | 0.97 | 0.97 |
| % of episodes reaching below 54 (CGM) | 39.6 (112) | 35.9 (114) | -3.7 (-7.8 to +0.8) | 0.10 | 0.18 |
| % of episodes starting at night | 20.0 (112) | 18.2 (114) | -1.8 (-4.3 to +0.8) | 0.12 | 0.20 |
| CGM slope in the 15 min before the episode (mg/dL/min) | -1.01 (112) | -0.99 (114) | +0.02 (-0.03 to +0.08) | 0.33 | 0.46 |
| % of episodes entered fast (slope < -1) | 40.6 (112) | 39.4 (114) | -1.2 (-4.1 to +2.5) | 0.47 | 0.62 |
| Number of low pairs per person | 39 (112) | 29 (114) | -10 (-18.5 to +0.5) | 0.25 | 0.38 |
| Mean fingerstick of the low pairs (mg/dL) | 62.3 (76) | 61.5 (74) | -0.8 (-1.7 to +0.5) | 0.07 | 0.13 |
| % of low pairs with fingerstick below 54 | 17.4 (76) | 18.0 (74) | +0.6 (-3.6 to +5.0) | 0.51 | 0.66 |
| % of low pairs at night | 13.5 (76) | 10.7 (74) | -2.7 (-5.7 to +1.1) | 0.10 | 0.18 |
| Mean ROC at the low pairs (mg/dL/min) | -0.33 (76) | -0.33 (74) | 0.00 (-0.09 to +0.09) | 0.54 | 0.69 |
| % of low pairs with glucose falling | 14.1 (76) | 15.5 (74) | +1.5 (-2.0 to +3.9) | 0.58 | 0.69 |
| % of low pairs on wear day 1 | 20.8 (76) | 19.5 (74) | -1.3 (-3.8 to +2.1) | 0.86 | 0.90 |
| % of low pairs with the CGM at its 39 mg/dL floor | 6.7 (76) | 4.7 (74) | -2.0 (-3.4 to -0.1) | 0.05 | 0.11 |

- Nothing passes correction. By the fingerstick (the fair ruler) women's and men's lows are the same depth, the same share below 54, the same speed, the same share on day 1.
- The only two rows near p 0.05 are measured by the CGM itself: women's episodes bottom out 0.8 mg/dL lower and hit the 39 floor more often. A sensor that reads 2-3 mg/dL lower in women would produce exactly these two rows. They are a symptom of the gap, not a cause.

### 4b. Matching: does the gap survive when women and men are compared at the same glucose and trend? Yes.
Same 10,022 low pairs. Strata = 5 mg/dL bins of the average x trend (falling / flat / rising / unknown). Standardised gap = within-stratum differences averaged with the pooled mix as weights (strata need 5 pairs per sex); mixed model = regression with the same bins and a random intercept per person.

| Comparison | Standardised gap, men minus women (CI) | Mixed-model gap (CI) | p | BH p |
|---|---|---|---|---|
| Pooled low pairs, no matching | +3.6 (+1.9 to +5.5); 10,022 pairs | +3.6 (+1.6 to +5.5) | <0.001 | 0.001 |
| Matched on glucose bin and trend | +3.7 (+1.9 to +5.6); 24 strata, 10,004 pairs | +3.6 (+1.9 to +5.2) | <0.001 | <0.001 |
| Matched, plus night, wear day 1 and arm | (regression only) | +3.4 (+1.6 to +5.1) | <0.001 | <0.001 |
| Sensitivity: matched on fingerstick bin and trend | +2.4 (+1.1 to +3.8); 36 strata, 9,987 pairs | +2.5 (+1.1 to +3.8) | <0.001 | 0.002 |

- The mix of low pairs is the same in both sexes: by glucose bin, women 0.9 / 3.1 / 8.6 / 13.4 / 18.8 / 25.2 / 30.0 % (below 40 up to 65-69) vs men 0.8 / 3.4 / 6.9 / 12.3 / 19.7 / 25.9 / 31.1 %; by trend, falling 16 vs 16 %, flat 72 vs 74 %, rising 5 vs 6 %.
- So there was nothing to match away. The gap after matching (+3.7) equals the gap before (+3.6). Matching on fingerstick bins gives +2.4; that version is a stricter test (see ERROR_DRIVERS.md section 8 on why fingerstick bins pull toward zero) and still excludes zero.
- Reading: the glucose pattern does not explain the gap. It is a property of the sensor-vs-fingerstick comparison itself.

## 5. Block C: body and physiology
What the two sexes look like (medians, IQR):

| Variable | Women | Men |
|---|---|---|
| Weight (kg) | 72.1 (63.8-81.3) | 86.0 (78.8-97.7) |
| BMI (kg/m2) | 26.3 (23.1-29.3) | 27.3 (24.7-30.3) |
| Height (cm) | 165 (161-170) | 180 (175-185) |
| HbA1c at screening (%) | 7.35 (6.9-7.8) | 7.25 (6.8-7.8) |
| Age (years) | 38.5 (30-52) | 47 (35-55) |
| TDD (U/day; 208 people with 14+ full pump days) | 35.1 (28.6-46.4) | 47.1 (38.0-60.0) |
| Insulin dose per kg (U/kg/day) | 0.51 (0.43-0.59) | 0.56 (0.46-0.67) |
| Glucose CV (%) | 37.8 (35.3-40.8) | 36.9 (34.2-40.6) |

Sex term for low-range bias after adjustment (OLS with robust errors, 150 people with a low-range bias; 141 with a dose):

| Model | n | Men minus women (CI) | p | BH p |
|---|---|---|---|---|
| Sex alone | 150 | +4.2 (+2.3 to +6.1) | <0.001 | <0.001 |
| + weight | 150 | +3.8 (+1.4 to +6.2) | 0.002 | 0.006 |
| + BMI | 150 | +4.1 (+2.1 to +6.0) | <0.001 | <0.001 |
| + height | 150 | +4.5 (+1.9 to +7.1) | <0.001 | 0.002 |
| + HbA1c | 150 | +4.1 (+2.2 to +6.1) | <0.001 | <0.001 |
| + age | 150 | +4.1 (+2.2 to +6.1) | <0.001 | <0.001 |
| + insulin dose per kg | 141 | +4.3 (+2.3 to +6.4) | <0.001 | <0.001 |
| + all six | 141 | +4.0 (+0.9 to +7.0) | 0.01 | 0.03 |
| + all six + CV + % time below 70 | 141 | +4.0 (+1.0 to +7.1) | 0.010 | 0.03 |

Within each sex, does any of these go with the bias? No.

| Variable | Women: rho (CI), p | Men: rho (CI), p |
|---|---|---|
| Weight | -0.04 (-0.27 to +0.19), 0.73 | +0.14 (-0.08 to +0.38), 0.22 |
| BMI | -0.01 (-0.20 to +0.20), 0.95 | +0.12 (-0.16 to +0.36), 0.32 |
| Height | -0.03 (-0.26 to +0.20), 0.77 | +0.10 (-0.14 to +0.34), 0.40 |
| HbA1c | -0.05 (-0.27 to +0.19), 0.67 | -0.15 (-0.35 to +0.06), 0.21 |
| Age | -0.19 (-0.42 to +0.06), 0.10 | +0.19 (-0.05 to +0.43), 0.11 |
| Insulin dose per kg | +0.02 (-0.24 to +0.29), 0.85 | -0.06 (-0.31 to +0.19), 0.61 |

All 12 BH p are 0.18 or more.
- Body size is the obvious candidate (women are 14 kg lighter and 15 cm shorter) and it is not it: the sex term barely moves, and within a sex, weight and height do not track the bias. The CI widens when all six are added because weight, BMI and height overlap heavily with sex, not because the estimate moved.
- Haematocrit, haemoglobin, kidney or liver values: REPLACE-BG's only central-lab analyte is HbA1c; its screening form has weight and height only. Shanghai has lipids, creatinine, eGFR, uric acid, urea and C-peptide but no blood count. So the one physiological variable with a known sensor mechanism cannot be checked in either dataset.

## 6. Block D: Shanghai (Abbott flash sensor, 112 patients, 4,012 pairs)
| Pairs | Women: bias (pairs, patients) | Men: bias (pairs, patients) | Men minus women (CI) | mixed-model p | BH p |
|---|---|---|---|---|---|
| Average below 70 | +1.2 % (11, 8) | -17.2 % (39, 10) | -18.4 (-39.1 to +9.8) | 0.39 | 0.94 |
| Fingerstick below 70 | +15.4 % (11, 6) | +14.7 % (26, 9) | -0.8 (-13.4 to +16.3) | 0.94 | 0.94 |
| Average 70-180 (context) | -5.3 % (1,230, 45) | -8.3 % (1,467, 50) | -3.0 (-10.0 to +4.5) | 0.87 | 0.94 |

Uninformative. There are 50 low pairs in total, no patient has 20 of them, and the CI spans -39 to +10 points. It neither supports nor contradicts the REPLACE-BG gap.

## 7. Block E: MAUDE complaint texts (a weak outside check)
Set: serious wrong-reading reports that state both a sensor and a meter value (17,573 pairs; 8,556 with a sex filled in, 82 % of them Dexcom). Dexcom pairs with a sex: 3,736 women, 3,294 men. Different sensor generations (mostly G6 and G7), complaint-sized errors, and the sex field only exists from 2021 (BRAND_COMPARISON.md section 8). Direction here is WOMEN MINUS MEN.

| Measure | Women | Men | Women minus men (CI) | p | BH p |
|---|---|---|---|---|---|
| Sensor read below the meter | 49.0 % | 44.6 % | +4.4 (+2.0 to +6.8) | <0.001 | <0.001 |
| Depth of the reads-low errors (median, % of meter; meter about 440 mg/dL) | -69.6 % | -72.8 % | +3.2 (+0.4 to +5.5) | 0.002 | 0.006 |
| Hidden low: meter below 70, sensor 70 or more | 35.5 % | 38.1 % | -2.6 (-4.8 to -0.5) | 0.02 | 0.04 |
| Meter below 70 (any sensor value) | 42.0 % | 44.5 % | -2.5 (-4.9 to -0.1) | 0.03 | 0.04 |
| False low: sensor below 70, meter 70 or more | 18.3 % | 18.2 % | +0.1 (-1.7 to +1.8) | 0.92 | 0.92 |

- Same direction on two of three: women's Dexcom complaints are more often "reads low" (+4.4 points) and less often a hidden low (-2.6 points). The depth of the reads-low errors is slightly smaller in women, not larger. All brands pooled: reads low 51.6 vs 48.3 %, hidden low 33.0 vs 34.8 %. Abbott alone: reads low 69.3 vs 63.4 %, hidden low 15.3 vs 19.7 %.
- These are complaint errors of -70 %, not 4 %, from people who chose to report. They can only say "nothing here contradicts the trial", and they say that.

## 8. Block F: does 2.5 mg/dL at 60 matter?
Near the 70 mg/dL alert line, pooled pairs with participant-bootstrap CIs:

| Pairs | Women | Men | Men minus women (CI) | p | BH p |
|---|---|---|---|---|---|
| Fingerstick 70-79: % with CGM below 70 (false low near the line; 3,683 / 3,446 pairs) | 36.0 % | 31.1 % | -4.9 (-8.5 to -1.4) | 0.001 | 0.004 |
| Fingerstick 60-69: % with CGM 70 or more (missed low near the line; 2,877 / 2,830 pairs) | 36.5 % | 41.8 % | +5.3 (+0.9 to +9.8) | 0.003 | 0.009 |

Per person (from the deep check, not counted again): missed-low rate 27.5 % in women vs 33.9 % in men (+6.4, CI +2.3 to +12.9); false-low rate 42.6 vs 38.9 % (-3.7, CI -10.0 to +2.4).

Simulation lookup (`simulation_v2_lookup.csv`; one constant bias on the whole trace, so an upper bound for a gap that only exists below 70):

| What the person would see | Bias -6.4 % (women's median) | Bias -2.2 % (men's median) | Women minus men | A +4.2 % sensor vs an unbiased one |
|---|---|---|---|---|
| Corrections skipped (% of all corrections) | 0.0 | 0.0 | 0.0 | 0.0 |
| Doses changed by 1 U or more (%) | 0.0 | 0.0 | 0.0 | 0.0 |
| False low alerts per day | 0.28 | 0.11 | +0.17 | 0.0 |
| True lows missed (%) | 0.0 | 0.0 | 0.0 | 11.8 |
| Time in range shown (%) | 67.7 | 64.5 | +3.2 | 59.4 |
| Time below 70 shown (%) | 5.1 | 4.1 | +1.0 | 3.0 |
| LBGI | 1.25 | 1.04 | +0.21 | 0.78 |

- Dosing: a 4-point bias is far below the 10-12 % where the dose rule starts skipping corrections (SIMULATION_V2.md). Nothing changes for insulin.
- Alerts: the gap moves the 70 mg/dL line by about 2.5 mg/dL. In the lookup that is about one extra false low alert every six days in women; in the real pairs it is 5 points more false lows and 5 points fewer missed lows near the line. Read from the men's side: a sensor that reads 4 points higher misses about 12 % of lows (lookup) or 5-6 points more lows (pairs). That is the same "missed lows" difference the deep check saw.
- The paper's safety message (the low-range bias hides lows) applies to both sexes; men's sensors hide a few more, women's cry wolf a little more.

## 9. Post hoc: could the way people fingerstick make the gap? (added after seeing the arm result; not in the BH families)
Fingersticks are not random. In the CGM-only arm people dosed from the sensor and may have tested when the sensor looked low. In the blinded run-in (128 people) the sensor was hidden, so a fingerstick could not be chosen because of the sensor's value.

| Split | Women | Men | Men minus women, per person (CI) | p | Pooled gap (CI); mixed-model p |
|---|---|---|---|---|---|
| Run-in, blinded CGM, average below 70 | -4.8 (22; 938 pairs) | -0.9 (18; 835 pairs) | +3.9 (-1.6 to +7.5) | 0.09 | +5.8 (+2.0 to +9.9); <0.001 |
| Run-in, standard (visible) CGM | -1.6 (2; 271 pairs) | -2.1 (1; 193 pairs) | n.t. | n.a. | +3.5 (-0.4 to +8.2); 0.07 |
| Run-in, blinded CGM, calibration pairs below 70 | -12.8 (18; 940 pairs) | -3.8 (19; 957 pairs) | +9.1 (+1.8 to +14.0) | 0.003 | +6.4 (+2.5 to +10.4); <0.001 |

- The gap is present when nobody could see the sensor. Choosing when to test does not make it.
- Testing habits by sex: verified fingersticks per day 3.3 (women) vs 3.2 (men), p 0.29; share of fingersticks that were low 5.2 vs 4.6 %, p 0.34. In the randomised CGM-only arm: 4.1 vs 3.9 per day, 3.8 vs 4.7 % low (p 0.20). In the randomised CGM+BGM arm: 2.7 vs 2.4 per day; 6.3 vs 2.9 % low (p 0.005). So in the one arm where the gap is absent, the men rarely tested while low (12 men reach 20 low pairs). guess: the CGM+BGM-arm null is small numbers plus a different group of men, not a different sensor; the data cannot prove that.

## 10. Literature (web search, 7 queries, 2026-11-06)
Queries: sex differences in CGM accuracy / MARD / hypoglycaemia bias; Dexcom G4 Platinum accuracy by sex; CGM accuracy factors (sex, BMI, age) for Libre and Dexcom G6; interstitial vs blood glucose by sex and menstrual cycle; FreeStyle Libre accuracy by sex; mechanism (skin thickness, subcutaneous fat, lag by sex); the ultra-runner menstrual-phase pilot.

Found:
- Edge J et al. "An alternative sensor-based method for glucose monitoring in children and young people with diabetes." Archives of Disease in Childhood, 2017. FreeStyle Libre, 89 children, MARD 13.9 %; "sensor accuracy was unaffected by patient factors such as age, body weight, sex, method of insulin administration" or time of day. The only accuracy study found that checked sex; it found nothing, in children, with a different sensor.
- Garg SK et al. "Accuracy and Safety of Dexcom G7 Continuous Glucose Monitoring in Adults with Diabetes." Diabetes Technology and Therapeutics, 2022. 316 adults, MARD 8.2 % (arm) and 9.1 % (abdomen). The abstract reports no result by sex.
- van Beers CA. "Analysis: The Accuracy and Efficacy of the Dexcom G4 Platinum Continuous Glucose Monitoring System." Journal of Diabetes Science and Technology, 2015. Commentary on the G4 accuracy study; nothing by sex. No G4 paper found reports accuracy by sex.
- Skroce K et al. "Real World Interstitial Glucose Profiles of a Large Cohort of Physically Active Men and Women." Sensors, 2024. About 12,500 active adults without diabetes on an Abbott Libre Sense: men's mean 24-h glucose 100 mg/dL vs women's 96. Glucose levels, not sensor accuracy.
- Not a paper: a University of Waikato PhD thesis (Dole A, 2024) reports a 12-runner pilot in which the CGM read 0.4-1.0 mmol/L (8-18 mg/dL) below capillary glucose during exercise and the menstrual phase changed the CGM-minus-capillary difference during fed running (p 0.02). The DOI attached to that record leads to a review (Dole, Beaven, Sims, "Menstrual Cycle Tracking in Sports Research: Challenges, Progress, and Future Directions", Physiologia 2023; 3: 598-610), not to the pilot, so the pilot stands as unpublished.

Not found: any published report of a sex difference in CGM bias in the low range, for Dexcom G4, G5, G6, G7 or Libre. Pivotal accuracy papers report sex only as the share of men enrolled.

## 11. Verdict in plain words
- Real or chance: real in this dataset. It reproduces in every split that can be measured, in two pair sources, under three ways of defining "low", and when the sensor was hidden. The one hole is the randomised CGM+BGM arm (36 people; the men there rarely tested while low). We cannot call that hole chance with certainty; it is the reason the claim stays modest.
- Sensor or glucose pattern: sensor. Women's and men's lows are the same by the fingerstick, matching changes nothing, and the only "differences" in the lows are the ones the CGM itself measures.
- Explained by anything we hold: no. Not body size, HbA1c, age, insulin dose, lag, wear day, time of day, trend, or testing habits. Haematocrit and sensor site are not in the data. guess: a tissue or site difference (the G4 was worn on the abdomen), or a meter effect, see caveats; this data cannot say.
- Does it matter: a little, for alerts only. About 2.5 mg/dL at 60. No dose changes. Women's sensors give a few more false low alerts; men's hide a few more true lows (near 70: 42 vs 37 % missed).
- What the paper should say (one sentence): "In the low range the sensor read about 2.5 mg/dL lower in women than in men (bias -6.4 vs -2.2 %, difference +4.2 points, CI +2.0 to +6.3); the gap survived matching on glucose level and trend and adjustment for body size, was absent in one small study arm, has no known mechanism, and is too small to change a dose."
- What would settle it: an accuracy dataset with a laboratory reference (YSI) rather than a home meter, both sexes well represented in the low range, a newer sensor (G6, G7 or Libre), and haematocrit and sensor-site recorded. A manufacturer's pivotal-trial data split by sex would do.

## 12. Caveats
- The 66 REPLACE-BG tests are not 66 independent questions: most re-test one effect in overlapping subsets, so "28 pass BH" means "the gap is robust", not "28 findings".
- Three splits (night, falling, rising) could only be tested on pooled pairs; below 54 and wear day 1 have per-person CIs that include zero but pooled gaps that do not. Meter type is not testable.
- The reference is a home meter (Contour Next), not laboratory blood. If meter error differed by sex, for example through haematocrit (lower in women; some meters read higher at low haematocrit), part of the gap could sit in the meter rather than the sensor. Calibrating with the same meter would absorb a constant offset but not a low-range-only one. There is no haematocrit in the data to check this. guess: unlikely to be the whole 4 points, but it cannot be ruled out.
- The CGM+BGM arm null rests on 24 women and 12 men with enough low pairs; the sex x arm interaction (BH p 0.05) is at the edge.
- The gap is a Dexcom G4 (2015-2016) result on an abdomen-worn sensor; newer sensors are factory-calibrated and worn on the arm.
- Shanghai has 50 low pairs; MAUDE is self-selected complaints with complaint-sized errors and a sex field only since 2021, mostly Dexcom.
- The post-hoc block (section 9) was designed after the arm result was seen.

## 13. How to run
`python analysis/demographics_followup.py "Uncommitted Data/Raw Data Dump" analysis` from the repo root (optional third argument: cache folder; `--no-maude` skips block E). Needs the preprocess cache and `cache/participant_metrics.parquet` (run `subgroups.py` first) and, for block E, the MAUDE files under `fda-maude/clean/` plus `fda-maude/results/report/tables/d_problem_family_mapping.csv`. Runtime 24 s with the cache (6 s of it MAUDE). Seed 600; 2,000 bootstrap resamples. Outputs: `demographics_followup_stats.json` (the pre-registered list is written to it before any test runs), figure 35, and the markdown tables above printed to the screen. Reuses `preprocess.py` (loaders), `demographics_deep.py` (tests, covariates, BH), and the MAUDE loaders in `fda-maude/scripts/text_results.py` and `brand_comparison.py`.
