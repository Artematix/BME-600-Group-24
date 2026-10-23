# Access check 02: bulk download files (download everything, filter on our laptop)

**Verdict: WORKS.** Both bulk sources downloaded fine with plain Python. No login, no blocking. The only real cost is size: about 8 GB (MAUDE raw) or about 18 GB (openFDA bulk), compressed.

Tested live on 2026-10-19. Probe scripts and downloads are in the session scratchpad (not committed).
Total downloaded during the test: about 75 MB (budget was 100 MB).

## Terms
- **Bulk file**: a big zip file with all reports for a time period. You download it, then search it yourself.
- **Partition**: one piece of the openFDA bulk data (one zip file, max 95,000 reports).
- **HEAD request**: asks a server "does this file exist, how big is it?" without downloading it.
- **Product code**: a 3-letter FDA code for a device type. CGM codes seen: MDS, QBJ, QLG, PQF, PZE, QHJ, SAF, SBA, QDK.
- **Narrative**: the free-text story of what happened, written by the reporter or maker.
- **MDR_REPORT_KEY**: the ID number of one report. It links the MAUDE tables together.
- **Pipe-delimited**: a text table where columns are split by the `|` character.

## What was tested

| Thing tested | URL | Result | Evidence |
|---|---|---|---|
| openFDA bulk manifest (file list) | api.fda.gov/download.json | yes | HTTP 200. device/event: 375 partitions, 18,699 MB zipped, 26,557,775 reports, export_date 2026-10-14 |
| openFDA bulk HEAD on 3 files | download.open.fda.gov/device/event/... | yes | All 200. Sizes: 2 KB, 64.9 MB, 85.4 MB. Last-Modified 16 Oct 2026 |
| openFDA partition download | .../device/event/2025q1/device-event-0008-of-0008.json.zip | yes | 16.2 MB zip in 2.7 s. Unzips to 146 MB JSON. Parsed in 3.2 s |
| Filter by `device[].device_report_product_code` | same file | yes | 20,251 reports. CGM codes: QBJ 2,359, PQF 206, QLG 172, MDS 16, PZE 8, SAF 7, QHJ 7, SBA 3, QDK 1 |
| Narrative (`mdr_text`) present | same file | yes | 100% of CGM reports have it. Types: "Description of Event" and "Manufacturer Narrative". Median length 203 characters |
| Problem terms present | same file | yes | `product_problems` in 99.7% of CGM reports (plain words, e.g. "Incorrect, Inadequate or Imprecise Result or Readings") |
| MAUDE data files page | fda.gov/.../mdr-data-files | yes | HTTP 200, not blocked. "Content current as of 09/02/2026". Says files update monthly |
| MAUDE HEAD on all 83 file links | accessdata.fda.gov/MAUDE/ftparea/*.zip | yes | All 83 returned 200 with a size. Current-year files dated 13 Oct 2026 |
| MAUDE small file download + format | deviceadd, mdrfoiadd, foitextadd, patientadd, 2 code lists | yes | 58 MB total. Format details below |
| Join by MDR_REPORT_KEY | add files above | yes | 145,991 CGM report keys in deviceadd. All 145,991 found in mdrfoiadd. 53,518 found in foitextadd |
| openFDA API (2 calls, for comparison) | api.fda.gov/device/event.json | yes | 3,375,299 CGM reports total. last_updated 2026-10-07. Newest date_received 2026-09-30 |
| Full download of any whole source | - | not tested | Too big for this test |
| Recall bulk files (device/recall 275 MB, enforcement 91 MB) | listed in manifest | not tested | Only seen in manifest |

## MAUDE raw file families

| Family | What it has | Example files | Size (zipped, all years) |
|---|---|---|---|
| mdrfoi (master) | 1 row per report: dates, event type (death / injury / malfunction) | mdrfoithru2025.zip (717 MB), mdrfoi.zip (104 MB, 2026) | 822 MB |
| device (foidev) | **product code**, brand, model, lot number | device2000.zip ... device2025.zip, device.zip | 925 MB |
| foitext | **narrative text** | foitext1996.zip ... foitext2025.zip (633 MB), foitext.zip (417 MB) | 5,355 MB |
| foidevproblem | device problem codes per report (numbers only) | foidevproblem_thru2025.zip, foidevproblem.zip | 141 MB |
| patient + patientproblemcode | patient age/sex, patient problem codes | patientthru2025.zip, patientproblemcode*.zip | 514 MB |
| code lookups | code number -> plain words | deviceproblemcodes2025.zip (13 KB), patientproblemcodes2026.zip (17 KB) | tiny |
| add / change | this month's new and changed reports | mdrfoiadd, deviceadd, foitextadd, ... | 190 MB |

All MAUDE files: about 7,947 MB zipped. Core set (mdrfoi + device + foitext + problems): about 7,240 MB.

MAUDE format facts (from the downloaded files):
- Data tables: pipe-delimited `.txt`, header row on line 1, Windows line endings.
- Encoding (how letters are stored as bytes): **not UTF-8**. Must read as cp1252 (Windows Latin) or the script crashes.
- Code lookups: comma-delimited CSV, UTF-8 with a BOM (hidden marker at file start). Columns: FDA_CODE, TERM, NCIT_CODE, IMDRF_CODE.
- 96 of 432,084 rows in mdrfoiadd had the wrong number of columns. Guess: stray `|` or line breaks inside text. Need a careful parser.
- Only 43% of reports in this month's add file have narrative rows. The rest may arrive later in change files. Guess: not checked.
- FDA's own size table on the page is out of date (says mdrfoi.zip is 49 MB; real file is 104 MB).

## Comparison

| | openFDA API | openFDA bulk | MAUDE raw files |
|---|---|---|---|
| Can filter before download | yes (search by product code) | no, must get everything | no, must get everything |
| Download size for CGM work | only CGM reports (3.4 M reports). guess: a few GB of JSON, many calls | 18,699 MB zipped (16,173 MB for 2015+). Unzipped about 9x bigger | about 7,240 MB zipped (core set) |
| Narratives | yes | yes, inside each report | yes, separate foitext tables |
| Problem codes | yes, as words | yes, as words | numbers + lookup table |
| Format | JSON, one record = one report | JSON, same as API | 5+ pipe tables, join by MDR_REPORT_KEY |
| Up to date | data to 2026-09-30 | export 2026-10-14, has 2026 Q3 files | files 13 Oct 2026, add file to 2026-09-30 |
| Ease | easy, but rate limits and max 25,000 records per search (guess: from openFDA docs, tested in another check) | easy parsing, big download | hardest: joins, encoding, broken rows |
| Download time (measured speeds) | not tested | about 6 MB/s -> guess: about 1 hour | 0.6-6 MB/s -> guess: 0.5-3 hours |
| Disk space | small | guess: 19 GB zipped; can read zips without unzipping | guess: 8 GB zipped; about 50 GB if unzipped |
| Process time on laptop | not tested | guess: about 1 hour (3 s per 146 MB file x 375 files, plus filtering) | guess: 1-2 hours, one pass per table |

## What this means for the robot
- Bulk download is a safe backup. It needs no API key and nothing blocked us.
- openFDA bulk is the easier bulk route. Same JSON as the API, narratives and problem words already inside each report.
- MAUDE raw files are smaller (about 8 GB vs 18 GB) but need joining 4-5 tables, cp1252 reading, and handling broken rows.
- Bulk only makes sense if the API route hits limits. The API can pull just CGM reports and skip about 23 million non-CGM reports.
- Use the full CGM code list, not just MDS/QBJ/QLG. PQF, PZE, QHJ, SAF, SBA, QDK are also CGMs. QFG is an insulin pump, not a CGM (it shows up next to Dexcom in many reports).
- Scale is large: about 3.4 million CGM reports. An LLM cannot read all of them. Plan to sample or pre-filter.
