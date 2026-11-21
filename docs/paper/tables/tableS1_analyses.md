# Table S1. Every analysis we ran

This table goes in the supplementary material, after the references. It does not count toward the page limit.

Text to print above the table:

Each row is one group of analyses. It gives the question we asked, what we did and what we found. The last column names the finding in the paper that the row feeds (R1 to R5). "Did not change the conclusions" means we ran the analysis and its result is not part of a finding. The repository holds the full list, with one analysis per row.

| # | Question | What we did | What we found | Used in |
|---|---|---|---|---|
| | **FDA reports** | | | |
| 1 | How many sensor reports exist, and what problems do they describe? | We downloaded every FDA report filed under the 13 product codes for glucose sensors and counted the problem codes that the FDA gives each report. We repeated the download from the FDA's bulk files as a check. | There are 3,382,071 reports. A wrong reading is the most common problem in serious reports, named in about 1 in 3 of them (33.1 %). | R3 |
| 2 | Can a program read the report texts reliably? | We searched each text with fixed text patterns and then had a language model, run on our own computer, fill in a fixed form for each report. We compared the results with 287 reference reports. An AI reader also checked 100 of the pairs found by the patterns against their texts. | The program agreed well with the reference reports. Kappa, a score of agreement beyond chance where 1 is perfect, was 0.77 for the type of fault and 0.75 for severity. Of the 100 checked pairs, 97 were right and none was wrong. | R3 |
| 3 | How far off was the sensor in serious reports? | We read 124,599 report texts and kept every report that states both the sensor value and the meter value. We compared the two values in each of these pairs, and we compared the two main makers. | In the typical report where the sensor read low, it read 77 % too low for Abbott and 69 % too low for Dexcom. | R3 |
| 4 | What errors do malfunction-only reports describe? | We ran the text patterns over all 3,382,071 reports and checked the result against a weighted sample of reports. | We found 191,112 pairs. In about 3 in 4 of them the sensor read low, and the typical one of these read 69 % too low. | R3 |
| 5 | How do reported errors compare with the errors of a working sensor? | We counted how often the trial sensor made errors as large as the reported ones, and we placed the reported errors on the curve of finding R1. | Errors this large are rare for a working sensor. A reading 69 % or more too low came up in about 1 meter check in 870. Over 26 weeks, 1 trial participant in 4 had at least one. | R3 |
| 6 | Who are the reports about, and on which day of wear do they happen? | We counted how often the age and sex fields are filled in, compared the reported errors by age and sex, and counted the days of wear that the reports name. | Of the reports that give an age, about 1 in 6 concerns a child under 18 (17.5 %). The reported errors differed little by age or sex. Abbott serious reports name the first day of wear about twice as often as an even spread over 14 days would give, but Dexcom serious reports do not, so the reports do not settle the wear-day question. | R5 |
| 7 | Do recalls, the country of the report, error grids or what users did change the picture? | We counted recalls and countries. We checked the error-grid zones that some reports state (an error grid rates each error by its risk for treatment). We read the fields for user actions, outcomes and harm. | No. For example, there were 32 recall events for glucose sensors, and about 2 in 3 of all reports come from the United States (63.8 %). | did not change the conclusions |
| | **Working sensor (trial data)** | | | |
| 8 | Which sensor-meter pairs make a fair test? | We kept only meter values that came from the meter's own log and were not used to calibrate the sensor, which means to adjust it with a meter value. This replaced a first check that used all pairs. | We kept 168,990 of 475,502 pairs, from 226 participants. | R2 |
| 9 | How accurate is a working sensor? | We calculated MARD, the average direction of the error, the share of readings close to the meter, and the seven FDA accuracy criteria for sensors that feed dosing systems (iCGM criteria). We chose these measures from a review of published accuracy studies. | MARD was 13.3 %. On average the sensor read 1.3 % too low. It failed all seven of the iCGM limits we could test. | R2 |
| 10 | Where is the error largest, and how far does the sensor run behind? | We calculated MARD in five glucose ranges, and we sorted the pairs into ranges in three ways, by the meter value, by the sensor value and by the average of both. We shifted the pairs in time to find the sensor's delay, and we split the error by how fast glucose was changing. | MARD was largest under 54 mg/dL under every sorting (19.6 to 37.5 %). The sensor runs 5 to 7 minutes behind the meter. When glucose was changing fast MARD was about 18 %, against 12 % when it was stable, and this gap is the delay. | R2, R5 |
| 11 | How often is a true low not shown as low? | For every meter check we compared which side of 70 mg/dL and of 180 mg/dL the meter and the sensor were on. We did this for the sensor reading at that moment, and again for any sensor reading within 15 minutes. | Of 10,104 meter lows, the sensor did not show a low at that moment in about 3 in 10 (31.4 %). Within 15 minutes it still had not shown a low in about 2 in 10 (18.5 %). | R2 |
| 12 | Do meter error, the time of day or the study site change the picture? | We added the largest meter error that the meter standard allows (ISO 15197). We split the sensor error by day and night and by study site. We also calculated the limits of agreement, which is the range that holds 95 % of the differences between sensor and meter. | No. For example, meter error adds at most 1.9 points to MARD, and the sensor was no less accurate at night. | did not change the conclusions |
| 13 | Is the first day of wear worse, and why? | We calculated MARD for each day of wear, followed the same sensors across their days, looked at when each sensor was calibrated, and fitted one model with all of these together. | MARD was 15.2 % on day 1 and 11.8 % on day 7. Almost all of the gap (92 %) is the sensor settling in, and very little is poor sensors being removed early. | R5 |
| 14 | Does who the participant is predict the error? | We ran 680 planned tests of a participant trait against a measure of error, with a correction for running many tests. We also tried prediction models and followed up the one difference by sex. An earlier version tested six traits. | After the correction, 1 of the 680 tests remained. At low glucose the sensor read 6.4 % too low for women and 2.2 % too low for men, a difference of about 2.5 mg/dL. | R5 |
| 15 | Is the picture the same in a second population with a different sensor? | We calculated the same accuracy measures on 4,012 pairs from 98 patients in the Shanghai data, and we ran 60 trait tests. | MARD was 13.9 %, and the sensor read 7.4 % too low on average. No trait predicted the error. | R5 |
| | **Simulation** | | | |
| 16 | How wrong must a sensor be before a dose changes? | We made every sensor reading too low by the same steady amount, from 0 up to 90 % too low, and recalculated 159,878 dose-calculator decisions each time. This replaced an earlier count of wrong readings. | Insulin corrections begin to be withheld when the sensor reads about 12 % too low. | R1 |
| 17 | Do other kinds of fault, or summary measures, change the picture? | We simulated six kinds of fault from an earlier version of the simulation, among them noise, drift, dropouts and delay. We also calculated time in range and looked at which participants were affected most. | No. A steady error changed doses the most. Noise kept 13 to 14 in 100 low episodes from being shown. | did not change the conclusions |
| 18 | What does each reported fault do in six hours? | We put the false low, the hidden low and the floor-pinned fault on real glucose traces for 2, 6 and 12 hours, and counted what a person following the standard rules would do differently. | Each fault breaks a different decision. The false low prompts unneeded sugar, the hidden low removes a low alert, and the floor-pinned sensor withholds the most insulin (Figure 5). | R4 |

## Which analyses each row covers

Numbers are the row numbers of `docs/paper/FACT_SHEET.md` section E. The same numbers are used in `tableS1_full.md`.

| Table row | Section-E rows | What they are |
|---|---|---|
| 1 | 1, 2, 8 | access check, pull and counts, second pull from bulk files |
| 2 | 6, 9, 10, 11, 12, 13, 72 | keyword count (replaced), choice of method, pilot, reference set, agreement check, repeat run, precision of the patterns |
| 3 | 14, 15, 21, 22, 23 | full text run, how far off, maker comparison, by year, and its checks |
| 4 | 25, 26, 28 | pattern tuning, patterns over all reports, weighted sample check |
| 5 | 19, 20, 70 | reported errors on the curve (first and extended version), trial errors against reported errors |
| 6 | 5, 17, 24 | age and sex fields, wear day in complaints, errors by age and sex |
| 7 | 3, 4, 7, 16, 18, 27, 29, 73 | recall timeline, recalls, country, error-grid zones, actions and outcomes, harm coding, field inventory, recall count and date check |
| 8 | 30, 33, 34 | first data check (replaced), pair cleaning, pump-entry check |
| 9 | 32, 35, 37 | methods review, overall accuracy, iCGM criteria |
| 10 | 36, 42, 43, 44, 48, 74 | accuracy by range, delay scan, low range after delay correction, rate of change, choice of glucose axis, three ways of sorting pairs into ranges |
| 11 | 38, 71 | wrong side of 70 or 180 mg/dL, low detection with a 15-minute window |
| 12 | 39, 40, 46, 53 | limits of agreement, meter error, time of day, study site |
| 13 | 45, 47, 60, 61 | wear day, joint model, settling against early removal, calibration timing |
| 14 | 49, 50, 51, 52, 54, 55, 56, 58, 59 | first six traits, glucose pattern, extra traits, 680 tests, prediction models, indirect effects, worst quarter, medications, sex follow-up |
| 15 | 41, 57 | Shanghai accuracy, Shanghai trait tests |
| 16 | 31, 62, 64, 65, 68 | simulation version 1 (replaced), steady-error sweep, meter as the true value, high line at 180 or 200, sweep extended to 90 % too low |
| 17 | 63, 66, 67 | six fault kinds, who gets most false low alerts, time in range and risk indexes |
| 18 | 69 | three-fault simulation |

All 70 section-E rows and the four checks added on 2026-11-21 are covered. Each is in one table row only.

## Notes for the writer

- This file was `table3_analyses.md` until 2026-11-21. Artemy asked for full sentences in "What we did", no semicolons, and a move to the supplement.
- Kappa is explained inside row 2. MARD, iCGM and "serious report" are explained in the paper before the table.
- Rows 7, 12 and 17 hold the analyses that the last Results paragraph names. They are the time of day, the study site, error grids, the country of the report and the earlier fault kinds. The rate of glucose change moved to row 10 on 2026-11-21, because it does move the error (it is the sensor's delay).
- Row 5 rests on 57 of 225 participants in the 26 randomised weeks. Per check it is 159 of 137,662 meter checks.
- Row 6. The 17.5 % is a share of all sensor reports that record an age. Abbott serious reports that name a wear day name day 1 in 13.4 % of cases, and an even spread over 14 days gives 7.1 %.
- Row 3 uses 69 % for Dexcom (the pair set of the maker comparison). The first text memo gives 68 % on a slightly different pair set.
- Row 4. The 69 % is the median over the 142,817 pairs that read low. The median over all 191,112 pairs is 66 % too low, and the paper does not use it.
- Row 10. The paper sets glucose ranges by the average of the sensor and meter value (`docs/paper/CHECKS.md`, block 6). The row's question was changed from "is it only delay?" because the row does not answer that.
- Row 4, to check before the build: what the "weighted sample" was read by (the language model or a person).
