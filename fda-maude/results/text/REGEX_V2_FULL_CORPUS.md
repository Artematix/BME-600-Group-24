# Wider pattern layer over every MAUDE CGM report: wrong-reading pairs in malfunction-only vs death/injury reports

Date: 2026-11-06. Script: `scripts/extract_regex_v2.py` (patterns) and `scripts/report_regex_v2.py` (tables, figures). Tuned against the model's output on the 124,599-report run set, then run over all 3,382,071 reports. Numbers below are counts of reports and of stated values. MAUDE counts reflect reporting behaviour, not failure rates.

## Summary (6 lines)

1. The new patterns find 89 % of the sensor-meter pairs the language model found (was 73 %); Abbott 63 -> 88 %, Dexcom 81 -> 91 %. Where both find a pair, they agree exactly in 88 % (was 89 %). Wear day recall went from 71 % to 95 %.
2. Over all 3.38 million reports the patterns found 209,388 pairs: 191,112 in malfunction-only reports (never read by the model) and 18,237 in death/injury reports. 85 % of the malfunction pairs are Abbott template reports, nearly all from 2025-2026 (81 % of all malfunction pairs).
3. Malfunction-only pairs are one failure: the sensor reads about a third of the true value while the true glucose is normal or high (median error -66 %, 75 % read low, true glucose under 70 in only 5 %).
4. Death/injury pairs are two failures: hidden lows (true glucose under 70 in 38 %, sensor reads normal or high) and extreme false lows at very high true glucose. Their error is bigger in absolute terms (median 85 % vs 72 %) but the direction, not the size, is what differs.
5. The share of pairs filed as death/injury is U-shaped against the error, for both brands: lowest in the common -80 to -50 % band (Abbott 1-4 %, Dexcom 10-17 %), highest when the sensor sits near its floor against a high true value (-100 to -90 %: Abbott 42 %, Dexcom 79 %) and when the sensor reads 2 to 3 times the true value (over 200 %: Abbott 12 %, Dexcom 76 %). The peak at small errors is a reporting artefact.
6. The gradient is partly real (same shape in both brands, matching how harm happens) and partly coding (Abbott 4 % vs Dexcom 28 % of pairs coded serious is reporting style). Harm words in malfunction-only texts stay flat at about 1 % across all error sizes, so the malfunction pile is not hiding coded harm. A human read of the extreme bands would settle it (section 8).

## 1. Words used here

- Pair = a report whose text states both the sensor value and the meter (fingerstick or lab) value. Error = sensor minus meter, in mg/dL and as % of the meter value. Negative = the sensor read low.
- Regex = a fixed text pattern. Recall = of the pairs the model found, the share the patterns also found. Agreement = when both found a pair, the share with the same two numbers (exact, or both within 5 mg/dL). Precision = the share of the patterns' pairs that are right; estimated by reading pairs by eye.
- Serious = FDA event type Death or Injury. Malfunction-only = event type Malfunction (no harm coded by the reporter).
- Median = the middle value. IQR = the middle half (25th to 75th percentile).
- Meter band = where the true glucose was: under 54, 54 to 69, 70 to 180, 181 to 250, over 250 mg/dL. Hidden low = meter under 70. False low = sensor under 70 while the meter was not.
- Weighted sample = the 6,168 random malfunction reports whose weights scale up to all 2.94 million malfunction reports received by 2026-07-21.
- Bound = a value written as a limit ("over 400", "less than 40", "400+"). Display word = the sensor showed LOW, LO, HIGH or HI instead of a number. Both are kept as flags, not as values (gold-set rule).
- Same-sentence pattern = both numbers were found in one sentence (the safer patterns). Cross-sentence = the numbers come from two neighbouring sentences or from the whole text.

## 2. Baseline vs tuned (run set, 124,599 reports; reference = the model's own numbers after its word-for-word guard)

| Brand | Model pairs | v1 recall % | v2 recall % | v1 exact agreement % | v2 exact agreement % | v2 within 5 mg/dL % | v2 pairs the model did not find |
|---|---|---|---|---|---|---|---|
| Abbott | 7,802 | 62.6 | 88.3 | 88.3 | 88.8 | 89.9 | 217 (3.1 % of v2 pairs) |
| Dexcom | 9,550 | 81.3 | 90.5 | 89.5 | 88.0 | 88.9 | 743 (7.9 %) |
| Medtronic (caution) | 524 | 66.6 | 70.0 | 95.7 | 95.1 | 95.1 | 13 (3.4 %) |
| Other (incl. Senseonics) | 560 | 85.2 | 93.9 | 87.0 | 86.5 | 89.9 | 27 (4.9 %) |
| All | 18,436 | 73.1 | 89.1 | 89.1 | 88.4 | 89.5 | 1,000 (5.7 %) |

- v2 pairs on the run set: 17,426 (v1: 14,108). Pairs found by both: 16,426. Role swaps (sensor and meter exchanged): 0.2 %.
- Agreement by pattern (exact): Abbott template 91 %, v1 prose in one sentence 91 %, v2 one sentence 79 %, v1 neighbouring sentences 91 %, v2 neighbouring sentences 83 %, v2 whole-text unique pair 92 %. Table: `tables/h_regex_v2_by_pattern.csv`.
- Why the v2 one-sentence agreement is lower: 45 of its disagreements were read by eye. Most are the model choosing another pair in the same text (the model is not consistent about "first pair"; it often takes the last member of a list), or model errors (mmol/L arithmetic, a bound taken as a value, a number from a different sentence). Two pattern faults found in that read (list positions, the "MG/D" typo unit) were fixed. So the agreement figure understates precision.
- Wear day (table `tables/h_regex_v2_wear_zone.csv`): recall 71 -> 95 % (Abbott 80 -> 98 %, Dexcom 15 -> 80 %); where both state a day they agree in 99 %. The patterns now find 10,073 wear days against the model's 7,186; 28 of 30 extra ones read by eye were right. Parkes zone: unchanged (recall 99.9 %, agreement 99 %).
- The model is not gold. Reading 400 misses showed two model error forms that the patterns now refuse: Abbott's "erratic" template (two sensor readings within 10 minutes, no meter) and a lone meter value with no sensor value. Reported recall is therefore a little pessimistic.

## 3. The new pattern forms (one short example each; v1 patterns are imported unchanged)

| Form | Example of the text it reads | Note |
|---|---|---|
| Role word after the number | "A READING OF 55 MG/DL OBTAINED ON THE ADC DEVICE COMPARED TO A READING OF 515 MG/DL ON AN UNSPECIFIED METER" | the biggest Abbott prose gain |
| Wider role words | ADC DEVICE, HCP METER, COMPETITOR BRAND DEVICE, BUILT-IN READER, LABORATORY RESULT, EGV, SG, G6/G7, RECEIVER, TANDEM PUMP, READER'S BUILT-IN METER | "another ADC device" and "built-in" always mean the meter |
| Unit-less number after a role word | "G6 READING 71, FINGER STICK READING IS 52"; "SENSOR WAS AT 202" | needs 2 digits or a decimal ("LIBRE 2" is a name) |
| Comparison structure | "41 MG/DL FROM SENSOR AGAINST 511 MG/DL"; "a COMPARED TO b" with one side labelled | sensor-first only assumed when the text holds just those two numbers |
| Typo units | MGDL, MG/ DL, MG/D/L, M/DL, NG/DL, MMOLL, MMOL//L, decimal commas | unit-less small decimals next to an mmol/L number are read as mmol/L |
| Ranges and lists | "90-100 MG/DL" -> 90 (flagged); "40 AND 57 MG/DL ON THE ADC DEVICE COMPARED TO 275 AND 400" -> 40 vs 275 | lists share one role; equal-length lists pair by position |
| Bounds and display words | "LO (LESS THAN 40 MG/DL)", "OVER 400", "400+", "THE CGM READ HIGH" | flags `sensor_bound`, `meter_bound`, `sensor_display_word`; a flag plus a number is a "bound pair" |
| Guards | A1C sentences; alert settings, limits, thresholds; insulin units; ketones; differences ("30 MG/DL LOWER THAN"); trend averages; device range statements ("ONLY REPORTS VALUES BETWEEN 40 AND 400"); two sensor readings "WITHIN 10 MINUTES" | the number is not a glucose comparison |
| Role fixes | the HCP's "THEIR DEVICE" is a meter; "BLOOD GLUCOSE WAS 197" glued to the number beats a sensor word further back; a v1 prose pair is dropped when v2 gives its numbers the opposite role, a block or a bound | removed the "CGM read LOW and the BG was 315" error |
| Cross-sentence | sensor-only sentence next to a meter-only sentence (1 or 2 apart); a whole text with exactly one sensor and one meter number | not when the other sentence already holds a display word or bound |
| Wear day | "THE LENGTH OF THE WEAR IS 8 DAYS"; "3 DAYS AFTER THE SENSOR WAS INSERTED"; "DURING HER 4 DAY WEAR OF"; "WEARING THE ... SENSOR FOR 14 DAYS"; "SESSION LASTED 5 DAYS"; "SAME DAY OF APPLYING" (= day 1) | not "AFTER FOURTEEN DAYS OR LESS OF WEAR" (Abbott boilerplate) |
| Keyword flags | reads low, reads high, inaccurate, signal loss, sensor error, adhesive, insertion/skin, insulin dose, ate carbs, hypo symptoms, hyper/DKA, fingerstick, EMS/hospital, death, no-harm sentence | mentions only, not facts |

Tested and dropped: "RESULTS OF a AND b WERE PLOTTED" (roles assumed; 65 % agreement, 17 % swapped). Pattern order: Abbott template, v1 one sentence, v2 one sentence, v1 neighbouring sentences, v2 neighbouring sentences, whole-text unique pair.

## 4. Precision spot-check (pairs the patterns found and the model did not)

- Such pairs are 5.7 % of the patterns' pairs on the run set (Abbott 3.1 %, Dexcom 7.9 %). 50 were read by eye in three rounds; the last round (48 judged, 2 unclear):

| Verdict | Pairs | Share |
|---|---|---|
| right (both numbers are the stated comparison) | 28 | 58 % |
| the two numbers come from different moments (a sensor value earlier, a meter value later at the hospital) | 15 | 31 % |
| wrong (a setting, a bound, a difference, a trend value, or both numbers from the meter) | 5 | 10 % |

- 4 of the 5 wrong forms were then fixed (section 3, "Role fixes" and "Guards"). The "different moments" pairs all come from the cross-sentence patterns (v1 neighbouring sentences 9, whole-text 4, v2 neighbouring 2). The model makes the same pairings, so they are also in the model-based results.
- On the full corpus, 98.2 % of pairs come from same-sentence patterns (the Abbott template alone gives 78.5 %), so the cross-sentence risk touches about 1 pair in 50 overall, and 1 in 5 of the serious pairs. Every table below is given for all pairs and, in the CSV, for same-sentence pairs only; the two differ by at most a few points.
- Guess: precision of all pairs on the full corpus is about 90 % (template and one-sentence agreement 88-91 %, with most disagreements being the model's), lower for the serious prose pairs than for the malfunction template pairs.

## 5. Full-corpus counts (`tables/h_full_coverage.csv`, `h_full_pairs_by_pattern.csv`)

Run: 3,382,071 reports in 7.8 min (20 workers, 7,244 reports per second); 3,144,535 have text.

| Group | Brand | Reports with text | Pairs | % of texts | Bound pairs | Wear day % | Zone % |
|---|---|---|---|---|---|---|---|
| Malfunction | Abbott | 457,991 | 162,072 | 35.4 | 67 | 32.3 | 74.3 |
| Malfunction | Dexcom | 2,429,126 | 25,273 | 1.0 | 4,309 | 0.0 | 8.7 |
| Malfunction | Medtronic (caution) | 123,223 | 3,651 | 3.0 | 19 | 0.2 | 0.0 |
| Malfunction | Senseonics | 4,212 | 74 | 1.8 | 2 | 3.3 | 0.0 |
| Malfunction | all | 3,021,063 | 191,112 | 6.3 | 4,397 | 4.9 | 18.2 |
| Injury | Abbott | 77,139 | 7,453 | 9.7 | 572 | 10.0 | 6.1 |
| Injury | Dexcom | 33,109 | 9,808 | 29.6 | 1,435 | 7.5 | 26.6 |
| Injury | Medtronic (caution) | 8,618 | 395 | 4.6 | 18 | 0.3 | 0.0 |
| Injury | Senseonics | 2,951 | 552 | 18.7 | 8 | 2.0 | 0.0 |
| Death | all | 622 | 25 | 4.0 | 2 | 1.9 | 1.8 |
| All | all | 3,144,535 | 209,388 | 6.7 | 6,433 | 5.1 | 18.0 |

- Pairs by pattern: Abbott template 164,460 (78.5 %), v1 prose one sentence 34,878 (16.7 %), v2 one sentence 5,359 (2.6 %), v1 neighbouring sentences 2,753 (1.3 %), v2 one-side comparison 862, v2 neighbouring 841, whole-text unique 231. The v2 forms add 1.6 % of the malfunction pairs but 23 % of the serious pairs (4,207 of 18,237).
- Serious pairs: 18,237 here against 18,118 from the model on the run set (`TEXT_RESULTS.md`). Abbott serious reads-low median -77 % in both.
- When the pairs were written (year received, `tables/h_by_year.csv`): Abbott malfunction pairs are 2024: 6,331, 2025: 36,497, 2026: 119,060 (the Libre 3 recall period; Abbott's template reports to FDA). Dexcom malfunction pairs are 2019: 5,295, 2020: 14,020, 2021: 5,031 and under 60 a year after that: Dexcom's later malfunction texts are one-line boilerplate ("inaccurate" is mentioned in 0.1-0.3 % of them). So the malfunction-only error data is Abbott 2024-2026 and Dexcom 2019-2021.
- Other flags: 1,387 Abbott "erratic" reports (two sensor readings within minutes; not pairs); 7,347 reports where the sensor showed a word (LOW, LO, HI, HIGH); 159,080 wear days; 564,607 stated Parkes zones (Abbott states one in 74 % of its malfunction texts).

## 6. Malfunction-only vs serious pairs (`tables/h_malf_vs_serious_errors.csv`, tests in `h_malf_vs_serious_tests.csv`, figure t12)

| | All malfunction | All serious | Abbott malfunction | Abbott serious | Dexcom malfunction | Dexcom serious |
|---|---|---|---|---|---|---|
| pairs | 191,112 | 18,237 | 162,072 | 7,466 | 25,273 | 9,818 |
| median error % (IQR) | -66 (-74 to +22) | -7 (-72 to +154) | -67 (-74 to +60) | -49 (-80 to +143) | -52 (-67 to -30) | +40 (-62 to +163) |
| median absolute error % | 72 | 85 | 74 | 86 | 59 | 85 |
| reads low % | 75 | 50 | 74 | 58 | 80 | 44 |
| median error, reads-low pairs % | -69 | -72 | -70 | -77 | -58 | -67 |
| median error, reads-high pairs % | +135 | +156 | +142 | +184 | +64 | +144 |
| absolute error 40 % or more | 96 | 88 | 98 | 93 | 81 | 85 |
| median sensor / meter, mg/dL | 63 / 178 | 104 / 131 | 63 / 180 | 90 / 175 | 65 / 148 | 112 / 100 |
| meter under 54 % | 2 | 31 | 2 | 22 | 3 | 38 |
| meter 54 to 69 % | 2 | 6 | 2 | 6 | 2 | 6 |
| meter 70 to 180 % | 50 | 20 | 48 | 24 | 63 | 17 |
| meter 181 to 250 % | 27 | 8 | 29 | 11 | 18 | 6 |
| meter over 250 % | 18 | 35 | 19 | 38 | 14 | 33 |
| false low (sensor < 70, meter not) % | 58 | 24 | 59 | 36 | 54 | 16 |
| hidden low (meter < 70, sensor not) % | 5 | 33 | 4 | 26 | 5 | 38 |
| missed high (meter > 180, sensor not) % | 43 | 33 | 46 | 43 | 25 | 25 |

- Size: serious pairs have a bigger absolute error, but the effect is small (Cliff's delta -0.17 overall, -0.20 Abbott) to medium (-0.39 Dexcom). Within the reads-low pairs the medians are close (-69 vs -72 %).
- Direction and place differ far more. Malfunction-only pairs are false lows at a normal or high true glucose: sensor about 60 while the meter is about 180. Serious pairs sit at the two ends of the glucose scale: the true value is under 54 in 31 % (hidden lows; the sensor read normal or high) and over 250 in 35 %.
- Hidden lows: 5 % of malfunction pairs vs 33 % of serious pairs (Abbott 4 vs 26, Dexcom 5 vs 38; differences of 24 to 39 points, 95 % intervals in the tests table).
- Medtronic (caution: undercounted, 3,651 vs 397 pairs) shows the same split: hidden lows 10 vs 44 %. Senseonics has 74 malfunction pairs; no difference is testable.
- By year (Abbott): malfunction medians are stable at -66 to -72 % in every year; serious medians moved from about +40 % (2018-2023, hidden lows) to -76 % in 2025 and -61 % in 2026 (the Libre 3 reads-low recall wave). Dexcom serious medians moved from +80 to +115 % (2017-2023) to -16 % (2025) and -37 % (2026): G7 complaints also lean low now, as `BRAND_COMPARISON.md` found.
- The two-humped shape of the serious distribution (figure t12) means its overall median (-7 %) says little; read the two directions separately.

## 7. The harm gradient (`tables/h_harm_gradient.csv`, `h_harm_gradient_abs.csv`, figure t13)

Share of pairs that sit in a death/injury report, per band of the signed error (negative = reads low). Only bands with 20+ pairs; 95 % Wilson intervals in the table.

| Error band (% of meter) | Abbott pairs | Abbott % serious | Dexcom pairs | Dexcom % serious |
|---|---|---|---|---|
| -100 to -90 (sensor near its floor, true value high) | 1,094 | 41.9 | 580 | 78.8 |
| -90 to -80 | 19,241 | 7.3 | 2,526 | 35.3 |
| -80 to -70 | 43,550 | 1.9 | 3,746 | 17.2 |
| -70 to -60 | 44,692 | 1.4 | 4,974 | 11.4 |
| -60 to -50 | 10,238 | 3.7 | 4,461 | 9.5 |
| -50 to -40 | 2,802 | 10.1 | 3,733 | 11.8 |
| -40 to -20 | 2,022 | 15 | 4,101 | 17 |
| -20 to +20 (small errors) | 735 | 22 | 632 | 62 |
| 20 to 60 | 1,892 | 14 | 3,160 | 27 |
| 60 to 100 | 6,485 | 6.5 | 1,918 | 44 |
| 100 to 200 (sensor 2 to 3 times the true value) | 24,379 | 3.6 | 2,534 | 61.1 |
| over 200 | 12,408 | 11.9 | 2,726 | 75.6 |
| all bands | 169,538 | 4.4 | 35,091 | 28.0 |

- The shape is the same for both brands: a U. The common complaint (sensor reads 50 to 80 % low) has the lowest harm share, below the brand's overall share (Abbott 1.4-3.7 %, Dexcom 9.5-17 %). Both ends are high: the sensor pinned near its floor against a high true value (-100 to -90 %: 10 times Abbott's overall share, 3 times Dexcom's) and the sensor reading 2 to 3 times the true value, which is a hidden low (over 200 %: 2.7 times the overall share for both brands).
- The peak at small errors (-20 to +20 %) is a reporting artefact, not harm from a small error: makers do not file a malfunction report for a 10 % discrepancy (Abbott's template reports carry a Parkes zone C to E), while injury narratives quote whatever numbers were around, often values measured after treatment. Those bands hold 735 and 632 pairs, under 1 % of the pile.
- Split by direction and absolute size (`h_harm_gradient_abs.csv`): for Dexcom the harm share rises steadily with the size of a reads-high error (20-30 %: 25 %; 50-60 %: 32 %; 80-90 %: 48 %; over 200 %: 76 %). For Abbott reads-high errors it falls with size until 200 % and only then rises (12 %). For reads-low errors both brands fall to a floor at 60-80 % and rise sharply at 90-100 %.

### Real gradient or coding artefact?

- Coding differences are large and known (`BRAND_COMPARISON.md` section on reporting style): of the Abbott serious pairs, 74 % carry only the FDA outcome "Required Intervention" and 8.5 % Hospitalization; of the Dexcom serious pairs, 69 % carry only "Other" and 26 % Hospitalization (`tables/h_outcome_coding.csv`). Abbott writes "no report of death or permanent impairment" in 99.9 % of its malfunction texts and 95 % of its serious texts, so that sentence carries no information. The brand levels (4 % vs 28 % of pairs coded serious) are therefore reporting style: Abbott files a malfunction report for almost every template comparison; Dexcom's malfunction texts rarely state numbers at all.
- The extra check done here: harm words in the narrative (symptoms, EMS/hospital, death) instead of the FDA code (`tables/h_harm_gradient_text.csv`). Inside malfunction-only pairs, harm words stay at about 1 % in every error band (Abbott 0.5-3 %; Dexcom 0.1-1 % between 20 and 90 %, 3-8 % above 90 %, and 8 % in the 39-pair under-10 % band). Inside serious pairs they are 59-83 % (Abbott, rising with the error size) and 85-95 % (Dexcom, flat). So the malfunction pile does not hide uncoded harm, and within Abbott's serious reports the bigger errors do come with more explicit harm.
- Verdict: the U shape is partly real. Both ends of the U match how a sensor error hurts someone (a false LOW at a very high true value: carbs eaten or insulin withheld while the person is in or near DKA; a sensor reading normal while the true value is under 54: a hypo that nobody treats). Both brands show it despite opposite coding habits. The middle of the U and the small-error peak are reporting behaviour: which numbers get written down, and whether a maker files the comparison as a malfunction or an injury.
- What would settle it: (1) a human read of about 100 malfunction-only and 100 injury reports drawn from the two extreme bands (-100 to -90 % and over 200 %), to see whether the narratives differ in what happened to the person or only in the code; (2) the same gradient inside one brand and one year (Abbott 2025-2026), to remove the era mix (Dexcom malfunction pairs are 2019-2021, its serious pairs mostly 2022-2026); (3) reporter type (patient vs maker) per band, from the report source field.

## 8. Agreement with the weighted sample (`tables/h_weighted_check.csv`)

Weighted estimates from the 6,168-report local sample (289 pairs; bootstrap 95 % interval, 500 draws, seed 20261106) against the full-corpus malfunction frame (2,936,278 reports received by 2026-07-21; 130,460 pairs).

| Brand | Measure | Weighted sample (95 % interval) | Full corpus | Inside? |
|---|---|---|---|---|
| All | pair rate, % of malfunction reports | 4.2 (3.6 to 4.7) | 4.4 | yes |
| All | median error % | -64 (-65 to -60) | -65 | yes |
| All | reads low % | 73 (67 to 79) | 75 | yes |
| All | meter under 70 % | 5.6 (2.8 to 9.0) | 5.0 | yes |
| All | absolute error 40 % or more | 95 (92 to 98) | 95 | yes |
| Abbott | pair rate % | 26.6 (23.2 to 29.6) | 26.0 | yes |
| Abbott | median error % | -65 (-67 to -63) | -67 | yes |
| Dexcom | pair rate % | 0.57 (0.34 to 0.81) | 1.05 | no |
| Dexcom | median error %; reads low %; meter under 70 % | -45; 65; 4.4 | -52; 80; 5.2 | yes (27 pairs, wide intervals) |

- Everything agrees within sampling error except the Dexcom pair rate. The sample drew fewer wrong-reading reports than expected in the 2019 and 2020 Dexcom strata (11 pairs where 24 were expected in 2020; "inaccurate" is mentioned in 5.0 % of the sampled 2020 texts vs 9.2 % in the frame, while text length and the month mix match). That is a thin-sample draw, not a pattern problem; `TEXT_RESULTS.md` already warned that the sample holds too few Dexcom pairs (31). The full corpus replaces the sample for every malfunction-only number from here on.
- Earlier model-based estimate for the weighted sample (`TEXT_RESULTS.md`): 4.3 % of malfunction reports state both values. Full corpus: 4.4 %.

## 9. What this does to the research question (5 lines)

1. The malfunction-only pile is 10 times the serious pile and is one fault: a false low of 60 to 80 % while the true glucose is 70 to 250 mg/dL. It almost never carries a harm code or harm words. This is the fault Phase 2 should simulate for "wrong readings that did not hurt": it tests needless carbs, insulin suspension and alarm fatigue.
2. The serious pile is two other faults: a hidden low (sensor reads normal or high while the true value is under 54 to 70; 33 % of serious pairs) and a floor-pinned sensor (LOW or under 40) at a true value over 250 (DKA missed). These are the faults to simulate for "wrong readings that hurt".
3. So the question sharpens from "how big is the error?" to "where on the glucose scale and in which direction?": the harm code follows the true glucose band and the extremeness of the error, not its percentage size in the common range.
4. The lookup-table join in `TEXT_RESULTS.md` (constant bias on a median person) covers fault 1 well; faults 2 and 3 need a simulation that fixes the true glucose band (under 54 or over 250) rather than the bias size.
5. Caveats stay: event type is the reporter's choice; brand levels are coding style; the pairs come from different eras per brand; the text-only "harm" markers are words, not confirmed outcomes.

## 10. How to run and what is written

From the repo root (Windows: plain `python`). Deterministic (seed 20261106).

| Command | Time | Writes |
|---|---|---|
| `python fda-maude/scripts/extract_regex_v2.py tune` | about 1 min (20 workers) | `tables/h_regex_v2_recall_by_brand.csv`, `h_regex_v2_by_pattern.csv`, `h_regex_v2_wear_zone.csv`, `h_regex_v2_spotcheck_50.csv`, `h_regex_v2_disagreements_sample.csv` |
| `python fda-maude/scripts/extract_regex_v2.py mine --stages v1` | about 1 min | 400 missed reports with the sentences around the model's values, to the TEMP folder |
| `python fda-maude/scripts/extract_regex_v2.py full` | 8 min + 1 min report | `clean/regex_v2_full.csv.gz` (one row per report, 39 MB, not in git), then everything `report` writes |
| `python fda-maude/scripts/extract_regex_v2.py report` | about 1 min | `tables/h_full_coverage.csv`, `h_full_pairs_by_pattern.csv`, `h_malf_vs_serious_errors.csv`, `h_malf_vs_serious_tests.csv`, `h_error_distribution.csv`, `h_by_year.csv`, `h_harm_gradient.csv`, `h_harm_gradient_abs.csv`, `h_harm_gradient_text.csv`, `h_outcome_coding.csv`, `h_weighted_check.csv`, `h_regex_v2_stats.json`; figures `t11_regex_v2_recall.png`, `t12_malfunction_vs_serious_errors.png`, `t13_harm_gradient.png` |

Per-report columns in `regex_v2_full.csv.gz`: mdr_report_key, event_type, event_group (death / injury / malfunction / other), brand, year_received, product_code, sensor_value, meter_value, unit, error_mgdl, error_pct, direction, meter_band, sensor_raw, meter_raw, pattern (which form fired), n_candidates, value_flags (range, approx, list, unitless, mmol), sensor_display_word, sensor_bound, meter_bound, bound_pattern, two_sensor_readings, wear_day, wear_pattern, zone_stated, 15 keyword flags, text_chars, has_text, match_text (the matched sentence, for audit).

Inputs read: `clean/full.parquet` (all reports), `clean/run_set.csv.gz` and `clean/text_extract_v3.jsonl` (tuning), `clean/sample_local.parquet` (weights). `extract_regex.py` (v1) is imported and not changed. Plausibility rules copied from `text_results.py`: sensor 20 to 600 mg/dL, meter 20 to 1,500 mg/dL; first pair in the text; a pair with equal values is not a pair.

## 11. Caveats

- MAUDE counts are reports, not failure rates. The malfunction-only pile is dominated by Abbott's 2025-2026 template reports and the Dexcom share by its 2019-2021 prose; brand and era are mixed in every pooled number.
- The patterns have no understanding. Precision is estimated, not measured against a gold set: about 88-91 % agreement with the model where both find a pair, about 60 % of the 6 % of pairs the model did not find are clearly right, and about 1 pair in 5 of the serious prose pairs joins numbers from two moments.
- Bounds and display words (6,433 bound pairs, 7,347 display words) are not in the error tables, which undercounts the most extreme reads-low cases, more so for Abbott ("LO" under 40 mg/dL).
- Medtronic is undercounted (pump codes) and Senseonics is small. Treat both as indicative.
- Harm words are mentions in the text, not confirmed outcomes; FDA event type is assigned by the reporter.
