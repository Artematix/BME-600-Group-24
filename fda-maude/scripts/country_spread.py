"""
Country spread of CGM problem reports (FDA MAUDE), for BMEN 600 Group 24.

What it does (plain words):
- Asks the openFDA web service how many CGM reports have each value of the field
  `reporter_country_code` (the country of the person who reported the event).
- openFDA cannot "count" this field directly, so the script asks one question per
  2-letter code (AA, AB, ... ZZ) and reads the total number of matches.
- Then it builds tables and one figure, and prints a summary to the screen.
- The write-up results/report/country_spread.md is written by hand from that
  output. The script does not write or change it.

How to run (from the fda-maude folder):
    py -3.11 scripts/country_spread.py fetch    (asks the API; answers are cached)
    py -3.11 scripts/country_spread.py report   (tables + figure, no API)

The API key is read from the Windows user setting OPENFDA_API_KEY.
It is sent in a hidden header (basic auth), never in the address, never saved.
All API answers are cached in results/report/tables/k_country_api_cache.csv,
so a second run makes no new calls.
"""

import csv
import itertools
import os
import string
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
API = "https://api.fda.gov/device/event.json"
CODES = ["QBJ", "PQF", "MDS", "QLG", "PZE", "SFI", "SBA", "SAF", "QHJ", "QCD", "QDK", "QII", "SBH"]
BASE = "device.device_report_product_code:(" + "+".join(CODES) + ")"
SERIOUS = "event_type:(Death+Injury)"
FOREIGN = "source_type:(foreign+foreig)"
MAKERS = {"Dexcom": "device.manufacturer_d_name:dexcom",
          "Abbott": "device.manufacturer_d_name:abbott",
          "Medtronic": "device.manufacturer_d_name:medtronic",
          "Senseonics": "device.manufacturer_d_name:senseonics"}
OUT = ROOT / "results" / "report"
TAB = OUT / "tables"
FIG = OUT / "figures"
CACHE = TAB / "k_country_api_cache.csv"
MIN_GAP = 0.55  # seconds between calls (under 2 calls per second)


# ---------------------------------------------------------------- API + cache

def api_key():
    k = os.environ.get("OPENFDA_API_KEY")
    if k or os.name != "nt":
        return k
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            return winreg.QueryValueEx(h, "OPENFDA_API_KEY")[0]
    except OSError:
        return None


class Api:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "bmen600-group24-country-spread"
        key = api_key()
        if key:
            self.s.auth = (key, "")
        self.last = 0.0
        self.calls = 0
        self.cache = {}
        if CACHE.exists():
            with open(CACHE, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    self.cache.setdefault(r["query_id"], {})[r["term"]] = int(r["count"])
        new = not CACHE.exists()
        TAB.mkdir(parents=True, exist_ok=True)
        self.f = open(CACHE, "a", newline="", encoding="utf-8")
        self.w = csv.writer(self.f, lineterminator="\n")
        if new:
            self.w.writerow(["query_id", "search", "count_field", "term", "count"])

    def _get(self, search, count=None):
        url = API + "?search=" + quote(search, safe=':+[]"()*.-_')
        url += ("&count=" + count) if count else "&limit=1"
        wait = 5
        for attempt in range(6):
            gap = time.time() - self.last
            if gap < MIN_GAP:
                time.sleep(MIN_GAP - gap)
            self.last = time.time()
            self.calls += 1
            try:
                r = self.s.get(url, timeout=120)
            except requests.RequestException:
                time.sleep(wait); wait *= 2
                continue
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(wait); wait *= 2
                continue
            raise RuntimeError(f"HTTP {r.status_code} for search={search} count={count}")
        raise RuntimeError(f"gave up: search={search} count={count}")

    def total(self, qid, search):
        """Number of reports that match the search (cached)."""
        if qid in self.cache:
            return self.cache[qid]["_total"]
        d = self._get(search)
        n = d["meta"]["results"]["total"] if d else 0
        self.cache[qid] = {"_total": n}
        self.w.writerow([qid, search, "", "_total", n]); self.f.flush()
        return n

    def count(self, qid, search, field):
        """openFDA count= answer, as {term: count} (cached)."""
        if qid in self.cache:
            return self.cache[qid]
        d = self._get(search, field)
        res = defaultdict(int)
        for x in (d or {}).get("results", []):
            if field == "date_received":  # days are added up to months, to keep the cache small
                res[str(x["time"])[:6]] += x["count"]
            else:
                res[str(x["term"])] += x["count"]
        res = dict(res) or {"_none": 0}
        self.cache[qid] = res
        label = "date_received (by month)" if field == "date_received" else field
        for j, (t, c) in enumerate(res.items()):
            self.w.writerow([qid, search if j == 0 else "", label, t, c])
        self.f.flush()
        return res


def cq(code):
    # quotes keep codes like "no", "in" from being read as words
    return f'reporter_country_code:"{code.lower()}"'


def all_codes():
    return ["".join(p) for p in itertools.product(string.ascii_uppercase, repeat=2)]


def fetch():
    api = Api()
    tot = api.total("base", BASE)
    print(f"all CGM reports: {tot:,}", flush=True)
    api.total("base_serious", f"{BASE}+AND+{SERIOUS}")
    api.total("base_foreign", f"{BASE}+AND+{FOREIGN}")
    api.total("base_serious_foreign", f"{BASE}+AND+{SERIOUS}+AND+{FOREIGN}")
    # round 1: every 2-letter code
    found = {}
    for i, c in enumerate(all_codes()):
        n = api.total(f"all_{c}", f"{BASE}+AND+{cq(c)}")
        if n:
            found[c] = n
        if (i + 1) % 100 == 0:
            print(f"  round 1: {i + 1}/676 codes, {len(found)} found, sum {sum(found.values()):,}, "
                  f"{api.calls} calls", flush=True)
    print(f"round 1 done: {len(found)} codes, sum {sum(found.values()):,} of {tot:,}", flush=True)
    # round 2: serious and foreign-flag counts for every code that has reports
    for c in found:
        api.total(f"serious_{c}", f"{BASE}+AND+{SERIOUS}+AND+{cq(c)}")
        api.total(f"foreign_{c}", f"{BASE}+AND+{FOREIGN}+AND+{cq(c)}")
        api.total(f"serious_foreign_{c}", f"{BASE}+AND+{SERIOUS}+AND+{FOREIGN}+AND+{cq(c)}")
    print(f"round 2 done, {api.calls} calls", flush=True)
    # round 3: makers for the 25 biggest codes and overall
    top = sorted(found, key=found.get, reverse=True)[:25]
    for m, s in MAKERS.items():
        api.total(f"maker_{m}", f"{BASE}+AND+{s}")
        api.total(f"maker_serious_{m}", f"{BASE}+AND+{SERIOUS}+AND+{s}")
        for c in top:
            api.total(f"maker_{m}_{c}", f"{BASE}+AND+{s}+AND+{cq(c)}")
    print(f"round 3 done, {api.calls} calls", flush=True)
    # round 4: reports per day received, all and per top code (summed to years later)
    api.count("days_all", BASE, "date_received")
    api.count("days_serious", f"{BASE}+AND+{SERIOUS}", "date_received")
    for c in top:
        api.count(f"days_{c}", f"{BASE}+AND+{cq(c)}", "date_received")
    print(f"round 4 done, {api.calls} calls", flush=True)
    # round 5: which code list each maker used, by month (Germany GM/DE, UK UK/GB),
    # and the two big two-meaning codes AU and CH split by maker and month
    for m, s in MAKERS.items():
        for c in ["GM", "DE", "UK", "GB", "AU", "CH"]:
            api.count(f"mdays_{m}_{c}", f"{BASE}+AND+{s}+AND+{cq(c)}", "date_received")
        for c in ["AU", "CH"]:
            api.count(f"mdays_serious_{m}_{c}", f"{BASE}+AND+{SERIOUS}+AND+{s}+AND+{cq(c)}", "date_received")
    for c in ["AU", "CH"]:
        api.count(f"days_serious_{c}", f"{BASE}+AND+{SERIOUS}+AND+{cq(c)}", "date_received")
    print(f"round 5 done, {api.calls} calls", flush=True)
    # round 6: reports with a blank country (NOT any of the codes found)
    blank = f"{BASE}+AND+NOT+reporter_country_code:(" + "+".join(f'"{c.lower()}"' for c in found) + ")"
    nb = api.total("blank", blank)
    api.total("blank_serious", blank.replace(BASE, f"{BASE}+AND+{SERIOUS}", 1))
    api.count("days_blank", blank, "date_received")
    print(f"round 6 done: blank {nb:,} (total minus sum = {tot - sum(found.values()):,}); "
          f"{api.calls} new calls this run", flush=True)


# ---------------------------------------------------------------- code -> country
# Two code systems are mixed in the field:
#   FIPS 10-4 (old US government list; GM = Germany, UK = United Kingdom, AS = Australia)
#   ISO 3166-1 (world standard; DE = Germany, GB = United Kingdom, AU = Australia)
# Most codes mean the same country in both, or exist in only one list.
# Where a code means two different countries, CONFLICT below says which one we chose and why.

def _parse(block):
    out = {}
    for part in block.split(";"):
        part = part.strip()
        if part:
            k, v = part.split("=")
            out[k.strip()] = v.strip()
    return out


FIPS = _parse("""
AA=Aruba; AC=Antigua and Barbuda; AE=United Arab Emirates; AF=Afghanistan; AG=Algeria; AJ=Azerbaijan;
AL=Albania; AM=Armenia; AN=Andorra; AO=Angola; AQ=American Samoa; AR=Argentina; AS=Australia; AU=Austria;
AV=Anguilla; BA=Bahrain; BB=Barbados; BC=Botswana; BD=Bermuda; BE=Belgium; BF=Bahamas; BG=Bangladesh;
BH=Belize; BK=Bosnia and Herzegovina; BL=Bolivia; BM=Myanmar; BN=Benin; BO=Belarus; BR=Brazil; BT=Bhutan;
BU=Bulgaria; BX=Brunei; BY=Burundi; CA=Canada; CB=Cambodia; CD=Chad; CE=Sri Lanka; CF=Congo; CG=DR Congo;
CH=China; CI=Chile; CJ=Cayman Islands; CM=Cameroon; CN=Comoros; CO=Colombia; CQ=Northern Mariana Islands;
CS=Costa Rica; CT=Central African Republic; CU=Cuba; CV=Cape Verde; CY=Cyprus; DA=Denmark; DJ=Djibouti;
DO=Dominica; DR=Dominican Republic; EC=Ecuador; EG=Egypt; EI=Ireland; EK=Equatorial Guinea; EN=Estonia;
ER=Eritrea; ES=El Salvador; ET=Ethiopia; EZ=Czech Republic; FG=French Guiana; FI=Finland; FJ=Fiji;
FO=Faroe Islands; FP=French Polynesia; FR=France; GA=Gambia; GB=Gabon; GG=Georgia; GH=Ghana; GI=Gibraltar;
GJ=Grenada; GK=Guernsey; GL=Greenland; GM=Germany; GP=Guadeloupe; GQ=Guam; GR=Greece; GT=Guatemala;
GV=Guinea; GY=Guyana; HA=Haiti; HK=Hong Kong; HO=Honduras; HR=Croatia; HU=Hungary; IC=Iceland; ID=Indonesia;
IM=Isle of Man; IN=India; IR=Iran; IS=Israel; IT=Italy; IV=Ivory Coast; IZ=Iraq; JA=Japan; JE=Jersey;
JM=Jamaica; JO=Jordan; KE=Kenya; KG=Kyrgyzstan; KN=North Korea; KS=South Korea; KU=Kuwait; KV=Kosovo;
KZ=Kazakhstan; LA=Laos; LE=Lebanon; LG=Latvia; LH=Lithuania; LI=Liberia; LO=Slovakia; LS=Liechtenstein;
LT=Lesotho; LU=Luxembourg; LY=Libya; MA=Madagascar; MB=Martinique; MC=Macau; MD=Moldova; MG=Mongolia;
MH=Montserrat; MI=Malawi; MJ=Montenegro; MK=North Macedonia; ML=Mali; MN=Monaco; MO=Morocco; MP=Mauritius;
MR=Mauritania; MT=Malta; MU=Oman; MV=Maldives; MX=Mexico; MY=Malaysia; MZ=Mozambique; NC=New Caledonia;
NG=Niger; NH=Vanuatu; NI=Nigeria; NL=Netherlands; NO=Norway; NP=Nepal; NS=Suriname; NT=Netherlands Antilles;
NU=Nicaragua; NZ=New Zealand; PA=Paraguay; PE=Peru; PK=Pakistan; PL=Poland; PM=Panama; PO=Portugal;
PP=Papua New Guinea; QA=Qatar; RE=Reunion; RI=Serbia; RM=Marshall Islands; RO=Romania; RP=Philippines;
RQ=Puerto Rico; RS=Russia; RW=Rwanda; SA=Saudi Arabia; SC=Saint Kitts and Nevis; SE=Seychelles;
SF=South Africa; SG=Senegal; SI=Slovenia; SL=Sierra Leone; SM=San Marino; SN=Singapore; SO=Somalia; SP=Spain;
ST=Saint Lucia; SU=Sudan; SW=Sweden; SY=Syria; SZ=Switzerland; TD=Trinidad and Tobago; TH=Thailand;
TI=Tajikistan; TK=Turks and Caicos; TN=Tonga; TO=Togo; TS=Tunisia; TU=Turkey; TW=Taiwan; TX=Turkmenistan;
TZ=Tanzania; UC=Curacao; UG=Uganda; UK=United Kingdom; UP=Ukraine; US=United States; UV=Burkina Faso;
UY=Uruguay; UZ=Uzbekistan; VC=Saint Vincent; VE=Venezuela; VI=British Virgin Islands; VM=Vietnam;
VQ=US Virgin Islands; VT=Vatican City; WA=Namibia; WE=West Bank; WS=Samoa; WZ=Eswatini; YM=Yemen;
ZA=Zambia; ZI=Zimbabwe
""")

ISO = _parse("""
AD=Andorra; AE=United Arab Emirates; AF=Afghanistan; AG=Antigua and Barbuda; AI=Anguilla; AL=Albania;
AM=Armenia; AO=Angola; AR=Argentina; AS=American Samoa; AT=Austria; AU=Australia; AW=Aruba; AZ=Azerbaijan;
BA=Bosnia and Herzegovina; BB=Barbados; BD=Bangladesh; BE=Belgium; BF=Burkina Faso; BG=Bulgaria; BH=Bahrain;
BJ=Benin; BM=Bermuda; BN=Brunei; BO=Bolivia; BR=Brazil; BS=Bahamas; BW=Botswana; BY=Belarus; BZ=Belize;
CA=Canada; CD=DR Congo; CH=Switzerland; CI=Ivory Coast; CL=Chile; CM=Cameroon; CN=China; CO=Colombia;
CR=Costa Rica; CU=Cuba; CW=Curacao; CY=Cyprus; CZ=Czech Republic; DE=Germany; DK=Denmark; DM=Dominica;
DO=Dominican Republic; DZ=Algeria; EC=Ecuador; EE=Estonia; EG=Egypt; ES=Spain; ET=Ethiopia; FI=Finland;
FJ=Fiji; FO=Faroe Islands; FR=France; GB=United Kingdom; GE=Georgia; GF=French Guiana; GG=Guernsey; GH=Ghana;
GI=Gibraltar; GL=Greenland; GP=Guadeloupe; GR=Greece; GT=Guatemala; GU=Guam; HK=Hong Kong; HN=Honduras;
HR=Croatia; HU=Hungary; ID=Indonesia; IE=Ireland; IL=Israel; IM=Isle of Man; IN=India; IQ=Iraq; IR=Iran;
IS=Iceland; IT=Italy; JE=Jersey; JM=Jamaica; JO=Jordan; JP=Japan; KE=Kenya; KR=South Korea; KW=Kuwait;
KY=Cayman Islands; KZ=Kazakhstan; LB=Lebanon; LI=Liechtenstein; LK=Sri Lanka; LT=Lithuania; LU=Luxembourg;
LV=Latvia; LY=Libya; MA=Morocco; MC=Monaco; MD=Moldova; ME=Montenegro; MK=North Macedonia; MO=Macau;
MQ=Martinique; MT=Malta; MU=Mauritius; MX=Mexico; MY=Malaysia; NC=New Caledonia; NG=Nigeria; NI=Nicaragua;
NL=Netherlands; NO=Norway; NP=Nepal; NZ=New Zealand; OM=Oman; PA=Panama; PE=Peru; PF=French Polynesia;
PH=Philippines; PK=Pakistan; PL=Poland; PR=Puerto Rico; PS=Palestine; PT=Portugal; PY=Paraguay; QA=Qatar;
RE=Reunion; RO=Romania; RS=Serbia; RU=Russia; SA=Saudi Arabia; SE=Sweden; SG=Singapore; SI=Slovenia;
SK=Slovakia; SM=San Marino; SV=El Salvador; SY=Syria; TH=Thailand; TN=Tunisia; TR=Turkey; TT=Trinidad and Tobago;
TW=Taiwan; UA=Ukraine; UG=Uganda; US=United States; UY=Uruguay; UZ=Uzbekistan; VE=Venezuela;
VG=British Virgin Islands; VI=US Virgin Islands; VN=Vietnam; XK=Kosovo; ZA=South Africa; ZM=Zambia;
ZW=Zimbabwe
""")

# Codes that mean different countries in the two lists, and the one we chose.
# Filled in after checking sample reports (see country_spread.md, "Code check").
# Checked 2026-10-20: sample reports name no country (the place is blacked out), so we used
# (a) size: a tiny country cannot have thousands of CGM reports, and
# (b) which list the maker used at that time (round 5: Germany as GM or DE, UK as UK or GB).
CONFLICT = {
    "GB": ("United Kingdom", "Gabon is too small; GB is used next to DE by the same makers"),
    "AS": ("Australia", "American Samoa is too small"),
    "SE": ("Sweden", "Seychelles is too small"),
    "ES": ("Spain", "El Salvador is too small; ES rises with DE and GB"),
    "IS": ("Israel", "Iceland is too small for 7,000 reports; ISO Israel (IL) appears only later"),
    "RS": ("Russia", "used by Abbott and Medtronic, both on the FIPS list then; Serbia is too small"),
    "CN": ("China", "Comoros is too small"),
    "ZA": ("South Africa", "Zambia is too small; used by Dexcom in its ISO years"),
    "CI": ("Chile", "used by makers on the FIPS list; Ivory Coast unlikely"),
    "SG": ("Singapore", "used by Dexcom in its ISO years; Senegal unlikely"),
    "MU": ("Oman", "used mostly by Abbott in its FIPS years; Mauritius unlikely"),
    "BA": ("Bahrain", "used by Abbott and Medtronic in FIPS years"),
    "LT": ("Lithuania", "used by Dexcom in 2022 (ISO year); Lesotho is too small"),
    "BG": ("Bulgaria", "used by Dexcom in 2022+ (ISO years); Bangladesh unlikely"),
    "TC": ("United Arab Emirates", "old FIPS code for UAE (before 1998, 'Trucial States'); "
                                   "ISO TC = Turks and Caicos is too small"),
}
# Two big codes that really are used both ways. Split by maker and month (see split_code()).
SPLIT = {"AU": ("Austria", "Australia"),          # (FIPS meaning, ISO meaning)
         "CH": ("China", "Switzerland")}

US_TERRITORIES = {"Puerto Rico", "Guam", "US Virgin Islands", "American Samoa", "Northern Mariana Islands"}


def country_of(code):
    """Returns (country name, how decided)."""
    if code in CONFLICT:
        return CONFLICT[code][0], "two meanings; " + CONFLICT[code][1]
    f, i = FIPS.get(code), ISO.get(code)
    if f and i:
        return (f, "same in FIPS and ISO") if f == i else (f + " or " + i, "two meanings; not checked")
    if f:
        return f, "FIPS only"
    if i:
        return i, "ISO only"
    return "Unknown code " + code, "in neither list"


# ---------------------------------------------------------------- report

def pct(a, b):
    return round(100 * a / b, 2) if b else 0.0


def _years(d):
    """Monthly (or daily) counts -> {year: count}."""
    out = defaultdict(int)
    for k, v in d.items():
        if k[:4].isdigit():
            out[int(k[:4])] += v
    return out


def report():
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    api = Api()
    C = api.cache
    T = lambda q: C.get(q, {}).get("_total", 0)
    tot, tot_s = T("base"), T("base_serious")
    codes = [c for c in all_codes() if T(f"all_{c}") > 0]

    # ISO share per maker and month: how often a maker wrote Germany/UK as DE/GB (ISO)
    # instead of GM/UK (FIPS). Used to split AU and CH.
    iso_share, sysrows = {}, []
    for m in MAKERS:
        months = sorted({t for c in ["GM", "DE", "UK", "GB"] for t in C.get(f"mdays_{m}_{c}", {}) if t.isdigit()})
        for ym in months:
            f = sum(C.get(f"mdays_{m}_{c}", {}).get(ym, 0) for c in ["GM", "UK"])
            i = sum(C.get(f"mdays_{m}_{c}", {}).get(ym, 0) for c in ["DE", "GB"])
            iso_share[(m, ym)] = i / (f + i) if f + i else 0.0
            sysrows.append({"maker": m, "year": ym[:4], "fips_GM_UK": f, "iso_DE_GB": i})
    sy = pd.DataFrame(sysrows).groupby(["maker", "year"]).sum().reset_index()
    sy["pct_iso"] = [pct(i, f + i) for f, i in zip(sy.fips_GM_UK, sy.iso_DE_GB)]
    sy.to_csv(TAB / "k_country_code_list_by_maker_year.csv", index=False)

    def split_code(c, prefix):
        """Split one two-meaning code into (FIPS part, ISO part) by maker and month.
        Reports from no listed maker (very few) go to the FIPS part."""
        fips = iso = 0.0
        yf, yi = defaultdict(float), defaultdict(float)
        for m in MAKERS:
            for ym, n in C.get(f"mdays_{prefix}{m}_{c}", {}).items():
                if not ym.isdigit():
                    continue
                sh = iso_share.get((m, ym), 0.0)
                iso += n * sh; fips += n * (1 - sh)
                yi[int(ym[:4])] += n * sh; yf[int(ym[:4])] += n * (1 - sh)
        tot_c = T(f"{'serious_' if prefix else 'all_'}{c}")
        fips += tot_c - fips - iso  # the rest
        return fips, iso, yf, yi

    # 1. one row per code (AU and CH become two rows each)
    rows, row_years = [], {}
    for c in codes:
        base_row = {"fips_meaning": FIPS.get(c, ""), "iso_meaning": ISO.get(c, ""),
                    "flagged_foreign": T(f"foreign_{c}"), "death_injury_flagged_foreign": T(f"serious_foreign_{c}")}
        mk_c = {m: C[f"maker_{m}_{c}"]["_total"] for m in MAKERS if f"maker_{m}_{c}" in C}
        if c in SPLIT:
            fa, ia, yf, yi = split_code(c, "")
            fs, is_, _, _ = split_code(c, "serious_")
            for part, name, n, ns, yy in [("FIPS", SPLIT[c][0], fa, fs, yf), ("ISO", SPLIT[c][1], ia, is_, yi)]:
                share = n / T(f"all_{c}")
                r = dict(base_row, code=c, part=part, country=name,
                         how_decided="two meanings, both used; split by maker and month",
                         reports=round(n), death_injury_reports=round(ns))
                r["flagged_foreign"] = round(r["flagged_foreign"] * share)
                r["death_injury_flagged_foreign"] = round(r["death_injury_flagged_foreign"] * share)
                for m in MAKERS:
                    yrs_m = 0.0
                    for ym, k in C.get(f"mdays_{m}_{c}", {}).items():
                        if ym.isdigit():
                            sh = iso_share.get((m, ym), 0.0)
                            yrs_m += k * (sh if part == "ISO" else 1 - sh)
                    r[f"maker_{m}"] = round(yrs_m)
                rows.append(r); row_years[(c, name)] = yy
        else:
            name, how = country_of(c)
            r = dict(base_row, code=c, part="", country=name, how_decided=how,
                     reports=T(f"all_{c}"), death_injury_reports=T(f"serious_{c}"))
            for m in MAKERS:
                r[f"maker_{m}"] = mk_c.get(m)
            rows.append(r)
            if f"days_{c}" in C:
                row_years[(c, name)] = _years(C[f"days_{c}"])
    dc = pd.DataFrame(rows).sort_values("reports", ascending=False)
    cols = ["code", "part", "country", "how_decided", "fips_meaning", "iso_meaning", "reports",
            "death_injury_reports", "flagged_foreign", "death_injury_flagged_foreign"] + [f"maker_{m}" for m in MAKERS]
    dc = dc[cols]
    dc.to_csv(TAB / "k_country_codes.csv", index=False)
    sum_all, sum_s = int(dc["reports"].sum()), int(dc["death_injury_reports"].sum())

    # 2. one row per country (codes from both lists added together)
    g = dc.groupby("country").agg(codes=("code", lambda x: "+".join(x)), reports=("reports", "sum"),
                                  death_injury_reports=("death_injury_reports", "sum"),
                                  flagged_foreign=("flagged_foreign", "sum")).reset_index()
    us = g[g.country == "United States"]
    us_all = int(us.reports.sum()); us_s = int(us.death_injury_reports.sum())
    non = g[g.country != "United States"].copy()
    non_all, non_s = int(non.reports.sum()), int(non.death_injury_reports.sum())
    g["pct_of_all_reports"] = g.reports.map(lambda v: pct(v, tot))
    g["pct_of_non_us_reports"] = [pct(v, non_all) if c != "United States" else None for c, v in zip(g.country, g.reports)]
    g["pct_of_all_death_injury"] = g.death_injury_reports.map(lambda v: pct(v, tot_s))
    g["pct_of_non_us_death_injury"] = [pct(v, non_s) if c != "United States" else None
                                       for c, v in zip(g.country, g.death_injury_reports)]
    g["death_injury_per_1000_reports"] = [round(1000 * s / r, 1) if r else None
                                          for s, r in zip(g.death_injury_reports, g.reports)]
    g["pct_flagged_foreign"] = [pct(f, r) for f, r in zip(g.flagged_foreign, g.reports)]
    g = g.sort_values("reports", ascending=False)
    g.to_csv(TAB / "k_country_by_country.csv", index=False)

    # 3. US vs not US
    terr = g[g.country.isin(US_TERRITORIES)]
    rest = g[(g.country != "United States") & ~g.country.isin(US_TERRITORIES)]
    uv = pd.DataFrame([
        {"group": "United States", "reports": us_all, "death_injury_reports": us_s},
        {"group": "US territories (Puerto Rico, Guam, ...)", "reports": int(terr.reports.sum()),
         "death_injury_reports": int(terr.death_injury_reports.sum())},
        {"group": "Other countries", "reports": int(rest.reports.sum()),
         "death_injury_reports": int(rest.death_injury_reports.sum())},
        {"group": "Blank country field", "reports": T("blank"), "death_injury_reports": T("blank_serious")},
    ])
    uv.loc[len(uv)] = {"group": "Total", "reports": tot, "death_injury_reports": tot_s}
    uv["pct_of_reports"] = uv.reports.map(lambda v: pct(v, tot))
    uv["pct_of_death_injury"] = uv.death_injury_reports.map(lambda v: pct(v, tot_s))
    uv.to_csv(TAB / "k_country_us_vs_non_us.csv", index=False)

    # 4. top 20 non-US + other, for all and for death + injury
    def top_table(col, total_non):
        t = non.sort_values(col, ascending=False)
        top, other = t.head(20), t.iloc[20:]
        out = [{"rank": i + 1, "country": r.country, "codes": r.codes, "reports": int(r[col]),
                "pct_of_non_us": pct(r[col], total_non)} for i, (_, r) in enumerate(top.iterrows())]
        out.append({"rank": "", "country": f"Other ({len(other)} countries/areas)", "codes": "",
                    "reports": int(other[col].sum()), "pct_of_non_us": pct(other[col].sum(), total_non)})
        out.append({"rank": "", "country": "All non-US", "codes": "", "reports": total_non, "pct_of_non_us": 100.0})
        return pd.DataFrame(out)
    ta = top_table("reports", non_all)
    ts = top_table("death_injury_reports", non_s)
    ta.to_csv(TAB / "k_country_top20_non_us_all.csv", index=False)
    ts.to_csv(TAB / "k_country_top20_non_us_death_injury.csv", index=False)

    # 5. cross-check with the "Foreign" source flag
    f_all, f_s = T("base_foreign"), T("base_serious_foreign")
    us_f = int(us.flagged_foreign.sum())
    us_fs = int(dc[dc.country == "United States"].death_injury_flagged_foreign.sum())
    non_f = int(non.flagged_foreign.sum())
    non_fs = int(dc[dc.country != "United States"].death_injury_flagged_foreign.sum())
    ff = pd.DataFrame([
        {"reporter_country": "United States", "set": "all", "reports": us_all, "flagged_foreign": us_f},
        {"reporter_country": "Not United States", "set": "all", "reports": non_all, "flagged_foreign": non_f},
        {"reporter_country": "United States", "set": "death+injury", "reports": us_s, "flagged_foreign": us_fs},
        {"reporter_country": "Not United States", "set": "death+injury", "reports": non_s, "flagged_foreign": non_fs},
    ])
    ff["not_flagged"] = ff.reports - ff.flagged_foreign
    ff["pct_flagged_foreign"] = [pct(a, b) for a, b in zip(ff.flagged_foreign, ff.reports)]
    ff.to_csv(TAB / "k_country_foreign_flag_check.csv", index=False)

    # 6. maker split for the biggest countries (only codes that had maker searches)
    mk = []
    for country in ["United States"] + list(non.sort_values("reports", ascending=False).country.head(12)):
        sub = dc[(dc.country == country) & dc["maker_Dexcom"].notna()]
        if sub.empty:
            continue
        r = {"country": country, "codes_used": "+".join(sub.code), "reports": int(sub.reports.sum())}
        for m in MAKERS:
            r[m] = int(sub[f"maker_{m}"].sum())
        r["Other_or_overlap"] = r["reports"] - sum(r[m] for m in MAKERS)
        for m in list(MAKERS) + ["Other_or_overlap"]:
            r[f"{m}_pct"] = pct(r[m], r["reports"])
        mk.append(r)
    dm = pd.DataFrame(mk)
    dm.to_csv(TAB / "k_country_by_maker.csv", index=False)
    # whole data set: share of each maker's reports that come from outside the US
    mk2 = []
    us_codes = list(dc[dc.country == "United States"].code)
    for m in MAKERS:
        mt = T(f"maker_{m}")
        mu = int(sum(T(f"maker_{m}_{c}") for c in us_codes))
        mk2.append({"maker": m, "reports": mt, "reporter_in_us": mu, "reporter_not_us_or_blank": mt - mu,
                    "pct_not_us_or_blank": pct(mt - mu, mt), "death_injury_reports": T(f"maker_serious_{m}")})
    dm2 = pd.DataFrame(mk2)
    dm2.to_csv(TAB / "k_country_maker_non_us_share.csv", index=False)

    # 7. by year received
    ya = _years(C["days_all"])
    ysa = _years(C["days_serious"])
    yb = _years(C.get("days_blank", {}))
    yus = defaultdict(int)
    for c in us_codes:
        for y, n in _years(C.get(f"days_{c}", {})).items():
            yus[y] += n
    top5 = list(non.sort_values("reports", ascending=False).country.head(5))
    ytop = {k: defaultdict(float) for k in top5}
    for (c, name), yy in row_years.items():
        if name in ytop:
            for y, n in yy.items():
                ytop[name][y] += n
    missing = [k for k in top5 if not any(nm == k for (_, nm) in row_years)]
    yr = []
    for y in sorted(ya):
        nb_y = yb.get(y, 0)
        r = {"year_received": y, "reports": ya[y], "death_injury_reports": ysa.get(y, 0),
             "us": yus[y], "other_countries": ya[y] - yus[y] - nb_y, "blank": nb_y,
             "pct_us": pct(yus[y], ya[y]), "pct_other_countries": pct(ya[y] - yus[y] - nb_y, ya[y]),
             "pct_blank": pct(nb_y, ya[y])}
        for k in top5:
            r[f"pct_{k}"] = pct(ytop[k][y], ya[y])
        yr.append(r)
    dy = pd.DataFrame(yr)
    dy.to_csv(TAB / "k_country_by_year.csv", index=False)
    if missing:
        print("warning: no monthly data for", missing)

    # 8. figure: top 15 non-US countries, % of non-US reports
    INK, INK2, MUTED, GRID, BLUE = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#2a78d6"
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.labelsize": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2,
        "ytick.color": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "savefig.dpi": 300, "savefig.bbox": "tight"})
    t15 = ta.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 5.6))
    ax.barh(t15.country, t15.pct_of_non_us, color=BLUE, height=0.65)
    ax.grid(axis="y", visible=False)
    for y, (v, n) in enumerate(zip(t15.pct_of_non_us, t15.reports)):
        ax.text(v + 0.3, y, f"{v:.1f}%  ({n:,})", va="center", fontsize=8.5, color=INK2)
    ax.set_xlim(0, t15.pct_of_non_us.max() * 1.3)
    ax.set_xlabel(f"Share of reports from outside the US (%)   [all non-US reports = {non_all:,}]")
    ax.set_title("Where CGM problem reports come from, outside the US", loc="left")
    ax.text(0, -0.13, f"Source: FDA MAUDE via openFDA, 13 CGM product codes, all years. Country = reporter country field. "
            f"US = {pct(us_all, tot):.1f}% and blank country = {pct(T('blank'), tot):.1f}% of all reports (not shown).", transform=ax.transAxes, fontsize=7.5, color=MUTED)
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / "fig7_foreign_countries.png", facecolor="white")
    plt.close(fig)

    # console summary for the person running it
    print(f"total {tot:,}; codes found {len(codes)}; sum over codes {sum_all:,} (gap {tot - sum_all:,})")
    print(f"serious {tot_s:,}; sum over codes {sum_s:,} (gap {tot_s - sum_s:,})")
    print(uv.to_string(index=False))
    print(ta.to_string(index=False))
    print(ts.to_string(index=False))
    print(ff.to_string(index=False))
    print(dm.to_string(index=False))
    print(dm2.to_string(index=False))
    print(dy.to_string(index=False))
    print(dc[dc.how_decided.str.startswith("two") | dc.how_decided.str.startswith("in neither")].to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "fetch":
        fetch()
    elif cmd == "report":
        report()
    else:
        print(__doc__)
