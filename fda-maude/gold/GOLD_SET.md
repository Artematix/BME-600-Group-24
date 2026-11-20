# Gold set v1: 287 MAUDE CGM reports labelled by reading

Purpose: a hand-labelled yardstick to score the automatic pipeline (regex and language model) against.
Files in this folder: `gold_labels_v1.csv` (the labels), `gold_relabel_check_v1.csv` (blind re-check of 40), `RUBRIC.md` (the rules), `build_gold.py` (builds the CSV and checks every row), `check_agreement.py`, `summarize_gold.py`, `print_batch.py` (prints reports for reading), `human_check_keys.txt`.

## How the set was built
- Source: `fda-maude/data/sample_narratives.jsonl`. 50 malfunction and 50 death/injury reports per maker (Medtronic has only 37 serious). Received 2011 to 2026; most from 2026.
- One reviewer (an AI assistant, labeller `ai_reviewer_v1`) read every report in full, in batches of 25, and filled the form by hand. No language model pipeline and no Ollama run was used for any label.
- The rules were written down as they were decided and are in `RUBRIC.md`. Three labels were changed at the end when the outcome rule was settled (a meter value under 70 or over 250 counts as a glucose event).
- `build_gold.py` checks every row: allowed values, every number appears in the text as digits, mmol/L conversions, zone and wear day found in the text, quote found in the text. Result: 0 problems.
- Self-check: 40 random reports (seed 2026) were re-labelled from a fresh shuffled print, without opening the label files. Same reviewer, same session, a few hours later.
- Honesty note: the self-check shows the rules are applied the same way twice. It is not an independent second labeller. The human check below is the real test, and the paper must say so.

## Counts by maker and event type
| Maker | Malfunction | Injury | Death | Total |
|---|---|---|---|---|
| Abbott Libre 3 | 50 | 49 | 1 | 100 |
| Dexcom G7 | 50 | 50 | 0 | 100 |
| Medtronic Guardian | 50 | 35 | 2 | 87 |
| All | 150 | 134 | 3 | 287 |

## Label distribution (n = 287)
- fault_type: reads_low 75 (26%); signal_loss 65 (23%); other_device 43 (15%); unclear 30 (10%); reads_high 27 (9%); insertion_or_skin_injury 22 (8%); sensor_error_or_early_end 19 (7%); adhesive_or_detachment 3; erratic 3; stuck 0.
- fault_type by maker: Abbott is mostly reads_low 52 and reads_high 22. Dexcom is signal_loss 27, unclear 20 (the "inaccuracy" template with no values), reads_low 19, other_device 14. Medtronic is signal_loss 36 and other_device 27 (app alerts, pump, reader).
- outcome_severity: none 153 (53%); hospital_or_er 60 (21%); symptoms_only 31 (11%); not_stated 21 (7%); hypoglycemia 10; hyperglycemia_or_dka 9; death 3.
- outcome by event type: all 150 malfunction reports are none, not_stated or symptoms_only. Of 134 injury reports, 60 reached hospital, ER or EMS; 7 say no harm; 18 give no patient detail.
- user_action: not_stated 180 (63%); sought_care 69 (24%); ate_carbs 18; took_insulin 9; other 9; skipped_insulin 2; none 0.
- fingerstick_check_done: yes 133 (46%); not_stated 152 (53%); no 2.
- Numbers: both sensor and meter 77 (27%); meter only 23; sensor only 6; wear day 51 (18%); Parkes zone 84 (29%: C 51, D 31, B 1, E 1); mmol/L 13; multiple pairs 20.
- Both numbers by group: Abbott malfunction 49 of 50; Abbott injury 10 of 50; Dexcom injury 15 of 50; Medtronic injury 3 of 37; Dexcom and Medtronic malfunction 0.
- confidence: high 182 (63%); medium 84 (29%); low 21 (7%). Low confidence sits in the injury reports (Medtronic 9, Dexcom 6, Abbott 5) and the 3 deaths.

## Self-check agreement (40 random reports, blind re-label)
| Field | Exact agreement | Cohen's kappa |
|---|---|---|
| fault_type | 100% (40/40) | 1.00 |
| sensor_value_mgdl | 100% | - |
| meter_value_mgdl | 100% | - |
| values_unit | 100% | - |
| multiple_pairs | 100% | - |
| parkes_zone_stated | 100% | - |
| wear_day | 100% | - |
| fingerstick_check_done | 100% | 1.00 |
| user_action | 100% | 1.00 |
| outcome_severity | 100% | 1.00 |
| confidence | 100% | 1.00 |

Kappa = agreement corrected for chance (1.00 = perfect). The sample had 9 Dexcom injury, 7 Medtronic malfunction, 7 Medtronic injury, 6 Abbott malfunction, 6 Dexcom malfunction, 5 Abbott injury. guess: a second person will agree less, mainly on `unclear` vs `reads_low` for Dexcom templates, on `other_device`, and on `hospital_or_er` for EMS-only cases.

## The 10 hardest reports and why
| Key | Maker | Why it is hard |
|---|---|---|
| 25669210 | Abbott | A delivery delay of a replacement sensor, not a sensor fault; patient hospitalised. Labelled unclear. |
| 25651463 | Abbott | Death report with no device problem and redacted dates. Fault unclear, outcome death. |
| 25671583 | Dexcom | Sensor read 60 then 50, patient fainted, no meter check at all. The sensor may have been right. Unclear. |
| 25673659 | Dexcom | CGM showed 5.0 mmol/L while the partner treated a hypo with glucagon. Direction inferred, no meter value. |
| 25667096 | Dexcom | Approximate values (100 vs 500), "insufficient insulin delivery", and "no injury" boilerplate that contradicts the story. |
| 25669621 | Dexcom | Two faults in one story: intermittent low values, then the sensor failed; juice taken on false lows; ER glucose 600. |
| 10009047 | Medtronic | Pump auto-mode complaint in mmol/L with one sensor-vs-meter pair (6.8 vs 3.9). other_device vs reads_high. |
| 9632343 | Medtronic | Errors in both directions, all meter values are bounds ("over 300"). Labelled erratic with no meter value. |
| 25662255 | Dexcom | A CPAP machine report filed under Dexcom G7. Labelled other_device. |
| 25649022 | Abbott | Loss of consciousness and a seizure in a clinic, but no glucose word or value. Rule gives symptoms_only. |

## For the human check
A team member should verify these 100 reports first. They are spread over the six maker-by-event-type groups in proportion to group size, with low- and medium-confidence reports taken first.
1. Open `gold_labels_v1.csv` and `RUBRIC.md`. Print a report with `python fda-maude/gold/print_batch.py --keys <key>`.
2. Read the whole report text before looking at the row.
3. Fill a fresh row yourself (every field) on a copy named `gold_labels_v1_human.csv`, with `labeller` = your name.
4. Do not change the AI row. Disagreements are the point.
5. Numbers: copy digits exactly as written; convert mmol/L by 18 and note it.
6. If the rubric does not cover a case, label it anyway and write "rubric gap" in `notes`.
7. Keep notes short: what you saw, not what you think happened.
8. Do about 25 reports per sitting; the templates are repetitive and attention drops.
9. When done, run `python fda-maude/gold/check_agreement.py` after pointing it at your file, and report kappa per field.
10. Disagreements get resolved together with a second person; the agreed label becomes gold v2.

Keys (100), in order of priority within each group:
25669383, 25649022, 25669210, 25674004, 25669266, 25669268, 25661691, 25649048, 25661455, 25660870
25673251, 25661511, 25661741, 25652442, 25660290, 25669424, 25662508, 25661436, 25662458, 25662880
25663017, 25662869, 25662932, 25663080, 25663173, 25663187, 25663280, 25663163, 25662562, 25662348
25663289, 25663018, 25662987, 25662849, 25662899, 25663015, 25671583, 25669945, 25657296, 25673659
25668707, 25651843, 25665246, 25669230, 25667361, 25669067, 25659864, 25667095, 25669621, 25666856
25655911, 25667096, 25653709, 25662291, 25662225, 25662578, 25662339, 25662290, 25662434, 25662335
25662424, 25662579, 25662520, 25662576, 25662222, 25662292, 25662289, 25662621, 25662669, 25662617
4079409, 19972408, 2940013, 25738105, 3800813, 4020279, 8261131, 9728899, 10009047, 15585669
3742386, 2047143, 11506763, 24956682, 24164955, 24489878, 24492327, 25024167, 24717127, 25107703
24986497, 24616859, 24227573, 24464057, 25341755, 24596648, 24197544, 24113715, 24567129, 25292256
