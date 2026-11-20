# Options for mining the MAUDE report texts (Phase 1, text step)

Written 2026-10-26. Status: research note, nothing built yet.
Project: failing CGM sensors (CGM = continuous glucose monitor). Phase 1 mines FDA MAUDE (device problem reports).
The structured codes are already counted (`results/report/report_results.md`). This note is about the free-text stories only.

## 1. Why a text step at all

The FDA codes already give us: problem family, patient problem (hypo, hyper, seizure, DKA), outcome (hospital, death), brand, dates.
The codes cannot give us these. Only the text can:

| Wanted from text | Why Phase 2 needs it |
|---|---|
| Paired numbers: sensor value vs meter value | Real-world error size of the recalled sensors. Feeds the fault simulation. |
| Direction and size of error (too low / too high, by how much) | "Low Readings" code has no size. |
| Wear day when the problem happened | Tells if faults come early (day 1) or late (day 10+). |
| Was a fingerstick check done? Did the user act on the wrong reading? | Links sensor error to treatment decisions. |
| Mechanism detail (compression, adhesive, insertion, signal loss, sensor error message) | Fault types to simulate. |
| Severity chain beyond the outcome code (EMS called, glucagon, ICU) | Finer "how bad" scale. |

The README and the robot plan only say "LLM labelling later, human spot check". Nothing more specific. This note fills that gap.

## 2. What the real texts look like (sample of 287 reports)

Sample file: `fda-maude/data/sample_narratives.jsonl` (made by a small script, openFDA, no key).
Per brand: 50 malfunction + 50 death/injury reports, newest first, received 2024-01 to 2026-06, CGM product codes only.
Medtronic "Guardian" has only 37 serious reports under CGM codes (all years), so that group is 37.
Each report has up to two texts: "Description of Event or Problem" and "Additional Manufacturer Narrative".

| Group | n | Median length (characters) | Has 2+ mg/dL values | Matches maker template (sensor X vs meter Y) | States wear day | States Parkes zone | Mentions meter / fingerstick | Has "(b)(4)" redaction |
|---|---|---|---|---|---|---|---|---|
| Abbott Libre 3, malfunction | 50 | 744 | 84% | 80% | 94% | 98% | 96% | 0% |
| Abbott Libre 3, death/injury | 50 | 866 | 20% | 4% | 8% | 2% | 34% | 0% |
| Dexcom G7, malfunction | 50 | 375 | 0% | 0% | 0% | 6% | 24% | 100% |
| Dexcom G7, death/injury | 50 | 1,506 | 48% | 10% | 0% | 12% | 78% | 96% |
| Medtronic Guardian, malfunction | 50 | 1,438 | 0% | 0% | 0% | 0% | 0% | 0% |
| Medtronic Guardian, death/injury | 37 | 767 | 14% | 0% | 3% | 0% | 19% | 32% |
| All | 287 | - | 28% | 16% | 18% | 21% | 43% | 38% |

- Length in tokens (model word-pieces) is about characters / 4. So 100 to 400 tokens is typical, 850 at the 90th percentile.
- Parkes zone = a chart zone (A to E) that grades how dangerous a sensor-vs-meter difference is. E is worst.

How each maker writes:
- Abbott malfunction reports are one fixed template. Example: "THE CUSTOMER RECEIVED SENSOR SCAN RESULTS OF 62 MG/DL COMPARED TO READINGS OF 293 MG/DL RESPECTIVELY OBTAINED ON A METER AND THE RESULTS, WHEN PLOTTED ON A PARKES ERROR GRID, FALL INTO THE C ZONE ... THE LENGTH OF SENSOR WEAR WAS 12 DAYS. THERE WAS NO REPORT OF DEATH, SERIOUS INJURY ..."
  Several values can be listed ("40 MG/DL,40 MG/DL,40 MG/DL COMPARED TO 150 MG/DL,150 MG/DL,150 MG/DL"). Foreign reports use mmol/L (14%).
- Abbott death/injury reports are free prose (what happened, symptoms, treatment). Only 20% give both numbers.
- Dexcom starts every report with a template line ("IT WAS REPORTED THAT AN INACCURACY BETWEEN THE CGM AND THE BG METER OCCURRED") and then free prose.
  Dexcom uses "BG" for the meter value (51% of Dexcom texts), "FSBG" for fingerstick, and writes "the CGM displayed LOW" (no number) when the screen shows LOW/HIGH.
  Dexcom's manufacturer narrative is usually just "(b)(4)." (redacted). Dates are "(b)(6)" (redacted). Dexcom malfunction reports have no numbers at all.
- Medtronic malfunction reports are mostly signal-loss boilerplate. Serious reports are often patient-written ("I DID A FINGER STICK ... THE ACTUAL NUMBER WAS 349 MG/DL"). Their older template: "THE BLOOD GLUCOSE VALUE WAS 423 MG/DL AND THE SENSOR GLUCOSE VALUE WAS 68 MG/DL".

Text quirks any method must handle:
- Newest reports have NO text yet. Reports received on 2026-09-30: 48% to 70% empty. Reports from 2024 and early 2025: 0% empty. Text arrives weeks to months after the record. So mine reports at least about 3 months old, or re-pull text later.
- Text is ALL CAPS in 85% to 100% of reports. Some Abbott texts are mixed case. Harmless for an LLM. Regex must ignore case.
- "(b)(4)" = trade-secret redaction, "(b)(6)" = private-info redaction (FDA MAUDE page). 38% and 27% of the sample. Dates and sometimes whole narratives are gone.
- Keyword traps: 99% of Abbott texts contain "DEATH" because of "THERE WAS NO REPORT OF DEATH". "NO HARM" phrases in 35%. Plain keyword counting over-counts harm.
- Units: mg/dL with decimals ("80.00 MG/DL"), mmol/L (multiply by 18 to convert), display words "LOW" / "HIGH", meter extremes (947, 1055, 1200 mg/dL seen). Values of 0 or 1 are noise.
- Order differs by maker: Abbott writes sensor first, Medtronic writes meter first, Dexcom varies.
- Dexcom codes 24% of reports as "Appropriate Device Problem Term/Code Not Available". For those the text is the only source of the fault type.
- About half of all texts say "No Clinical Signs"; those reports are about the device only.

## 3. The options

a. Structured FDA codes only (no text). Already done (`report_results.md`).
- Gives: problem family, patient problem, outcome, counts by brand and month. Free, exact, reviewer-friendly.
- Misses: everything in the table in section 1. Dexcom's "code not available" reports stay unlabelled.
- Verdict: keep as the backbone. Every text result should be compared against the codes.

b. Rules / regex (fixed text patterns). Code in plain Python, runs on all 3.4 million texts in minutes.
- Gives: paired values (sensor X vs meter Y) from the maker templates, wear day, Parkes zone, units, "fingerstick" mentions, EMS/hospital words.
- In the sample a first regex caught 80% of Abbott malfunction reports and 10% of Dexcom serious reports (section 2 table). guess: 90%+ for Abbott after tuning; Dexcom and Medtronic prose needs the LLM.
- Precision is high when the template matches (the numbers are in a fixed slot). Recall is low on prose. Outcome keywords alone are unreliable (see traps).
- Prior art: Krouwer 2020 did exactly this on 2019 Dexcom reports with keyword code and found pairs in 5,436 of 7,707 reports, then plotted a Parkes grid (zones A 1.6%, B 61.2%, C 32.0%, D 5.0%, E 0.1%).
- Verdict: do it first. Free, fully explainable, and a check on the LLM.

c. Zero-shot NLI classifiers (bart-large-mnli, DeBERTa-v3 NLI). Zero-shot = the model is used without training on our data. NLI = the model judges if "this text is about X" is true.
- Gives: one fault label per text from a list we write. Cannot extract numbers, wear day, or "acted on the reading".
- Quality: on 28 public tasks bart-large-mnli averages macro-F1 0.50, deberta-v3-large-zeroshot-v2.0 about 0.68 (model card). Nothing published on MAUDE text. 512-token input limit.
- Cost: free. guess: 150k texts x 12 labels in 1 to 3 hours on the RTX 5080.
- Verdict: not as the main method. Templated boilerplate ("no report of death") will confuse it. Usable as a cheap cross-check only.

d. Sentence embeddings + clustering (BERTopic style). Embedding = turning a text into a list of numbers so similar texts sit close. Clustering = grouping those.
- Gives: groups of similar reports with top words. Humans then name the groups. Finds fault types we did not think of. No numbers, no severity.
- Tools: `nomic-embed-text` is already in Ollama. BERTopic = embeddings + UMAP + HDBSCAN + word lists (docs: bertopic.readthedocs.io).
- Cost: free. guess: 150k texts embed in under 1 hour; clustering 10 to 30 minutes. One day of work.
- Risk: templates dominate the clusters (every Abbott malfunction report lands in one group). Strip boilerplate first.
- Verdict: optional side step to discover categories before fixing the LLM label list. Not a labelling method.

e. Local small LLM with JSON output (main candidate). The model reads each text and fills a fixed form (JSON = a small structured record).
- Constrained decoding = the engine only lets the model produce output that fits our schema. Ollama `format` takes a JSON schema (docs.ollama.com); llama.cpp has GBNF grammars / `json_schema`; vLLM has `structured_outputs` (xgrammar); Outlines wraps all of them.
- Models that fit 16 GB at 4-bit: Qwen2.5-7B-Instruct (`qwen2.5:7b-instruct`, 4.7 GB), Qwen3-8B (5.2 GB, turn "thinking" off), Llama-3.1-8B, Gemma-3-12B (8.2 GB, slower), Gemma-3-4B / Phi-4-mini (faster, weaker). No published head-to-head on extraction like ours; a 1-hour bake-off on 100 hand-labelled reports decides.
- Engines on Windows: Ollama runs natively (needs NVIDIA driver 551.61+). llama.cpp runs natively. vLLM has no official Windows build; use WSL2 or Docker Model Runner (Dec 2025). Blackwell cards (RTX 50) need CUDA 12.8+ builds; the installed torch is cu128, fine.
- Speed anchors: Qwen2.5-7B single stream on an A100 with vLLM: 84 tok/s BF16, 148 tok/s AWQ (Qwen docs). Single RTX 4090 with vLLM, 16-bit, hundreds of parallel requests: 7B-class models 2,400 to 3,500 output tok/s (DatabaseMart). Ollama runs 1 request at a time unless `OLLAMA_NUM_PARALLEL` is raised; memory grows with parallel x context (Ollama FAQ).
- Our job: about 400 input + 80 output tokens per report, plus a fixed prompt of 600 to 900 tokens.

| Setup on the RTX 5080 (guess, from the anchors) | Output tok/s | Reports / hour | 150k reports | 500k reports |
|---|---|---|---|---|
| Ollama, default (1 at a time), 7B 4-bit | 80 to 120 | 3,000 to 4,500 | 35 to 50 h | 110 to 170 h |
| Ollama or llama.cpp, 8 parallel, context 2k | 400 to 800 | 15k to 35k | 4 to 10 h | 14 to 33 h |
| vLLM in WSL2, AWQ 4-bit, 64+ parallel | 1,500 to 3,000 | 60k to 130k | 1 to 3 h | 4 to 9 h |

- Constrained JSON adds some overhead (guess: 10 to 30%). Measure on 500 reports before trusting any row.
- Cost: electricity only (guess: under 5 kWh for 150k). Reproducible: pin model file hash, prompt, temperature 0, seed.
- Verdict: top pick for the prose fields. Simple to justify: "an open model read each report and filled a form; we checked 400 by hand".

f. Distillation: label 2k to 5k texts with an LLM, then train a small classifier (DeBERTa-v3-small or ModernBERT) for the rest.
- Evidence it works: Gu et al. 2023 distilled GPT-3.5 labels into PubMedBERT for adverse drug events; the student beat its teacher by 6+ F1 points. Luschi et al. 2023 fine-tuned ClinicalBERT on 3,705 expert-labelled MAUDE reports (F1 0.99 on a yes/no task). DeBERTa-v3 is more accurate on short text, ModernBERT is faster and takes long text (Antoun et al. 2025).
- Gives: labels only. Numbers and wear day still need rules or the LLM.
- Worth it only if we label more than about 1 million texts, or must re-run many times. Our target is 130k to 500k, which one LLM pass does in hours. Adds a training step a reviewer must understand.
- Verdict: skip for now. Revisit if we decide to label all 3.4 million reports.

g. Cloud LLM batch APIs. Batch = send all requests at once, get results within hours, pay half price.
Prices checked 2026-10-26 on platform.claude.com/docs/en/about-claude/pricing and developers.openai.com/api/docs/pricing. Batch = 50% off on both.
Job size: 500 input + 100 output tokens per report (fixed prompt not included; caching cuts most of that).

| Model (batch price, $ per million tokens in / out) | 150k reports | 500k reports |
|---|---|---|
| Claude Haiku 5.5 (0.05 / 0.25) | $7.50 | $25 |
| Claude Haiku 4.5 (0.50 / 2.50) | $75 | $250 |
| Claude Sonnet 5.5 (1.00 / 5.00) | $150 | $500 |
| GPT-5 nano (0.025 / 0.20) | $5 | $16 |
| GPT-5.4 nano (0.10 / 0.625) | $17 | $56 |
| GPT-5 mini (0.125 / 1.00) | $24 | $81 |
| GPT-5.4 mini (0.375 / 2.25) | $62 | $206 |

- With the fixed prompt uncached, input cost roughly triples (still under $25 for Haiku 5.5 at 150k). Standard (non-batch) price is double.
- Limits (Anthropic): 100,000 requests or 256 MB per batch, most batches done within 1 hour, hard stop at 24 hours. So 2 to 5 batches.
- Prior art: Yu et al. 2024 used GPT-4 on 4,459 MAUDE colonoscopy reports; Shi and Gong 2025 used GPT-4-turbo on endoscopic clip reports.
- Downsides: needs an API key and credits; model versions retire (reproducibility); data leaves the machine (it is public data, so acceptable).
- Verdict: runner-up. Cheapest in wall-clock. Also a good second rater for the validation step.

h. Prior work that mined MAUDE text (what they did, how they checked):
- Krouwer 2020 (J Diabetes Sci Technol 16:228): keyword/VBA extraction of CGM-meter pairs from 2019 Dexcom reports, Parkes grid. Checked by manual reading. Closest to our goal.
- Krouwer 2025 (J Diabetes Sci Technol 19:80, online 2023): 281,963 CGM events from 2022, causes judged from the text by hand, ranked per device.
- Luschi, Nesi, Iadanza 2023 (Heliyon 9:e21723): ClinicalBERT classifier on 3,705 expert-labelled MAUDE reports; 10-fold cross-validation; F1 0.99; no kappa reported.
- Bala, Sharma, Mitchell 2025 (Art Int Surg 5:476): LLaMA-2-13B, 4-bit, zero-shot on 2,422 mesh-implant reports; 200 held out for scoring; adding retrieval raised adverse-event flag accuracy from 83% to 99%.
- Yu, Shi, Feng, Gong 2024 (Stud Health Technol Inform): GPT-4 pipeline on 4,459 colonoscopy reports, three categories, little human annotation.
- Muaz et al. 2026 (AIAI preprint, DkIT): assigned IMDRF codes with LLMs; kept only records where human and LLM agreed; GPT-OSS-120B reached 59% consensus at the coarse level, 23% at the fine level. Lesson: fine-grained fixed code lists are hard; keep our label list short.
- Common pattern: a few hundred hand-checked reports as the yardstick, accuracy or F1 reported, kappa rarely. Nobody has done the paired-number extraction at LLM scale yet.

## 4. Comparison

| Option | Money | Setup effort | Run time (RTX 5080) | Explainable to a reviewer | Reproducible | Expected accuracy | Validation needed |
|---|---|---|---|---|---|---|---|
| a. Codes only | $0 | done | done | very high | exact | exact but shallow | none |
| b. Regex | $0 | 1 to 2 days | minutes | very high | exact | high on templates, low on prose | 200 hand-checked |
| c. Zero-shot NLI | $0 | 1 day | 1 to 3 h | medium | high | guess: low to medium | 300 hand-checked |
| d. Embeddings + clusters | $0 | 1 day | under 2 h | medium (clusters need names) | medium (random seeds) | n/a (discovery) | human naming |
| e. Local LLM + JSON | ~$0 | 2 to 3 days | 1 to 50 h (depends on engine) | high (form + evidence quotes) | high (pinned model) | guess: high on numbers, medium on judgement fields | 400 hand-checked, kappa |
| f. Distillation | ~$0 | 4 to 6 days | hours | medium | medium | similar to e for labels | 400 hand-checked + training split |
| g. Cloud batch (Haiku 5.5) | $8 to $50 | 1 to 2 days | 1 to 6 h | high (same form) | medium (model retires) | guess: slightly above e | 400 hand-checked, kappa |

## 5. Recommendation

Top pick: codes (done) -> regex -> local LLM form-filling -> hand-checked validation. Runner-up: same, but the LLM step runs on Claude Haiku 5.5 batch.

Stage 0. Choose the target set (half a day). Do not run text on all 3.4 million.
- All death/injury reports: 123,607 (`clean/serious.csv.gz`, has both texts).
- The random malfunction sample: 5,193 (`clean/sample.csv.gz`, weighted, has both texts).
- All Libre 3 / 3 Plus malfunction reports coded Low Readings, High Readings or Incorrect Readings (from `clean/full.csv.gz`; guess: 50k to 100k). These carry the recall error sizes.
- Total about 180k to 230k. Skip reports received in the last 3 months (text not there yet). The clean files are not on this PC; copy them (README) or re-pull.

Stage 1. Regex extractor (1 to 2 days). One pattern per maker template plus generic patterns.
- Fields: all mg/dL and mmol/L values with their role (sensor / meter), Parkes zone, wear day, units, LOW/HIGH display words, meter or fingerstick mentioned.
- Check 200 random matches by hand. Target: 98% of extracted pairs correct. Report what share of each maker's texts the regex covers.

Stage 2. Local LLM form-filling (2 to 3 days to build, hours to days to run).
- Model: `qwen2.5:7b-instruct` in Ollama (installed, 4.7 GB). Backup: `qwen3:8b` with thinking off, `gemma3:12b`. Pick by a bake-off on 100 gold reports.
- Tooling: Python 3.11, `ollama` package, `format=` the JSON schema from a pydantic model, temperature 0, fixed seed, `num_ctx` 2048, `OLLAMA_NUM_PARALLEL` 4 to 8. Validate every answer with pydantic; retry once on failure; store raw JSON, model digest and prompt hash per report.
- Before the full run: time 500 reports. If under 10 reports/s, move to llama.cpp server (`-np 8`) or vLLM in WSL2, or switch to the cloud runner-up.
- Form (JSON schema), one record per report:

| Field | Type / allowed values |
|---|---|
| fault_type | one of: reads_low, reads_high, erratic_readings, signal_loss, sensor_error_message, stopped_early, fell_off_or_adhesive, skin_reaction, insertion_injury_or_bleeding, pain, compression_low, lag, alarm_missed, app_or_software, other, not_stated |
| mechanism_note | free text, max 20 words, or empty |
| cgm_values_mgdl | list of numbers (converted from mmol/L if needed); display words as "LOW" / "HIGH" |
| reference_values_mgdl | list of numbers |
| reference_type | fingerstick_meter, lab, other_cgm, not_stated |
| fingerstick_done | yes, no, not_stated |
| acted_on_wrong_reading | yes, no, not_stated; plus action: insulin_given, carbs_given, ems_called, treatment_withheld, other, none |
| wear_day | integer or null |
| outcome_severity | one of: none_stated, no_harm_stated, unneeded_treatment, hypo_symptoms, severe_hypo_needing_help, hyper_or_dka, hospital_or_er, death, not_stated |
| evidence_quotes | 1 to 3 short exact quotes from the text |
| confidence | low, medium, high |

- Prompt sketch (system message, cached / reused): "You read FDA MAUDE reports about glucose sensors. Fill the form. Copy numbers exactly as written. Use not_stated when the text does not say. Boilerplate like 'no report of death' means nothing happened. Sensor = CGM / scan result; reference = meter / BG / fingerstick / lab. Quote the words you used." Then 3 short worked examples (one per maker). Then the report text.
- Post-checks (automatic): every number in the answer must appear in the text; wear day 1 to 15; fault_type reads_low must have sensor < reference when both exist; regex pairs and LLM pairs must agree on Abbott templates (flag the rest).

Stage 3. Validation (2 days, two team members).
- Gold set: 400 reports, stratified: 3 makers x 2 event types, plus extra Libre 3 "Low Readings" reports. Two people label independently with a 1-page codebook, then resolve disagreements together.
- Report human-vs-human Cohen's kappa first (kappa = agreement corrected for chance; 0.6 moderate, 0.7 to 0.8 substantial, over 0.8 almost perfect). Humans must reach 0.7 or the codebook is unclear.
- LLM vs gold: fault_type kappa at least 0.70 to accept (0.80 good); outcome_severity at least 0.75; fingerstick_done and acted_on_wrong_reading at least 0.60 (these are often unstated); paired numbers exact match at least 95%. Report a prevalence-adjusted kappa (PABAK) too, because "no harm" dominates.
- guess: 400 reports gives a 95% confidence interval of about plus or minus 0.05 to 0.08 around kappa 0.8. Exact tables: Sim and Wright 2005.
- Large-scale sanity check, free: LLM reads_low vs FDA "Low Readings" code; LLM hospital vs outcome code "Hospitalization"; LLM pairs vs regex pairs.

Stage 4. Outputs for Phase 2 (1 day): error = sensor - meter, by maker, product, year, and recall window; Parkes zones; wear-day histogram; share with fingerstick check; share who acted on the wrong reading; severity by fault type.

Expected wall-clock, top pick: 2 to 3 weeks of part-time work in total. Compute: under 1 day with a parallel engine, 2 days worst case with plain Ollama (table in option e).
Runner-up (Haiku 5.5 batch): same stages; Stage 2 compute becomes 2 to 5 batches, each usually under 1 hour; cost $8 to $50 for 150k to 500k reports.

Known failure modes and what to do:
- Text missing for recent reports. Filter by date received; re-pull text later for the recall months of 2026.
- Templates make the model lazy. Validate per maker, not pooled; keep the Abbott template in the regex path.
- Redactions "(b)(4)" / "(b)(6)". Expect not_stated for dates and wear day on Dexcom. Report the share.
- Number hallucination or role swap (sensor vs meter). The "number must appear in text" check plus the direction check catch most; sample the rest by hand.
- Many values in one report (Abbott lists several pairs). Lists, not single numbers.
- Units and display words. Convert mmol/L; keep LOW/HIGH as words; flag values over 600 or under 20.
- Invalid JSON or schema breaks. Constrained decoding plus pydantic plus one retry; count failures.
- Judgement fields often unstated. Report "not_stated" rates honestly; do not force a guess.
- Duplicates (patient and maker report the same event). Flag repeated report numbers before counting.
- Slow run on Windows. Benchmark 500 first; the fallback order is llama.cpp -> vLLM in WSL2 -> cloud batch.
- Label list too fine (Muaz 2026 lesson). Start with 16 fault types; merge any with kappa under 0.5.
- Model choice. Keep the prompt and schema fixed, swap the model only, compare on the gold set.

How to iterate: run the 400 gold reports after every prompt or schema change; keep a one-line log of kappa per field; stop when the acceptance thresholds hold on two makers at once; only then run the full set.

## 6. Sources (checked 2026-10-26)

- openFDA MAUDE data page, redaction markers and update notes: https://open.fda.gov/data/maude/
- Anthropic pricing and batch: https://platform.claude.com/docs/en/about-claude/pricing ; https://platform.claude.com/docs/en/build-with-claude/batch-processing
- OpenAI pricing: https://developers.openai.com/api/docs/pricing
- Ollama structured outputs, FAQ (parallel requests), Windows: https://docs.ollama.com/capabilities/structured-outputs ; https://docs.ollama.com/faq ; https://docs.ollama.com/windows
- Ollama model sizes: https://ollama.com/library/qwen2.5 ; https://ollama.com/library/qwen3 ; https://ollama.com/library/gemma3
- llama.cpp grammars / JSON schema: https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md
- vLLM structured outputs: https://docs.vllm.ai/en/latest/features/structured_outputs.html ; Docker Model Runner vLLM on Windows: https://www.docker.com/blog/docker-model-runner-vllm-windows
- Outlines: https://dottxt-ai.github.io/outlines/latest/
- Qwen2.5 speed benchmark: https://qwen.readthedocs.io/en/v2.5/benchmark/speed_benchmark.html ; RTX 4090 vLLM benchmark: https://www.databasemart.com/blog/vllm-gpu-benchmark-rtx4090
- Zero-shot models: https://huggingface.co/facebook/bart-large-mnli ; https://huggingface.co/MoritzLaurer/deberta-v3-large-zeroshot-v2.0
- BERTopic: https://bertopic.readthedocs.io/
- ModernBERT vs DeBERTa-v3 (Antoun et al. 2025): https://arxiv.org/abs/2504.08716 ; ModernBERT paper: https://arxiv.org/abs/2412.13663
- Distillation (Gu et al. 2023): https://arxiv.org/abs/2307.06439
- Krouwer 2020: https://pmc.ncbi.nlm.nih.gov/articles/PMC8875056 ; Krouwer 2025: doi 10.1177/19322968231178525
- Luschi et al. 2023: https://pmc.ncbi.nlm.nih.gov/articles/PMC10638042/
- Bala et al. 2025: https://www.oaepublish.com/articles/ais.2025.44
- Yu et al. 2024: doi 10.3233/SHTI240155 ; Shi and Gong 2025: doi 10.3233/SHTI250076
- Muaz et al. 2026 preprint: https://eprints.dkit.ie/id/eprint/1049/
- Kappa interpretation and sample size (Sim and Wright 2005): doi 10.1093/ptj/85.3.257
