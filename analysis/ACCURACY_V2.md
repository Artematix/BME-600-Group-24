# CGM accuracy, version 2 (2026-10-27)

Script: `analysis/accuracy_v2.py`. Numbers: `analysis/accuracy_v2_stats.json`. Figures 13-16 in `analysis/figures/`.
All data comes from the shared cache (`analysis/preprocess.py`, cache version 2026-10-27.1).

Terms used here:
- CGM = continuous glucose monitor (the sensor). Meter = fingerstick blood glucose meter. Reference = the meter value we treat as truth.
- Pair = one CGM reading matched in time to one meter value. Error = CGM minus reference.
- Bias = mean error. Negative = the sensor reads low. MARD = mean absolute relative difference, the average percent error. Median ARD = the middle percent error.
- 15/15, 20/20, 40/40 = share of pairs within 15 (20, 40) mg/dL when the reference is below 100 mg/dL, or within 15 (20, 40) % above that.
- Parkes grid = error chart with zones A (harmless) to E (dangerous). iCGM = the FDA accuracy rule for CGMs (21 CFR 862.1355).
- CI = 95 % confidence interval. All CIs here come from a bootstrap that resamples participants (1,000 draws, seed 600), because one person gives hundreds of pairs that are not independent.
- Calibration = a fingerstick typed into the Dexcom receiver to correct the sensor. Those fingersticks are not a fair test, so they are excluded from sets A-C.

## 1. Headline

- Set A (the headline set): 33,467 pairs, 77 people. MARD 13.8 % (CI 12.3 to 15.7). Bias -5.2 mg/dL (CI -6.1 to -4.3), -1.1 % (CI -2.1 to +0.1).
- The midterm number was 10.4 % MARD. It was too low. Pump "blood glucose" entries were counted as fingersticks, and in the CGM-only arm most of them are CGM values typed into the pump (section 3). Fixed here.
- Below 70 mg/dL (by the average of CGM and meter) the sensor reads low by 3 to 4 mg/dL (-4.9 % under 54, -2.7 % at 54-69) and MARD is 16 to 19 %.
- 28 % of meter-confirmed lows (under 70) showed as not low on the CGM. 3.4 % of not-low meter values showed as low.
- Against the FDA iCGM thresholds, Set A fails all 7 criteria. The G4 predates the rule (2018); the thresholds are only a familiar yardstick, and our reference is a home meter, not lab blood.

## 2. Analysis sets

| Set | Definition | Pairs | People |
|---|---|---|---|
| A (headline) | meter-log fingersticks, not used for calibration, study window, CGM+BGM arm, randomised phase | 33,467 | 77 |
| B | same rules, all 226 participants, run-in and randomised phases | 168,990 | 226 |
| C (sensitivity) | same rules, CGM-only arm, randomised phase | 104,195 | 148 |
| D | calibration pairs in the study window (sensor just before correction) | 116,244 | 226 |
| E (old headline set) | every meter-table pair in the window, every reference source, calibration-timed pairs included | 460,634 | 226 |
| S | Shanghai fingerstick pairs, Abbott flash CGM (98 of 112 patients have a fingerstick) | 4,012 | 98 |

Rules shared by A-C: study window = day 0 to 329; "meter-log" = rows read from the Contour Next meter itself (`source = meter`); randomised phase = day at or after the person's randomisation day.
Set A has 388 pairs with the CGM clipped at 39 or 401 mg/dL (kept, flagged). Median 399 pairs per person (range 1 to 1,368).

## 3. From the midterm number (set E0) to Set A

| Step | Pairs | People | Bias mg/dL | MARD % (CI) | 20/20 % | Parkes A+B % |
|---|---|---|---|---|---|---|
| E0: every meter-table pair, all days (midterm headline) | 475,502 | 226 | -4.0 | 10.4 (9.9 to 10.9) | 88.2 | 99.0 |
| E: keep the study window only | 460,634 | 226 | -4.0 | 10.2 (9.8 to 10.7) | 88.5 | 99.1 |
| Em: keep meter-log rows only (drop pump BG entries) | 285,166 | 226 | -4.9 | 11.9 (11.4 to 12.3) | 86.1 | 99.1 |
| B: drop pairs used for calibration | 168,990 | 226 | -5.0 | 13.3 (12.7 to 13.9) | 83.8 | 98.6 |
| A1: CGM+BGM arm only | 43,255 | 77 | -5.0 | 13.7 (12.4 to 15.3) | 83.8 | 98.4 |
| A: randomised phase only | 33,467 | 77 | -5.2 | 13.8 (12.3 to 15.7) | 84.0 | 98.3 |

Why pump BG entries are dropped. The meter table mixes two sources: the meter's own log and "BG" values logged by insulin pumps. The table below splits non-calibration pairs in the randomised phase by source. "CGM = reference exactly" is the share of pairs with zero error. A real fingerstick matches the CGM exactly about 2 % of the time.

| Arm | Reference source | Pairs | People | MARD % | Median ARD % | CGM = reference exactly % |
|---|---|---|---|---|---|---|
| CGM-only | meter log | 104,195 | 148 | 13.1 | 9.0 | 2.2 |
| CGM-only | pump entry, not a copy of a meter reading | 77,077 | 134 | 4.7 | 1.1 | 36.9 |
| CGM-only | pump entry that copies a meter reading | 5,059 | 130 | 9.1 | 6.3 | 8.3 |
| CGM+BGM | meter log | 33,467 | 77 | 13.8 | 9.1 | 2.2 |
| CGM+BGM | pump entry, not a copy of a meter reading | 15,417 | 68 | 10.2 | 4.3 | 14.4 |
| CGM+BGM | pump entry that copies a meter reading | 13,112 | 65 | 10.7 | 8.2 | 2.1 |

- In the CGM-only arm, people were told to dose from the CGM. The pump entries are the CGM number typed into the pump. They are not a reference. Their "MARD" of 4.7 % is the sensor against itself.
- In the CGM+BGM arm about 1 pump entry in 7 is an exact CGM match, so a part of them are CGM values too. guess: about a fifth.
- With the pump entries removed, the two arms agree: 13.8 % vs 13.1 %. Calibration pairs (set D) give 14.1 %. The earlier "calibration pairs are much worse" story (10.8 vs 14.1) was mostly this contamination.
- This affects every other script that uses `independent_meter` from preprocess.py. Flagged to the manager.

## 4. Overall accuracy per set

| Set | Pairs | People | Bias mg/dL (CI) | Bias % (CI) | MARD % (CI) | Median ARD % (CI) | 15/15 % | 20/20 % (CI) | 40/40 % | Parkes A / B / C / D / E % |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 33,467 | 77 | -5.2 (-6.1 to -4.3) | -1.1 (-2.1 to +0.1) | 13.8 (12.3 to 15.7) | 9.1 (8.6 to 9.6) | 73.8 | 84.0 (81.2 to 86.3) | 96.0 | 83.7 / 14.6 / 1.4 / 0.3 / 0.0 |
| B | 168,990 | 226 | -5.0 (-5.4 to -4.6) | -1.3 (-1.6 to -0.9) | 13.3 (12.7 to 13.9) | 9.0 (8.8 to 9.2) | 73.6 | 83.8 (82.7 to 84.9) | 96.5 | 83.6 / 15.0 / 1.2 / 0.2 / 0.0 |
| C | 104,195 | 148 | -5.0 (-5.5 to -4.6) | -1.4 (-1.8 to -0.9) | 13.1 (12.5 to 13.8) | 9.0 (8.7 to 9.3) | 73.2 | 83.6 (82.3 to 84.9) | 96.6 | 83.3 / 15.5 / 1.1 / 0.2 / 0.0 |
| D | 116,244 | 226 | -5.2 (-5.5 to -4.9) | -2.8 (-3.0 to -2.5) | 14.1 (13.7 to 14.4) | 10.5 (10.2 to 10.8) | 67.8 | 79.8 (78.8 to 80.7) | 96.4 | 80.0 / 19.3 / 0.7 / 0.0 / 0.0 |
| E | 460,634 | 226 | -4.0 (-4.4 to -3.6) | -1.4 (-1.7 to -1.0) | 10.2 (9.8 to 10.7) | 6.1 (5.9 to 6.3) | 81.1 | 88.5 (87.8 to 89.2) | 97.5 | 88.4 / 10.7 / 0.8 / 0.1 / 0.0 |
| S | 4,012 | 98 | -15.1 (-20.9 to -9.9) | -7.4 (-10.7 to -4.5) | 13.9 (12.2 to 16.1) | 11.0 (9.6 to 12.9) | 64.2 | 76.8 (70.0 to 82.3) | 96.4 | 74.7 / 25.1 / 0.3 / 0.0 / 0.0 |

- In Set A the CGM reads below the meter in 58 % of pairs. 1.7 % of pairs (570) sit in Parkes zones C to E.
- Sensitivity checks on Set A: without clipped CGM values MARD 13.6 %; adding the run-in phase 13.7 % (43,255 pairs); adding the pump entries back 12.2 % (61,996 pairs).

## 5. Accuracy by glucose range, Set A

Table 5a bins by the AVERAGE of CGM and meter. This is the fair axis: binning by either device alone creates a fake bias (see RESULTS.md). Figure 13 shows this table.

| Average of CGM and meter (mg/dL) | Pairs | People | Bias mg/dL (CI) | Bias % (CI) | MARD % (CI) | 20/20 % (CI) |
|---|---|---|---|---|---|---|
| <54 | 597 | 59 | -3.9 (-5.3 to -2.5) | -4.9 (-7.6 to -2.2) | 19.1 (18.0 to 20.4) | 92.0 (89.4 to 94.5) |
| 54-69 | 1,826 | 74 | -3.2 (-4.1 to -2.3) | -2.7 (-4.1 to -1.3) | 16.4 (15.3 to 17.6) | 86.4 (83.8 to 88.7) |
| 70-180 | 19,680 | 76 | -4.1 (-5.0 to -3.0) | -0.5 (-1.9 to +1.3) | 14.8 (12.9 to 17.4) | 81.3 (77.9 to 84.2) |
| 181-250 | 7,747 | 76 | -7.2 (-9.2 to -5.4) | -1.7 (-2.5 to -0.9) | 11.6 (10.3 to 13.2) | 87.2 (84.2 to 89.5) |
| >250 | 3,617 | 77 | -7.7 (-10.9 to -4.7) | -1.3 (-2.2 to -0.4) | 10.2 (9.5 to 11.4) | 89.1 (86.6 to 90.7) |

Table 5b bins by the CGM VALUE. This is what the patient sees on the screen. Low readings on the screen are far too low on average; that is partly a selection effect (a reading is more likely to show under 54 when noise pushed it down).

| CGM value (mg/dL) | Pairs | People | Bias mg/dL (CI) | Bias % (CI) | MARD % (CI) | 20/20 % (CI) |
|---|---|---|---|---|---|---|
| <54 | 902 | 66 | -17.8 (-21.5 to -14.9) | -20.8 (-23.6 to -18.4) | 25.0 (23.1 to 27.1) | 71.5 (66.3 to 76.3) |
| 54-69 | 1,916 | 73 | -10.7 (-13.7 to -8.5) | -8.6 (-10.5 to -6.9) | 16.6 (15.3 to 18.2) | 82.4 (78.5 to 85.6) |
| 70-180 | 19,733 | 76 | -7.2 (-8.8 to -6.1) | -2.1 (-3.0 to -1.0) | 13.4 (12.2 to 15.0) | 82.6 (79.6 to 85.1) |
| 181-250 | 7,444 | 77 | -2.5 (-4.7 to +0.1) | +2.3 (+0.1 to +4.9) | 12.5 (10.5 to 15.1) | 87.8 (85.0 to 90.1) |
| >250 | 3,472 | 76 | +6.9 (+2.4 to +11.6) | +6.9 (+3.9 to +10.7) | 14.0 (11.4 to 17.6) | 87.6 (84.5 to 89.8) |

Bins: 70-180 includes both ends; 181-250 means above 180 up to 250. Sets B and C give the same picture within 1 point (see the JSON).

## 6. FDA iCGM-style table, Set A (figure 14)

The iCGM rule bins by the CGM value and uses its own limits: mg/dL limits below 70, percent limits at or above 70, and 20 % for all pairs. Each share must have a lower one-sided 95 % bound above the threshold. Source: 21 CFR 862.1355(b)(6), https://www.law.cornell.edu/cfr/text/21/862.1355. The Dexcom G4 (2012-2015) predates this 2018 rule, and our reference is a home meter, not lab blood. We use the thresholds only as a familiar benchmark, not as a pass/fail test.

| CGM bin | Criterion | Pairs | Observed % | Lower 95 % bound | Threshold | Result |
|---|---|---|---|---|---|---|
| <70 | within 15 mg/dL | 2,818 | 69.6 | 66.1 | above 85 | fail |
| <70 | within 40 mg/dL | 2,818 | 92.7 | 90.6 | above 98 | fail |
| 70-180 | within 15 % | 19,733 | 69.8 | 67.3 | above 70 | fail (narrow) |
| 70-180 | within 40 % | 19,733 | 95.6 | 93.9 | above 99 | fail |
| >180 | within 15 % | 10,916 | 78.4 | 76.0 | above 80 | fail (narrow) |
| >180 | within 40 % | 10,916 | 96.2 | 94.3 | above 99 | fail |
| all | within 20 % | 33,467 | 81.5 | 79.3 | above 87 | fail |

- The rule also allows no pair with CGM below 70 and reference above 180, or the reverse. Set A has 34 and 33 such pairs.
- The old set E (pump entries included) passed the two 15 % criteria. Sets B, C and D fail all seven.

## 7. Misclassification at the thresholds, Set A (figure 15)

Rows = meter category, columns = CGM category. Low = under 70. In range = 70 to 180 (or 200). High = above 180 (or 200).

| Meter \ CGM (70 / 180) | Low | In range | High | Total |
|---|---|---|---|---|
| Low | 1,751 (71.8 %) | 656 (26.9 %) | 33 (1.4 %) | 2,440 |
| In range | 1,033 (5.4 %) | 16,963 (88.7 %) | 1,134 (5.9 %) | 19,130 |
| High | 34 (0.3 %) | 2,114 (17.8 %) | 9,749 (81.9 %) | 11,897 |

| Rate (Set A) | 70 / 180 rule | 70 / 200 rule |
|---|---|---|
| Missed lows: meter under 70, CGM 70 or more | 28.2 % (24.4 to 32.8) | same |
| False lows: meter 70 or more, CGM under 70 | 3.4 % (2.9 to 4.0) | same |
| Missed highs: meter high, CGM not high | 18.1 % (15.6 to 20.9) | 20.3 % (17.6 to 23.6) |
| False highs: meter not high, CGM high | 5.4 % (4.3 to 6.7) | 4.6 % (3.8 to 5.6) |
| Any pair in the wrong category | 15.0 % (13.6 to 16.6) | 13.9 % (12.7 to 15.3) |

Hypoglycaemia detection, pair level (sensitivity = share of meter lows the CGM also called low; PPV = share of CGM lows that were real):

| Threshold | TP / FN / FP / TN | Sensitivity % (CI) | Specificity % (CI) | PPV % (CI) | NPV % (CI) |
|---|---|---|---|---|---|
| 70 mg/dL | 1,751 / 689 / 1,067 / 29,960 | 71.8 (67.2 to 75.6) | 96.6 (96.0 to 97.1) | 62.1 (57.8 to 66.5) | 97.8 (97.3 to 98.2) |
| 54 mg/dL | 307 / 286 / 595 / 32,279 | 51.8 (45.7 to 56.7) | 98.2 (97.8 to 98.5) | 34.0 (29.3 to 38.2) | 99.1 (98.9 to 99.3) |

- Fingersticks are not random. People test when they suspect a low, so these rates describe tested moments, not all moments. Sets B and C: missed lows 31 % and 33 %, false lows 3.0 % and 2.8 %.

## 8. Bland-Altman with repeated measures, Set A (figure 16)

Method: Bland and Altman 2007, "Agreement between methods of measurement with multiple observations per individual", J Biopharm Stat 17:571-582, https://pubmed.ncbi.nlm.nih.gov/17613642/. A one-way random-effects analysis of variance on the differences splits their spread into a between-person part and a within-person part. Limits of agreement (LoA) = bias plus or minus 1.96 times the combined SD.

| Scale | Bias (CI) | SD between people | SD within person | SD combined | LoA low (CI) | LoA high (CI) | Pairs inside |
|---|---|---|---|---|---|---|---|
| mg/dL | -5.2 (-6.1 to -4.3) | 3.4 | 31.4 | 31.6 | -67.1 (-78.0 to -58.7) | +56.8 (+47.8 to +67.5) | 95.0 % |
| % of meter | -1.1 (-2.1 to +0.1) | 3.9 | 24.4 | 24.7 | -49.5 (-58.8 to -41.0) | +47.3 (+37.0 to +58.7) | 96.8 % |

- Almost all the spread is within person (31.4 of 31.6 mg/dL). People differ little in bias; readings differ a lot from moment to moment. So the naive LoA (ignoring clustering) are the same; only the CIs change.
- In plain words: a single CGM reading can sit about 50 to 65 mg/dL away from the meter and still be "normal" for this sensor.

## 9. Meter uncertainty (ISO 15197), Set A

ISO 15197:2013 allows 95 % of meter results within 15 mg/dL (below 100) or 15 % (100 and above). We added random meter error of that size (SD = limit / 1.96) to the reference, and half of it, and recomputed. 20 draws per level, seed 601.

| Meter error added | MARD % | MARD % (average under 70) | Bias mg/dL (average under 70) | Bias % (average under 70) |
|---|---|---|---|---|
| none (observed) | 13.8 | 17.0 | -3.4 | -3.3 |
| half the ISO limit (SD 3.8 mg/dL or 3.8 %) | 14.3 (+0.5) | 18.1 (+1.0) | -2.9 (+0.5) | -2.1 (+1.2) |
| the ISO limit (SD 7.7 mg/dL or 7.7 %) | 15.7 (+1.9) | 21.0 (+3.9) | -1.7 (+1.7) | +1.0 (+4.3) |

What it shows:
- Meter error of the largest allowed size would add about 2 points to MARD. The Contour Next is far better than the limit (MARD about 3 %, METHODS_REVIEW.md section 2), so guess: its share of our 13.8 % is under 1 point.
- Extra meter noise pushes the low-range bias (by average) toward zero, not away from it. So meter error cannot create the low-range under-reading. If anything it hides part of it.

## 10. Published MARD values for context

| Device | Setting | Reference | MARD % | Source |
|---|---|---|---|---|
| Dexcom G4 Platinum, Software 505 | adults, clinic sessions | YSI lab / meter | 9.0 (lab), 11.3 (meter) | Bailey 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604574 |
| Dexcom G4 Platinum, original vs Software 505 | children 2-17, clinic | YSI lab | 17 (original), 10 (505) | Laffel 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4717517 |
| Abbott FreeStyle Navigator II | adults, free living at home, 10,597 pairs | built-in meter | 14.2 overall; 30.6 under 70, 13.9 at 70-180, 9.8 above 180 | Thabit 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4649721 |
| Abbott FreeStyle Libre (first generation) | 72 adults, 14 days at home, 13,195 pairs | reader meter / YSI | 11.4 (meter), 12 (lab); consensus zone A 86.7, A+B 99.7 | Bailey 2015, https://doi.org/10.1089/dia.2014.0378 |
| Abbott FreeStyle Libre | 742 inpatients with type 2 diabetes, 25,579 pairs | hospital meter | 14 overall; 24.5 at 3 AM (bias -23 %); 72 % of pairs read low | Wen 2022, https://pmc.ncbi.nlm.nih.gov/articles/PMC9639390 |

- Our 13.8 % (home use, meter reference, 26 weeks) sits with the free-living studies (14.2 %, 14 %), above the clinic G4 figure (11.3 %). Home studies with meter references usually read 2 to 4 points higher than clinic studies with lab blood. guess: the REPLACE-BG G4 ran Software 505 (trial paper, to confirm).

## 11. Shanghai comparator (set S, Abbott flash CGM)

| Group | Pairs | Patients | Bias % (CI) | MARD % (CI) | 20/20 % | Parkes A+B % |
|---|---|---|---|---|---|---|
| All | 4,012 | 98 | -7.4 (-10.7 to -4.5) | 13.9 (12.2 to 16.1) | 76.8 | 99.7 |
| T1DM | 750 | 10 | -13.3 (-22.3 to -3.2) | 18.4 (11.8 to 24.6) | 62.4 | 99.5 |
| T2DM | 3,262 | 88 | -6.1 (-9.1 to -3.5) | 12.9 (11.6 to 14.4) | 80.1 | 99.8 |

By the average of CGM and meter (bias %, MARD %, pairs, patients): 70-180: -6.9 (CI -10.7 to -3.7), 14.2, 2,697, 95. 181-250: -8.3, 13.1, 912, 78. >250: -8.2, 12.2, 353, 51.
Low bins are not estimable: under 54 has 6 pairs from 5 patients (bias CI -24 to +20 %); 54-69 has 44 pairs from 17 patients (bias -15.2 %, CI -29 to +7). The flash sensor reads 7 to 8 % low at every level where we can measure, with 68 % of pairs below the meter. Timing slack is up to 7.5 min (fingerstick written on the nearest 15-min row).

## 12. What changed vs RESULTS.md and why

- RESULTS.md numbers reproduce exactly (set E0: 475,502 pairs, MARD 10.4 %, bias -4.0 mg/dL, Parkes 88.1 / 10.9 / 0.8 / 0.1 / 0.01; MARD by reference 41.8 % under 54 and 18.7 % at 54-69; bias by average -6.6 % and -4.8 %).
- Headline MARD moves from 10.4 % to 13.8 %. Table in section 3: 0.2 points from the study window, 1.7 from dropping pump BG entries (CGM values typed into pumps), 1.4 from dropping calibration fingersticks, 0.5 from the CGM+BGM arm and randomised phase.
- The low-range bias by average is unchanged in direction: the G4 reads 3 to 5 % low under 70 mg/dL, now with CIs that exclude zero.
- New: CIs on everything, median ARD, 15/15 and 40/40, iCGM table, misclassification rates, hypo detection, repeated-measures Bland-Altman, meter sensitivity, published comparison, Shanghai CIs.
- Bins now put exactly 180 and 250 mg/dL in the lower range, as the labels say (preprocess.py puts them in the upper range). Effect: last digit at most.

## 13. Limits

- The reference is a home meter (Contour Next), not lab blood. Our MARD includes meter error (section 9).
- Fingersticks are not random samples. People test when they feel low or doubt the sensor. Detection rates describe tested moments.
- Pump BG entries were dropped as a whole. Some were real fingersticks that never reached the meter log. We lose pairs, not validity.
- Set A has 77 people, so its CIs are wide (MARD 12.3 to 15.7). Set B (226 people) gives the same numbers with tighter CIs.
- Binning by one device creates a fake bias. Table 5b (by CGM value) is for "what the patient sees" only; use 5a for the sensor's true bias.
- Meter and receiver clocks are separate, and the sensor lags blood by 5 to 10 min. Pairs during fast change carry lag error that looks like bias (error_drivers.py).
- Devices are a 2015 Dexcom G4 and a 2021 Libre H. The recalled sensor is the Libre 3. Results transfer only in kind, not in number.
- People are White, insured, well-controlled adult pump users (REPLACE-BG) or older Chinese inpatients (Shanghai).
- Pairs where the person also used the value to dose (pump copies of meter readings) show lower error (10.7 % vs 13.8 %). guess: routine pre-meal checks happen at calmer glucose than symptom-driven checks. Not analysed further here.

## 14. How to run

From the repo root, with the cache built (preprocess.py builds it on first use, about 40 s):
`python analysis/accuracy_v2.py "Uncommitted Data/Raw Data Dump" analysis`
Runtime: 5 s (cache loads in 1 s; the bootstrap uses per-person sums, so 1,000 resamples cost almost nothing). An optional third argument writes every table as markdown.
