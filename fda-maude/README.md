# Phase 1: FDA recall and MAUDE report mining

## What Phase 1 is

- We collected every FDA problem report and every recall for CGM sensors.
- We counted what goes wrong, how often, how bad, for which brand, and when.
- The results tell Phase 2 which sensor faults are worth simulating.
- LLM labelling of the free-text stories is a later, separate step. Not started.

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

### Country per report (not stored yet)

- `reporter_country_code` = country of the person who reported the problem.
- The robot keeps this field since 2026-10-20. Our raw files were pulled before that, so the clean tables have no country per report.
- To get it per report: re-pull tier 5 `full` (about 4,100 calls, about 2 hours with the key), then run `clean --tiers full`. Not done. Only needed if the LLM step needs it.
- Country counts for the report come from `scripts/country_spread.py` (one API search per country code). See `results/report/country_spread.md`.

## Known risks

- MAUDE is voluntary reporting. Counts show reporting behaviour, not true failure rates.
- Date received is not the date the problem happened. Libre 3 reports jump in 2026 by date received only (late reports). We keep both dates.
- Many reports have missing age and sex. Race and ethnicity are almost always empty.
- Brand names are messy ("FREESTYLE LIBRE 3" vs "FreeStyle Libre 3").
- A few sensors are filed under insulin-pump codes (OZP, OZO). The 13 codes miss those.
- LLM labels (later) need a human spot check.
