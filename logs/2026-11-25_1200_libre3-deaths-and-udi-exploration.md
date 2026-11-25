# Libre 3 death narratives, UDI pulls, symptom-by-direction figures

Date: 2026-11-25 12:00
Who: agent (Claude Code, side chat)
Asked by: Artemy

## Asked
- What is in MAUDE reports, how reports spread by year, whether the free text is usable for the paper.
- Pull the Libre 3 / 3 Plus death reports with text; then injury reports for four UDIs; make figures of clinical codes vs reading direction.

## Done
- `fda-maude/results/libre3_deaths/`: all 98 Libre 3 / 3 Plus death reports from openFDA (2026-11-23) as CSV, XLSX, markdown and raw JSON; `LIBRE3_DEATHS_with_narrative.docx` holds the 43 with a usable story (hand-picked; `hand_tier` column in the CSV).
- `fda-maude/results/udi_reports/`: all 15,619 reports for UDIs 00357599844011, 00357599818005, 00357599843014, 00357599819002 (coded fields; `tier` column: 301 injury, 79 effect-coded malfunction, 15,239 template malfunction); the 301 injury reports with full text (`injury_reports_4udis_with_text.*`, with `sensor_mgdl` / `meter_mgdl` extracted for 28).
- Figures in `udi_reports/`: `fig_injury_clinical_codes.png`, `fig_symptom_vs_reading.png`, `fig_symptom_terms_by_direction.png`, `fig_symptoms_low_readings_death_vs_injury.png`, `fig_symptoms_low_readings_by_model.png`.

## Findings (preliminary, small n)
- Deaths: 98 reports; ~36 say only "patient deceased"; ~43 describe a fault-to-harm chain, nearly all the same: sensor shows 40 to 150 while blood glucose is 300 to over 1000, person treats the false low with sugar or withholds insulin, DKA or cardiac arrest follows. 25 of 623 CGM deaths overall state a number pair; median 86 % low.
- UDI is on 9 of 98 deaths and ~33 % of Libre 3 injuries; lot on 7 deaths. UDI is a product code, not a lot, so recall lots cannot be traced from MAUDE.
- Symptom follows coded direction: Low Readings -> hyperglycemia on 57 %, hypoglycemia 10 %; High Readings -> hypoglycemia 57 %, hyperglycemia 7 % (157 injury reports). DKA only under Low Readings. Loss of consciousness ~15 % in both.
- Deaths vs injuries, Low Readings: DKA 27 % vs 4 %; cardiac arrest and brain injury only in deaths.
- Libre 3 vs 3 Plus: no visible difference in symptom mix.

## Decisions
- openFDA API with limit 100 (no key on this machine; limit 1000 needs a key). Bulk files not re-pulled.
- Direction taken from Abbott's product problem code, not from text, because only 28 of 301 injury texts state a pair.

## Open questions / next
- Extend symptom-by-direction to all 18,707 Libre 3 injuries and to Dexcom G6/G7 (brand name + problem code; no UDI needed). ~190 + ~270 API calls with text.
- Add outcome code (Required Intervention / Hospitalization / Life Threatening) by direction; device problem by quarter around the recall.
- Run the repo's pattern layer over the 15,239 template malfunction rows for error size per UDI.
- Paper: one qualitative paragraph from the death narratives, one figure (symptom by direction) linking reports to the simulation.
