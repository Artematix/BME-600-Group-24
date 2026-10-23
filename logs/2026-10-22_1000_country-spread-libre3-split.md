# Country spread + Libre 3 death/injury split

Date: 2026-10-20 to 2026-10-22
Who: manager + 2 general-purpose agents
Asked by: Artemy

## Asked
- Spread of countries in the FDA reports, as percentages.
- Death / injury split for the Libre 3 post-recall summary (table f).

## Done
- Full pull cleaned: clean/full.csv.gz, 3,382,071 unique reports.
- results/report/country_spread.md, tables k_country_*.csv, fig7. Script: scripts/country_spread.py.
- Country = `reporter_country_code` (found by Artemy). Searchable, not countable, so 1 search per code (~1,500 calls).
- Robot now keeps reporter_country_code (needs a ~1 h re-pull of `full` to store it per report).
- report_results.py: new `--only-f-summary` flag. f_libre3_summary.csv + section f table updated.

## Decisions
- Country codes mix FIPS and ISO by maker and year. Both merged per country. Ambiguous codes resolved by maker/era (see k_country_codes.csv).
- Use the country field, not the "Foreign" flag. The flag misses 44% of non-US reports.

## Findings worth remembering
- US 63.8% of all reports, 44.3% of death + injury. Germany is the top non-US country.
- The old "5,347 Low Readings" row was ALL TIME, not post-recall. Post-recall Low Readings = 2,638 (21 deaths, 2,617 injuries).

## Open questions / next
- Re-pull `full` to store country per report (only if needed for the LLM step).
- LLM labelling plan. Commit when Artemy asks.
