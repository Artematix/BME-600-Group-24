# 2026-10-30 18:10. MAUDE text full run finished, results memo, lookup extension

## Asked
- User (Oct 26): run the text pipeline on all serious reports and join the real error sizes to the fault simulation.
- User (today): explain all work so far for the group meeting; draft the group update.

## Who
Manager plus two agents (results memo; lookup extension).

## What happened
- Full model run 08:24 to 17:57: 124,599 reports, 0 errors, 3.5 % guard drops. Output `fda-maude/clean/text_extract_v3.jsonl` (local only, gitignored).
- Results agent wrote `fda-maude/scripts/text_results.py`, `fda-maude/results/text/TEXT_RESULTS.md`, `fda-maude/results/text/tables/`, figures `t1` to `t6`, `analysis/FINDINGS.md` section 6.1, and a run block in `fda-maude/README.md`. Manager re-ran the script: byte-identical.
- A duplicate results agent was started by mistake before the first one reported back. Stopped before it wrote anything.
- Lookup extension agent started 18:20: extend `analysis/simulation_v2_lookup.csv` to -90..+90 % as a separate file and redo the join.

## Decisions
- The join must not be a clipped floor. Extend the lookup table instead of reporting the -40 % row.
- Direction of a reported error comes from the two numbers, not the model's label (the model mislabels Dexcom direction).
- Keep the wear-day-1 result in the paper, labelled exploratory. User agreed today.
- Ignore pilot model outputs in git (`fda-maude/results/text/llm_sample_*.jsonl`, `llm_serious500_*.jsonl`). Keep the gold v2 and v3 runs that the validation rests on.

## Key new numbers
| Item | Value |
|---|---|
| Serious reports with both glucose values | 18,118 of 118,462 |
| Abbott reads-low error, median | -77 % |
| Dexcom reads-low error, median | -68 % |
| Dexcom complaints that read high | 55 %, most hiding a true low |
| Reads-low errors beyond -40 % | 78 to 94 % |

## Open
- Human check of 100 gold reports by teammates (`fda-maude/gold/GOLD_SET.md`).
- Push waits for the user's word.
- Ollama server still running; 19 GB of bulk zips in `fda-maude/raw/bulk_zips/` can be deleted.

## Update 18:55
- Extension done: `analysis/simulation_v2_lookup_extended.csv` (-90..+90 %). Join redone. Abbott reads-low complaints: 49 % of corrections skipped, 96 % of highs hidden. Details: `fda-maude/METHODOLOGY.md`, `analysis/METHODOLOGY.md`.
- Figure fixes 13, 15, 20, 22 done; no computed value changed.
- Push list: 161 files, 10.1 MB; the biggest are four 0.6 MB gold-run files. Waiting for the user.
