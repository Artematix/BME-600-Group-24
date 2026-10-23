# MAUDE robot: build + first run

Date: 2026-10-19 16:00
Who: manager (setup, review) + 1 general-purpose agent (build + run)
Asked by: Artemy

## Asked
- Build the approved robot (tiers 1-4) and run it.

## Done
- Python 3.11 installed by Artemy. Manager installed analysis packages + requests. CLAUDE.md section 7 updated: use `py -3.11`.
- .gitignore: added fda-maude/raw/ and fda-maude/clean/.
- fda-maude/scripts/maude_robot.py + config.json. Subcommands: counts, recalls, serious, sample, clean, status.
- Tier 1 counts: 169 queries -> fda-maude/results/counts/. Totals match access check (3,382,071).
- Tier 4 recalls: results/recalls_cgm.csv (95 records, 32 events). results/recall_harm_manual.csv (Libre 3 row only).
- Tier 2: clean/serious.csv.gz, 123,607 unique death + injury reports.
- Tier 3: 2,787 of 5,000 malfunction reports. Stopped at daily call cap (700).
- fda-maude/README.md and results/PULL_SUMMARY.md written.

## Decisions
- Recall search also uses codes PHV, QRX and pump code OZP (needed to find all 32 CGM events).
- Sample = proportional by product code x year received, fixed seed, small clusters of <=10 reports per call. Weight column kept.

## Open questions / next
- 2026-10-20: run `py -3.11 scripts/maude_robot.py sample` then `clean` from fda-maude/. About 200 calls (guess).
- Fill recall_harm_manual.csv for the other 6 Class I recalls by hand.
- Next plan: LLM labelling of narratives.
- Nothing committed yet.
