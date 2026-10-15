---
title: "How Wrong Must a Glucose Sensor Be Before It Changes a Treatment Decision? Measuring Continuous Glucose Monitor Error by Glucose Range and Simulating a Low-Reading Fault"
subtitle: "BMEN 600 Midterm Research Plan, Group 24"
author:
  - Myleni Zatorre de Oliveira
  - Mahlaqa Mubasher
  - Laaraib Anwar
  - Mirha Kanwal
  - Artemy Gavrilov
date: "Department of Biomedical Engineering, University of Calgary. BMEN 600, Dr. Farago and Dr. Park. October 16, 2026. Repository: https://github.com/Artematix/BME-600-Group-24"
---

# I. Introduction and Motivation

Diabetes is a chronic metabolic condition in which the body cannot regulate blood glucose because insulin is absent or ineffective [1]. Treatment aims to keep glucose within a target range, usually 70 to 180 mg/dL, because both hypoglycemia (below 70 mg/dL) and hyperglycemia (above 180 mg/dL) carry immediate and long-term harm [2]. Continuous glucose monitors (CGMs) are small sensors worn under the skin that report glucose every 1 to 15 minutes, and current guidelines permit people with diabetes to dose insulin directly from a CGM reading without a confirmatory fingerstick [3], [6]. About 38 million people in the United States have diabetes, and those who use insulin make several dosing or carbohydrate decisions a day on the basis of these readings.

A CGM measures glucose in the interstitial fluid rather than in blood, so its readings can differ from the true value for physiological and technical reasons [4], [5]. When they do, the direction of the error determines the harm. In November 2025 Abbott initiated a Class I recall of 2,990,939 FreeStyle Libre 3 and Libre 3 Plus sensors that read lower than true glucose; by January 2026 Abbott had reported 860 serious injuries and seven deaths to the FDA, caused by patients eating carbohydrates they did not need or skipping insulin they did [8]. Published accuracy figures for CGMs, however, are almost always reported as a single unsigned average over the whole glucose range, which cannot say how often a systematically low reading would move a patient across a treatment threshold.

This project asks one question: across the hypoglycemic, target and hyperglycemic ranges, how large and in which direction is CGM error relative to paired fingerstick glucose in adults with type 1 and type 2 diabetes, and how often would an error of a given size change a threshold-based treatment decision? We answer it with two public datasets that pair CGM readings with fingerstick values, REPLACE-BG (Dexcom G4, 226 adults with type 1 diabetes, 475,502 pairs) and ShanghaiT1DM/T2DM (FreeStyle Libre H, 112 adults, 4,012 pairs), computing signed bias, mean absolute relative difference and error-grid zones by glucose range, and then injecting a recall-scale downward bias into the real CGM traces to count how many readings cross the 70 and 200 mg/dL decision thresholds. The contribution is a range-specific, direction-aware error profile for two sensor generations, and a quantified estimate of how many decisions a Libre-type low bias would change, which neither pooled accuracy statistics nor the FDA recall notices provide.

# II. Background and Research Gap

CGM accuracy is conventionally summarized by the mean absolute relative difference (MARD), the average percentage gap between sensor and reference glucose. A 2024 systematic review of 22 ambulatory studies with 2,294 participants reported a pooled MARD of 9.4 percent, but found that accuracy was inadequate in hypoglycemia, where no device met the ISO 15197 criterion of 95 percent of readings within 15 mg/dL [9]. MARD is an unsigned, pooled statistic: it hides the direction of error and treats a 15 percent miss at 60 mg/dL the same as one at 250 mg/dL. Error grids were developed to address this by scoring each reading pair according to the clinical consequence of acting on the sensor value [10]. Both approaches are standard in regulatory review [27], but neither is routinely reported by glucose range together with the sign of the error, and the review's hypoglycemia finding rests on a small share of all paired readings.

The direction of error is not random for the Libre family. When the FDA approved the FreeStyle Libre Pro in 2016, its summary of safety and effectiveness recorded a negative bias against the laboratory comparator and required labelling that the device may inaccurately indicate hypoglycemia [12]. In a study of 742 adults with type 2 diabetes and 25,579 paired readings, the Libre read below the fingerstick reference in 75 percent of pairs, with a mean bias of minus 23 percent at 3 a.m. and worse accuracy in patients with complications [13]. Rapid changes in glucose widen the gap because interstitial glucose lags blood glucose by several minutes [4], [5], and sensor compression, adhesive failure and interfering substances add further error [3], [11]. Against that background, the three Abbott recalls since 2023 show the two directions of bias producing two different harms: a July 2024 recall of 8,174 Libre 3 sensors for falsely high readings, which risk insulin overdose and missed hypoglycemia [17], and the November 2025 recall for falsely low readings, which risk unnecessary carbohydrate intake and withheld insulin [8], [18]–[21]. (A February 2023 correction concerned signal loss in the Libre 3 app, not the sensor [16].) A pooled MARD would not have distinguished these faults; a signed, range-specific analysis would.

How much error is too much has been studied mainly by simulation. Kovatchev and colleagues replayed real CGM, pump and meter records from 56 pump users with added sensor error and concluded that insulin dosing from a CGM is safe below roughly 10 percent MARD [7]; Campos-Náñez and colleagues used a virtual-patient simulator to show that reduced meter accuracy increases severe hypoglycemia [14]. Both studies injected symmetric random error into simulated or replayed physiology. The only recent analysis of the REPLACE-BG dataset compared CGM and meter summary metrics over two-week windows and found that the CGM underestimated mean glucose and overestimated time in range, attributing the offset to interstitial lag; it also showed that most participants have readings capped at the sensor's 40 and 400 mg/dL limits, which must be handled before any accuracy analysis [15]. No published study has injected a one-directional, recall-scale low bias into real paired data and counted how many treatment decisions change.

The gap this project addresses is therefore specific. Existing accuracy studies report pooled, unsigned error; the Libre's low bias is documented but has not been translated into decision-level consequences; and the simulation literature has modelled symmetric error in virtual patients rather than directional error in real traces. We will quantify signed CGM error by glucose range in two paired CGM-fingerstick datasets from two manufacturers, and use a bias-injection simulation on the real traces to find the level of low bias at which threshold-based decisions begin to change. FDA adverse event reports will be used to describe the real-world failure modes behind the recall and to anchor the magnitude of the bias we simulate.

# III. Dataset and Responsible Use

Three public data sources are used. Their characteristics are summarized in Table 1.

Table 1. Data sources.

| | REPLACE-BG [22], [23] | ShanghaiT1DM / T2DM [24], [25] | FDA recalls and MAUDE [16]–[21], [30] |
|---|---|---|---|
| Access (date) | Jaeb Center public dataset 546, terms of use (Oct 7, 2026) | Figshare, CC BY 4.0 (Oct 7, 2026) | Public, openFDA API (Oct 12, 2026) |
| Population | 226 adults, type 1, 14 US sites, 2015–16, all pump users, HbA1c ≤ 9.0% | 112 adults, two Shanghai hospitals, 2019–21: 12 type 1 (10 LADA), 100 type 2 | Reports by manufacturers, clinicians, patients; not a population |
| Device; reference | Dexcom G4 Platinum, 5 min; Contour Next meter (plus Precision Xtra, 203 pts) | FreeStyle Libre H, 15 min; capillary meter, brand not stated | 4 UDI identifiers in the 2025 recall |
| Size; matched pairs | 13.7 M CGM readings in window; 580,577 meter readings; 475,502 pairs (±5 min), 120,202 calibration pairs | 127,982 CGM readings, 125 files; 4,012 pairs (same 15-min row, ≤ ±7.5 min) | 6 product records, 3 events; MAUDE count pending |
| Independent unit | Participant; pairs are repeated measures | Participant | Recall event; de-duplicated report |

**REPLACE-BG.** The trial randomized 226 adults 2:1 to 26 weeks of CGM with (n = 77) or without (n = 149) routine confirmatory fingersticks [22]. Both arms performed fingersticks after randomization (5.4 and 2.8 per day, including two daily G4 calibrations), but the CGM-only arm's non-calibration tests were concentrated in protocol-defined situations such as suspected hypoglycemia, so its pairs are selected toward extremes; the primary analysis uses the CGM+BGM arm and treats the CGM-only arm as a sensitivity analysis. The tables are de-identified with relative dates. Our exploration found that 7.4 percent of CGM rows predate enrolment and are excluded, that 0.5 percent of readings sit at the sensor floor or ceiling and are flagged as censored [15], and that 50 meter values outside 20 to 600 mg/dL are entry errors. The cohort is narrow: 94 percent white, 77 percent with a bachelor's degree or higher, mean HbA1c 7.0 percent, no recent severe hypoglycemia, so error estimates come from well-controlled, experienced users who rarely reach the extremes where error matters most.

**ShanghaiT1DM and ShanghaiT2DM.** Patients were recruited from a hospital registry and monitored under real-life conditions for 3 to 14 days; an intravenous insulin column shows that some periods include inpatient care [24]. Each file holds the 15-minute CGM value, capillary glucose when taken, ketones, meals and four insulin columns; summary sheets hold demographics and laboratory values, 20 to 50 percent of which are missing. The type 1 group is mostly older adults with latent autoimmune diabetes (mean age 58). Only 37 pairs have a reference below 70 mg/dL, so the dataset is a comparator for the Abbott sensor family, not a basis for low-range estimates.

**FDA records.** The recall database supports description only: the four 2026 product records are one event initiated on November 24, 2025 and posted on January 14, 2026 [18]–[21]; the 2024 and 2023 records are separate events [16], [17]. MAUDE is passive surveillance: one report is not one patient or device, reports may be duplicated or unverified, reporting rises after a public notice, and devices in use are unknown, so counts are safety signals, never incidence rates. Reports will be de-duplicated on report key and event date, follow-ups collapsed onto initial reports, and no narrative quoted with identifying details.

**Responsible use across sources.** The participant, not the pair, is the independent unit, because pairs from one person share sensor, calibration history, physiology and testing habits; estimates are computed per participant first, intervals come from a bootstrap that resamples participants, and comparisons use a mixed-effects model with a participant random intercept. Fingerstick timing is patient-chosen, so pairs over-represent moments of suspected error. The reference meter is itself permitted 5 percent of results outside ±15 mg/dL or ±15 percent under ISO 15197:2013 [26], so differences are reported as disagreement between devices. The two datasets differ at once in device, calibration, era, country, meter and diabetes type, so any difference between them is descriptive. Neither involves the recalled Libre 3, and no claim will be made about the recalled lots. No re-identification will be attempted, only aggregate results will be published, the Jaeb attribution will be reproduced, and because the Jaeb terms bind anyone who uses a redistributed copy, the repository holds code and aggregate outputs only.

# IV. Proposed Methods and Evaluation

**Variables and preprocessing.** The unit of observation is a matched pair. For each pair we keep both glucose values, timestamp, participant, treatment arm, days since sensor insertion, rate of glucose change from the surrounding CGM trace, and participant characteristics (age, sex, diabetes type, HbA1c, BMI, duration). REPLACE-BG is 30 pipe-delimited tables; Shanghai is 125 Excel files plus two summary workbooks, seven with non-standard headers matched by prefix. The cleaning in Section III is applied before pairing. In REPLACE-BG each meter reading is matched to the single nearest CGM reading of the same participant within ±5 minutes using a one-to-one time join, giving 475,502 pairs (82 percent of meter readings); a second pairing matches each calibration entry to the last CGM reading within 10 minutes before it (120,202 pairs), a harder test because the receiver is about to be corrected. In the Shanghai files the pairing is fixed by the data provider at up to ±7.5 minutes. Because interstitial glucose lags blood glucose [4], [5], we will estimate the lag by shifting fingerstick times forward by 0, 5, 10 and 15 minutes and keeping the offset that minimizes median absolute error, and report results with and without the correction.

**Metrics.** For every pair we compute the signed difference (CGM minus reference) and the absolute relative difference as a percentage of the reference, summarized as mean signed bias, MARD, the percentage of pairs within 20 percent (or 20 mg/dL below 100 mg/dL), and the share of pairs in each zone of the Clarke and consensus (Parkes) error grids [10], [28]. Summaries are produced for each dataset by glucose range (below 54, 54 to 69, 70 to 180, 181 to 250, above 250 mg/dL), and in the next phase by rate of change, sensor wear day, treatment arm and participant subgroup, with the FDA integrated-CGM agreement criteria (for example, at least 85 percent of readings below 70 mg/dL within ±15 mg/dL of the reference) as the regulatory benchmark [27]. One choice matters more than any other in the low range. If pairs are grouped by the reference value, random error in the reference selects pairs where the fingerstick happened to read low and the sensor appears to read high; grouping the same pairs by the CGM value reverses the sign. This is regression to the mean, not a property of the sensor. We therefore report bias against the average of the two readings, as in a Bland-Altman analysis, and report MARD by reference range with that caveat.

**Bias simulation.** Every CGM reading in each participant's study window is multiplied by 0.9, 0.8 and 0.7, reproducing a sensor that reads 10, 20 or 30 percent low, the failure mode of the recalled sensors [8]. Two rules are applied to the original and altered traces: treat for hypoglycemia if the reading is below 70 mg/dL, and take a correction dose if the reading is above 200 mg/dL. A decision flip is a reading at which the rule gives a different answer on the altered trace. Flips are counted per participant and expressed per person per day; the distribution across participants gives the uncertainty band. This replay approach follows Kovatchev et al. [7], with a one-directional bias matching the recall applied to real traces. The next version adds random noise drawn from the empirical residual distribution, repeats each run many times, and replaces the fixed thresholds with the pump bolus-calculator settings recorded in the HDeviceWizard table so that flips are counted at the moments participants actually dosed.

**MAUDE analysis.** Reports for FreeStyle Libre sensors will be retrieved through the openFDA API [30], de-duplicated, and coded into "reads low", "reads high", "no reading" and "other" by two coders using the scheme of Krouwer [29]. Monthly counts before and after the 2025 recall will be reported as a safety signal.

**Software and code.** Python 3.11 with pandas, numpy, matplotlib, openpyxl, xlrd and requests; scipy and statsmodels will be added for the bootstrap and mixed-effects model. `explore_raw_data.py` loads both datasets, builds the pairs, computes all metrics and writes Figure 1 and `summary_stats.json` (35 s); `bias_simulation.py` writes Figure 2 and `simulation_stats.json` (25 s). Planned: `pair_lag_correction.py`, `subgroup_analysis.py`, `maude_pull.py`.

**Main result and comparison.** The main result is signed bias and MARD by glucose range for each dataset with participant-level confidence intervals, plus the decision-flip rate at each bias level. Signed bias answers whether the sensor leans low, MARD by range is the measure used in the literature and regulatory review, and the flip rate converts error into the decision-level consequence behind the recall. Comparisons: the pooled 9.4 percent MARD of the 2024 review [9], the Libre results of Wen et al. [13], the FDA integrated-CGM thresholds [27], and Dexcom G4 versus Libre H within our data, with the caveats in Section III.

**Avoiding misleading results.** The participant is the independent unit: pairs from one participant are never split across groups, per-participant MARD is reported beside pooled values (8.9 to 23.2 percent, median 13.9), the simulation runs per participant, and the next phase adds a participant bootstrap and mixed-effects model. Datasets are never pooled; calibration and meter pairs are reported separately; results are given with and without lag correction; hypoglycemia-bin counts always accompany the estimate; meter error under ISO 15197 is stated. **Variability** is shown as 95 percent bootstrap confidence intervals on pooled estimates, medians with interquartile ranges across participants, full scatter on the error grids, and an interquartile band on the simulation curves.

# V. Preliminary Results

The exploration script was run on both datasets to establish whether they can support the research question. Table 2 summarizes what is available after cleaning and pairing, and Figure 1 shows accuracy by glucose range.

Table 2. Data available after cleaning and pairing, and headline accuracy.

| | REPLACE-BG meter pairs | REPLACE-BG calibration pairs | Shanghai T1DM + T2DM |
|------------------------------|-------------|-------------|-------------|
| Participants | 226 | 226 | 112 |
| Matched pairs | 475,502 | 120,202 | 4,012 |
| Pairs with reference below 70 mg/dL | 20,110 (4.2 percent) | 6,589 (5.5 percent) | 37 (0.9 percent) |
| Pairs with reference below 54 mg/dL | 4,166 | 1,319 | 7 |
| Overall bias, mg/dL (percent) | −4.0 (−1.3) | −5.3 (−2.8) | −15.1 (−7.4) |
| Overall MARD, percent | 10.4 | 14.1 | 13.9 |
| Parkes grid zones A / B / C+D+E, percent | 88.1 / 10.9 / 0.9 | 79.9 / 19.4 / 0.7 | 74.7 / 25.1 / 0.3 |

![Figure 1. CGM accuracy by glucose range in the three pairings. Left: pairs per range (log scale). Centre: mean relative bias, CGM minus reference, grouped by the average of the two readings. Right: MARD by reference range. Hatched bars: fewer than 50 pairs. Not lag-corrected.](../../analysis/figures/09_accuracy_by_range.png)

Three findings follow. First, REPLACE-BG has enough low-range pairs to answer the question: 20,110 meter pairs below 70 mg/dL from 226 participants, against 37 in Shanghai. This resolved the main uncertainty in our original plan and fixed REPLACE-BG as primary. Second, both sensors read low across the target and high ranges before any fault is added: the Dexcom G4 by 1 to 4 percent and the Libre H by 7 to 8 percent at every level above 70 mg/dL, with the Shanghai type 1 subgroup worse than type 2 (MARD 18.4 versus 12.9 percent). The direction matches the recall fault, so the real traces are a realistic base for the simulation. Third, error roughly doubles below 70 mg/dL (MARD 18.7 percent in the 54 to 69 band and 41.8 percent below 54 for meter pairs), which is where a wrong reading matters most.

The low-range analysis exposed a pitfall that changed our methods. Grouped by reference value, the G4 appears to read 33 percent high below 54 mg/dL; grouped by CGM value, the same pairs show it reading 23 percent low; grouped by the average of the two readings (Figure 1, centre), it reads 5 to 11 percent low. The first two are artefacts of selecting on a noisy variable. We adopted the average-based grouping for bias and added the consensus error grid, which does not depend on choosing an axis.

![Figure 2. Decision flips from a simulated low-reading sensor, REPLACE-BG, 13.7 million readings from 226 participants. Line is the median participant; band is the interquartile range. Rule L: reading below 70 mg/dL triggers carbohydrate intake. Rule H: reading above 200 mg/dL triggers a correction dose.](../../analysis/figures/12_decision_flips.png)

The first simulation (Figure 2) shows that missed insulin doses are the larger effect. A sensor reading 10 percent low hides 31.7 percent of readings truly above 200 mg/dL (median 20.7 missed high alerts per person per day) and produces false low alerts on 2.6 percent of readings (median 6.5 per day); at 20 percent bias these are 60.1 and 6.9 percent, and at 30 percent 80.9 and 13.4 percent, with a wide spread between people (IQR 40 to 67 missed highs per day at 30 percent). On the paired subset the unbiased sensor already disagrees with the meter on 10.7 percent of decisions, so the bias stacks on existing error. These counts are 5-minute readings, not actions; the pump-log version in Section IV will convert them to dosing events.

**What the data can support.** Descriptive statements about how closely CGM and fingerstick readings agree in everyday use, the direction of the disagreement, how it varies with glucose range (and, next, rate of change, wear day and subgroup), and the rate at which a low bias of a given size changes threshold-based decisions. They cannot support claims about the recalled lots or attribute differences between datasets to manufacturer or population, and subgroup results will be exploratory.

**Most important remaining uncertainty.** Whether the low-range bias survives lag correction and exclusion of calibration pairs: lag makes the sensor read low while glucose rises and high while it falls, and calibration pairs are taken just before the sensor is corrected, so both could shift the estimate in either direction. A second uncertainty is how many per-reading flips correspond to real dosing decisions, which only the pump logs can answer.

**Remaining work.** (1) Lag estimation and correction. (2) Stratification by rate of change, wear day and treatment arm. (3) Participant-level bootstrap intervals and a mixed-effects model. (4) Simulation version 2 with empirical noise, repeated runs and pump-log dosing events. (5) MAUDE pull and two-coder narrative coding. (6) Comparison with published MARD values and the FDA thresholds. (7) Final figures and report.

# VI. Teamwork and Project Plan

Artemy leads code and quantitative analysis; the other members lead writing, literature comparison, MAUDE narrative coding, figures and report assembly. Each milestone has an accountable lead and a reviewing collaborator. The team meets weekly [CONFIRM DAY] and tracks progress through GitHub issues.

Table 3. Milestones to final submission. [CONFIRM LEADS, FINAL DUE DATE AND PRESENTATION DATE.]

| Milestone | Target | Lead | Collaborator |
|--------------------------------------------------|--------|------------|--------------|
| Submit midterm research plan | Oct 16 | Myleni | All |
| Lag correction, arm split, calibration-pair exclusion; Table 2 and Figure 1 regenerated | Oct 23 | Artemy | Mirha |
| Bootstrap intervals and mixed-effects model; accuracy by rate of change and wear day | Oct 30 | Artemy | Myleni |
| Simulation version 2 (noise, repeats, pump-log dosing events) | Nov 6 | Artemy | Mahlaqa |
| MAUDE pull and coding; subgroup analysis; comparison with published values and FDA criteria | Nov 13 | Laaraib, Artemy | Mirha, Mahlaqa |
| All figures final with captions | Nov 20 | Mirha | Artemy |
| Full draft of final report | Nov 27 | Myleni | Section authors |
| Revisions, reference check, repository cleanup | [DATE] | Laaraib | All |
| Presentation and final submission | [DATE] | Mahlaqa, Myleni | All |

# Data and Code Availability

REPLACE-BG is available from the Jaeb Center (https://public.jaeb.org/dataset/546) under terms that require attribution and bind anyone who uses a redistributed copy, so the raw tables are not in our repository. ShanghaiT1DM/T2DM are on Figshare under CC BY 4.0 (doi: 10.6084/m9.figshare.c.6310860) and are cited rather than copied. FDA records are public via the openFDA API. All code is at https://github.com/Artematix/BME-600-Group-24. The README gives the research question, dataset download steps and file locations, a file map, and the two commands that reproduce Table 2 and Figures 1 and 2; `analysis/requirements.txt` lists the Python 3.11 packages; `explore_raw_data.py` and `bias_simulation.py` produce every number in Section V, also saved in `summary_stats.json` and `simulation_stats.json`; raw data is excluded from version control.

# AI-Assisted Work

The team used Claude (Anthropic) to search and summarize literature, draft and tighten prose, write and debug the loading, pairing, metric and simulation scripts, and review drafts against the rubric. [LIST ANY OTHER TOOLS USED.] Every AI-suggested reference was opened and checked against the publisher record before citation, and one that could not be located was discarded. All AI-generated code was run on the real datasets with row counts, value ranges, timestamps and pair counts inspected by hand against the documentation; the regression-to-the-mean artefact in Section V was caught in that inspection. Every number in this report traces to a named script output. AI-drafted prose was edited by the member responsible for the section, who checked its claims against the sources. The team made all decisions on the research question, matching windows, thresholds, grouping and interpretation.

# Author Contributions

[CONFIRM WITH EACH MEMBER.] All members jointly defined the research question. Myleni, Laaraib, Mahlaqa and Mirha conducted the literature review and wrote Sections I and II; Myleni and Mirha described the datasets and wrote Section III; Artemy acquired, cleaned and paired the data, wrote all code, produced the analysis and figures, and wrote Sections IV and V; Myleni and Artemy wrote Section VI and the availability and AI-use statements; Laaraib managed references in IEEE format; Artemy maintains the repository. All members contributed to interpretation and revised the final document.

# References

[1] M. Z. Banday, A. S. Sameer, and S. Nissar, "Pathophysiology of diabetes: An overview," *Avicenna J. Med.*, vol. 10, no. 4, pp. 174–188, Oct. 2020, doi: 10.4103/ajm.ajm_53_20.

[2] T. Battelino et al., "Clinical targets for continuous glucose monitoring data interpretation: Recommendations from the international consensus on time in range," *Diabetes Care*, vol. 42, no. 8, pp. 1593–1603, Aug. 2019, doi: 10.2337/dci19-0028.

[3] American Diabetes Association Professional Practice Committee, "7. Diabetes technology: Standards of Care in Diabetes—2025," *Diabetes Care*, vol. 48, Suppl. 1, pp. S146–S166, Jan. 2025, doi: 10.2337/dc25-S007.

[4] D. C. Klonoff, D. Ahn, and A. Drincic, "Continuous glucose monitoring: A review of the technology and clinical use," *Diabetes Res. Clin. Pract.*, vol. 133, pp. 178–192, Nov. 2017, doi: 10.1016/j.diabres.2017.08.005.

[5] S. Vaddiraju, D. J. Burgess, I. Tomazos, F. C. Jain, and F. Papadimitrakopoulos, "Technologies for continuous glucose monitoring: Current problems and future promises," *J. Diabetes Sci. Technol.*, vol. 4, no. 6, pp. 1540–1562, Nov. 2010, doi: 10.1177/193229681000400632.

[6] J. R. Castle and P. G. Jacobs, "Nonadjunctive use of continuous glucose monitoring for diabetes treatment decisions," *J. Diabetes Sci. Technol.*, vol. 10, no. 5, pp. 1169–1173, Sep. 2016, doi: 10.1177/1932296816631569.

[7] B. P. Kovatchev, S. D. Patek, E. A. Ortiz, and M. D. Breton, "Assessing sensor accuracy for non-adjunct use of continuous glucose monitoring," *Diabetes Technol. Ther.*, vol. 17, no. 3, pp. 177–186, Mar. 2015, doi: 10.1089/dia.2014.0272.

[8] U.S. Food and Drug Administration, "Glucose monitor sensor recall: Abbott Diabetes Care removes certain FreeStyle Libre 3 and FreeStyle Libre 3 Plus sensors," *Medical Device Recalls and Early Alerts*, Feb. 5, 2026. Accessed: Oct. 10, 2026. [Online]. Available: https://www.fda.gov/medical-devices/medical-device-recalls-and-early-alerts/glucose-monitor-sensor-recall-abbott-diabetes-care-removes-certain-freestyle-libre-3-and-freestyle

[9] V. Dávila-Ruales, L. F. Gilón, A. M. Gómez, O. M. Muñoz, M. N. Serrano, and D. C. Henao, "Evaluating the precision and reliability of real-time continuous glucose monitoring systems in ambulatory settings: A systematic review," *Ther. Adv. Endocrinol. Metab.*, vol. 15, Art. no. 20420188241304459, Dec. 2024, doi: 10.1177/20420188241304459.

[10] D. C. Klonoff et al., "The Diabetes Technology Society error grid and trend accuracy matrix for glucose monitors," *J. Diabetes Sci. Technol.*, vol. 18, no. 6, pp. 1346–1361, Nov. 2024, doi: 10.1177/19322968241275701.

[11] K. Englert et al., "Skin and adhesive issues with continuous glucose monitors: A sticky situation," *J. Diabetes Sci. Technol.*, vol. 8, no. 4, pp. 745–751, Jul. 2014, doi: 10.1177/1932296814529893.

[12] U.S. Food and Drug Administration, "Summary of safety and effectiveness data: FreeStyle Libre Pro Flash Glucose Monitoring System, PMA P150021," Sep. 23, 2016. [Online]. Available: https://www.accessdata.fda.gov/cdrh_docs/pdf15/P150021b.pdf

[13] X. Wen et al., "Diabetes complications and related comorbidities impair the accuracy of FreeStyle Libre, a flash continuous glucose monitoring system, in patients with type 2 diabetes," *Diabetes Metab. Syndr. Obes.*, vol. 15, pp. 3437–3445, Nov. 2022, doi: 10.2147/DMSO.S381565.

[14] E. Campos-Náñez, K. Fortwaengler, and M. D. Breton, "Clinical impact of blood glucose monitoring accuracy: An in-silico study," *J. Diabetes Sci. Technol.*, vol. 11, no. 6, pp. 1187–1195, Nov. 2017, doi: 10.1177/1932296817710474.

[15] J. F. Mulley, "Prevalence, duration, and clinical implications of continuous glucose monitor measurement limit capping in type 1 diabetes," *Diabet. Med.*, Art. no. e70412, 2026, doi: 10.1111/dme.70412.

[16] U.S. Food and Drug Administration, "Class 2 device recall: FreeStyle Libre 3 App (Android 13), recall no. Z-0734-2024," *CDRH Medical Device Recall Database*, posted Jan. 16, 2024. Accessed: Oct. 12, 2026. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=204243

[17] U.S. Food and Drug Administration, "Class 1 device recall: FreeStyle Libre 3 Sensor, recall no. Z-2692-2024," *CDRH Medical Device Recall Database*, posted Aug. 27, 2024. Accessed: Oct. 12, 2026. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=209214

[18] U.S. Food and Drug Administration, "Class 1 device recall: FreeStyle Libre 3 Sensor REF 72081-01, recall no. Z-1020-2026," *CDRH Medical Device Recall Database*, posted Jan. 14, 2026. Accessed: Oct. 12, 2026. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217499

[19] U.S. Food and Drug Administration, "Class 1 device recall: FreeStyle Libre 3 Plus Sensor REF 78768-01, recall no. Z-1021-2026," *CDRH Medical Device Recall Database*, posted Jan. 14, 2026. Accessed: Oct. 12, 2026. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217500

[20] U.S. Food and Drug Administration, "Class 1 device recall: FreeStyle Libre 3 Plus Sensor REF 78769-01, recall no. Z-1022-2026," *CDRH Medical Device Recall Database*, posted Jan. 14, 2026. Accessed: Oct. 12, 2026. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217774

[21] U.S. Food and Drug Administration, "Class 1 device recall: FreeStyle Libre 3 Plus Sensor REF 72080-01, recall no. Z-1023-2026," *CDRH Medical Device Recall Database*, posted Jan. 14, 2026. Accessed: Oct. 12, 2026. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217776

[22] G. Aleppo et al., "REPLACE-BG: A randomized trial comparing continuous glucose monitoring with and without routine blood glucose monitoring in adults with well-controlled type 1 diabetes," *Diabetes Care*, vol. 40, no. 4, pp. 538–545, Apr. 2017, doi: 10.2337/dc16-2482.

[23] Jaeb Center for Health Research, "REPLACE-BG public dataset," *JCHR Public Study Websites*. Accessed: Oct. 7, 2026. [Online]. Available: https://public.jaeb.org/dataset/546

[24] Q. Zhao et al., "Chinese diabetes datasets for data-driven machine learning," *Sci. Data*, vol. 10, Art. no. 35, Jan. 2023, doi: 10.1038/s41597-023-01940-7.

[25] Q. Zhao, J. Zhu, C. Wang, and W. Rao, "Diabetes datasets, ShanghaiT1DM and ShanghaiT2DM," figshare, collection, ver. 2, Jan. 4, 2023, doi: 10.6084/m9.figshare.c.6310860.

[26] *In vitro diagnostic test systems: Requirements for blood-glucose monitoring systems for self-testing in managing diabetes mellitus*, ISO 15197:2013, International Organization for Standardization, Geneva, Switzerland, 2013.

[27] Integrated continuous glucose monitoring system, 21 C.F.R. § 862.1355 (2026). Accessed: Oct. 14, 2026. [Online]. Available: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-862/subpart-B/section-862.1355

[28] A. Pfützner, D. C. Klonoff, S. Pardo, and J. L. Parkes, "Technical aspects of the Parkes error grid," *J. Diabetes Sci. Technol.*, vol. 7, no. 5, pp. 1275–1281, Sep. 2013, doi: 10.1177/193229681300700517.

[29] J. S. Krouwer, "Adverse event causes from 2022 for four continuous glucose monitors," *J. Diabetes Sci. Technol.*, vol. 19, no. 1, pp. 80–83, Jan. 2025, doi: 10.1177/19322968231178525.

[30] U.S. Food and Drug Administration, "Device adverse event overview," *openFDA*. Accessed: Oct. 12, 2026. [Online]. Available: https://open.fda.gov/apis/device/event
