# Phase 1: FDA recall and MAUDE report mining

## What Phase 1 is

- We collected every FDA problem report and every recall for CGM sensors.
- We counted what goes wrong, how often, how bad, for which brand, and when.
- The results tell Phase 2 which sensor faults are worth simulating.
- Text extraction (patterns + a local language model) is validated against a 287-report gold set; the full run is in progress. See the section "Text extraction" below and `results/text/VALIDATION.md`.

Main results: `results/report/report_results.md` and `results/report/country_spread.md`.
Pull numbers and checks: `results/PULL_SUMMARY.md`.

## Status: DONE

Snapshot: FDA data last updated 2026-10-07. Pulled 2026-10-19. Full pull cleaned 2026-10-20.

| Tier | What | Result |
|---|---|---|
| 1. Counts | Count tables for all CGM reports | 3,382,071 reports. DONE |
| 2. Serious | All death + injury reports | 123,607 reports. DONE |
| 3. Sample | Random malfunction reports (target 5,000) | 5,193 reports. DONE |
| 4. Recalls | All CGM recalls + recall class | 95 records, 32 recall events. DONE |
| 5. Full | Every CGM report, all event types | 3,382,071 reports. DONE |
| Clean | One tidy table per tier (tiers 2, 3, 5) | DONE |
| Report | Tables + figures for the course report | DONE |
| Country spread | Where reports come from | DONE |

## Words used here

- CGM = continuous glucose monitor (the sensor on the arm).
- MAUDE = FDA database of device problem reports. Each report has codes and a free-text story.
- openFDA API = an FDA web address a script asks for data. It sends back clean data (JSON).
- Product code = 3-letter FDA label for a device type. We use 13 CGM codes (list in `scripts/config.json`).
- Call = one request to the API.
- Tier = one part of the pull (see the status table).
- Slice = one small piece of a tier (for example one product code x one month). The robot saves each slice on its own, so it can stop and resume.
- API key = a free password from FDA. It raises the daily limit:

| | Calls per day | Calls per minute |
|---|---|---|
| No key | 1,000 | 240 |
| With key | 120,000 | 240 |

## Folder layout

```
fda-maude/
  README.md              this file
  access-check/          tests done before building the robot (2026-10-19). Why we chose the API.
  scripts/
    maude_robot.py       the robot: downloads from openFDA, then cleans (one script, several commands)
    report_results.py    makes the report tables, figures and report_results.md (no API calls)
    country_spread.py    country spread of reports: fetch (API) and report (no API)
    config.json          robot settings: product codes, call caps, sample size, seed
  results/               small files. In git.
    PULL_SUMMARY.md      what was pulled, headline numbers, checks
    counts/              tier 1 count tables (11 CSVs)
    recalls_cgm.csv      tier 4: 95 recall records, 32 recall events
    recall_harm_manual.csv  injuries/deaths per recall, typed in by hand (only on fda.gov news pages)
    report/
      report_results.md  main results write-up (made by report_results.py)
      country_spread.md  country write-up (written by hand from country_spread.py output)
      figures/           fig1-fig6 (report_results.py), fig7 (country_spread.py)
      tables/            a_* to i_* (31 CSVs, report_results.py), k_country_* (country_spread.py)
                         k_country_api_cache.csv = saved API answers. Input for country_spread.py report
  raw/                   downloads. GITIGNORED. 367 MB.
    counts/              raw count answers
    serious/             tier 2 reports, one gzipped file per slice
    sample/              tier 3 reports, one gzipped file per group + sample_plan.json
    full/                tier 5 reports, one gzipped file per slice (997 files)
    recalls/             raw recall answers
    state.json           call counter + list of finished slices
    query_log.jsonl      every call made
    *.log                run messages
  clean/                 one row per report. GITIGNORED. About 225 MB.
    serious.csv.gz       tier 2 (31.7 MB). Needed by report_results.py
    sample.csv.gz        tier 3 (0.5 MB)
    full.csv.gz          tier 5 (193 MB, 3.4 million rows)
```

## Before you start (new computer)

1. Python 3.11.
   - Windows: use `py -3.11` (plain `python` may be a different, older Python).
   - Mac / Linux: use `python3` in place of `py -3.11`.
2. Packages. From the repo root:
   `py -3.11 -m pip install -r requirements.txt`
3. Copy the files git does not give you (next table).

### Files git does not give you

Copy these from the old machine by hand. Keep the same paths.

| What | Size | Needed for | Without it |
|---|---|---|---|
| `fda-maude/clean/serious.csv.gz` | 31.7 MB | `report_results.py` (REQUIRED) | the report script stops with a message |
| rest of `fda-maude/clean/` (`full.csv.gz`, `sample.csv.gz`) | 194 MB | later work (LLM step, full-text analysis). Not used by any script yet | nothing breaks today |
| `fda-maude/raw/` | 367 MB | only to resume or extend the robot, or to run `tables` | robot `status` shows nothing done. `serious`, `sample`, `full` cannot plan until `counts` runs |
| `OPENFDA_API_KEY` user setting | - | any NEW pull (`full`, `country_spread.py fetch`) | robot uses the no-key limit (1,000 calls/day) |

- Everything else the scripts read is in git (`results/counts/`, `results/recalls_cgm.csv`, `results/recall_harm_manual.csv`, `k_country_api_cache.csv`).
- You can rebuild `raw/` and `clean/` with the robot. But FDA adds new reports every week. A new pull will NOT give the exact numbers in our results.

## How to run

Run every command from the repo root. Paths inside the scripts are found from the script folder, so the current folder does not matter for them.

### What each script reads and writes

| Script | Reads | Writes | API calls | Time |
|---|---|---|---|---|
| `maude_robot.py` | openFDA, `scripts/config.json`, `raw/` | `raw/`, `clean/`, `results/counts/`, `results/recalls_cgm.csv` | depends on command (below) | below |
| `report_results.py` | `results/counts/*.csv`, `results/recalls_cgm.csv`, `results/recall_harm_manual.csv`, `clean/serious.csv.gz` | `results/report/report_results.md`, `results/report/tables/a_*` to `i_*`, `results/report/figures/fig1-fig6` | 0 | about 35 s |
| `country_spread.py report` | `results/report/tables/k_country_api_cache.csv` | `results/report/tables/k_country_*.csv`, `results/report/figures/fig7_foreign_countries.png` | 0 | about 4 s |
| `country_spread.py fetch` | openFDA (skips answers already in the cache) | adds to `k_country_api_cache.csv` | about 1,500 if the cache is empty. Needs the key | guess: 30 min |

### Remake the report (most common)

```
py -3.11 fda-maude/scripts/report_results.py
py -3.11 fda-maude/scripts/country_spread.py report
```

- `report_results.py` options:
  - `[path/to/serious.csv.gz]` = use a different input file.
  - `--only-f-summary` = rewrite only `tables/f_libre3_summary.csv`, then stop.
  - `--help` = show the help text.
- `country_spread.py` with no command prints its help text.
- `country_spread.md` is written by hand. Update it yourself if the numbers change.

### The robot: `maude_robot.py`

| Command | What it does | Calls | Time |
|---|---|---|---|
| `py -3.11 fda-maude/scripts/maude_robot.py status` | Shows what is done, what is left, calls used today | 0 | seconds |
| `py -3.11 fda-maude/scripts/maude_robot.py counts` | Tier 1. Count tables only. No reports downloaded. Writes `raw/counts/` and `results/counts/*.csv` | ~170 | about 7 min (no key) |
| `py -3.11 fda-maude/scripts/maude_robot.py tables` | Rebuilds `results/counts/*.csv` from `raw/counts/` | 0 | seconds |
| `py -3.11 fda-maude/scripts/maude_robot.py recalls` | Tier 4. Recall records + recall class. Writes `results/recalls_cgm.csv` | ~45 | guess: 2 min |
| `py -3.11 fda-maude/scripts/maude_robot.py serious` | Tier 2. All death + injury reports. Needs `counts` first | ~190 | about 16 min (no key) |
| `py -3.11 fda-maude/scripts/maude_robot.py sample` | Tier 3. Random malfunction sample. Needs `counts` first | ~550 | guess: 15-30 min |
| `py -3.11 fda-maude/scripts/maude_robot.py full --workers 4` | Tier 5. Every CGM report. Needs `counts` first and the API key | ~4,100 | about 2 h |
| `py -3.11 fda-maude/scripts/maude_robot.py clean` | Builds `clean/serious.csv.gz`, `clean/sample.csv.gz`, `clean/full.csv.gz` from `raw/` | 0 | guess: 10 min |
| `py -3.11 fda-maude/scripts/maude_robot.py clean --tiers full` | Builds only `clean/full.csv.gz` | 0 | guess: 10 min |

- Order for a fresh pull: `counts`, `recalls`, `serious`, `sample`, `full`, `clean`. Then the report scripts.
- Smallest pull for the report: `counts`, `serious`, `clean --tiers serious` (about 360 calls, no key needed). Recalls are already in git.
- Add `--codes SBH,QCD` to run only some product codes (good for tests).
- The robot counts its calls. It stops at the daily cap (`config.json`):
  - no key: `daily_call_cap` = 900
  - with key: `daily_call_cap_with_key` = 100,000
- If it stops, run the SAME command again (next day if the cap was hit). It skips finished work.
- Every call is written to `raw/query_log.jsonl` (address + time + result size).
- Only run one robot command at a time. The lock file `raw/robot.lock` stops two runs.
- The lock file holds the process ID (the number Windows gives a running program). A lock left by a stopped run is taken over automatically.

### The API key

- The scripts read the key from the environment variable `OPENFDA_API_KEY` (a setting Windows keeps for your user).
- If a program starts without it, the scripts read the saved Windows user setting directly.
- The key is sent in a hidden header ("basic auth"), not in the web address.
- So the key is never written to `query_log.jsonl`, logs, or any file. Never paste it into a file yourself.
- Get a free key from the openFDA website. Set it once (PowerShell), then open a new terminal:
  `[Environment]::SetEnvironmentVariable("OPENFDA_API_KEY","<your key>","User")`

### Tier 5: the full pull (all reports)

- Workers = slices fetched at the same time. Default 4 (`full_workers` in `config.json`). Allowed: 1 to 8.
- Calls start at least 0.6 s apart across all workers (`full_min_seconds_between_calls`). So at most 100 calls per minute. FDA allows 240.
- On a "too many requests" answer (code 429) all workers pause, then retry.
- Server and network errors are retried with longer and longer waits.
- A slice that still fails is tried again 2 more times at the end of the run.
- Our run (2026-10-19): 16:05 to 17:55, 4,093 calls, all 997 slices complete.

Speed test (2026-10-19, pages of 999 QBJ reports):

| Workers | Reports per hour |
|---|---|
| 1 | about 2.1 million |
| 2 | about 4.2 million |
| 4 | about 6.4 million |
| 6 | about 7.3 million |

- 4 workers chosen: big gain over 1, small extra gain past 4.
- The real run is slower: the 0.6 s call gap, small slices, and writing files.

Start it in the background, so it keeps running after the terminal closes. Windows PowerShell only, from the `fda-maude` folder:

```
$py = (py -3.11 -c "import sys;print(sys.executable)")
$cmd = "cmd.exe /c `"`"$py`" -u scripts\maude_robot.py full --workers 4 >> raw\full_run.log 2>&1`""
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$cmd; CurrentDirectory=(Get-Location).Path}
```

| Task | Command (from the `fda-maude` folder) |
|---|---|
| Check progress | `py -3.11 scripts/maude_robot.py status` |
| See the latest log lines | `Get-Content raw\full_run.log -Tail 20` |
| Stop it | `Stop-Process -Id (Get-Content raw\robot.lock)` |
| Resume after a stop or crash | Run the start command above again. Finished slices are skipped |
| After it ends | `py -3.11 scripts/maude_robot.py clean --tiers full` |

- `status` shows: slices done, reports, calls, speed, and a guess of the time left.
- A slice that was half done when stopped is fetched again from its start.
- FDA updates its data about once a week. If that happens during the run, some slices may get a few more reports than planned. `status` lists them. This is normal.

## How the pieces are split (so the robot can resume)

- Tier 2: one slice = one product code x one year (by date received). Years with more than 10,000 reports are cut into date ranges.
- Tier 5: one slice = one product code x one month (by date received). 997 slices.
- Tier 5 months with more than 20,000 reports are cut into date ranges (`full_max_slice`).
- Inside a slice the robot follows the API's "next page" link. This gets past the API's 25,000-record limit.
- Tier 5 slices are written to disk page by page, so memory use stays small.
- A slice is marked done only after its file is fully written.
- Reports keep only the fields we need: IDs, both dates, event type, device, problems, patient, and the two story texts.

## Sampling method (tier 3, malfunction reports)

- Groups (strata) = product code x year received. Sizes come from the tier 1 daily counts.
- Each group gets a share of the 5,000 in proportion to its size. Any group with 25+ reports gets at least 25.
- Small groups: the robot downloads the whole group and picks reports at random.
- Big groups: the robot picks a random report position in the group (so busy days are picked more often), then takes that report and up to 9 more right after it on the same day (a "cluster" of up to 10). One call per cluster. It repeats until the group has enough reports.
- Random choices use a fixed seed (20261019), so a rerun picks the same reports (if FDA data has not changed).
- Each report gets: its group, its chance of being picked (`sel_prob`), and a weight (`weight` = 1 / chance). `weight_norm` is the weight scaled so a group's weights add up to the group size.
- Use the weights when you turn sample counts into estimates for all malfunction reports.

## Cleaning rules

- One row per report (`mdr_report_key`). Duplicate keys are removed.
- Repeated `report_number` is flagged (`repeated_report_number`), not removed.
- A report that lists two CGM codes is downloaded in two slices. Clean keeps it once.
- `full.csv.gz` has the same columns as `serious.csv.gz`.
- `full.csv.gz` rows are in slice order (product code, then month), not sorted by date.
- `full.csv.gz` is built one report at a time, so it never holds all 3.4 million stories in memory.
- `full.csv.gz` is 193 MB on disk and much bigger in memory. Read it in chunks: `pd.read_csv("fda-maude/clean/full.csv.gz", chunksize=200000)`.
- Blank, "NA", "N/A", "Unknown", "UNK" and "None" count as missing.
- Device fields come from the device with a CGM product code (a report can list more than one device).
- `event_text` = "Description of Event or Problem". `mfr_narrative` = "Additional Manufacturer Narrative". Both are ALL CAPS in the API.

### Country per report

- `reporter_country_code` = country of the person who reported the problem.
- It IS in the clean tables. Checked 2026-11-08: filled in 94.9 % of serious reports (top codes US, GM = Germany, FR = France). An earlier note here said it was missing and needed a re-pull. That was wrong.
- The per-report field agrees with the API country counts (`results/inventory/country_per_report.csv`, from `scripts/field_inventory.py`).
- Country counts in the report came from `scripts/country_spread.py` (one API search per country code). See `results/report/country_spread.md`.

## Known risks

- MAUDE is voluntary reporting. Counts show reporting behaviour, not true failure rates.
- Date received is not the date the problem happened. Libre 3 reports jump in 2026 by date received only (late reports). We keep both dates.
- Many reports have missing age and sex. Race and ethnicity are almost always empty.
- Brand names are messy ("FREESTYLE LIBRE 3" vs "FreeStyle Libre 3").
- A few sensors are filed under insulin-pump codes (OZP, OZO). The 13 codes miss those.
- LLM labels (later) need a human spot check.

## Text extraction (validated; full run started 2026-10-30)

Three layers read the report texts: FDA codes (done), patterns (regex), and a local language model that fills a fixed form. Method and decisions: `METHODOLOGY.md`. Pilot: `results/text/PILOT.md`. Validation against the 287-report gold set: `results/text/VALIDATION.md` (summary) and `validation_v1.md`, `validation_v2.md`, `validation_v3.md` (all tables). Prompt history: `prompts/CHANGELOG.md`. Run set: `results/text/RUN_SET.md`.

| File | What it is |
|---|---|
| `scripts/extract_regex.py` | pattern layer (regex). Reads the maker templates. Free, exact, auditable. |
| `scripts/llm_extract.py` | model layer. A local open model (Ollama, qwen2.5:7b-instruct) fills the form. `--prompt-version v1`, `v2` or `v3`. Guards every number against the text. Combines with the regex into `final`. Resumable. |
| `scripts/score_against_gold.py` | scores regex, model and combined output against `gold/gold_labels_v1.csv`: accuracy, kappa, exact match, confusion tables, run-to-run agreement. |
| `scripts/build_run_set.py` | builds the run set: serious reports with text (3+ months old) plus a local weighted malfunction sample. Writes `results/text/RUN_SET.md`. |
| `scripts/start_ollama_server.ps1` | stops the Ollama tray app and stray `llama-server.exe`, starts `ollama serve` with 8 slots. |
| `scripts/run_full_extract.ps1` | starts or resumes the full model run as a detached process. |
| `prompts/v1_*`, `v2_*`, `v3_*` | the exact prompt and form of each version. Never edit a scored version; make a new one. v3 is used for the full run. |
| `results/text/` | pilot outputs, gold-set runs (`llm_gold_v2_run1.jsonl`, ...), validation reports, `RUN_SET.md`, `regex_run_set_hitrates.md` |
| `clean/run_set.csv.gz`, `clean/regex_run_set.csv`, `clean/text_extract_v3.jsonl`, `clean/logs/` | run set, regex output, model output and logs. Not in git; rebuilt by the scripts. |

Validation result (v3, combined system, 287 gold reports): fault_type kappa 0.77, outcome_severity 0.75 (exact 0.745), user_action 0.77, numbers 96 % exact, 91 % of forms identical between two runs. Medtronic is the weakest maker (kappa about 0.6).

How to run (from the repo root; Windows: plain `python`, not `python -I`):

1. Patterns: `python fda-maude/scripts/extract_regex.py INPUT OUTPUT.csv` (INPUT = `fda-maude/data/sample_narratives.jsonl`, `fda-maude/clean/serious.csv.gz` or `fda-maude/clean/run_set.csv.gz`). Writes `*_hitrates.md` next to the output. About 1,300 reports per second.
2. Server for parallel runs: `powershell -ExecutionPolicy Bypass -File fda-maude/scripts/start_ollama_server.ps1 -Parallel 8`. This quits the tray app. When all runs are done, start Ollama from the Start menu again.
3. Model on the gold set: `python fda-maude/scripts/llm_extract.py fda-maude/data/sample_narratives.jsonl OUT.jsonl --prompt-version v3 --parallel 8 --num-ctx 6144 --regex-csv fda-maude/results/text/regex_sample.csv --tag mytag`
4. Score: `python fda-maude/scripts/score_against_gold.py --gold fda-maude/gold/gold_labels_v1.csv --regex fda-maude/results/text/regex_sample.csv --llm OUT.jsonl --llm2 OUT2.jsonl --version v3 --out fda-maude/results/text/validation_v3.md --compare fda-maude/results/text/validation_v1_metrics.json`
5. Run set: `python fda-maude/scripts/build_run_set.py`, then `python fda-maude/scripts/extract_regex.py fda-maude/clean/run_set.csv.gz fda-maude/clean/regex_run_set.csv`
6. Full run, start or resume (it skips reports already in the output file): `powershell -ExecutionPolicy Bypass -File fda-maude/scripts/run_full_extract.ps1`
   - progress: `Get-Content fda-maude/clean/logs/text_extract_v3.log -Tail 3`
   - rows done: `(Get-Content fda-maude/clean/text_extract_v3.jsonl | Measure-Object -Line).Lines`
   - stop: `Stop-Process -Id <pid>` (the pid is printed at start). Run the script again to resume.
7. Output rows (JSONL): `llm` = the model's form (v2+: raw values and units, converted to mg/dL in code), `regex` = the pattern layer, `final` = the combined answer to use, `final_source` = where each value came from, `guard_dropped`, `disagree_fields`, `role_swap`, latency and tokens. `OUT_summary.json` has throughput and counts.

Settings used for validation and the full run: temperature 0, seed 42, 8 parallel requests, num_ctx 6144 (v3; the v3 prompt is about 2,900 tokens and the longest report texts reach 2,000), model digest 845dbda0ea48. Before any long run check `ollama ps` says "100% GPU" and that only one `llama-server.exe` is alive.

Results of the full run (2026-10-30: 124,599 reports in 9.55 h, 0 errors): `python fda-maude/scripts/text_results.py` (about 10 s; all paths are options, see `--help`; `--max-rows N` for a quick test).
- Reads `clean/text_extract_v3.jsonl`, `clean/run_set.csv.gz`, `clean/regex_run_set.csv`, `clean/serious.csv.gz`, `clean/sample_local.parquet`, `analysis/simulation_v2_lookup.csv` and the problem-family mapping.
- Writes tables to `results/text/tables/` (`a_*` coverage, `b_*` fault types vs codes, `c_*` error sizes and Parkes zones, `d_*` wear day, `e_*` actions and outcomes, `f_*` the join to the Phase 2 lookup table; `key_tables.md` = markdown copies; `text_results_stats.json` = the key numbers).
- Writes figures `results/text/figures/t1_coverage.png` to `t6_join.png`.
- Write-up: `results/text/TEXT_RESULTS.md`. The bridge numbers are also in `analysis/FINDINGS.md` section 6.1.

Brand comparison and demographics (2026-11-06): `python fda-maude/scripts/brand_comparison.py` (about 70 s; `--n-boot 200` for a quick test; all paths are options, see `--help`; seed 20261106, deterministic).
- Reads the same files as `text_results.py` (it imports that script's loading code) plus age, sex and reporter from `clean/serious.csv.gz` and `clean/sample_local.parquet`.
- Compares Abbott, Dexcom, Medtronic (caution) and Senseonics on the wrong-reading complaints: error size, direction, where the true glucose was, Parkes zone, wear day, fingerstick, actions, outcomes, FDA codes, year and the two Libre 3 recall windows; tests with effect sizes and bootstrap CIs; confound checks (Abbott template, serious vs sample, year); the same cuts by patient age group and sex.
- Writes tables `results/text/tables/g_*.csv` (`g_key_tables.md` = markdown copies; `g_brand_comparison_stats.json` = the key numbers) and figures `results/text/figures/t7_brand_error_sizes.png` to `t10_demographics.png`. Does not touch the `a_` to `f_` tables.
- Write-up: `results/text/BRAND_COMPARISON.md`.

Wider pattern layer over every report (2026-11-06): `scripts/extract_regex_v2.py` (imports the v1 patterns from `extract_regex.py`, which is not changed) and `scripts/report_regex_v2.py` (tables and figures).
- Why: the model read only the 124,599 run-set reports. The 3.26 million malfunction-only reports were never read. Patterns are fast enough for all of them.
- `python fda-maude/scripts/extract_regex_v2.py tune` (about 1 min with 20 workers): runs v1 and v2 on the run set and compares both with the model's numbers. Writes `results/text/tables/h_regex_v2_recall_by_brand.csv`, `h_regex_v2_by_pattern.csv`, `h_regex_v2_wear_zone.csv`, `h_regex_v2_spotcheck_50.csv` (50 random pairs the model did not find, for the eye check), `h_regex_v2_disagreements_sample.csv`.
- `python fda-maude/scripts/extract_regex_v2.py mine [--stages v1|v2]` prints the sentences around the model's values for 400 random reports the patterns missed (seed 20261106; the file goes to the TEMP folder, not the repo).
- `python fda-maude/scripts/extract_regex_v2.py full` (about 8 min with 20 workers; `--max-groups 2` for a quick test): every report in `clean/full.parquet`, one row per report -> `clean/regex_v2_full.csv.gz` (39 MB, not in git), then the report step.
- `python fda-maude/scripts/extract_regex_v2.py report` (about 1 min): tables `results/text/tables/h_*.csv`, `h_regex_v2_stats.json`, figures `results/text/figures/t11_regex_v2_recall.png`, `t12_malfunction_vs_serious_errors.png`, `t13_harm_gradient.png`.
- Options: `--workers N` (default: CPUs minus 2, at most 20), `--out`, `--tables-dir`, `--figures-dir`. Deterministic: seed 20261106.
- Write-up: `results/text/REGEX_V2_FULL_CORPUS.md`.
