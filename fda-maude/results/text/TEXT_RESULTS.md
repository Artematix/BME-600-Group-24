# Phase 1 text results: what the report texts say, and the join to Phase 2

Date: 2026-10-30. Made by `scripts/text_results.py` from the full text-extraction run (prompt v3). Tables: `tables/` (CSV; markdown copies in `tables/key_tables.md`). Figures: `figures/t1_*.png` to `t6_*.png`. Method: `../../METHODOLOGY.md`. Validation: `VALIDATION.md`. Run set: `RUN_SET.md`.

Words used here:
- Serious reports = FDA death and injury reports with text (118,462). Malfunction sample = 6,137 random malfunction reports; "weighted" means each one is scaled up to stand for all 2.92 million malfunction reports.
- Pair = a report that states both the sensor value and the meter (fingerstick) value. Error = sensor minus meter, in mg/dL and as % of the meter value. Negative = the sensor read low.
- Pattern layer = fixed text patterns (regex) that read the maker templates. Model = the local language model that fills the form. Final value = pattern value when the Abbott template matched (and for zone and wear day whenever a pattern found one), else the model value.
- Guard drop = a number the model wrote that does not appear in the text; it is deleted.
- Parkes zone = error-grid zone A (harmless) to E (dangerous). Lookup table = `analysis/simulation_v2_lookup_extended.csv` (bias -90 to +90 % in 2 % steps, made 2026-10-30; the base file `simulation_v2_lookup.csv` stops at -40 / +40 %), what a constant sensor bias does to decisions in the trial data (median person).
- Medtronic numbers carry a caution: most Medtronic sensor reports sit under pump codes (undercount), and Medtronic had the weakest validation (kappa about 0.6).

## 1. Run facts

| Item | Value |
|---|---|
| Reports processed | 124,599 (118,462 serious + 6,137 sample); 0 model errors, 0 retries |
| Wall-clock | 08:23:50 to 17:57:08 on 2026-10-30 = 9.55 h, one segment, no restart |
| Throughput | 217 reports per minute; latency per request mean 2.2 s (p90 2.8 s); 10.4 million output tokens, 301 tokens/s |
| Longest prompt | 5,889 tokens (context window 6,144, so no report was cut) |
| Guard drops | 4,324 reports (3.5 %): wear day 2,274, meter value 1,056, zone 808 (453 of these got the pattern-layer zone instead), sensor value 276 |
| Other checks | 26 sensor/meter role swaps flagged; 4,667 reports converted from mmol/L in code |
| Reports left out of the run set | serious: 5,135 too recent for text, 10 with no text (Abbott 2, Dexcom 2, other 6); sample: 31 of 6,168 with no text |

## 2. Coverage: what could be read (% of reports)

| Group | n | fault type known | both values | Parkes zone | wear day | fingerstick stated | user action stated | outcome stated | any guard drop |
|---|---|---|---|---|---|---|---|---|---|
| Serious, Abbott | 74,657 | 98.2 | 10.3 | 5.6 | 8.9 | 38.4 | 93.4 | 99.9 | 3.4 |
| Serious, Dexcom | 32,045 | 88.5 | 30.4 | 26.0 | 3.6 | 56.9 | 87.6 | 98.8 | 3.9 |
| Serious, Medtronic (caution) | 8,660 | 94.1 | 5.9 | 0.0 | 0.2 | 76.0 | 92.9 | 99.4 | 1.2 |
| Serious, other makers | 3,100 | 88.3 | 17.6 | 0.0 | 1.4 | 31.4 | 65.2 | 94.8 | 1.8 |
| Serious, all | 118,462 | 95.0 | 15.6 | 10.6 | 6.6 | 46.0 | 91.1 | 99.4 | 3.3 |
| Sample (weighted), Abbott | 843 | 70.9 | 28.0 | 72.2 | 26.5 | 28.0 | 0.0 | 100.0 | 44.1 |
| Sample (weighted), Dexcom | 4,574 | 86.7 | 0.6 | 8.7 | 0.0 | 0.8 | 0.1 | 97.3 | 0.1 |
| Sample (weighted), all | 6,137 | 85.1 | 4.3 | 16.7 | 3.5 | 4.5 | 0.2 | 97.8 | 6.0 |

- Where the final values came from: every stated Parkes zone (99.9 %) and 74 % of wear days came from the pattern layer. Sensor values: 35 % from the pattern layer for Abbott serious reports (the template), 98 % for the Abbott sample, 0 % for Dexcom (free prose; the model read them, and where both layers found a sensor value they agreed in 88 % of reports: 15,556 agree, 2,040 disagree).
- The 44 % guard-drop rate in the Abbott sample is the model writing the wrong zone letter on the template. The pattern layer supplies the zone for those reports, so the final zone is not affected.
- Pairs: 18,866 reports state both values. 421 were dropped as implausible (sensor outside 20 to 600 mg/dL or meter outside 20 to 1,500 mg/dL). 18,445 kept: 18,118 serious and 327 sample (weighted: 125,755 malfunction reports, 4.3 %).

## 3. Fault type from the text vs the FDA problem codes

Fault type (% of reports; figure t2). Serious reports are unweighted; the sample is weighted.

| Fault type | Serious Abbott | Serious Dexcom | Serious Medtronic (caution) | Serious all | Sample all (weighted) |
|---|---|---|---|---|---|
| reads low | 15.9 | 20.2 | 2.6 | 16.0 | 6.2 |
| reads high | 11.4 | 15.0 | 2.6 | 11.6 | 1.2 |
| erratic or stuck | 0.4 | 1.8 | 0.3 | 0.8 | 1.1 |
| signal loss | 9.5 | 6.0 | 3.7 | 8.0 | 42.7 |
| sensor error or early end | 26.1 | 5.1 | 1.6 | 18.1 | 15.3 |
| adhesive or fell off | 8.2 | 2.4 | 0.2 | 5.9 | 3.5 |
| insertion or skin injury | 14.5 | 22.8 | 2.3 | 16.1 | 0.4 |
| other device problem | 12.2 | 15.2 | 80.9 | 18.5 | 14.6 |
| unclear | 1.8 | 11.5 | 5.9 | 5.0 | 14.9 |

- Wrong readings (low + high + erratic + stuck) = 28.4 % of serious reports by text, against 33.1 % by the FDA code family (`report_results.md` d). In the malfunction sample the text gives 8.5 % against 30 code mentions per 100 reports: Dexcom malfunction texts are one-line boilerplate ("signal loss occurred"), so the text cannot see what the code says.
- Agreement with the codes (serious): of 18,933 text "reads low" reports, 95.5 % carry a wrong-readings code; Abbott 94.7 % carry the exact code "Low Readings", Dexcom only 17.9 % (Dexcom uses "Incorrect ... Readings" for 41.9 %). Of 13,754 text "reads high" reports, 97.3 % carry a wrong-readings code.
- The reverse: of 14,242 serious reports coded "Low Readings", the text says reads low in 87.2 % (Abbott 90.5 %, Dexcom 64.4 %), reads high in 4.0 % (Dexcom 23.3 %), unclear 3.6 %. The Dexcom mismatch is the model's known weakness: when the person was low and the sensor read high, it sometimes labels the sensor's direction wrongly (`VALIDATION.md` s7). Direction below is therefore taken from the numbers, not the label.
- Model labels vs the pair numbers: of the Abbott pairs where the sensor is below the meter, the model said "reads low" for 93.8 %; Dexcom 59.5 %; Medtronic 47.5 %.

## 4. Error sizes (the key output; figure t3)

Reports that state both values. Median (IQR); 10th and 90th percentiles in `tables/c_error_sizes.csv`.

| Group | Pairs | Error, mg/dL | Error, % of meter | Sensor read low | Sensor read high |
|---|---|---|---|---|---|
| Serious, Abbott | 7,556 | -65 (-278 to +95) | -47 % (-80 to +144) | 57.6 % | 41.7 % |
| Serious, Dexcom | 9,518 | +27 (-207 to +77) | +42 % (-63 to +169) | 43.7 % | 55.2 % |
| Serious, Medtronic (caution) | 500 | -24 (-220 to +65) | -15 % (-65 to +144) | 51.4 % | 42.4 % |
| Serious, other makers | 544 | -20 (-105 to +60) | -19 % (-53 to +117) | 53.5 % | 45.8 % |
| Serious, all | 18,118 | 0 (-239 to +80) | 0 % (-72 to +157) | 50.0 % | 48.9 % |
| Deaths only | 25 | -450 (-912 to -228) | -86 % (-91 to -63) | 84.0 % | 16.0 % |
| Sample, all (weighted) | 327 | -106 (-149 to +42) | -64 % (-71 to +59) | 73.1 % | 26.9 % |
| Sample, Abbott (weighted) | 255 | -110 (-151 to +56) | -65 % (-72 to +84) | 73.3 % | 26.7 % |
| Libre 3, received before 2025-11-24 | 1,355 | -180 (-441 to +41) | -70 % (-87 to +62) | 69.8 % | 29.8 % |
| Libre 3, received on or after 2025-11-24 | 1,044 | -98 (-246 to +70) | -59 % (-79 to +95) | 67.3 % | 32.2 % |

Split by the direction of the pair (serious reports):

| Group | Pairs | Error, mg/dL | Error, % of meter | 10th to 90th pct, % | Median sensor / meter, mg/dL | Crosses the 70 mg/dL line |
|---|---|---|---|---|---|---|
| Abbott, sensor below meter | 4,352 | -240 (-404 to -112) | -77 % (-86 to -60) | -90 to -42 | 60 / 317 | 61.5 % false low (sensor under 70, meter not) |
| Dexcom, sensor below meter | 4,160 | -258 (-426 to -111) | -68 % (-85 to -47) | -91 to -29 | 86 / 414 | 39.4 % false low |
| Abbott, sensor above meter | 3,149 | +120 (+60 to +225) | +190 % (+100 to +400) | +56 to +766 | 202 / 52 | 62.0 % missed low (meter under 70, sensor not) |
| Dexcom, sensor above meter | 5,255 | +69 (+41 to +126) | +150 % (+80 to +300) | +43 to +592 | 121 / 40 | 69.8 % missed low |

- The errors in complaints are enormous: the typical reads-low report has the sensor at about 60 to 90 mg/dL while the meter is 300 to 400 mg/dL. 96 to 97 % of all serious pairs are more than 20 % off (Abbott 97.3 %, Dexcom 96.2 %).
- Direction differs by maker. Abbott complaints lean low (58 %). Dexcom complaints lean high (55 %): the sensor showed a normal number while the meter was under 70. Reads-high pairs cross the 70 line in 62 to 70 % of cases; that is a hidden low.
- By model label: "reads low" pairs (9,194) have median -148 mg/dL, -64 %; "reads high" pairs (7,485) +76 mg/dL, +126 %.
- Libre 3 after the recall: the median error is smaller than before (-59 % vs -70 %), with about the same share reading low (67 vs 70 %). By date of the event the picture is the same (-55 % vs -71 %). guess: the recall news brought in more reports with less extreme errors. Texts arrive late, so the post-recall group is still filling.

## 5. Maker-stated Parkes zone vs the zone computed from the pair (figure t4)

| Maker | Pairs with a stated zone | Exact agreement | Within one zone | Stated zone worse | Computed zone worse |
|---|---|---|---|---|---|
| Abbott | 4,134 | 87.9 % | 98.1 % | 8.9 % | 3.3 % |
| Dexcom | 6,531 | 86.6 % | 96.0 % | 7.4 % | 6.0 % |
| All | 10,667 | 87.1 % | 96.8 % | 8.0 % | 4.9 % |

- Zone shares among all stated zones (serious): Abbott (4,177): C 46.6 %, D 47.8 %, E 5.4 %, A + B 0.2 %. Dexcom (8,329): A 4.4 %, B 23.5 %, C 29.5 %, D 35.7 %, E 6.9 %. Trial (REPLACE-BG Set A, all pairs): A 83.7 %, B 14.6 %, C 1.4 %, D 0.3 %, E 0.0 %. Complaints are the 1.7 % tail of the trial grid.
- Our grid is the type 1 Parkes grid; the makers do not say which version they use. guess: most disagreements (Abbott states a worse zone than we compute in 8.9 %) come from reports with several pairs, where we use the first pair and the maker may grade the worst one.
- Dexcom malfunction sample: 90.3 % of stated zones are D with almost no numbers in the text. guess: a fixed phrase in Dexcom's template, not a graded pair. Not used further.

## 6. Wear day of the reported failure (figure t5)

Complaint timing is not a failure rate: people report when they notice, and makers only record the day when asked.

| Group | Reports with a wear day | Median day | Day 1 | Days 1 to 2 | Last two days | Flat expectation: day 1 / days 1-2 / last two |
|---|---|---|---|---|---|---|
| Serious, Abbott (14-day sensor) | 6,627 (8.9 %) | 5 | 13.4 % | 24.3 % | 6.6 % | 7.1 % / 14.3 % / 14.3 % |
| Sample (weighted), Abbott | 217 (26.5 %) | 3 | 34.5 % | 42.7 % | 3.0 % | 7.1 % / 14.3 % / 14.3 % |
| Serious, Dexcom (10-day sensor) | 1,140 (3.6 %) | 6 | 7.1 % | 17.9 % | 18.2 % | 10.0 % / 20.0 % / 20.0 % |

- Abbott: day 1 is 1.9 times the flat rate in serious reports and 4.8 times in the malfunction sample; the last two days are under half the flat rate. Day 7 has a second bump (11.9 %). 0.4 % of wear days are past day 14 (15-day Libre Plus sensors exist, so 14 is a simplification).
- Dexcom: no day-1 excess (7.1 % vs 10 % flat); peaks at days 3, 7 and 10 (14.4, 16.8, 13.6 %). guess: people round to "a few days", "a week" and "the end".
- Trial side (`analysis/ERROR_DRIVERS.md` s5): Dexcom G4 accuracy was worst on wear day 1 (MARD 15.2 % vs 11.8 % on day 7; 86 % of people worse on day 1), and the low-range bias sat on day 1. The Abbott complaint pattern points the same way, but complaint timing cannot measure the size of a day-1 effect.

## 7. What people did, and what happened (serious reports)

| Group | n | Fingerstick check stated yes | Ate carbs | Took insulin | Skipped insulin | Sought care | Outcome: hypoglycaemia | Outcome: hospital or ER | Outcome: death |
|---|---|---|---|---|---|---|---|---|---|
| All fault types, all makers | 118,462 | 39.9 % | 26.3 % | 4.8 % | 0.1 % | 51.5 % | 14.0 % | 53.8 % | 0.5 % |
| reads low, all makers | 18,933 | 69.1 % | 27.7 % | 13.1 % | 0.2 % | 48.3 % | 10.6 % | 74.8 % | 0.1 % |
| reads low, Abbott | 11,880 | 56.5 % | 20.5 % | 16.9 % | 0.2 % | 50.9 % | 8.9 % | 72.1 % | 0.1 % |
| reads low, Dexcom | 6,470 | 90.6 % | 40.3 % | 6.5 % | 0.1 % | 46.7 % | 11.5 % | 83.9 % | 0.0 % |
| reads high, all makers | 13,754 | - | 45.0 % | 4.7 % | 0.1 % | 42.7 % | 15.6 % | 70.9 % | 0.0 % |

- In 28 % of reads-low reports the person ate carbs (treated a low that was not there); 13 % took insulin anyway (after a fingerstick showed the true high); skipping insulin is almost never written down (0.2 %). Together, ate carbs or skipped insulin = 27.9 %.
- Fingerstick checks: stated in 46 % of serious reports overall (yes 39.9 %, no 6.1 %), and in 69 % of reads-low reports (Dexcom 91 %), because a pair of numbers implies a check.
- "Hospital or ER" (53.8 %) is much wider than FDA's "Hospitalization" flag (13.9 %, `report_results.md` e). Cross-tab against the FDA patient-outcome codes (`tables/e_outcome_vs_fda.csv`; a report can carry several codes; two small rows, hyperglycaemia n = 4 and not stated n = 720, are in the CSV only):

| Model outcome | n | % of serious | FDA: Hospitalization | FDA: Required Intervention | FDA: either of the two | FDA: Other | FDA: no code |
|---|---|---|---|---|---|---|---|
| none | 12,636 | 10.7 % | 2.0 % | 39.8 % | 41.5 % | 24.8 % | 31.7 % |
| symptoms only | 24,275 | 20.5 % | 0.5 % | 60.3 % | 60.7 % | 34.8 % | 4.4 % |
| hypoglycaemia | 16,568 | 14.0 % | 2.3 % | 48.9 % | 51.2 % | 42.0 % | 6.6 % |
| hospital or ER | 63,700 | 53.8 % | 24.5 % | 55.1 % | 75.2 % | 33.3 % | 1.2 % |
| death | 559 | 0.5 % | 9.1 % | 2.0 % | 10.4 % | 35.1 % | 0.9 % |
| All serious | 118,462 | 100 % | 13.9 % | 53.2 % | 64.7 % | 34.0 % | 6.0 % |

- Verdict: mostly a definition difference, with a smaller over-count inside it. FDA files an ER, EMS or clinic visit under "Required Intervention", not "Hospitalization". Of the model's 63,700 "hospital or ER" reports, 24.5 % carry FDA's Hospitalization code, 55.1 % Required Intervention, 75.2 % one of the two. The model also catches 94.7 % of FDA's 16,475 Hospitalization reports.
- Against the matching FDA group (Hospitalization or Required Intervention, 64.7 % of serious reports) the model's 53.8 % is not an over-count. The over-count sits in the 24.8 % of "hospital or ER" reports (about 15,800) with neither code: the model files a call or visit to any health professional there (`VALIDATION.md` s7).
- Read "hospital or ER" as "sought medical care". About one in four of those reports is an admission by FDA's flag. The reverse gap: 39.8 % of the model's "none" reports carry FDA's Required Intervention code. Deaths line up: 92.1 % of model "death" reports carry FDA's Death code, and the model says death for 84.6 % of FDA's 609 Death reports.
- Malfunction sample: outcome "none" in 97.7 % (weighted), user action stated in 0.2 %. As expected for malfunction reports.

## 8. The join to Phase 2 (figure t6)

Method: take every pair where the sensor is below the meter, round the error to the lookup's 2 % steps, clip at the table's edge (-90 %; before 2026-10-30 the table stopped at -40 %), weight the lookup's median-person outcome by the share of reports in each step. Weighted sample rows use the sampling weights. "Floor" rows repeat the old join clipped at -40 %, for comparison. Reference rows show the plain lookup at a constant bias. "Time shown below 70" = share of the day the faulted sensor reads under 70 mg/dL (true trace 3.5 %). Full tables: `tables/f_join_reads_low.csv` (the `clip` column says which edge a row used).

| Group | Reads-low pairs | Median error | Beyond -20 % | Beyond -40 % | Beyond -90 % (edge) | Corrections skipped | Doses changed by more than 1 U | False low alerts per day | Time shown below 70 | High episodes missed | TIR change, points | LBGI (true 0.95) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Serious, Abbott | 4,352 | -76.8 % | 98.1 % | 90.7 % | 8.3 % | 49.3 % | 38.4 % | 0.85 | 79.5 % | 96.4 % | -44.0 | 26.7 |
| Serious, Dexcom | 4,160 | -68.4 % | 96.6 % | 80.5 % | 9.6 % | 45.2 % | 37.3 % | 1.00 | 69.0 % | 92.7 % | -34.6 | 22.5 |
| Serious, Medtronic (caution) | 257 | -63.8 % | 94.2 % | 77.8 % | 5.1 % | 43.7 % | 36.4 % | 1.08 | 65.0 % | 90.9 % | -31.1 | 20.6 |
| Serious, all makers | 9,060 | -72.1 % | 97.1 % | 85.0 % | 8.6 % | 46.9 % | 37.7 % | 0.94 | 73.3 % | 94.2 % | -38.4 | 24.2 |
| Sample, all (weighted) | 229 | -67.4 % | 98.7 % | 94.1 % | 0.7 % | 50.6 % | 38.9 % | 1.22 | 76.3 % | 98.0 % | -40.2 | 22.9 |
| Libre 3, received on or after 2025-11-24 | 703 | -73.1 % | 97.9 % | 89.9 % | 5.5 % | 48.8 % | 38.2 % | 0.94 | 77.1 % | 96.1 % | -41.6 | 25.3 |
| Serious, Abbott: clipped at -40 %, floor (old result) | 4,352 | -76.8 % | 98.1 % | 90.7 % | - | 31.3 % | 37.7 % | 1.75 | 25.3 % | 86.5 % | +6.7 | 5.87 |
| Serious, Dexcom: clipped at -40 %, floor (old result) | 4,160 | -68.4 % | 96.6 % | 80.5 % | - | 29.8 % | 36.7 % | 1.69 | 24.2 % | 84.2 % | +7.0 | 5.62 |
| Reference: constant -20 % bias | - | - | - | - | - | 7.2 % | 16.7 % | 0.86 | 10.1 % | 50.8 % | +11.5 | 2.33 |
| Reference: constant -40 % bias | - | - | - | - | - | 32.6 % | 38.7 % | 1.80 | 26.2 % | 88.7 % | +6.4 | 6.09 |
| Reference: constant -60 % bias | - | - | - | - | - | 52.3 % | 39.4 % | 1.96 | 63.8 % | 100 % | -27.1 | 16.3 |
| Reference: constant -90 % bias (table edge) | - | - | - | - | - | 54.2 % | 39.4 % | 0.19 | 100 % | 100 % | -63.3 | 38.2 |

- Reading the table: on the median trial person, the reported Abbott reads-low errors would skip 49 % of correction doses, change 38 % of doses by more than a unit, hide 96 % of high episodes and show "below 70" for 80 % of the day. That is about 7 times the -20 % scenario for skipped doses and twice its hidden highs.
- Floor vs full grid: the old -40 % clip gave Abbott 31 % skipped and 87 % hidden highs; the full grid gives 49 % and 96 %. The floor undercounted skipped doses by 18 points. 97 to 98 % of reported reads-low errors are past the 20 % tipping point of `SIMULATION_V2.md`, 78 to 94 % past -40 %, and 5 to 10 % still past the new -90 % edge (sample 0.7 %). The edge no longer matters: every outcome is flat past about -70 %, so these are the simulation's full numbers, not floors (`SIMULATION_V2.md` s13).
- Saturation: from -70 % on the dose rule skips every correction that was needed (54.2 % of decisions); from -56 % on every high episode is missed; "changed by more than 1 U" is flat at 39.4 % from -44 % on, because a dose can only fall to zero. That is why Abbott, Dexcom, the sample and Libre 3 land within a few points of each other.
- False low alerts per day fall from 1.75 (floor) to 0.85 (Abbott), because past about -60 % the sensor sits below 70 nearly all day: one endless low episode, no new alerts. The honest measures there are time shown below 70 (true 3.5 %, 69 to 80 % with the reported errors) and LBGI (true 0.95, 23 to 27). TIR no longer looks better; it drops by 35 to 44 points. At the reported error sizes a low-reading sensor does not hide itself (the -20 % message of `SIMULATION_V2.md` s5); it shows a constant "LOW".
- Both directions together (`tables/f_join_all_errors.csv`, clipped at -90 and +90 %; the -40 / +40 floor rows are in the file): serious all makers, 18,118 pairs: 23.5 % of corrections skipped (floor 15.2 %), 59.5 % of doses changed by more than 1 U (51.1 %), 10.6 % spurious corrections (5.8 %), 0.47 false low alerts per day (0.86), 47.1 % of high episodes missed (42.6 %), 46.8 % of low episodes missed (39.8 %). 36 % of all pairs are still beyond +90 % (reads-high medians are +150 to +190 %), so the reads-high side is still a floor.
- State this clearly in the paper: complaint texts describe the worst cases people noticed and reported. This is "what the reported failures would do", not what an average sensor does. The trial sensor's own error (MARD 13 %) is in `analysis/FINDINGS.md`.

## 9. Five takeaways

1. Reported sensor errors are huge, not subtle: the typical reads-low complaint has the sensor at 60 to 90 mg/dL and the meter at 300 to 400 mg/dL (median -77 % Abbott, -68 % Dexcom). 97 % are beyond the 20 % tipping point.
2. The two big makers fail in opposite directions in complaints: Abbott mostly reads low (58 % of pairs), Dexcom mostly reads high (55 %), and 62 to 70 % of those reads-high pairs hid a true low under 70 mg/dL. Both faults belong in Phase 2.
3. Fed into the Phase 2 lookup, now -90 to +90 %, the reported reads-low errors would skip 45 to 49 % of correction doses, hide 93 to 96 % of high episodes and show "below 70" for 69 to 80 % of the day on the median trial person. The old -40 % clip (31 %, 87 %) was a floor; the dose rule saturates near -70 %, so these are the simulation's full numbers.
4. People act on the wrong number: in 28 % of reads-low reports the person ate carbs for a low that was not there; a fingerstick is mentioned in 69 % of those reports.
5. Abbott complaints over-represent wear day 1 (13 % vs 7 % flat; 35 % in the malfunction sample), the same day the trial sensor was least accurate; the makers' own Parkes zones agree with the pair numbers 87 % of the time and are 95 to 100 % in zones C to E, the tail that the trial almost never reached (1.7 %).

## 10. Caveats

- Reporting bias: these are reports, not rates. People report the dramatic cases, and recall news changes reporting.
- Templates decide coverage. Abbott's template gives most pattern-layer values; Dexcom injury prose gives most pairs (30 % of reports); Dexcom malfunction texts are boilerplate, so the weighted sample rests on 327 pairs, 255 of them Abbott.
- Medtronic: undercounted (pump codes) and the weakest validation (kappa 0.62 to 0.63). Treat all Medtronic rows as indicative only.
- Model limits (`VALIDATION.md`): fault type kappa 0.77, outcome 0.75, user action 0.77 on 287 gold reports; Dexcom direction errors; "hospital or ER" means any medical care, not an admission (s7); "none" overcounted; 91 % of forms identical between two runs. The 100-report human check of the gold set is still pending.
- Numbers: first pair only when a report lists several; values must appear word-for-word in the text; 421 implausible pairs dropped; "LOW"/"HI" display words are not pairs and are left out, which undercounts the most extreme reads-low cases.
- The join uses the trial's median person and a constant bias. The lookup now reaches -90 %; 8 to 10 % of serious reads-low pairs lie beyond it, but every outcome is flat (saturated) past about -70 %, so the reads-low results are no longer floors. Reads-high errors are still clipped at +90 % and 36 % of all pairs lie beyond it, so the both-directions join is a floor on the high side. Libre 3 before/after uses the date FDA received the report; texts arrive months late.
