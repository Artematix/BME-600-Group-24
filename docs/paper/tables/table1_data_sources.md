# Table 1. The data sources

Built 2026-11-20 for the Methods section. Shortened 2026-11-21 after Artemy's review ("a tiny bit too wordy"). Every fact comes from `docs/paper/FACT_SHEET.md`.

| Source | What it holds | Device | Size | What counts as one case | Who is in it | What we used it for |
|---|---|---|---|---|---|---|
| REPLACE-BG trial | US adults with type 1 diabetes on insulin pumps, 2015 to 2016. Sensor readings, meter values and dose-calculator records. | Dexcom G4 Platinum sensor, Contour Next meter | 226 participants, 168,990 pairs | One participant, who gives many pairs (median 719) | Age 19 to 78, 50 % are women, 94 % are White | Accuracy of a working sensor, what predicts error, and the glucose traces and dose decisions for the simulations |
| Shanghai data | Adult in-patients of two Shanghai hospitals, 12 with type 1 and 100 with type 2 diabetes. Sensor readings and meter values. | Abbott FreeStyle Libre H sensor, meter not named | 112 patients, 98 of them with pairs, 4,012 pairs | One patient (median 37.5 pairs) | Age 22 to 97, 46 % are women, all are Chinese | Accuracy in a second population |
| FDA MAUDE problem reports | Reports of sensor problems sent to the US FDA from March 1992 to September 2026, with coded fields and free text | All brands under 13 sensor product codes | 3,382,071 reports, 123,607 of them serious. 207,771 report pairs (16,659 in serious reports, 191,112 in malfunction-only reports). | One report. One event can produce several reports. | 64 % of reports come from the US. Age is filled in for about 73 % of reports, sex for 46 %, race or ethnicity for 0.3 %. | How far off the sensor was in reported failures, and the three faults for the second simulation |

No note is printed under the table (changed 2026-11-21). The terms pair, report pair, serious report and malfunction-only report are defined in the Methods text just before the table. The recall records (32 recall events) are no longer named here. They feed no finding and stay in Table S1.

## What changed on 2026-11-21

- The fourth row (FDA recall records) is now one note line. Reason: the paper speaks of three data sources, Figure 1 shows three, and the recall count feeds no finding.
- Dropped from the cells: the number of clinics, the candidate pair count (now a note), the 124,599 texts read (it is in Methods and Results), the fill rates for the 39,667 serious wrong-reading reports (they are in Results 3.5), and the harm counts of the Libre 3 recall (they are in the Introduction).
- Size now: longest cell 24 words, all 21 cells together about 210 words (was 320).

## Sources

Line numbers are lines of `docs/paper/FACT_SHEET.md`. "A1 Population" means section A1, row "Population". "derived" means worked out from numbers in that line.

REPLACE-BG trial

- What it holds: A1 Population (line 29), A1 Main variables (line 35).
- Device: A1 Sensor (line 31), A1 Reference meter (line 32).
- Size: 226 from A1 Population (line 29). 475,502 from B, Trial step 2 (line 77). 168,990 from B, Trial step 5 (line 80).
- One case is: A1 Independent case (line 34).
- Who is in it: A1 Population (line 29). "Half" is derived (112 of 226 = 49.6 %). 94 % is 212 of 226.
- What we used it for: D2 (line 224), D5 (lines 362 to 372), C3 True glucose and "A decision" (lines 150 and 152).
- Inclusion rule: B, Trial steps 2 to 5 (lines 77 to 80). The meter value comes from the meter's own log, was not used to calibrate the sensor, lies inside the study window, and has a sensor reading within 5 minutes.

Shanghai data

- What it holds: A2 Population (line 46), A2 Main variables (line 50).
- Device: A2 Sensor (line 47). "Meter not named" is also in section H, item 3 (line 539).
- Size: 112 from A2 Population (line 46). 98 and 4,012 from B, Shanghai step 2 (line 84).
- One case is: A2 Independent case (line 49).
- Who is in it: A2 Population (line 46). All three facts describe all 112 patients, not only the 98 with pairs.
  - Age 22 to 97 is derived (type 1: 37 to 73, type 2: 22 to 97).
  - 46 % is derived (51 of 112 = 45.5 %, 51 = 7 + 44).
- What we used it for: D5, row "Shanghai" (line 373).

FDA MAUDE problem reports

- What it holds: A3 MAUDE scope and population (line 60), A3 MAUDE main variables (line 63).
- Device: A3 MAUDE scope and population (line 60).
- Size:
  - 3,382,071 from B, MAUDE step 1 (line 86).
  - 123,607 from B, MAUDE step 2 (line 87).
  - 16,659 is derived: Abbott 7,470 + Dexcom 9,189, from B, MAUDE step 8 (line 93).
  - 191,112 from B, MAUDE step 10 (line 95).
  - 207,771 is derived: 16,659 + 191,112. It leaves out 914 serious pairs from other makers (Medtronic 379, Senseonics 532, other 3, line 93).
- One case is: A3 MAUDE independent case (line 61), A3 "many records per event?" (line 62).
- Who is in it: 63.8 %, 73.8 %, 45.7 % and 0.3 % from A3 MAUDE scope and population (line 60). Each is a share of all 3,382,071 reports.
- What we used it for: D3 (lines 282 to 321), C3 "Three faults: FDA source of each size" (line 157).

Recall note: 32 events from `fda-maude/results/RECALL_COUNT_CHECK.md` (confirmed by Artemy 2026-11-21).

## Points to settle before this table goes into the paper

- The fact sheet has two versions of the fill rates for all reports. Line 60 gives age 73.8 % and sex 45.7 %. Line 411 gives age 73.4 % and sex 46.6 %. The table says "about 73 %" and "46 %".
- The Shanghai row says 112 patients. Figure 1 says 98 patients. Both are right, because 98 of the 112 have a pair.
