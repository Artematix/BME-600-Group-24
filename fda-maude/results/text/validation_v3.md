# Validation of text extraction v3 against the gold set

Date: 2026-10-30. Gold: `gold_labels_v1.csv` (287 reports). Regex: `regex_sample.csv`. Model run 1: `llm_gold_v3_run1.jsonl`. Model run 2: `llm_gold_v3_run2.jsonl`.

Words: kappa = Cohen's kappa, agreement corrected for chance (1.00 = perfect, 0 = chance). Accuracy = share of reports where the system gives the gold label. "Exact among system values" = of the values the system wrote, the share equal to gold. "Exact among gold values" = of the values in the gold, the share the system got right. Presence precision / recall = how well the system knows WHEN a value exists. Invented = system wrote a value where the gold has none. Missed = gold has a value, system wrote none.

Systems: `regex` = pattern layer alone (only numbers, zone, wear day, multiple_pairs). `llm` = model alone. `combined` = regex value when the Abbott template matched, else the model; zone and wear day from the regex when it found one, else the model; judgement fields from the model.

Joined reports: 287. Model errors (no form): 0.

## 1. Headline numbers

| Field | llm kappa | combined kappa | exact (3 dp) | combined accuracy | target kappa | status |
|---|---|---|---|---|---|---|
| fault_type | 0.77 | 0.77 | 0.770 | 81% | 0.70 | met |
| outcome_severity | 0.75 | 0.75 | 0.745 | 84% | 0.75 | met |
| user_action | 0.77 | 0.77 | 0.772 | 87% | - | - |
| fingerstick_check_done | 0.74 | 0.74 | 0.741 | 87% | - | - |
| multiple_pairs | 0.39 | 0.69 | 0.690 | 95% | - | - |

Status compares the kappa rounded to 2 decimals with the target, as the target is written (kappa on 287 reports has a sampling error of about 0.03). The exact value is shown next to it.

Numbers pooled (sensor value, meter value, wear day, zone). Target: 95 % exact among system values.

| System | gold values | system values | exact | exact among system values | exact among gold values | status |
|---|---|---|---|---|---|---|
| regex | 318 | 322 | 311 | 96.6% | 97.8% | met |
| llm | 318 | 318 | 303 | 95.3% | 95.3% | met |
| combined | 318 | 319 | 307 | 96.2% | 96.5% | met |

## 2. Judgement fields: accuracy and kappa, per maker

### fault_type

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 81% | 0.77 |
| Abbott | 100 | 92% | 0.88 |
| Dexcom | 100 | 76% | 0.71 |
| Medtronic | 87 | 74% | 0.63 |

Run 2 (same version, same settings): accuracy 82%, kappa 0.78 (run 1: 81%, 0.77).

### outcome_severity

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 84% | 0.75 |
| Abbott | 100 | 82% | 0.71 |
| Dexcom | 100 | 92% | 0.87 |
| Medtronic | 87 | 78% | 0.62 |

Run 2 (same version, same settings): accuracy 84%, kappa 0.75 (run 1: 84%, 0.75).

### user_action

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 87% | 0.77 |
| Abbott | 100 | 91% | 0.84 |
| Dexcom | 100 | 89% | 0.81 |
| Medtronic | 87 | 82% | 0.57 |

Run 2 (same version, same settings): accuracy 89%, kappa 0.79 (run 1: 87%, 0.77).

### fingerstick_check_done

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 87% | 0.74 |
| Abbott | 100 | 87% | 0.72 |
| Dexcom | 100 | 80% | 0.61 |
| Medtronic | 87 | 94% | 0.83 |

Run 2 (same version, same settings): accuracy 87%, kappa 0.75 (run 1: 87%, 0.74).

### multiple_pairs

| Group | n | regex accuracy | llm accuracy | combined accuracy | regex kappa | llm kappa | combined kappa |
|---|---|---|---|---|---|---|---|
| All | 287 | 99% | 84% | 95% | 0.94 | 0.39 | 0.69 |
| Abbott | 100 | 99% | 69% | 100% | 0.96 | 0.34 | 1.00 |
| Dexcom | 100 | 100% | 88% | 88% | 1.00 | 0.29 | 0.29 |
| Medtronic | 87 | 99% | 97% | 97% | 0.00 | 0.39 | 0.39 |

Run 2 (same version, same settings): accuracy 84%, kappa 0.38 (run 1: 84%, 0.39).

## 3. Number fields

### sensor_value_mgdl

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 83 | 82 | 81 | 98% | 99% | 99% | 98% | 0 | 1 | 2 |
| regex | Abbott | 59 | 59 | 59 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Dexcom | 19 | 19 | 19 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Medtronic | 5 | 4 | 3 | 60% | 75% | 75% | 60% | 0 | 1 | 2 |
| llm | All | 83 | 82 | 77 | 93% | 94% | 99% | 98% | 4 | 1 | 2 |
| llm | Abbott | 59 | 59 | 55 | 93% | 93% | 100% | 100% | 4 | 0 | 0 |
| llm | Dexcom | 19 | 19 | 19 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| llm | Medtronic | 5 | 4 | 3 | 60% | 75% | 75% | 60% | 0 | 1 | 2 |
| combined | All | 83 | 82 | 80 | 96% | 98% | 99% | 98% | 1 | 1 | 2 |
| combined | Abbott | 59 | 59 | 58 | 98% | 98% | 100% | 100% | 1 | 0 | 0 |
| combined | Dexcom | 19 | 19 | 19 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| combined | Medtronic | 5 | 4 | 3 | 60% | 75% | 75% | 60% | 0 | 1 | 2 |

### meter_value_mgdl

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 100 | 104 | 96 | 96% | 92% | 94% | 98% | 2 | 6 | 2 |
| regex | Abbott | 60 | 60 | 59 | 98% | 98% | 98% | 98% | 0 | 1 | 1 |
| regex | Dexcom | 28 | 30 | 27 | 96% | 90% | 93% | 100% | 1 | 2 | 0 |
| regex | Medtronic | 12 | 14 | 10 | 83% | 71% | 79% | 92% | 1 | 3 | 1 |
| llm | All | 100 | 99 | 92 | 92% | 93% | 95% | 94% | 2 | 5 | 6 |
| llm | Abbott | 60 | 60 | 59 | 98% | 98% | 100% | 100% | 1 | 0 | 0 |
| llm | Dexcom | 28 | 25 | 24 | 86% | 96% | 96% | 86% | 0 | 1 | 4 |
| llm | Medtronic | 12 | 14 | 9 | 75% | 64% | 71% | 83% | 1 | 4 | 2 |
| combined | All | 100 | 99 | 93 | 93% | 94% | 95% | 94% | 1 | 5 | 6 |
| combined | Abbott | 60 | 60 | 60 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| combined | Dexcom | 28 | 25 | 24 | 86% | 96% | 96% | 86% | 0 | 1 | 4 |
| combined | Medtronic | 12 | 14 | 9 | 75% | 64% | 71% | 83% | 1 | 4 | 2 |

### wear_day

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| regex | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| regex | Dexcom | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| regex | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| llm | All | 51 | 53 | 51 | 100% | 96% | 96% | 100% | 0 | 2 | 0 |
| llm | Abbott | 51 | 51 | 51 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| llm | Dexcom | 0 | 1 | 0 | - | 0% | 0% | - | 0 | 1 | 0 |
| llm | Medtronic | 0 | 1 | 0 | - | 0% | 0% | - | 0 | 1 | 0 |
| combined | All | 51 | 54 | 51 | 100% | 94% | 94% | 100% | 0 | 3 | 0 |
| combined | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| combined | Dexcom | 0 | 1 | 0 | - | 0% | 0% | - | 0 | 1 | 0 |
| combined | Medtronic | 0 | 1 | 0 | - | 0% | 0% | - | 0 | 1 | 0 |

### parkes_zone_stated

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 84 | 84 | 83 | 99% | 99% | 100% | 100% | 1 | 0 | 0 |
| regex | Abbott | 57 | 57 | 57 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Dexcom | 27 | 27 | 26 | 96% | 96% | 100% | 100% | 1 | 0 | 0 |
| regex | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| llm | All | 84 | 84 | 83 | 99% | 99% | 100% | 100% | 1 | 0 | 0 |
| llm | Abbott | 57 | 57 | 57 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| llm | Dexcom | 27 | 27 | 26 | 96% | 96% | 100% | 100% | 1 | 0 | 0 |
| llm | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| combined | All | 84 | 84 | 83 | 99% | 99% | 100% | 100% | 1 | 0 | 0 |
| combined | Abbott | 57 | 57 | 57 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| combined | Dexcom | 27 | 27 | 26 | 96% | 96% | 100% | 100% | 1 | 0 | 0 |
| combined | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |

Combine rule check (exact among system values; multiple_pairs = accuracy): `template` (used) vs `anypair`.

| Field | template | anypair |
|---|---|---|
| sensor_value_mgdl | 98% (80/82) | 99% (81/82) |
| meter_value_mgdl | 94% (93/99) | 94% (93/99) |
| wear_day | 94% (51/54) | 94% (51/54) |
| parkes_zone_stated | 99% (83/84) | 99% (83/84) |
| multiple_pairs | 95% | 98% |

## 4. Confusion tables (model answers)

Rows = gold label. Columns = model label. Short names: low = reads_low, high = reads_high, errat = erratic, signal = signal_loss, error = sensor_error_or_early_end, adhes = adhesive_or_detachment, skin = insertion_or_skin_injury, other = other_device, uncl = unclear; sympt = symptoms_only, hypo = hypoglycemia, hyper = hyperglycemia_or_dka, hosp = hospital_or_er, n/s = not_stated.

### fault_type, all makers

| fault_type (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 59 | 7 | 3 | 0 | 2 | 0 | 0 | 1 | 3 |
| high | 4 | 21 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| errat | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 59 | 0 | 0 | 0 | 6 | 0 |
| error | 0 | 0 | 0 | 5 | 13 | 0 | 0 | 1 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 2 | 20 | 0 | 0 |
| other | 0 | 1 | 0 | 3 | 1 | 0 | 0 | 35 | 3 |
| uncl | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 7 | 20 |

### fault_type, Abbott

| Abbott (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 48 | 0 | 2 | 0 | 1 | 0 | 0 | 0 | 1 |
| high | 0 | 20 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| error | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| uncl | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |

### fault_type, Dexcom

| Dexcom (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 11 | 6 | 0 | 0 | 1 | 0 | 0 | 0 | 1 |
| high | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 0 | 0 |
| error | 0 | 0 | 0 | 4 | 2 | 0 | 0 | 1 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 2 | 6 | 0 | 0 |
| other | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 11 | 1 |
| uncl | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 2 | 17 |

### fault_type, Medtronic

| Medtronic (gold down, system across) | low | high | errat | signal | error | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|
| low | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 1 |
| high | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| errat | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 30 | 0 | 0 | 6 | 0 |
| error | 0 | 0 | 0 | 1 | 5 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| other | 0 | 0 | 0 | 2 | 1 | 0 | 22 | 2 |
| uncl | 0 | 1 | 0 | 0 | 1 | 0 | 3 | 3 |

### outcome_severity, all makers

| outcome (gold down, system across) | none | sympt | hypo | hosp | death | n/s |
|---|---|---|---|---|---|---|
| none | 152 | 0 | 1 | 0 | 0 | 0 |
| sympt | 3 | 21 | 1 | 6 | 0 | 0 |
| hypo | 0 | 0 | 4 | 5 | 0 | 1 |
| hyper | 4 | 0 | 4 | 1 | 0 | 0 |
| hosp | 1 | 1 | 2 | 56 | 0 | 0 |
| death | 0 | 0 | 0 | 0 | 3 | 0 |
| n/s | 14 | 0 | 0 | 1 | 0 | 6 |

### outcome_severity, Abbott

| Abbott (gold down, system across) | none | sympt | hypo | hosp | death | n/s |
|---|---|---|---|---|---|---|
| none | 54 | 0 | 0 | 0 | 0 | 0 |
| sympt | 2 | 14 | 1 | 4 | 0 | 0 |
| hypo | 0 | 0 | 2 | 3 | 0 | 0 |
| hyper | 1 | 0 | 0 | 1 | 0 | 0 |
| hosp | 0 | 0 | 0 | 9 | 0 | 0 |
| death | 0 | 0 | 0 | 0 | 1 | 0 |
| n/s | 5 | 0 | 0 | 1 | 0 | 2 |

### outcome_severity, Dexcom

| Dexcom (gold down, system across) | none | sympt | hypo | hosp | n/s |
|---|---|---|---|---|---|
| none | 50 | 0 | 1 | 0 | 0 |
| sympt | 0 | 6 | 0 | 2 | 0 |
| hypo | 0 | 0 | 1 | 1 | 0 |
| hyper | 0 | 0 | 1 | 0 | 0 |
| hosp | 0 | 1 | 2 | 33 | 0 |
| n/s | 0 | 0 | 0 | 0 | 2 |

### outcome_severity, Medtronic

| Medtronic (gold down, system across) | none | sympt | hypo | hosp | death | n/s |
|---|---|---|---|---|---|---|
| none | 48 | 0 | 0 | 0 | 0 | 0 |
| sympt | 1 | 1 | 0 | 0 | 0 | 0 |
| hypo | 0 | 0 | 1 | 1 | 0 | 1 |
| hyper | 3 | 0 | 3 | 0 | 0 | 0 |
| hosp | 1 | 0 | 0 | 14 | 0 | 0 |
| death | 0 | 0 | 0 | 0 | 2 | 0 |
| n/s | 9 | 0 | 0 | 0 | 0 | 2 |

### user_action, all makers

| action (gold down, system across) | none | ate_carbs | took_insulin | sought_care | other | n/s |
|---|---|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 | 0 | 0 |
| ate_carbs | 1 | 12 | 3 | 2 | 0 | 0 |
| took_insulin | 0 | 2 | 6 | 1 | 0 | 0 |
| skipped_insulin | 0 | 0 | 0 | 1 | 0 | 1 |
| sought_care | 3 | 2 | 0 | 61 | 0 | 3 |
| other | 0 | 2 | 0 | 2 | 2 | 3 |
| n/s | 7 | 1 | 0 | 2 | 0 | 170 |

## 5. Run-to-run reproducibility (same version, two runs, same settings)

| Field | identical answers |
|---|---|
| fault_type | 96.9% |
| outcome_severity | 100.0% |
| user_action | 97.6% |
| fingerstick_check_done | 98.6% |
| multiple_pairs | 96.9% |
| sensor_value_mgdl | 99.3% |
| meter_value_mgdl | 99.0% |
| wear_day | 100.0% |
| parkes_zone_stated | 100.0% |
| all fields identical | 90.6% |

Kappa against gold in each run:

| Field | llm run 1 | llm run 2 | combined run 1 | combined run 2 |
|---|---|---|---|---|
| fault_type | 0.77 | 0.78 | 0.77 | 0.78 |
| outcome_severity | 0.75 | 0.75 | 0.75 | 0.75 |
| user_action | 0.77 | 0.79 | 0.77 | 0.79 |
| fingerstick_check_done | 0.74 | 0.75 | 0.74 | 0.75 |
| multiple_pairs | 0.39 | 0.38 | 0.69 | 0.68 |

## 6. v1 vs v3

Kappa of the combined system, per field and maker. Numbers: exact among system values (combined).

| Field | Group | v1 kappa | v3 kappa | change |
|---|---|---|---|---|
| fault_type | All | 0.61 | 0.77 | +0.16 |
| fault_type | Abbott | 0.69 | 0.88 | +0.19 |
| fault_type | Dexcom | 0.52 | 0.71 | +0.19 |
| fault_type | Medtronic | 0.50 | 0.63 | +0.13 |
| outcome_severity | All | 0.56 | 0.75 | +0.19 |
| outcome_severity | Abbott | 0.42 | 0.71 | +0.29 |
| outcome_severity | Dexcom | 0.70 | 0.87 | +0.17 |
| outcome_severity | Medtronic | 0.52 | 0.62 | +0.09 |
| user_action | All | 0.40 | 0.77 | +0.38 |
| user_action | Abbott | 0.39 | 0.84 | +0.46 |
| user_action | Dexcom | 0.52 | 0.81 | +0.29 |
| user_action | Medtronic | 0.21 | 0.57 | +0.36 |
| fingerstick_check_done | All | 0.73 | 0.74 | +0.01 |
| fingerstick_check_done | Abbott | 0.74 | 0.72 | -0.03 |
| fingerstick_check_done | Dexcom | 0.60 | 0.61 | +0.01 |
| fingerstick_check_done | Medtronic | 0.74 | 0.83 | +0.09 |
| multiple_pairs | All | 0.65 | 0.69 | +0.04 |
| multiple_pairs | Abbott | 0.93 | 1.00 | +0.07 |
| multiple_pairs | Dexcom | 0.29 | 0.29 | +0.00 |
| multiple_pairs | Medtronic | 0.32 | 0.39 | +0.07 |

| Field | Group | v1 exact among system | v3 exact among system | v1 exact among gold | v3 exact among gold |
|---|---|---|---|---|---|
| sensor_value_mgdl | All | 97% (75/77) | 98% (80/82) | 90% | 96% |
| sensor_value_mgdl | Abbott | 98% (57/58) | 98% (58/59) | 97% | 98% |
| sensor_value_mgdl | Dexcom | 94% (16/17) | 100% (19/19) | 84% | 100% |
| sensor_value_mgdl | Medtronic | 100% (2/2) | 75% (3/4) | 40% | 60% |
| meter_value_mgdl | All | 97% (93/96) | 94% (93/99) | 93% | 93% |
| meter_value_mgdl | Abbott | 100% (59/59) | 100% (60/60) | 98% | 100% |
| meter_value_mgdl | Dexcom | 88% (23/26) | 96% (24/25) | 82% | 86% |
| meter_value_mgdl | Medtronic | 100% (11/11) | 64% (9/14) | 92% | 75% |
| wear_day | All | 91% (51/56) | 94% (51/54) | 100% | 100% |
| wear_day | Abbott | 98% (51/52) | 98% (51/52) | 100% | 100% |
| wear_day | Dexcom | 0% (0/2) | 0% (0/1) | - | - |
| wear_day | Medtronic | 0% (0/2) | 0% (0/1) | - | - |
| parkes_zone_stated | All | 99% (83/84) | 99% (83/84) | 99% | 99% |
| parkes_zone_stated | Abbott | 100% (57/57) | 100% (57/57) | 100% | 100% |
| parkes_zone_stated | Dexcom | 96% (26/27) | 96% (26/27) | 96% | 96% |
| parkes_zone_stated | Medtronic | - (0/0) | - (0/0) | - | - |

| Field | v1 identical | v3 identical |
|---|---|---|
| fault_type | 94.8% | 96.9% |
| outcome_severity | 95.5% | 100.0% |
| user_action | 91.3% | 97.6% |
| fingerstick_check_done | 98.6% | 98.6% |
| multiple_pairs | 98.3% | 96.9% |
| sensor_value_mgdl | 98.3% | 99.3% |
| meter_value_mgdl | 98.3% | 99.0% |
| wear_day | 99.3% | 100.0% |
| parkes_zone_stated | 100.0% | 100.0% |
| all_fields_identical | 80.5% | 90.6% |
