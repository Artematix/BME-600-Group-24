# Verified reference list for the paper

Checked on 2026-11-20. Every entry in section 1 was opened in this session. Nothing here is written from memory.

## How to read this file

- Numbers like [12] are for this file only. Renumber in the paper in order of first use (IEEE rule).
- "Opened" says which page was read:
  - PubMed = the PubMed record (title, authors, journal, year, abstract). The PubMed website blocked scripts today, so the same records were read through PubMed's own data service (NCBI E-utilities). The link given is the normal PubMed address.
  - PMC = the free full text on PubMed Central. Read with a page-reading tool that returns answers and short quotes.
  - Direct = the page or PDF was downloaded and its text read line by line.
- "Abstract only" means the full text was not opened. Cite only what the abstract says.
- Words used:
  - CGM = continuous glucose monitor. A skin sensor that reads glucose every few minutes.
  - Meter (also BGM or SMBG) = fingerstick blood glucose meter.
  - MARD = mean absolute relative difference. The average size of the error, in percent of the reference value. Lower is better.
  - YSI = a lab glucose analyzer. The usual lab reference in sensor studies.
  - Bias = average of (sensor minus reference). Negative = the sensor reads low.
  - MAUDE = the FDA database of device problem reports.
  - In silico = done by computer simulation.
  - Nonadjunctive use = dosing insulin from the CGM value with no confirming fingerstick.
  - 20/20 (or 15/15) = share of readings within 20 mg/dL of the reference at low glucose, or within 20 % at higher glucose.

## 1. Verified

### Topic 1. The 2025 Abbott FreeStyle Libre 3 recall

**[1]** U.S. Food and Drug Administration, "Glucose Monitor Sensor Recall: Abbott Diabetes Care Removes Certain FreeStyle Libre 3 and FreeStyle Libre 3 Plus Sensors," FDA, content current as of Feb. 5, 2026. Accessed: Nov. 20, 2026. [Online].
- Link: https://www.fda.gov/medical-devices/medical-device-recalls-and-early-alerts/glucose-monitor-sensor-recall-abbott-diabetes-care-removes-certain-freestyle-libre-3-and-freestyle
- Opened: Direct.
- Says: "Abbott Diabetes Care is recalling certain FreeStyle Libre 3 and FreeStyle Libre 3 Plus sensors due to incorrect glucose readings that are lower than actual blood glucose levels."
- Says: "As of January 7, 2026, Abbott has reported 860 serious injuries, and seven deaths associated with this issue."
- Says: early alert issued 12/02/2025. Updated 2/4/2026: "this issue has been classified as a Class I Recall." The page gives no count of sensors.
- Use: Introduction. The motivating event, the harm numbers, the recall class.

**[2]** Abbott, "Abbott Initiates Medical Device Correction for Certain FreeStyle Libre 3 and FreeStyle Libre 3 Plus Sensors in the U.S.," company announcement, Nov. 24, 2025. Accessed: Nov. 20, 2026. [Online].
- Link (FDA copy, published Jan. 15, 2026): https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/abbott-initiates-medical-device-correction-certain-freestyle-librer-3-and-freestyle-libre-3-plus
- Link (Abbott): https://abbott.mediaroom.com/press-releases?item=124718
- Opened: both pages, with a page-reading tool.
- Says: "This action involves approximately 3 million Libre 3 and Libre 3 Plus sensors in the U.S. from that production line, about half of which are estimated to have expired or been used."
- Says: "Globally, Abbott has received reports of 736 severe adverse events (57 in the U.S.) and seven deaths (none in the U.S.) potentially associated with this issue."
- Says: Abbott calls the action a "medical device correction". Its text does not use the word "recall".
- Use: Introduction. The only source for "about 3 million sensors".

**[3]** U.S. Food and Drug Administration, "Class 1 Device Recall FreeStyle Libre" (four records, recall nos. Z-1020-2026 to Z-1023-2026, recall event 98049), Medical Device Recalls database, posted Jan. 14, 2026. Accessed: Nov. 20, 2026. [Online]. These are refs [12] to [15] of the midterm plan.
- Opened: Direct (all four pages).
- Says: date initiated by firm November 24, 2025. Status open, classified. Product code QLG.
- Says: reason, same in all four: "Due to a manufacturing process issue that may cause carbon build up in the sensor that may result in incorrect low glucose results". FDA determined cause: "Process control".
- Says: distribution lists 36 U.S. states and 19 other countries.

| Recall no. | Product named in the record | Quantity in commerce | Link |
|---|---|---|---|
| Z-1020-2026 | FreeStyle Libre 3 Sensor REF 72081-01 | 1,060,723 sensors | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217499 |
| Z-1021-2026 | FreeStyle Libre 3 Plus Sensor REF 78768-01 | 1,663,241 sensors | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217500 |
| Z-1022-2026 | FreeStyle Libre 3 Plus Sensor REF 78769-01 | 258,913 sensors | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217774 |
| Z-1023-2026 | FreeStyle Libre 3 Plus Sensor REF 72080-01 | 8,062 sensors | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217776 |
| Sum (our addition) | | 2,990,939 sensors | |

- Use: Introduction. The cause, the class, and an FDA count that adds up to about 3 million.

**[4]** U.S. Food and Drug Administration, "Class 1 Device Recall FreeStyle Libre 3 sensor, a component of the FreeStyle Libre 3 Continuous Glucose Monitoring System," recall no. Z-2692-2024, Medical Device Recalls database, posted Aug. 27, 2024. Accessed: Nov. 20, 2026. [Online]. Midterm ref [11].
- Link: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=209214
- Opened: Direct.
- Says: initiated July 24, 2024. Quantity 8,174. Reason: "Users of the FreeStyle Libre 3 sensors reported situations where they were receiving erroneously high glucose results."
- Use: Introduction or Discussion. An earlier Class 1 recall of the same sensor for the opposite fault (reads too high). Supports testing more than one fault type.

**[5]** U.S. Food and Drug Administration, "Summary of Safety and Effectiveness Data (SSED): FreeStyle Libre Pro Flash Glucose Monitoring System," PMA P150021, approved Sep. 23, 2016. Accessed: Nov. 20, 2026. [Online].
- Link: https://www.accessdata.fda.gov/cdrh_docs/pdf15/P150021B.pdf (record: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpma/pma.cfm?id=P150021)
- Opened: Direct (PDF, 31 pages).
- Says: "40% of the time when the device indicated that user sensor glucose values were at or below 60 mg/dL, user glucose values were actually in the range of 81-160 mg/dL."
- Says: the clinical results "demonstrate a negative bias ... especially in the range of 81-160 mg/dL. This level of bias is worse than similar recently approved continuous glucose monitors".
- Says: MARD 12.1 % overall (12,080 pairs against the lab comparator). By wear day: 13.7 % on day 1, 9.0 % on day 14.
- Use: Introduction. FDA wrote in 2016 that an Abbott flash sensor read low. Also first-day error (topic 12).

**[6]** T. Kogai et al., "Diabetic ketoacidosis due to a sensor defect of FreeStyle Libre: A case report," *J. Diabetes Investig.*, vol. 14, no. 11, pp. 1321-1324, Nov. 2023, doi: 10.1111/jdi.14065.
- Link: https://pubmed.ncbi.nlm.nih.gov/37530563/
- Opened: PubMed; PMC (PMC10583651).
- Says: a 59-year-old man with type 1 diabetes saw sensor values "much lower than usual" after a sensor change. He cut his insulin and developed diabetic ketoacidosis (DKA, a dangerous acid build-up from too little insulin).
- Says (full text): at admission the sensor read 40 mg/dL and the fingerstick read 417 mg/dL.
- Use: Introduction. One documented path from a false low reading to harm.

### Topic 2. The REPLACE-BG trial and its dataset

**[7]** G. Aleppo et al., "REPLACE-BG: A Randomized Trial Comparing Continuous Glucose Monitoring With and Without Routine Blood Glucose Monitoring in Adults With Well-Controlled Type 1 Diabetes," *Diabetes Care*, vol. 40, no. 4, pp. 538-545, Apr. 2017, doi: 10.2337/dc16-2482.
- Link: https://pubmed.ncbi.nlm.nih.gov/28209654/
- Opened: PubMed; PMC (PMC5864100).
- Says: question = is CGM without confirming fingersticks as safe and effective as CGM with fingersticks. Design = randomized noninferiority trial, 14 sites, 26 weeks, 2:1, CGM-only n = 149, CGM+BGM n = 77. Adults with type 1 diabetes on pumps, HbA1c 9.0 % or less.
- Says: time in 70-180 mg/dL was 63 % in the CGM-only group and 65 % in the CGM+BGM group at 26 weeks (adjusted difference 0 %). Meter tests per day 2.8 vs 5.4.
- Says (full text): the sensor was the "Dexcom G4 Platinum CGM System with an enhanced algorithm (Software 505)". The meter was the CONTOUR NEXT. The paper reports no MARD.
- Use: Methods. Source of the data, the devices, the arms. This confirms the Software 505 guess in `analysis/ACCURACY_V2.md`.

**[8]** Jaeb Center for Health Research, "A Randomized Trial Comparing Continuous Glucose Monitoring With and Without Routine Blood Glucose Monitoring in Adults with Type 1 Diabetes" (public dataset), JCHR Public Study Websites. Accessed: Nov. 20, 2026. [Online].
- Link: https://public.jaeb.org/dataset/546 (list of datasets: https://public.jaeb.org/datasets/diabetes)
- Opened: Direct.
- Says: download needs name, email, institution and planned use, and a tick box for the terms of use.
- Says: terms = users must include a set attribution sentence ("The source of the data is ..."), the publisher gives no warranty, and users carry all responsibility and liability.
- Says: the page names no licence. The words "no redistribution" are not on the page.
- Use: Methods. Data source and terms. Copy the attribution sentence from the dataset's Read Me file.

**[9]** J. F. Mulley, "Prevalence, duration, and clinical implications of continuous glucose monitor measurement limit capping in type 1 diabetes," *Diabet. Med.*, vol. 43, no. 10, Art. no. e70412, Oct. 2026, doi: 10.1111/dme.70412.
- Link: https://pubmed.ncbi.nlm.nih.gov/42394198/
- Opened: PubMed; PMC (PMC13643679).
- Says: 46,990,617 CGM readings, 948 people, four public trial datasets (REPLACE-BG is one). Capped readings (stuck at the 40 or 400 mg/dL limit) were 0.47 to 0.98 % of readings.
- Says: in the 77 people of the REPLACE-BG CGM+BGM arm, over 1,162 two-week windows, CGM mean glucose was 10.0 mg/dL below the meter mean (158.4 vs 168.4). CGM time in range was 8.3 points higher (64.4 % vs 56.1 %).
- Says (full text): no MARD, no paired bias, no accuracy by range, no fault simulation. Window numbers were computed separately from CGM data and from meter data.
- Use: Introduction (the gap) and Discussion. The team's "Mulley 2026".

**[10]** P. Avari, C. Uduku, D. George, P. Herrero, M. Reddy, and N. Oliver, "Differences for Percentage Times in Glycemic Range Between Continuous Glucose Monitoring and Capillary Blood Glucose Monitoring in Adults with Type 1 Diabetes: Analysis of the REPLACE-BG Dataset," *Diabetes Technol. Ther.*, vol. 22, no. 3, pp. 222-227, Mar. 2020, doi: 10.1089/dia.2019.0276.
- Link: https://pubmed.ncbi.nlm.nih.gov/31613142/
- Opened: PubMed; PMC (PMC7047084).
- Says: 226 participants. Median time in range 63.0 % from CGM vs 54.6 % from fingersticks (P < 0.001).
- Says (full text): no paired point accuracy (no MARD, bias or error grid) and no simulation.
- Use: Introduction. An earlier re-use of the same dataset that did not measure sensor error.

### Topic 3. The Shanghai datasets

**[11]** Q. Zhao et al., "Chinese diabetes datasets for data-driven machine learning," *Sci. Data*, vol. 10, no. 1, Art. no. 35, Jan. 2023, doi: 10.1038/s41597-023-01940-7.
- Link: https://pubmed.ncbi.nlm.nih.gov/36653358/
- Opened: PubMed; PMC (PMC9849330).
- Says: type 1 n = 12, type 2 n = 100, Shanghai, real-life conditions, CGM periods of 3 to 14 days.
- Says (full text): sensor = FreeStyle Libre H (Abbott), one value every 15 minutes. The meter is not named. "the CBG values were usually greater than those of CGM readings" (CBG = fingerstick). No MARD is given.
- Use: Methods (comparator dataset). Introduction: the authors saw the sensor read low and did not measure it.

**[12]** Q. Zhao, J. Zhu, C. Wang, and W. Rao, "Diabetes Datasets, ShanghaiT1DM and ShanghaiT2DM," figshare, collection, ver. 2, Jan. 4, 2023, doi: 10.6084/m9.figshare.c.6310860.
- Link: https://doi.org/10.6084/m9.figshare.c.6310860 (data file: https://doi.org/10.6084/m9.figshare.21600933.v5)
- Opened: Direct (figshare's public record for the collection and for the data file; the normal web page returned "403 forbidden").
- Says: host = figshare. Licence of the data file = CC BY 4.0. Data file version 5, dated Oct. 30, 2023.
- Use: Methods. Host and licence.

### Topic 4. FDA MAUDE and openFDA

**[13]** U.S. Food and Drug Administration, "About Manufacturer and User Facility Device Experience (MAUDE) Database," FDA, content current as of Dec. 8, 2025. Accessed: Nov. 20, 2026. [Online].
- Link: https://www.fda.gov/medical-devices/mandatory-reporting-requirements-manufacturers-importers-and-device-user-facilities/about-manufacturer-and-user-facility-device-experience-maude-database
- Opened: Direct.
- Says: "MDR data is not intended to be used either to evaluate rates of adverse events, evaluate a change in event rates over time, or to compare adverse event occurrence rates across devices."
- Says: "this passive surveillance system has limitations. The incidence, prevalence, or cause of an event cannot be determined from this reporting system alone due to under-reporting of events, inaccuracies in reports, lack of verification that the device caused the reported event, and lack of information about frequency of device use."
- Says: reporters are manufacturers, importers, user facilities (mandatory) and voluntary reporters.
- Use: Methods and Discussion. The limits of the report data, in FDA's own words.

**[14]** U.S. Food and Drug Administration, "Device Adverse Event Overview," openFDA. Accessed: Nov. 20, 2026. [Online]. Midterm ref [16].
- Link: https://open.fda.gov/apis/device/event/
- Opened: with a page-reading tool.
- Says: the service returns MAUDE reports and is updated weekly.
- Says: "a causal relationship cannot be established between product and reactions listed in a report." "Adverse event reports submitted to FDA do not undergo extensive validation or verification."
- Use: Methods. How the reports were pulled.

### Topic 5. Published accuracy of the Dexcom G4 Platinum and the Abbott FreeStyle Libre family

Summary table. Details and links are in the entries below.

| Ref | Device | Setting | Reference | MARD % |
|---|---|---|---|---|
| [15] | G4 Platinum, original | clinic, 72 people | YSI lab | 13 overall; 16.7 day 1; 18 when YSI is 70 or less |
| [16] | G4 Platinum (guess: original software, same study as [15]) | 72 people | YSI; meter | 13 (YSI); 14 (meter) |
| [17] | G4 Platinum "with an advanced algorithm" (guess: Software 505) | clinic; home, 51 adults | YSI; Contour Next meter | 9.0 (YSI); 11.3 (meter, home use) |
| [18] | G4 Platinum, original vs Software 505, ages 2-17 | clinic | YSI; meter | 17 vs 10 (YSI); 15 vs 13 (meter) |
| [19] | G4 Platinum (software not named in the abstract), 24 people | clinic; 6 days at home | venous lab; meter | 13.6 (clinic); 12.2 (home) |
| [20] | G4 Platinum (software not named in the abstract), 38 people | daily life, 4-6 days | HemoCue meter | 13.9; 20.0 under 72 mg/dL (4.0 mmol/L) |
| [21] | FreeStyle Libre, first generation, 72 people | 14 days, home and clinic | built-in meter; YSI | 11.4 (meter); 12.0 (YSI) |
| [5] | FreeStyle Libre Pro | clinic | lab comparator | 12.1 |
| [22] | FreeStyle Libre 2 | clinic | YSI | 9.2 adults; 9.7 children |
| [23] | FreeStyle Libre 3 | clinic | YSI | 7.8 (age 6 and over) |
| [24] | FreeStyle Libre, 742 inpatients, type 2 | hospital | hospital meter | 14 |
| [25] | Abbott FreeStyle Navigator II | home, free living | built-in meter | 14.2; 30.6 under 70 mg/dL |

**[15]** M. Christiansen et al., "A new-generation continuous glucose monitoring system: improved accuracy and reliability compared with a previous-generation system," *Diabetes Technol. Ther.*, vol. 15, no. 10, pp. 881-888, Oct. 2013, doi: 10.1089/dia.2013.0077.
- Link: https://pubmed.ncbi.nlm.nih.gov/23777402/
- Opened: PubMed; PMC (PMC3781114).
- Says: original G4 Platinum against YSI: MARD 13 %; 82 % within 20/20. Mean absolute difference 11 mg/dL when YSI was under 70.
- Says (full text): MARD by day: 16.7 % day 1, 11.4 % day 4, 11.9 % day 7. MARD 18 % when YSI was 70 or less. Mean bias not reported.
- Use: Results comparison. Pivotal clinic accuracy of the original G4; first-day and low-range error.

**[16]** K. Nakamura and A. Balo, "The Accuracy and Efficacy of the Dexcom G4 Platinum Continuous Glucose Monitoring System," *J. Diabetes Sci. Technol.*, vol. 9, no. 5, pp. 1021-1026, 2015, doi: 10.1177/1932296815577812.
- Link: https://pubmed.ncbi.nlm.nih.gov/25802469/
- Opened: PubMed (abstract only).
- Says: 72 subjects at 4 US centers. MARD 13 % against YSI and 14 % against the meter (SMBG).
- Says: the abstract does not name the software. guess: original software, same study as [15] (same 72 subjects and 4 centers).
- Use: Results comparison. A meter-reference MARD for the G4.

**[17]** T. S. Bailey, A. Chang, and M. Christiansen, "Clinical accuracy of a continuous glucose monitoring system with an advanced algorithm," *J. Diabetes Sci. Technol.*, vol. 9, no. 2, pp. 209-214, Mar. 2015, doi: 10.1177/1932296814559746.
- Link: https://pubmed.ncbi.nlm.nih.gov/25370149/
- Opened: PubMed; PMC (PMC4604574).
- Says: 51 subjects, "a modified Dexcom G4 Platinum system with an advanced algorithm". Against YSI (n = 2,263): MARD 9.0 %, median 7.0 %.
- Says: "The MARD of CGM-SMBG for home use was 11.3%."
- Says (full text): adults 18 or older. Home pairs: 2,992, against a Bayer Contour Next USB meter. MARD against YSI by day: 10.7 % day 1, 8.0 % day 4, 8.5 % day 7. The results text gives 11.2 % where the abstract and table give 11.3 %.
- Says (full text): the paper never uses the name "Software 505". guess: it is the same algorithm (REPLACE-BG [7] calls its sensor the G4 "with an enhanced algorithm (Software 505)").
- Use: Results comparison. The closest published number to ours: home use, adults, Contour Next meter as reference.

**[18]** L. Laffel, "Improved Accuracy of Continuous Glucose Monitoring Systems in Pediatric Patients with Diabetes Mellitus: Results from Two Studies," *Diabetes Technol. Ther.*, vol. 18, suppl. 2, pp. S223-S233 (page numbers as PubMed lists them), Feb. 2016, doi: 10.1089/dia.2015.0380.
- Link: https://pubmed.ncbi.nlm.nih.gov/26784126/
- Opened: PubMed (abstract only).
- Says: ages 2-17. Against YSI: MARD 17 % (original) vs 10 % (Software 505). Against the meter: 15 % vs 13 %.
- Use: Results comparison. Size of the software effect.

**[19]** J. Kropff et al., "Accuracy of two continuous glucose monitoring systems: a head-to-head comparison under clinical research centre and daily life conditions," *Diabetes Obes. Metab.*, vol. 17, no. 4, pp. 343-349, Apr. 2015, doi: 10.1111/dom.12378.
- Link: https://pubmed.ncbi.nlm.nih.gov/25132320/
- Opened: PubMed (abstract only).
- Says: G4 Platinum MARD 13.6 % in the clinic and 12.2 % at home (meter reference, n = 839). The abstract does not name the software version.
- Says: in the clinic, G4 MARD was 17.6 % at 70 mg/dL or less against 13.0 % at 70-180.
- Use: Results comparison. Home-use G4 number; worse accuracy at low glucose.

**[20]** V. Matuleviciene et al., "A clinical trial of the accuracy and treatment experience of the Dexcom G4 sensor (Dexcom G4 system) and Enlite sensor (guardian REAL-time system) tested simultaneously in ambulatory patients with type 1 diabetes," *Diabetes Technol. Ther.*, vol. 16, no. 11, pp. 759-767, Nov. 2014, doi: 10.1089/dia.2014.0238.
- Link: https://pubmed.ncbi.nlm.nih.gov/25233297/
- Opened: PubMed (abstract only).
- Says: 38 people in daily life, HemoCue meter 6 to 10 times a day. G4 MARD 13.9 %. Days 1-3: 15.0 %. Under 4.0 mmol/L (72 mg/dL): 20.0 %. The abstract does not name the software version.
- Use: Results comparison. Home-use G4 number with a meter reference.

**[21]** T. Bailey, B. W. Bode, M. P. Christiansen, L. J. Klaff, and S. Alva, "The Performance and Usability of a Factory-Calibrated Flash Glucose Monitoring System," *Diabetes Technol. Ther.*, vol. 17, no. 11, pp. 787-794, Nov. 2015, doi: 10.1089/dia.2014.0378.
- Link: https://pubmed.ncbi.nlm.nih.gov/26171659/
- Opened: PubMed; PMC (PMC4649725).
- Says: 72 participants, 14 days. MARD 11.4 % against the built-in meter; 86.7 % in consensus grid zone A. Lag 4.5 ± 4.8 min.
- Says: "Sensor accuracy was not affected by factors such as body mass index, age, type of diabetes, clinical site, insulin administration, or hemoglobin A1c."
- Says (full text): 13,195 meter pairs; MARD 12.0 % against YSI; zones A+B 99.7 %; day-1 zone A 72.0 %. Mean bias not reported.
- Use: Results comparison (Shanghai comparator). Also topic 15: sex is not in the list of factors tested.

**[22]** S. Alva et al., "Accuracy of a 14-Day Factory-Calibrated Continuous Glucose Monitoring System With Advanced Algorithm in Pediatric and Adult Population With Diabetes," *J. Diabetes Sci. Technol.*, vol. 16, no. 1, pp. 70-77, Jan. 2022, doi: 10.1177/1932296820958754.
- Link: https://pubmed.ncbi.nlm.nih.gov/32954812/
- Opened: PubMed (abstract only).
- Says: FreeStyle Libre 2 against YSI: MARD 9.2 % (144 adults) and 9.7 % (129 children); 93.2 % and 92.1 % within 20/20.
- Use: Results comparison or Discussion. Newer Libre generation.

**[23]** S. Alva, R. Brazg, K. Castorino, M. Kipnes, D. R. Liljenquist, and H. Liu, "Accuracy of the Third Generation of a 14-Day Continuous Glucose Monitoring System," *Diabetes Ther.*, vol. 14, no. 4, pp. 767-776, Apr. 2023, doi: 10.1007/s13300-023-01385-6.
- Link: https://pubmed.ncbi.nlm.nih.gov/36877403/
- Opened: PubMed (abstract only).
- Says: FreeStyle Libre 3 against YSI, age 6 and over: MARD 7.8 %, 93.4 % within 20/20, 6,845 pairs, 100 participants.
- Use: Introduction or Discussion. The expected accuracy of the recalled sensor model when it works.

**[24]** X. Wen et al., "Diabetes Complications and Related Comorbidities Impair the Accuracy of FreeStyle Libre, a Flash Continuous Glucose Monitoring System, in Patients with Type 2 Diabetes," *Diabetes Metab. Syndr. Obes.*, vol. 15, pp. 3437-3445, Nov. 2022, doi: 10.2147/DMSO.S381565.
- Link: https://pubmed.ncbi.nlm.nih.gov/36353669/
- Opened: PubMed; PMC (PMC9639390).
- Says: 742 inpatients, 25,579 pairs. At 3 AM: bias -23.0 %, MARD 24.5 %. "FCGM commonly underestimates blood glucose levels."
- Says: sensor below the meter in 75 % of pairs (abstract) and in 72.3 % of pairs (results text). The paper gives both numbers.
- Says (full text): overall MARD 14 %. Meter = Accu-Chek Performa.
- Use: Results comparison (Shanghai). An Abbott flash sensor reading low in Chinese inpatients.

**[25]** H. Thabit et al., "Accuracy of Continuous Glucose Monitoring During Three Closed-Loop Home Studies Under Free-Living Conditions," *Diabetes Technol. Ther.*, vol. 17, no. 11, pp. 801-807, Nov. 2015, doi: 10.1089/dia.2015.0062.
- Link: https://pubmed.ncbi.nlm.nih.gov/26241693/
- Opened: PubMed; PMC (PMC4649721).
- Says: FreeStyle Navigator II at home, 57 people. MARD 14.2 ± 15.5 % overall; 9.8 % above 10 mmol/L (180 mg/dL).
- Says (full text, Table 2): 30.6 % under 3.9 mmol/L (70 mg/dL); 13.9 % at 3.9-10.0. Pairs: 10,597 in the abstract, 10,647 in the table.
- Use: Results comparison. A home-use, meter-reference study with range splits.

**[26]** G. Freckmann, M. Link, S. Pleus, A. Westhoff, U. Kamecke, and C. Haug, "Measurement Performance of Two Continuous Tissue Glucose Monitoring Systems Intended for Replacement of Blood Glucose Monitoring," *Diabetes Technol. Ther.*, vol. 20, no. 8, pp. 541-549, Aug. 2018, doi: 10.1089/dia.2018.0105.
- Link: https://pubmed.ncbi.nlm.nih.gov/30067410/
- Opened: PubMed (abstract only).
- Says: Dexcom G5 and FreeStyle Libre, 20 people, 14 days. About 25 % of readings at times of treatment decisions differed from the meter by more than 15 mg/dL or 15 %. About 5 % differed by more than 30 mg/dL or 30 %. Over 99.5 % were in consensus grid zones A and B.
- Use: Discussion. Error grids look fine while one decision in four rests on a reading more than 15 % off.

**[27]** V. Dávila-Ruales, L. F. Gilón, A. M. Gómez, O. M. Muñoz, M. N. Serrano, and D. C. Henao, "Evaluating the precision and reliability of real-time continuous glucose monitoring systems in ambulatory settings: a systematic review," *Ther. Adv. Endocrinol. Metab.*, vol. 15, Art. no. 20420188241304459, Dec. 2024, doi: 10.1177/20420188241304459. Midterm ref [8].
- Link: https://pubmed.ncbi.nlm.nih.gov/39669532/
- Opened: PubMed (abstract only).
- Says: 22 studies, 2,294 patients. Average MARD 9.4 %. No device met the ISO 15197:2013 limit (95 % within 15 mg/dL) in the low range. Sensitivity for hypoglycemia 85.7 %.
- Use: Introduction. Current sensors are weakest at low glucose.

### Topic 6. FDA integrated CGM (iCGM) special controls

**[28]** *Integrated continuous glucose monitoring system*, 21 C.F.R. § 862.1355 (2025). [Online]. Midterm ref [25].
- Link: https://www.ecfr.gov/current/title-21/section-862.1355 (text opened at https://www.govinfo.gov/content/pkg/CFR-2025-title21-vol8/xml/CFR-2025-title21-vol8-sec862-1355.xml and through the eCFR data service, version 2026-01-01; both texts are the same)
- Opened: Direct. The normal eCFR web page blocked scripts.
- Says: limits apply to adult clinical data. Each one is a lower one-sided 95 % confidence bound. Bins are by the iCGM (sensor) value. The reference is an FDA-accepted lab method.

| Paragraph | iCGM value | Readings within | Lower bound must exceed |
|---|---|---|---|
| (A) | under 70 mg/dL | ±15 mg/dL | 85 % |
| (B) | 70 to 180 mg/dL | ±15 % | 70 % |
| (C) | over 180 mg/dL | ±15 % | 80 % |
| (D) | under 70 mg/dL | ±40 mg/dL | 98 % |
| (E) | 70 to 180 mg/dL | ±40 % | 99 % |
| (F) | over 180 mg/dL | ±40 % | 99 % |
| (G) | whole range | ±20 % | 87 % |

- Says: (H) when the iCGM reads under 70, no blood value above 180. (I) when the iCGM reads over 180, no blood value under 70. (J), (K): no more than 1 % of readings may show a rise above 1 mg/dL/min when blood is falling faster than 2 mg/dL/min, or the reverse.
- Use: Methods and Results comparison. The regulator's yardstick for our iCGM-style table.

**[29]** Food and Drug Administration, "Medical Devices; Clinical Chemistry and Clinical Toxicology Devices; Classification of the Integrated Continuous Glucose Monitoring System," *Fed. Regist.*, vol. 87, no. 34, pp. 9237-9239, Feb. 18, 2022 (final order, Docket No. FDA-2021-N-1343).
- Link: https://www.govinfo.gov/content/pkg/FR-2022-02-18/pdf/2022-03504.pdf
- Opened: Direct (PDF, first page read).
- Says: FDA classifies the iCGM into class II (special controls). "This order is effective February 18, 2022. The classification was applicable on March 27, 2018."
- Use: Methods. Origin and date of the iCGM rule.

### Topic 7. Accuracy of fingerstick meters

**[30]** *In vitro diagnostic test systems - Requirements for blood-glucose monitoring systems for self-testing in managing diabetes mellitus*, ISO 15197:2013, 2nd ed., International Organization for Standardization, Geneva, Switzerland, May 2013.
- Link: https://www.iso.org/standard/54976.html
- Opened: Direct (catalogue page only; the standard itself is paid).
- Says: edition 2, published 2013-05, 46 pages, last reviewed and confirmed in 2018, stage "to be revised". The page does not print the accuracy limits. Take the limits from [31].
- Use: Methods. The meter standard.

**[31]** N. Jendrike, A. Baumstark, U. Kamecke, C. Haug, and G. Freckmann, "ISO 15197: 2013 Evaluation of a Blood Glucose Monitoring System's Measurement Accuracy," *J. Diabetes Sci. Technol.*, vol. 11, no. 6, pp. 1275-1276, Nov. 2017, doi: 10.1177/1932296817727550. Midterm ref [24].
- Link: https://pubmed.ncbi.nlm.nih.gov/28849677/
- Opened: PubMed; PMC (PMC5951056).
- Says (full text): "at least 95% of BGMS results have to be within ±15 mg/dl at glucose concentrations <100 mg/dl and within ±15% at ≥100 mg/dl". Also "at least 99% of results have to be within zones A and B" of the consensus error grid.
- Use: Methods. The exact ISO limits used in our meter-error check.

**[32]** D. C. Klonoff et al., "Investigation of the Accuracy of 18 Marketed Blood Glucose Monitors," *Diabetes Care*, vol. 41, no. 8, pp. 1681-1688, Aug. 2018, doi: 10.2337/dc17-1960.
- Link: https://pubmed.ncbi.nlm.nih.gov/29898901/
- Opened: PubMed (abstract only).
- Says: 1,035 subjects, 18 FDA-cleared meters, three studies. Six of 18 met the accuracy standard in all three studies. Four met it in none.
- Use: Discussion (limits). Real-world meters do not always meet the standard.

**[33]** L. Ekhlaspour et al., "Comparative Accuracy of 17 Point-of-Care Glucose Meters," *J. Diabetes Sci. Technol.*, vol. 11, no. 3, pp. 558-566, May 2017, doi: 10.1177/1932296816672237.
- Link: https://pubmed.ncbi.nlm.nih.gov/27697848/
- Opened: PubMed; PMC (PMC5505415).
- Says: MARD ranged from 5.6 % to 20.8 % across 17 meters, against YSI.
- Says (full text): the Contour Next had the lowest MARD, 5.6 % overall and 8.9 % under 70 mg/dL.
- Use: Methods and Discussion. Accuracy of our reference meter.

**[34]** D. J. DeSalvo, S. Shanmugham, T. T. Ly, D. M. Wilson, and B. A. Buckingham, "Accuracy evaluation of blood glucose monitoring systems in children on overnight closed-loop control," *J. Diabetes Sci. Technol.*, vol. 8, no. 5, pp. 969-973, Sep. 2014, doi: 10.1177/1932296814532238.
- Link: https://pubmed.ncbi.nlm.nih.gov/24876427/
- Opened: PubMed (abstract only).
- Says: 28 subjects, 457 time points, against YSI. Contour Next MARD 3.13 %; HemoCue 10.73 %.
- Use: Methods. Source of the "about 3 %" figure for our meter. Note [33] found 5.6 % in a harder test.

### Topic 8. How CGM accuracy is measured, and its problems

**[35]** F. Reiterer et al., "Significance and Reliability of MARD for the Accuracy of CGM Systems," *J. Diabetes Sci. Technol.*, vol. 11, no. 1, pp. 59-67, Jan. 2017, doi: 10.1177/1932296816662047.
- Link: https://pubmed.ncbi.nlm.nih.gov/27566735/
- Opened: PubMed (abstract only).
- Says: MARD values "are strongly influenced by the design of the study" and should be read "not as precise values but as indications with some uncertainty".
- Use: Methods and Discussion. Why MARD needs confidence intervals and care across studies.

**[36]** H. Kirchsteiger et al., "Performance Comparison of CGM Systems: MARD Values Are Not Always a Reliable Indicator of CGM System Accuracy," *J. Diabetes Sci. Technol.*, vol. 9, no. 5, pp. 1030-1040, Sep. 2015, doi: 10.1177/1932296815586013.
- Link: https://pubmed.ncbi.nlm.nih.gov/26330485/
- Opened: PubMed (abstract only).
- Says: MARD depends on the number of pairs, the spread of glucose values, the accuracy of the reference and the time delay between pairs.
- Use: Discussion. Why our home, meter-reference MARD differs from clinic figures.

**[37]** L. Heinemann et al., "Benefits and Limitations of MARD as a Performance Parameter for Continuous Glucose Monitoring in the Interstitial Space," *J. Diabetes Sci. Technol.*, vol. 14, no. 1, pp. 135-150, Jan. 2020, doi: 10.1177/1932296819855670.
- Link: https://pubmed.ncbi.nlm.nih.gov/31216870/
- Opened: PubMed (abstract only).
- Says: "The MARD should not be used as the sole parameter to characterize CGM systems, especially when it comes to nonadjunctive usage of such systems."
- Use: Introduction or Discussion. MARD alone does not show whether dosing from the sensor is safe.

**[38]** J. L. Parkes, S. L. Slatin, S. Pardo, and B. H. Ginsberg, "A new consensus error grid to evaluate the clinical significance of inaccuracies in the measurement of blood glucose," *Diabetes Care*, vol. 23, no. 8, pp. 1143-1148, Aug. 2000, doi: 10.2337/diacare.23.8.1143.
- Link: https://pubmed.ncbi.nlm.nih.gov/10937512/
- Opened: PubMed (abstract only).
- Says: 100 diabetes experts assigned each possible error to 1 of 5 risk categories. Separate grids for type 1 and type 2 diabetes.
- Use: Methods. The Parkes (consensus) error grid.

**[39]** A. Pfützner, D. C. Klonoff, S. Pardo, and J. L. Parkes, "Technical aspects of the Parkes error grid," *J. Diabetes Sci. Technol.*, vol. 7, no. 5, pp. 1275-1281, Sep. 2013, doi: 10.1177/193229681300700517.
- Link: https://pubmed.ncbi.nlm.nih.gov/24124954/
- Opened: PubMed (abstract only).
- Says: gives the exact zone coordinates of the Parkes grid. ISO 15197:2013 uses this grid.
- Use: Methods. Cite for the zone borders in our code.

**[40]** D. C. Klonoff et al., "The surveillance error grid," *J. Diabetes Sci. Technol.*, vol. 8, no. 4, pp. 658-672, Jul. 2014, doi: 10.1177/1932296814539589.
- Link: https://pubmed.ncbi.nlm.nih.gov/25562886/
- Opened: PubMed (abstract only).
- Says: 206 clinicians rated the risk of meter errors. Each data point gets its own risk score; points are grouped into 15 risk zones.
- Use: Methods or Discussion. The surveillance error grid.

**[41]** D. C. Klonoff et al., "The Diabetes Technology Society Error Grid and Trend Accuracy Matrix for Glucose Monitors," *J. Diabetes Sci. Technol.*, vol. 18, no. 6, pp. 1346-1361, Nov. 2024, doi: 10.1177/19322968241275701. Midterm ref [9].
- Link: https://pubmed.ncbi.nlm.nih.gov/39369312/
- Opened: PubMed (abstract only).
- Says: 89 experts. One grid with five zones (A to E) for both meters and CGMs. Each 1 % more data in zone A went with about 0.33 % lower MARD.
- Use: Discussion. The newest error grid.

**[42]** W. L. Clarke, D. Cox, L. A. Gonder-Frederick, W. Carter, and S. L. Pohl, "Evaluating clinical accuracy of systems for self-monitoring of blood glucose," *Diabetes Care*, vol. 10, no. 5, pp. 622-628, Sep.-Oct. 1987, doi: 10.2337/diacare.10.5.622.
- Link: https://pubmed.ncbi.nlm.nih.gov/3677983/
- Opened: PubMed (abstract only).
- Says: introduces error grid analysis, which rates errors by their clinical meaning.
- Use: Methods (appendix). The Clarke grid.

**[43]** J. M. Bland and D. G. Altman, "Agreement between methods of measurement with multiple observations per individual," *J. Biopharm. Stat.*, vol. 17, no. 4, pp. 571-582, 2007, doi: 10.1080/10543400701329422.
- Link: https://pubmed.ncbi.nlm.nih.gov/17613642/
- Opened: PubMed (abstract only).
- Says: gives limits-of-agreement methods for repeated pairs from the same person.
- Use: Methods. Our repeated-measures limits of agreement.

**[44]** G. Freckmann et al., "Clinical Performance Evaluation of Continuous Glucose Monitoring Systems: A Scoping Review and Recommendations for Reporting," *J. Diabetes Sci. Technol.*, vol. 17, no. 6, pp. 1506-1526, Nov. 2023, doi: 10.1177/19322968231190941.
- Link: https://pubmed.ncbi.nlm.nih.gov/37599389/
- Opened: PubMed; PMC (PMC10658695, first part).
- Says (full text): 129 studies, 2002 to 2022. "most studies (76.0%) included adults only." "10.9% of studies did not report the subject sex". "only 24.8% reported the ethnicity of the subjects."
- Says (full text): 55.0 % of studies used in-clinic data only; 21.7 % free-living data only. Accuracy against subject characteristics was analysed in 10.1 % of studies.
- Use: Introduction and Discussion. Gaps in the evidence. Also topic 15.

### Topic 9. Nonadjunctive use

**[45]** U.S. Food and Drug Administration, "Summary of Safety and Effectiveness Data (SSED): Dexcom G5 Mobile Continuous Glucose Monitoring System," PMA P120005/S041, approved Dec. 20, 2016. Accessed: Nov. 20, 2026. [Online].
- Link: https://www.accessdata.fda.gov/cdrh_docs/pdf12/P120005S041B.pdf (record: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpma/pma.cfm?id=P120005S041)
- Opened: Direct (PDF, 16 pages) and the record page.
- Says: new indication: "The Dexcom G5 is designed to replace fingerstick blood glucose testing for diabetes treatment decisions." Age 2 years and older.
- Says: panel of July 21, 2016 voted 8 to 2 (safe), 9 to 1 (effective), 8 to 2 (benefits outweigh risks). "No new clinical study was conducted".
- Says: Dexcom ran two computer simulations ("meal-dosing" and "two-week"). Panel members "generally concluded that the results of the simulations were not helpful ... and these simulations were therefore not considered in the determination of device safety and effectiveness."
- Use: Introduction. The decision that lets people dose from a CGM, and how little weight simulation carried in it.

**[46]** J. R. Castle and P. G. Jacobs, "Nonadjunctive Use of Continuous Glucose Monitoring for Diabetes Treatment Decisions," *J. Diabetes Sci. Technol.*, vol. 10, no. 5, pp. 1169-1173, Sep. 2016, doi: 10.1177/1932296816631569. Midterm ref [7].
- Link: https://pubmed.ncbi.nlm.nih.gov/26880390/
- Opened: PubMed (abstract only).
- Says: review written before the approval. Expects CGM alone to replace routine fingersticks.
- Use: Introduction. Background on nonadjunctive use.

**[47]** S. V. Edelman, "Regulation Catches Up to Reality," *J. Diabetes Sci. Technol.*, vol. 11, no. 1, pp. 160-164, Jan. 2017, doi: 10.1177/1932296816667749.
- Link: https://pubmed.ncbi.nlm.nih.gov/27630249/
- Opened: PubMed (abstract only).
- Says: commentary on the FDA panel meeting for the G5 nonadjunctive claim. Argues in favour.
- Use: Introduction. One side of the debate.

**[48]** A. R. Shapiro, "Nonadjunctive Use of Continuous Glucose Monitors for Insulin Dosing: Is It Safe?," *J. Diabetes Sci. Technol.*, vol. 11, no. 4, pp. 833-838, Jul. 2017, doi: 10.1177/1932296816688303.
- Link: https://pubmed.ncbi.nlm.nih.gov/28540756/
- Opened: PubMed; PMC (PMC5588827).
- Says: "A text analysis of reports to the FDA MAUDE database since 2015 reveals over 25 000 complaints of CGM sensor inaccuracy, with instances directly leading to serious outcomes."
- Says (full text): 25,966 complaints about Dexcom G4/G5 inaccuracy, start of 2015 to September 2016. 415 gave both values; over 95 % of those differed by 30 mg/dL or more and 55 % by 100 mg/dL or more. More than 150 detailed serious outcomes.
- Says (full text): Dexcom's simulations used a single-peak error spread with a 9 % MARD. The author's point: the question is how often large errors happen, not the average.
- Use: Introduction and Discussion. The other side of the debate, and the nearest earlier text analysis of MAUDE CGM reports. Also topic 11.

### Topic 10. Simulation and modelling of sensor or meter error and treatment decisions

**[49]** B. P. Kovatchev, S. D. Patek, E. A. Ortiz, and M. D. Breton, "Assessing sensor accuracy for non-adjunct use of continuous glucose monitoring," *Diabetes Technol. Ther.*, vol. 17, no. 3, pp. 177-186, Mar. 2015, doi: 10.1089/dia.2014.0272. Midterm ref [5].
- Link: https://pubmed.ncbi.nlm.nih.gov/25436913/
- Opened: PubMed; PMC (PMC4346608).
- Says: records of 56 pump users were "replayed" through a body model. 2,082 glucose segments, each starting at an insulin dose. Seven error levels (MARD 3 to 22 %). Six scenarios (dosing, threshold alarms, predictive alarms; each with and without trend arrows).
- Says: low glucose (50 mg/dL or less, 39 or less) and high glucose (250 or more, 400 or more) rose with sensor error, with "an abrupt slope change at MARD =10%". Conclusion: dosing from CGM "is feasible below a certain level of sensor error, estimated in silico at MARD=10%."
- Says (full text): error came from 280 real sensor traces scaled up or down. No designed low-reading fault. No dropouts. Low treated with 15 g carbohydrate every 15 min; high corrected toward 120 mg/dL.
- Use: Introduction and Discussion. The closest earlier study.

**[50]** M. Vettoretti, A. Facchinetti, G. Sparacino, and C. Cobelli, "Predicting Insulin Treatment Scenarios with the Net Effect Method: Domain of Validity," *Diabetes Technol. Ther.*, vol. 18, no. 11, pp. 694-704, Nov. 2016, doi: 10.1089/dia.2016.0148.
- Link: https://pubmed.ncbi.nlm.nih.gov/27860496/
- Opened: PubMed (abstract only).
- Says: tests the replay method of [49] ("net effect") against a full simulator.
- Says: the method "underestimates time in hyperglycemia when introducing correction boluses" and "overestimates time in hypoglycemia when introducing hypotreatments". It "is reliable for small adjustments of basal insulin, while outside this domain of validity it can provide inaccurate results."
- Use: Discussion (limits). A published limit of replay methods that predict glucose after a changed decision.

**[51]** M. Vettoretti, A. Facchinetti, G. Sparacino, and C. Cobelli, "Type-1 Diabetes Patient Decision Simulator for In Silico Testing Safety and Effectiveness of Insulin Treatments," *IEEE Trans. Biomed. Eng.*, vol. 65, no. 6, pp. 1281-1290, Jun. 2018, doi: 10.1109/TBME.2017.2746340.
- Link: https://pubmed.ncbi.nlm.nih.gov/28866479/
- Opened: PubMed (abstract only).
- Says: joins a body model (UVA/Padova) with models of meter and CGM error, patient decisions and insulin delivery. Checked against 44 people using a Dexcom G5 with a meter.
- Says: time in range 61.75 % real vs 63.60 % simulated; time low 3.17 % vs 2.14 %.
- Use: Introduction and Methods. Earlier model of patient decisions under sensor error.

**[52]** M. Vettoretti, A. Facchinetti, G. Sparacino, and C. Cobelli, "Patient decision-making of CGM sensor driven insulin therapies in type 1 diabetes: In silico assessment," in *Proc. 37th Annu. Int. Conf. IEEE Eng. Med. Biol. Soc. (EMBC)*, 2015, pp. 2363-2366, doi: 10.1109/EMBC.2015.7318868.
- Link: https://pubmed.ncbi.nlm.nih.gov/26736768/
- Opened: PubMed (abstract only).
- Says: 20 virtual subjects, 7 days. CGM-driven decisions gave about 9 % more time in 70-180 mg/dL than meter-driven decisions.
- Use: Methods. The team's "Vettoretti 2015".

**[53]** M. D. Breton and B. P. Kovatchev, "Impact of blood glucose self-monitoring errors on glucose variability, risk for hypoglycemia, and average glucose control in type 1 diabetes: an in silico study," *J. Diabetes Sci. Technol.*, vol. 4, no. 3, pp. 562-570, May 2010, doi: 10.1177/193229681000400309.
- Link: https://pubmed.ncbi.nlm.nih.gov/20513321/
- Opened: PubMed; PMC (PMC2901032).
- Says: 100 simulated adults, meter error of 5, 10, 15 and 20 %. Chance of missing a true 60 mg/dL reading: 0 to 1 % at 5-10 % error, 3.5 to 10 % at 15-20 % error. "A threshold effect apparent between 10 and 15% permitted SMBG error".
- Says (full text): error was random with zero average. "we did not investigate the effect of meter bias."
- Use: Introduction. Random meter error and decisions; no bias tested.

**[54]** E. Campos-Náñez, K. Fortwaengler, and M. D. Breton, "Clinical Impact of Blood Glucose Monitoring Accuracy: An In-Silico Study," *J. Diabetes Sci. Technol.*, vol. 11, no. 6, pp. 1187-1195, Nov. 2017, doi: 10.1177/1932296817710474.
- Link: https://pubmed.ncbi.nlm.nih.gov/28569076/
- Opened: PubMed (abstract only).
- Says: 30-day simulation of pump users with models of 43 commercial meters.
- Says: "a positive systemic bias will reduce HbA1c, but increase the number of severe hypoglycemia attacks". Random error raises severe hypoglycemia but has little effect on HbA1c.
- Use: Introduction and Discussion. The direction of a bias matters, not only its size.

**[55]** J. C. Boyd and D. E. Bruns, "Quality specifications for glucose meters: assessment by simulation modeling of errors in insulin dose," *Clin. Chem.*, vol. 47, no. 2, pp. 209-214, Feb. 2001. (PubMed lists no DOI.)
- Link: https://pubmed.ncbi.nlm.nih.gov/11159768/
- Opened: PubMed (abstract only).
- Says: random-draw simulation of meter bias and imprecision against insulin dose tables. At 5 % total error, 8 to 23 % of doses were wrong. At 10 %, 16 to 45 %.
- Use: Introduction. The first error-to-dose simulation.

**[56]** N. S. Virdi and J. J. Mahoney, "Importance of blood glucose meter and carbohydrate estimation accuracy," *J. Diabetes Sci. Technol.*, vol. 6, no. 4, pp. 921-926, Jul. 2012, doi: 10.1177/193229681200600425.
- Link: https://pubmed.ncbi.nlm.nih.gov/22920820/
- Opened: PubMed (abstract only).
- Says: random-draw simulation of five meters plus carbohydrate counting error. On-target doses 50.1 to 98.5 % with exact carbohydrate counts, 27.2 to 80.1 % with counting errors.
- Use: Discussion. Glucose error is one of several sources of dose error.

**[57]** A. Baumstark, N. Jendrike, S. Pleus, C. Haug, and G. Freckmann, "Evaluation of Accuracy of Six Blood Glucose Monitoring Systems and Modeling of Possibly Related Insulin Dosing Errors," *Diabetes Technol. Ther.*, vol. 19, no. 10, pp. 580-588, Oct. 2017, doi: 10.1089/dia.2016.0408.
- Link: https://pubmed.ncbi.nlm.nih.gov/28704063/
- Opened: PubMed (abstract only).
- Says: six meters, measured error fed into a dose model. Up to 14.3 % of modelled doses were off by more than 0.5 U, 4.3 % by more than 1.0 U and 0.3 % by more than 1.5 U (glucose oxidase comparison).
- Use: Results comparison. A published "share of doses changed by more than X units" to set beside ours.

**[58]** A. Facchinetti, S. Del Favero, G. Sparacino, J. R. Castle, W. K. Ward, and C. Cobelli, "Modeling the glucose sensor error," *IEEE Trans. Biomed. Eng.*, vol. 61, no. 3, pp. 620-629, Mar. 2014, doi: 10.1109/TBME.2013.2284023.
- Link: https://pubmed.ncbi.nlm.nih.gov/24108706/
- Opened: PubMed (abstract only).
- Says: splits sensor error into three parts: blood-to-tissue delay, a time-varying part for calibration and drift, and autoregressive noise (noise where each error depends on the one before). Data: 36 adults, four Dexcom SEVEN Plus sensors each.
- Use: Methods. The source for "error = lag + calibration or drift + noise".

**[59]** A. Facchinetti, G. Sparacino, and C. Cobelli, "Modeling the error of continuous glucose monitoring sensor data: critical aspects discussed through simulation studies," *J. Diabetes Sci. Technol.*, vol. 4, no. 1, pp. 4-14, Jan. 2010, doi: 10.1177/193229681000400102.
- Link: https://pubmed.ncbi.nlm.nih.gov/20167162/
- Opened: PubMed (abstract only).
- Says: small errors in recalibration or in the blood-to-tissue model distort the estimated sensor error. "correct characterization of CGM sensor error is still an open issue".
- Use: Methods or Discussion. The team's "Facchinetti 2010". The three-part split is in [58], not here.

**[60]** A. Facchinetti, S. Del Favero, G. Sparacino, and C. Cobelli, "Model of glucose sensor error components: identification and assessment for new Dexcom G4 generation devices," *Med. Biol. Eng. Comput.*, vol. 53, no. 12, pp. 1259-1269, Dec. 2015, doi: 10.1007/s11517-014-1226-y.
- Link: https://pubmed.ncbi.nlm.nih.gov/25416850/
- Opened: PubMed (abstract only).
- Says: error model for the G4 Platinum. MARD 11.1 % (G4 Platinum), 14.2 % (SEVEN Plus), 10.0 % (G4 with the advanced algorithm).
- Use: Methods. An error model for our own sensor type.

**[61]** M. Breton and B. Kovatchev, "Analysis, modeling, and simulation of the accuracy of continuous glucose sensors," *J. Diabetes Sci. Technol.*, vol. 2, no. 5, pp. 853-862, Sep. 2008, doi: 10.1177/193229680800200517.
- Link: https://pubmed.ncbi.nlm.nih.gov/19750186/
- Opened: PubMed (abstract only).
- Says: sensor errors depend on the rate of change, are not independent from one reading to the next, and can be simulated as a delay plus correlated noise.
- Use: Methods. Why plain random noise is not a realistic sensor error.

**[62]** M. Vettoretti, C. Battocchio, G. Sparacino, and A. Facchinetti, "Development of an Error Model for a Factory-Calibrated Continuous Glucose Monitoring Sensor with 10-Day Lifetime," *Sensors*, vol. 19, no. 23, Art. no. 5320, Dec. 2019, doi: 10.3390/s19235320.
- Link: https://pubmed.ncbi.nlm.nih.gov/31816886/
- Opened: PubMed (abstract only).
- Says: 79 Dexcom G6 traces. Error = blood-to-tissue delay + calibration error (second-order curve over wear time) + autoregressive noise.
- Use: Discussion. Error model for a factory-calibrated sensor, the same class as the Libre 3.

### Topic 11. Earlier analyses of MAUDE reports for diabetes devices

See also [48].

**[63]** J. S. Krouwer, "Adverse Event Causes From 2022 for Four Continuous Glucose Monitors," *J. Diabetes Sci. Technol.*, vol. 19, no. 1, pp. 80-83, Jan. 2025, doi: 10.1177/19322968231178525.
- Link: https://pubmed.ncbi.nlm.nih.gov/37264590/
- Opened: PubMed; PMC (PMC11688675).
- Says: "281 963 CGM adverse events occurring in 2022". Causes were read from the report text for Dexcom G6, Abbott Libre, Medtronic Guardian 3 and Senseonics Eversense.
- Says (full text): 268,310 malfunctions, 13,644 injuries, 9 deaths. Inaccuracy was 99.4 % of Libre malfunction reports, 62.2 % of Dexcom G6 injury reports and 10.5 % of G6 malfunction reports.
- Says (full text): limits named by the author: duplicates, uneven brand names, maker-chosen codes, no user counts so no rates.
- Use: Introduction and Results comparison (Phase 1). The team's "Krouwer 2025".

**[64]** J. S. Krouwer, "An Analysis of 2019 FDA Adverse Events for Two Insulin Pumps and Two Continuous Glucose Monitors," *J. Diabetes Sci. Technol.*, vol. 16, no. 1, pp. 228-232, Jan. 2022, doi: 10.1177/1932296820951872.
- Link: https://pubmed.ncbi.nlm.nih.gov/32880188/
- Opened: PubMed (abstract only).
- Says: "With Dexcom CGMs, users complained about inaccurate result when most results were in the B zone." For Abbott FreeStyle the most frequent event was an allergic skin reaction.
- Use: Results comparison (Phase 1). Earlier use of sensor-against-meter pairs taken from report text.

**[65]** J. S. Krouwer, "Adverse Event Data for Years 2018 to 2020 for Diabetes Devices," *J. Diabetes Sci. Technol.*, vol. 16, no. 5, pp. 1299-1302, Sep. 2022, doi: 10.1177/19322968211011688.
- Link: https://pubmed.ncbi.nlm.nih.gov/33969718/
- Opened: PubMed (abstract only).
- Says: counts events for meters, CGMs and pumps, 2018 to 2020. The rate per test is "exceedingly small"; the rate per insulin-using patient "is of concern".
- Use: Introduction. Scale of device reports.

**[66]** J. L. Estock, R. A. Codario, S. Keddem, M. F. Zupa, K. L. Rodriguez, and M. M. DiNardo, "Insulin Pump-Associated Adverse Events: A Qualitative Descriptive Study of Clinical Consequences and Potential Root Causes," *Diabetes Technol. Ther.*, vol. 25, no. 5, pp. 343-355, May 2023, doi: 10.1089/dia.2022.0498.
- Link: https://pubmed.ncbi.nlm.nih.gov/36724310/
- Opened: PubMed (abstract only).
- Says: people read a 20 % random sample (n = 2,429) of MAUDE pump reports from the first half of 2020. 92 % named a clinical result: glucose above 400 mg/dL in 47 %, below 54 mg/dL in 24 %. "Only 50% of the AE narratives included information to support the identification of a root cause."
- Use: Methods and Discussion (Phase 1). A human-coded sample of report texts, and how often the text lacks a cause.

**[67]** S. L. Orbell, R. A. Codario, M. F. Zupa, and J. L. Estock, "Severe Insulin Pump-Related Adverse Events: Potential Root Causes and Impact of the COVID-19 Pandemic," *J. Diabetes Sci. Technol.*, vol. 19, no. 6, pp. 1614-1623, Nov. 2025, doi: 10.1177/19322968241254521.
- Link: https://pubmed.ncbi.nlm.nih.gov/38804542/
- Opened: PubMed (abstract only).
- Says: May 2019 to January 2021: 460 reports with an intensive-care admission and 288 with a death, for five pump models.
- Use: Discussion. Serious-report counts for another diabetes device.

**[68]** M. R. Brandão, J. L. B. Marques, and R. G. Ojeda, "Analysis of Adverse Events in Medical Devices for Diabetes," *J. Diabetes Sci. Technol.*, early online, Sep. 2025, doi: 10.1177/19322968251368860.
- Link: https://pubmed.ncbi.nlm.nih.gov/40948456/
- Opened: PubMed (abstract only).
- Says: MAUDE, January 2019 to December 2024: 52,601 meter reports, 1,624,664 CGM reports, 1,339,652 pump reports.
- Use: Results comparison (Phase 1). A published CGM report count for a six-year window.

### Topic 12. Sources of CGM error

First-day error: see [15] and [5]. Low-range error: see also [15], [19], [20], [25], [27].

**[69]** A. Basu et al., "Time lag of glucose from intravascular to interstitial compartment in humans," *Diabetes*, vol. 62, no. 12, pp. 4083-4087, Dec. 2013, doi: 10.2337/db13-1132.
- Link: https://pubmed.ncbi.nlm.nih.gov/24009261/
- Opened: PubMed (abstract only).
- Says: 8 healthy adults, fasted overnight. "the physiological delay of glucose transport from the vascular to the interstitial space is 5-6 min."
- Use: Methods and Discussion. The body's share of sensor lag.

**[70]** G. Schmelzeisen-Redeker, M. Schoemaker, H. Kirchsteiger, G. Freckmann, L. Heinemann, and L. Del Re, "Time Delay of CGM Sensors: Relevance, Causes, and Countermeasures," *J. Diabetes Sci. Technol.*, vol. 9, no. 5, pp. 1006-1015, Aug. 2015, doi: 10.1177/1932296815590154.
- Link: https://pubmed.ncbi.nlm.nih.gov/26243773/
- Opened: PubMed (abstract only).
- Says: prototype sensor, 37 patients. Mean delay of the raw signal 9.5 min (SD 3.7). No significant link between delay and patient history or body measures.
- Use: Methods and Discussion. Whole-sensor lag.

**[71]** M. Sinha et al., "A Comparison of Time Delay in Three Continuous Glucose Monitors for Adolescents and Adults," *J. Diabetes Sci. Technol.*, vol. 11, no. 6, pp. 1132-1137, Nov. 2017, doi: 10.1177/1932296817704443.
- Link: https://pubmed.ncbi.nlm.nih.gov/28459159/
- Opened: PubMed (abstract only).
- Says: G4 Platinum delay 5.6 ± 0.9 min in adolescents and 8.1 ± 0.7 min in adults. Delay grew with age.
- Use: Results comparison. Published lag for our sensor. Also topic 15 (age).

**[72]** S. Pleus et al., "Rate-of-Change Dependence of the Performance of Two CGM Systems During Induced Glucose Swings," *J. Diabetes Sci. Technol.*, vol. 9, no. 4, pp. 801-807, Jul. 2015, doi: 10.1177/1932296815578716.
- Link: https://pubmed.ncbi.nlm.nih.gov/25852074/
- Opened: PubMed (abstract only).
- Says: Dexcom G4, 10 subjects. MARD 12.6 % and 11.3 % when blood glucose changed by less than 1 mg/dL/min. MARD 24.9 % (falling faster than 3) and 29.6 % (rising 3 or faster).
- Use: Results comparison. Error during fast change.

**[73]** O. Moser et al., "Performance of intermittently scanned continuous glucose monitoring systems in people with type 1 diabetes: A pooled analysis," *Diabetes Obes. Metab.*, vol. 24, no. 3, pp. 522-529, Mar. 2022, doi: 10.1111/dom.14609.
- Link: https://pubmed.ncbi.nlm.nih.gov/34866293/
- Opened: PubMed (abstract only).
- Says: 12 studies, 311 participants, 15,837 pairs. Median absolute relative difference 12.7 %. Accuracy fell when glucose changed fast.
- Use: Results comparison (flash sensors).

**[74]** B. D. Mensh, N. A. Wisniewski, B. M. Neil, and D. R. Burnett, "Susceptibility of interstitial continuous glucose monitor performance to sleeping position," *J. Diabetes Sci. Technol.*, vol. 7, no. 4, pp. 863-870, Jul. 2013, doi: 10.1177/193229681300700408.
- Link: https://pubmed.ncbi.nlm.nih.gov/23911167/
- Opened: PubMed (abstract only).
- Says: healthy volunteers, four sensors each. Readings more than 25 mg/dL away from the median of the four "were strongly correlated with subjects lying on the sensors". Most were sudden drops.
- Use: Introduction and Discussion. Pressure-induced false lows.

**[75]** N. Baysal et al., "A novel method to detect pressure-induced sensor attenuations (PISA) in an artificial pancreas," *J. Diabetes Sci. Technol.*, vol. 8, no. 6, pp. 1091-1096, Nov. 2014, doi: 10.1177/1932296814553267.
- Link: https://pubmed.ncbi.nlm.nih.gov/25316716/
- Opened: PubMed (abstract only).
- Says: over 1,125 nights of home data. An expert marked about 3 % of CGM readings as pressure events. The method found 88.34 % of them.
- Use: Discussion. How common pressure lows are at night.

**[76]** E. Zijlstra, T. Heise, L. Nosek, L. Heinemann, and S. Heckermann, "Continuous glucose monitoring: quality of hypoglycaemia detection," *Diabetes Obes. Metab.*, vol. 15, no. 2, pp. 130-135, Feb. 2013, doi: 10.1111/dom.12001.
- Link: https://pubmed.ncbi.nlm.nih.gov/22974231/
- Opened: PubMed (abstract only).
- Says: Medtronic Guardian REAL-Time, 18 patients, lab reference. MARD 16.7 % overall and 38.8 % in the low range. Sensitivity for lows 37.5 %. False alert rate 53.3 %.
- Use: Results comparison. An older sensor that missed more than half of true lows.

**[77]** J. B. Welsh, S. Psavko, X. Zhang, P. Gao, and A. K. Balo, "Comparisons of Fifth-, Sixth-, and Seventh-Generation Continuous Glucose Monitoring Systems," *J. Diabetes Sci. Technol.*, vol. 18, no. 1, pp. 143-147, Jan. 2024, doi: 10.1177/19322968221099879.
- Link: https://pubmed.ncbi.nlm.nih.gov/35695305/
- Opened: PubMed; PMC (PMC10899839).
- Says: adjusted MARD 9.0 % (G5), 9.9 % (G6), 9.1 % (G7 abdomen), 8.2 % (G7 arm), against YSI.
- Says (full text, Table 2): share of true low events missed, with a 15-minute window. Alert at 70 mg/dL: G5 9 %, G6 14.0 %. Alert at 55 mg/dL: G5 32 %, G6 36.1 %.
- Use: Results comparison. Clinic missed-low rates to set beside our pair-level rates.

**[78]** B. W. Bequette, "Fault detection and safety in closed-loop artificial pancreas systems," *J. Diabetes Sci. Technol.*, vol. 8, no. 6, pp. 1204-1214, Nov. 2014, doi: 10.1177/1932296814543661.
- Link: https://pubmed.ncbi.nlm.nih.gov/25049365/
- Opened: PubMed (abstract only).
- Says: sensor signals "can suffer from a variety of anomalies, including signal dropout and pressure-induced sensor attenuations."
- Use: Introduction. Sensor faults come in several kinds.

**[79]** K. Turksoy, A. Roy, and A. Cinar, "Real-Time Model-Based Fault Detection of Continuous Glucose Sensor Measurements," *IEEE Trans. Biomed. Eng.*, vol. 64, no. 7, pp. 1437-1445, Jul. 2017, doi: 10.1109/TBME.2016.2535412.
- Link: https://pubmed.ncbi.nlm.nih.gov/26930674/
- Opened: PubMed (abstract only).
- Says: data from 51 subjects. The method found 155 of 184 sensor failures (84.2 %), on average in 2.8 min.
- Use: Discussion. Sensor faults can be caught by software; a possible defence.

### Topic 13. Clinical thresholds and dosing rules

**[80]** T. Battelino et al., "Clinical Targets for Continuous Glucose Monitoring Data Interpretation: Recommendations From the International Consensus on Time in Range," *Diabetes Care*, vol. 42, no. 8, pp. 1593-1603, Aug. 2019, doi: 10.2337/dci19-0028. Midterm ref [3].
- Link: https://pubmed.ncbi.nlm.nih.gov/31177185/
- Opened: PubMed; PMC (PMC6973648, first part).
- Says (full text): targets for adults with type 1 or type 2 diabetes:

| Measure | Target |
|---|---|
| Time in 70-180 mg/dL | over 70 % |
| Time under 70 mg/dL | under 4 % |
| Time under 54 mg/dL | under 1 % |
| Time over 180 mg/dL | under 25 % |
| Time over 250 mg/dL | under 5 % |

- Says (full text): level 1 low = 54-69 mg/dL; level 2 low = under 54. Level 1 high = 181-250; level 2 high = over 250.
- Use: Methods. Source of the 70, 54, 180 and 250 mg/dL lines.

**[81]** International Hypoglycaemia Study Group, "Glucose Concentrations of Less Than 3.0 mmol/L (54 mg/dL) Should Be Reported in Clinical Trials: A Joint Position Statement of the American Diabetes Association and the European Association for the Study of Diabetes," *Diabetes Care*, vol. 40, no. 1, pp. 155-157, Jan. 2017, doi: 10.2337/dc16-2215.
- Link: https://pubmed.ncbi.nlm.nih.gov/27872155/
- Opened: PubMed (title and citation; the record has no abstract).
- Says: the title states the position. Glucose under 54 mg/dL should be reported in trials.
- Use: Methods. Why 54 mg/dL is a threshold.

**[82]** American Diabetes Association Professional Practice Committee for Diabetes, "6. Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises: Standards of Care in Diabetes-2026," *Diabetes Care*, vol. 49, suppl. 1, pp. S132-S149, Jan. 2026, doi: 10.2337/dc26-S006.
- Link: https://pubmed.ncbi.nlm.nih.gov/41358894/
- Opened: PubMed; PMC (PMC12690178, first part).
- Says (full text, Rec. 6.15): "Glucose is the preferred treatment for the conscious individual with glucose <70 mg/dL (<3.9 mmol/L)." "Fifteen minutes after initial treatment, repeat the treatment if hypoglycemia persists."
- Says (full text): "For most individuals, 15 g carbohydrates should be ingested." People on automated insulin delivery usually need 5 to 10 g.
- Says (full text): level 1 low = under 70 and at least 54 mg/dL; level 2 = under 54; level 3 = needs help from another person. CGM targets are the same as in [80].
- Use: Methods. The current source for the 15 g rule and the recheck after 15 minutes.

**[83]** J. Walsh, R. Roberts, and T. Bailey, "Guidelines for insulin dosing in continuous subcutaneous insulin infusion using new formulas from a retrospective study of individuals with optimal glucose levels," *J. Diabetes Sci. Technol.*, vol. 4, no. 5, pp. 1174-1181, Sep. 2010, doi: 10.1177/193229681000400516.
- Link: https://pubmed.ncbi.nlm.nih.gov/20920437/
- Opened: PubMed (abstract only).
- Says: data from 1,020 pumps (396 analysed). Correction factor = 1960 / total daily dose. (The correction factor, also called insulin sensitivity factor, is defined in [85].)
- Use: Methods. A published formula for the insulin sensitivity factor.

**[84]** P. C. Davidson, H. R. Hebblewhite, R. D. Steed, and B. W. Bode, "Analysis of guidelines for basal-bolus insulin dosing: basal insulin, correction factor, and carbohydrate-to-insulin ratio," *Endocr. Pract.*, vol. 14, no. 9, pp. 1095-1101, Dec. 2008, doi: 10.4158/EP.14.9.1095.
- Link: https://pubmed.ncbi.nlm.nih.gov/19158048/
- Opened: PubMed (abstract only).
- Says: correction factor = 1,700 / total daily dose (167 well-controlled pump users).
- Use: Methods. A second formula; shows the constant differs between sources (1700 vs 1960).

**[85]** G. Aleppo et al., "A Practical Approach to Using Trend Arrows on the Dexcom G5 CGM System for the Management of Adults With Diabetes," *J. Endocr. Soc.*, vol. 1, no. 12, pp. 1445-1460, Dec. 2017, doi: 10.1210/js.2017-00388.
- Link: https://pubmed.ncbi.nlm.nih.gov/29344577/
- Opened: PubMed; PMC (PMC5760210).
- Says (full text): "CF, correction factor in mg/dL indicates glucose lowering per unit of rapid-acting insulin". Worked example: sensor 180, target 120, correction factor 30 gives 2.0 U. The paper shows no written formula; its examples match (glucose minus target) / correction factor.
- Use: Methods. A citable worked example of the correction dose rule, taken from the sensor value.

**[86]** B. P. Kovatchev, D. J. Cox, L. A. Gonder-Frederick, D. Young-Hyman, D. Schlundt, and W. Clarke, "Assessment of risk for severe hypoglycemia among adults with IDDM: validation of the low blood glucose index," *Diabetes Care*, vol. 21, no. 11, pp. 1870-1875, Nov. 1998, doi: 10.2337/diacare.21.11.1870.
- Link: https://pubmed.ncbi.nlm.nih.gov/9802735/
- Opened: PubMed (abstract only).
- Says: low blood glucose index (LBGI, a risk score from glucose readings): under 2.5 low risk, 2.5 to 5 moderate, over 5 high. Over six months these groups had 0.4, 2.3 and 5.2 severe low episodes.
- Use: Methods. Source of the LBGI we report.

### Topic 14. Language models that extract data from adverse event reports or clinical text

**[87]** N. Sohoni et al., "Automated Classification of Adverse Events After Hydrogel Perirectal Spacer Insertion for Prostate Cancer Using Large Language Models," *Urology*, vol. 209, pp. 18-24, Mar. 2026, doi: 10.1016/j.urology.2026.01.008.
- Link: https://pubmed.ncbi.nlm.nih.gov/41565161/
- Opened: PubMed (abstract only).
- Says: MAUDE reports. People labelled 97 reports first; three model families were scored against those labels. Best model (GPT-4o) scored 4.96 against 4.99 for the human reviewers. It was then run on all 1,455 reports.
- Use: Methods (Phase 1). The same design as ours: a human-labelled set, then the model on the full set.

**[88]** J. Guillot et al., "Extracting adverse event nature, severity, timelines and resulting interventions from clinical notes of patients receiving CAR-T cell therapy using large language models," *PLOS Digit. Health*, vol. 5, no. 8, Art. no. e0001426, Aug. 2026, doi: 10.1371/journal.pdig.0001426.
- Link: https://pubmed.ncbi.nlm.nih.gov/42658846/
- Opened: PubMed (abstract only).
- Says: 4,762 clinical notes, 293 patients. Checked against two human annotators on 50 notes. Accuracy 0.97 and 0.91 for the two main event grades; 0.62 to 0.76 for a pre-set list of events. "performance varied for broader AE attributes, warranting cautious use."
- Use: Methods and Discussion. Model extraction works unevenly across fields, so each field needs its own check.

**[89]** A. Luschi, P. Nesi, and E. Iadanza, "Evidence-based clinical engineering: Health information technology adverse events identification and classification with natural language processing," *Heliyon*, vol. 9, no. 11, Art. no. e21723, Nov. 2023, doi: 10.1016/j.heliyon.2023.e21723.
- Link: https://pubmed.ncbi.nlm.nih.gov/37954315/
- Opened: PubMed (abstract only).
- Says: a language model (ClinicalBERT) was tuned and tested on 3,075 MAUDE reports labelled by experts.
- Use: Methods (Phase 1). Earlier MAUDE text classification with expert labels.

**[90]** Y. Yu, Y. Shi, Y. Feng, and Y. Gong, "Enhancing MAUDE Database Utility by GPT-4 and Cause-Effect Visualization," *Stud. Health Technol. Inform.*, vol. 315, pp. 290-294, Jul. 2024, doi: 10.3233/SHTI240155.
- Link: https://pubmed.ncbi.nlm.nih.gov/39049270/
- Opened: PubMed (abstract only).
- Says: GPT-4 pipeline on 4,459 MAUDE colonoscopy reports (2011-2021). The abstract gives no accuracy number.
- Use: Methods (Phase 1), background only.

**[91]** Y. Shi and Y. Gong, "Leveraging LLMs to Understand Narratives in MAUDE Reports," *Stud. Health Technol. Inform.*, vol. 323, pp. 194-198, Apr. 2025, doi: 10.3233/SHTI250076.
- Link: https://pubmed.ncbi.nlm.nih.gov/40200473/
- Opened: PubMed (abstract only).
- Says: GPT-4-turbo on MAUDE reports about endoscopic clips. The abstract gives no accuracy number.
- Use: Methods (Phase 1), background only.

### Other sources the team already cites (verified, lower priority)

| No. | Citation | Link | Opened | What it says that we can cite | Use in the paper |
|---|---|---|---|---|---|
| [92] | N. Garg, K. Lewis, P. C. White, and S. Adhikari, "Continuous Glucose Monitor Accuracy for Diabetes Management in Hospitalized Children," *Diabetes Care*, vol. 48, no. 2, pp. 259-264, Feb. 2025, doi: 10.2337/dc24-1562. | https://pubmed.ncbi.nlm.nih.gov/39621933/ | PubMed (abstract only; publisher page gave "403 forbidden") | Dexcom G6, 2,904 pairs against hospital meters, ages 2-18. MARD 15.9 %; 96.6 % in Clarke zones A and B. guess: this is the team's "children study, Diabetes Care 2025". The abstract does not say the sensor reads high. | Introduction, only for the MARD. Do not cite it for the direction of the error. |
| [93] | U.S. Food and Drug Administration, "Class 2 Device Recall FreeStyle Libre 3 App," recall no. Z-0734-2024, Medical Device Recalls database, posted Jan. 16, 2024. Midterm ref [10]. | https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=204243 | Direct | Initiated Feb. 9, 2023. App on Android 13 could lose signal for long periods, so readings and alarms were missed. Quantity 45,173. | Introduction. A dropout-type fault. |
| [94] | M. Z. Banday, A. S. Sameer, and S. Nissar, "Pathophysiology of diabetes: An overview," *Avicenna J. Med.*, vol. 10, no. 4, pp. 174-188, Oct.-Dec. 2020, doi: 10.4103/ajm.ajm_53_20. Midterm ref [1]. | https://pubmed.ncbi.nlm.nih.gov/33437689/ | PubMed (abstract only) | Review of diabetes types and causes. | Introduction, background. |
| [95] | World Health Organization, "Diabetes," WHO health topics. Accessed: Nov. 20, 2026. Midterm ref [2]. | https://www.who.int/health-topics/diabetes | Page-reading tool | "About 830 million people worldwide have diabetes". | Introduction, background. |
| [96] | D. C. Klonoff, D. Ahn, and A. Drincic, "Continuous glucose monitoring: A review of the technology and clinical use," *Diabetes Res. Clin. Pract.*, vol. 133, pp. 178-192, Nov. 2017, doi: 10.1016/j.diabres.2017.08.005. Midterm ref [4]. | https://pubmed.ncbi.nlm.nih.gov/28965029/ | PubMed (abstract only) | Review of CGM devices and outcomes, literature to January 2017. | Introduction, background. |
| [97] | S. Vaddiraju, D. J. Burgess, I. Tomazos, F. C. Jain, and F. Papadimitrakopoulos, "Technologies for continuous glucose monitoring: current problems and future promises," *J. Diabetes Sci. Technol.*, vol. 4, no. 6, pp. 1540-1562, Nov. 2010, doi: 10.1177/193229681000400632. Midterm ref [17]. | https://pubmed.ncbi.nlm.nih.gov/21129353/ | PubMed (abstract only) | Review of sensor technology; accuracy, body reaction to the sensor, calibration. | Introduction, background. |
| [98] | American Diabetes Association Professional Practice Committee, "7. Diabetes Technology: Standards of Care in Diabetes-2025," *Diabetes Care*, vol. 48, suppl. 1, pp. S146-S166, Jan. 2025, doi: 10.2337/dc25-S007. Midterm ref [18]. | https://pubmed.ncbi.nlm.nih.gov/39651978/ | PubMed (citation only; the abstract is a standard paragraph) | Has a correction notice: *Diabetes Care* 2025;48(4):666. | Introduction. Prefer the 2026 edition [100]. |
| [99] | American Diabetes Association Professional Practice Committee, "6. Glycemic Goals and Hypoglycemia: Standards of Care in Diabetes-2025," *Diabetes Care*, vol. 48, suppl. 1, pp. S128-S145, Jan. 2025, doi: 10.2337/dc25-S006. | https://pubmed.ncbi.nlm.nih.gov/39651981/ | PubMed (citation only) | Superseded by [82]. | Use [82] instead. |
| [100] | American Diabetes Association Professional Practice Committee for Diabetes, "7. Diabetes Technology: Standards of Care in Diabetes-2026," *Diabetes Care*, vol. 49, suppl. 1, pp. S150-S165, Jan. 2026, doi: 10.2337/dc26-S007. | https://pubmed.ncbi.nlm.nih.gov/41358889/ | PubMed (citation only) | Current technology chapter. Text not read in this session. | Introduction. Read the chapter before quoting it. |
| [101] | L. DeJournett and J. DeJournett, "In Silico Testing of an Artificial-Intelligence-Based Artificial Pancreas Designed for Use in the Intensive Care Unit Setting," *J. Diabetes Sci. Technol.*, vol. 10, no. 6, pp. 1360-1371, Nov. 2016, doi: 10.1177/1932296816653967. Midterm ref [19]. | https://pubmed.ncbi.nlm.nih.gov/27301982/ | PubMed (abstract only) | Simulation of an intensive-care glucose controller with sensor error of ±10 %. Not about home CGM users. | Weak fit. [49] to [54] are closer. |
| [102] | Y. Hirota, M. Toyoda, T. Murata, and J. Miura, "Caution is required for the evaluation of the accuracy of continuous glucose monitoring devices," *J. Diabetes Investig.*, vol. 11, no. 1, p. 255, Jan. 2020, doi: 10.1111/jdi.13149. | https://pubmed.ncbi.nlm.nih.gov/31576662/ | PubMed (citation only; a letter with no abstract) | Text not read in this session. | Methods, only after reading the letter. |
| [103] | J. Hughes, J. B. Welsh, N. C. Bhavaraju, S. J. Vanslyke, and A. K. Balo, "Stability, Accuracy, and Risk Assessment of a Novel Subcutaneous Glucose Sensor," *Diabetes Technol. Ther.*, vol. 19, no. S3, pp. S21-S24, Jun. 2017, doi: 10.1089/dia.2017.0072. | https://pubmed.ncbi.nlm.nih.gov/28585874/ | PubMed (abstract only) | 50 subjects, 2,739 sensor-meter pairs, 10 days. MARD 9.6 %; median error 8.9 % on day 1 and 6.5 % on day 10. | Results comparison (meter-reference study). |
| [104] | A. Baumstark, N. Jendrike, S. Pleus, C. Liebing, C. Haug, and G. Freckmann, "Accuracy Evaluation of a New System for Self-Monitoring of Blood Glucose With Three Test Strip Lots Based on ISO 15197:2013," *J. Diabetes Sci. Technol.*, vol. 12, no. 2, pp. 539-540, Mar. 2018, doi: 10.1177/1932296817730380. | https://pubmed.ncbi.nlm.nih.gov/28931322/ | PubMed (citation only; a letter with no abstract) | Text not read. For the ISO limits use [31]. | Use [31] instead. |
| [105] | J. B. Welsh et al., "Performance of a Factory-Calibrated, Real-Time Continuous Glucose Monitoring System in Pediatric Participants With Type 1 Diabetes," *J. Diabetes Sci. Technol.*, vol. 13, no. 2, pp. 254-258, Mar. 2019, doi: 10.1177/1932296818798816. | https://pubmed.ncbi.nlm.nih.gov/30198331/ | PubMed (abstract only) | Dexcom G6, ages 6-17, 1,387 pairs against YSI. MARD 7.7 %; 96.2 % within 20/20. | Results comparison (newer sensor). |
| [106] | E. R. Faulds et al., "Continuous Glucose Monitoring in the Intensive Care Unit: A Multicenter, Retrospective Hospital-Based Analysis," *J. Diabetes Sci. Technol.*, vol. 20, no. 4, pp. 1141-1151, Jul. 2026, doi: 10.1177/19322968251343108. | https://pubmed.ncbi.nlm.nih.gov/40492314/ | PubMed (abstract only) | 169 patients, 6,783 pairs. Used models that account for repeated pairs per person to test what drives error. | Methods. Example of the person-level model. |
| [107] | B. P. Kovatchev, "Hypoglycemia Reduction and Accuracy of Continuous Glucose Monitoring," *Diabetes Technol. Ther.*, vol. 17, no. 8, pp. 530-533, Aug. 2015, doi: 10.1089/dia.2015.0144. | https://pubmed.ncbi.nlm.nih.gov/25978096/ | PubMed (citation only; a comment with no abstract) | Text not read. | Cite [49] instead. |
| [108] | A. Facchinetti, "Continuous Glucose Monitoring Sensors: Past, Present and Future Algorithmic Challenges," *Sensors*, vol. 16, no. 12, Art. no. 2093, Dec. 2016, doi: 10.3390/s16122093. | https://pubmed.ncbi.nlm.nih.gov/27941663/ | PubMed (abstract only) | Review of signal-processing methods for CGM. The team's "Facchinetti 2016". | Introduction, background. |
| [109] | B. S. Karon, J. C. Boyd, and G. G. Klee, "Glucose meter performance criteria for tight glycemic control estimated by simulation modeling," *Clin. Chem.*, vol. 56, no. 7, pp. 1091-1097, Jul. 2010, doi: 10.1373/clinchem.2010.145367. | https://pubmed.ncbi.nlm.nih.gov/20511447/ | PubMed (abstract only) | 29,920 hospital glucose values. Large dose errors were rare unless total meter error reached 20 %. Hospital insulin tables, not home use. | Discussion, optional. |
| [110] | G. Freckmann, C. Schmid, A. Baumstark, S. Pleus, M. Link, and C. Haug, "System accuracy evaluation of 43 blood glucose monitoring systems for self-monitoring of blood glucose according to DIN EN ISO 15197," *J. Diabetes Sci. Technol.*, vol. 6, no. 5, pp. 1060-1075, Sep. 2012, doi: 10.1177/193229681200600510. | https://pubmed.ncbi.nlm.nih.gov/23063032/ | PubMed (abstract only) | 27 of 34 fully tested meters (79.4 %) met the 2003 standard. Meter bias ranged from -14.1 % to +12.4 %. | Discussion (meter limits). |
| [111] | G. Freckmann, S. Pleus, M. Grady, S. Setford, and B. Levy, "Measures of Accuracy for Continuous Glucose Monitoring and Blood Glucose Monitoring Devices," *J. Diabetes Sci. Technol.*, vol. 13, no. 3, pp. 575-583, May 2019, doi: 10.1177/1932296818812062. | https://pubmed.ncbi.nlm.nih.gov/30453761/ | PubMed (abstract only) | Meters are judged by ISO 15197:2013 limits; CGMs mainly by MARD. Reviews how to compare the two. | Methods. |
| [112] | G. Freckmann et al., "Choice of Continuous Glucose Monitoring Systems May Affect Metrics: Clinically Relevant Differences in Times in Ranges," *Exp. Clin. Endocrinol. Diabetes*, vol. 130, no. 5, pp. 343-350, May 2022, doi: 10.1055/a-1347-2550. | https://pubmed.ncbi.nlm.nih.gov/33511578/ | PubMed (abstract only) | 24 people wore a FreeStyle Libre and a Dexcom G5 together. Time below range 7.7 % (Libre) vs 3.8 % (G5), p = 0.003. | Discussion. A flash sensor showing twice the time low of a Dexcom on the same people. |
| [113] | S. Pleus et al., "Clinical assessment and acceptance criteria for continuous glucose monitoring (CGM) system performance: A proposed guideline by the IFCC Working Group on CGM," *Clin. Chim. Acta*, vol. 580, Art. no. 120728, Jan. 2026, doi: 10.1016/j.cca.2025.120728. | https://pubmed.ncbi.nlm.nih.gov/41253217/ | PubMed (abstract only) | A proposed guideline for how to test CGMs, with minimum accuracy requirements. The abstract gives no numbers. | Discussion. |

## 2. The closest prior studies

| Study | What they studied | Data | Method | Main finding | What they did not do that our paper does |
|---|---|---|---|---|---|
| Kovatchev 2015 [49] | How much sensor error is safe for dosing from a CGM | 56 pump users, 2,082 dose segments | Real records replayed through a body model, at 7 error levels (MARD 3-22 %) | Lows and highs rise with error; sharp change at MARD 10 % | No named fault types (false low, hidden low, stuck at floor). Error sizes came from clinic traces, not from FDA reports. No accuracy measured on its own data. |
| Vettoretti 2016 [50] | Whether that replay method gives right answers | Simulated patients (UVA/Padova) | Replay prediction against the full simulator | Reliable only for small basal changes; biased when correction doses or carbohydrate treatments are added | Tested a method. No sensor fault study. |
| Vettoretti 2018 [51] | A full model of patient decisions with meter or CGM | 44 people (Dexcom G5 plus meter) for checking | Body model + device error models + decision rules | Simulated time in range matched real data | Published as a tool. Abstract reports no fault scenarios and uses no FDA report data. |
| Breton and Kovatchev 2010 [53] | Random meter error and glucose control | 100 simulated adults | 16,000 simulation runs at 5-20 % error | Missed lows and HbA1c worsen above 10-15 % error | Meter, not CGM. Zero-average error only; bias left out on purpose. |
| Campos-Náñez 2017 [54] | Meter bias and random error over 30 days | Simulated pump users, 43 meter models | UVA/Padova simulator | A meter that reads high lowers HbA1c and raises severe lows | Meter, not CGM. No real traces. No episode faults. |
| Shapiro 2017 [48] | Whether dosing from a CGM is safe, using MAUDE text | 25,966 Dexcom G4/G5 inaccuracy complaints, 2015 to Sept. 2016 | Text analysis of reports | 415 complaints gave both values; 55 % differed by 100 mg/dL or more; over 150 serious outcomes | One maker, 21 months. No link from report error sizes to a decision simulation. |
| Krouwer 2025 [63] | Causes of CGM reports in 2022 | 281,963 reports, four products | Problem codes, then reading and term counts in the text | Inaccuracy and "no result" lead the causes; inaccuracy was 99.4 % of Libre malfunction reports | One year. No sensor-meter error sizes. No accuracy data or simulation. |
| Mulley 2026 [9] (same dataset as ours) | Sensor readings stuck at the display limits | 948 people, four trials; REPLACE-BG CGM+BGM arm for the meter comparison | Two-week window averages, CGM against meter | CGM mean 10.0 mg/dL below the meter mean; time in range 8.3 points higher | No paired accuracy (MARD, bias by range). No fault simulation. No FDA reports. |

## 3. Recall facts check

| Our note | What the sources say, word for word | Supported? |
|---|---|---|
| The recall is from 2025 | [3]: "Date Initiated by Firm November 24, 2025". [1]: early alert "12/02/2025". | Yes for the start of the action. |
| It is an FDA Class I recall | [1]: "2/4/2026 The FDA updated this communication to inform the public that this issue has been classified as a Class I Recall." [3]: page titles "Class 1 Device Recall", posted January 14, 2026. | Yes. The class was assigned in 2026, not 2025. Write "Class I recall (action started November 2025, classified early 2026)". |
| Products: Libre 3 and Libre 3 Plus sensors | [1]: "FreeStyle Libre 3 Sensor Model Numbers: 72081-01, 72080-01" and "FreeStyle Libre 3 Plus Sensor Model Numbers: 78768-01, 78769-01". Readers and apps "are not impacted". | Yes. Small mismatch: [3] names REF 72080-01 a "FreeStyle Libre 3 Plus Sensor". |
| Sensors read too low | [1]: "incorrect glucose readings that are lower than actual blood glucose levels". [2]: "some sensors may provide incorrect low glucose readings". [3]: "carbon build up in the sensor that may result in incorrect low glucose results". | Yes. |
| About 3 million sensors | [2]: "approximately 3 million Libre 3 and Libre 3 Plus sensors in the U.S. from that production line, about half of which are estimated to have expired or been used". [3]: 1,060,723 + 1,663,241 + 258,913 + 8,062 = 2,990,939 (our sum). [1]: no number. | Yes, from Abbott and from the FDA database sum. The FDA recall page itself gives no count. Cite [2] for this number. |
| 860 serious injuries | [1]: "As of January 7, 2026, Abbott has reported 860 serious injuries, and seven deaths associated with this issue." [2] (Nov. 24, 2025): "736 severe adverse events (57 in the U.S.)". | Yes. Give the date. It is a count reported by Abbott. The earlier Abbott count was 736, worldwide, with 57 in the U.S. |
| 7 deaths | [1]: "seven deaths associated with this issue". [2]: "seven deaths (none in the U.S.) potentially associated with this issue". | Yes. Abbott adds "none in the U.S." and "potentially associated". |
| It is a "recall" | [1] title: "Glucose Monitor Sensor Recall ... Removes Certain ... Sensors". [2]: "medical device correction". | Yes in FDA's words. Abbott's own word is "correction". |

## 4. Not verified

| Source | What was tried | Status |
|---|---|---|
| N. Vaughan, "Meta-Analysis of a Decade of Studies Assessing Accuracy of Abbott FreeStyle Libre Continuous Glucose Monitor," *Diabetes Technology and Obesity Medicine*, vol. 1, no. 1, Oct. 2025, doi: 10.1177/29986702251390418. The team's "Vaughan 2025". | Publisher page https://journals.sagepub.com/doi/10.1177/29986702251390418: "403 forbidden", twice. Not in PubMed (two searches). The Crossref record for the DOI opened: it shows this title, one author (Neil Vaughan), this journal, online date Oct. 27, 2025, and the abstract. | Exists. Not opened at the publisher. Page numbers not confirmed. The abstract in Crossref says accuracy falls with "hypoglycemia, rapid glucose changes, night time, exercise, the first and last days of the 14-day sensor life". No pooled MARD seen. Open it in a browser before citing numbers. |
| FDA news release of Dec. 20, 2016 on the Dexcom G5 fingerstick-replacement approval | One fda.gov address tried: "404 not found". | Not opened. The decision is verified through [45]. Cite [45]. |
| The original FDA early alert text of Dec. 2, 2025 | Its address now redirects to the updated recall page [1]. | Original wording and its injury count not seen. |
| Abbott's "Urgent Medical Device Correction" customer letter of Nov. 24, 2025 | Not searched for as a document. | Not opened. Its instructions are quoted in [3]. |
| The paper that describes the UVA/Padova type 1 diabetes simulator (Dalla Man and co-authors, about 2014) | Two PubMed searches, no match. | Details not confirmed. Find it before citing the simulator directly. |
| Full text of ISO 15197:2013 | Catalogue page opened [30]. The standard is paid. | Limits verified only through [31]. |
| Full text of Garg 2025 [92] | Publisher page: "403 forbidden". | The claim "Dexcom reads slightly high in children" is not confirmed. |
| The team's "related work" PDF named in `docs/plans/2026-10-07_team-sources.md` | Not found in the repo folders that were read. | Its nine sources without author names were not checked. |
| Links in other repo documents (outside the files this task named) | Not opened. | In `analysis/METHODS_REVIEW.md`: Field and Welsh 2007; Bland and Altman 1995 (PDF); the Kobe study PDF; Holm; Benjamini and Hochberg; two clinicaltrials.gov PDFs; a Stanford page; a diabetesnet.com page; three unipd.it links; the DTS grid web page; an IU ScholarWorks link. In `fda-maude/OPTIONS.md`: Bala 2025; Muaz 2026 preprint; Sim and Wright 2005; three arXiv papers. |

## 5. Not found

- Topic 15, sex differences in CGM accuracy: no study was found that reports MARD or bias split by sex. Searched PubMed with "continuous glucose monitor" plus accuracy plus sex, gender, women, "sex difference", and also race, ethnicity, "skin tone", "skin pigment". No relevant result.
  - What exists instead: [44] (10.9 % of accuracy studies do not report sex; 24.8 % report ethnicity; 10.1 % analyse accuracy against any subject trait). [21] (no effect of body mass index, age, diabetes type or HbA1c; sex is not in the list). [71] (lag grows with age). [70] (lag not linked to body measures).
- A published simulation of a sensor that reads low by a fixed share, or in episodes, and its effect on dosing and alerts: none found. Nearest: [49] (error scaled up and down, no designed low fault), [54] (meter bias), [53] (bias left out).
- A peer-reviewed analysis of the 2025 Libre 3 recall: none found in PubMed.
- A study that uses a language model on MAUDE reports about CGMs: none found. [87], [90] and [91] use other devices.
- An FDA page that states "3 million sensors": none found. Only Abbott [2] says it; the FDA database numbers add up to it [3].

## 6. Numbers and claims that differ from our notes

| Our note or number | What the source says | What to do |
|---|---|---|
| `analysis/ACCURACY_V2.md` section 10: Bailey 2015 G4 (505), setting "clinic sessions", 11.3 % against the meter. Line below the table: "above the clinic G4 figure (11.3 %)". | [17]: "The MARD of CGM-SMBG for home use was 11.3%." So 11.3 % is a home-use, meter-reference number, like ours (adults, Contour Next meter, 2,992 pairs). | Fix the label. Our 13.8 % is 2.5 points above this published home-use figure. guess: same software as ours (see [17]). Other G4 figures against a meter: 12.2 % at home [19], 13.9 % in daily life [20], 14 % [16]. |
| Same file: "guess: the REPLACE-BG G4 ran Software 505". | [7] full text: "Dexcom G4 Platinum CGM System with an enhanced algorithm (Software 505)". | Remove "guess". |
| Same table: Wen 2022, "72 % of pairs read low". Team sources file: "75 %". | [24] gives both: 75 % in the abstract, 72.3 % in the results text. | Pick one and say which part of the paper it comes from. |
| Same table: Thabit 2015, 10,597 pairs. | [25]: 10,597 in the abstract; 10,647 in Table 2 (the range counts add up to 10,647). | Say "about 10,600 pairs" or cite the table. |
| Our missed lows (meter under 70, CGM 70 or more): 28 % (Set A), 31 % (Set B). | [77], clinic, lab reference, 15-minute window, alert at 70 mg/dL: G5 missed 9 %, G6 14.0 %. [15]: when YSI was 55 or less, 88 % of G4 values were 70 or less. | Not the same measure. Ours is per fingerstick, at home, with tests done when a low is suspected, and no time window. Say this where the number appears. |
| Our paired bias: -5.2 mg/dL (Set A). | [9]: CGM mean 10.0 mg/dL below the meter mean, same trial arm. | Not the same measure. [9] compares the average of all CGM readings with the average of all meter readings in two-week windows. Ours is the average of paired differences. |
| Team sources: "Kovatchev 2015. 'Replay' method ... Exactly what we do." | [49] replays records through a body model and predicts glucose after each changed decision. [50] found that kind of prediction biased once correction doses or carbohydrate treatments are added. [45]: the FDA panel judged Dexcom's own simulations "not helpful". | Describe our method as counting changed decisions on recorded traces. Cite [50] as a limit of outcome prediction. |
| Team sources: "Facchinetti 2010. CGM error = lag + drift + noise." | The three-part split is in Facchinetti 2014 [58]. Facchinetti 2010 [59] shows how hard it is to estimate sensor error. | Cite [58] for the split. |
| Team sources: "Freckmann 2023 ... Many skip sex and ethnicity." | [44]: 10.9 % of studies did not report sex. 75.2 % did not report ethnicity (24.8 % did). | Write "most report sex; three in four do not report ethnicity; one in ten analyses accuracy against subject traits". |
| Team sources: "Children study, Diabetes Care 2025. Dexcom reads slightly HIGH." | [92] abstract: MARD 15.9 %. No direction of error given. | Do not state the direction until someone reads the full text. |
| Team sources: "ISO 15197 ... Allows ~15% error." | [31]: 95 % of results within ±15 mg/dL under 100 mg/dL and within ±15 % at 100 mg/dL or more; 99 % in error grid zones A and B. | Use the exact wording. Up to 5 % of results may be further off. |
| `README.md`: Jaeb licence "No redistribution". | [8]: the terms of use on the dataset page do not contain these words. | Check the Read Me file inside the download. Do not state "no redistribution" on the strength of the web page. |
| `CLAUDE.md`: "2025 FDA Class I recall ... 860 injuries, 7 deaths". | [1], [2]: see section 3. The FDA classified it Class I on 13 January 2026 (enforcement data) and updated its public notice on 2/4/2026 (corrected 2026-11-21, see `fda-maude/results/RECALL_DATE_CHECK.md`). 860 is "serious injuries" as of January 7, 2026. Abbott: no deaths in the U.S. | Use the section 3 wording. |
| `analysis/METHODS_REVIEW.md`: Contour Next MARD "3.1 %". | [34]: 3.13 % (28 children, clinic). [33]: 5.6 % overall and 8.9 % under 70 mg/dL in a harder lab test. | Give both. "About 3 to 6 %". |
| Meter name | [7] and [10]: CONTOUR NEXT. [9] names the meter "ContourOne". | Follow the trial paper [7]. |
| Midterm plan reference details | [27]: the journal is *Therapeutic Advances in Endocrinology and Metabolism*, dated Dec. 2024 (plan: "Therapeutic Advances in Endocrinology", Oct. 2024). [41]: issue dated Nov. 2024 (plan: Oct. 2024). [31]: issue dated Nov. 2017 (plan: Aug. 2017). [98]: dated Jan. 2025 (plan: Dec. 2024). | Fix in the final reference list. |

## Added 2026-11-21 for the Methods section (NOT yet opened, written from memory, confirm before submission)

**[110]** Y. Benjamini and Y. Hochberg, "Controlling the false discovery rate: a practical and powerful approach to multiple testing," *J. R. Stat. Soc. Ser. B (Methodol.)*, vol. 57, no. 1, pp. 289-300, 1995, doi: 10.1111/j.2517-6161.1995.tb02031.x.
- Link: https://doi.org/10.1111/j.2517-6161.1995.tb02031.x
- Opened: not opened. Written from memory on 2026-11-21. Confirm volume, pages and DOI.
- Use: Methods. The correction for running many tests (680 trait comparisons).

**[111]** A. Yang et al., "Qwen2.5 Technical Report," arXiv:2412.15115, Dec. 2024.
- Link: https://arxiv.org/abs/2412.15115
- Opened: not opened. Written from memory on 2026-11-21. Confirm the author list and the arXiv number.
- Use: Methods. The language model that read the report texts (qwen2.5:7b-instruct, run with Ollama).
