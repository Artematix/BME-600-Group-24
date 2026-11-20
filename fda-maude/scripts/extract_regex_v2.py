#!/usr/bin/env python
"""
extract_regex_v2.py : wider pattern layer for the MAUDE CGM report texts (Phase 1, BMEN 600 Group 24).

Why this file exists
- extract_regex.py (v1) reads the Abbott template and a loose "CGM value vs BG value" prose form.
  The language model found both glucose values in about 15.6 % of serious reports; v1 found 10 %.
- The model never read the 3.26 million malfunction-only reports (too slow). Patterns are fast.
- v2 keeps every v1 pattern (imported, not copied) and adds more prose forms, tuned against the
  model's output on the 124,599-report run set. Then it runs over all 3.38 million reports.

Commands (run from the repo root; Windows: plain `python`)
  python fda-maude/scripts/extract_regex_v2.py tune     run-set comparison against the model; tuning tables
  python fda-maude/scripts/extract_regex_v2.py mine     print the sentences around the model's values for a
                                                        random 400 reports the baseline missed (seed 20261106)
  python fda-maude/scripts/extract_regex_v2.py full     run over clean/full.parquet; write regex_v2_full.csv.gz
  python fda-maude/scripts/extract_regex_v2.py report   tables and figures from regex_v2_full.csv.gz
  (`full` runs `report` at the end.)  All paths are options; see --help.

Deterministic: seed 20261106, fixed pattern order, ordered chunking. Progress is printed.

Definitions shared with text_results.py (copied, with a comment, so the numbers match):
  plausible sensor 20 to 600 mg/dL, plausible meter 20 to 1,500 mg/dL; error = sensor minus meter;
  direction from the two numbers; meter bands under 54 / 54 to 69 / 70 to 180 / 181 to 250 / over 250.
"""

import argparse
import collections
import csv
import gzip
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract_regex as v1  # noqa: E402  (the v1 patterns and helpers; v1 is never edited)

REPO = HERE.parents[1]
FDA = REPO / "fda-maude"
SEED = 20261106
T0 = time.time()

# ----------------------------------------------------------------------------
# Shared definitions (copied from text_results.py so the two scripts agree)
# ----------------------------------------------------------------------------
SENSOR_RANGE = (20.0, 600.0)       # plausible stated sensor value, mg/dL   (text_results.SENSOR_RANGE)
METER_RANGE = (20.0, 1500.0)       # plausible stated meter / lab value     (text_results.METER_RANGE)
METER_BANDS = [(0, 54, "under 54"), (54, 70, "54 to 69"), (70, 181, "70 to 180"), (181, 251, "181 to 250"),
               (251, 10_000, "over 250")]
BRANDS = ["Abbott", "Dexcom", "Medtronic", "Senseonics", "Other"]
MAX_TEXT_CHARS = v1.MAX_TEXT_CHARS


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def brand_of(manufacturer, brand_name):
    """Brand label: v1's maker rule, with Senseonics (Eversense) split out of 'Other' (as brand_comparison.py)."""
    mk = v1.maker_of(manufacturer, brand_name)
    if mk == "Other":
        s = f"{manufacturer or ''} {brand_name or ''}".upper()
        if "SENSEONICS" in s or "EVERSENSE" in s:
            return "Senseonics"
    return mk


def event_group(event_type):
    """FDA event type -> death / injury / malfunction / other."""
    e = (event_type or "").strip().lower()
    if e in ("death", "injury", "malfunction"):
        return e
    return "other"


def meter_band(m):
    for lo, hi, name in METER_BANDS:
        if lo <= m < hi:
            return name
    return ""


# ----------------------------------------------------------------------------
# v2 patterns. All matching is on UPPERCASE text (v1.norm). One block per idea, with an example.
#
# How a pair is found (after the v1 template and v1 prose forms have had their turn):
#   1. every glucose number in a sentence is collected: numbers with a unit (typo units included),
#      and unit-less numbers that follow a role word through filler words ("FINGER STICK READING IS 52")
#   2. each number gets a role (sensor / meter) from the nearest role word BEFORE it ("THE CGM READ 55")
#      or AFTER it ("55 MG/DL ON THE ADC DEVICE", "210 MG/DL OBTAINED ON A COMPETITOR BRAND METER")
#   3. comparison structure fills gaps ("41 MG/DL FROM SENSOR AGAINST 511 MG/DL", "a COMPARED TO b")
#   4. a sentence with a sensor number and a meter number gives the pair; else two neighbouring
#      sentences; else the whole text when it has exactly one sensor and one meter number
# Bounds ("OVER 400", "LESS THAN 40", "400+") and display words ("LOW", "HI") are kept as flags, not values.
# ----------------------------------------------------------------------------
NUM = v1.NUM                                   # 80 | 80.00 | 5.6 | 1,000 | 5,6 (decimal comma)
# Units, including the typos seen in the texts: "MGDL", "MG/ DL", "MG/D/L", "M/DL", "MD/DL", "NG/DL", "MG/DO", "MMOLL", "MMO/L"
UNIT2 = r"(?:MG\s*/?\s*D\s*/?\s*[LO]\b|MG\s*/\s*D\b|M\s*/\s*DL\b|MD\s*/\s*DL\b|NG\s*/\s*DL\b|MMOL\s*/{0,2}\s*L\b|MMOLL\b|MMO\s*/\s*L\b|MMOL\b)"
# "ABOUT 400" is a value; "OVER 400" / "LESS THAN 40" / "400+" is a bound (gold rubric: bounds stay null)
APPROX = (r"(?:APPROXIMATELY|APPROX\.?|ABOUT|AROUND|ROUGHLY|CLOSE\s+TO|ALMOST|NEARLY|NEAR|~|"
          r"(?:A\s+LITTLE|JUST|SLIGHTLY)\s+(?:OVER|UNDER|ABOVE|BELOW)|MID|IN\s+THE)")
BOUND = r"(?:(?:GREATER|MORE|LESS|HIGHER|LOWER)\s+THAN|OVER|ABOVE|BELOW|UNDER|EXCEED(?:ED|ING|S)?|>|<)"
UNUM = r"(?:\d{2,4}(?:[.,]\d{1,3})?|\d[.,]\d{1,3})"   # a unit-less value needs 2 digits or a decimal ("LIBRE 2" is a name, not a value)


def range_pat(num):
    """'90-100' keeps the first number (flagged as a range); '400+' is a bound."""
    return rf"(?P<n>{num})(?:\s*-\s*(?P<n2>{num}))?(?P<plus>\s*\+)?"


RANGE = range_pat(NUM)
# Not a glucose value when followed by these (time, dose, day count, difference, percentage, ordinal)
NOT_AFTER = (r"(?!\s*-?\s*(?:%|PERCENT\b|:\d|AM\b|PM\b|A\.M\.|P\.M\.|UNITS?\b|U\b|IU\b|DAYS?\b|HOURS?\b|HRS?\b|MINUTES?\b|MINS?\b|"
             r"YEARS?\b|MONTHS?\b|WEEKS?\b|TIMES\b|POINTS?\b|/\s*\d|G\b|GRAMS?\b|LBS?\b|KG\b|MM\b|CM\b|ST\b|ND\b|RD\b|TH\b|X\b|"
             r"(?:MG\s*/?\s*DL\s+)?(?:LOWER|HIGHER|LESS|MORE)\s+THAN|(?:MG\s*/?\s*DL\s+)?(?:BELOW|ABOVE|OFF\b|DIFFEREN|OR\s+MORE|OR\s+LESS|"
             r"(?:AND|OR)\s+(?:BELOW|ABOVE|LOWER|HIGHER|LESS|MORE|GREATER|UNDER|OVER))))")
# Form A: a number with a unit:  "55 MG/DL", "OVER 400 MG/DL", "3.4 MMOL/L", "90-100 MG/DL", "500MGDL"
RE_VAL2 = re.compile(rf"(?:(?P<approx>{APPROX})\s*)?(?:(?P<bound>{BOUND})\s*)?{RANGE}\s*(?P<u>{UNIT2}){NOT_AFTER}")

# Role words. Strong words decide; weak words count only when no strong word is near.
# Order inside each class is longest-first, and the classes are tried in this order at each position.
MS = (  # meter, strong
    r"BLOOD\s+GLUCOSE\s+(?:\(BG\)\s+)?(?:METER|MONITOR)(?:\s+(?:READING|RESULT|VALUE))?|BG\s+METERS?|BGM|GLUCOMETERS?|METERS?(?:'S)?|"
    r"READER'S\s+BUILT\s*-?\s*IN(?:\s+METER)?|BUILT\s*-?\s*IN(?:\s+(?:GLUCOSE\s+)?(?:METER|READER))?|"
    r"FINGER\s*-?\s*STICKS?|FINGER\s*-?\s*PRICKS?|FINGER\s*-?\s*POKES?|FINGERSTICKS?|FSBG|FBG|\bFS\b|BGL|BGS|\bBG\b|"
    r"BLOOD\s+(?:GLUCOSE\s+|SUGAR\s+)?(?:TEST|CHECK|MEASUREMENT|DRAW|WORK)S?|BLOOD\s+(?:GLUCOSE|SUGAR)\s+(?:READING|RESULT|LEVEL|VALUE)S?|"
    r"GLUCOSE\s+TESTS?|LAB(?:ORATORY)?(?:\s+(?:RESULT|TEST|VALUE|GLUCOSE|DRAW|WORK|READING)S?)?|"
    r"CAPILLARY(?:\s+(?:READING|RESULT|GLUCOSE|METER|TEST))?|VENOUS|SERUM(?:\s+GLUCOSE)?|PLASMA(?:\s+GLUCOSE)?|POC|POINT\s+OF\s+CARE|"
    r"COMPETITOR(?:'S)?(?:\s+BRAND)?(?:\s+(?:BLOOD\s+GLUCOSE\s+)?(?:METER|DEVICE|GLUCOMETER|MONITOR))?|"
    r"(?:HCP|HCP'S|HEALTHCARE\s+PROFESSIONAL(?:'S)?(?:\s+\(HCP\))?|HEALTH\s*CARE(?:\s+PROFESSIONAL(?:'S)?|\s+PROVIDER(?:'S)?)?|HOSPITAL(?:'S)?|"
    r"PARAMEDIC(?:S|'S|S')?|EMS|EMT(?:S|'S)?|DOCTOR(?:'S)?|NURSE(?:'S)?|PHYSICIAN(?:'S)?)\s+(?:BLOOD\s+GLUCOSE\s+)?(?:METER|DEVICE|GLUCOMETER|MONITOR|READING|RESULT|TEST)S?|"
    r"(?:ANOTHER(?:\s+ADC)?|DIFFERENT|UNSPECIFIED|UNKNOWN|OTHER|HOME)\s+(?:BLOOD\s+GLUCOSE\s+)?(?:METER|DEVICE|GLUCOMETER|MONITOR)|"
    r"PARAMEDIC(?:S|'S|S')?|\bEMS\b|\bEMTS?\b|CALIBRATION\s+(?:ENTRY|VALUE|READING)|ACCU\s*-?\s*CHE[CK]K?|ONE\s*TOUCH|CONTOUR|TRUE\s+METRIX|RELION|"
    r"PRECISION\s+(?:NEO|XTRA)|FREESTYLE\s+(?:LITE|PRECISION|OPTIUM|FREEDOM)|CONTROL\s+SOLUTION|ACTUAL(?:LY)?|IN\s+FACT|TRUE(?!\s+METRIX)|REAL(?:LY)?")
MW = (  # meter, weak
    r"BLOOD\s+GLUCOSE|BLOOD\s+SUGARS?|HOSPITAL|EMERGENCY\s+(?:ROOM|DEPARTMENT)|\bER\b|\bED\b|URGENT\s+CARE|CLINIC|HCP|"
    r"HEALTHCARE\s+PROFESSIONAL|DOCTOR|NURSE|PHYSICIAN")
SS = (  # sensor, strong
    r"CGM\s+BG|SENSOR\s+BG|CGMS?|CONTINUOUS\s+GLUCOSE\s+MONITOR(?:ING)?(?:\s+SYSTEM)?|SENSORS?(?:'S)?|SENSOR\s+GLUCOSE|\bSG\b|EGVS?|"
    r"ESTIMATED\s+GLUCOSE\s+VALUES?|DEXCOM(?:\s+G[4-7])?|\bG[4-7]\b|(?:FREESTYLE\s+)?LIBRE(?:\s+[23](?:\s+PLUS)?)?|FREESTYLE|GUARDIAN|ENLITE|SIMPLERA|EVERSENSE|"
    r"RECEIVER|TRANSMITTER|SCANS?|SCANNED|SCANNING|READER|(?:THE|HER|HIS|MY|THEIR|DEXCOM|G[67]|CLARITY|LIBRELINK|MOBILE|PHONE)\s+APP|"
    r"CGM\s+DISPLAY\s+DEVICE|DISPLAY\s+DEVICE|MOBILE\s+DEVICE|ADC\s+(?:DEVICE|SENSOR|READER|FREESTYLE\s+LIBRE(?:\s+[23])?(?:\s+SENSOR)?)|"
    r"ABBOTT\s+DIABETES\s+CARE\s+(?:\(ADC\)\s+)?(?:DEVICE|SENSOR)")
SW = r"DEVICE|PUMP|SYSTEM|MONITOR|SCREEN|DISPLAY"      # sensor, weak
BLK = (  # the number is not a glucose comparison
    r"KETONES?|A1C|HBA1C|INSULIN|UNITS?|TARGET|THRESHOLD|LIMIT|GOAL|SETTINGS?|SHOULD\s+HAVE\s+ALERTED|"
    r"ALERTS?\s+(?:WAS\s+|WERE\s+|IS\s+)?(?:SET|CHANGED|ADJUSTED|LEVEL|AT|FOR|THRESHOLD|VALUE|SETTING)|ALARMS?\s+(?:WAS\s+|WERE\s+|IS\s+)?(?:SET|CHANGED|ADJUSTED|LEVEL|AT|FOR|THRESHOLD)|SET\s+(?:AT|TO|FOR)|"
    r"TREND\s+(?:GLUCOSE\s+)?VALUE|AVERAGE|\bMEAN\b|\bGMI\b|TIME\s+IN\s+RANGE|\d{1,3}\s*-\s*DAY\s+(?:TREND|AVERAGE)|"
    r"ONLY\s+(?:REPORTS?|DISPLAYS?|SHOWS?|READS?)|REPORTABLE\s+RANGE|READING\s+RANGE|DISPLAY\s+RANGE|MEASUR(?:ES|ING|EMENT)\s+RANGE|RANGE\s+OF\s+(?:THE\s+)?(?:DEVICE|SENSOR|SYSTEM|CGM)|WILL\s+(?:BE\s+)?DISPLAY|"
    r"PER\s+MINUTE|WEIGH(?:S|ED|T)?|TEMPERATURE|HEART\s+RATE|PULSE|BLOOD\s+PRESSURE|\bBP\b|\bPH\b|AGED?|YEARS?\s+OLD|LOT\s*(?:#|NUMBER|NO\.?)?|"
    r"SERIAL|\bSN\b|\bREF\b|MODEL|MARD|DIFFERENCE|OFF\s+BY|VARIED|BETA\s+HYDROXYBUTYRATE|SODIUM|POTASSIUM|CREATININE|BICARB|LACTATE|CO2|"
    r"OXYGEN|SPO2|\bO2\b|RATE\s+OF|DOSE|BOLUS|BASAL|CARBS?|GRAMS?|CALORIES|STRIPS?")
RE_ROLE = re.compile(rf"\b(?:(?P<ms>{MS})|(?P<mw>{MW})|(?P<ss>{SS})|(?P<sw>{SW})|(?P<blk>{BLK}))(?![A-Z])")
ROLE_ALT = rf"(?:{MS}|{MW}|{SS}|{SW})"
RE_SCAN = re.compile(r"\bSCAN(?:S|NED|NING)?\b")
# Words allowed between a role word and its number ("FINGER STICK READING IS 52", "CGM WAS DISPLAYING 90")
FILL = (r"(?:A|AN|THE|HER|HIS|THEIR|MY|OUR|ITS|THAT|THIS|WHICH|IT|HE|SHE|THEY|I|AND|STILL|ONLY|THEN|NOW|LATER|CURRENTLY|WAS|WERE|IS|ARE|HAD|HAS|HAVE|"
        r"BEEN|BEING|BE|READ|READS|READING|READINGS|SHOWED|SHOWING|SHOWS|SHOWN|SAID|SAYS|SAYING|STATED|STATES|STATING|DISPLAYED|DISPLAYING|DISPLAYS|"
        r"INDICATED|INDICATING|INDICATES|REPORTED|REPORTING|RESULTED|RESULT|RESULTS|RETURNED|REGISTERED|GAVE|GIVING|GIVE|MEASURED|MEASURING|RECORDED|"
        r"REVEALED|CONFIRMED|CAME|BACK|UP|DOWN|IN|OUT|AT|OF|TO|FOR|ON|WITH|BY|FROM|PER|AS|VALUE|VALUES|LEVEL|LEVELS|NUMBER|NUMBERS|GLUCOSE|BG|BLOOD|"
        r"SUGAR|SUGARS|DATA|SCREEN|APP|TEST|TESTED|TESTING|CHECK|CHECKED|OBTAINED|RECEIVED|TAKEN|TOOK|GOT|GETTING|PROVIDED|CONSISTENTLY|REPEATEDLY|"
        r"CONTINUED|CONTINUOUSLY|SUDDENLY|ALWAYS|STEADY|STABLE|AROUND|ABOUT|APPROXIMATELY|APPROX\.?|ROUGHLY|LIKE|BETWEEN|OVERNIGHT|TODAY|STATING)")
FILLS = r"(?:\s*(?:,|:|=|-|\(BG\)|\(CGM\)|\(FSBG\)|\(EGV\)|" + FILL + r"\b)){0,7}\s*"
# Form B: role word, fillers, then a unit-less number:  "G6 READING 71", "FINGER STICK READING IS 52", "SENSOR WAS AT 202", "DEXCOM INDICATED 52"
RE_ROLE_VAL = re.compile(rf"\b(?P<role>{ROLE_ALT})(?![A-Z]){FILLS}(?:(?P<approx>{APPROX})\s*)?(?:(?P<bound>{BOUND})\s*)?{range_pat(UNUM)}(?!\s*{UNIT2})(?!\d){NOT_AFTER}")
# Comparison words that separate the two sides of a comparison (they cut the look-back and look-ahead windows)
CONNECT = (r"(?:LOWER|HIGHER|LESS|MORE|GREATER)\s+THAN|COMPARED\s+(?:TO|WITH|AGAINST)|IN\s+COMPARISON\s+(?:TO|WITH)|COMPARISON\s+(?:TO|WITH)|\bAGAINST\b|\bVS\.?(?![A-Z])|\bVERSUS\b|\bWHILE\b|"
           r"\bWHEREAS\b|\bWHEN\b|\bBUT\b|\bHOWEVER\b|\bALTHOUGH\b|\bTHOUGH\b|\bDESPITE\b|INSTEAD\s+OF|RATHER\s+THAN|AS\s+OPPOSED\s+TO|;")
RE_CONNECT = re.compile(CONNECT)
STRONG_CONNECT = re.compile(r"COMPARED\s+(?:TO|WITH|AGAINST)|IN\s+COMPARISON\s+(?:TO|WITH)|COMPARISON\s+(?:TO|WITH|OF)|\bAGAINST\b|\bVS\.?(?![A-Z])|\bVERSUS\b|\bWHILE\b|\bWHEREAS\b")
# Words allowed between a number and the role word after it ("55 MG/DL OBTAINED ON THE ADC DEVICE", "46 MG/DL WITH THE READER'S BUILT-IN METER")
AFTER_FILL = re.compile(
    r"(?:\s*(?:,|\(ADC\)|\(HCP\)|\(BG\)|\(CGM\)|\(EGV\)|WAS|WERE|IS|ARE|BEING|OBTAINED|RECEIVED|TAKEN|MEASURED|RECORDED|REPORTED|PROVIDED|DISPLAYED|SHOWN|"
    r"READING|READINGS|RESULT|RESULTS|VALUE|VALUES|LEVEL|SCAN|ON|FROM|BY|WITH|VIA|USING|PER|ACCORDING|TO|THE|A|AN|THEIR|HER|HIS|MY|THAT|WHICH|IT|IN|AT|OF|"
    r"BLOOD|GLUCOSE|SUGAR|ADC|ABBOTT|DIABETES|CARE|COMPETITOR|BRAND|HCP|HCP'S|HEALTHCARE|HEALTH|PROFESSIONAL|PROFESSIONAL'S|PROVIDER|PROVIDER'S|"
    r"UNSPECIFIED|UNKNOWN|ANOTHER|DIFFERENT|OTHER|BUILT-IN|BUILT|PRECISION|HOSPITAL|HOSPITAL'S|LAB|LABORATORY|PARAMEDIC|PARAMEDIC'S|PARAMEDICS|EMS|EMT|"
    r"EMT'S|DOCTOR'S|NURSE'S|PATIENT'S|CUSTOMER'S|CUSTOMER|USER'S|S|HC|MEDICAL|MOBILE|DISPLAY|TANDEM|T:|T:SLIM|SLIM|X2|OMNIPOD|LOWER|HIGHER|LOW|HIGH|"
    r"NEW|OLD|SAME|BOTH|THRU|THROUGH|OFF|ESTIMATED)\b)*\s*", re.X)
# Abbott "erratic" template: two SENSOR readings, no meter:  "READINGS OF 20 MG/DL AND 380 MG/DL WITHIN 10 MINUTES"
RE_ERRATIC = re.compile(r"(?:READINGS?|RESULTS?|VALUES?|SCANS?)\s+OF\s+[^.]{0,80}?\bWITHIN\s+(?:\d+|TEN|FIVE|FIFTEEN|THIRTY|A\s+FEW|SEVERAL)\s+MINUTES")
# Abbott prose: "RESULTS OF 2.1 MMOL/L AND 12.1 MMOL/L WERE PLOTTED ON A PARKES ERROR GRID" (sensor first, then meter)
RE_PLOTTED = re.compile(r"(?:RESULTS?|READINGS?|VALUES?)\s+OF\s+(?P<a>.{1,40}?)\s+AND\s+(?P<b>.{1,40}?)\s+(?:WERE\s+|WAS\s+)?PLOTTED")
# Sensor shows a word, not a number:  "THE CGM DISPLAYED LOW", "SENSOR READ HI", "'LO' (READING LESS THAN 40 MG/DL)", "READING LOW", "URGENT LOW"
RE_DISPLAY_WORD = re.compile(
    rf"\b(?:{SS})\b(?:(?!\b(?:BG|BGM|METERS?|FINGER|FINGERSTICK|BLOOD|GLUCOMETER|LAB|FSBG)\b)[^.]){{0,70}}?\b(?:DISPLAY(?:ED|ING|S)?|SHOW(?:ED|ING|S|N)?|READ(?:ING|S)?|SA(?:ID|YS)|STAT(?:ED|ES)|INDICAT(?:ED|ES|ING)|WAS|WERE|"
    r"CONTINUED\s+TO\s+(?:DISPLAY|READ|SHOW)|ALERT(?:ED|ING)?|ALARM(?:ED|ING)?|REGISTERED|STUCK\s+(?:AT|ON))\s+(?:AN?\s+|AS\s+|OF\s+|URGENT\s+|STILL\s+|CONSTANTLY\s+|JUST\s+)*"
    r"[\"'\s]*(?P<w>LOW|HIGH|HI|LO)\b(?!\s+(?:GLUCOSE|BLOOD|READINGS?|RESULTS?|VALUES?|ALERT|ALARM|BATTERY|SIGNAL|LIMIT|THRESHOLD|SCAN|SENSOR|AND\s+HIGH|OR\s+HIGH|TO\s+HIGH))"
    r"|[\"']\s*(?P<w2>LO|HI)\s*[\"']|\b(?P<w3>LO|HI)\s+(?:MESSAGE|READING|RESULT|SCAN|DISPLAY)|(?:MESSAGE|READING|RESULT|SCAN|DISPLAY)S?\s+(?:OF\s+)?[\"']?(?P<w4>LO|HI)\b")
RE_PLOT_ERRATIC_WORDS = re.compile(r"\bERRATIC\b|\bFLUCTUAT")

# Wear day forms added in v2 (v1 has the Abbott "LENGTH OF SENSOR WEAR WAS n DAYS" and six prose forms)
DAYNUM = v1.DAYNUM
RE_WEAR_V2 = [
    # "THE LENGTH OF THE WEAR IS 8 DAYS", "LENGTH OF SENSOR WEAR WAS FOR 3 DAYS", "THE LENGTH OF ADC DEVICE WAS 6 DAYS"
    re.compile(r"LENGTH\s+OF\s+(?:THE\s+)?(?:SENSOR\s+|ADC\s+DEVICE\s+|DEVICE\s+)?(?:WEAR\s+)?(?:WAS|IS)\s+(?:FOR\s+)?(?:APPROXIMATELY\s+|ABOUT\s+|LESS\s+THAN\s+|OVER\s+)?" + DAYNUM + r"[\s-]+DAYS?"),
    # "3 DAYS AFTER THE SENSOR WAS INSERTED", "8 DAYS AFTER IT WAS INSERTED", "6 DAYS AFTER THE SENSOR WAS PUT ON", "2 DAYS OF WEARING"
    re.compile(r"\b" + DAYNUM + r"[\s-]+DAYS?\s+(?:AFTER|SINCE|INTO|OF)\s+(?:THE\s+|HIS\s+|HER\s+|THEIR\s+)?(?:SENSOR\s+|WEARABLE\s+|IT\s+|CGM\s+|DEVICE\s+)?(?:WAS\s+|HAD\s+BEEN\s+|BEING\s+)?"
               r"(?:INSERTED|INSERTION|PUT\s+ON|APPLIED|APPLICATION|PLACED|PLACEMENT|STARTED|START|WEARING|WEAR|USE|ACTIVATED|ACTIVATION)\b"),
    # "DURING HER 4 DAY WEAR OF", "WITH THE 4 DAY USE OF", "AFTER 10-DAYS OF WEAR"
    re.compile(r"\b" + DAYNUM + r"[\s-]+DAYS?\s+(?:WEAR|USE)\s+OF\b|\b" + DAYNUM + r"[\s-]+DAYS?\s+OF\s+(?:SENSOR\s+)?(?:WEAR|USE)\b"),
    # "WEARING THE ADC FREESTYLE LIBRE SENSOR FOR 4 DAYS", "WORE THE SENSOR FOR 7 DAYS", "APPLYING THE SENSOR FOR 14 DAYS"
    re.compile(r"(?:WEARING|WORE|WORN|APPLYING|APPLIED|USING|USED)\s+(?:THE\s+|AN?\s+|HIS\s+|HER\s+|THEIR\s+|MY\s+)?(?:ADC\s+)?(?:FREESTYLE\s+)?(?:LIBRE\s*[23]?\s*(?:PLUS\s+)?)?(?:DEXCOM\s+)?(?:G[4-7]\s+)?(?:CGM\s+)?(?:SENSORS?\s+)?FOR\s+(?:APPROXIMATELY\s+|ABOUT\s+|ONLY\s+|OVER\s+)?" + DAYNUM + r"[\s-]+DAYS?"),
    # "THE SENSOR SESSION LASTED (APPROXIMATELY) 5 DAYS"
    re.compile(r"SESSION\s+(?:LASTED|RAN)\s+(?:FOR\s+)?(?:APPROXIMATELY\s+|ABOUT\s+)?" + DAYNUM + r"[\s-]+DAYS?"),
    # "WITHIN 2 DAYS OF APPLICATION", "DAY 20 AFTER INSERTION"
    re.compile(r"WITHIN\s+" + DAYNUM + r"[\s-]+DAYS?\s+OF\s+(?:SENSOR\s+)?(?:APPLICATION|INSERTION|WEAR|USE|STARTING|PLACEMENT)|\bDAY\s+" + DAYNUM + r"\s+(?:AFTER|SINCE|POST)\s+(?:SENSOR\s+)?(?:INSERTION|APPLICATION|PLACEMENT|START)"),
    # "THE SENSOR HAD BEEN WORN (FOR) (ABOUT) 5 DAYS", "SENSOR WAS IN USE 5 DAYS"
    re.compile(r"SENSOR\s+(?:HAD\s+BEEN|HAS\s+BEEN|WAS|WERE)\s+(?:WORN|IN\s+USE|ON|INSERTED|APPLIED|ACTIVE|ACTIVATED)\s+(?:FOR\s+)?(?:APPROXIMATELY\s+|ABOUT\s+|OVER\s+|ONLY\s+|ROUGHLY\s+|AROUND\s+)?" + DAYNUM + r"\s+DAYS?"),
    # "5 DAYS INTO (THE) SENSOR", "5 DAYS INTO WEAR", "5 DAYS INTO THE 10 DAY"
    re.compile(r"\b" + DAYNUM + r"\s+DAYS?\s+INTO\s+(?:THE\s+|A\s+|HER\s+|HIS\s+|ITS\s+|MY\s+)?(?:SENSOR|WEAR|SESSION|USE|\d{1,2}[\s-]*DAY)"),
    # "ON ITS 5TH DAY", "ON THE 5TH DAY (OF WEAR)", "THE 5TH DAY OF THE SENSOR"
    re.compile(r"\b(?:ON\s+)?(?:ITS|THE|HER|HIS|MY)\s+" + DAYNUM + r"(?:ST|ND|RD|TH)\s+DAY\b"),
    # "SENSOR WAS ON DAY 5", "DAY 5 SENSOR", "SENSOR DAY 5"
    re.compile(r"\bSENSOR\s+(?:WAS\s+)?(?:ON\s+)?DAY\s+" + DAYNUM + r"\b|\bDAY\s+" + DAYNUM + r"\s+SENSOR\b"),
    # "AFTER 5 DAYS" (only with a sensor word in the same sentence; checked in code). Not the Abbott boilerplate
    # "DETACHED AFTER FOURTEEN DAYS OR LESS OF WEAR", which names the wear period, not the day.
    re.compile(r"\bAFTER\s+(?:APPROXIMATELY\s+|ABOUT\s+|ONLY\s+|AROUND\s+)?" + DAYNUM + r"\s+DAYS?\b(?!\s+OR\s+(?:LESS|MORE|FEWER))"),
    # "5 DAYS OF WEAR / USE / LIFE", "5 DAYS OLD"
    re.compile(r"\b" + DAYNUM + r"\s+DAYS?\s+(?:OF\s+(?:SENSOR\s+)?(?:WEAR|USE|LIFE)|OLD)\b"),
]
RE_SENSOR_WORD_ANY = re.compile(rf"\b(?:{SS})\b")
# "WITHIN THE FIRST 24 HOURS", "FIRST DAY", "SAME DAY AS INSERTION", "DAY OF INSERTION" -> day 1
RE_WEAR_HOURS = re.compile(r"\bWITHIN\s+(?:THE\s+)?(?:FIRST\s+)?(?:\d{1,2}|TWENTY[\s-]FOUR|TWELVE|SIX)\s+HOURS\s+(?:OF|AFTER|FROM)\s+(?:SENSOR\s+)?(?:INSERTION|APPLICATION|START|PLACEMENT|ACTIVATION)|"
                           r"\bFIRST\s+DAY\s+(?:OF|AFTER)\s+(?:SENSOR\s+)?(?:WEAR|USE|INSERTION|APPLICATION)|\bSAME\s+DAY\s+(?:AS|OF)\s+(?:SENSOR\s+)?(?:INSERTION|APPLICATION|INSERTING|APPLYING)|"
                           r"\bDAY\s+OF\s+(?:SENSOR\s+)?(?:INSERTION|APPLICATION)\b")

# Fault keyword flags (mentions only, not facts). Each is one readable pattern.
KW = collections.OrderedDict([
    ("kw_reads_low", re.compile(r"READ(?:S|ING)?\s+(?:TOO\s+|FALSELY\s+|MUCH\s+)?LOW(?:ER)?\b|LOW(?:ER)?\s+(?:THAN|READINGS?|RESULTS?|VALUES?|GLUCOSE|SCAN)\b|FALSE(?:LY)?\s+LOW|FALSE\s+HYPO|INACCURATE(?:LY)?\s+LOW|ERRONEOUS(?:LY)?\s+LOW|UNDER-?\s*READ")),
    ("kw_reads_high", re.compile(r"READ(?:S|ING)?\s+(?:TOO\s+|FALSELY\s+|MUCH\s+)?HIGH(?:ER)?\b|HIGH(?:ER)?\s+(?:THAN|READINGS?|RESULTS?|VALUES?|GLUCOSE|SCAN)\b|FALSE(?:LY)?\s+HIGH|FALSE\s+HYPER|INACCURATE(?:LY)?\s+HIGH|ERRONEOUS(?:LY)?\s+HIGH|OVER-?\s*READ")),
    ("kw_inaccurate", re.compile(r"INACCURA|NOT\s+ACCURATE|INCORRECT\s+(?:READING|RESULT|VALUE|GLUCOSE)|WRONG\s+(?:READING|RESULT|VALUE|NUMBER)|ERRONEOUS|DISCREPAN|DID\s+NOT\s+MATCH|DIDN'T\s+MATCH|OFF\s+BY|DIFFEREN(?:CE|T)\s+(?:OF|FROM|BETWEEN)")),
    ("kw_signal_loss", re.compile(r"SIGNAL\s+LOSS|LOSS\s+OF\s+SIGNAL|LOST\s+(?:THE\s+)?SIGNAL|NO\s+SIGNAL|SIGNAL\s+WAS\s+LOST|CONNECTION\s+(?:LOSS|LOST|ISSUE|PROBLEM)|NOT\s+CONNECT|DISCONNECT|BLUETOOTH|NO\s+(?:READINGS?|DATA)\s+(?:FOR|WAS|WERE|AVAILABLE)|GAPS?\s+IN\s+(?:THE\s+)?(?:DATA|READINGS?)|COMMUNICATION\s+(?:ERROR|LOSS|PROBLEM|FAILURE)|OUT\s+OF\s+RANGE")),
    ("kw_sensor_error", re.compile(r"SENSOR\s+ERROR|SENSOR\s+FAIL(?:ED|URE)|REPLACE\s+(?:THE\s+)?SENSOR|SENSOR\s+(?:ENDED|STOPPED|EXPIRED|SHUT\s*(?:DOWN|OFF))|ENDED\s+EARLY|EARLY\s+(?:SENSOR\s+)?(?:END|TERMINATION|SHUTOFF|SHUT\s+OFF)|SENSOR\s+(?:WAS\s+)?(?:NOT\s+)?WORKING|FAILED\s+TO\s+(?:START|WARM|ACTIVATE|PAIR)|WARM[\s-]*UP|SENSOR\s+(?:ISSUE|PROBLEM|MALFUNCTION)")),
    ("kw_adhesive", re.compile(r"ADHESIVE|FELL\s+OFF|FALL(?:ING|S)?\s+OFF|CAME\s+OFF|COMING\s+OFF|DETACH|DISLODG|PEEL(?:ED|ING)?\s+(?:OFF|UP|AWAY)|NOT\s+STICK|DID\s+NOT\s+STAY|WOULDN'T\s+STAY|OVERPATCH|OVER-PATCH|\bTAPE\b")),
    ("kw_insertion_skin", re.compile(r"BLEED|BLOOD\s+AT\s+(?:THE\s+)?(?:SITE|INSERTION)|\bPAIN(?:FUL)?\b|RASH|IRRITAT|ITCH|REDNESS|SWELL|BLISTER|BURN(?:ING|ED)?\b|INFECT|ABSCESS|CELLULITIS|SCAR|BRUIS|FILAMENT|NEEDLE|CANNULA|BROKE\s+OFF|BROKEN\s+OFF|LEFT\s+(?:IN|UNDER)\s+(?:THE\s+)?(?:SKIN|ARM|BODY)|RETAINED|STUCK\s+IN\s+(?:THE\s+)?(?:SKIN|ARM)|ALLERG|REACTION\s+TO\s+(?:THE\s+)?(?:ADHESIVE|SENSOR|TAPE)|SKIN\s+(?:REACTION|IRRITATION|DAMAGE|TEAR)")),
    ("kw_insulin_dose", re.compile(r"(?:TOOK|TAKE|TAKEN|TAKING|GAVE|GIVE|GIVEN|ADMINISTER(?:ED)?|INJECT(?:ED)?|DOSED?|DOSING|BOLUS(?:ED)?|DELIVER(?:ED)?)\b[^.]{0,40}?\bINSULIN|INSULIN\s+(?:WAS\s+)?(?:TAKEN|GIVEN|ADMINISTERED|INJECTED|DOSED?|DELIVERED|BOLUS)|CORRECTION\s+(?:BOLUS|DOSE)|\bUNITS?\s+OF\s+INSULIN|\d+\s*(?:U|UNITS?)\b[^.]{0,20}?INSULIN|INSULIN\s+(?:OVER|UNDER)[\s-]*DOS")),
    ("kw_ate_carbs", re.compile(r"\bATE\b|\bEAT(?:ING)?\b|\bDRANK\b|\bDRINK(?:ING)?\b|JUICE|GLUCOSE\s+TAB|GLUCOSE\s+GEL|CANDY|SUGAR(?:Y)?\s+(?:DRINK|SNACK|FOOD)|CARB(?:OHYDRATE)?S?\b|SNACK|\bSODA\b|HONEY|GLUCAGON|TREAT(?:ED|ING)?\s+(?:THE\s+|FOR\s+|A\s+)?(?:LOW|HYPO)|CONSUM(?:ED|ING)|CORRECT(?:ED|ING)\s+(?:THE\s+|A\s+)?(?:LOW|HYPO)")),
    ("kw_hypo_symptoms", re.compile(r"HYPOGLYC|SHAK(?:Y|ING|ES)|SWEAT|DIZZ|CONFUS|UNCONSCIOUS|PASSED\s+OUT|SEIZURE|CONVULS|UNRESPONSIVE|FAINT|LOSS\s+OF\s+CONSCIOUSNESS|LOW\s+BLOOD\s+SUGAR\s+SYMPTOMS|SYMPTOMS\s+OF\s+(?:A\s+)?(?:LOW|HYPO)")),
    ("kw_hyper_dka", re.compile(r"HYPERGLYC|\bDKA\b|KETOACIDOSIS|KETONES?|HIGH\s+BLOOD\s+SUGAR\s+SYMPTOMS|SYMPTOMS\s+OF\s+(?:A\s+)?(?:HIGH|HYPER)|NAUSE|VOMIT|THIRST")),
])
RE_KW_FINGERSTICK = v1.RE_KW_METER      # a reference check was mentioned
RE_KW_EMS = v1.RE_KW_EMS                # medical care words
RE_KW_DEATH = v1.RE_KW_DEATH
RE_KW_NOHARM = v1.RE_KW_NOHARM

OUTPUT_COLUMNS = [
    "mdr_report_key", "event_type", "event_group", "brand", "year_received", "product_code",
    "sensor_value", "meter_value", "unit", "error_mgdl", "error_pct", "direction", "meter_band",
    "sensor_raw", "meter_raw", "pattern", "n_candidates", "value_flags",
    "sensor_display_word", "sensor_bound", "meter_bound", "bound_pattern", "two_sensor_readings",
    "wear_day", "wear_pattern", "zone_stated",
    "kw_reads_low", "kw_reads_high", "kw_inaccurate", "kw_signal_loss", "kw_sensor_error", "kw_adhesive",
    "kw_insertion_skin", "kw_insulin_dose", "kw_ate_carbs", "kw_hypo_symptoms", "kw_hyper_dka",
    "kw_fingerstick", "kw_ems_or_hospital", "kw_death_real", "kw_no_harm_boilerplate",
    "text_chars", "has_text", "match_text",
]

# Pattern ids in the order they are tried. The first stage that yields a plausible pair wins.
V1_STAGES = ["abbott_template", "v1_prose_same_sentence", "v1_prose_adjacent_sentence"]
V2_STAGES = ["v2_same_sentence", "v2_comparison_one_side", "v2_comparison_implicit",
             "v2_adjacent_sentence", "v2_text_unique"]
# Tested and dropped: "v2_plotted_pair" ("RESULTS OF a AND b WERE PLOTTED", roles assumed) agreed with the model in only
# 65 % of 25 run-set pairs and swapped the roles in 17 %. The code stays for reference; the stage is not in V2_STAGES.
STAGES = V1_STAGES + V2_STAGES


# ----------------------------------------------------------------------------
# v2 value finding
# ----------------------------------------------------------------------------
def unit_name2(u):
    return "mmol/L" if u.upper().replace(" ", "").startswith("MMO") else "mg/dL"


def _make_val(sent, m, has_unit):
    """Value dict from a RE_VAL2 or RE_ROLE_VAL match."""
    v = v1.parse_number(m.group("n"))
    unit = unit_name2(m.group("u")) if has_unit else "none"
    mgdl = v1.to_mgdl(v, unit) if unit != "none" else v
    bound = m.group("bound") or ""
    plus = bool(m.group("plus"))
    if bound:
        b = "<" if re.match(r"LESS|LOWER|BELOW|UNDER|<", bound) else ">"
    elif plus:
        b = ">"
    else:
        b = ""
    start = m.start("approx") if m.group("approx") else (m.start("bound") if bound else m.start("n"))
    return {"raw": sent[start:m.end()].strip(), "raw_start": start, "value": v, "unit": unit, "mgdl": mgdl, "bound": b,
            "approx": bool(m.group("approx")), "range": bool(m.group("n2")), "start": m.start("n"), "end": m.end(),
            "role": None, "strength": None, "src": "unit" if has_unit else "phrase"}


def _classify_role(word):
    m = RE_ROLE.match(word)
    if not m:
        return None, None
    for g, (role, strength) in (("ms", ("meter", "strong")), ("mw", ("meter", "weak")), ("ss", ("sensor", "strong")),
                                ("sw", ("sensor", "weak")), ("blk", ("block", "strong"))):
        if m.group(g):
            return role, strength
    return None, None


def _role_before(sent, val, prev_end):
    """Nearest role word before the number: (role, strength, distance) or (None, None, None). 'block' when a block
    word is nearer than any role word. The window stops at the previous number and at a comparison word."""
    a = max(prev_end, val["start"] - 110, 0)
    span = sent[a:val["start"]]
    cuts = list(RE_CONNECT.finditer(span))
    if cuts:
        span = span[cuts[-1].end():]
    scans = list(RE_SCAN.finditer(span))
    if scans and len(span) - scans[-1].end() <= 45 and not re.search(r"\b(?:BG|FINGER|GLUCOMETER|LAB|HCP|HOSPITAL|COMPETITOR|BUILT|CAPILLARY)", span[scans[-1].end():]):
        return "sensor", "strong", len(span) - scans[-1].end()   # "SCAN RESULTS FROM THE ADC METER SHOWED 40 MG/DL": a scan is the sensor
    # "...THE SENSOR ENDED AND CUSTOMER CHECKED HIS BLOOD GLUCOSE WAS 197": a reference word glued to the number
    # beats a sensor word further back (Medtronic and Dexcom texts call the fingerstick "blood glucose")
    glued = re.search(r"\b(?:BLOOD\s+(?:GLUCOSE|SUGAR)|FINGER\s*-?\s*STICK|FINGERSTICK|METER|BG)\s+(?:\(BG\)\s+)?(?:WAS|IS|WERE|OF|AT|READ|READING\s+WAS|LEVEL\s+WAS|LEVEL\s+OF)\s*$", span)
    if glued and len(span) - glued.start() <= 40:
        last_sensor_end = None
        for m in RE_ROLE.finditer(span[:glued.start()]):
            if _classify_role(m.group(0))[0] == "sensor":
                last_sensor_end = m.end()
        if last_sensor_end is None or glued.start() - last_sensor_end > 30:
            return "meter", "strong", len(span) - glued.end()     # the sensor word (if any) is far away: "THE CGM BG WAS 60" stays a sensor value
    best = None
    for m in RE_ROLE.finditer(span):
        role, strength = _classify_role(m.group(0))
        dist = len(span) - m.end()
        if role == "block":
            best = ("block", "strong", dist)          # the latest word wins; a later role word replaces it
        elif role:
            if best is None or best[0] == "block" or strength == "strong" or best[1] == "weak":
                if best is not None and best[0] != "block" and best[1] == "strong" and strength == "weak":
                    continue                          # keep a strong word over a later weak one
                best = (role, strength, dist)
    return best if best else (None, None, None)


def _role_after(sent, val):
    """Role word right after the number through filler words only: "55 MG/DL OBTAINED ON THE ADC DEVICE"."""
    span = sent[val["end"]:val["end"] + 110]
    cut = RE_CONNECT.search(span)
    if cut:
        span = span[:cut.start()]
    dm = re.search(r"\d", span)
    if dm:
        span = span[:dm.start()]
    m = RE_ROLE.search(span)
    if not m:
        return None, None, None
    role, strength = _classify_role(m.group(0))
    if role in (None, "block"):
        return None, None, None
    if AFTER_FILL.fullmatch(span[:m.start()]) is None:
        return None, None, None
    return role, strength, m.start()


RE_HCP_WORDS = re.compile(r"\b(?:HCP|HEALTHCARE|HEALTH\s*CARE|PARAMEDICS?|DOCTOR|NURSE|PHYSICIAN|HOSPITAL|EMS|EMTS?|CLINIC|ER|ED)\b")
RE_A1C = re.compile(r"\bA1C\b|HBA1C")
RE_LIST_SEP = re.compile(r"^\s*(?:,|;|/|&|\+|AND|OR|,\s*AND|,\s*OR)?\s*$")
RE_RANGE_BEFORE = re.compile(rf"(?:\d|{UNIT2})\s*(?:-|TO)\s*$")


def find_values(sent):
    """All glucose numbers in one sentence with their roles. Returns (list of value dicts in text order, erratic flag)."""
    if RE_A1C.search(sent):
        return [], False                              # an A1C sentence: its numbers are not glucose readings
    vals = []
    for m in RE_VAL2.finditer(sent):
        if RE_RANGE_BEFORE.search(sent[max(0, m.start("n") - 14):m.start("n")]):
            # "170 MG/DL - 180 MG/DL", "51 MG/DL TO 70 MG/DL": keep the first number, flag the range
            if vals and m.start("n") - vals[-1]["end"] <= 6:
                vals[-1]["end"], vals[-1]["range"] = m.end(), True
                vals[-1]["raw"] = sent[vals[-1]["raw_start"]:m.end()].strip()
            continue                                  # "FROM 90 TO 500 MG/DL": a change over time, not a value
        vals.append(_make_val(sent, m, True))
    taken = [(v["start"], v["end"]) for v in vals]
    for m in RE_ROLE_VAL.finditer(sent):
        s = m.start("n")
        if any(a <= s < b for a, b in taken):
            continue
        v = _make_val(sent, m, False)
        role, strength = _classify_role(m.group("role"))
        if RE_SCAN.search(m.group("role")):
            role, strength = "sensor", "strong"
        v["role"], v["strength"], v["phrase_role"] = role, strength, True
        vals.append(v)
    vals.sort(key=lambda v: v["start"])
    prev_end = 0
    for v in vals:
        if v.get("phrase_role"):
            prev_end = v["end"]
            continue
        rb, sb, db = _role_before(sent, v, prev_end)
        ra, sa, da = _role_after(sent, v)
        prev_end = v["end"]
        if ra == "sensor" and sa == "weak" and RE_HCP_WORDS.search(sent[:v["start"]]) and not RE_SENSOR_WORD_ANY.search(sent[:v["start"]]):
            ra = "meter"                              # "THE HCP OBTAINED A READING OF 147 MG/DL ON THEIR DEVICE": the HCP's device is a meter
        if rb == "block" and (ra is None or db <= 12):
            v["role"] = "block"
            continue
        if rb == "block":
            rb = None
        if rb and ra:
            if sb == sa:
                pick = (rb, sb) if db <= da else (ra, sa)
            else:
                pick = (rb, sb) if sb == "strong" else (ra, sa)
        elif rb:
            pick = (rb, sb)
        elif ra:
            pick = (ra, sa)
        else:
            pick = (None, None)
        v["role"], v["strength"] = pick
    # a list shares one role: "40 MG/DL AND 57 MG/DL ON THE ADC DEVICE" -> both sensor (the first one is used)
    i = 0
    while i < len(vals):
        j = i
        while (j + 1 < len(vals) and RE_LIST_SEP.match(sent[vals[j]["end"]:vals[j + 1]["start"]])
               and (vals[j]["unit"] == vals[j + 1]["unit"] or "none" in (vals[j]["unit"], vals[j + 1]["unit"]))):
            j += 1
        if j > i:
            roles = {v["role"] for v in vals[i:j + 1] if v["role"] not in (None, "block")}
            if len(roles) == 1:
                r = roles.pop()
                st = next(v["strength"] for v in vals[i:j + 1] if v["role"] == r)
                for v in vals[i:j + 1]:
                    if v["role"] is None:
                        v["role"], v["strength"], v["list"] = r, st, True
        i = j + 1
    if RE_ERRATIC.search(sent):
        for v in vals:
            if v["role"] is None:
                v["role"], v["strength"] = "sensor", "strong"
        return vals, True
    return vals, False


def numeric(v):
    return v["role"] != "block" and not v["bound"]


def plausible(s_mgdl, m_mgdl):
    return (SENSOR_RANGE[0] <= s_mgdl <= SENSOR_RANGE[1]) and (METER_RANGE[0] <= m_mgdl <= METER_RANGE[1])


def fix_units(s, mt, text_has_mmol):
    """Unit-less numbers next to an mmol/L number, or small decimals in an mmol/L text, are read as mmol/L."""
    for v, other in ((s, mt), (mt, s)):
        if v["unit"] == "none":
            if (other["unit"].startswith("mmol") and v["value"] < 35) or \
               (text_has_mmol and v["value"] < 35 and "." in v["raw"]) or \
               (other["unit"] == "none" and v["value"] < 35 and other["value"] < 35 and ("." in v["raw"] or "." in other["raw"])):
                v["unit"], v["mgdl"] = "mmol/L (guessed)", float(round(v["value"] * v1.MMOL_FACTOR))


def sentence_list(t):
    return [t[a:b] for a, b in v1.sentence_spans(t)]


def _word_in(sent):
    dw = RE_DISPLAY_WORD.search(sent)
    if not dw:
        return ""
    return next((g for g in (dw.group("w"), dw.group("w2"), dw.group("w3"), dw.group("w4")) if g), "")


def v2_pairs(t, stages):
    """Pairs from the v2 forms. Returns (pairs in stage-priority order, n_candidates, erratic_flag, bound_pairs).
    Each pair: sensor, meter, pattern, sentence."""
    sents = sentence_list(t)
    text_has_mmol = "MMOL" in t
    per = []
    erratic_any = False
    all_cands = set()
    for sent in sents:
        vals, erratic = find_values(sent)
        erratic_any = erratic_any or erratic
        for v in vals:
            if v["role"] != "block" and 20 <= v["mgdl"] <= 1500:
                all_cands.add(v["mgdl"])
        word = _word_in(sent)
        per.append({"text": sent, "vals": vals, "word": word,
                    "sens": [v for v in vals if v["role"] == "sensor" and numeric(v)],
                    "mets": [v for v in vals if v["role"] == "meter" and numeric(v)],
                    "free": [v for v in vals if v["role"] is None and numeric(v)],
                    "s_bound": [v for v in vals if v["role"] == "sensor" and v["bound"]],
                    "m_bound": [v for v in vals if v["role"] == "meter" and v["bound"]]})
        per[-1]["s_pinned"] = bool(word or per[-1]["s_bound"])     # the sensor value in this sentence is a word or a bound

    def mk(s, mt, pid, sent):
        s, mt = dict(s), dict(mt)
        fix_units(s, mt, text_has_mmol)
        if not plausible(s["mgdl"], mt["mgdl"]) or s["mgdl"] == mt["mgdl"]:
            return None
        return {"sensor": s, "meter": mt, "pattern": pid, "sentence": sent}

    same, one_side, implicit, plotted = [], [], [], []
    for p in per:
        sens, mets, free = p["sens"], p["mets"], p["free"]
        if sens and mets:
            # two lists of the same length are paired by position: "52, 93 AND 52 SCAN AGAINST LO (<20), 83 AND 35"
            s_all = [v for v in p["vals"] if v["role"] == "sensor"]
            m_all = [v for v in p["vals"] if v["role"] == "meter"]
            s_pick, m_pick = sens[0], mets[0]
            if len(s_all) == len(m_all) > 1:
                for a, b in zip(s_all, m_all):
                    if numeric(a) and numeric(b):
                        s_pick, m_pick = a, b
                        break
            pr = mk(s_pick, m_pick, "v2_same_sentence", p["text"])
            if pr:
                same.append(pr)
                continue
        # one side labelled, the other side sits across a comparison word
        if (len(sens) + len(mets)) == 1 and len(free) == 1 and not p["s_pinned"] and not p["m_bound"]:
            lab = (sens or mets)[0]
            other = free[0]
            a, b = sorted([lab, other], key=lambda v: v["start"])
            if STRONG_CONNECT.search(p["text"][a["end"]:b["start"]]):
                pr = mk(lab, other, "v2_comparison_one_side", p["text"]) if sens else mk(other, lab, "v2_comparison_one_side", p["text"])
                if pr:
                    one_side.append(pr)
                    continue
        # no labels at all: "55 COMPARED TO 210", "RESULTS OF 2.1 AND 12.1 WERE PLOTTED" (Abbott convention: sensor first)
        if not sens and not mets and len(free) == 2 and not p["s_pinned"] and not p["m_bound"]:
            a, b = free
            between = p["text"][a["end"]:b["start"]]
            if STRONG_CONNECT.search(between):
                pr = mk(a, b, "v2_comparison_implicit", p["text"])
                if pr:
                    implicit.append(pr)
                    continue
            pm = RE_PLOTTED.search(p["text"])
            if pm and not erratic_any and not RE_PLOT_ERRATIC_WORDS.search(t) and pm.start() <= a["start"] and pm.end() >= b["end"]:
                pr = mk(a, b, "v2_plotted_pair", p["text"])
                if pr:
                    plotted.append(pr)
    # neighbouring sentences: sensor-only sentence next to meter-only sentence (one or two sentences apart).
    # Not when the other sentence already holds the partner as a bound or a display word ("LO (<40) vs 31 MG/DL").
    adjacent = []
    for i, p in enumerate(per):
        sens, mets = p["sens"], p["mets"]
        if bool(sens) == bool(mets):
            continue
        if (sens and p["m_bound"]) or (mets and p["s_pinned"]):
            continue
        for j in (i + 1, i + 2):
            if j >= len(per):
                break
            q = per[j]
            if sens and q["mets"] and not q["sens"] and not q["s_pinned"]:
                pr = mk(sens[0], q["mets"][0], "v2_adjacent_sentence", p["text"] + " || " + q["text"])
            elif mets and q["sens"] and not q["mets"] and not q["m_bound"]:
                pr = mk(q["sens"][0], mets[0], "v2_adjacent_sentence", p["text"] + " || " + q["text"])
            else:
                pr = None
            if pr:
                adjacent.append(pr)
                break
            if q["sens"] or q["mets"] or q["s_pinned"] or q["m_bound"]:
                break
    # whole text: exactly one sensor number and exactly one meter number, and no bound or display word anywhere
    unique = []
    all_s = [(p["text"], v) for p in per for v in p["sens"]]
    all_m = [(p["text"], v) for p in per for v in p["mets"]]
    pinned_any = any(p["s_pinned"] or p["m_bound"] for p in per)
    if len({v["mgdl"] for _, v in all_s}) == 1 and len({v["mgdl"] for _, v in all_m}) == 1 and not pinned_any:
        pr = mk(all_s[0][1], all_m[0][1], "v2_text_unique", all_s[0][0] + " || " + all_m[0][0])
        if pr:
            unique.append(pr)
    # one side is a bound or a display word: "CGM READ LOW ... BG WAS 123", "SENSOR 130 AND BG OVER 600"
    bound_pairs = []
    for i, p in enumerate(per):
        if p["mets"] and p["s_pinned"] and not p["sens"]:
            sb = p["s_bound"][0] if p["s_bound"] else None
            bound_pairs.append({"sensor_bound": (sb["bound"] + v1.fmt_num(sb["mgdl"])) if sb else "", "word": p["word"],
                                "meter": p["mets"][0], "pattern": "v2_bound_pair", "sentence": p["text"]})
        elif p["sens"] and p["m_bound"] and not p["mets"]:
            mb = p["m_bound"][0]
            bound_pairs.append({"sensor": p["sens"][0], "meter_bound": mb["bound"] + v1.fmt_num(mb["mgdl"]), "word": "",
                                "pattern": "v2_bound_pair", "sentence": p["text"]})
        elif p["s_pinned"] and not p["sens"] and not p["mets"]:
            for j in (i + 1, i + 2):          # "SENSOR READ HI (>500 MG/DL). ... A PARAMEDIC METER READING OF 1.1 MMOL/L"
                if j >= len(per):
                    break
                q = per[j]
                if q["mets"] and not q["sens"] and not q["s_pinned"]:
                    sb = p["s_bound"][0] if p["s_bound"] else None
                    bound_pairs.append({"sensor_bound": (sb["bound"] + v1.fmt_num(sb["mgdl"])) if sb else "", "word": p["word"],
                                        "meter": q["mets"][0], "pattern": "v2_bound_pair_adjacent", "sentence": p["text"] + " || " + q["text"]})
                    break
                if q["sens"] or q["mets"] or q["s_pinned"]:
                    break
    ordered = []
    for group in (same, one_side, implicit, plotted, adjacent, unique):
        ordered += [pr for pr in group if pr["pattern"] in stages]
    roles = {}                      # value (mg/dL) -> the roles v2 gave it anywhere in the text ("block" and "bound" included)
    for p in per:
        for v in p["vals"]:
            if v["role"] is not None:
                roles.setdefault(v["mgdl"], set()).add(v["role"])
            if v["bound"]:
                roles.setdefault(v["mgdl"], set()).add("bound")
    return ordered, len(all_cands), erratic_any, bound_pairs, roles


def display_word(t):
    m = RE_DISPLAY_WORD.search(t)
    if not m:
        return ""
    return next((g for g in (m.group("w"), m.group("w2"), m.group("w3"), m.group("w4")) if g), "")


def wear_day_v2(t, use_v2=True):
    """v1 wear-day forms first, then the v2 forms. Returns (day or None, pattern id)."""
    day, _, flag = v1.wear_day(t)
    if day is not None:
        return day, "v1"
    if flag or not use_v2:
        return None, ""
    for i, rx in enumerate(RE_WEAR_V2):
        for m in rx.finditer(t):
            if i == 10:   # "AFTER n DAYS" needs a sensor word in the same sentence
                a = t.rfind(". ", 0, m.start()) + 1
                b = t.find(". ", m.end())
                if not RE_SENSOR_WORD_ANY.search(t[a:b if b > 0 else len(t)]):
                    continue
            raw = next((g for g in m.groups() if g), None)      # patterns with two alternatives have two groups
            if raw is None:
                continue
            d = v1.WORDNUM.get(raw) if raw in v1.WORDNUM else int(raw)
            if d is None or d < 1 or d > v1.MAX_WEAR_DAY:
                continue
            return d, f"v2_{i + 1}"
    if RE_WEAR_HOURS.search(t):
        return 1, "v2_first_day"
    return None, ""


# ----------------------------------------------------------------------------
# The v2 extractor: one report -> one output row
# ----------------------------------------------------------------------------
SAME_SENTENCE_V2 = ("v2_same_sentence", "v2_comparison_one_side", "v2_comparison_implicit", "v2_plotted_pair")


def extract_v2(report, stages=None):
    """report: dict with mdr_report_key, event_type, brand, year_received, product_code, text.
    stages: which pair stages to use (default all). Returns the output row (dict)."""
    stages = STAGES if stages is None else stages
    raw = report.get("text") or ""
    t = v1.norm(raw[:MAX_TEXT_CHARS])
    row = {c: "" for c in OUTPUT_COLUMNS}
    row.update({"mdr_report_key": report.get("mdr_report_key", ""), "event_type": report.get("event_type", ""),
                "event_group": event_group(report.get("event_type", "")), "brand": report.get("brand", ""),
                "year_received": report.get("year_received", ""), "product_code": report.get("product_code", ""),
                "text_chars": len(raw), "has_text": "yes" if t.strip() else "no", "pattern": "none", "n_candidates": 0,
                "two_sensor_readings": "no"})
    if not t.strip():
        return row

    # --- pairs. v1 first (template, then prose in one sentence), then the v2 forms; a v1 pair from two
    #     neighbouring sentences gives way to any v2 pair found inside one sentence.
    v1_pair, v1_flags = None, []
    if any(s in stages for s in V1_STAGES):
        v1_row = v1.extract_report({"text": raw, "mdr_report_key": "", "maker": "", "brand_name": "", "event_type": ""})
        if v1_row["pair_found"] == "yes":
            pid = "abbott_template" if v1_row["pair_scope"] == "template" else (
                "v1_prose_same_sentence" if v1_row["pair_scope"] == "same_sentence" else "v1_prose_adjacent_sentence")
            if pid in stages:
                s_m, m_m = float(v1_row["sensor_value_mgdl"]), float(v1_row["meter_value_mgdl"])
                if v1.is_bound_raw(v1_row["sensor_value_raw"]) or v1.is_bound_raw(v1_row["meter_value_raw"]):
                    pass    # a bound ("OVER 600 MG/DL") is not a value (gold rubric)
                elif plausible(s_m, m_m) and s_m != m_m:
                    v1_pair = {"sensor": {"mgdl": s_m, "raw": v1_row["sensor_value_raw"], "unit": v1_row["sensor_unit"]},
                               "meter": {"mgdl": m_m, "raw": v1_row["meter_value_raw"], "unit": v1_row["meter_unit"]},
                               "pattern": pid, "sentence": v1_row["match_pair_sentence"]}
                    if v1_row["mmol_converted"] == "yes":
                        v1_flags.append("mmol")
                    if v1_row["multiple_pairs"] == "yes":
                        v1_flags.append("multiple_pairs")
    v2, n_cands, erratic, bound_pairs, roles = v2_pairs(t, stages)
    v2 = [p for p in v2 if not (p["pattern"] == "v2_comparison_implicit" and n_cands > 2)]   # implicit roles need a clean text
    row["n_candidates"] = n_cands
    row["two_sensor_readings"] = "yes" if erratic else "no"
    v2_on = any(s.startswith("v2") for s in stages)
    if v2_on and v1_pair is not None and v1_pair["pattern"] != "abbott_template":
        s_roles = roles.get(v1_pair["sensor"]["mgdl"], set())
        m_roles = roles.get(v1_pair["meter"]["mgdl"], set())
        if ("block" in s_roles or "block" in m_roles or "bound" in s_roles or "bound" in m_roles
                or (s_roles and "sensor" not in s_roles) or (m_roles and "meter" not in m_roles)):
            v1_pair = None      # v1 prose took a setting, dose, difference or bound, or gave a number the opposite role
                                # ("THE CGM WAS LOW AND THE BG WAS 315 MG/DL": 315 is the meter, the sensor showed a word)
    pair, flags = None, []
    if v1_pair is not None and v1_pair["pattern"] != "v1_prose_adjacent_sentence":
        pair, flags = v1_pair, v1_flags
    elif v1_pair is not None:
        pair = next((p for p in v2 if p["pattern"] in SAME_SENTENCE_V2), None)
        if pair is None:
            pair, flags = v1_pair, v1_flags
    elif v2:
        pair = v2[0]
    if pair is not None and pair["pattern"].startswith("v2"):
        for v in (pair["sensor"], pair["meter"]):
            if v.get("range"):
                flags.append("range")
            if v.get("approx"):
                flags.append("approx")
            if v.get("list"):
                flags.append("list")
            if v["unit"] == "none":
                flags.append("unitless")
            if v["unit"].startswith("mmol"):
                flags.append("mmol_guessed" if "guessed" in v["unit"] else "mmol")
    if pair is not None:
        s, mt = pair["sensor"], pair["meter"]
        err = s["mgdl"] - mt["mgdl"]
        units = sorted({u for u in (s.get("unit", ""), mt.get("unit", "")) if u})
        row.update({"sensor_value": v1.fmt_num(s["mgdl"]), "meter_value": v1.fmt_num(mt["mgdl"]),
                    "unit": "/".join(units), "error_mgdl": v1.fmt_num(err), "error_pct": f"{100.0 * err / mt['mgdl']:.1f}",
                    "direction": "low" if err < 0 else "high", "meter_band": meter_band(mt["mgdl"]),
                    "sensor_raw": s.get("raw", ""), "meter_raw": mt.get("raw", ""), "pattern": pair["pattern"],
                    "match_text": (pair.get("sentence") or "")[:300]})
    elif bound_pairs:
        bp = bound_pairs[0]
        row["bound_pattern"] = bp["pattern"]
        row["match_text"] = bp["sentence"][:300]
        if "meter" in bp:
            row.update({"meter_value": v1.fmt_num(bp["meter"]["mgdl"]), "meter_raw": bp["meter"]["raw"],
                        "meter_band": meter_band(bp["meter"]["mgdl"]), "sensor_bound": bp["sensor_bound"]})
        else:
            row.update({"sensor_value": v1.fmt_num(bp["sensor"]["mgdl"]), "sensor_raw": bp["sensor"]["raw"],
                        "meter_bound": bp["meter_bound"]})
    row["value_flags"] = ";".join(sorted(set(flags)))

    # --- display word (and the bound it implies), wear day, zone
    word = display_word(t)
    row["sensor_display_word"] = word
    if word and not row["sensor_bound"]:
        row["sensor_bound"] = "<40" if word in ("LOW", "LO") else (">500" if report.get("brand") == "Abbott" else ">400")
    day, wp = wear_day_v2(t, use_v2=any(s.startswith("v2") for s in stages))
    row["wear_day"] = "" if day is None else day
    row["wear_pattern"] = wp
    row["zone_stated"], _ = v1.parkes_zone(t)

    # --- keyword flags on text without boilerplate
    clean = v1.strip_boilerplate(t)
    for k, rx in KW.items():
        row[k] = "yes" if rx.search(clean) else "no"
    row["kw_fingerstick"] = "yes" if RE_KW_FINGERSTICK.search(clean) else "no"
    row["kw_ems_or_hospital"] = "yes" if RE_KW_EMS.search(clean) else "no"
    row["kw_death_real"] = "yes" if RE_KW_DEATH.search(clean) else "no"
    row["kw_no_harm_boilerplate"] = "yes" if RE_KW_NOHARM.search(t) else "no"
    return row


# ----------------------------------------------------------------------------
# Loading: run set, model reference, full parquet chunks
# ----------------------------------------------------------------------------
def frame_to_reports(df):
    """Clean-table rows -> report dicts for extract_v2."""
    out = []
    man = df["manufacturer"].fillna("") if "manufacturer" in df else pd.Series([""] * len(df), index=df.index)
    bn = df["brand_name"].fillna("") if "brand_name" in df else pd.Series([""] * len(df), index=df.index)
    dr = df["date_received"].fillna("").astype(str) if "date_received" in df else pd.Series([""] * len(df), index=df.index)
    pc = df["product_code"].fillna("") if "product_code" in df else pd.Series([""] * len(df), index=df.index)
    et = df["event_text"].fillna("") if "event_text" in df else pd.Series([""] * len(df), index=df.index)
    mn = df["mfr_narrative"].fillna("") if "mfr_narrative" in df else pd.Series([""] * len(df), index=df.index)
    ev = df["event_type"].fillna("") if "event_type" in df else pd.Series([""] * len(df), index=df.index)
    for key, m, b, d, p, e, n, evt in zip(df["mdr_report_key"].astype(str), man, bn, dr, pc, et, mn, ev):
        out.append({"mdr_report_key": key, "event_type": evt, "brand": brand_of(m, b), "year_received": d[:4],
                    "product_code": p, "text": v1.build_text(e, n)})
    return out


def load_run_set(path):
    cols = ["mdr_report_key", "date_received", "event_type", "product_code", "brand_name", "manufacturer",
            "event_text", "mfr_narrative", "tier", "weight", "split", "maker"]
    df = pd.read_csv(path, usecols=cols, dtype=str)
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(1.0)
    log(f"run set: {len(df):,} rows")
    return df


def load_model_reference(path, max_rows=None):
    """The model's own numbers (llm block, after the word-for-word guard) plus the combined final values."""
    recs = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_rows and i >= max_rows:
                break
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            llm, fin = r.get("llm") or {}, r.get("final") or {}
            recs.append({"mdr_report_key": str(r["mdr_report_key"]), "maker": r.get("maker"), "split": r.get("split"),
                         "m_sensor": llm.get("sensor_value_mgdl"), "m_meter": llm.get("meter_value_mgdl"),
                         "m_sensor_raw": llm.get("sensor_value_raw"), "m_meter_raw": llm.get("meter_value_raw"),
                         "m_sensor_unit": llm.get("sensor_unit"), "m_meter_unit": llm.get("meter_unit"),
                         "m_wear_day": llm.get("wear_day"), "m_zone": llm.get("parkes_zone_stated"),
                         "m_fault_type": llm.get("fault_type"), "m_confidence": llm.get("confidence"),
                         "f_sensor": fin.get("sensor_value_mgdl"), "f_meter": fin.get("meter_value_mgdl"),
                         "f_wear_day": fin.get("wear_day"), "f_zone": fin.get("parkes_zone_stated")})
    df = pd.DataFrame(recs).drop_duplicates("mdr_report_key", keep="last")
    for c in ("m_sensor", "m_meter", "m_wear_day", "f_sensor", "f_meter", "f_wear_day"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    log(f"model reference: {len(df):,} reports")
    return df


# ----------------------------------------------------------------------------
# Parallel runner
# ----------------------------------------------------------------------------
def _run_chunk(args):
    reports, stages = args
    return [extract_v2(r, stages) for r in reports]


def run_reports(reports, workers, stages=None, chunk=2000, label="regex v2", pool=None):
    """Run extract_v2 over a list of report dicts, in order, on several processes (an existing pool can be reused)."""
    import multiprocessing as mp
    chunks = [(reports[i:i + chunk], stages) for i in range(0, len(reports), chunk)]
    rows = []
    t1 = time.time()
    if workers <= 1:
        for i, c in enumerate(chunks, 1):
            rows.extend(_run_chunk(c))
            if i % 10 == 0:
                log(f"  {label}: {len(rows):,} / {len(reports):,}")
    else:
        own = pool is None
        pool = pool or mp.Pool(workers)
        try:
            for i, part in enumerate(pool.imap(_run_chunk, chunks, chunksize=1), 1):
                rows.extend(part)
                if i % 10 == 0:
                    log(f"  {label}: {len(rows):,} / {len(reports):,}")
        finally:
            if own:
                pool.close()
                pool.join()
    dt = time.time() - t1
    log(f"{label}: {len(rows):,} reports in {dt:.1f} s ({len(rows) / max(dt, 1e-9):,.0f} reports/s, {workers} workers)")
    return rows


def default_workers():
    return max(1, min(20, (os.cpu_count() or 2) - 2))


# ----------------------------------------------------------------------------
# tune: compare with the model on the run set
# ----------------------------------------------------------------------------
def compare_frame(rows, ref):
    """Join regex rows (list of dicts) to the model reference. One row per report."""
    rx = pd.DataFrame(rows)
    for c in ("sensor_value", "meter_value", "wear_day"):
        rx[c] = pd.to_numeric(rx[c], errors="coerce")
    df = ref.merge(rx, on="mdr_report_key", how="left", suffixes=("", "_rx"))
    df["brand_cmp"] = df["brand"].where(df["brand"] != "Senseonics", "Other")   # the model tables use 4 makers
    df["model_pair"] = df["m_sensor"].notna() & df["m_meter"].notna() & df["m_sensor"].between(*SENSOR_RANGE) & df["m_meter"].between(*METER_RANGE)
    df["regex_pair"] = df["sensor_value"].notna() & df["meter_value"].notna()
    both = df["model_pair"] & df["regex_pair"]
    df["exact"] = both & (df["sensor_value"] == df["m_sensor"]) & (df["meter_value"] == df["m_meter"])
    df["within5"] = both & ((df["sensor_value"] - df["m_sensor"]).abs() <= 5) & ((df["meter_value"] - df["m_meter"]).abs() <= 5)
    df["swapped"] = both & (df["sensor_value"] == df["m_meter"]) & (df["meter_value"] == df["m_sensor"]) & ~df["exact"]
    df["one_matches"] = both & ~df["within5"] & ((df["sensor_value"] == df["m_sensor"]) | (df["meter_value"] == df["m_meter"]))
    return df


def recall_table(df, label):
    """Recall and agreement by brand. recall = share of model pairs the regex also found."""
    rows = []
    for b in ["Abbott", "Dexcom", "Medtronic", "Other", "All"]:
        d = df if b == "All" else df[df["brand_cmp"] == b]
        mp_ = d["model_pair"]
        both = mp_ & d["regex_pair"]
        n_model, n_both, n_regex = int(mp_.sum()), int(both.sum()), int(d["regex_pair"].sum())
        rows.append({"version": label, "brand": b, "reports": len(d), "model_pairs": n_model, "regex_pairs": n_regex,
                     "both": n_both, "recall_pct": round(100 * n_both / n_model, 1) if n_model else np.nan,
                     "regex_pair_rate_pct": round(100 * n_regex / len(d), 1) if len(d) else np.nan,
                     "model_pair_rate_pct": round(100 * n_model / len(d), 1) if len(d) else np.nan,
                     "agree_exact_pct": round(100 * d["exact"].sum() / n_both, 1) if n_both else np.nan,
                     "agree_within5_pct": round(100 * d["within5"].sum() / n_both, 1) if n_both else np.nan,
                     "swapped_pct": round(100 * d["swapped"].sum() / n_both, 1) if n_both else np.nan,
                     "one_value_matches_pct": round(100 * d["one_matches"].sum() / n_both, 1) if n_both else np.nan,
                     "regex_only_pairs": int((d["regex_pair"] & ~mp_).sum()),
                     "regex_only_pct_of_regex": round(100 * (d["regex_pair"] & ~mp_).sum() / n_regex, 1) if n_regex else np.nan})
    return pd.DataFrame(rows)


def stage_table(df, label):
    """Per pattern: how many pairs, recall contribution and agreement."""
    rows = []
    for pid, d in df[df["regex_pair"]].groupby("pattern"):
        both = d["model_pair"]
        rows.append({"version": label, "pattern": pid, "regex_pairs": len(d), "also_model": int(both.sum()),
                     "regex_only": int((~both).sum()),
                     "agree_exact_pct": round(100 * d["exact"].sum() / both.sum(), 1) if both.sum() else np.nan,
                     "agree_within5_pct": round(100 * d["within5"].sum() / both.sum(), 1) if both.sum() else np.nan,
                     "swapped_pct": round(100 * d["swapped"].sum() / both.sum(), 1) if both.sum() else np.nan})
    return pd.DataFrame(rows).sort_values("regex_pairs", ascending=False)


def other_fields_table(df, label):
    """Wear day and zone against the model (where the model found one)."""
    rows = []
    for b in ["Abbott", "Dexcom", "Medtronic", "Other", "All"]:
        d = df if b == "All" else df[df["brand_cmp"] == b]
        mw = d["m_wear_day"].notna()
        rw = d["wear_day"].notna()
        mz = d["m_zone"].notna() & (d["m_zone"].astype(str) != "")
        rz = d["zone_stated"].astype(str) != ""
        rows.append({"version": label, "brand": b, "reports": len(d),
                     "model_wear": int(mw.sum()), "regex_wear": int(rw.sum()), "wear_both": int((mw & rw).sum()),
                     "wear_recall_pct": round(100 * (mw & rw).sum() / mw.sum(), 1) if mw.sum() else np.nan,
                     "wear_agree_pct": round(100 * ((mw & rw) & (d["wear_day"] == d["m_wear_day"])).sum() / (mw & rw).sum(), 1) if (mw & rw).sum() else np.nan,
                     "model_zone": int(mz.sum()), "regex_zone": int(rz.sum()), "zone_both": int((mz & rz).sum()),
                     "zone_recall_pct": round(100 * (mz & rz).sum() / mz.sum(), 1) if mz.sum() else np.nan,
                     "zone_agree_pct": round(100 * ((mz & rz) & (d["zone_stated"].astype(str) == d["m_zone"].astype(str))).sum() / (mz & rz).sum(), 1) if (mz & rz).sum() else np.nan})
    return pd.DataFrame(rows)


def cmd_tune(a):
    rs = load_run_set(a.run_set)
    ref = load_model_reference(a.model_jsonl, a.max_rows)
    if a.max_rows:
        rs = rs[rs["mdr_report_key"].isin(ref["mdr_report_key"])]
    reports = frame_to_reports(rs)
    out_dir = Path(a.tables_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    versions = [("v1 baseline", ["abbott_template", "v1_prose_same_sentence", "v1_prose_adjacent_sentence"]),
                ("v2 tuned", STAGES)]
    rec, stg, oth, frames = [], [], [], {}
    for label, stages in versions:
        rows = run_reports(reports, a.workers, stages, label=label)
        df = compare_frame(rows, ref)
        frames[label] = df
        rec.append(recall_table(df, label))
        stg.append(stage_table(df, label))
        oth.append(other_fields_table(df, label))
        log(f"{label}: recall {rec[-1].iloc[-1]['recall_pct']} %, exact {rec[-1].iloc[-1]['agree_exact_pct']} %, "
            f"regex-only {rec[-1].iloc[-1]['regex_only_pairs']}")
    pd.concat(rec).to_csv(out_dir / "h_regex_v2_recall_by_brand.csv", index=False)
    pd.concat(stg).to_csv(out_dir / "h_regex_v2_by_pattern.csv", index=False)
    pd.concat(oth).to_csv(out_dir / "h_regex_v2_wear_zone.csv", index=False)
    # the regex-only pairs of the tuned version: a random 50 for the eye check (seed)
    d = frames["v2 tuned"]
    only = d[d["regex_pair"] & ~d["model_pair"]].copy()
    rng = random.Random(SEED)
    keys = sorted(only["mdr_report_key"].tolist())
    pick = set(rng.sample(keys, min(50, len(keys))))
    spot = only[only["mdr_report_key"].isin(pick)][["mdr_report_key", "brand", "pattern", "sensor_value", "meter_value",
                                                    "sensor_raw", "meter_raw", "m_sensor", "m_meter", "match_text"]]
    spot.sort_values("mdr_report_key").to_csv(out_dir / "h_regex_v2_spotcheck_50.csv", index=False)
    # disagreements of the tuned version, for the audit (first 300, deterministic order)
    dis = d[d["model_pair"] & d["regex_pair"] & ~d["within5"]].sort_values("mdr_report_key")
    dis[["mdr_report_key", "brand", "pattern", "sensor_value", "meter_value", "m_sensor", "m_meter", "m_sensor_raw",
         "m_meter_raw", "match_text"]].head(300).to_csv(out_dir / "h_regex_v2_disagreements_sample.csv", index=False)
    if a.run_set_out:
        # optional per-report tuned output on the run set (for later re-use); not written by default
        pd.DataFrame(frames["v2 tuned"]).to_csv(a.run_set_out, index=False)
        log(f"wrote {a.run_set_out}")
    log("tune done")
    print(pd.concat(rec).to_string(index=False))
    print(pd.concat(stg).to_string(index=False))
    print(pd.concat(oth).to_string(index=False))
    return frames


# ----------------------------------------------------------------------------
# mine: show the sentences around the model's numbers for 400 baseline misses
# ----------------------------------------------------------------------------
def cmd_mine(a):
    rs = load_run_set(a.run_set)
    ref = load_model_reference(a.model_jsonl, a.max_rows)
    if a.max_rows:
        rs = rs[rs["mdr_report_key"].isin(ref["mdr_report_key"])]
    reports = frame_to_reports(rs)
    stages = STAGES if a.stages == "v2" else ["abbott_template", "v1_prose_same_sentence", "v1_prose_adjacent_sentence"]
    rows = run_reports(reports, a.workers, stages, label="baseline for mining")
    df = compare_frame(rows, ref)
    miss = df[df["model_pair"] & ~df["regex_pair"]]
    log(f"model pairs {int(df['model_pair'].sum()):,}; baseline misses {len(miss):,}")
    rng = random.Random(SEED)
    keys = sorted(miss["mdr_report_key"].tolist())
    pick = rng.sample(keys, min(a.n, len(keys)))
    text_of = {r["mdr_report_key"]: r["text"] for r in reports}
    lines = []
    for k in pick:
        r = miss[miss["mdr_report_key"] == k].iloc[0]
        t = v1.norm(text_of[k][:MAX_TEXT_CHARS])
        lines.append(f"### {k} | {r['brand']} | model S={r['m_sensor_raw']} {r['m_sensor_unit']} M={r['m_meter_raw']} {r['m_meter_unit']} | regex {r['pattern']} s={r['sensor_value']} m={r['meter_value']}")
        spans = []
        for tag, rawv in (("S", r["m_sensor_raw"]), ("M", r["m_meter_raw"])):
            s = v1.fmt_num(float(rawv)) if rawv is not None and str(rawv) not in ("", "nan") else str(rawv)
            m = re.search(r"(?<![\d.])" + re.escape(s) + r"(?![\d])", t)
            if not m:
                m = re.search(re.escape(str(rawv)), t)
            if m:
                spans.append((tag, m.start(), m.end()))
            else:
                lines.append(f"  [{tag}] value {rawv} not found as digits")
        spans.sort(key=lambda x: x[1])
        merged = []
        for tag, s0, e0 in spans:
            if merged and s0 - merged[-1][2] < 2 * a.context:
                merged[-1] = (merged[-1][0] + tag, merged[-1][1], max(merged[-1][2], e0))
            else:
                merged.append((tag, s0, e0))
        for tag, s0, e0 in merged:
            lines.append(f"  [{tag}] ..." + t[max(0, s0 - a.context):e0 + a.context].replace("\n", " ") + "...")
    Path(a.out).write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote {a.out} ({len(pick)} reports)")


# ----------------------------------------------------------------------------
# full: every report in full.parquet
# ----------------------------------------------------------------------------
def cmd_full(a):
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(a.full_parquet)
    n_rg, n_rows = pf.metadata.num_row_groups, pf.metadata.num_rows
    cols = ["mdr_report_key", "date_received", "event_type", "product_code", "brand_name", "manufacturer",
            "event_text", "mfr_narrative"]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    log(f"full run: {n_rows:,} reports in {n_rg} row groups -> {out} ({a.workers} workers)")
    import multiprocessing as mp
    done = 0
    t1 = time.time()
    pool = mp.Pool(a.workers) if a.workers > 1 else None
    try:
        with gzip.open(out, "wt", encoding="utf-8", newline="", compresslevel=6) as f:
            w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
            w.writeheader()
            for g in range(n_rg):
                if a.max_groups and g >= a.max_groups:
                    break
                df = pf.read_row_group(g, columns=cols).to_pandas()
                reports = frame_to_reports(df)
                rows = run_reports(reports, a.workers, None, label=f"group {g + 1}/{n_rg}", pool=pool)
                w.writerows(rows)
                done += len(rows)
                el = time.time() - t1
                log(f"progress: {done:,} / {n_rows:,} ({100 * done / n_rows:.1f} %), {done / el:,.0f} reports/s, "
                    f"about {(n_rows - done) / max(done / el, 1e-9) / 60:.0f} min left")
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    log(f"full run done: {done:,} reports in {(time.time() - t1) / 60:.1f} min")
    if not a.no_report:
        cmd_report(a)


# ----------------------------------------------------------------------------
# report: tables and figures from the full-corpus file
# ----------------------------------------------------------------------------
def cmd_report(a):
    import report_regex_v2  # noqa: F401  (kept in a separate module so `full` stays small)
    report_regex_v2.main(a)


# ----------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["tune", "mine", "full", "report"])
    ap.add_argument("--run-set", default=str(FDA / "clean" / "run_set.csv.gz"))
    ap.add_argument("--model-jsonl", default=str(FDA / "clean" / "text_extract_v3.jsonl"))
    ap.add_argument("--full-parquet", default=str(FDA / "clean" / "full.parquet"))
    ap.add_argument("--sample-parquet", default=str(FDA / "clean" / "sample_local.parquet"))
    ap.add_argument("--out", default=None, help="full: output csv.gz (default clean/regex_v2_full.csv.gz); mine: text file")
    ap.add_argument("--tables-dir", default=str(FDA / "results" / "text" / "tables"))
    ap.add_argument("--figures-dir", default=str(FDA / "results" / "text" / "figures"))
    ap.add_argument("--workers", type=int, default=default_workers())
    ap.add_argument("--max-rows", type=int, default=None, help="tune/mine: only the first N model rows (quick test)")
    ap.add_argument("--max-groups", type=int, default=None, help="full: only the first N row groups (quick test)")
    ap.add_argument("--n", type=int, default=400, help="mine: how many missed reports to print")
    ap.add_argument("--context", type=int, default=110, help="mine: characters of context around each value")
    ap.add_argument("--stages", default="v1", help="mine: 'v1' (baseline misses) or 'v2' (tuned misses)")
    ap.add_argument("--no-report", action="store_true", help="full: skip the report step")
    ap.add_argument("--run-set-out", default=None, help="tune: also write the per-report tuned output on the run set to this CSV")
    a = ap.parse_args(argv)
    if a.out is None:
        if a.command in ("full", "report"):
            a.out = str(FDA / "clean" / "regex_v2_full.csv.gz")
        else:   # mine: a working file with text snippets; keep it out of the repo
            a.out = str(Path(os.environ.get("TEMP", ".")) / "regex_v2_misses.txt")
    {"tune": cmd_tune, "mine": cmd_mine, "full": cmd_full, "report": cmd_report}[a.command](a)


if __name__ == "__main__":
    main()
