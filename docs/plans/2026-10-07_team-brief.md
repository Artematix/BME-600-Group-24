# Team brief: failing glucose sensors and treatment decisions

BMEN 600, Group 24. 7 October 2026.

**Our research question:** When a glucose sensor is wrong, how wrong must it be before it changes what a patient does?

## The problem in 5 lines

- People with diabetes wear a CGM. A CGM is a small sensor under the skin that reads blood sugar every few minutes.
- They decide when to take insulin, and when to eat sugar, from the CGM number.
- In late 2025 the FDA recalled about 3 million Abbott FreeStyle Libre 3 sensors. They read too LOW.
- A false low makes a person eat sugar they do not need, or skip insulin. Blood sugar then goes very high.
- FDA count (January 2026): 860 serious injuries and 7 deaths. So we ask: how much low error is dangerous?

## What we are NOT doing

- We do NOT have data from the recalled Libre 3 sensors. No such public dataset exists.
- So we cannot say anything about the recalled sensors themselves.
- Instead we use data from OTHER, working CGM sensors:
  - a Dexcom G4 sensor, worn by US adults in a 2015-16 study;
  - an Abbott-type flash sensor, worn by patients in Chinese hospitals. A flash sensor is a CGM you scan with a reader.
- In both studies, CGM readings come paired with fingersticks. A fingerstick is a drop of blood on a test strip. We treat it as the true value.
- Step 1: we measure how far each sensor was from the truth, in real life.
- Step 2: we FAKE a sensor failure on that real data. We make the readings worse on purpose. Then we count what would change.
- Analogy: we cannot test the broken car. So we take a working car and loosen its brakes a bit at a time. We watch when it stops being safe.
- No machine learning is needed. Machine learning means a computer finding patterns on its own. We only need counting and simple statistics.

## The two phases

### Phase 1: FDA report mining (small, done first, guides Phase 2)

- MAUDE is the FDA's public database of medical device problem reports. Anyone can read it.
- We pull the reports about CGM sensors from Abbott, Dexcom and Medtronic.
- We sort each report by what went wrong (the fault type) and how bad the outcome was.
- We count by fault type, brand and month. We compare before and after the recall.
- Result: a table of real sensor fault types, with how common and how harmful each one is.
- This tells us which faults to fake in Phase 2. Caveat: reports are voluntary. Counts are warning signs, not failure rates.

### Phase 2, Part A: measure sensor accuracy by glucose range

- Match each CGM reading to a fingerstick taken within a few minutes. One match is a "pair".
- Split pairs by glucose level: low (below 70 mg/dL), normal, high. mg/dL is the unit for blood sugar.
- For each range, work out how far the sensor is from the truth, and in which direction.
- Check what makes error worse: fast-changing sugar, sensor wear day, age, sex, weight.
- Repeat on the Chinese data as a smaller check with an Abbott-type sensor.

### Phase 2, Part B: simulate failing sensors and count changed decisions

- Take the real sensor traces. Add a fake fault. Keep the fingerstick as truth.
- Apply two simple rules to the clean trace and to the faulty trace:
  - If the sensor says below 70, eat sugar.
  - If the sensor says above 200, take extra insulin.
- A "decision flips" when a rule gives a different answer on the faulty trace.
- Example: true sugar is 90. The faulty sensor says 65. The person eats sugar they did not need. That is one flip.
- Count flips per person. Repeat many times with random noise. This gives a range, not one number.
- Compare flip rates between patient groups.
- Our first run: every reading X percent too low, with X = 10, 20 and 30. This mimics the recall fault.
- More fault types follow. Phase 1 decides which. The list is open:

| Fault type | What it looks like |
|---|---|
| Constant low bias | Every reading X percent too low |
| Drift over wear days | Error grows each day the sensor is worn |
| Added noise | Readings jump around more than normal |
| Dropouts | Readings go missing for minutes or hours |
| Lag | Readings trail the true value by many minutes |
| Pressure lows | Short sharp false lows, often at night when lying on the sensor |

## The data we have

| Dataset | Who is in it | How big | Role |
|---|---|---|---|
| REPLACE-BG (US, 2015-16) | 226 adults with type 1 diabetes. Dexcom G4 sensor. 26 weeks each. | 14.8 million CGM readings. About 600,000 pairs. | Main dataset |
| Shanghai T1DM / T2DM (China, 2019-21) | 112 hospital patients: 12 type 1, 100 type 2. Abbott-type flash sensor. About 2 weeks each. | 128,000 CGM readings. 4,012 pairs. | Second, smaller check |
| OhioT1DM (US) | 12 adults with type 1 diabetes. Medtronic sensor. 8 weeks each. | Not downloaded. Needs a signed data agreement. | Optional, maybe later |

All data is public and has no names in it. The first two are downloaded and explored.

## What we already found

MARD = the sensor's average percent error. Lower is better. Under 10 percent is good.

- REPLACE-BG has enough low-sugar pairs. Shanghai does not.

| Pairs with fingerstick below 70 mg/dL | REPLACE-BG | Shanghai |
|---|---|---|
| Count | 6,600 to 20,000 (depends on pair type) | 37 |

- Both sensors read a bit too low in the normal and high range. Same direction as the recall fault.

| Sensor | How much too low, above 70 mg/dL |
|---|---|
| Dexcom G4 (REPLACE-BG) | 3 to 5 percent |
| Abbott-type flash (Shanghai) | 6 to 13 percent |

- MARD roughly doubles when sugar is low.

| Range | MARD |
|---|---|
| All readings | 10 to 14 percent |
| Below 70 mg/dL | 19 to 42 percent |

- People differ a lot. Per-person MARD in REPLACE-BG: 9 to 23 percent. Median: 13.9 percent.
- In the very low range, the error direction depends on how you group the data. It is a maths effect, not a sensor fact. We handle it with care.
- Both groups of people are narrow. No children in either.

| Dataset | Who the people are |
|---|---|
| REPLACE-BG | Median age 43. 94 percent White. Well-controlled diabetes. |
| Shanghai | Median age about 60. All Chinese. Hospital in-patients. Poorly controlled diabetes. |

- So we cannot claim results for children, non-White, or low-income groups.

## How each report section maps to this

| Report section | What goes in it | Owners |
|---|---|---|
| 1. Intro | The problem in 5 lines. Our research question. | Mahlaqa, Laaraib |
| 2. Background | What is known about CGM error. What nobody has done yet. 6 or more scholarly sources. | Mahlaqa, Laaraib |
| 3. Dataset | The data table above. Who it covers and who it does not. | Myleni, Artemy, Mirha |
| 4. Methods | Phase 1, Phase 2 Part A, Phase 2 Part B. | Myleni, Artemy, Mirha |
| 5. Preliminary Results | The findings above, with one real figure. | Everyone |
| 6. Teamwork | Who does what, and the timeline. | Everyone |

## Key dates

- Monday 13 October, 1 PM: online team meeting. We polish the full draft together.
- Friday 16 October, 11:59 PM: submit the research plan. 6 pages max, as PDF, plus the GitHub link.

## Glossary

| Term | Meaning |
|---|---|
| CGM | Continuous glucose monitor. A small sensor under the skin. Reads sugar every few minutes. |
| Fingerstick | A drop of blood on a test strip, read by a hand-held meter. We treat it as the true value. |
| mg/dL | Milligrams per decilitre. The unit for blood sugar. Normal is about 70 to 180. |
| Hypoglycaemia | Low blood sugar. Below 70 mg/dL. Below 54 is very low and dangerous. |
| Bias | Average of (sensor minus fingerstick). A minus sign means the sensor reads too low. |
| MARD | Mean absolute relative difference. The sensor's average percent error. Lower is better. |
| Error grid | A chart that sorts each pair by how dangerous the error would be for treatment. Zone A is safe. Zones D and E can cause harm. |
| MAUDE | The FDA's public database of medical device problem reports. |
| Pair | One CGM reading matched to one fingerstick taken at nearly the same time. |
| HbA1c | A blood test for average sugar over about 3 months. About 7 percent is good. Higher is worse. |
