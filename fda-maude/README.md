# FDA recall and MAUDE report mining

Status: NOT STARTED. This folder is a placeholder so the plan has a home.

## Goal (simple)

This is Phase 1 of the project. It runs first and guides Phase 2.

- Collect FDA reports about CGM sensor problems (wrong readings, failures, injuries, deaths).
- Sort them by what went wrong (e.g. "read too low", "sensor fell off", "carbon buildup", "lost signal").
- Count by type, brand, severity, and time.
- Outputs feed Phase 2: which sensor faults are worth simulating, and how big they are.
  Example: reports say "carbon buildup lowered readings over days". Phase 2 then simulates a slow downward drift.
- Teammates also write insights from this on its own (who was harmed, how, when the signal showed up).
- Scope is open. Decide the exact questions after a first look at the data.

## Data sources

| Source | What it is | Access |
|---|---|---|
| FDA MAUDE | Device problem reports, free text + codes | Web search page, or openFDA device event API (free, JSON) |
| FDA recall database | Official recall notices | openFDA device recall API |
| Health Canada incidents | Canadian version | Web only (maybe later) |

CGM product code: QLG (~148k reports). Other codes may exist for older sensors. Check.

## Planned steps

1. Decide: web robot (browser automation) vs openFDA API. Note: the API is simpler and more reliable if it covers what we need. Robot only if the website has data the API does not.
2. Pull reports for Abbott Libre, Dexcom, Medtronic sensors. Save raw JSON here under `raw/` (gitignored if large).
3. Clean: remove duplicates, extract date, brand, outcome, narrative.
4. LLM step: label each narrative with a problem category and a severity. Keep the prompt and a small hand-checked sample for validation.
5. Summaries: counts by category, brand, month. Short plain-language write-up.

## Folder layout (when started)

```
fda-maude/
  README.md        this file
  scripts/         pull + clean + label code
  raw/             downloaded data (gitignored if big)
  results/         tables, figures, plain-language summary
```

## Known risks

- MAUDE is voluntary reporting. Counts show reporting behaviour, not true rates.
- Many reports have missing age/sex.
- Duplicates are common.
- LLM labels need a human spot check.
