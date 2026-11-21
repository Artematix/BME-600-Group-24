# Table S1, full list: every analysis we ran

- This is the full list behind Table S1 of the paper (`docs/paper/tables/tableS1_analyses.md`). Until 2026-11-21 the two files were called `table3_analyses.md` and `table3_full.md`.
- One row = one analysis. 70 rows.
- Row numbers are those of `docs/paper/FACT_SHEET.md` section E. Every result is taken from that fact sheet.
- Rows are grouped as in the paper table, so the numbers are not always in order.

## Words used

| Word | Meaning |
|---|---|
| Sensor | The continuous glucose monitor (CGM). It reads glucose under the skin every 5 minutes. |
| Meter | The fingerstick meter. It is the reference. |
| Pair | A sensor value and a meter value for the same moment. In a report: a report that states both. |
| Serious report | A report of a death or an injury. |
| Malfunction-only report | A report with no death or injury. |
| Reads X % too low | The sensor value is X % below the meter value. |
| MARD | The average distance between sensor and meter, ignoring direction, as a percentage of the meter value. |
| Typical participant | The median across participants. "Middle pair" = the median pair. |
| 95 % interval | The range that holds the true value with 95 % confidence. |
| Kappa | Agreement beyond chance. 1 = perfect, 0 = chance. |
| p-value | The chance of a result this large if there is no real effect. Under 0.05 counts as a signal. |
| Corrected p-value | The p-value after the Benjamini-Hochberg correction, which allows for running many tests. |
| Calculator decision | One recorded use of the pump's dose calculator. |
| Used in | The finding of the paper that the analysis feeds. |
| Did not change the conclusions | We ran it. Its result is not part of a finding. |

The five findings:
- R1: insulin corrections start to be withheld when the sensor reads about 12 % too low.
- R2: a working sensor reads only 1.3 % too low on average, but about 3 in 10 true lows are not shown as low.
- R3: in reported failures the sensor is typically 69 to 77 % too low, and the failures are three faults.
- R4: each fault breaks a different decision.
- R5: error follows wear day and glucose range, not who the patient is.

## The list

| # | Question | What we did | What came out | Used in |
|---|---|---|---|---|
| | **FDA reports** | | | |
| 1 | Which way of getting the FDA reports works? | Live tests of the openFDA service, the bulk files, the FDA website and the recall records. | The openFDA service works. 13 product codes cover glucose sensors. About 3.4 million reports; a free key is needed. | R3 |
| 2 | How many reports are there, and about which problem, maker and year? | Pulled every report for the 13 sensor product codes. Counted the FDA's coded fields. | 3,382,071 reports. A wrong reading is the most common problem type in serious reports: 33.1 % of serious reports. | R3 |
| 3 | Did reports rise around the recalls? | Counted serious reports per month, by date received and by date of the event. | Libre 3 sensors: 6,785 serious reports received since 2025-11-24. 2,638 of them are coded "Low Readings". | did not change the conclusions |
| 4 | How many sensor recalls are there, and of which class? | Grouped the FDA recall and enforcement records by recall event. | 32 recall events (33 after the records were refreshed on 2026-10-26). 7 are Class I, the most serious class. | did not change the conclusions |
| 5 | Who are the reports about? | Counted how often the FDA age and sex fields are filled in. | Age is filled in for 73.4 % of reports; the middle age is 52. Sex is missing in 53.4 % of reports. Of the reports with an age, 17.5 % concern a person under 18. | R5 |
| 6 | Do the report texts mention low readings? | Searched the texts of serious reports for fixed words. | Low-reading words in 12.1 % of serious reports. Replaced by the text reading in rows 9 to 14. | did not change the conclusions |
| 7 | Where do the reports come from? | One count per country code from the openFDA service; two code lists merged. | The US gives 63.8 % of all reports and 44.3 % of serious reports. | did not change the conclusions |
| 8 | Do the FDA bulk files give the same data as the openFDA service? | Compared the totals per product code and the report tables of both pulls. | The same 3,382,071 reports. 24 of 33 tables are identical byte for byte. | did not change the conclusions |
| 9 | How should the report texts be read? | Compared six methods on cost, clarity and repeatability. | Chosen: FDA codes first, then text patterns, then a local language model that fills a fixed form. | R3 |
| 10 | Is this text reader fast and safe enough? | Ran the patterns and the model on 287 and on 500 reports. Timed them. | About 300 reports per minute. 2 to 6 % of the model's answers held a number that the text did not support. | R3 |
| 11 | What is the text reader checked against? | One AI reviewer labelled 287 reports with a written rubric. This is the reference set. | The reviewer labelled 40 of them again without seeing the first labels: 100 % of the labels agreed. A teammate checked 100 of the 287 and found no issues. | R3 |
| 12 | Does the text reader agree with the reference set? | Kappa per field and per maker, for three versions of the model's instructions. | Version 3: kappa 0.77 for fault type and 0.75 for outcome severity. 96.2 % of the numbers it gave were exactly right (307 of 319). | R3 |
| 13 | Does the model give the same answer twice? | Two runs with the same settings, compared field by field. | 90.6 % of the filled forms were identical in all ten fields. | did not change the conclusions |
| 14 | What do the 124,599 report texts say? | Patterns plus the model. A number counts only if it stands word for word in the text. | 15.6 % of serious reports state both the sensor value and the meter value. 16.0 % of serious reports say the sensor read low. | R3 |
| 15 | How far off was the sensor in the reports? | Sensor value against meter value for each pair. Middle pair and middle half of pairs. | Among pairs that read low, the middle pair read 77 % too low for Abbott and 68 % too low for Dexcom. The pair set of row 21 gives 69 % too low for Dexcom; the paper uses that one. | R3 |
| 16 | Do the error-grid zones that makers state match the numbers? | Worked out the Parkes error-grid zone from each stated pair. The grid grades the risk of an error from A to E. | Of the stated zones, 87.1 % equal the worked-out zone and 96.8 % are within one zone. | did not change the conclusions |
| 17 | On which day of wear do complaints fall? | Share of reports that name each wear day, against an even spread over the wear time. | Abbott serious reports that name a day: 13.4 % name day 1 (an even spread gives 7.1 %). Dexcom: 7.1 % name day 1 (an even spread gives 10 %). | R5 |
| 18 | What did people do, and what happened to them? | Fields filled by the model, compared with the FDA outcome codes. | In reports where the sensor read low, 27.7 % say the person ate carbohydrate. 53.8 % of all serious reports were read as "hospital or ER", which here means any medical care. | did not change the conclusions |
| 19 | What would the reported errors do to treatment decisions? | Weighted the rows of the steady-error lookup (row 62) by the reported errors. The lookup stopped at 40 % too low. | Abbott: 31.3 % of calculator decisions lose their correction. This is a lower limit. Replaced by row 20. | did not change the conclusions |
| 20 | The same question, without the stop at 40 % too low. | The lookup was extended to 90 % too low (row 68). Same weighting. | Abbott, typical participant: 49.3 % of calculator decisions lose their correction, and 96.4 % of high episodes are not shown as high. | R3 |
| 21 | Do the makers' sensors fail differently? | Rank tests, effect measures and bootstrap intervals on 17,573 pairs from serious reports. | Equally far off: the middle pair is 86 % away from the meter value (Abbott) and 87 % away (Dexcom). Abbott pairs read low more often: 57.8 % against 43.8 % of pairs. In Dexcom pairs the meter is more often under 70 mg/dL: 45.7 % against 28.1 % of pairs. | R3 |
| 22 | Is the gap between makers stable over the years? | Share of pairs that read low, per year and per recall window. | Over all years, Abbott pairs read low 14 points more often than Dexcom pairs. In 2026 the gap is 2 points (64 % against 62 % of pairs). | did not change the conclusions |
| 23 | Is the maker difference caused by Abbott's report template, by the sample or by the year? | Template reports against free-text reports; serious reports against the sample; year by year. | The template does not change the numbers (difference 0.00). | did not change the conclusions |
| 24 | Do age or sex change the complaints? | The same tests by age group and by sex. | Of serious wrong-reading reports with an age, 11.7 % concern a person under 18. The sensor read low in 54.6 % of reports for under-18s against 42.6 % for people of 65 and over. Sex made almost no difference. | R5 |
| 25 | Can text patterns alone find the pairs? | New patterns tuned against the model's output and checked by eye. | The patterns find 89.1 % of the pairs the model found. Before tuning: 73.1 %. | R3 |
| 26 | What errors are in malfunction-only reports? | The tuned patterns ran over all 3,382,071 reports. | 191,112 pairs in malfunction-only reports. The middle pair reads 66 % too low. 75 % of the pairs read low. | R3 |
| 27 | Are larger errors more often filed as serious reports? | Share of pairs that sit in serious reports, by how far off the sensor was. | U-shaped: the share is high at both ends. Part is real and part is how reports get coded. Not settled. | did not change the conclusions |
| 28 | Does the sample of malfunction reports match the full set of reports? | Bootstrap intervals from the weighted sample, set against the full counts. | Every full count falls inside the sample's interval except one: the share of Dexcom reports with a pair (0.57 % in the sample, 1.05 % in the full set). | did not change the conclusions |
| 29 | What else do the reports hold? | Fill rates of the fields; 300 texts read; 52 theme patterns. | Where a device was returned, the text says "no defect found" for 81 % of the returned devices. Running the model on malfunction-only texts is not worth it. | did not change the conclusions |
| 70 | How often does a working sensor make an error as large as the reported ones? | Trial pairs counted at the error levels found in reports. Intervals by resampling participants. | The trial sensor read 69 % or more too low in 0.11 % of meter checks (95 % interval 0.073 to 0.15). Only 3.25 to 11.4 % of report pairs lie inside the range that holds 95 % of trial pairs. | R3 |
| | **Working sensor (trial data)** | | | |
| 30 | What is in the trial data, and how accurate is the sensor at first look? | Every meter value paired with the sensor, including calibration values and values typed into the pump. | 475,502 pairs; MARD 10.4 %. Replaced by rows 33 and 35. | did not change the conclusions |
| 32 | Which methods do sensor accuracy papers use? | Literature check against our plan. | A priority list was adopted: confidence intervals, the iCGM table, sensor delay, decisions. | R2 |
| 33 | Which sensor-meter pairs are a fair test? | One shared cleaning step. Values typed into the pump and meter values used to calibrate the sensor were removed. | 168,990 of 475,502 pairs kept. MARD went from 10.4 % to 13.3 %. | R2 |
| 34 | Are the glucose values typed into the pump real meter values? | Share of pairs where the sensor value and the other value are exactly equal, by source and study arm. | 36.9 % of pump-entry pairs are exactly equal, against 2.2 % of meter-log pairs. Many pump entries are sensor values typed into the pump. | R2 |
| 35 | How accurate is a working sensor? | MARD, average error and agreement shares. Intervals by resampling participants. | MARD 13.3 % (95 % interval 12.7 to 13.9). On average the sensor reads 1.3 % too low. All 226 participants. | R2 |
| 36 | Where is the error largest? | Pairs grouped by glucose range, using the average of sensor and meter. | MARD 19.6 % under 54 mg/dL against MARD 10.3 % over 250 mg/dL. | R2 |
| 37 | Does the sensor meet the FDA limits for sensors that feed dosing systems (the iCGM criteria)? | Pairs grouped by sensor value. The lower one-sided 95 % bound must pass. | It meets none of the 7 criteria. Example: 81.7 % of pairs are within 20 % of the meter value (81.5 % in the 77-person check arm); the rule needs more than 87 % of pairs. | R2 |
| 38 | How often is a reading on the wrong side of 70 or 180 mg/dL? | Table of the meter category (low, in range, high) against the sensor category. | 31.4 % of meter lows were not shown as low (3,177 of 10,104). In the 77-person check arm: 28.2 % of meter lows. | R2 |
| 39 | How far can one reading sit from the meter? | Bland-Altman limits of agreement: the range that holds 95 % of the differences. Many pairs per participant are allowed for. | From 67 mg/dL below the meter to 57 mg/dL above it (77-person check arm). | did not change the conclusions |
| 40 | Could meter error explain the results? | Random error as large as the ISO 15197 limit for meters was added to the meter values. | MARD rises by at most 1.9 points. The average error in the low range moves toward zero. | did not change the conclusions |
| 41 | Is the picture the same with a second sensor and population (Shanghai)? | The same measures on 4,012 pairs from 98 patients. | MARD 13.9 %. On average the sensor reads 7.4 % too low. | R5 |
| 42 | How far does the sensor run behind the blood? | Each meter value was paired again with sensor readings from 5 minutes earlier to 20 minutes later. | The best match is a shift of 5 minutes on real readings and 7 minutes on the trace filled in between readings. | R2 |
| 43 | Does the sensor still read too low in the low range once the delay is removed? | Each meter value paired with the sensor reading 5 minutes later. | Under 54 mg/dL the sensor still reads 6.5 % too low (95 % interval 5.1 to 7.9). | R2 |
| 44 | Is fast-changing glucose a separate fault? | Average error and MARD by how fast glucose was moving, before and after the 5-minute shift. | Glucose falling fast: the sensor reads 12.7 % too high as paired and 0.7 % too high after the shift. | did not change the conclusions |
| 45 | Is the first day of wear worse? | MARD by day of wear, in sensor sessions with a confirmed start. | MARD 15.2 % on day 1 against MARD 11.8 % on day 7. | R5 |
| 46 | Is the sensor worse at night? | Night against day, for all pairs together and per participant. | All pairs together: MARD 14.3 % at night, MARD 13.2 % by day. Per participant there is no difference: for the typical participant, night MARD is 0.2 points lower. | did not change the conclusions |
| 47 | Which factors add error when counted together? | A regression on 143,051 pairs that knows which pairs belong to the same participant (a mixed model). | Extra error, in points of percent error: 5.8 under 54 mg/dL, 2.3 on wear day 1, 0.9 at night. | R5 |
| 48 | Does the way pairs are grouped by glucose change the direction of the error? | The same pairs grouped three ways. | Under 54 mg/dL the sensor reads 29.8 % too high when grouped by meter value, 22.5 % too low by sensor value, and 5.2 % too low by the average of both. | R2 |
| 49 | Do six participant traits predict MARD? | MARD per participant, compared by group, with the correction for many tests. | No trait passes the correction (smallest corrected p-value 0.15). | R5 |
| 50 | What does predict a participant's MARD? | Rank correlation per participant (0 = no link, 1 = perfect link). | Glucose swings and time under 70 mg/dL each go with a higher MARD: correlation 0.33. | did not change the conclusions |
| 51 | Do other traits matter? | 22 more tests, with the same correction. | One passed. It was gone after adjusting for age and glucose swings. | R5 |
| 52 | Does any trait, pair of traits or study site predict error? | 680 tests listed before any was run. One correction for all of them. | 1 of 680 remains: sex against the average error in the low range (corrected p-value 0.016). 69 passed before the correction; chance alone gives about 34. | R5 |
| 53 | Does the clinic matter? | Share of the spread in MARD that lies between the 14 sites; a permutation test. | 3.5 % of the spread in MARD lies between sites (p-value 0.10). | did not change the conclusions |
| 54 | Is there a hidden pattern that single tests miss? | Three flexible prediction models (forest, boosting, ridge), each tested on participants it had not seen. | Traits predict nothing (R-squared below 0). The glucose pattern predicts little (R-squared 0.03). R-squared = the share of the spread that is explained. | R5 |
| 55 | Does a trait act on MARD through the glucose pattern? | Indirect effects in standard-deviation units, with bootstrap intervals. | Age, through the glucose pattern: MARD is lower by 0.07 standard deviations (95 % interval 0.03 to 0.12 lower). | did not change the conclusions |
| 56 | Who is in the worst quarter of participants? | 140 tests of the worst quarter against the rest. | No trait passes the correction. | R5 |
| 57 | Do traits matter in the Shanghai data? | 60 tests with their own correction. | Nothing passes (smallest corrected p-value 0.97). | R5 |
| 58 | Is "more drugs, lower MARD" real? | Adjusted for age and glucose pattern. | Gone after the adjustment (0.12 MARD points lower per drug, p-value 0.36). | R5 |
| 59 | Is the gap between women and men in the low range real? | 74 tests listed in advance. Matching on glucose level and trend. Adjustment for body size, HbA1c, age and insulin dose. | Under 70 mg/dL the sensor reads 6.4 % too low for women and 2.2 % too low for men: a gap of 4.2 points. After matching: 3.7 points. In the 77-person check arm there is no gap (0.6 points). | R5 |
| 60 | Why is day 1 worse: the sensor settling, or poor sensors removed early? | Sensor sessions rebuilt; the same sensors compared across days. | Settling is 92 % of the day-1 excess (95 % interval 85 to 100). Early removal is 8 % of it. | R5 |
| 61 | Does the timing of calibration explain day 1? | Error by time since the last calibration. | No. Day 1 is worse at every time since calibration. Just before a calibration the error is 19.3 % of the meter value on day 1 against 11.9 % on day 7. | R5 |
| | **Simulation** | | | |
| 31 | How many readings change side under a steady low error? | Version 1: every reading made steadily too low; lines at 70 and 200 mg/dL. | Sensor reads 20 % too low: 17.2 false low readings and 39.8 missed high readings per day. Replaced by row 62, which counts decisions. | did not change the conclusions |
| 62 | What does a steady error do to decisions? | Version 2: each recorded use of the dose calculator worked out again with the wrong reading. Steady error from 40 % too low to 40 % too high. | Sensor reads 20 % too low: 7.2 % of calculator decisions lose their correction (13.5 % of the corrections that were needed), and 50.8 % of high episodes are not shown as high. | R1 |
| 63 | Which kind of fault changes decisions most? | Six other kinds of fault (two kinds of noise, drift, dropouts, delay, a mix), 10 random draws per participant. | A steady error changes doses most. Noise with a spread of 10 mg/dL hides 13 to 14 % of low episodes. | did not change the conclusions |
| 64 | What if the true value is the meter and not the sensor trace? | 15,034 calculator decisions that have a verified meter value (67 participants). | Working sensor, no fault added: 2.1 % of the corrections that were needed are withheld; 4.2 % of all calculator doses change by more than 1 unit. Sensor reads 20 % too low: 23.8 % of needed corrections withheld, against 13.5 % in row 62 (`docs/paper/CHECKS.md`, block 1). | R1 and R2 |
| 65 | Which high line, 180 or 200 mg/dL? | The same outcomes at both lines. | Sensor reads 20 % too low: 51 % of high episodes are not shown as high at 180 mg/dL, 59 % at 200 mg/dL. | R1 |
| 66 | Who gets the most false low alerts? | Rank correlation with each participant's glucose measures. | Participants with a lower average glucose get more false low alerts (correlation strength 0.74). | did not change the conclusions |
| 67 | Does a sensor that reads too low make glucose control look better? | Time in range and risk indexes worked out on the displayed trace. | Sensor reads 20 % too low: time in range goes from 63.3 % to 74.8 % of the time. The low blood glucose index (LBGI, a risk score for lows) goes from 0.95 to 2.33. | did not change the conclusions |
| 68 | What happens when the sensor reads more than 40 % too low? | Steady error from 90 % too low to 90 % too high, in steps of 2 points. | From 70 % too low on, 54.2 % of calculator decisions lose their correction. That is every correction that was needed. | R1 |
| 69 | What do the faults described in the reports do to decisions? | False low, hidden low and floor-pinned put on real traces in episodes of 2, 6 and 12 hours. Each fault acts in its own glucose range. | Six hours, typical participant. False low: 20.3 unneeded sugar prompts. Hidden low: 33.7 minutes under 54 mg/dL while the display shows 70 or above. Floor-pinned: 1.29 units of insulin not given. | R4 |
| | **Checks added on 2026-11-21** | | | |
| 71 | Does the sensor show a true low a little before or after the meter check? | Any sensor reading under 70 mg/dL within 15 or 30 minutes of a meter value under 70, the way clinic studies count. | Not shown at the matched reading: 31.4 % of 10,104 meter lows. Not shown within 15 minutes: 18.5 %. Within 30 minutes: 16.1 %. | R2 |
| 72 | How often is a pair found by the text patterns right? | An AI reader read 100 random malfunction-only pattern pairs against their texts. Also compared with the reference set and with the language model. | 97 of 100 right, 3 unclear, 0 wrong (95 % interval 91.5 to 99.0). Reference set: 74 of 74 pattern pairs right. | R3 |
| 73 | Are there 32 or 33 sensor recall events, and when was the Libre 3 recall classified? | Compared the two pulls of the recall records; read the FDA enforcement data and the FDA notice. | 32 events: the 33rd is dosing software, not a sensor. Classified Class I on 13 January 2026; public notice updated 4 February 2026. | did not change the conclusions |
| 74 | Does the by-range picture depend on how pairs are sorted into ranges? | MARD and direction of error in five ranges, with pairs sorted by the meter, by the sensor, and by the average of both. | Under 54 mg/dL: MARD 37.5 % (meter), 25.7 % (sensor), 19.6 % (average). The direction flips: 29.8 % too high (meter), 22.5 % too low (sensor). MARD is largest under 54 under every sorting. | R2 |

## Notes

- A replaced analysis is tagged "did not change the conclusions". Its row names the row that replaced it.
- A clean check is also tagged "did not change the conclusions" (rows 8, 13, 22, 23, 28). In the paper table it sits in the family it checks.
- Row 64 feeds two findings: the check in R1 and the working-sensor doses in R2.
- Row 5: the fact sheet gives two sets of fill rates. Section E has age 73.4 % and sex missing 53.4 %. Section A3 has age 73.8 % and sex filled 45.7 %. This row uses section E.
- Row 15 and row 21: 68 % and 69 % too low for Dexcom come from two slightly different pair sets (fact sheet section D6).
- Row 37: section E quotes the 77-person arm (81.5 %). The value for all 226 participants (81.7 %) is from fact sheet section D2.
- Row 59: the 95 % interval of the gap is 2.0 to 6.0 points in one stats file and 2.0 to 6.3 in another (fact sheet section D6). It is left out here.
- Rows 71 to 74 were added on 2026-11-21 (row 74: `analysis/ACCURACY_BY_RANGE_SORTING.md`). They are checks made after the fact sheet was built: `analysis/LOW_DETECTION_WINDOW.md`, `fda-maude/results/text/PATTERN_PRECISION.md`, `fda-maude/results/RECALL_COUNT_CHECK.md` and `fda-maude/results/RECALL_DATE_CHECK.md`.

## Where each analysis is written up

| Rows | Memo |
|---|---|
| 1 | `fda-maude/access-check/` |
| 2 | `fda-maude/results/report/report_results.md`; `fda-maude/results/PULL_SUMMARY.md` |
| 3, 4, 5, 6 | `fda-maude/results/report/report_results.md` |
| 7 | `fda-maude/results/report/country_spread.md` |
| 8 | `fda-maude/DATA_NOTES.md` |
| 9 | `fda-maude/OPTIONS.md`; `fda-maude/METHODOLOGY.md` |
| 10 | `fda-maude/results/text/PILOT.md` |
| 11 | `fda-maude/gold/GOLD_SET.md`; `fda-maude/results/text/VALIDATION.md` |
| 12, 13 | `fda-maude/results/text/VALIDATION.md` |
| 14 to 20 | `fda-maude/results/text/TEXT_RESULTS.md` |
| 21 to 24 | `fda-maude/results/text/BRAND_COMPARISON.md` |
| 25 to 28 | `fda-maude/results/text/REGEX_V2_FULL_CORPUS.md` |
| 29 | `fda-maude/results/FIELD_INVENTORY.md` |
| 30 | `analysis/RESULTS.md` |
| 31 | `analysis/SIMULATION_RESULTS.md`; `analysis/SIMULATION_V2.md` |
| 32 | `analysis/METHODS_REVIEW.md` |
| 33 | `analysis/PREPROCESSING.md`; `analysis/ACCURACY_V2.md` |
| 34 | `analysis/ACCURACY_V2.md`; `analysis/SUBGROUPS.md` |
| 35 to 41 | `analysis/ACCURACY_V2.md` |
| 42 to 48 | `analysis/ERROR_DRIVERS.md` |
| 49, 50, 51 | `analysis/SUBGROUPS.md` |
| 52 to 58 | `analysis/DEMOGRAPHICS_DEEP.md` |
| 59 | `analysis/DEMOGRAPHICS_FOLLOWUP.md` |
| 60, 61 | `analysis/WEAR_DAY.md` |
| 62 to 68 | `analysis/SIMULATION_V2.md` |
| 69 | `analysis/SIMULATION_THREE_FAULTS.md` |
| 70 | `analysis/TAIL_COMPARISON.md` |
