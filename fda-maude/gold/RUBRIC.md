# Gold-set labelling rubric (v1)

One row per report. Labels come from careful reading of the report text only.
Terms: CGM = continuous glucose monitor (the sensor). Meter = fingerstick blood glucose meter. Pair = one sensor value and one meter value compared at the same time. HCP = healthcare professional. EMS = ambulance / paramedics.

## General rules
- Read both text parts: "Description of Event" and "Manufacturer Narrative". Some reports repeat the text twice (upper case and mixed case). Read all of it.
- Label from the text only. Do not use the FDA codes (event type, problem codes, patient problems). If the codes disagree with the text, say so in `notes`.
- Boilerplate means nothing happened. "THERE WAS NO REPORT OF DEATH, SERIOUS INJURY, OR MISTREATMENT" = no harm reported. It does not mean death. "NO INJURY OR MEDICAL INTERVENTION WAS REPORTED" and "THE CUSTOMER REPORTED NO ADVERSE EVENT" mean the same.
- Redactions: "(b)(4)" hides company data, "(b)(6)" hides private data (names, dates). Treat them as missing words. A fully redacted or empty narrative gets `unclear`, `not_stated`, null values and `confidence = low`.
- Numbers must appear in the text as digits. "ONE DAY" or "three days" gives null (say so in notes). "53.00" counts as 53. "over 600", "400+", "greater than 1,000", "in the 50s", "40-50" are bounds or ranges, not values: null, and note them. "approximately 400" is a value; note "approximate".
- Several problems in one report: label the main one, the problem the reporter complains about or the one tied to the harm. Name the others in `notes`.
- Never guess. Prefer `not_stated` or `unclear`, and lower the confidence.

## fault_type
What the device did wrong. Allowed: reads_low, reads_high, erratic, stuck, signal_loss, sensor_error_or_early_end, adhesive_or_detachment, insertion_or_skin_injury, other_device, unclear.
- reads_low: sensor minus meter is negative, or the text says the sensor read low or lower than the true value, or the sensor showed "LOW" while the meter was 70 or more.
- reads_high: sensor minus meter is positive, or the sensor read high, or showed "HIGH" while the meter was under 250. A sensor showing a normal value while the patient was treated for a hypo is reads_high with low confidence.
- erratic: wrong in both directions, jumping, fluctuating. A pair beats words: if numbers exist, use their sign. Mixed signs across pairs = erratic.
- stuck: same value for a long time, not updating (none seen in this set).
- signal_loss: readings do not reach the display: lost signal, lost communication, cannot pair, no sensor data, transmitter and app not connected, pump and phone not connected.
- sensor_error_or_early_end: error messages ("SENSOR ERROR", "REPLACE SENSOR", "CHANGE SENSOR", "SENSOR FAILED", "CHECK AGAIN IN 10 MINUTES", "BRIEF SENSOR ISSUE"), sensor ended before its wear time, failed in warm-up.
- adhesive_or_detachment: sensor fell off or did not stick.
- insertion_or_skin_injury: harm at the site: pain, bleeding, bruising, rash, infection, burn, needle or wire left in the skin.
- other_device: the problem is not the sensor's readings: reader, pump, infusion set, app, missed alarm or notification, labeling, packaging, applicator that would not insert (bent tip), transmitter battery, a report about a different product.
- unclear: "inaccurate" with no direction and no numbers (the Dexcom template "AN INACCURACY BETWEEN THE CGM AND THE BG METER OCCURRED" with no values), no device problem described at all, or low sensor readings with no meter check where the patient may truly have been low.
Examples:
- "LOWER SENSOR SCAN RESULTS OF 80 MG/DL COMPARED TO READINGS OF 400 MG/DL" -> reads_low.
- "THE PATIENT'S CGM WAS READING 141 MG/DL WHILE THE BG METER WAS READING 30 MG/DL" -> reads_high.
- "THE CGM DISPLAYED 'LOW' ... A LABORATORY GLUCOSE TEST SHOWED A BLOOD GLUCOSE VALUE OF 419 MG/DL" -> reads_low, sensor value null.
- "THE DEVICE DISPLAYED 'HIGH.' THE PATIENT THEN PERFORMED AN FSBG TEST, WHICH 500 MG/DL" with a missed-alert complaint -> other_device (the sensor agreed with the meter).

## sensor_value_mgdl and meter_value_mgdl
The first pair in the text, as whole numbers in mg/dL. Sensor = CGM, scan result, "the pump reported a BG of" (the pump shows the sensor). Meter = fingerstick, BG meter, BGM, FSBG, HCP meter, lab test, the reader's built-in Precision meter.
- Take the FIRST pair that has both numbers. With no pair, a lone sensor value or lone meter value from the event may be filled (note which).
- Order differs by maker. Abbott writes the sensor first: "SENSOR SCAN RESULTS OF X COMPARED TO READINGS OF Y ... ON A METER". Medtronic and some Dexcom texts write the meter first: "HER BGM READING WAS 1200 MG/DL, WHILE HER CGM SHOWED 220 MG/DL" -> sensor 220, meter 1200. Read the words, not the order.
- Not glucose values: insulin doses ("80 UNITS"), antibiotic doses ("CEPHALEXIN 500 MG"), ketones, A1c, lot numbers, times ("11:15PM"), counts of days or calls.
- Display words "LOW" / "HIGH" give null for the sensor; note "sensor showed LOW".
Examples: "PUMP REPORTED A BG OF 179 MG/DL. I DID A FINGER STICK ... THE ACTUAL NUMBER WAS 349 MG/DL" -> 179 / 349. "SENSOR SCAN RESULTS OF 50, 60 MG/DL COMPARED TO READINGS OF 90, 195 MG/DL" -> 50 / 90, multiple_pairs yes.

## values_unit
mg/dL, mmol/L, or null when no value. mmol/L: multiply by 18, round to a whole number, store the mg/dL number, keep the original in `evidence` and `notes`. "2.90 MMOL/L ... 11.10 MMOL/L" -> 52 and 200, unit mmol/L. Consumer text with no unit ("THE GLUCOSE IS 100 BUT THE ACTUAL BLOOD GLUCOSE IS 40") -> mg/dL, note "unit not written".

## multiple_pairs
yes when the text gives more than one sensor-vs-meter comparison, or lists several sensor values against meter values ("40 MG/DL,40 MG/DL,40 MG/DL COMPARED TO 150 MG/DL,150 MG/DL,150 MG/DL"). Several meter values with no sensor value is no. A later value after the sensor was removed is no. The first pair still goes in the value fields.

## parkes_zone_stated
A to E only when the text names the zone: "FALL INTO THE C ZONE", "FALL WITHIN THE D ZONE OF THE PARKES ERROR GRID", 'THE "D" ZONE'. If a reported zone and an investigation zone differ, take the reported one and note the other. Never work it out yourself.

## wear_day
Days the sensor had been worn when the problem happened, only when written as digits. "THE LENGTH OF SENSOR WEAR WAS 12 DAYS" -> 12. "on day 3" / "on the 3rd day" -> 3. "WEAR WAS ONE DAY" -> null, note it. "WEAR WAS UNKNOWN" -> null. Do not compute from dates ("inserted 06/02, event 06/05" -> null, note). Not wear days: hospital stays ("DISCHARGED AFTER 6 DAYS"), antibiotic courses ("FOR 10 DAYS"), expected sensor life ("SUPPOSED TO LAST 7 DAYS"), "2 DAYS EARLY", "WAIT 3 HOURS".

## fingerstick_check_done
- yes: any blood glucose check by a meter or lab is reported at any point in the event, by anyone (user, family, EMS, hospital). The Abbott template "COMPARED TO READINGS ... OBTAINED ON A METER" counts. The Dexcom title "INACCURACY BETWEEN THE CGM AND THE BG METER" counts (confidence medium when no values follow).
- no: the text says no check was done and gives no reference value: "SHE DID NOT CHECK HER CGM DEVICE OR PERFORM A BLOOD GLUCOSE MEASUREMENT".
- not_stated: otherwise, including "COMPARED TO ... A COMPETITOR BRAND DEVICE" (the device is not named as a meter) and "NO DEVICE COMPARISON WAS PROVIDED".

## user_action
What the user or a family member did to treat the glucose problem. Pick the first that applies: ate_carbs, took_insulin or skipped_insulin (the user's or caregiver's own glucose treatment; the first one in time if several) > sought_care (any HCP, clinic, urgent care, ER, EMS contact, including treatment they gave) > other (self-treated but how is not said; glucagon given by family or by the user) > none (text says no treatment or no action was taken) > not_stated.
- Advice and intent are not actions: "THE CUSTOMER WAS ADVISED TO ..." or "SHE MENTIONED THAT SHE WOULD BE GOING TO THE HOSPITAL" -> not_stated, unless the text says it was done.
- Insulin delivered or withheld by a pump because of the sensor reading counts as took_insulin or skipped_insulin; note "pump".
- Replacing the sensor, calling the company, or doing a fingerstick are not actions here.
- "NO REPORT OF ... MISTREATMENT" and "NO MEDICAL INTERVENTION WAS REPORTED" do not say what the user did -> not_stated.
Examples: "THE PATIENT'S PARENT TREATED THE PATIENT WITH LIQUID SUGAR, GRAPE JUICE, AND JELLY" -> ate_carbs (EMS came but gave no treatment). "SHE ADMINISTERED 80 UNITS OF INSULIN AS SELF-TREATMENT" -> took_insulin. "A HEALTHCARE PROFESSIONAL OBTAINED A 400 MG/DL GLUCOSE TEST AND PROVIDED AN INSULIN DRIP" -> sought_care.

## outcome_severity
How bad it was for the patient, from the text. Take the highest that applies: death > hospital_or_er > hypoglycemia or hyperglycemia_or_dka > symptoms_only > none > not_stated.
- hospital_or_er: hospital, ER or ED, urgent care, ambulance, EMS or paramedics who treated or transported the patient, "EMERGENCY HCP". EMS called but no treatment and no transport does not count.
- hypoglycemia: the text says hypoglycemia, low blood sugar or "hypo", or gives a meter or lab value under 70. hyperglycemia_or_dka: hyperglycemia, high blood sugar, DKA, ketones, or a meter or lab value over 250.
- symptoms_only: symptoms (dizzy, shaky, sweating, confusion, vomiting, tired, skin reaction, bruising, burn) with no glucose word or value and no hospital. Loss of consciousness or a seizure with no glucose word or value is still symptoms_only; note it.
- none: the text says no harm, no symptoms, asymptomatic, no injury, no adverse event, or the Abbott malfunction boilerplate. This beats a low or high meter value: an Abbott template with meter 48 and "NO REPORT OF ... SERIOUS INJURY" is none.
- not_stated: "DETAILS OF SYMPTOMS AND TREATMENT ARE UNKNOWN", or nothing about the patient. The FDA event type Injury does not make it an injury: "THE CUSTOMER EXPERIENCED A SIGNAL LOSS ... DETAILS OF SYMPTOMS AND TREATMENT ARE UNKNOWN" -> not_stated.
- An HCP who gave an IV, glucagon or a glucose shot with no hospital word: label the glucose state and note the treatment.
Examples: "THE CUSTOMER LOST CONSCIOUSNESS THREE TIMES AND WAS TAKEN BY AN AMBULANCE TO A HOSPITAL" -> hospital_or_er. "THE CUSTOMER EXPERIENCED DIZZINESS, HYPOGLYCEMIA BUT WAS ABLE TO SELF-TREAT WITH SUGAR" -> hypoglycemia. "THE CUSTOMER DID NOT REPORT SYMPTOMS" with meter 278 -> none.

## confidence
high: template or plain statement, no judgement needed. medium: one inference (direction from words, Dexcom title counted as a meter check, approximate values, main fault chosen among several, "unclear" for a template with no values). low: redacted, cut off, contradictory, or no device problem described.

## evidence and notes
evidence: an exact quote of at most 120 characters that shows the fault and the numbers; use " ... " to skip words. notes: everything odd: unit conversion, bounds and ranges, extra pairs, code-versus-text disagreements, second faults, pump or app details, numbers that are not glucose.
