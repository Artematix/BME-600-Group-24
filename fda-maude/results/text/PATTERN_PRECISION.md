# How often are the pattern pairs right? (precision of the version 2 patterns)

Date: 2026-11-21. Script: `scripts/pattern_precision.py`. Counts: `pattern_precision_stats.json`. Sample rows: `pattern_precision_sample.csv`. Input: the saved pattern output `clean/regex_v2_full.csv.gz` (3,382,071 reports, 209,388 pairs, 191,112 of them malfunction-only). No input file was missing.

## Short answer
| # | Compared with | Result |
|---|---|---|
| 1 | Reference set (287 reports, labelled by an AI reviewer) | 74 of 74 pattern pairs have both values right |
| 2 | Language model, run set (124,599 reports) | the two agree on both values in 14,535 of 16,434 pairs (88.4 %) |
| 3 | Direct read of 100 random malfunction-only pairs | 97 of 100 right (97 %), 3 unclear, 0 wrong |

- Measurement 3 is the one to quote. Its 95 % interval is 91.5 to 99.0 % (97 of 100 pairs).
- The 100 texts were read by an AI reader (Claude), not by a person. One reader, one pass. `pattern_precision_sample.csv` lists every sampled report id with its verdict, so a person can re-check any row.

## Words
- Pair = the sensor value and the fingerstick meter value a report states for the same moment.
- Precision = of the pairs the patterns output, the share that are right.
- Malfunction-only = a report with no death or injury coded. Template = a fixed sentence a maker re-uses, with only the numbers changed.
- False low call = the patterns output a sensor value under 70 and a meter value of 70 or more.
- Interval = 95 % Wilson interval: the range the true share most likely sits in, given the sample size.

## 1. Against the reference set (`gold/gold_labels_v1.csv`)
| Group | Reports | Pairs in reference | Pattern pairs | Sensor right | Meter right | Both right | Reference pairs missed |
|---|---|---|---|---|---|---|---|
| All | 287 | 77 | 74 | 74 of 74 | 74 of 74 | 74 of 74 (100 %; interval 95.1 to 100) | 3 of 77 |
| Malfunction-only | 150 | 49 | 48 | 48 of 48 | 48 of 48 | 48 of 48 (100 %; interval 92.6 to 100) | 1 of 49 |
| Death or injury | 137 | 28 | 26 | 26 of 26 | 26 of 26 | 26 of 26 (100 %; interval 87.1 to 100) | 2 of 28 |

- The patterns output no pair where the reference has none (0 of 74). No pair was swapped.
- The 3 missed pairs: report 25662953 (Abbott, a list "50, 60" against "90, 195"), 10069748 and 10009047 (Medtronic injury, free text).
- Limit: the reference labels come from an AI reviewer, not a person. And this is not a fresh test: the first pattern version was scored on these same reports (`VALIDATION.md`), and version 2 copies the reference rule on bounds.
- Limit: all 49 malfunction-only reference pairs are Abbott template reports (`gold/GOLD_SET.md`).

## 2. Against the language model (reports where both output a pair)
| Group | Both output a pair | Agree on both values |
|---|---|---|
| All run-set reports | 16,434 | 14,535 (88.4 %) |
| Death or injury | 16,146 | 14,278 (88.4 %) |
| Malfunction-only | 288 | 257 (89.2 %) |
| Text holds one pair | 14,012 | 12,825 (91.5 %) |
| Text lists several pairs | 2,422 | 1,710 (70.6 %) |
| Malfunction-only, text holds one pair | 215 | 212 (98.6 %) |
| Malfunction-only, text lists several pairs | 73 | 45 (61.6 %) |

- Both values within 5 mg/dL: 14,705 of 16,434 (89.5 %). Swapped: 33 of 16,434 (0.2 %).
- Does it match `REGEX_V2_FULL_CORPUS.md`? The percentages match (88.4 %, 89.5 %, 0.2 %). The counts differ a little: that memo's text says 16,426 pairs found by both and 17,426 pattern pairs; re-computed 16,434 and 17,429.
- The re-computed counts equal the saved table `tables/h_regex_v2_recall_by_brand.csv`. guess: the memo text was written just before the last small pattern fix.
- Agreement is not precision: the model is also wrong at times. Most disagreements are in texts that list several pairs. There the patterns take the first pair by rule, and the model often takes another one.

## 3. Direct read of 100 malfunction-only pairs
| Maker | Pairs in the pile | Share of 191,112 | Sampled | Right |
|---|---|---|---|---|
| Abbott | 162,072 | 84.8 % | 85 | 83 of 85 |
| Dexcom | 25,273 | 13.2 % | 13 | 12 of 13 |
| Medtronic | 3,651 | 1.9 % | 2 | 2 of 2 |

- Drawn with seed 20261120, split by maker share. Other makers hold 116 pairs (0.06 % of 191,112) and got 0 of the 100.
- Verdicts (100 pairs): right 97, swapped 0, wrong moment 0, wrong number 0, unclear 3.
- Precision: 97 of 100 = 97 % (interval 91.5 to 99.0 %). Unclear rows count as not right.
- False low calls: 66 of the 100 pairs. Right: 63 of 66 = 95.5 % (interval 87.5 to 98.4 %). All 3 unclear rows are false low calls.
- Unclear, report 25477901 (Abbott): two scans (50 and 65) against one reading (180) on an "unknown device". The patterns took 50.
- Unclear, report 20734005 (Abbott): the comparison readings are written as "obtained on a FreeStyle Libre scan", not on a meter.
- Unclear, report 8582753 (Dexcom): ranges ("42-58" against "142-177"). The patterns paired the two low ends. No single moment is stated.
- Why it is so high: 85 pairs come from Abbott's template and 12 from Dexcom's 2019-2021 template. Both name the sensor value and the meter value in one sentence.

## Reading rules and limits
- What was read: the event description in full. In the maker's narrative, every sentence that holds a number (the rest is stock wording).
- "Same moment": the templates state no clock time. A comparison written in one sentence ("X compared to Y respectively") was accepted as the same moment.
- Lists: 23 of the 100 texts list several pairs. The first sensor value against the first meter value was accepted (21 right, 2 unclear).
- mmol/L: the patterns converted 21 of the 100 pairs (times 18). All 21 conversions were checked and are right.
- "Comparison device": 23 of the 85 Abbott pairs call the reference "the comparison device" and never say "meter". These were accepted as right. If a person does not accept them, the count is 74 of 100 (interval 64.6 to 81.6 %). The paper should say which reading it uses.
- Thin spots: 1 of the 100 pairs comes from a version 2 form (the range row). 0 come from two-sentence patterns (353 of the 191,112 pairs). Dexcom (13) and Medtronic (2) are too few for a number per maker.
- This sample says nothing about death or injury pairs (18,237). `REGEX_V2_FULL_CORPUS.md` section 4 found pairs from two moments there.

## Files and how to re-run
- `python -B fda-maude/scripts/pattern_precision.py sample` re-draws the same 100 reports and keeps the verdicts. With `texts --batch 1` instead of `sample`, it prints 10 report texts to the screen for a re-check (batches 1 to 10).
- `python -B fda-maude/scripts/pattern_precision.py stats` re-builds every count in `pattern_precision_stats.json` (about 20 seconds).
- Check done: the current pattern script was re-run on the 287 reference reports and the 100 sampled reports. It gives the saved values in 387 of 387.
