#!/usr/bin/env python
"""
extract_regex.py : the pattern layer of the MAUDE text step (Phase 1, BMEN 600 Group 24).

What it does
- Reads MAUDE reports. Input is JSONL (API shape, e.g. data/sample_narratives.jsonl)
  or CSV / CSV.GZ (clean shape, e.g. clean/serious.csv.gz).
- Joins the two narratives: D5 "Description of Event or Problem" and
  H10 "Additional Manufacturer Narrative" (labelled, see build_text).
- Runs fixed text patterns (regex) that read the maker templates and simple prose.
- Writes one row per report: the schema fields the patterns can fill, plus the
  matched text for audit.
- Prints hit rates per maker and per event type (also saved as *_hitrates.md).

Usage
  python fda-maude/scripts/extract_regex.py INPUT OUTPUT.csv [--limit N]
  INPUT  = fda-maude/data/sample_narratives.jsonl   or   fda-maude/clean/serious.csv.gz
  OUTPUT = fda-maude/results/text/regex_sample.csv

Schema fields written
  sensor_value_mgdl, meter_value_mgdl : first stated sensor/meter pair, in mg/dL
                                        (mmol/L is multiplied by 18 and flagged)
  multiple_pairs                      : yes / no
  parkes_zone_stated                  : A to E, or empty
  wear_day                            : whole number, or empty
  regex_template                      : abbott_template / dexcom_bg / none
                                        (dexcom_bg = prose "CGM value vs BG value" in one
                                        sentence or two neighbouring sentences, any maker)
Other columns: units, all values found, keyword flags, redaction counts and the matched
substrings (match_*). See OUTPUT_COLUMNS.

Other scripts import: load_reports(), build_text(), extract_report().
"""

import argparse
import collections
import csv
import gzip
import json
import re
import sys
import time
from pathlib import Path

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
D5_LABEL = "[D5 DESCRIPTION OF EVENT]"
H10_LABEL = "[H10 MANUFACTURER NARRATIVE]"
MMOL_FACTOR = 18.0            # mmol/L -> mg/dL
MAX_WEAR_DAY = 30             # a wear day above this is dropped and flagged
PLAUSIBLE_MGDL = (10, 1500)   # values outside are kept but flagged (value_flag)
LOOKBACK_CHARS = 80           # how far back from a number we look for a role word
MAX_TEXT_CHARS = 20000        # safety cap per report for the regex pass

OUTPUT_COLUMNS = [
    "mdr_report_key", "maker", "brand_name", "event_type",
    # schema fields
    "sensor_value_mgdl", "meter_value_mgdl", "multiple_pairs", "parkes_zone_stated", "wear_day",
    "regex_template",
    # extra fields about the numbers
    "pair_found", "pair_scope", "sensor_unit", "meter_unit", "mmol_converted",
    "sensor_value_raw", "meter_value_raw", "sensor_values_all", "meter_values_all",
    "other_values_all", "n_pairs", "sensor_display_word", "sensor_lower_than_meter", "value_flag",
    # keyword flags (mentions only, not facts)
    "kw_meter_mentioned", "kw_ems_or_hospital", "kw_death_real", "kw_no_harm_boilerplate",
    # text facts
    "n_b4", "n_b6", "text_chars",
    # audit
    "match_sensor", "match_meter", "match_pair_sentence", "match_zone", "match_wear",
]

# ----------------------------------------------------------------------------
# Patterns (one readable block). All matching is done on UPPERCASE text.
# ----------------------------------------------------------------------------
# A glucose number: 80 | 80.00 | 5.6 | 1,000 | 5,6 (decimal comma)
NUM = r"\d{1,4}(?:[.,]\d{1,3})?"
# Optional qualifier before a number: "over 600", "greater than 1,000", "approximately 400"
QUAL = (r"(?:(?:GREATER\s+THAN|MORE\s+THAN|LESS\s+THAN|OVER|ABOVE|BELOW|UNDER|APPROXIMATELY|"
        r"APPROX\.?|ABOUT|AROUND|NEARLY|ALMOST|>|<)\s*)?")
# Units. "MG/DL" and "MMOL/L" with any spacing. "400+ MG/DL" also allowed.
UNIT = r"(?:MG\s*/\s*DL|MMOL\s*/\s*L|MMOL\b)"
VAL = rf"{QUAL}{NUM}\s*\+?\s*{UNIT}"
# List separators: "40 MG/DL,40 MG/DL" | "140 MG/DL, 127 MG/DL, AND 159 MG/DL" | "115 AND 130 MG/DL"
SEP = r"\s*(?:,\s*(?:AND\s+|OR\s+)?|(?:AND|OR)\s+|/\s*|;\s*)"
LIST = rf"{VAL}(?:{SEP}{VAL})*"
RE_LIST = re.compile(LIST)
RE_VAL = re.compile(rf"({QUAL})({NUM})\s*(\+?)\s*({UNIT})")

# Numbers WITHOUT a unit, only right after a clear "reading/value/BG ... was/of" phrase.
# Example: "THE CGM SAYS THE GLUCOSE IS 100 BUT THE ACTUAL BLOOD GLUCOSE IS 40".
RE_VAL_UNITLESS = re.compile(
    r"\b(?:READINGS?|RESULTS?|VALUES?|LEVELS?|GLUCOSE|BG|FSBG|BGM|NUMBER|SUGAR)\s+"
    r"(?:OF|WAS|WERE|IS|AT|READ|SHOWED|SHOWING|MEASURED|DISPLAYED|OVER|ABOVE|BELOW|UNDER)\s+"
    + QUAL +
    r"(\d{2,4})\b(?!\s*(?:MG|MMOL|%|:|AM|PM|UNITS?|DAYS?|HOURS?|MINUTES?|YEARS?|MONTHS?|WEEKS?|TIMES|POINTS?|/|-|G\b))"
)

# Abbott malfunction template, sensor first:
#   "SENSOR SCAN RESULTS OF 62 MG/DL COMPARED TO READINGS OF 293 MG/DL ... OBTAINED ON A METER"
#   "A SENSOR RESULT OF 304 MG/DL WAS COMPARED TO AN ADC METER READING OF 44 MG/DL"
#   "A LOW SCAN OF 56 MG/DL ON THE ... DEVICE COMPARED TO A COMPETITOR BRAND METER RESULT OF 318 MG/DL"
#   "SENSOR SCAN OF 2.30 MMOL/L, 2.40 MMOL/L WAS COMPARED TO A BLOOD GLUCOSE TEST ... WITH A RESULT OF 12.30 MMOL/L, 10 MMOL/L"
ABBOTT_SENSOR_ANCHOR = (
    r"(?:SENSOR\s+(?:SCAN\s+)?(?:RESULTS?|READINGS?|VALUES?)\s+OF|SENSOR\s+SCANS?\s+OF|"
    r"(?:LOW(?:ER)?|HIGH(?:ER)?|ERRONEOUS)\s+SCANS?(?:\s+RESULTS?)?\s+OF|SCAN\s+RESULTS?\s+OF)"
)
ABBOTT_METER_ANCHOR = r"(?:READINGS?|RESULTS?|VALUES?)\s+OF"
RE_ABBOTT_PAIR = re.compile(
    ABBOTT_SENSOR_ANCHOR + r"\s*[\"']?\s*(?P<sensor>" + LIST + r")[\"']?"
    r"[^.]{0,120}?\bCOMPARED\s+(?:TO|WITH)\s+[^.]{0,90}?\b" + ABBOTT_METER_ANCHOR +
    r"\s*[\"']?\s*(?P<meter>" + LIST + r")"
)
# Same template, meter written first (rare)
RE_ABBOTT_PAIR_REV = re.compile(
    r"METER\s+(?:READINGS?|RESULTS?)\s+OF\s*(?P<meter>" + LIST + r")"
    r"[^.]{0,120}?\bCOMPARED\s+(?:TO|WITH)\s+[^.]{0,60}?\b" + ABBOTT_SENSOR_ANCHOR +
    r"\s*[\"']?\s*(?P<sensor>" + LIST + r")"
)
# Template with the meter value missing: "... COMPARED TO UNSPECIFIED READINGS"
RE_ABBOTT_SENSOR_ONLY = re.compile(
    ABBOTT_SENSOR_ANCHOR + r"\s*[\"']?\s*(?P<sensor>" + LIST + r")[\"']?"
    r"[^.]{0,120}?\bCOMPARED\s+(?:TO|WITH)\s+(?:AN?\s+)?(?:UNSPECIFIED|UNKNOWN|NO)\b"
)

# Role words for prose (Dexcom, Medtronic, Abbott serious reports).
# "strong" words decide the role of the nearest number. "weak" words only count if no strong word is near.
# "block" words mean the number is not a glucose comparison (ketones, insulin units, ranges...).
ROLE_WORDS = [
    ("sensor", "strong", re.compile(
        r"\bCGM\b|\bSENSORS?\b|\bSENSOR'S\b|\bSCAN(?:S|NED|NING)?\b|\bSG\b|\bDEXCOM\b|\bLIBRE\b|"
        r"\bGUARDIAN\b|\bRECEIVER\b|\bREADER\b|\bTRANSMITTER\b|\bPUMP\b")),   # Medtronic: the pump shows the sensor value
    ("meter", "strong", re.compile(
        r"\bBG\b|\bBGM\b|\bFSBG\b|\bFINGER\s*-?\s*STICKS?\b|\bFINGER\s*-?\s*PRICKS?\b|\bMETERS?\b|"
        r"\bGLUCOMETER\b|\bLAB(?:ORATORY)?\b|\bCAPILLARY\b|\bPOC\b|\bEMS\b|\bPARAMEDICS?\b")),
    ("meter", "weak", re.compile(
        r"\bBLOOD\s+GLUCOSE\b|\bBLOOD\s+SUGARS?\b|\bACTUAL\b|\bTRUE\b|\bVENOUS\b|\bSERUM\b|\bPLASMA\b")),
    ("block", "strong", re.compile(
        r"\bKETONES?\b|\bA1C\b|\bHBA1C\b|\bINSULIN\b|\bUNITS?\b|\bRANGE\b|\bRANGING\b|\bOUTSIDE\b|"
        r"\bBETWEEN\b|\bTARGET\b|\bTHRESHOLD\b|\bALERT\s+(?:SET|LEVEL)\b|\bPER\s+MINUTE\b|\bWEIGH(?:S|ED|T)\b")),
]
RE_AFTER_BLOCK = re.compile(r"^\s*(?:PER\s+MIN|RANGE|\)\s*RANGE|TARGET|ALERT)")   # right after the unit
RE_RANGE_BEFORE = re.compile(r"\d\s*[-]?\s*$")   # "40-50 MG/DL" or "40 400 MG/DL": a number just before

# Sensor shows a word instead of a number: "THE CGM CONTINUED TO DISPLAY LOW"
RE_DISPLAY_WORD = re.compile(
    r"\b(?:CGM|SENSOR|DEXCOM|LIBRE|GUARDIAN|DEVICE|READER|RECEIVER|APP)\b[^.]{0,50}?"
    r"\b(?:DISPLAY(?:ED|ING|S)?|SHOW(?:ED|ING|S|N)?|READ(?:ING|S)?|SA(?:ID|YS)|STAT(?:ED|ES)|"
    r"INDICAT(?:ED|ES|ING))\s+(?:AN?\s+)?(?:GLUCOSE\s+|VALUE\s+OF\s+|READING\s+OF\s+|RESULT\s+OF\s+)*"
    r"[\"'\s]*(LOW|HIGH)\b(?!\s+(?:GLUCOSE|BLOOD|READINGS?|RESULTS?|VALUES?|ALERT|ALARM))"
)

# Parkes zone: "FALL INTO THE C ZONE", "FALL INTO THE "C" ZONE", "ZONE C"
RE_ZONE = re.compile(
    r"(?:FALLS?|FELL|FALLING)\s+(?:INTO|IN|WITHIN)\s+(?:THE\s+)?[\"']?([A-E])[\"']?\s+ZONE|"
    r"PARKES[^.]{0,80}?\b[\"']?([A-E])[\"']?\s+ZONE|"
    r"PARKES[^.]{0,80}?\bZONE\s+[\"']?([A-E])\b"
)

# Wear day: "THE LENGTH OF SENSOR WEAR WAS 12 DAYS", "... WAS ONE DAY", "ON DAY 3 OF WEAR"
WORDNUM = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8,
           "NINE": 9, "TEN": 10, "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14, "FIFTEEN": 15}
DAYNUM = r"(\d{1,2}|" + "|".join(WORDNUM) + r")"
RE_WEAR = [
    re.compile(r"LENGTH\s+OF\s+(?:SENSOR\s+)?WEAR\s+WAS\s+(?:LESS\s+THAN\s+|APPROXIMATELY\s+|ABOUT\s+)?" + DAYNUM + r"\s+DAYS?"),
    re.compile(r"\bDAY\s+" + DAYNUM + r"\s+OF\s+(?:SENSOR\s+|THE\s+)?(?:WEAR|USE|SESSION)"),
    re.compile(r"\b" + DAYNUM + r"(?:ST|ND|RD|TH)?\s+DAY\s+OF\s+(?:SENSOR\s+|THE\s+)?(?:WEAR|USE|SESSION)"),
    re.compile(r"(?:AFTER|FOR)\s+" + DAYNUM + r"\s+DAYS?\s+OF\s+(?:SENSOR\s+)?(?:WEAR|USE)"),
    re.compile(r"(?:WORN|WEARING|IN\s+USE)\s+FOR\s+(?:APPROXIMATELY\s+|ABOUT\s+)?" + DAYNUM + r"\s+DAYS?"),
    re.compile(r"\b" + DAYNUM + r"\s+DAYS?\s+(?:INTO|AFTER)\s+(?:THE\s+)?(?:SENSOR\s+)?(?:WEAR|INSERTION|START|SESSION)"),
    re.compile(r"\bON\s+DAY\s+" + DAYNUM + r"\b"),
]

# Boilerplate removed BEFORE the keyword flags are computed
BOILERPLATE = [
    re.compile(r"(?:THERE\s+(?:WAS|IS)\s+)?NO\s+REPORTS?\s+OF\s+DEATH[^.]*\.?"),
    re.compile(r"NO\s+REPORTS?\s+OF\s+(?:SERIOUS\s+INJURY|PERMANENT\s+IMPAIRMENT)[^.]*\.?"),
    re.compile(r"NO\s+(?:INJURY|HARM)\s+(?:OR\s+MEDICAL\s+INTERVENTION\s+|REQUIRING\s+MEDICAL\s+INTERVENTION\s+)?WAS\s+REPORTED\.?"),
    re.compile(r"DIABETES\s+MELLITUS\s+IS\s+A\s+KNOWN\s+CAUSE\s+OF\s+[A-Z ]+\.?"),
    re.compile(r"IT\s+WAS\s+REPORTED\s+THAT\s+AN\s+INACCURACY\s+BETWEEN\s+THE\s+(?:CONTINUOUS\s+GLUCOSE\s+MONITOR\s+\(CGM\)|CGM)"
               r"\s+AND\s+THE\s+(?:BLOOD\s+GLUCOSE\s+\(BG\)|BG)\s+METER\s+OCCURRED[^.]*\.?"),
    re.compile(r"DEATH\s+REPORT\s+FORM\b"),  # Medtronic form name, not an event
]
RE_KW_METER = re.compile(r"FINGER\s*-?\s*STICK|FINGER\s*-?\s*PRICK|\bFSBG\b|\bBGM?\b|\bMETERS?\b|GLUCOMETER|"
                         r"BLOOD\s+GLUCOSE\s+(?:TEST|CHECK|MEASUREMENT|READING|VALUE)|\bCAPILLARY\b|\bLAB(?:ORATORY)?\s+(?:GLUCOSE|TEST|VALUE)")
RE_KW_EMS = re.compile(r"\bEMS\b|PARAMEDIC|\b911\b|EMERGENCY\s+(?:ROOM|DEPARTMENT|SERVICES|MEDICAL)|\bER\b|\(ED\)|"
                       r"HOSPITAL|ADMITTED|\bICU\b|URGENT\s+CARE|AMBULANCE|INTENSIVE\s+CARE")
RE_KW_DEATH = re.compile(r"\bDEATH\b|\bDIED\b|\bDECEASED\b|PASSED\s+AWAY|\bFATAL\b|\bEXPIRED\b|\bDEAD\b")
RE_KW_NOHARM = re.compile(r"NO\s+REPORTS?\s+OF\s+DEATH|NO\s+(?:INJURY|HARM)\b.{0,40}?REPORTED|NO\s+CLINICAL\s+SIGNS|"
                          r"NO\s+ADVERSE\s+EVENT")
RE_B4 = re.compile(r"\(B\)\s*\(4\)")
RE_B6 = re.compile(r"\(B\)\s*\(6\)")

# Sentence boundary: a period after a letter, quote or bracket (not after a digit, so "5.6" stays),
# a newline, or the " | " that joins several texts of the same type
RE_SENT_SPLIT = re.compile(r"(?<=[A-Z\)\"'\]])\.\s+|\n+|\s\|\s")
RE_UNIT_ONLY = re.compile(UNIT)


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def maker_of(*names):
    """Maker label from manufacturer / brand strings. 'ABBOTT DIABETES CARE INC' -> 'Abbott'."""
    s = " ".join(str(n or "") for n in names).upper()
    if "ABBOTT" in s or "LIBRE" in s:
        return "Abbott"
    if "DEXCOM" in s:
        return "Dexcom"
    if "MEDTRONIC" in s or "MINIMED" in s or "GUARDIAN" in s or "SIMPLERA" in s or "ENLITE" in s:
        return "Medtronic"
    return "Other"


def build_text(event_text, mfr_narrative):
    """Join D5 and H10 with labels. A missing part is left out. Returns '' if both are empty."""
    parts = []
    if event_text and str(event_text).strip():
        parts.append(D5_LABEL + "\n" + str(event_text).strip())
    if mfr_narrative and str(mfr_narrative).strip():
        parts.append(H10_LABEL + "\n" + str(mfr_narrative).strip())
    return "\n\n".join(parts)


def _join(v):
    if isinstance(v, list):
        return "; ".join(str(x).strip() for x in v if str(x).strip())
    return "" if v is None else str(v)


def _row_from_api(r):
    """One JSONL record (openFDA shape) -> unified dict."""
    texts = r.get("mdr_text") or []
    d5 = [t.get("text", "") for t in texts
          if (t.get("type") or t.get("text_type_code")) == "Description of Event or Problem" and t.get("text")]
    h10 = [t.get("text", "") for t in texts
           if (t.get("type") or t.get("text_type_code")) == "Additional Manufacturer Narrative" and t.get("text")]
    manufacturer = r.get("manufacturer_d_name") or r.get("manufacturer") or ""
    brand = r.get("brand_name") or ""
    event_text, mfr = " | ".join(d5), " | ".join(h10)
    return {
        "mdr_report_key": str(r.get("mdr_report_key") or ""),
        "report_number": str(r.get("report_number") or ""),
        "maker": maker_of(manufacturer, brand, r.get("brand_label")),
        "brand_name": brand, "manufacturer": manufacturer,
        "brand_label": r.get("brand_label") or "", "split": r.get("split") or "",
        "event_type": r.get("event_type") or "",
        "product_problems": _join(r.get("product_problems")),
        "patient_outcome": _join(r.get("patient_outcome")),
        "date_received": r.get("date_received") or "",
        "event_text": event_text, "mfr_narrative": mfr,
        "text": build_text(event_text, mfr),
    }


def _row_from_csv(r):
    """One clean CSV row -> unified dict."""
    manufacturer = r.get("manufacturer") or r.get("manufacturer_d_name") or ""
    brand = r.get("brand_name") or ""
    event_text, mfr = r.get("event_text") or "", r.get("mfr_narrative") or ""
    return {
        "mdr_report_key": str(r.get("mdr_report_key") or ""),
        "report_number": r.get("report_number") or "",
        "maker": maker_of(manufacturer, brand, r.get("brand_label")),
        "brand_name": brand, "manufacturer": manufacturer,
        "brand_label": r.get("brand_label") or "", "split": r.get("split") or r.get("_stratum") or "",
        "event_type": r.get("event_type") or "",
        "product_problems": r.get("product_problems") or "",
        "patient_outcome": r.get("patient_outcome") or "",
        "date_received": r.get("date_received") or "",
        "event_text": event_text, "mfr_narrative": mfr,
        "text": build_text(event_text, mfr),
    }


def load_reports(path, limit=None):
    """Read JSONL or CSV(.gz). Returns a list of unified report dicts (see _row_from_api)."""
    path = Path(path)
    rows = []
    if path.suffix.lower() == ".jsonl":
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(_row_from_api(json.loads(line)))
                    if limit and len(rows) >= limit:
                        break
    else:
        opener = gzip.open if path.suffix.lower() == ".gz" else open
        csv.field_size_limit(10_000_000)
        with opener(path, "rt", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rows.append(_row_from_csv(r))
                if limit and len(rows) >= limit:
                    break
    return rows


# ----------------------------------------------------------------------------
# Helpers for numbers and text
# ----------------------------------------------------------------------------
def norm(text):
    """Uppercase. Every non-ASCII char becomes one space, so character positions do not move."""
    return "".join(ch if ord(ch) < 128 else " " for ch in text).upper()


def parse_number(s):
    """'1,000' -> 1000.0 ; '5,6' -> 5.6 ; '80.00' -> 80.0"""
    if "," in s:
        head, tail = s.split(",", 1)
        s = head + tail if len(tail) == 3 else head + "." + tail
    return float(s)


def unit_name(u):
    return "mmol/L" if u.upper().startswith("MMOL") else "mg/dL"


def to_mgdl(value, unit):
    """Convert to mg/dL. mmol/L x 18, rounded to a whole number."""
    if unit == "mmol/L":
        return float(round(value * MMOL_FACTOR))
    return value


def fmt_num(v):
    """80.0 -> '80', 80.5 -> '80.5', None -> ''"""
    if v is None:
        return ""
    return str(int(v)) if float(v).is_integer() else str(v)


def values_from_list(list_text):
    """'17.00 MMOL/L,14.00 MMOL/L' -> [{'raw','value','unit','mgdl','qual'}, ...]"""
    out = []
    for m in RE_VAL.finditer(list_text):
        qual, num, plus, unit = m.groups()
        u = unit_name(unit)
        v = parse_number(num)
        out.append({"raw": m.group(0).strip(), "value": v, "unit": u, "mgdl": to_mgdl(v, u),
                    "qual": (qual or "").strip() + plus})
    return out


def sentence_spans(t):
    """List of (start, end) sentence spans in t. Duplicated sentences keep only their first span."""
    spans, start = [], 0
    for m in RE_SENT_SPLIT.finditer(t):
        if m.start() > start:
            spans.append((start, m.start()))
        start = m.end()
    if start < len(t):
        spans.append((start, len(t)))
    seen, out = set(), []
    for a, b in spans:
        key = t[a:b].strip()
        if key and key not in seen:
            seen.add(key)
            out.append((a, b))
    return out


def role_before(sentence, pos):
    """Role of the number at position pos: 'sensor', 'meter', 'block' or None.
    Looks back LOOKBACK_CHARS, but not past an earlier number with a unit."""
    start = max(0, pos - LOOKBACK_CHARS)
    span = sentence[start:pos]
    prev_units = list(RE_UNIT_ONLY.finditer(span))
    if prev_units:
        span = span[prev_units[-1].end():]
    prev_digits = list(re.finditer(r"\d", span))      # also stop at an earlier number (unit-less values)
    if prev_digits:
        span = span[prev_digits[-1].end():]
    strong, weak = [], []
    for role, strength, rx in ROLE_WORDS:
        for m in rx.finditer(span):
            (strong if strength == "strong" else weak).append((len(span) - m.end(), role, m.start(), m.group(0)))
    if strong:
        strong.sort()
        _, role, mstart, word = strong[0]
        if role == "meter" and word in ("BG", "BGM"):
            # "THE PUMP REPORTED A BG OF 179 MG/DL": a BG right after a sensor word is the sensor's value
            if ROLE_WORDS[0][2].search(span[max(0, mstart - 25):mstart]):
                return "sensor"
        return role
    return "meter" if weak else None


def values_in_sentence(sent):
    """Find glucose values in one sentence and give each list a role.
    Returns list of (role, values, start, end). role in sensor / meter / None."""
    found = []
    taken = []
    for m in RE_LIST.finditer(sent):
        if RE_RANGE_BEFORE.search(sent[max(0, m.start() - 6):m.start()]):
            continue                                  # "40-50 MG/DL": second half of a range
        if RE_AFTER_BLOCK.search(sent[m.end():m.end() + 14]):
            continue                                  # "1 MG/DL PER MINUTE"
        role = role_before(sent, m.start())
        if role == "block":
            continue
        found.append((role, values_from_list(m.group(0)), m.start(), m.end()))
        taken.append((m.start(), m.end()))
    for m in RE_VAL_UNITLESS.finditer(sent):
        a, b = m.start(1), m.end(1)
        if any(x <= a < y for x, y in taken):
            continue
        v = parse_number(m.group(1))
        if not (20 <= v <= 1500):
            continue
        role = role_before(sent, a)
        if role in ("block", None):
            continue
        found.append((role, [{"raw": m.group(1), "value": v, "unit": "none", "mgdl": v, "qual": ""}], a, b))
    # the sensor showed a word instead of a number ("THE CGM CONTINUED TO DISPLAY LOW")
    for m in RE_DISPLAY_WORD.finditer(sent):
        found.append(("sensor", [{"raw": m.group(1), "value": None, "unit": "word", "mgdl": None, "qual": ""}],
                      m.start(1), m.end(1)))
    found.sort(key=lambda x: x[2])
    return found


def is_num(v):
    return v.get("mgdl") is not None


# ----------------------------------------------------------------------------
# The extractor
# ----------------------------------------------------------------------------
def _pair_from_template(m, t):
    s_vals = values_from_list(m.group("sensor"))
    m_vals = values_from_list(m.group("meter"))
    return {"sensor": s_vals, "meter": m_vals, "scope": "template",
            "match_sensor": m.group("sensor"), "match_meter": m.group("meter"),
            "sentence": t[max(0, m.start() - 40):m.end() + 20]}


def abbott_template(t):
    """All Abbott template matches in text t (pairs and sensor-only). Deduplicated."""
    pairs, sensor_only, seen = [], [], set()
    for rx in (RE_ABBOTT_PAIR, RE_ABBOTT_PAIR_REV):
        for m in rx.finditer(t):
            p = _pair_from_template(m, t)
            key = (tuple(v["mgdl"] for v in p["sensor"]), tuple(v["mgdl"] for v in p["meter"]))
            if key not in seen:
                seen.add(key)
                pairs.append(p)
    for m in RE_ABBOTT_SENSOR_ONLY.finditer(t):
        vals = values_from_list(m.group("sensor"))
        key = (tuple(v["mgdl"] for v in vals), ())
        if key not in seen:
            seen.add(key)
            sensor_only.append({"sensor": vals, "meter": [], "scope": "template_sensor_only",
                                "match_sensor": m.group("sensor"), "match_meter": "",
                                "sentence": t[max(0, m.start() - 40):m.end() + 20]})
    return pairs, sensor_only


def prose_pairs(t):
    """Prose pairing: sensor and meter values in one sentence, or in two neighbouring sentences."""
    sents = []
    for a, b in sentence_spans(t):
        sent = t[a:b]
        hits = values_in_sentence(sent)
        if hits:
            sents.append({"text": sent, "hits": hits})
    pairs, loose_sensor, loose_meter, other = [], [], [], []
    for i, s in enumerate(sents):
        s_lists = [h for h in s["hits"] if h[0] == "sensor"]
        m_lists = [h for h in s["hits"] if h[0] == "meter"]
        other += [v for h in s["hits"] if h[0] is None for v in h[1]]
        if s_lists and m_lists:
            pairs.append({"sensor": [v for h in s_lists for v in h[1]], "meter": [v for h in m_lists for v in h[1]],
                          "scope": "same_sentence", "match_sensor": s["text"][s_lists[0][2]:s_lists[0][3]],
                          "match_meter": s["text"][m_lists[0][2]:m_lists[0][3]], "sentence": s["text"], "i": i})
            s["paired"] = True
        else:
            s["paired"] = False
            s["s_lists"], s["m_lists"] = s_lists, m_lists
    # neighbouring sentences: sensor-only next to meter-only
    for i, s in enumerate(sents):
        if s.get("paired") or not (s.get("s_lists") or s.get("m_lists")):
            continue
        for j in (i + 1, i - 1):
            if 0 <= j < len(sents) and not sents[j].get("paired"):
                n = sents[j]
                if s["s_lists"] and n["m_lists"] and not s["m_lists"] and not n["s_lists"]:
                    pairs.append({"sensor": [v for h in s["s_lists"] for v in h[1]],
                                  "meter": [v for h in n["m_lists"] for v in h[1]], "scope": "adjacent_sentence",
                                  "match_sensor": s["text"][s["s_lists"][0][2]:s["s_lists"][0][3]],
                                  "match_meter": n["text"][n["m_lists"][0][2]:n["m_lists"][0][3]],
                                  "sentence": s["text"] + " || " + n["text"], "i": min(i, j)})
                    s["paired"] = n["paired"] = True
                    break
    for s in sents:
        if not s.get("paired"):
            loose_sensor += [v for h in s.get("s_lists", []) for v in h[1]]
            loose_meter += [v for h in s.get("m_lists", []) for v in h[1]]
    pairs.sort(key=lambda p: p["i"])
    return pairs, loose_sensor, loose_meter, other


def parkes_zone(t):
    m = RE_ZONE.search(t)
    if not m:
        return "", ""
    zone = next(g for g in m.groups() if g)
    return zone, m.group(0)


def wear_day(t):
    """First wear-day pattern that hits. Returns (day or None, matched text, flag)."""
    for rx in RE_WEAR:
        m = rx.search(t)
        if m:
            raw = m.group(1)
            day = WORDNUM.get(raw, None) if raw in WORDNUM else int(raw)
            if day is None or day > MAX_WEAR_DAY:
                return None, m.group(0), "wear_day_out_of_range"
            return day, m.group(0), ""
    return None, "", ""


def strip_boilerplate(t):
    for rx in BOILERPLATE:
        t = rx.sub(" ", t)
    return t


def extract_report(report):
    """Run every pattern on one report dict (needs 'text'; uses 'maker', ids). Returns the output row."""
    raw = report.get("text") or ""
    t = norm(raw[:MAX_TEXT_CHARS])
    row = {c: "" for c in OUTPUT_COLUMNS}
    row.update({"mdr_report_key": report.get("mdr_report_key", ""), "maker": report.get("maker", ""),
                "brand_name": report.get("brand_name", ""), "event_type": report.get("event_type", ""),
                "text_chars": len(raw), "n_b4": len(RE_B4.findall(t)), "n_b6": len(RE_B6.findall(t)),
                "regex_template": "none", "pair_found": "no", "multiple_pairs": "no", "mmol_converted": "no",
                "n_pairs": 0})
    if not t.strip():
        return row

    # 1. Abbott template first, then prose
    pairs, sensor_only = abbott_template(t)
    template = "abbott_template" if (pairs or sensor_only) else "none"
    p_pairs, loose_s, loose_m, other = prose_pairs(t)
    if not pairs and p_pairs:
        pairs = p_pairs
        template = "dexcom_bg"
    elif pairs and p_pairs:
        # keep template pairs; add prose pairs that bring new numbers
        known = {(tuple(v["mgdl"] for v in p["sensor"]), tuple(v["mgdl"] for v in p["meter"])) for p in pairs}
        pairs += [p for p in p_pairs if (tuple(v["mgdl"] for v in p["sensor"]), tuple(v["mgdl"] for v in p["meter"])) not in known]

    # numeric pairs first (sensor number + meter number); word pairs (sensor showed LOW/HIGH) after
    num_pairs = [p for p in pairs if any(is_num(v) for v in p["sensor"]) and any(is_num(v) for v in p["meter"])]
    word_pairs = [p for p in pairs if p not in num_pairs and any(is_num(v) for v in p["meter"])]
    template_vals = {v["mgdl"] for p in pairs + sensor_only for v in p["sensor"] + p["meter"] if p["scope"].startswith("template")}
    loose_s = [v for v in loose_s if v["mgdl"] not in template_vals]       # the prose path re-reads template sentences
    loose_m = [v for v in loose_m if v["mgdl"] not in template_vals]
    other = [v for v in other if v["mgdl"] not in template_vals]
    all_sensor = [v for p in pairs for v in p["sensor"] if is_num(v)] + [v for p in sensor_only for v in p["sensor"]] + [v for v in loose_s if is_num(v)]
    all_meter = [v for p in pairs for v in p["meter"] if is_num(v)] + [v for v in loose_m if is_num(v)]
    first = num_pairs[0] if num_pairs else (word_pairs[0] if word_pairs else (sensor_only[0] if sensor_only else None))
    s_first = next((v for v in first["sensor"] if is_num(v)), None) if first else next((v for v in loose_s if is_num(v)), None)
    m_first = next((v for v in first["meter"] if is_num(v)), None) if first else next((v for v in loose_m if is_num(v)), None)
    if num_pairs or word_pairs:
        row["pair_found"] = "yes" if num_pairs else "display_word"
        row["pair_scope"] = first["scope"]
        row["match_pair_sentence"] = first["sentence"][:400]
        n_pairs = len(num_pairs) + len(word_pairs) + (max(len(first["sensor"]), len(first["meter"])) - 1)
        row["n_pairs"] = n_pairs
        row["multiple_pairs"] = "yes" if n_pairs > 1 else "no"
    elif first:
        row["pair_scope"] = first["scope"]
        row["match_pair_sentence"] = first["sentence"][:400]
    row["regex_template"] = template
    if s_first:
        row.update({"sensor_value_mgdl": fmt_num(s_first["mgdl"]), "sensor_unit": s_first["unit"],
                    "sensor_value_raw": s_first["raw"], "match_sensor": (first or {}).get("match_sensor", s_first["raw"])})
    if m_first:
        row.update({"meter_value_mgdl": fmt_num(m_first["mgdl"]), "meter_unit": m_first["unit"],
                    "meter_value_raw": m_first["raw"], "match_meter": (first or {}).get("match_meter", m_first["raw"])})
    if any(v["unit"] == "mmol/L" for v in all_sensor + all_meter):
        row["mmol_converted"] = "yes"
    row["sensor_values_all"] = ";".join(fmt_num(v["mgdl"]) for v in all_sensor)
    row["meter_values_all"] = ";".join(fmt_num(v["mgdl"]) for v in all_meter)
    row["other_values_all"] = ";".join(fmt_num(v["mgdl"]) for v in other if is_num(v))
    word = next((v["raw"] for p in (word_pairs or pairs) for v in p["sensor"] if v["unit"] == "word"), "")
    if s_first and m_first:
        row["sensor_lower_than_meter"] = "yes" if s_first["mgdl"] < m_first["mgdl"] else "no"
    elif word and m_first:
        row["sensor_lower_than_meter"] = "yes" if word == "LOW" else "no"
    flags = []
    for v in all_sensor + all_meter:
        if not (PLAUSIBLE_MGDL[0] <= v["mgdl"] <= PLAUSIBLE_MGDL[1]):
            flags.append("implausible_value")
            break
    if any(v["unit"] == "none" for v in all_sensor + all_meter):
        flags.append("unitless_value")
    if any(v["qual"] for v in all_sensor + all_meter):
        flags.append("qualifier_or_bound")

    # 2. display word, zone, wear day
    dm = RE_DISPLAY_WORD.search(t)
    row["sensor_display_word"] = word or (dm.group(1) if dm else "")
    row["parkes_zone_stated"], row["match_zone"] = parkes_zone(t)
    day, wm, wflag = wear_day(t)
    row["wear_day"] = "" if day is None else day
    row["match_wear"] = wm
    if wflag:
        flags.append(wflag)
    row["value_flag"] = ";".join(flags)

    # 3. keyword flags on text without boilerplate
    clean = strip_boilerplate(t)
    row["kw_meter_mentioned"] = "yes" if RE_KW_METER.search(clean) else "no"
    row["kw_ems_or_hospital"] = "yes" if RE_KW_EMS.search(clean) else "no"
    row["kw_death_real"] = "yes" if RE_KW_DEATH.search(clean) else "no"
    row["kw_no_harm_boilerplate"] = "yes" if RE_KW_NOHARM.search(t) else "no"
    return row


# ----------------------------------------------------------------------------
# Hit rates
# ----------------------------------------------------------------------------
def hit_rate_table(rows, key_fn, title):
    """Markdown table of hit rates for groups given by key_fn(row)."""
    groups = collections.OrderedDict()
    for r in rows:
        groups.setdefault(key_fn(r), []).append(r)
    lines = [f"### {title}", "",
             "| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]

    def pct(rs, f):
        return f"{100.0 * sum(1 for r in rs if f(r)) / len(rs):.0f}%" if rs else "-"

    for g, rs in groups.items():
        lines.append("| " + " | ".join([
            str(g), str(len(rs)),
            pct(rs, lambda r: r["pair_found"] == "yes"),
            pct(rs, lambda r: r["pair_found"] in ("yes", "display_word")),
            pct(rs, lambda r: r["regex_template"] == "abbott_template"),
            pct(rs, lambda r: r["regex_template"] == "dexcom_bg"),
            pct(rs, lambda r: r["sensor_value_mgdl"] != ""),
            pct(rs, lambda r: r["meter_value_mgdl"] != ""),
            pct(rs, lambda r: r["sensor_display_word"] != ""),
            pct(rs, lambda r: r["parkes_zone_stated"] != ""),
            pct(rs, lambda r: r["wear_day"] != ""),
        ]) + " |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Regex layer for MAUDE CGM report texts.")
    ap.add_argument("input", help="JSONL (API shape) or CSV/CSV.GZ (clean shape)")
    ap.add_argument("output", help="output CSV path")
    ap.add_argument("--limit", type=int, default=None, help="only the first N reports")
    args = ap.parse_args()

    t0 = time.time()
    reports = load_reports(args.input, args.limit)
    print(f"loaded {len(reports)} reports in {time.time() - t0:.1f} s")
    rows = []
    t1 = time.time()
    for i, rep in enumerate(reports, 1):
        rows.append(extract_report(rep))
        if i % 5000 == 0:
            print(f"  {i} reports, {time.time() - t1:.1f} s")
    dt = time.time() - t1
    print(f"regex done: {len(rows)} reports in {dt:.2f} s ({len(rows) / max(dt, 1e-9):.0f} reports/s)")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}")

    tables = [hit_rate_table(rows, lambda r: r["maker"], "By maker"),
              hit_rate_table(rows, lambda r: r["event_type"], "By event type"),
              hit_rate_table(rows, lambda r: f'{r["maker"]} / {r["event_type"]}', "By maker and event type")]
    md = f"# Regex hit rates\n\nInput: `{args.input}`. Reports: {len(rows)}.\n\n" + "\n".join(tables)
    hit_path = out.with_name(out.stem + "_hitrates.md")
    hit_path.write_text(md, encoding="utf-8")
    print(md)
    print(f"wrote {hit_path}")


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------------
# Shared helper for the model layer and the scorer (added with prompt v2)
# ----------------------------------------------------------------------------
RE_BOUND_WORD = re.compile(r"^\s*(?:GREATER\s+THAN|MORE\s+THAN|LESS\s+THAN|OVER|ABOVE|BELOW|UNDER)\b|^\s*[<>]|\d\s*\+")


def is_bound_raw(raw):
    """True when a matched value text is a bound, not a value: 'OVER 600 MG/DL', '400+ MG/DL', '> 500'.
    'APPROXIMATELY 400 MG/DL' is a value (False). Used by the combined rule to null such values."""
    if not raw:
        return False
    return RE_BOUND_WORD.search(str(raw).upper()) is not None
