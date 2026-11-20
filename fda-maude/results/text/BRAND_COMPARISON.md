# Brand comparison: wrong-reading complaints by brand, and by patient age and sex

Date: 2026-11-06. Made by `scripts/brand_comparison.py` from the full text-extraction run (prompt v3, `TEXT_RESULTS.md`). Tables: `tables/g_*.csv` (markdown copies in `tables/g_key_tables.md`; key numbers in `tables/g_brand_comparison_stats.json`). Figures: `figures/t7_brand_error_sizes.png` to `t10_demographics.png`.

Read this first: MAUDE counts and shares reflect who reports, what they report and how each maker writes and codes its reports. They are not failure rates. Medtronic rows carry a caution label: most Medtronic sensor reports sit under pump codes (undercount) and Medtronic had the weakest validation (kappa about 0.6).

## Summary

1. Comparison set: 39,667 serious wrong-reading reports (Abbott 22,935; Dexcom 14,911; Senseonics 1,014; Medtronic 757, caution) and 17,573 of them state both the sensor and the meter value (a "pair").
2. The size of the error is the same for Abbott and Dexcom: median absolute error 86 % vs 87 % of the meter value (Cliff's delta 0.01 = no difference). Senseonics errors are smaller (66 %; delta 0.27, small).
3. The direction differs: Abbott pairs read low in 58 %, Dexcom in 44 % (14 points apart, 95 % CI 12 to 15). This holds outside the recall windows (+15 points), in Abbott prose-only reports (+15) and in 7 of 9 years (not 2021, not 2026). It shrinks to +4 points after the Nov 2025 recall and to +2 points in 2026, because Dexcom G7 complaints also moved to reads-low.
4. Where the true glucose was differs most: Dexcom complaints are about hidden lows (meter under 70 in 46 % vs 28 % for Abbott; -18 points, CI -19 to -16). Abbott complaints are about false lows (sensor under 70 while the meter was not: 36 % vs 17 %). This holds in every period and in both Abbott text forms.
5. Most other brand differences are reporting style, not failure: FDA outcome codes (Abbott codes "Required Intervention" in 81 % of reports, Dexcom in 4 %; Dexcom codes "Other" in 91 %), fingerstick mentions (53 vs 81 %), stated Parkes zones (Abbott only C to E), filled age (19 vs 93 %). Deaths are the same (0.2 vs 0.1 %).
6. Demographics: age is filled in 49 % and sex in 41 % of the reports, almost all of them Dexcom reports. Where filled: median age 54, children under 18 are 12 %, 51 % female. Children's complaints read low more often (55 % vs 43 % for 65+) and end in hypoglycaemia more often (20 % vs 11 %). Sex makes no practical difference (every effect negligible).

## 1. Words used here

- Wrong-reading report = a report whose fault is a wrong reading, by the text (the model's fault type is reads low, reads high, erratic or stuck) OR by the FDA problem codes (the family "Wrong readings (accuracy)"). Serious = FDA death and injury reports. Sample = the weighted random sample of malfunction reports.
- Pair = a report that states both the sensor value and the meter (fingerstick) value. Error = sensor minus meter, in mg/dL and as % of the meter value. Negative = the sensor read low. Direction is always taken from the two numbers, never from the model's label (the label is wrong for 40 % of Dexcom reads-low pairs, `TEXT_RESULTS.md` s3).
- Meter band = where the true glucose was: under 54, 54 to 69, 70 to 180, 181 to 250, over 250 mg/dL. Hidden low = meter under 70. False low = sensor under 70 while the meter was not.
- Median = the middle value. IQR = the middle half (25th to 75th percentile). Percentile = the value below which that share of pairs fall.
- p = the chance of seeing a difference this big if the brands were the same. With tens of thousands of reports almost everything is "p < 0.001", so the effect size matters more.
- Effect size = how big the difference is, on a fixed scale. Cliff's delta (for sizes): -1 to +1; 0 = no difference; under 0.15 negligible, 0.15 to 0.33 small, 0.33 to 0.47 medium, above 0.47 large. Cramer's V (for shares across several groups): 0 to 1; under 0.1 negligible, 0.1 to 0.3 small, 0.3 to 0.5 medium. Risk difference = share A minus share B, in percentage points.
- CI = 95 % confidence interval: the range the true difference most likely sits in. Bootstrap = the CI is found by re-drawing the reports at random 1,000 times (seed 20261106).
- Tests: Mann-Whitney compares two groups of numbers; Kruskal-Wallis compares several; chi-square compares shares. None assumes a bell curve. No test is run on a group under 20 reports ("too few").
- Parkes zone = error-grid zone A (harmless) to E (dangerous), computed from the pair with the type 1 grid; "stated" = the zone the maker wrote in the text.
- Template = Abbott's fixed sentence form ("the sensor read X compared to Y, Parkes zone Z"). Prose = everything else. Dexcom, Medtronic and Senseonics never use a template; some of their prose matches a loose "CGM value vs BG value" pattern, which is still prose.
- Recall windows, by the date FDA received the report: W1 = 2024-07-24 to 2025-01-23 (six months from the Libre 3 falsely-high recall); W2 = 2025-11-24 onward (the Libre 3 falsely-low recall, to the 2026-07-21 text cut-off). Texts arrive months after the event, so the windows mark reporting time, not failure time.

## 2. The comparison set

| Brand | Reports in run set | Wrong by text | Wrong by code | Either (the set) | % of reports | Pairs in the set | % of set with a pair |
|---|---|---|---|---|---|---|---|
| Abbott | 74,657 | 20,694 | 22,506 | 22,935 | 30.7 | 7,470 | 32.6 |
| Dexcom | 32,045 | 11,845 | 14,109 | 14,911 | 46.5 | 9,189 | 61.6 |
| Medtronic (caution) | 8,660 | 470 | 655 | 757 | 8.7 | 379 | 50.1 |
| Senseonics (Eversense) | 2,878 | 634 | 979 | 1,014 | 35.2 | 532 | 52.5 |
| Other makers (LifeScan, Animas, ...) | 222 | 11 | 48 | 50 | 22.5 | 3 | 6.0 |
| All serious | 118,462 | 33,654 | 38,297 | 39,667 | 33.5 | 17,573 | 44.3 |
| Sample (weighted), Abbott | 843 | 478 | 797 | 797 (97.4 % weighted) | 97.4 | 255 | 32.0 |
| Sample (weighted), Dexcom | 4,574 | 40 | 623 | 634 (14.5 % weighted) | 14.5 | 31 | 4.9 |

- Text and codes agree: 81 % of the set is flagged by both. Text-only 3.5 %, code-only 15 %.
- Senseonics (the implanted Eversense sensor) has enough reports for its own column. It was "Other" in `TEXT_RESULTS.md`.
- 97 % of all plausible pairs fall inside the set (the rest are reports with two numbers but a different fault type and no wrong-reading code).
- Of the pairs, 2,982 Abbott pairs come from the template and 4,488 from prose; every other brand's pairs are prose.

## 3. Error size and direction (figure t7)

Serious pairs. Median (IQR). Tests across the four brands: Kruskal-Wallis, all p < 0.001; the effect size (epsilon squared) is 0.002 to 0.08, which is small, because the distributions overlap a lot.

| Brand | Pairs | Error, mg/dL | Error, % of meter | Absolute error, % | Sensor read low | Sensor read high | Median sensor / meter, mg/dL |
|---|---|---|---|---|---|---|---|
| Abbott | 7,470 | -67 (-280 to +96) | -47 (-80 to +146) | 85.5 | 57.8 % | 41.8 % | 91 / 167 |
| Dexcom | 9,189 | +29 (-217 to +77) | +44 (-64 to +172) | 86.7 | 43.8 % | 55.4 % | 110 / 95 |
| Medtronic (caution) | 379 | 0 (-220 to +73) | 0 (-63 to +166) | 83.3 | 48.8 % | 49.1 % | 110 / 124 |
| Senseonics | 532 | -22 (-105 to +60) | -19 (-53 to +117) | 65.5 | 54.1 % | 45.3 % | 105 / 99 |
| All | 17,573 | -5 (-244 to +81) | -5 (-73 to +160) | 85.7 | 50.2 % | 49.2 % | 102 / 130 |

The overall error is two-humped (one hump near -80 %, one from +100 to +300 %), so the overall median mostly says which hump is bigger. Read the two directions separately:

| Brand | Reads low: pairs | Error, % of meter | Error, mg/dL | Sensor / meter | Reads high: pairs | Error, % of meter | Error, mg/dL | Sensor / meter |
|---|---|---|---|---|---|---|---|---|
| Abbott | 4,315 | -77 (-86 to -60) | -240 (-407 to -112) | 60 / 318 | 3,126 | +191 (+100 to +400) | +120 (+60 to +225) | 202 / 52 |
| Dexcom | 4,029 | -69 (-85 to -48) | -266 (-430 to -119) | 86 / 420 | 5,088 | +152 (+83 to +300) | +70 (+41 to +128) | 122 / 40 |
| Medtronic (caution) | 185 | -64 (-80 to -44) | -220 (-360 to -100) | 91 / 400 | 186 | +170 (+100 to +270) | +74 (+54 to +120) | 121 / 47 |
| Senseonics | 288 | -51 (-66 to -37) | -97 (-171 to -46) | 78 / 208 | 241 | +126 (+75 to +211) | +63 (+42 to +101) | 113 / 50 |

Pairwise tests, Abbott against each other brand (serious pairs; Mann-Whitney; CIs by bootstrap). Full table with every pair of brands: `g_brand_error_pairwise.csv`.

| Measure | Abbott | Other brand | Median difference (CI) | Cliff's delta (CI) | Size | p |
|---|---|---|---|---|---|---|
| Absolute error, % | 85.5 | Dexcom 86.7 | -1.1 (-2.2 to -0.2) | 0.01 (0.00 to 0.03) | none | 0.15 |
| Absolute error, % | 85.5 | Senseonics 65.5 | +20.0 (+15.4 to +24.8) | 0.27 (0.22 to 0.33) | small | < 0.001 |
| Reads-low error, % | -76.8 | Dexcom -69.2 | -7.6 (-9.0 to -6.2) | -0.15 (-0.17 to -0.12) | small | < 0.001 |
| Reads-low error, % | -76.8 | Medtronic -64.0 | -12.8 (-16.0 to -7.3) | -0.25 (-0.34 to -0.17) | small | < 0.001 |
| Reads-low error, % | -76.8 | Senseonics -51.3 | -25.5 (-29.2 to -22.6) | -0.56 (-0.61 to -0.52) | large | < 0.001 |
| Reads-low error, mg/dL | -240 | Dexcom -266 | +26 (+14 to +41) | 0.05 (0.03 to 0.07) | negligible | < 0.001 |
| Reads-high error, % | +191 | Dexcom +152 | +40 (+27 to +49) | 0.12 (0.10 to 0.15) | negligible | < 0.001 |
| Reads-high error, mg/dL | +120 | Dexcom +70 | +50 (+46 to +57) | 0.31 (0.28 to 0.33) | small | < 0.001 |
| Meter value, mg/dL | 167 | Dexcom 95 | +72 (+63 to +82) | 0.14 (0.12 to 0.16) | negligible | < 0.001 |
| Share reading low | 58.0 % | Dexcom 44.2 % | +13.8 points (+12.4 to +15.3) | Cramer's V 0.13 (4 brands) | small | < 0.001 |
| Share reading low | 58.0 % | Senseonics 54.4 % | +3.6 points (-0.6 to +8.0) | | | 0.11 |

- Abbott and Dexcom complaints are equally far off. What differs is the direction and the glucose level at which the sensor failed.
- Abbott reads-low errors are a little deeper in % (-77 vs -69) but smaller in mg/dL (-240 vs -266), because Dexcom reads-low pairs sit at higher true glucose (meter 420 vs 318).
- Abbott reads-high errors are bigger in mg/dL (+120 vs +70, small effect) because the Abbott sensor showed a higher number (202 vs 122) at about the same true glucose (52 vs 40).
- Senseonics is the one brand with clearly smaller reported errors in both directions (reads-low -51 % vs -77 %; delta -0.56, large). Senseonics pairs have the meter nearer to normal (median 99 mg/dL) and only 16 % land in Parkes D or E (Abbott 44 %).
- Medtronic (caution): 379 pairs; direction 50/50; reads-low -64 %. 44 % of its CGM-coded wrong-reading reports come from patients or family (voluntary reports), against 2 to 6 % for the other brands, so it is a different reporting channel as well as an undercount.

## 4. Where the glucose was, Parkes zone, wear day (figure t8)

Shares of serious pairs (chi-square across the four brands; V = Cramer's V).

| Measure | Abbott (7,470) | Dexcom (9,189) | Medtronic (379) | Senseonics (532) | Test |
|---|---|---|---|---|---|
| Meter under 54 | 21.8 % | 39.7 % | 37.7 % | 26.9 % | meter band: V 0.13 small, p < 0.001 |
| Meter 54 to 69 | 6.3 % | 6.0 % | 4.7 % | 13.0 % | |
| Meter 70 to 180 | 24.7 % | 15.2 % | 16.1 % | 27.4 % | |
| Meter 181 to 250 | 10.2 % | 5.3 % | 5.5 % | 12.2 % | |
| Meter over 250 | 37.0 % | 33.8 % | 35.9 % | 20.5 % | |
| Sensor under 54 | 20.8 % | 13.7 % | 14.5 % | 13.5 % | sensor band: V 0.10, p < 0.001 |
| Sensor 70 to 180 | 36.4 % | 48.2 % | 55.9 % | 53.9 % | |
| Hidden low (meter under 70) | 28.1 % | 45.7 % | 42.5 % | 39.8 % | Abbott vs Dexcom -17.6 points (-19.0 to -16.2) |
| False low (sensor under 70, meter not) | 35.6 % | 17.3 % | 14.5 % | 23.9 % | +18.3 points (+16.9 to +19.5) |
| Missed low (meter under 70, sensor not) | 26.1 % | 39.1 % | 40.1 % | 35.7 % | -13.0 points (-14.4 to -11.6) |
| Parkes D or E, computed | 43.6 % | 35.4 % | 34.0 % | 16.0 % | zone: V 0.09, p < 0.001; A vs D +8.2 points (+6.7 to +9.6) |
| Parkes zone stated by the maker: A or B | 0.2 % (of 4,175) | 27.9 % (of 8,325) | 2 reports | none | V 0.35 medium, p < 0.001 |
| Stated zone C / D / E | 46.6 / 47.8 / 5.4 % | 29.5 / 35.7 / 6.9 % | | | |
| Wear day stated | 2,197 reports | 378 | 6 | 20 | |
| Wear day 1 | 15.8 % | 7.9 % | | | wear day: V 0.17 small, p < 0.001 (3 brands) |
| Wear days 2 to 3 / 4 to 7 | 20.7 / 32.9 % | 24.9 / 40.5 % | | | |
| Wear days 8 to 10 / 11 to 14 | 16.5 / 13.3 % | 26.2 / 0.3 % | | | |

- The Abbott picture: a false low at a high true glucose (median meter 318 when reading low). The Dexcom picture: a hidden low (true glucose under 54 in 40 % of pairs, the sensor showing 70 to 180 in 48 %). Medtronic looks like Dexcom. Senseonics sits between.
- Stated Parkes zones differ by brand because the makers grade differently, not because the pairs differ: Abbott never states A or B, Dexcom does in 28 %. The computed zones (same rule for every brand) differ far less (V 0.09).
- Wear day: Abbott over-reports day 1 (16 % of reports with a day, flat expectation 7 % for a 14-day sensor), Dexcom does not (8 % vs a flat 10 % for 10 days). Abbott wear days come from the template (36 % of template reports state one, 6 % of prose reports), so this is a template feature as much as a sensor feature. Sensor lives differ, so the bands are not directly comparable.

## 5. Fingerstick, user action, outcome and FDA codes

Shares of serious wrong-reading reports (all, not only pairs). Chi-square across the four brands.

| Measure | Abbott (22,935) | Dexcom (14,911) | Medtronic (757) | Senseonics (1,014) | Test (V) | Abbott vs Dexcom, points (CI) |
|---|---|---|---|---|---|---|
| Fingerstick check mentioned: yes | 53.4 % | 80.5 % | 85.9 % | 67.2 % | 0.21 small | -27.1 (-28.1 to -26.2) |
| Fingerstick: not stated | 39.5 % | 12.2 % | 9.6 % | 23.4 % | | |
| Ate carbs | 30.5 % | 34.8 % | 23.5 % | 31.6 % | user action 0.14 small | -4.3 (-5.2 to -3.3) |
| Took insulin | 10.4 % | 5.4 % | 12.3 % | 11.9 % | | +5.0 (+4.5 to +5.5) |
| Sought care | 45.8 % | 47.6 % | 26.6 % | 12.4 % | | -1.7 (-2.7 to -0.6) |
| User action: none | 4.7 % | 5.8 % | 24.6 % | 28.1 % | | |
| Outcome (model): none | 12.8 % | 6.7 % | 18.1 % | 32.4 % | outcome 0.17 small | |
| Outcome: hypoglycaemia | 11.3 % | 12.5 % | 33.3 % | 46.5 % | | -1.3 (-1.9 to -0.6) |
| Outcome: hospital or ER (= sought medical care) | 66.7 % | 77.5 % | 46.9 % | 17.5 % | | -10.8 (-11.7 to -9.9) |
| Outcome: death | 0.1 % | 0.1 % | 0.0 % | 0.1 % | | +0.1, p 0.06 |
| FDA event type: Death | 0.2 % (56) | 0.1 % (21) | 0.1 % (1) | 0.1 % (1) | 0.01 negligible, p 0.14 | +0.1 (0.0 to +0.2), p 0.03 |
| FDA code: Required Intervention | 80.5 % | 3.8 % | 15.6 % | 0.2 % | 0.76 large | +76.8 |
| FDA code: Hospitalization | 7.9 % | 26.9 % | 34.2 % | 12.2 % | 0.26 small | -19.0 (-19.8 to -18.2) |
| FDA code: Life Threatening | 0.8 % | 4.6 % | 2.2 % | 0.7 % | 0.13 small | -3.8 (-4.2 to -3.5) |
| FDA code: Other | 11.5 % | 91.2 % | 28.8 % | 44.0 % | 0.77 large | |
| FDA code: none stated | 7.1 % | 3.0 % | 25.2 % | 43.5 % | 0.27 small | |
| Reporter: patient or family (FDA occupation field) | 2.2 % | 6.3 % | 44.0 % | 0.1 % | 0.18 small | |

- The largest effects in the whole memo are the FDA outcome codes (V 0.76 to 0.77). They are coding habits: Abbott files almost everything as "Required Intervention", Dexcom as "Other". `TEXT_RESULTS.md` s7 showed that FDA puts ER and clinic visits under "Required Intervention"; Dexcom evidently does not. Do not read the Hospitalization gap (8 vs 27 %) as a harm difference.
- Deaths do not differ by brand: 56 Abbott and 21 Dexcom reports in the set, 0.2 vs 0.1 %. The p of 0.03 is driven by the large n; the difference is one tenth of a point.
- Fingerstick mentions and "sought care" follow the text form (section 7a): Abbott template reports mention a fingerstick in 94 %, Abbott prose in 47 %, Dexcom in 81 %.
- Senseonics reports are different in kind: outcome none in 32 %, hypoglycaemia in 47 %, sought care in 12 %. guess: Eversense is fitted and followed in clinics, so its complaints come through the clinic with a glucose event recorded but little else.

## 6. Report year and the recall windows (figure t9)

Serious wrong-reading reports and pairs per year (date received). W1 and W2 mark the recall windows. Full table: `g_brand_by_year.csv`; per-year Abbott vs Dexcom tests: `g_brand_by_year_tests.csv`.

| Year | Abbott reports | Abbott pairs read low | Dexcom reports | Dexcom pairs read low | Senseonics pairs read low | Abbott minus Dexcom, points (CI) |
|---|---|---|---|---|---|---|
| 2018 | 452 | 46.6 % | 479 | 25.1 % | | +21 (+14 to +30) |
| 2019 | 782 | 53.3 % | 646 | 33.9 % | | +19 (+13 to +23) |
| 2020 | 800 | 59.0 % | 514 | 39.0 % | | +20 (+13 to +28) |
| 2021 | 1,807 | 49.0 % | 672 | 45.2 % | | +4 (-2 to +10), p 0.19 |
| 2022 | 2,361 | 46.3 % | 1,015 | 34.3 % | | +12 (+7 to +16) |
| 2023 | 3,567 | 47.7 % | 1,996 | 32.0 % | 36.1 % | +16 (+11 to +19) |
| 2024 (W1 starts July) | 4,215 | 54.0 % | 2,500 | 43.6 % | 46.5 % | +10 (+6 to +14) |
| 2025 (W1 ends Jan; W2 starts Nov) | 4,437 | 72.2 % | 4,099 | 52.8 % | 69.0 % | +19 (+16 to +22) |
| 2026 to July (W2) | 4,497 | 64.4 % | 2,319 | 62.0 % | 64.0 % | +2 (-1 to +6), p 0.23 |

Abbott vs Dexcom inside and outside the windows (serious pairs):

| Period | Pairs A / D | Read low A / D | Difference, points (CI) | Hidden low (meter under 70) A / D | Difference (CI) | Reads-low error A / D | Cliff's delta (CI) |
|---|---|---|---|---|---|---|---|
| Outside the windows | 4,933 / 6,888 | 54.9 / 39.8 % | +15.1 (+13.4 to +16.9) | 30.9 / 49.6 % | -18.7 (-20.5 to -17.0) | -78.0 / -68.0 % | -0.19 (-0.21 to -0.16) |
| W1 (Jul 2024 recall, falsely high) | 683 / 751 | 58.6 / 48.5 % | +10.1 (+4.5 to +15.1) | 29.1 / 40.1 % | -10.9 (-15.8 to -5.8) | -76.8 / -73.2 % | -0.09 (-0.17 to -0.01) |
| W2 (Nov 2025 recall, falsely low) | 1,854 / 1,550 | 66.0 / 61.6 % | +4.4 (+1.2 to +7.6) | 20.3 / 31.1 % | -10.8 (-13.5 to -7.8) | -73.6 / -71.4 % | -0.06 (-0.11 to -0.01) |
| All time | 7,470 / 9,189 | 58.0 / 44.2 % | +13.8 (+12.3 to +15.2) | 28.1 / 45.7 % | -17.6 (-19.0 to -16.2) | -76.8 / -69.2 % | -0.15 (-0.17 to -0.12) |

- The direction gap is real outside the windows and in 7 of 9 years, so it is not a recall artefact. But it is not fixed either: every brand's complaints moved toward reads-low in 2025 and 2026 (Dexcom from 32 % in 2023 to 62 % in 2026; Senseonics from 36 % to 64 %). In 2026 the brands are level.
- The hidden-low gap (Dexcom complaints at a true glucose under 70) is the steadiest brand difference: -11 to -19 points in every period.
- Report volumes: Abbott's wrong-reading reports grew every year and did not jump in the windows (4,215 in 2024, 4,437 in 2025, 4,497 in the first seven months of 2026). Dexcom's jumped in 2025 (4,099 vs 2,500). guess: for Dexcom the 2025 jump is the G7 roll-out plus a change in Dexcom's coding ("Low Readings" appears from mid-2025, `report_results.md` f), not the Abbott recall.

Product lines (serious pairs; `g_product_lines.csv`): the newest generation of each brand leans low.

| Line | Pairs | Read low | Median error, % | Hidden low |
|---|---|---|---|---|
| Libre 3 Plus | 1,061 | 71.4 % | -63 | 15.6 % |
| Libre 3 | 1,321 | 67.0 % | -67 | 23.4 % |
| Libre 2 Plus | 650 | 63.5 % | -63 | 24.0 % |
| Libre 2 | 2,462 | 47.8 % | +31 | 35.6 % |
| Libre 14 day | 1,499 | 55.9 % | -37 | 29.9 % |
| Dexcom G7 | 3,760 | 55.0 % | -29 | 36.1 % |
| Dexcom G6 | 4,499 | 38.8 % | +66 | 49.8 % |
| Dexcom G5 | 580 | 29.5 % | +108 | 64.1 % |
| Eversense | 532 | 54.1 % | -19 | 39.8 % |

- Libre 3 vs Libre 2: +19 points reading low (CI +16 to +22). G7 vs G6: +16 points (+14 to +18). Libre 3 vs G7: +12 (+9 to +15). Libre 2 vs G6: +9 (+7 to +11). So about half of the Abbott-vs-Dexcom direction gap is "Abbott vs Dexcom within a generation" and the rest is the generation mix in each brand's reports.

## 7. Confound checks

### 7a. Abbott's template vs prose

Abbott pairs by text form, against Dexcom (all prose). Tests: `g_confound_template_tests.csv`.

| Group | Pairs | Error, % (IQR) | Reads-low error, % | Read low | Hidden low | Meter over 250 | Parkes D or E |
|---|---|---|---|---|---|---|---|
| Abbott, template | 2,982 | -50 (-80 to +150) | -78.0 | 56.3 % | 28.1 % | 36.7 % | 43.0 % |
| Abbott, prose | 4,488 | -46 (-80 to +142) | -75.7 | 59.1 % | 28.1 % | 37.3 % | 44.0 % |
| Dexcom, prose | 9,189 | +44 (-64 to +172) | -69.2 | 44.2 % | 45.7 % | 33.8 % | 35.4 % |
| Senseonics, prose | 532 | -19 (-53 to +117) | -51.3 | 54.4 % | 39.8 % | 20.5 % | 16.0 % |

- Template vs prose within Abbott: error delta 0.00 (CI -0.03 to +0.02, p 0.86); reads-low error -78.0 vs -75.7 (delta -0.06, negligible); read low 56.3 vs 59.1 % (-2.8 points, CI -5.3 to -0.5); hidden low identical. The template does not change the numbers.
- Abbott prose vs Dexcom: read low +14.9 points (CI +13.1 to +16.6); hidden low -17.6 (-19.2 to -15.9); reads-low error delta -0.12. The brand differences of sections 3 and 4 survive with the template removed.
- What the template does change is everything around the numbers (all Abbott wrong-reading reports, `g_confound_template_reports.csv`):

| Share of reports | Abbott template (3,098) | Abbott prose (19,837) | Dexcom (14,911) |
|---|---|---|---|
| States a pair | 98.1 % | 23.2 % | 63.1 % |
| States a Parkes zone | 71.6 % | 9.9 % | 55.8 % |
| States a wear day | 35.8 % | 5.5 % | 2.5 % |
| Fingerstick check: yes | 93.6 % | 47.1 % | 80.5 % |
| Took insulin | 16.4 % | 9.5 % | 5.4 % |
| Sought care | 36.2 % | 47.4 % | 47.6 % |
| Outcome: hospital or ER | 69.6 % | 66.3 % | 77.5 % |
| Age filled | 14.7 % | 19.8 % | 93.2 % |
| Median text length, characters | 3,153 | 2,767 | 1,350 |

- So the coverage gaps between brands (pairs, zones, wear days, fingerstick) are mostly writing form. Outcomes and actions move much less with the form.

### 7b. Serious reports vs the weighted malfunction sample

| Group | Wrong-reading reports (weighted) | Pairs (weighted) | Error, % (IQR) | Read low | Hidden low |
|---|---|---|---|---|---|
| Serious, Abbott | 22,935 | 7,470 | -47 (-80 to +146) | 57.8 % | 28.1 % |
| Serious, Dexcom | 14,911 | 9,189 | +44 (-64 to +172) | 43.8 % | 45.7 % |
| Sample, Abbott | 797 (376,494) | 255 (107,133) | -65 (-72 to +84) | 73.3 % | 6.3 % |
| Sample, Dexcom | 634 (349,517) | 31 (15,472) | -45 (-58 to +29) | 68.6 % | 4.3 % |
| Sample, Medtronic (caution) | 40 (5,343) | 24 (2,907) | -66 (-73 to -50) | 91.6 % | 3.7 % |

- Tests on the sample rows (unweighted; 255 Abbott vs 31 Dexcom pairs): error delta -0.21 (CI -0.38 to -0.05, p 0.055); read low +2.5 points (CI -15 to +20, p 0.78).
- Verdict: the sample cannot confirm or deny the brand differences. Dexcom malfunction texts are one-line boilerplate (31 pairs stand for 15,000 reports). What the sample does show is that malfunction complaints of both brands lean low (69 to 73 %) with the true glucose rarely under 70 (4 to 6 %): a reads-low sensor that caused no harm. The hidden-low complaints that set Dexcom apart in the serious tier are, by definition, injury reports.
- The model's direction label cannot be used in the sample instead of the numbers: it says reads-low for 86 % of Abbott and 59 % of Dexcom sample reports with a direction label, but 40 % of Dexcom reads-low pairs are mislabelled (`TEXT_RESULTS.md` s3).

### 7c. Year

See section 6. The direction gap holds outside the windows (+15 points) and in 7 of 9 years; the hidden-low gap holds in every period; the reads-low error gap is small outside the windows (delta -0.19) and shrinks inside W2 (delta -0.06).

## 8. Demographics (figure t10)

### 8a. How much is missing

Fill rates in the serious wrong-reading set (`g_demographics_fill.csv`):

| Cut | Group | n | Age filled | Sex filled | Both |
|---|---|---|---|---|---|
| Brand | Abbott | 22,935 | 19.1 % | 18.2 % | 9.2 % |
| Brand | Dexcom | 14,911 | 93.2 % | 78.1 % | 74.5 % |
| Brand | Medtronic (caution) | 757 | 88.0 % | 23.5 % | 23.5 % |
| Brand | Senseonics | 1,014 | 47.3 % | 35.2 % | 34.3 % |
| All | | 39,667 | 49.1 % | 41.2 % | 34.7 % |
| FDA event type | Injury | 39,588 | 49.1 % | 41.2 % | 34.7 % |
| FDA event type | Death | 79 | 36.7 % | 39.2 % | 34.2 % |
| Brand x event | Abbott deaths / injuries | 56 / 22,879 | 16.1 / 19.2 % | 16.1 / 18.2 % | |
| Brand x event | Dexcom deaths / injuries | 21 / 14,890 | 85.7 / 93.2 % | 95.2 / 78.1 % | |
| FDA code | Required Intervention | 19,184 | 19.3 % | 15.6 % | 6.9 % |
| FDA code | Hospitalization | 6,201 | 72.5 % | 62.6 % | 58.0 % |
| Year received | 2018 / 2020 / 2022 / 2024 / 2026 | | 84.5 / 76.9 / 35.1 / 39.7 / 45.8 % | 0.0 / 0.4 / 54.2 / 44.3 / 48.5 % | |
| Sample (weighted) | Abbott / Dexcom | 797 / 634 | 4.1 / 95.9 % | 5.7 / 56.3 % | |

- Fill is a brand habit. Dexcom fills age in 93 % of reports, Abbott in 19 %. So "reports with an age" are 71 % Dexcom and "reports without" are 92 % Abbott. Every cut below is therefore mostly a Dexcom cut, and we show Abbott and Dexcom separately where the numbers allow.
- Deaths are not filled more often than injuries. They are filled less (37 vs 49 % for age), because deaths are mostly Abbott reports. Within a brand the death and injury fill rates are alike.
- The sex field was empty before 2021 (0 % in 2018 to 2020) and is filled in about half of the reports since 2022. The age fill rate fell from 85 % (2018) to 35 to 50 % as Abbott's share of the reports grew.
- Filled vs unfilled reports, within a brand (`g_demographics_filled_vs_unfilled_tests.csv`): Abbott pairs with an age have a median error of -43 % vs -50 % without (delta 0.07, negligible); Dexcom +47 vs +31 % (delta 0.03, p 0.18). Death shares do not differ within a brand (Abbott 0.20 vs 0.25 %, p 0.56; Dexcom 0.13 vs 0.29 %, p 0.18). The filled reports look like the unfilled ones of the same brand.

### 8b. Age and sex by brand

Reports with the field filled (`g_demographics_age_sex_by_brand.csv`).

| Brand | With an age | Median age (IQR) | Under 18 | 18 to 39 | 40 to 64 | 65 and over | With a sex | Female |
|---|---|---|---|---|---|---|---|---|
| Abbott | 4,391 | 58 (42 to 69) | 9.3 % | 13.2 % | 41.7 % | 35.8 % | 4,169 | 46.6 % |
| Dexcom | 13,892 | 53 (32 to 67) | 13.2 % | 19.2 % | 38.3 % | 29.3 % | 11,650 | 52.9 % |
| Medtronic (caution) | 666 | 54 (39 to 64) | 5.7 % | 19.7 % | 49.7 % | 24.9 % | 178 | 50.6 % |
| Senseonics | 480 | 57 (43 to 64) | 1.5 % | 17.7 % | 57.1 % | 23.8 % | 357 | 48.2 % |
| All | 19,462 | 54 (35 to 67) | 11.7 % | 17.8 % | 39.9 % | 30.5 % | 16,356 | 51.1 % |

- Abbott patients are 5 years older than Dexcom patients (CI 4 to 6; Cliff's delta 0.12, negligible) and less often female (46.6 vs 52.9 %, -6.3 points, CI -8.1 to -4.7). Across the four brands: age Kruskal-Wallis p < 0.001 with epsilon squared 0.008; age-group mix V 0.07; sex V 0.06. All negligible in size.
- Senseonics has almost no children (1.5 %); Eversense is approved for adults.

### 8c. By age group

Serious wrong-reading reports with an age; pairs for the error columns (`g_demographics_by_group.csv`, tests in `g_demographics_by_group_tests.csv` and `_pairwise.csv`).

| Age group | Reports | Pairs | Error, % (IQR) | Read low | Hidden low | Meter over 250 | Fingerstick yes | Took insulin | Ate carbs | Outcome hypoglycaemia | Outcome hospital or ER | FDA death |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Under 18 | 2,286 | 1,373 | -32 (-71 to +138) | 54.6 % | 37.1 % | 45.9 % | 84.3 % | 13.1 % | 33.3 % | 19.6 % | 67.3 % | 0.04 % (1) |
| 18 to 39 | 3,471 | 2,030 | +26 (-66 to +148) | 47.7 % | 42.5 % | 39.0 % | 78.2 % | 6.7 % | 30.8 % | 14.5 % | 74.9 % | 0.2 % |
| 40 to 64 | 7,770 | 4,124 | +31 (-66 to +173) | 46.8 % | 42.4 % | 32.0 % | 73.8 % | 5.9 % | 33.3 % | 13.4 % | 71.0 % | 0.2 % |
| 65 and over | 5,935 | 3,205 | +50 (-62 to +200) | 42.6 % | 46.9 % | 27.4 % | 73.0 % | 5.6 % | 35.0 % | 11.4 % | 72.2 % | 0.2 % |

Tests across the four age groups (all brands): error Kruskal-Wallis p < 0.001, epsilon squared 0.005; direction chi-square V 0.07; meter band V 0.08; outcome V 0.06; death p 0.50. All negligible in size. Children vs 65 and over: read low +11.9 points (CI +8.8 to +15.1); hidden low -9.8 (-12.8 to -6.8); hypoglycaemia outcome +8.3 (+6.5 to +10.0); hospital or ER -4.8 (-6.9 to -2.6); took insulin +7.5; death -0.1 (p 0.21).

Within each big brand (read low, by age group):

| Brand | Under 18 | 18 to 39 | 40 to 64 | 65 and over | Chi-square |
|---|---|---|---|---|---|
| Abbott (1,650 pairs) | 49.0 % | 51.5 % | 58.4 % | 66.9 % | V 0.13 small, p < 0.001 |
| Dexcom (8,586 pairs) | 55.6 % | 46.8 % | 44.1 % | 36.6 % | V 0.12 small, p < 0.001 |

- Age moves the direction in opposite ways for the two brands. Older Abbott patients report false lows (67 % read low; the true glucose was 70 to 180 in 40 %). Older Dexcom patients report hidden lows (true glucose under 54 in 46 %; 37 % read low). guess: different users. Libre users check with a meter when the sensor says "LOW"; Dexcom users over 65 are more often on insulin and report the lows they did not see coming. The data cannot show this.
- Children: more fingersticks (84 %), more insulin given on a wrong reading (13 %; Abbott children 20 %), more hypoglycaemia outcomes (20 %), fewer medical visits (67 %). guess: parents check more and report more. One child death in the set.

### 8d. By sex

| Sex | Reports | Pairs | Error, % (IQR) | Absolute error, % | Read low | Hidden low | Outcome hypoglycaemia | Outcome hospital or ER | FDA death |
|---|---|---|---|---|---|---|---|---|---|
| Female | 8,362 | 4,433 | -21 (-70 to +146) | 83.0 | 52.1 % | 39.1 % | 11.6 % | 74.4 % | 0.19 % |
| Male | 7,994 | 4,123 | +20 (-69 to +158) | 84.6 | 48.6 % | 40.6 % | 12.2 % | 70.7 % | 0.19 % |

- Female vs male: error delta -0.03 (CI -0.05 to 0.00); absolute error delta -0.03; read low +3.5 points (CI +1.5 to +5.6); hidden low -1.5 (p 0.16); hospital or ER +3.7 (+2.4 to +5.0); hypoglycaemia -0.5 (p 0.29); death 0.0 (p 0.96). Within Abbott and within Dexcom the same (every V under 0.1). Sex makes no practical difference.

## 9. What this means

Real differences in what fails (they survive the template, year and within-generation checks):

1. Abbott and Dexcom complaints fail at different glucose levels. Abbott: the sensor shows a false low while the true glucose is high (median sensor 60, meter 318; false low in 36 % of pairs). Dexcom: the sensor shows a normal number while the true glucose is under 70 (hidden low in 46 %; 40 % under 54). Medtronic (caution) looks like Dexcom. This gap is -11 to -19 points in every period and in both Abbott text forms. For Phase 2 both faults matter: the Abbott fault wastes corrections and triggers carbs; the Dexcom fault hides lows.
2. The direction gap (Abbott 58 % read low, Dexcom 44 %) is real but moving. It holds in 7 of 9 years and outside the recall windows (+15 points), but each brand's newest sensor leans low (Libre 3: 67 %, G7: 55 %) and by 2026 the brands are level (64 vs 62 %). guess: the Nov 2025 recall changed what Abbott users report, and the G7 changed what Dexcom users report; Phase 2 should treat "reads low" as a current-generation fault for both brands, not an Abbott fault.
3. The size of the error does not differ between Abbott and Dexcom (absolute error 86 vs 87 %). Within the reads-low direction Abbott is a little deeper (-77 vs -69 %, small effect) and the gap shrinks in 2026. Senseonics errors are clearly smaller (-51 %; large effect) and rarely reach Parkes D or E (16 % vs 35 to 44 %). guess: an implanted, clinic-calibrated sensor with a different user group; or Senseonics' complaint texts record milder events because they come through clinics.

Differences in how brands write and code reports (do not read them as failure or harm differences):

4. FDA outcome codes: Abbott "Required Intervention" 81 % vs Dexcom 4 %; Dexcom "Other" 91 %; Hospitalization 8 vs 27 %; Life Threatening 0.8 vs 4.6 %. These are the biggest effects in the memo (V 0.76) and they are coding habits. Deaths, which both makers must code the same way, do not differ (0.2 vs 0.1 %).
5. Coverage: pairs (33 vs 62 % of reports), stated Parkes zones (Abbott only C to E; Dexcom A to E in 28 %), wear days (Abbott template only), fingerstick mentions (53 vs 81 %), age and sex (19 vs 93 %) all follow the writing form. Abbott's template mentions a fingerstick in 94 % of reports, Abbott's prose in 47 %.
6. The model's outcome "hospital or ER" (67 vs 78 %) partly follows the text: Dexcom's short texts name the ER visit; Abbott's longer texts describe the sensor. Treat the 11-point gap as reporting style until the pending 100-report human check says otherwise.
7. Medtronic (caution): 44 % of its CGM-coded wrong-reading reports are voluntary (patient or family), against 2 to 6 % elsewhere. Its numbers describe a different reporting channel on top of the undercount.

Demographics: the filled reports are a Dexcom cut with a fifth of Abbott. Within a brand the filled reports look like the unfilled ones, and deaths are not filled more often. Age matters a little (children: more reads-low, more hypoglycaemia outcomes, more insulin given; older Abbott users: more false lows; older Dexcom users: more hidden lows), sex not at all. No age or sex group has a different death share.

## 10. Caveats

- Reporting bias: these are complaint reports, not failure rates. Brand counts depend on how many sensors are worn, how each maker's complaint team writes, and recall news. Every brand result above carries this caveat.
- Medtronic: undercounted (pump codes) and weakest validation (kappa 0.62 to 0.63). Indicative only.
- Pairs: first pair only; values must appear word-for-word in the text; 421 implausible pairs dropped; "LOW" / "HI" display words are not pairs, which undercounts the most extreme reads-low cases (more so for Abbott, whose sensors show "LO" under 40 mg/dL).
- Direction comes from the numbers; the model's label is not used. The model's outcome and user-action fields have kappa about 0.75 to 0.77 and known weak spots (`VALIDATION.md`); the 100-report human check is still pending.
- Tests: with n in the thousands almost every p is under 0.001. Judge by the effect size and the CI. The bootstrap CIs assume the reports are independent; repeat reports about the same sensor are not removed.
- The sample has too few Dexcom pairs (31) to test brand differences. Tests on the sample are unweighted.
- Recall windows use the date FDA received the report. Texts arrive months late, so W2 is still filling and its numbers will change.
- Demographics: the fields are filled by the reporter; "filled" means mostly Dexcom; sex was not recorded before 2021. Deaths with an age: 29 reports. Age groups use the FDA age field converted to years (months, weeks and days converted; 110 and over dropped).

## 11. How to run and what is written

From the repo root (Windows: plain `python`): `python fda-maude/scripts/brand_comparison.py` (about 70 s; `--n-boot 200` for a quick test; all paths are options, see `--help`). Deterministic: seed 20261106; two runs give byte-identical tables.

Reads: `clean/text_extract_v3.jsonl`, `clean/run_set.csv.gz`, `clean/regex_run_set.csv`, `clean/serious.csv.gz` and `clean/sample_local.parquet` (age, sex, reporter), `results/report/tables/d_problem_family_mapping.csv`. Imports the loading code from `scripts/text_results.py`.

Writes (all in `results/text/`):

| File | What it holds |
|---|---|
| `tables/g_comparison_set_counts.csv`, `g_other_makers.csv` | the set, by brand and tier |
| `tables/g_brand_error_sizes.csv`, `_percentiles.csv`, `_bins.csv`, `_kruskal.csv`, `_pairwise.csv` | error sizes, full distribution, tests |
| `tables/g_brand_shares.csv`, `g_brand_share_tests.csv`, `g_brand_shares_pairwise.csv` | direction, bands, zones, wear day, fingerstick, actions, outcomes, FDA codes, reporter |
| `tables/g_confound_template_pairs.csv`, `_tests.csv`, `_reports.csv` | 7a |
| `tables/g_confound_serious_vs_sample.csv`, `_tests.csv` | 7b |
| `tables/g_brand_by_year.csv`, `_tests.csv`, `g_recall_windows.csv`, `_tests.csv`, `g_product_lines.csv`, `_tests.csv` | 6 and 7c |
| `tables/g_demographics_fill.csv`, `_age_sex_by_brand.csv`, `_tests.csv`, `_by_group.csv`, `_tests.csv`, `_pairwise.csv`, `_filled_vs_unfilled.csv`, `_tests.csv` | 8 |
| `tables/g_key_tables.md`, `tables/g_brand_comparison_stats.json` | markdown copies; key numbers |
| `figures/t7_brand_error_sizes.png`, `t8_brand_meter_bands.png`, `t9_brand_by_year.png`, `t10_demographics.png` | figures |
