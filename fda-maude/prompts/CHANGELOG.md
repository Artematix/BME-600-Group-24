# Prompt change log

One entry per prompt version. The files `vN_system.txt`, `vN_user_template.txt` and `vN_schema.json` are frozen once a version has been scored. Make a new version instead of editing.

Words: schema = the fixed JSON form the model must fill. Guard = a code check that drops a model answer that is not supported by the text. Regex = the pattern layer (`scripts/extract_regex.py`). Gold set = 287 hand-labelled reports (`gold/`).

## v1 (2026-10-27). Pilot prompt

- 8 rules, 10 fields, 2 examples (one Abbott template, one Dexcom prose).
- The model converted mmol/L to mg/dL itself.
- Scored against the gold set on 2026-10-30 (`results/text/validation_v1.md`): fault_type kappa 0.61, outcome_severity 0.56, user_action 0.40, numbers 96.5 % exact.

## v2 (2026-10-30). Fixes from the pilot and the v1 validation

Changes in the prompt and schema (`v2_system.txt`, `v2_schema.json`):

| # | Change | Why (what v1 got wrong) |
|---|---|---|
| 1 | Raw number + unit fields (`sensor_value_raw`, `sensor_unit`, `meter_value_raw`, `meter_unit`). The code converts mmol/L (x 18) and fills `sensor_value_mgdl` / `meter_value_mgdl`. | v1 lost decimals when multiplying ("2.90 mmol/L" became 522). Every guard drop in the pilot was a bad conversion. |
| 2 | Regex-first rule in code: when the Abbott template matched, the numbers, multiple_pairs, zone and wear day come from the regex. Model values are kept in `llm`, final values in `final`. | The regex reads the template exactly (98 % exact on sensor values). The model missed 14 of 83 sensor values. |
| 3 | Explicit rule and Example 1: a low or high sensor number is not harm. Boilerplate with no symptom = outcome `none` and user_action `not_stated`. | v1 answered hypoglycemia for 8 Abbott templates that say "no report of serious injury", and ate_carbs where nothing was said. |
| 4 | Explicit first-pair rule: first comparison with BOTH numbers; first value of a list; read the words, not the order. | v1 took the second value of lists and mixed two pairs in one Dexcom report. |
| 5 | Stricter wear-day and zone guards in code: the digits must sit next to "DAY" (not inside a date or time); the letter must appear as "X ZONE" or "ZONE X". Prompt lists what is not a wear day (hospital stay, "2 days early", sensor life). | v1 invented 5 wear days from dates and other day counts. |
| 6 | Temperature 0 and a fixed seed (42) in every request; reported run-to-run agreement. | Parallel decoding changes about 20 % of forms even at temperature 0. The paper reports this number. |
| 7 | "Inaccuracy" alone = `unclear`. `erratic` only for both directions or jumping. Several pairs in the same direction = that direction. | 7 Dexcom "inaccuracy" templates were called erratic; 8 Abbott multi-pair templates were called erratic. |
| 8 | Connection and pairing problems (transmitter, app, phone, pump) = `signal_loss`. | 11 Medtronic pairing reports were called other_device. |
| 9 | `other_device` list widened: alerts/alarms, labeling, unauthorized product, applicator, another product. | 15 Dexcom and Medtronic device reports were called unclear. |
| 10 | Skin reaction under the patch = `insertion_or_skin_injury`, not adhesive. | 9 skin reactions were called adhesive_or_detachment. |
| 11 | Outcome ladder made explicit: hospital/EMS beats hypo/hyper; symptoms count even with boilerplate; `none` only when the text says no harm; a device-only story is `not_stated`. Loss of consciousness without a glucose word = symptoms_only (as in the rubric). | 21 symptoms_only were called none; 19 not_stated were called none; 10 hospital cases were called hypo/hyper. |
| 12 | user_action order from the rubric: own treatment > sought_care > other > none > not_stated. `none` only when the text says no action. Glucagon by family = `other`. Being taken to hospital = sought_care. | 31 sought_care were called none; 24 not_stated were called none. The gold has zero `none`. |
| 13 | fingerstick_check_done: the Dexcom "CGM and BG meter" sentence and any meter mention count as yes. | 34 yes were called not_stated. |
| 14 | Bounds ("over 600", "400+") are null. Approximate values are kept. | Gold rule; 2 bound values were copied as numbers. |
| 15 | Four examples instead of two: Abbott template, Dexcom mmol/L with meter first, Medtronic pairing with nothing about the patient, Dexcom template with symptoms. Each has a one-line "why". | Covers the four biggest error groups. |

Code changes that go with v2 (`scripts/llm_extract.py`): `--prompt-version v2`, unit conversion in code, stricter guards, `final` dict with the combined rule and a `final_source` map, `--log` file with throughput and ETA, `--num-ctx` (default 5120, the longer prompt needs it).

Scoring: `results/text/validation_v2.md`.

## v3 (2026-10-30). One focused round on the two fields that missed their targets

v2 scores (`results/text/validation_v2.md`): fault_type kappa 0.64 (target 0.70), outcome_severity 0.34 (target 0.75; v1 was 0.56), user_action 0.66, numbers 95.3 %, identical forms between two runs 89.5 %.

What went wrong in v2 and what v3 changes (schema and user template unchanged, copied from v2):

| # | Change | Why (what v2 got wrong) |
|---|---|---|
| 1 | `none` is defined by an explicit list of no-harm sentences for all three makers ("NO INJURY OR MEDICAL INTERVENTION WAS REPORTED", "THE CUSTOMER REPORTED NO ADVERSE EVENT", "NO HARM REQUIRING MEDICAL INTERVENTION", ...). `not_stated` only when no such sentence exists and nothing is said about the patient. Example 3 now carries the Medtronic no-harm sentence and answers `none`. | The v2 rule "a device-only story is not_stated" made the model answer not_stated for 98 Dexcom and Medtronic malfunction templates that end with a no-harm sentence (gold: none). This alone took outcome kappa from 0.56 to 0.34. |
| 2 | "A no-harm sentence does not cancel a stated symptom or glucose event", with two quoted examples. Contact with a healthcare professional without a hospital word stays at the symptom level. | 11 Abbott skin-reaction reports with "no report of death or permanent impairment" were called none (gold: symptoms_only); 4 Medtronic hyperglycemia reports were called none. |
| 3 | reads_low / reads_high describe the sensor's error, not the patient's glucose; "compare the numbers" spelled out. | 7 Dexcom reports where the patient had high blood sugar but the CGM showed the lower number were called reads_high. |
| 4 | Pairing, "NO COM", "CGM VALUE UNAVAILABLE" and all communication problems are signal_loss, never other_device; other_device says "not a connection". | 12 Medtronic pairing and communication reports were still called other_device. |
| 5 | "SKIN REACTION" and "ADVERSE SKIN REACTION" named in insertion_or_skin_injury; adhesive_or_detachment limited to "fell off / came off / detached / did not stick"; new Example 5 (Abbott skin-reaction template). | 18 skin reactions were called adhesive_or_detachment (v1: 9). |
| 6 | Example 1 now has two value pairs (62, 70 vs 293, 250): first of each list, multiple_pairs yes, direction from all pairs. | 6 Abbott multi-pair templates were called erratic; the model sometimes took the last value of a list. |

Settings for the v3 scoring runs: temperature 0, seed 42, 8 parallel requests, num_ctx 6144 (same as the planned full run, so long serious-tier texts are never cut).

Scoring: `results/text/validation_v3.md`. Per the plan, v3 is the last prompt round before the full run; the result is reported whether or not the targets are met.
