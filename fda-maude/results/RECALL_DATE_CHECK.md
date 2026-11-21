# Recall date check: when did the Libre 3 recall become Class I?
Checked 2026-11-21. Every web page below was opened that day. Class I = the most serious FDA recall class.
## Answer
- FDA classified the recall as Class I on **13 January 2026**.
- **4 February 2026** is the day FDA updated its public notice to announce the class. It is not the classification date.
- Safe sentence: "Abbott began the action on 24 November 2025. The FDA classified it as a Class I recall on 13 January 2026 and announced this publicly on 4 February 2026."
- Limit: the 13 January date is only in FDA's enforcement data [B]. Pages [A] and [C] do not show it. The FDA Enforcement Report website itself was not opened. If unsure, write "classified in January 2026".

| Date | What it means | Where it is written |
|---|---|---|
| 2026-01-13 | FDA classified the recall as Class I | [B], field `center_classification_date`. FDA's definition [E]: "The date that FDA classified the recalled products as Class I, II, or III" |
| 2026-01-14 | FDA posted the record in its public recall database | [A] "Date Posted". [B], field `event_date_posted` |
| 2026-01-21 | The recall appeared in FDA's weekly Enforcement Report (list of classified recalls) | [B], field `report_date` |
| 2026-02-04 | FDA updated its notice. The notice began as an "Early Alert" on 12/02/2025 | [C]: "2/4/2026 The FDA updated this communication to inform the public that this issue has been classified as a Class I Recall." |

## Our two files
- `recalls_cgm.csv` (event 98049, four recall numbers): `date_classified` 20260113 and `date_posted` 2026-01-14. Both come from openFDA (FDA's public data service). Both match the live data today.
- `docs/paper/REFERENCES.md`: 2026-02-04 comes from the update line on the FDA notice [C]. Line 792 says "Class I was assigned on 2/4/2026". That is wrong. Line 745 ("classified early 2026") is fine.

## Two other facts
- 860 serious injuries and 7 deaths: holds. [C] says: "As of January 7, 2026, Abbott has reported 860 serious injuries, and seven deaths associated with this issue."
- "Correction, not a removal": holds only for Abbott's own words. Abbott [D] says "medical device correction". Its letter, quoted in [A], is titled "Urgent Medical Device Correction". But the FDA notice [C] says the recall "involves removing certain devices from where they are used or sold", and its title says "Removes". Safe wording: "recall", or "Abbott called it a medical device correction".

## Sources
- [A] FDA recall database, Z-1020-2026: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfres/res.cfm?id=217499
- [B] openFDA: https://api.fda.gov/device/enforcement.json?search=event_id:98049 and https://api.fda.gov/device/recall.json?search=res_event_number:98049
- [C] FDA notice: https://www.fda.gov/medical-devices/medical-device-recalls-and-early-alerts/glucose-monitor-sensor-recall-abbott-diabetes-care-removes-certain-freestyle-libre-3-and-freestyle
- [D] Abbott notice, FDA copy: https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/abbott-initiates-medical-device-correction-certain-freestyle-librer-3-and-freestyle-libre-3-plus
- [E] FDA definitions: https://www.fda.gov/safety/enforcement-reports/enforcement-report-information-and-definitions
