# BMEN 600 Project

## Team Name
Group 24

## Team Members Present
- Myleni Zatorre de Oliveira
- Mahlaqa Mubasher
- Laaraib Anwar
- Mirha Kanwal
- Artemy Gavrilov

## Candidate Project 1

### Biomedical Problem
Continuous glucose monitors (CGMs) are used by people with diabetes to make real-time insulin and carbohydrate decisions. In late 2025 the FDA issued a Class I recall of roughly 3 million Abbott FreeStyle Libre 3 and Libre 3 Plus sensors that reported glucose values lower than the patient's true blood glucose. The FDA has linked the defect to 860 serious injuries and 7 deaths. Falsely low readings cause patients to eat unnecessary carbohydrates or skip insulin, leading to uncontrolled hyperglycemia and diabetic ketoacidosis. The reliability of CGM readings, especially in the low glucose range where treatment decisions are most sensitive, is therefore a direct patient safety issue.

### Possible Research Question
How accurate are CGM readings relative to reference blood glucose across glucose ranges, and how large does a systematic low bias need to be before it changes clinically meaningful treatment decisions?

Sub-questions:
- What is the signed error (bias) and mean absolute relative difference (MARD) of CGM readings in the hypoglycemic, euglycemic, and hyperglycemic ranges?
- What fraction of paired readings fall into clinically dangerous zones of the Clarke or consensus error grid?
- Does accuracy drift with sensor wear day or with rate of glucose change?
- When a downward bias of 10, 20, or 30 percent is applied to real CGM traces, how many insulin correction or hypoglycemia treatment decisions flip?

### Dataset
Candidate public datasets with CGM readings paired with reference glucose:
- OhioT1DM (12 patients with type 1 diabetes, 8 weeks each, 5-minute CGM, fingerstick glucose, insulin, carbohydrate, and exercise logs; requires a data use agreement)
- Shanghai T1DM and T2DM datasets (CGM with laboratory and fingerstick glucose; openly available on Figshare)
- Jaeb Center for Health Research public study datasets (CGM alongside laboratory reference glucose from clinical trials)

### Biggest Uncertainty
Whether the public datasets contain enough paired CGM and reference readings in the hypoglycemic range to draw conclusions about accuracy where it matters most. Hypoglycemia is rare in daily-life data, so the low-range sample size may be small. We also need to confirm data access timelines for datasets that require an agreement.

## Candidate Project 2

### Biomedical Problem
Same clinical motivation as Project 1, viewed from the post-market surveillance side. The FDA's MAUDE database holds the individual adverse event reports behind the recall, but the pattern of who was harmed, how, and when the signal became visible has not been characterized in a way that is accessible to patients or clinicians.

### Possible Research Question
What do publicly reported adverse events for CGM sensors reveal about the demographics, mechanism of harm, and timeline of the FreeStyle Libre 3 recall, and was the safety signal detectable in reporting data before the recall was issued?

Sub-questions:
- Age and sex distribution of Libre 3 injury and death reports compared to other CGM brands
- Categorization of event narratives by outcome (unnecessary hypoglycemia treatment, skipped insulin, DKA, hospitalization)
- Monthly report volume for "reading too low" events before and after the November 2025 recall
- Comparison of problem types across Abbott, Dexcom, and Medtronic sensors over the same period

### Dataset
- FDA MAUDE (Manufacturer and User Facility Device Experience) database, accessed through the openFDA device event API. Reports include event type, device brand, manufacturer, patient age and sex, outcome flags, product problem codes, dates, and free-text narratives. The CGM product code (QLG) contains roughly 148,000 reports.
- Health Canada Medical Device Incidents database as a possible Canadian comparison.

### Biggest Uncertainty
MAUDE is a voluntary, manufacturer-filed reporting system. Report counts reflect reporting behaviour rather than true incidence, duplicates are common, and patient age and sex are missing in many records. We are uncertain how much of the analysis will be limited by missing fields and by the lag between events and their appearance in the database.

## Current Decision
We are currently leaning toward: Candidate Project 1, CGM reading reliability with a bias simulation, with elements of Project 2 as a supporting analysis if time allows.

Because: it uses openly available datasets with a true reference measurement, so we can make defensible accuracy claims rather than descriptive ones. The analysis (error metrics, error grids, and a simple bias simulation on real traces) does not require machine learning, is achievable in the course timeline, and connects directly to the mechanism of harm behind the recall. The MAUDE analysis is a natural complement that grounds the simulation in what actually happened to patients.
