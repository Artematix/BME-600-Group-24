# Where CGM problem reports come from (country spread)

Data: all FDA MAUDE reports for our 13 CGM product codes, via openFDA. Checked 2026-10-20.
MAUDE = FDA database of device problem reports. CGM = continuous glucose monitor.
Script: `scripts/country_spread.py` makes the tables (`tables/k_country_*.csv`) and the figure (`figures/fig7_foreign_countries.png`). This page is written by hand from the script output. The script does not change it.

## Method (plain words)

- Each report has a field `reporter_country_code`: the country of the person who reported the problem.
- openFDA cannot count this field directly. So we asked one search per 2-letter code (AA to ZZ, 676 searches) and read the number of matches.
- Every report has exactly one value. Check: the codes add up to 3,137,088. Blank = 244,983. Together = 3,382,071 = all reports. No double counting.
- About 1,300 API calls (plus about 200 test calls). All answers are saved in `k_country_api_cache.csv`, so the tables can be rebuilt with no new calls.

## Code check (important)

- The field mixes two code lists. FIPS = old US government list (GM = Germany, UK = United Kingdom). ISO = world standard (DE = Germany, GB = United Kingdom).
- Which list was used depends on the maker and the year (`k_country_code_list_by_maker_year.csv`):

| Maker | FIPS years | ISO years |
|---|---|---|
| Dexcom | up to 2021 | 2022 on (2026 mixed: 83% ISO) |
| Abbott | 2021 on | 2019-2020 partly (31-44% ISO) |
| Medtronic, Senseonics | all years | none |

- We added both codes for the same country (for example Germany = GM + DE).
- 17 codes mean different countries in the two lists. Sample reports did not help: the place is blacked out in the text.
- We decided by size and by which list the maker used. Example: GB = United Kingdom, not Gabon. Reasons for each code: `k_country_codes.csv`.
- AU (Austria in FIPS, Australia in ISO) and CH (China in FIPS, Switzerland in ISO) are used both ways. We split them by maker and month, using that maker's FIPS/ISO share. guess: a few hundred reports may sit in the wrong one of the two countries.
- TC is in neither modern list. It is the old FIPS code for United Arab Emirates (used before 1998). We counted it as UAE.
- 10 tiny two-meaning codes (under 35 reports each) were left as "X or Y". 3 unknown codes (SR, FK, LQ; 11 reports) were left as unknown.

## Result 1: US vs not US

| Group | All reports | % | Death + injury | % |
|---|---|---|---|---|
| United States | 2,156,966 | 63.8 | 54,811 | 44.3 |
| Other countries (incl. 49 from US territories) | 980,122 | 29.0 | 62,478 | 50.5 |
| Blank country | 244,983 | 7.2 | 6,318 | 5.1 |
| Total | 3,382,071 | 100 | 123,607 | 100 |

- Non-US reports are a bigger share of death + injury reports (50.5%) than of all reports (29.0%).
- Death + injury per 1,000 reports: US 25.4. Germany 49.4. UK 79.4. France 102.4. Spain 159.0.
- guess: other countries may have different rules on what must be reported, so this does not mean sensors are worse there.

## Result 2: top 10 countries outside the US

% = share of all non-US reports (980,122 all; 62,478 death + injury).

| Rank | All reports | % | Death + injury | % |
|---|---|---|---|---|
| 1 | Germany | 26.3 | Germany | 20.4 |
| 2 | United Kingdom | 11.0 | France | 14.1 |
| 3 | Canada | 9.4 | United Kingdom | 13.7 |
| 4 | France | 8.8 | Spain | 9.9 |
| 5 | Italy | 5.2 | Italy | 6.3 |
| 6 | Australia | 4.1 | Canada | 5.5 |
| 7 | Spain | 4.0 | Poland | 5.0 |
| 8 | Poland | 3.2 | Netherlands | 3.5 |
| 9 | Sweden | 3.0 | Brazil | 2.3 |
| 10 | Switzerland | 2.8 | Sweden | 1.5 |

- 121 groups in total (countries, areas, a few unclear codes). Top 20: `k_country_top20_non_us_*.csv`.

## Result 3: by maker and by year

| Maker (search on maker name) | Reports | % not US or blank |
|---|---|---|
| Dexcom | 2,506,875 | 23.6 |
| Abbott | 724,396 | 77.0 |
| Medtronic | 135,248 | 51.9 |
| Senseonics | 7,767 | 26.3 |

- Maker mix per country (top 12 countries): `k_country_by_maker.csv`. Example: Germany 52% Dexcom, 46% Abbott.
- By year received (`k_country_by_year.csv`): other countries were about 5-18% of reports from 2010 to 2020. They were 27-30% in 2022-2025 and 50.0% in 2026.
- guess: the 2026 jump is mostly Abbott. Abbott alone has 93,544 Germany (GM) reports received in 2026.
- Blank country is mostly 2012-2014 (78-95% blank) and 2021 (20% blank).

## Check against the "Foreign" source flag

- `source_type` = who sent the report. One option is "Foreign".
| Reporter country | Reports | % flagged Foreign |
|---|---|---|
| United States, all | 2,156,966 | 0.5 |
| Not US, all | 980,122 | 56.1 |
| United States, death + injury | 54,811 | 0.5 |
| Not US, death + injury | 62,478 | 9.0 |

- The two fields mostly agree on the US.
- But the Foreign flag misses about 44% of non-US reports, and 91% of non-US death + injury reports.
- So the Foreign flag (596,247 reports) is a poor way to count non-US reports. Use the country field.

## Limits

- Reporter country = where the reporter is. guess: almost always where the event happened, but this is not guaranteed.
- MAUDE only has foreign reports for devices also sold in the US. This is NOT the world spread of CGM problems.
- More reports in a country can mean more users or stricter reporting rules, not worse sensors.
- 7.2% of reports have a blank country.
- The mixed code lists add some error (see "Code check").
- Our saved raw files do not have this field yet. Re-pulling the full set (about 4,100 calls, about 1 hour) would give the country per report.
