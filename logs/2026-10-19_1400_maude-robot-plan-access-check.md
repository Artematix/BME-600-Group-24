# MAUDE robot plan + access check

Date: 2026-10-19 14:00
Who: manager (plan) + 4 general-purpose agents (access checks, run in parallel)
Asked by: Artemy

## Asked
- Plan the FDA MAUDE/recall robot. Confirm each step can actually access the data. Consider web scraping options.

## Done
- docs/plans/2026-10-19_maude-robot-plan.md (draft v2, waiting for approval)
- fda-maude/access-check/01_openfda-event-api.md: WORKS. 3.38 M CGM reports, 13 product codes.
- fda-maude/access-check/02_bulk-files.md: WORKS, but 8-19 GB. Backup only.
- fda-maude/access-check/03_website-scraping.md: PARTLY. 500-result cap, bot wall on form searches, adds ~nothing. TPLC blocked by robots.txt.
- fda-maude/access-check/04_recalls.md: WORKS. 32 CGM recall events, all 6 known recall numbers found.

## Decisions (approved by Artemy 2026-10-19)
- openFDA API is the main route. No scraping.
- Tiered pull: counts for all reports, full records for deaths + injuries, malfunction sample, recalls.
- Recall injury/death counts copied by hand from fda.gov (not in any API).

## Open questions / next
- Approved: tiers 1-4, all 13 codes, 5k malfunction sample, install Python 3.11. Next: build robot after Python install.
- Laptop has Python 3.8.2, no packages. CLAUDE.md section 7 says 3.11. Not edited yet; ask Artemy.
- README guess of "~148k QLG reports" was wrong. Real total is 3.38 M across 13 codes.
