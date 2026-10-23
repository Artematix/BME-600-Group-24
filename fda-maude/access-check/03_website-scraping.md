# Access check 03: scraping the FDA websites

**Verdict: scraping PARTLY WORKS. It is allowed for MAUDE and the recall pages, but it adds almost nothing the openFDA API does not already give us. TPLC is NOT ALLOWED.**

Tested live on 2026-10-19. Total requests: 16 to accessdata.fda.gov, 6 to api.fda.gov, at least 2.5 seconds apart.
Probe scripts and saved pages were kept locally, not in the repo.

Terms:
- **Scraping** = a script downloads web pages made for people and pulls the data out of the page text (HTML, the code behind a web page).
- **API** = a door built for scripts. It returns clean data (JSON, a structured text format). openFDA = `api.fda.gov`.
- **robots.txt** = a file where a website says which pages robots may and may not fetch.
- **Bot wall** = a check that tries to block scripts, for example a hidden JavaScript puzzle.
- **Product codes**: QBJ = newer CGMs (Dexcom G6/G7, Libre 2/3). QLG = Libre-type CGMs. MDS = older CGMs (Medtronic).

## 1. What robots.txt says (`accessdata.fda.gov/robots.txt`)

| Path | Allowed? |
|---|---|
| `/scripts/cdrh/cfdocs/cfmaude/` (MAUDE search, results, detail) | Yes, not listed |
| `/scripts/cdrh/cfdocs/cfRES/res.cfm` (recall database) | Yes (only `cfres/textresults.cfm` is blocked) |
| `/scripts/cdrh/cfdocs/cftplc/` (TPLC) | **No, blocked** |
| Any `/scripts/cdrh/*excel*.cfm` ("Export to Excel" buttons) | **No, blocked** |

The file also asks robots to:
- wait **30 seconds** between requests ("Hit-rate: 30"),
- crawl only between **11 PM and 5 AM US Eastern** ("Visiting-hours"),
- use at most **2** connections at once.

These are polite requests, not hard rules. A fair robot should follow them.

## 2. Live test results

| Thing tested | URL (short) | Result | Evidence |
|---|---|---|---|
| MAUDE search page | `cfmaude/search.cfm` | yes | HTTP 200, 195 KB of normal HTML. No captcha. |
| Search sent as a form (POST) | `cfmaude/results.cfm` + form data | **no** | 3 of 3 tries (QBJ, QBJ with cookies, QLG): HTTP 200 but page title "Challenge Validation". That is an Akamai bot wall (JavaScript puzzle). No data. |
| Search as a plain link (GET) | `results.cfm?ProductCode=MDS&ReportDateFrom=09/01/2026&ReportDateTo=09/30/2026&pagenum=100` | yes | HTTP 200, 160 records, 100 rows per page. Each row links to a report. No JavaScript needed. |
| Same for QBJ and QLG (Sept 2026) | same, ProductCode=QBJ / QLG | partial | Both say "500 records ... results are incomplete - please narrow your search". |
| Page 2 of results | `results.cfm?start_search=101...` | yes | HTTP 200, 60 more rows (MDS). |
| Going past 500 | `results.cfm?start_search=501...` (QBJ) | no | HTTP 200, 0 rows. |
| Narrow search: QBJ deaths, Jan 2025 - Sept 2026 | `results.cfm?ProductCode=QBJ&EventType=Death...` | yes | 189 records (under the cap). |
| One report page | `cfmaude/detail.cfm?mdrfoi__id=21050673` | yes | HTTP 200, 43 KB. Works with or without cookies. |
| TPLC for QBJ | `cfTPLC/tplc.cfm` | not tested | Blocked by robots.txt, so not fetched. |
| Recall search for QBJ | `cfRES/res.cfm?start_search=1&productcode=QBJ` | yes | HTTP 200, 23 recalls listed. |
| One recall page | `cfRES/res.cfm?id=220303` | yes | HTTP 200. Dexcom G7, Class 2, recall Z-2574-2026. |

Hard limits of the website:
- **500** results max per search (stated on the page and confirmed).
- Last **10** years of reports only (stated on the page).
- QBJ reports received in Sept 2026 alone (API count): **83,884**. That is about **2,800 per day**, so even a 1-day search hits the cap.

## 3. Website vs openFDA API (same questions)

| Check | Website | API |
|---|---|---|
| MDS reports, Sept 2026 | 160 | 164 |
| QBJ deaths, Jan 2025 - Sept 2026 | 189 | 190 |
| QBJ recalls (all time) | 23 | 23 |

The counts almost match. guess: the small gaps come from slightly different date fields or update timing.

Fields on the report page (report 21050673), compared with the API record for the same report:
- Same in both: brand, model, lot number, expiry date, event type, dates, patient age/sex/weight, problem names, full narrative text (including follow-up reports), manufacturer, 510(k) number.
- **Only on the website:** the number of each problem code. Example: "Wireless Communication Problem (3283)". The API gives only the name.
- **Only on the website:** narrative in normal upper/lower case. The API gives ALL CAPS.
- Recall pages: all fields we saw (reason, FDA cause, action, lots, distribution) are also in the API `device/recall.json`. The recall **class** (1, 2, 3) shows on the web page but is not in `device/recall.json`. guess: it is in the API `device/enforcement.json` (not tested).

## 4. Python tools on the test laptop (at test time)

Found: **Python 3.8.2** only, with pip 19.2.3.
- Python 3.11 was not installed yet. It was installed later for the robot (see `fda-maude/README.md`).
- Only pip, setuptools, vboxapi are installed. Microsoft Edge is installed (a browser tool could drive it).

| Tool | Installed? | Needed? | Why |
|---|---|---|---|
| requests (download pages) | no | yes, if we scrape | GET pages work with plain requests. My tests used Python's built-in `urllib`, which does the same job. |
| BeautifulSoup (bs4) + lxml (read HTML) | no | yes, if we scrape | Pages are plain HTML tables and label/value lists. Easy to parse. |
| httpx | no | no | Same job as requests. No extra benefit here. |
| pandas (tables) | no | yes, for later analysis | Not needed to collect. |
| Playwright (drives a real browser) | no | no | Only needed to beat the POST bot wall. GET links avoid it. |
| Selenium (drives a real browser) | no | no | Same as Playwright, older and slower. |
| Scrapy (big crawler framework) | no | no | Built for crawling thousands of pages fast. The site asks for 30 s per page, so speed gives no gain. |

## 5. What this means for the robot

- **Use the openFDA API as the main source.** It has the same reports, the same text, the same counts, and no 500 cap per search.
- Scraping the website adds very little. The only new things seen: numeric problem codes, mixed-case text, and recall class on one page.
- Do not crawl MAUDE in bulk. At the requested 30 s per page, 1,000 reports would take about **8 hours**. One month of QBJ has about **84,000** reports.
- If we need the website at all, use plain GET links with requests + BeautifulSoup. No browser tool is needed. Avoid the POST form (it hits the bot wall).
- Do not use TPLC or "Export to Excel" pages. robots.txt blocks them.
- Before building: install a newer Python (3.11+) or confirm 3.8 is fine, then `pip install requests` (plus bs4 only if we scrape).
