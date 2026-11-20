# What is in the MAUDE reports that we have not used yet

Date: 2026-11-06 (tables and 300-report reading); patterns tightened and memo finished 2026-11-08. Script: `scripts/field_inventory.py`. Tables: `results/inventory/`. Method: `../METHODOLOGY.md` (entry 2026-11-06).

Words used here:
- Fill rate = share of reports where a field has a real value (not blank, "NA", "Unknown" or "*").
- Serious reports = death + injury reports (123,607; 122,657 have text). Malfunction sample = 6,137 random malfunction reports with text. "Weighted" = each sample report is scaled up to stand for all 2.92 million malfunction reports it was drawn from.
- Stratified sample = a random sample drawn in fixed numbers from each group (here: event type x maker), so small groups are not missed.
- Regex = a fixed text pattern a computer can match. Precision = of the texts the pattern flags, the share that really say it. Recall = of the texts that really say it, the share the pattern flags. Both were measured on the 300 texts I read.
- Reminder: MAUDE counts show who reports and how, not how often sensors fail.

## Summary (6 lines)

1. The clean tables already hold 88 columns, far more than the README says. Country per report, maker evaluation code, device returned or not, recall id, lot number and report source are all there and unused. Only two useful raw fields were dropped by the clean step: the device manufacture date (filled in 78 % of CGM records in the raw zip) and the date the device was returned (5 %). Adding them costs one small code edit and a 6 to 10 minute re-run.
2. Age and sex in MAUDE are a maker habit, not a patient fact: Dexcom fills age for 93 % and sex for 57 % of its reports; Abbott fills 7 % of both. Race and ethnicity are empty (0.3 %). The text does not rescue them (an age appears in 0.03 % of serious texts where the field is blank). Filled MAUDE ages are older than the trial: 28 % are 65+ (trial 8 %) and 17 % are under 18 (trial 0 %).
3. The 300 texts I read say a lot the 12-field form does not capture. The biggest themes: whether the device was returned (56 % say it was not; 20 % say it was) and what the maker found (41 % no defect or could not confirm; 16 % a cause or defect; 28 % cause not determined), symptoms (13 %), a carer or family member in the story (24 %), EMS or hospital (24 %), severe signs (13 %), an app or phone problem (10 %), alarm that did not sound or was not heard (8 %).
4. Patterns catch most of these at scale: 14 themes have precision 80 % or better on the 300. Over all serious reports: not returned 66 % (Abbott 86 %, Medtronic 83 %, Dexcom 23 %); where a device was returned the text says "no defect found" in 81 % (Abbott 98 %, Dexcom 75 %); EMS or hospital 38 %; a carer in the story 32 %; alarm failed 6 %; app or phone 9 %; skin reaction 18 % (Dexcom 27 %); pump automation acting on the reading 2 % (Dexcom G7 9 %).
5. Rare in the text, so not worth a model run: compression lows 0.3 %, interfering substances 0.9 %, timing in hours after insertion 1.2 %, maker telling the user to fingerstick 0.6 %. Common but already a form field: sensor error or early end (28 % of serious texts).
6. Reading more malfunction texts with the model would mostly add volume. 46 % of the 3.26 million malfunction texts are one of 241 identical templates, 237,000 Dexcom reports have no text at all, and the pattern layer (`REGEX_V2_FULL_CORPUS.md`) has already read the numbers in all of them. A full model run would take 250 GPU-hours. If anything, run the model on the 481,000 malfunction reports that carry a wrong-readings code and a real story (37 GPU-hours), or do the two human reads listed in part 5.

## Part 1. Fields: what the clean tables hold, and what the clean step dropped

### 1a. `clean/serious.csv.gz` (123,607 reports, 88 columns)

Full table with top values: `inventory/fill_rates_serious.csv`. The same for the weighted malfunction sample: `inventory/fill_rates_sample_weighted.csv`. Fill by maker, event type and year: `inventory/fill_rates_serious_by_group.csv`.

Always or nearly always filled (99 % or more): report key, report number, both dates (date of event 99.4 %), event type, product code, brand, maker, problem codes (99.1 %), patient problem codes, event text (99.2 %), report source code, type of report, device operator, device availability.

| Field | Fill % | What is in it | Used so far? |
|---|---|---|---|
| mfr_narrative (H10) | 95.7 | the maker's narrative; often template text | yes (text step) |
| reporter_country_code | 94.9 | 2-letter country of the reporter (US 44 %; GM = Germany 11,861; FR 8,835; UK 7,686) | no. README says it is missing; it is not |
| source_type | 96.8 | Consumer 85 %, Other 3 %, "Foreign; Consumer" 2 %, Health Professional | no |
| reporter_occupation_code | 98.0 | codes: "003" 62 %, OTHER 26 %, PATIENT 4.5 %, NOT APPLICABLE 3 % | no (mostly uninformative) |
| patient_outcome | 93.7 | Required Intervention 49 %, Other 28 %, Hospitalization 6 % | yes (report) |
| model_number | 90.6 | 823 values | partly (families) |
| mfr_report_type | 88.6 | Thirty-Day 72 %, Initial 14 %, Follow-Up 2 %, FDA Requested 1 % | no |
| device_evaluated_by_manufacturer | 76.9 | Y = evaluated 33 %; R = device not returned 27 %; N = not evaluated 17 %; blank 23 % | no. Key unused field |
| single_use_flag | 71.4 | Y 65 %, N 7 % | no |
| initial_report_to_fda | 53.3 | No 51 %, Yes 2 % | no |
| expiration_date_of_device | 44.6 | date | no |
| patient_age | 44.5 | "62 YR" style; parsed into patient_age_value / unit | no (this memo) |
| device_age_text | 43.2 | "DA" or "DAY" with no number in 99 % of filled rows | useless |
| suppl_dates_fda_received / mfr_received | 41 / 40 | dates of follow-up reports | no |
| reporter_state_code | 40.8 | US state (CA, TX, FL, NY, PA, OH) | no |
| catalog_number | 36.8 | | no |
| udi_di / udi_public | 34.0 | device identifier (Dexcom 47 %, Abbott 32 %, Medtronic 1 %) | no |
| patient_weight | 32.7 | kg; Dexcom 62 %, Medtronic 76 %, Abbott 16 % | no |
| patient_sex | 29.2 | Female 18,768; Male 17,222; Prefer not 120 | no (this memo) |
| lot_number | 26.9 | Dexcom 82 %, Senseonics 91 %, Medtronic 10 %, Abbott 2 % | no |
| previous_use_code | 22.2 | I 89 %, N 11 % (new device), A, R, U | no |
| event_location | 18.8 | "I" (invalid code) 93 %; HOME 471; HOSPITAL 12 | useless |
| health_professional | 12.1 | N 92 %, Y 8 % | weak |
| patient_treatment | 9.6 | free text list of devices or treatments | no |
| report_to_fda | 8.0 | | no |
| patient_race | 3.0 | White 3,064; Black 276; Asian 177 | no (empty) |
| patient_ethnicity | 2.0 | Non Hispanic 2,136; Hispanic 288 | no (empty) |
| remedial_action | 1.6 | Recall, Notification, Replace (about 1,900 rows) | no |
| removal_correction_number | 1.3 | recall record ids. Top value "2954323-11/22/25-001-C" (721 reports) is the Nov 2025 Libre 3 removal; "3004753838-02/29/16-001C" (236) is the 2016 Dexcom receiver recall | no. Direct link report-to-recall |
| 0 % (empty for all CGM reports) | 0 | date_report_to_fda, date_facility_aware, number_devices_in_event, number_patients_in_event, event_key, manufacturer_name, manufacturer_country, distributor_name, implant_flag, device_event_key, report_to_manufacturer, exemption_number | nothing to use |

Fill differs by maker and by year more than by anything else (`fill_rates_serious_by_group.csv`):

| Field (serious reports) | Abbott | Dexcom | Medtronic | Senseonics | Death | Injury |
|---|---|---|---|---|---|---|
| patient_age | 17.8 | 93.4 | 91.3 | 50.0 | 68.2 | 44.4 |
| patient_sex | 15.5 | 66.2 | 5.7 | 38.7 | 19.1 | 29.3 |
| patient_weight | 16.4 | 61.9 | 76.1 | 0.1 | 36.4 | 32.7 |
| lot_number | 2.2 | 82.4 | 9.7 | 90.7 | 43.5 | 26.8 |
| udi_di | 31.5 | 46.7 | 0.7 | 53.6 | 10.1 | 34.1 |
| device_evaluated_by_manufacturer | 82.3 | 64.0 | 76.6 | 85.1 | 50.4 | 77.0 |
| mfr_narrative | 97.9 | 89.6 | 99.3 | 98.1 | 89.6 | 95.7 |

- By year received: age was filled for 73 to 97 % of serious reports up to 2020, 54 % in 2021, then 17 to 49 % from 2022 on (Abbott's share grew). Sex was almost never filled before 2021 and 22 to 53 % after. The maker evaluation code was 0 % in 2013 to 2021 and 91 to 99 % from 2022 on. So any trend in these fields is a change in form-filling, not in patients.
- Over all 3.38 million reports (every event type): device_evaluated_by_manufacturer is filled 67 % (N 856k, Y 797k, R 528k); device_availability 100 % (No 65 %, returned to manufacturer 23 %, Yes 11 %); remedial_action 6 % (Recall 102k alone); health_professional 20 %; previous_use_code 49 %; patient_race 0.26 %; patient_ethnicity 0.34 %; reporter_country_code 92.8 % (US 2,156,966).

### 1b. What the raw records carry that the clean step dropped

One raw openFDA bulk zip was streamed: `2025q1_0001-of-0008.zip`, 95,000 records of all device types, of which 12,935 are CGM reports (our 13 product codes). Table: `inventory/raw_fields_one_zip.csv` (145 field paths; "kept_by_clean_step" yes/no; fill % for all devices and for CGM records). Text types: `inventory/raw_text_types_one_zip.csv`.

- The raw record has 145 field paths. The clean step keeps 78 and drops 67.
- Nothing is dropped from the text. Only two text types exist in the raw data (Description of Event, Additional Manufacturer Narrative) and both are kept.
- Dropped fields with a fill rate of 5 % or more in CGM records:

| Dropped field | CGM fill % | Worth adding? | Why |
|---|---|---|---|
| device_date_of_manufacturer | 78.0 | yes | with date_of_event it gives the sensor's age at the event, and the production era (ties to the Libre 3 recall lots) |
| device[].date_returned_to_manufacturer | 4.9 | yes (small) | time from event to return; pairs with the evaluation code |
| device[].serviced_by_3rd_party_flag | 91.0 | no | a flag with one value for sensors |
| device[].combination_product_flag | 100 | no | always N for sensors |
| device[].openfda.medical_specialty_description | 100 | no | constant ("Clinical Chemistry") |
| device[].date_received, patient[].date_received | 100 | no | repeat the report date |
| mdr_text[].mdr_text_key, mdr_text[].patient_sequence_number | 100 | no | ids only |
| manufacturer_contact_* (name, address, phone; 17 fields) | 80 to 99 | no | the maker's complaint-office contact; same for every report of a maker |
| device[].manufacturer_d_address_1 / city / postal_code / state | 89 to 99 | no | the maker's address |
| manufacturer_g1_* (8 fields) | 8.8 | no | a second maker address block |
| device[].implant_date_year, date_removed_year, report_date, distributor_*, manufacturer_address_* | 0 to 0.3 | no | empty for CGM |

- Fields the task listed as "candidates" that are in fact already in the clean tables: reporter_country_code, reporter_occupation_code, health_professional, source_type, event_location, initial_report_to_fda, device_evaluated_by_manufacturer, device_operator, remedial_action, patient_race, patient_ethnicity, patient_weight, device_age_text, device_availability, number_devices_in_event, previous_use_code, single_use_flag, lot_number, model_number, udi_di/udi_public. They came in with the bulk re-pull of 2026-10-27 (`DATA_NOTES.md`). The README section "Country per report (not stored yet)" is out of date.
- Cost of adding the two useful fields: two lines in `clean_row` / `EXTRA_DEV` in `scripts/maude_robot.py`, then `python fda-maude/scripts/maude_robot.py clean --tiers bulk`. The clean step took 6 minutes on this machine (`DATA_NOTES.md`); no download is needed because `raw/bulk/*.jsonl.gz` holds the whole records. guess: 10 minutes in total.

## Part 2. Who is in the reports (demographics)

Tables: `inventory/demographics_fill_rates.csv`, `demographics_age_sex.csv`, `demographics_filled_vs_unfilled.csv`, `demographics_age_in_text.csv`, `demographics_trial_side_by_side.csv`, `country_per_report.csv`.

### 2a. How often age and sex are filled (all 3,382,071 reports)

| Group | Reports | Age filled % | Sex filled % | Weight % | Race % | Ethnicity % |
|---|---|---|---|---|---|---|
| All | 3,382,071 | 73.3 | 45.7 | 38.2 | 0.3 | 0.3 |
| Abbott | 724,461 | 6.8 | 7.2 | 2.4 | 0.8 | 0.5 |
| Dexcom | 2,507,809 | 92.8 | 57.4 | 48.8 | 0.1 | 0.3 |
| Medtronic | 135,260 | 70.4 | 35.9 | 37.1 | 0.0 | 0.0 |
| Senseonics | 7,775 | 64.5 | 52.2 | 0.1 | 0.0 | 0.0 |
| Death | 623 | 67.4 | 19.1 | 36.4 | 2.2 | 1.4 |
| Injury | 122,984 | 44.2 | 29.2 | 32.7 | 3.0 | 2.0 |
| Malfunction | 3,257,570 | 74.4 | 46.3 | 38.4 | 0.2 | 0.3 |

- By product family: Dexcom G7 95 % age, 97 % sex; G6 91 / 57; G5 95 / 1; G4 93 / 0; Libre 3 9 / 10; Libre 2 4 / 6; Libre 14-day 8 / 4. Sex was not recorded at all before 2021; Dexcom started filling it in 2022 (79 to 84 % in 2022 to 2025).
- Deaths have age more often than injuries (67 vs 44 %) but sex less often (19 vs 29 %).
- "Prefer not to disclose" is 0.9 % of all reports (Dexcom G6 2.2 %).

Are filled reports different from blank ones? Yes, but because of the maker, not the patient:

| | Age filled (2.48 M) | Age blank (0.90 M) |
|---|---|---|
| Abbott share | 2 % | 75 % |
| Carries a wrong-readings code | 15 % | 67 % |
| Injury share | 2.2 % | 7.6 % |
| Reporter outside the US | 15 % | 67 % |
| Median text length (characters) | 417 | 802 |
| Serious reports with a sensor-meter pair | 20 % | 10 % |

The blank group is Abbott, non-US and accuracy complaints: exactly the reports the project cares most about. Medtronic adds a second reason: 43 % of its malfunction texts say "select patient information cannot be provided due to regional privacy regulations".

Does the text give the age when the field is blank? No. In the 68,809 serious reports with a blank age field, 24 texts (0.03 %) state an age; 0.6 % use a child word (child, son, daughter, pediatric). Where both exist they agree within a year in 72 % (Abbott 97 %, Dexcom 61 %; guess: Dexcom texts often give a carer's or relative's age).

### 2b. Age and sex where filled

| Group | Age known | Median age | Under 18 % | 18-39 % | 40-64 % | 65+ % | Sex known | Female % |
|---|---|---|---|---|---|---|---|---|
| All reports | 2,479,918 | 52 | 17.5 | 18.3 | 36.5 | 27.7 | 1,544,007 | 50.3 |
| Abbott | 48,985 | 64 | 3.2 | 7.9 | 40.3 | 48.5 | 52,280 | 43.6 |
| Dexcom | 2,328,174 | 51 | 18.1 | 18.5 | 36.1 | 27.3 | 1,439,030 | 50.7 |
| Medtronic | 95,271 | 53 | 10.5 | 19.6 | 44.2 | 25.7 | 48,594 | 47.2 |
| Senseonics | 5,016 | 57 | 0.8 | 17.5 | 49.4 | 32.3 | 4,055 | 44.9 |
| Deaths | 420 | 59 | 2.6 | 13.3 | 50.5 | 33.6 | 119 | 47.9 |
| Injuries | 54,378 | 51 | 14.1 | 19.9 | 41.3 | 24.6 | 35,871 | 52.2 |
| Malfunctions | 2,424,448 | 52 | 17.5 | 18.3 | 36.4 | 27.7 | 1,507,800 | 50.3 |
| Dexcom G4 | 121,521 | 42 | 27.7 | 20.2 | 38.6 | 13.6 | 156 | 50.0 |
| Dexcom G7 | 649,441 | 60 | 10.3 | 13.3 | 36.7 | 39.7 | 660,862 | 47.8 |
| Libre 3 / 3 Plus | 24,427 | 65 | 0.9 | 5.7 | 42.0 | 51.4 | 28,176 | 42.0 |

- Reported ages have moved up: median 44 in 2019, 50 in 2021, 53 in 2023, 59 in 2025, 57 in 2026. guess: CGM use spread to older adults and to type 2 diabetes (G7, Libre), and Medicare coverage widened in 2023.
- Sex is 50/50 overall. Abbott and Senseonics skew male (44 to 45 % female); injuries skew female (52 %).
- Children: 17.5 % of reports with an age are under 18 (Dexcom G4 28 %, G5 28 %). Deaths: 2.6 % under 18 (11 of 420).

### 2c. Side by side with the trial cohort (REPLACE-BG, Dexcom G4)

Trial numbers come from the roster and screening tables on this machine (226 randomised adults with type 1 diabetes).

| | MAUDE, all reports | MAUDE, death + injury | MAUDE, deaths | MAUDE, Dexcom G4 (the trial sensor) | REPLACE-BG trial |
|---|---|---|---|---|---|
| Reports or people | 3,382,071 | 123,607 | 623 | 131,078 | 226 |
| Age known | 73 % | 44 % | 67 % | 93 % | 100 % |
| Median age | 52 | 51 | 59 | 42 | 43 |
| Under 18 | 17.5 % | 14.0 % | 2.6 % | 27.7 % | 0 % |
| 18-39 | 18.3 % | 19.9 % | 13.3 % | 20.2 % | 43.4 % |
| 40-64 | 36.5 % | 41.4 % | 50.5 % | 38.6 % | 48.2 % |
| 65+ | 27.7 % | 24.7 % | 33.6 % | 13.6 % | 8.4 % |
| Sex known | 46 % | 29 % | 19 % | 0.1 % | 100 % |
| Female | 50.3 % | 52.1 % | 47.9 % | 50.0 % | 49.6 % |
| Race known | 0.3 % | 3.0 % | 2.2 % | 0 % | 100 % (White 93.8 %) |
| Diabetes type | not recorded | not recorded | not recorded | not recorded | type 1, 100 % |

- The Dexcom G4 reports and the trial have the same median age (42 vs 43) but the reports include children (28 %) and the trial has none.
- The reports as a whole are older than the trial (65+: 28 % vs 8 %) and the deaths older still (65+: 34 %). The trial cannot speak for children or for people over 65, the two groups that make up 45 % of filled MAUDE ages.
- Race and ethnicity cannot be compared; MAUDE does not have them.
- Say in the paper: MAUDE tells us little about who is hurt. Use the trial's own cohort description and name the gap.

### 2d. Country per report

Country is in the clean tables after all (`reporter_country_code`, filled 92.8 %). Table: `inventory/country_per_report.csv`. The codes mix two lists (FIPS: GM = Germany, UK; ISO: DE = Germany, GB), see `report/country_spread.md`.

| Group | Reports | US % | Not US % | Blank % | Top non-US codes |
|---|---|---|---|---|---|
| All | 3,382,071 | 63.8 | 29.0 | 7.2 | GM 181k, CA 92k, FR 86k, DE 76k, UK 65k, IT 51k |
| Death + injury | 123,607 | 44.3 | 50.5 | 5.1 | GM 11.9k, FR 8.8k, UK 7.7k, SP 5.6k, IT 3.9k |
| Deaths | 623 | 73.0 | 15.1 | 11.9 | GM 29, UK 12, CA 11, FR 8 |
| Abbott, death + injury | 77,868 | 26.9 | 71.6 | 1.5 | GM 10.7k, FR 8.6k, UK 7.1k, SP 5.5k |
| Dexcom, death + injury | 33,783 | 79.2 | 14.9 | 5.9 | GB 851, CA 672, DE 581 |
| Medtronic, death + injury | 8,721 | 58.6 | 6.6 | 34.8 | CA 142, GM 84 |

- These per-report numbers match the API counts in `country_spread.md` (US 2,156,966 both ways), so the earlier work is confirmed and no re-pull is needed.
- To use country per report: map FIPS and ISO codes to one country list (the mapping is already in `report/tables/k_country_codes.csv`) and add a `country` column to the clean step. guess: 1 to 2 hours.
- 72 % of Abbott's serious reports come from outside the US. Different countries have different rules on what must be reported; this is reporting behaviour, not sensor quality.

## Part 3. What the free text says that the 12-field form does not capture

Method: a stratified random sample of 300 texts (seed 20261106): 35 deaths, 140 injuries, 125 malfunctions; Abbott 107, Dexcom 112, Medtronic 55, other makers 26. Keys: `inventory/sample_300_keys.txt`. I read all 300 and coded each one by hand: `inventory/sample_300_hand_codes.txt` (codes explained at the top of the file); counts: `inventory/theme_hand_counts_sample300.csv`. Then patterns were written for each theme and checked against the hand codes: `inventory/theme_regex_vs_hand_sample300.csv`. Quotes below are at most one sentence and carry no names or identifiers.

| Theme | Of 300 | Death / Injury / Malfunction | One real example | Pattern at scale? (precision / recall on the 300) |
|---|---|---|---|---|
| Device NOT returned, discarded or never provided | 168 (56 %) | 22 / 78 / 68 | "Repeated attempts by ADC to retrieve the product were unsuccessful and/or the customer discarded the product." | yes (90 / 89) |
| Device returned and examined | 60 (20 %) | 4 / 23 / 33 | "Sensor has been returned and investigated." | yes (90 / 88) |
| Maker found no defect, met specification, could not confirm or reproduce | 124 (41 %) | 10 / 69 / 45 | "The sensor was found to be in sensor state 5 (indicating normal termination)." | yes (89 / 94) |
| Maker confirmed the problem or named a cause (incl. a known recall defect) | 49 (16 %) | 2 / 11 / 36 | "The root cause was determined to be a coding issue." | yes (86 / 86) |
| Root or probable cause not determined, inconclusive, not enough information | 85 (28 %) | 4 / 45 / 36 | "The allegation and a probable cause could not be determined." | yes (87 / 95) |
| Investigation still open, follow-up promised | 72 (24 %) | 16 / 39 / 17 | "A follow-up report will be submitted once additional information is obtained." | maybe (64 / 88; I under-coded this one by hand) |
| Maker reviewed the data remotely (share logs, cloud data) rather than the device | not hand-coded | pattern: 9 / 45 / 49 | "A review of the share logs was performed and a loss of connection was found within the investigation window." | yes (new theme; Dexcom and Senseonics) |
| Symptoms described (shaky, sweating, dizzy, vomiting, thirsty, confused) | 40 (13 %) | 2 / 38 / 0 | "She was not experiencing any symptoms of hypoglycemia." | yes (74 / 88) |
| The reading did not match how the person felt (explicit) | about 7 | 0 / 7 / 0 | "The patient felt that the CGM was reading inaccurately because the value did not match how he felt." | maybe (small n) |
| A lab, venous or clinic meter value is quoted | 20 (7 %) | 3 / 14 / 3 | "A laboratory result of 580 mg/dL was also obtained and compared to a sensor scan result of 120 mg/dL." | maybe (74 / 70) |
| An alarm fired and prompted the check | 18 (6 %) | 1 / 14 / 3 | "The patient reported being woken up by a CGM low alert." | needs the model (36 / 22; device-status alarms confuse it) |
| Failure timed in hours or minutes after insertion, or "same day" | 17 (6 %) | 1 / 13 / 3 | "Five sensors failed in less than an hour of insertion." | maybe (88 / 41) |
| Sensor ended early or showed an error message (replace sensor, scan again in 10 minutes, no active sensor) | 33 (11 %) | 3 / 19 / 11 | "Customer received a 'scan again in 10' message and was unable to obtain readings." | yes (72 / 100); overlaps the form's fault type |
| Adhesive problem, sensor detached or knocked off | 8 (3 %) | 0 / 8 / 0 | "The sensor prematurely detached after 7 days of wear." | maybe (67 / 100); already a form fault type |
| Skin reaction, infection, abscess, scar | 14 (5 %) | 0 / 14 / 0 | "The patient underwent surgery and had an incision and drainage to relieve the abscess." | maybe (56 / 100; the Dexcom label sentence and other body parts add false hits) |
| Bleeding or bruising at the site | 9 (3 %) | 0 / 8 / 1 | "The bleeding was the result of blood thinners and a pierced vein during insertion." | maybe (53 / 100) |
| Sensor wire or filament detached, broken or left in the skin | 9 (3 %) | 0 / 5 / 4 | "It was determined that the sensor wire was still in the patient's body." | yes (75 / 100) |
| Pain at insertion or at the site | 5 (2 %) | 0 / 5 / 0 | "For the past four days I have been experiencing an unusual intermittent pain and burning sensation at the site of my sensor." | yes (100 / 100) |
| Applicator or inserter failed, bent tip, sensor stayed in the tool | 4 (1 %) | 0 / 3 / 1 | "The sensor likely remained inside the insertion tool and the HCP might have not noticed it." | yes (100 / 100) but rare |
| Compression low (lying or pressing on the sensor) | 1 (0.3 %) | 0 / 1 / 0 | "It was indicated that the patient rubbed/bumped/laid on the transmitter." | yes, but rare: rejected as a theme worth chasing |
| Night, sleep, waking | 17 (6 %) | 6 / 11 / 0 | "The spouse woke up and checked on the patient but she couldn't wake him." | yes (75 / 88) |
| Interfering substance or dialysis | 3 (1 %) | 1 / 1 / 1 | "The patient was taking medication containing more than 1 gram acetaminophen over the course of 6 hours." | yes, but rare: rejected |
| App, phone, Bluetooth, software update, compatibility | 31 (10 %) | 2 / 15 / 14 | "The G7 CGM application only detects that the session has ended, thus it does not alert the user that the sensor has failed." | yes (66 / 94) |
| Receiver, reader, transmitter hardware, battery, overheating | 20 (7 %) | 1 / 8 / 11 | "Customer reports their device is too hot to hold." | maybe (65 / 100) |
| Alarm did not sound, was not heard, or was too quiet | 23 (8 %) | 2 / 17 / 4 | "The spouse said she didn't hear any alarm that he was low." | yes (82 / 78) |
| Insulin pump automation acted on the reading | 8 (3 %) | 2 / 6 / 0 | "This device is connected to my insulin pump which automatically gives me insulin based on its input." | maybe (75 / 75) |
| A pump is mentioned at all | 58 (19 %) | 13 / 28 / 17 | | yes (86 / 86); mostly Medtronic pump-system reports |
| Written in the first person (the patient or carer typed it) | 7 (2 %) | 1 / 6 / 0 | "Every single sensor I have used so far this year has failed." | yes (88 / 100) |
| A carer or family member is in the story | 72 (24 %) | 20 / 52 / 0 | "The patient's daughter noticed the CGM was displaying 400 mg/dL and immediately checked the patient's BG and it was reading 48 mg/dL." | yes (94 / 81) |
| A clinician is in the story (HCP, nurse, physician, clinic) | 56 (19 %) | 8 / 48 / 0 | | yes (91 / 88) |
| Pure template text with no individual story | 75 (25 %) | 0 / 8 / 67 | "A customer reported receiving erroneous glucose results from an Abbott Diabetes Care device." | yes (pattern "maker wording" is wider: 253 of 300) |
| EMS, 911, ambulance, ER, hospital, ICU | 71 (24 %) | 10 / 61 / 0 | "A policeman saw her inside and called 911." | yes (96 / 97) |
| Glucagon given | 13 (4 %) | 0 / 13 / 0 | | yes (93 / 100) |
| Seizure, unconscious, unresponsive, collapse | 40 (13 %) | 6 / 34 / 0 | | yes (80 / 100) |
| DKA or ketones | 19 (6 %) | 3 / 16 / 0 | | yes (100 / 95) |
| Driving, a fall or a head injury | 5 (2 %) | 0 / 5 / 0 | "The patient experienced confusion and passed out in the car." | yes (71 / 100) |
| Pregnancy (both were fetal deaths) | 2 (0.7 %) | 2 / 0 / 0 | | yes (100 / 100) |
| Maker told the user to use a meter, calibrate properly, charge or change the device | 18 (6 %) | 0 / 15 / 3 | "The customer was recommended to calibrate the system using true fingerstick BG values." | needs the model (100 / 50) |
| Maker cites the label or a "known and anticipated" effect | pattern 12 | 1 / 11 / 0 | | yes |
| Maker attributes the event to user error, misuse, off-label use or an unsupported phone | 12 (4 %) | 1 / 9 / 2 | "The probable cause of the alarm being inaudible is due to user error." | maybe (47 / 75) |
| Replacement, credit or refund | 18 (6 %) | 0 / 11 / 7 | | yes (70 / 89) |
| Several sensors failed, or it keeps happening | 6 (2 %) | 1 / 4 / 1 | "When you have 10 fail in a row there is a problem." | maybe (40 / 100) |
| Lawyer, "report to FDA", "should be recalled", coroner or medical examiner | 33 (11 %) | 16 / 7 / 10 | | split into three patterns: death investigation words (29 of 35 deaths), legal/escalation (75 / 27), recall or field action id (yes) |
| Reporter unreachable, declined follow-up, or details withheld for privacy | 15 (5 %) | 6 / 1 / 8 | "Select patient information cannot be provided due to regional privacy regulations." | maybe (56 / 100) |
| Report later withdrawn ("submitted in error", "not reportable") | 6 (2 %) | 0 / 2 / 4 | | yes (100 / 100) |

Things the reading taught that the counts do not show:
- Death reports are mostly not device stories. 29 of the 35 death texts are about a coroner, autopsy or death certificate; many say "there was no alleged device malfunction" (a spouse told the maker the person had died while wearing a sensor). Several Medtronic "CGM" deaths are insulin-pump reports filed under a CGM code. The two fetal deaths (Abbott, 2024 and 2025) are the only pregnancy reports.
- Malfunction texts are two things: the Abbott template (a sensor value, a meter value, a Parkes zone, a wear day, then "no product has been returned ... no indication that the product did not meet specification") and Dexcom one-liners ("it was reported that signal loss over one hour occurred. No product or data was provided for evaluation."). 67 of the 125 malfunction texts in the sample had no individual story at all.
- "No defect found" usually means a paper check. Abbott's standard sentence appears whether or not the sensor came back; when it did, the test is electrical ("sensor state 5", "poise voltage within specification"), not a glucose test. Dexcom's "allegation confirmed" for signal loss means the logs show the gap, and the cause is still "could not be determined" (70 % of Dexcom serious texts).
- The hidden-low story is written by family. In the injury texts, the carer is the one who finds the person, checks the meter and calls 911; the sensor often read normal or high.
- The recall shows up in two places: Abbott's 2025-2026 malfunction template cites field action FA1002-2025 ("may not meet product design specifications and may produce low glucose readings which are not clinically acceptable"), and the structured field removal_correction_number carries the FDA removal id on 721 serious reports.

## Part 4. The patterns at scale

Patterns (regex) for all 52 themes are in `scripts/field_inventory.py` (`THEMES`, with maker boilerplate sentences removed first by `BOILERPLATE`); the list with labels is `inventory/theme_patterns.csv`. Hit rates: `inventory/theme_hits_serious.csv` (by maker and by event type; 122,657 serious texts), `theme_hits_serious_by_family.csv` (12 product families), `theme_hits_sample_weighted.csv` (6,137 malfunction texts, weighted to 2.92 million). A hit means the text mentions the theme; it is not a confirmed fact. Themes with precision under 80 % on the 300 are marked "~" and should be quoted as rough.

Hit rate, % of texts. Serious = death + injury, unweighted. Sample = malfunction, weighted.

| Theme | Serious all | Abbott | Dexcom | Medtronic | Deaths | Sample all | Sample Abbott | Sample Dexcom |
|---|---|---|---|---|---|---|---|---|
| Device not returned | 66.5 | 85.9 | 23.2 | 83.3 | 41.8 | 40.3 | 51.3 | 35.8 |
| Device returned and examined | 20.1 | 24.7 | 12.1 | 13.7 | 15.1 | 30.1 | 33.8 | 30.4 |
| Remote data review | 29.4 | 17.9 | 63.8 | 0.1 | 27.0 | 70.9 | 5.4 | 85.3 |
| No defect / within spec / not confirmed | 64.8 | 92.7 | 15.5 | 12.4 | 51.3 | 23.9 | 62.3 | 18.4 |
| Problem confirmed or cause named | 8.0 | 5.7 | 14.3 | 3.0 | 8.5 | 35.1 | 29.6 | 37.4 |
| Cause not determined | 21.1 | 3.0 | 70.0 | 0.1 | 36.2 | 60.7 | 0.5 | 73.6 |
| Investigation pending ~ | 44.8 | 63.7 | 6.4 | 26.9 | 23.8 | 10.2 | 31.6 | 6.5 |
| Symptoms described ~ | 36.6 | 40.1 | 35.3 | 17.2 | 10.6 | 0.9 | 0.0 | 1.1 |
| Lab or clinic value ~ | 7.5 | 8.8 | 6.7 | 0.4 | 4.0 | 0.1 | 0.5 | 0.0 |
| Hours or minutes after insertion | 1.2 | 0.2 | 3.8 | 0.3 | 1.4 | 0.1 | 0.0 | 0.1 |
| Sensor ended early or error message ~ | 28.3 | 39.9 | 10.6 | 1.9 | 8.0 | 7.2 | 2.3 | 8.3 |
| Adhesive or fell off ~ | 8.3 | 10.2 | 6.2 | 1.8 | 1.0 | 0.5 | 0.5 | 0.5 |
| Skin reaction or infection ~ | 18.1 | 15.1 | 27.3 | 6.6 | 6.3 | 2.6 | 0.2 | 3.1 |
| Bleeding or bruise ~ | 6.5 | 2.0 | 18.5 | 1.5 | 2.3 | 0.1 | 0.0 | 0.0 |
| Sensor wire detached, broken or retained ~ | 2.7 | 1.4 | 4.6 | 5.7 | 0.8 | 5.7 | 0.0 | 7.0 |
| Pain at the site | 5.0 | 3.6 | 8.8 | 0.6 | 0.6 | 0.0 | 0.0 | 0.0 |
| Compression or lying on the sensor | 0.3 | 0.2 | 0.4 | 0.0 | 0.5 | 0.1 | 0.0 | 0.1 |
| Night or sleep ~ | 6.8 | 1.9 | 17.9 | 6.5 | 14.6 | 0.1 | 0.2 | 0.0 |
| Interfering substance or dialysis | 0.9 | 0.5 | 2.1 | 0.3 | 2.6 | 0.2 | 0.0 | 0.3 |
| Off-label site ~ | 4.7 | 3.3 | 9.4 | 0.1 | 0.3 | 2.9 | 0.0 | 3.5 |
| App, phone, Bluetooth ~ | 9.4 | 9.2 | 10.8 | 5.6 | 15.4 | 19.2 | 0.7 | 22.5 |
| Receiver, reader, hardware ~ | 5.0 | 4.6 | 5.8 | 6.3 | 5.8 | 18.8 | 3.1 | 21.4 |
| Alarm failed or not heard | 6.1 | 5.4 | 8.3 | 3.5 | 9.2 | 3.1 | 0.0 | 3.8 |
| Pump automation acted on the reading ~ | 2.1 | 0.2 | 5.6 | 6.6 | 4.7 | 0.1 | 0.0 | 0.0 |
| Pump mentioned | 11.4 | 0.7 | 19.6 | 77.9 | 26.4 | 5.3 | 0.0 | 1.9 |
| First person | 3.1 | 1.6 | 7.1 | 1.1 | 3.9 | 1.0 | 0.3 | 1.0 |
| Carer or family in the story | 32.4 | 36.0 | 33.2 | 8.2 | 55.5 | 1.3 | 0.0 | 1.6 |
| Clinician in the story | 39.4 | 46.2 | 28.5 | 14.3 | 27.2 | 0.1 | 0.3 | 0.1 |
| EMS, ER, hospital | 37.6 | 22.6 | 62.4 | 80.5 | 43.4 | 0.0 | 0.0 | 0.0 |
| Glucagon | 6.1 | 6.5 | 7.1 | 1.2 | 1.3 | 0.0 | 0.0 | 0.0 |
| Seizure, unconscious, collapse | 34.6 | 41.2 | 29.0 | 7.6 | 20.7 | 0.3 | 1.8 | 0.0 |
| DKA or ketones | 6.1 | 1.9 | 10.8 | 26.4 | 9.8 | 0.0 | 0.0 | 0.0 |
| Driving, fall, head injury ~ | 3.0 | 1.1 | 7.0 | 3.7 | 4.7 | 0.1 | 0.2 | 0.0 |
| Pregnancy | 0.2 | 0.1 | 0.3 | 0.4 | 1.6 | 0.1 | 0.0 | 0.1 |
| Maker advised meter or calibration | 0.6 | 0.1 | 0.9 | 2.0 | 0.2 | 0.2 | 0.0 | 0.0 |
| Maker cites the label | 7.5 | 4.7 | 14.5 | 0.1 | 1.0 | 2.0 | 0.2 | 2.4 |
| User error or misuse claimed ~ | 5.4 | 4.5 | 8.8 | 1.7 | 3.7 | 5.1 | 0.0 | 6.2 |
| Replacement or refund ~ | 5.5 | 3.0 | 6.6 | 20.3 | 3.1 | 3.1 | 0.6 | 3.1 |
| Repeat failures ~ | 3.8 | 2.2 | 7.1 | 5.8 | 5.6 | 0.3 | 0.2 | 0.3 |
| Libre scan | 19.9 | 31.2 | 0.8 | 0.2 | 4.2 | 3.7 | 28.0 | 0.0 |
| Recall or field action cited | 4.1 | 2.4 | 9.0 | 0.8 | 4.3 | 3.6 | 27.0 | 0.0 |
| Coroner, autopsy, death certificate | 0.6 | 0.3 | 1.3 | 1.3 | 90.7 | 0.0 | 0.0 | 0.0 |
| Legal or escalation language ~ | 3.9 | 5.6 | 1.2 | 0.8 | 9.5 | 0.3 | 2.2 | 0.0 |
| Report channel named (social media, web form, MedWatch) | 13.9 | 14.0 | 14.5 | 8.4 | 30.1 | 5.8 | 23.1 | 3.2 |
| Reporter unreachable or details withheld ~ | 5.2 | 6.4 | 3.4 | 2.6 | 13.8 | 1.9 | 0.2 | 0.1 |
| Report withdrawn as not reportable | 0.3 | 0.1 | 0.6 | 0.4 | 1.0 | 2.7 | 0.0 | 3.2 |

What the maker found, cross-checked (serious texts; `inventory/eval_returned_outcomes.csv`, `eval_code_vs_text.csv`):

| | All | Abbott | Dexcom | Medtronic |
|---|---|---|---|---|
| Text says returned only | 6.0 % | 5.9 % | 4.3 % | 12.2 % |
| Text says not returned only | 52.4 % | 67.1 % | 15.4 % | 81.9 % |
| Both (follow-up reports) | 14.1 % | 18.8 % | 7.7 % | 1.5 % |
| Neither | 27.5 % | 8.2 % | 72.5 % | 4.4 % |
| Of the returned: no defect found | 80.9 % | 98.3 % | 75.3 % | 16.7 % |
| Of the returned: problem confirmed or cause named | 13.7 % | 8.6 % | 28.5 % | 7.5 % |
| Of the returned: cause not determined | 18.2 % | 3.4 % | 79.6 % | 0.0 % |

- The structured field agrees: device_availability says "returned to manufacturer" for 16.6 % of serious reports and device_evaluated_by_manufacturer says Y for 33 %, R (not returned) for 27 %. Where the code says returned, about 9 in 10 texts say no defect was found. The text adds the reason (state 5, within specification, could not reproduce) and the Dexcom remote-data route that the code does not record.
- Reading for the paper: in the injury reports the sensor almost never comes back (Abbott 86 % not returned) and when it does the maker's bench test finds nothing in 98 % (Abbott) to 75 % (Dexcom). So "no defect found" in MAUDE is not evidence that the sensor was accurate; it is evidence that the bench test does not reproduce an in-body error.
- Brand families differ where it matters for Phase 2: skin reactions are 44 % of Dexcom G4 serious texts, 26 % for G6, 22 % for G7, 9 % for Libre 2; alarm failures 15 % for G4, 8 % for G6, 6 % for G7, 5 % for Libre 2 and 3; pump automation 9 % for G7, 5 % for G6, 0.2 % for Libre; EMS or hospital 72 % for G7 and 64 % for G6 against 21 to 26 % for Libre (a coding habit: Abbott files most injuries as "required intervention"); recall or field action id 14 % for G7 (the 2025 receiver recall), 7 % for Libre 3.
- Among malfunction texts the patterns mostly see templates: 27 % of Abbott malfunction texts cite the FA1002-2025 field action (the Libre 3 recall), 85 % of Dexcom malfunction texts describe a remote log review, 74 % of them end in "cause could not be determined", and 43 % of Medtronic ones withhold patient details for privacy.

## Part 5. Beyond death and injury: is it worth reading the 3.26 million malfunction reports?

Tables: `inventory/beyond_serious_fault_mix.csv`, `malfunction_text_dedup.csv`, `malfunction_template_texts.csv`, `bigger_text_run_cost.csv`. Complement: `results/text/REGEX_V2_FULL_CORPUS.md` (the pattern layer run over every report after this inventory started).

What the weighted malfunction sample (6,137 texts standing for 2.92 million) says against the serious reports (model forms from the full run):

| | Malfunction, all (weighted) | Malfunction, Abbott | Malfunction, Dexcom | Serious, all | Serious, Abbott | Serious, Dexcom |
|---|---|---|---|---|---|---|
| Wrong readings (low, high, erratic, stuck) | 8.5 % | 58.1 % | 0.8 % | 28.4 % | 27.7 % | 37.0 % |
| Signal loss | 42.7 % | 0.1 % | 47.9 % | 8.0 % | 9.5 % | 6.0 % |
| Sensor error or early end | 15.3 % | 10.2 % | 16.8 % | 18.1 % | 26.1 % | 5.1 % |
| Unclear | 14.9 % | 29.1 % | 13.3 % | 5.0 % | 1.8 % | 11.5 % |
| Both sensor and meter value stated | 4.3 % | 27.7 % | 0.6 % | 15.3 % | 10.1 % | 29.7 % |
| Pairs | 327 | 255 | 32 | 18,118 | 7,556 | 9,518 |
| Median error, % of meter | -64 | -65 | -45 | -0.3 | -47 | +42 |
| Sensor below meter | 73 % | 73 % | 69 % | 50 % | 58 % | 44 % |
| Error beyond 20 % | 99 % | 100 % | 92 % | 96 % | 97 % | 96 % |
| Outcome "none" | 97.7 % | 100 % | 97.3 % | 10.7 % | 11.1 % | 8.4 % |

How much of the malfunction text is real text:

| | All makers | Abbott | Dexcom | Medtronic |
|---|---|---|---|---|
| Malfunction reports | 3,257,570 | 646,461 | 2,473,325 | 126,518 |
| Distinct texts | 808,899 | 196,528 | 508,176 | 95,146 |
| Share that is a template (an identical text shared by 1,000+ reports) | 45.5 % | 59.6 % (20 templates) | 44.0 % (220 templates) | 6.0 % |
| Share under 120 characters | 7.4 % | 29.2 % | 2.0 % | 2.6 % |
| Reports with no text at all | 236,507 (all Dexcom) | | | |
| Share with a real story (not a template, 120+ characters) | 54.3 % (1.77 M) | 40.3 % | 55.8 % | 94.0 % |
| Share with a wrong-readings code | 28.7 % (933k) | 92.0 % | 13.3 % | 4.4 % |
| Wrong-readings code AND a real story | 481,095 (14.8 %) | 244,190 | 229,328 | 5,149 |

What a bigger model run would cost at the measured 217 reports per minute (one 16 GB GPU):

| Option | Reports | GPU hours | Working days (8 h) |
|---|---|---|---|
| A. Every malfunction report | 3,257,570 | 250 | 31 |
| B. Real stories only | 1,770,310 | 136 | 17 |
| C. Wrong-readings code | 933,365 | 72 | 9 |
| D. Wrong-readings code and a real story | 481,095 | 37 | 4.6 |
| E. D, Abbott only | 244,190 | 19 | 2.3 |
| F. 10 % random sample of D (weighted) | 48,110 | 3.7 | 0.5 |

Since this inventory started, the pattern layer was widened and run over every report (`REGEX_V2_FULL_CORPUS.md`): 191,112 malfunction pairs were read (162,072 Abbott), the malfunction-only fault is one thing (a false low of 60 to 80 % while the true glucose is normal or high; true value under 70 in 5 %), the serious pairs hold the two other faults (hidden lows, 38 %; sensor pinned at the floor while the true value is over 250), and the weighted-sample numbers sit inside the full-corpus intervals for Abbott and for all makers. That answers the "error sizes beyond death + injury" question without the model.

Opinion (5 lines):
1. Reading all malfunction texts with the model would add volume, not knowledge: half the texts are templates the patterns already read, Dexcom's say "signal loss, no data provided, cause not determined" in 74 % of cases, and the outcome is "none" in 98 %.
2. The model's advantages over patterns (fault type where codes are vague, user action, outcome) are worth little here: user action is stated in 0.2 % of malfunction texts and outcome is almost always none.
3. It would not change the research question. The regex-v2 pass already did that: the question is now "which direction and at which true-glucose band", and the Phase 2 faults are set (false low in the normal range, hidden low, floor-pinned high).
4. If the team wants model-grade fault types for the malfunction pile, option E (Abbott only, 19 GPU-hours) or F (3.7 hours) is enough to check the pattern layer; option A is not justified.
5. Better uses of the same hours: the two human reads that would settle the harm gradient (100 malfunction and 100 injury texts from the extreme error bands), and a 100-report read of Abbott "returned, no defect found" injuries to see what the person experienced when the bench test found nothing.

## Recommendations, ranked by value for effort

| Rank | What | Effort | Why it is worth it |
|---|---|---|---|
| 1 | Use the unused structured fields: device_evaluated_by_manufacturer + device_availability (what the maker found), reporter_country_code (harmonise FIPS/ISO with `k_country_codes.csv`), removal_correction_number (reports tied to the Libre 3 removal id), mfr_report_type / type_of_report (follow-ups), source_type "Foreign" | 1 to 2 hours, no new data | a "maker evaluation" table and a country column for every report, with no model and no API |
| 2 | Quote the at-scale theme rates for the paper's Phase 1 section: not returned 66 %, no defect found in 81 % of returned devices, EMS/hospital 38 %, carer in the story 32 %, alarm failure 6 %, pump automation 2 % (G7 9 %), skin reactions by family | done (this memo); quote only themes with precision 80 %+ | these are facts the 12-field form does not hold, and they shape how to read "reads low" complaints |
| 3 | Add device_date_of_manufacturer and date_returned_to_manufacturer to `clean_row`, re-run `clean --tiers bulk` | 10 minutes | sensor age at the event, production era vs the recall lots, time to return |
| 4 | Two human reads of 100 + 100 texts (extreme error bands from `REGEX_V2_FULL_CORPUS.md`; Abbott "returned, no defect" injuries) | 3 to 4 hours | settles whether the harm gradient is real and what "no defect found" hides |
| 5 | A second pattern round on the "~" themes (skin, bleeding, adhesive, app, hardware, repeat failures) if any of them is used in the paper | 1 to 2 hours | precision 50 to 70 % today; the fixes are known (label sentence, body parts, device-status alarms) |
| 6 | Model run on malfunction texts | 19 GPU-hours (Abbott) to 250 (all) | low value; only option E or F, and only to check the pattern layer |
| 7 | Demographics | stop | age and sex are a Dexcom habit; race and ethnicity are empty; the text does not help. State the gap (children 17.5 %, 65+ 28 % of filled MAUDE ages; trial 0 % and 8 %) and move on |

## How to run

From the repo root (Windows: plain `python`). Deterministic (seed 20261106). About 7 minutes without a zip; the zip stream added 11 seconds for a 77 MB zip.

```
python fda-maude/scripts/field_inventory.py                      # default zip raw/bulk_zips/2025q1_0001-of-0008.zip if present
python fda-maude/scripts/field_inventory.py --zip PATH/TO/one.zip
python fda-maude/scripts/field_inventory.py --skip-zip --skip-hash   # fastest (no raw zip, no 3.38 M text hashing)
python fda-maude/scripts/field_inventory.py --write-texts SOME/FOLDER/sample_300_texts.txt   # dump the 300 texts for re-reading (not in git)
```

Reads: `clean/serious.csv.gz`, `clean/full.parquet`, `clean/sample_local.parquet`, `clean/text_extract_v3.jsonl`, one raw zip, `scripts/config.json`, the trial roster (`Uncommitted Data/.../HPtRoster.txt`, `HScreening.txt`; without them the trial column says "in progress"). Writes only to `results/inventory/`.

| Output (results/inventory/) | What |
|---|---|
| fill_rates_serious.csv, fill_rates_sample_weighted.csv, fill_rates_serious_by_group.csv | part 1a |
| raw_fields_one_zip.csv, raw_text_types_one_zip.csv | part 1b |
| demographics_fill_rates.csv, demographics_age_sex.csv, demographics_filled_vs_unfilled.csv, demographics_age_in_text.csv, demographics_trial_side_by_side.csv, country_per_report.csv | part 2 |
| sample_300_keys.txt, sample_300_hand_codes.txt, theme_hand_counts_sample300.csv, theme_hits_sample300_by_report.csv, theme_regex_vs_hand_sample300.csv | part 3 (the hand codes and the pattern check were written by hand and by a small helper, not by the script) |
| theme_patterns.csv, theme_hits_serious.csv, theme_hits_serious_by_family.csv, theme_hits_sample_weighted.csv, eval_code_vs_text.csv, eval_returned_outcomes.csv | part 4 |
| beyond_serious_fault_mix.csv, malfunction_text_dedup.csv, malfunction_template_texts.csv, bigger_text_run_cost.csv | part 5 |
| inventory_stats.json | key numbers |

Caveats:
- Everything here is a count of reports and of words in reports. It reflects who reports, which maker writes the text, and which template they use. It is not a failure rate and not a confirmed outcome.
- Pattern precision and recall were measured on 300 texts read by one person; a second reader has not checked the hand codes.
- The 300-text sample over-weights deaths and Medtronic on purpose (stratified), so its raw counts are not population shares; the at-scale tables are.
- Medtronic is undercounted (most sensor reports sit under pump codes) and its "CGM" reports are often pump stories.
