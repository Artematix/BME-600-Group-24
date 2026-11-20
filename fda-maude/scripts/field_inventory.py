#!/usr/bin/env python
"""
field_inventory.py : what is in the MAUDE reports that we have not used yet (Phase 1, BMEN 600 Group 24).

Five parts, one script, no required arguments:
  1. Field inventory. Fill rate (share of reports where a field is not blank) and top values for every
     column of clean/serious.csv.gz and clean/sample_local.parquet. Then streams ONE raw openFDA bulk zip
     and lists every field the raw records carry, marks which ones the clean step drops, with fill rates.
  2. Demographics. Age and sex fill rates by maker, event type and year; age bands; sex split;
     filled vs unfilled reports; age found in the text when the field is blank; the trial cohort side by side.
  3. A stratified random sample of 300 report texts (seed 20261106) for hand reading. Keys only are saved
     in results/inventory/sample_300_keys.txt; the texts go to --write-texts PATH (default: not written).
  4. Text themes as patterns (regex), run over all serious reports and the weighted malfunction sample.
  5. Beyond death + injury: wrong-readings share of malfunction reports, identical (template) texts,
     the size of a bigger text run and what it would cost.

Usage (from the repo root; Windows: plain `python`):
  python fda-maude/scripts/field_inventory.py
  python fda-maude/scripts/field_inventory.py --zip fda-maude/raw/bulk_zips/2025q1_0001-of-0008.zip
  python fda-maude/scripts/field_inventory.py --skip-zip --write-texts some/folder/sample_300_texts.txt

Reads (never writes): clean/serious.csv.gz, clean/full.parquet, clean/sample_local.parquet,
  clean/text_extract_v3.jsonl, one raw bulk zip (optional), scripts/config.json,
  and the trial roster (Uncommitted Data/Raw Data Dump/Replace-BG Dataset/Data Tables/HPtRoster.txt + HScreening.txt).
Writes: results/inventory/*.csv, sample_300_keys.txt, inventory_stats.json.
Time: about 6 to 10 minutes without the zip; the zip stream adds about 1 to 3 minutes per 75 MB zip.
"""

import argparse
import collections
import gzip
import json
import re
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

SEED = 20261106
HERE = Path(__file__).resolve().parent
FDA = HERE.parent
REPO = FDA.parent
CLEAN = FDA / "clean"
OUT = FDA / "results" / "inventory"
TRIAL_DIR = REPO / "Uncommitted Data" / "Raw Data Dump" / "Replace-BG Dataset" / "Data Tables"
DEFAULT_ZIP = FDA / "raw" / "bulk_zips" / "2025q1_0001-of-0008.zip"

MISSING = {"", "na", "n/a", "unknown", "unk", "none", "*"}   # "*" = FDA's "not provided"
ACCURACY_TERMS = ["Incorrect, Inadequate or Imprecise Result or Readings", "Low Readings", "High Readings", "Imprecision"]
TEMPLATE_MIN_COPIES = 1000      # an identical text shared by this many malfunction reports = a maker template
MIN_TEXT_CHARS = 120            # shorter texts carry no story
REPORTS_PER_MINUTE = 217        # measured on the full model run (TEXT_RESULTS.md)

T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f} s] {msg}", flush=True)


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def _s(v):
    """Null-safe string: None, pandas NA and NaN become ''."""
    if v is None or v is pd.NA:
        return ""
    if isinstance(v, float) and v != v:
        return ""
    return str(v)


def maker_of(*names):
    s = " ".join(_s(n) for n in names).upper()
    if "ABBOTT" in s or "LIBRE" in s:
        return "Abbott"
    if "DEXCOM" in s:
        return "Dexcom"
    if "MEDTRONIC" in s or "MINIMED" in s or "GUARDIAN" in s or "SIMPLERA" in s or "ENLITE" in s:
        return "Medtronic"
    if "SENSEONICS" in s or "EVERSENSE" in s:
        return "Senseonics"
    return "Other"


def maker4(m):
    """Text tables use four groups, like TEXT_RESULTS.md."""
    return m if m in ("Abbott", "Dexcom", "Medtronic") else "Other"


def family_of(brand, maker):
    b = _s(brand).upper()
    if maker == "Abbott":
        if "LIBRE 3" in b or "LIBRE3" in b:
            return "Abbott Libre 3 / 3 Plus"
        if "LIBRE 2" in b or "LIBRE2" in b:
            return "Abbott Libre 2 / 2 Plus"
        return "Abbott Libre 14-day / other"
    if maker == "Dexcom":
        for g in ("G7", "G6", "G5", "G4"):
            if g in b:
                return f"Dexcom {g}"
        if "STELO" in b:
            return "Dexcom Stelo"
        return "Dexcom other"
    if maker == "Medtronic":
        return "Medtronic Guardian / other"
    if maker == "Senseonics":
        return "Senseonics Eversense"
    return "Other / unknown"


def is_filled(series):
    """True where a clean-table value is really there (not blank, NA, Unknown or '*')."""
    s = series.astype("string").str.strip()
    return s.notna() & ~s.str.lower().isin(MISSING)


def pct(n, d):
    return round(100.0 * n / d, 1) if d else float("nan")


def age_years(value, unit):
    f = {"YR": 1.0, "MO": 1 / 12, "WK": 1 / 52, "DA": 1 / 365, "HR": 0.0}
    v = pd.to_numeric(value, errors="coerce")
    factor = unit.map(f)
    yrs = v * factor
    return yrs.where((yrs >= 0) & (yrs <= 110))


def age_band(yrs):
    return pd.cut(yrs, [-0.01, 17.999, 39.999, 64.999, 200], labels=["< 18", "18-39", "40-64", "65+"])


def write_csv(df, name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    df.to_csv(p, index=False)
    log(f"wrote {p.relative_to(REPO)} ({len(df)} rows)")


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def load_serious():
    log("loading clean/serious.csv.gz ...")
    df = pd.read_csv(CLEAN / "serious.csv.gz", dtype=str, keep_default_na=True, low_memory=False)
    df["maker"] = [maker_of(m, b) for m, b in zip(df["manufacturer"], df["brand_name"])]
    df["maker4"] = df["maker"].map(maker4)
    df["family"] = [family_of(b, m) for b, m in zip(df["brand_name"], df["maker"])]
    df["year"] = df["date_received"].str[:4]
    df["text"] = (df["event_text"].fillna("") + " || " + df["mfr_narrative"].fillna("")).str.upper()
    df["has_text"] = df["text"].str.strip().str.len() > 4
    log(f"serious: {len(df):,} reports, {df['has_text'].sum():,} with text")
    return df


def load_sample():
    log("loading clean/sample_local.parquet ...")
    df = pq.read_table(CLEAN / "sample_local.parquet").to_pandas()
    df["maker"] = [maker_of(m, b) for m, b in zip(df["manufacturer"], df["brand_name"])]
    df["maker4"] = df["maker"].map(maker4)
    df["year"] = df["date_received"].astype("string").str[:4]
    df["text"] = (df["event_text"].fillna("").astype(str) + " || " + df["mfr_narrative"].fillna("").astype(str)).str.upper()
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0.0)
    log(f"sample: {len(df):,} reports, weights add up to {df['weight'].sum():,.0f} malfunction reports")
    return df


def load_llm():
    """clean/text_extract_v3.jsonl -> DataFrame of the final form (one row per report)."""
    p = CLEAN / "text_extract_v3.jsonl"
    if not p.exists():
        log("text_extract_v3.jsonl not found; parts that need it are skipped")
        return None
    log("loading clean/text_extract_v3.jsonl (124,599 lines; about a minute) ...")
    rows = []
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            r = json.loads(line)
            fin = r.get("final") or {}
            rows.append({
                "mdr_report_key": str(r.get("mdr_report_key")), "split": r.get("split"),
                "llm_maker": r.get("maker"), "llm_event_type": r.get("event_type"),
                "fault_type": fin.get("fault_type"), "sensor_mgdl": fin.get("sensor_value_mgdl"),
                "meter_mgdl": fin.get("meter_value_mgdl"), "outcome": fin.get("outcome_severity"),
                "user_action": fin.get("user_action"), "wear_day": fin.get("wear_day"),
            })
            if i % 40000 == 0 and i:
                log(f"  {i:,} lines")
    df = pd.DataFrame(rows)
    df["sensor_mgdl"] = pd.to_numeric(df["sensor_mgdl"], errors="coerce")
    df["meter_mgdl"] = pd.to_numeric(df["meter_mgdl"], errors="coerce")
    ok = df["sensor_mgdl"].between(20, 600) & df["meter_mgdl"].between(20, 1500)
    df["has_pair"] = ok
    df["err_pct"] = np.where(ok, 100.0 * (df["sensor_mgdl"] - df["meter_mgdl"]) / df["meter_mgdl"], np.nan)
    df["err_mgdl"] = np.where(ok, df["sensor_mgdl"] - df["meter_mgdl"], np.nan)
    log(f"model forms: {len(df):,} ({df['has_pair'].sum():,} usable pairs)")
    return df


# ----------------------------------------------------------------------------
# Part 1: field inventory
# ----------------------------------------------------------------------------
CATEGORICAL_HINT = {
    "event_type", "product_code", "manufacturer", "patient_outcome", "patient_sex", "patient_age_unit", "patient_race",
    "patient_ethnicity", "report_source_code", "reporter_country_code", "source_type", "type_of_report", "mfr_report_type",
    "adverse_event_flag", "product_problem_flag", "remedial_action", "health_professional", "reporter_occupation_code",
    "reporter_state_code", "event_location", "initial_report_to_fda", "report_to_fda", "report_to_manufacturer",
    "summary_report_flag", "single_use_flag", "previous_use_code", "reprocessed_and_reused_flag", "manufacturer_link_flag",
    "device_operator", "device_availability", "device_evaluated_by_manufacturer", "implant_flag", "date_removed_flag",
    "manufacturer_d_country", "manufacturer_country", "openfda_device_class", "openfda_device_name", "generic_name",
    "noe_summarized", "number_devices_in_event", "number_patients_in_event", "n_devices", "n_patients", "n_mdr_text",
    "repeated_report_number", "all_product_codes", "device_age_text", "family", "maker",
}
SKIP_IN_INVENTORY = {"text", "has_text", "maker4", "year"}


def fill_table(df, weights=None, label="serious"):
    """One row per column: fill rate, unique count, top values."""
    rows = []
    n = len(df)
    wsum = float(weights.sum()) if weights is not None else None
    for c in df.columns:
        if c in SKIP_IN_INVENTORY:
            continue
        filled = is_filled(df[c])
        s = df.loc[filled, c].astype(str).str.strip()
        nun = s.nunique()
        top = ""
        if c in CATEGORICAL_HINT or nun <= 25:
            vc = s.value_counts().head(6)
            top = " | ".join(f"{str(v)[:60]} ({k:,})" for v, k in vc.items())
        row = {"column": c, "n_reports": n, "n_filled": int(filled.sum()), "fill_pct": pct(filled.sum(), n),
               "n_unique_values": int(nun),
               "star_or_unknown_n": int((df[c].astype("string").str.strip().str.lower().isin({"*", "unknown", "unk"})).sum()),
               "top_values": top,
               "example": (s.iloc[0][:80] if len(s) else "")}
        if weights is not None:
            row["weighted_fill_pct"] = round(100.0 * float(weights[filled].sum()) / wsum, 1) if wsum else float("nan")
        rows.append(row)
    out = pd.DataFrame(rows)
    out.insert(0, "table", label)
    return out


def fill_by_group(df, cols, group_col, label):
    rows = []
    for g, part in df.groupby(group_col, observed=True, dropna=False):
        row = {"table": label, "group_by": group_col, "group": str(g), "n_reports": len(part)}
        for c in cols:
            row[f"{c}_fill_pct"] = pct(is_filled(part[c]).sum(), len(part))
        rows.append(row)
    return pd.DataFrame(rows)


# Raw record paths the clean step keeps (from scripts/maude_robot.py clean_row / clean_extras, 2026-10-26).
KEPT_TOP = {
    "mdr_report_key", "report_number", "date_received", "date_of_event", "event_type", "product_problems",
    "report_source_code", "reporter_country_code", "date_report", "date_manufacturer_received", "date_report_to_fda",
    "date_report_to_manufacturer", "date_facility_aware", "date_added", "date_changed", "source_type", "type_of_report",
    "mfr_report_type", "adverse_event_flag", "product_problem_flag", "remedial_action", "health_professional",
    "reporter_occupation_code", "reporter_state_code", "event_location", "initial_report_to_fda", "report_to_fda",
    "report_to_manufacturer", "summary_report_flag", "noe_summarized", "single_use_flag", "previous_use_code",
    "reprocessed_and_reused_flag", "manufacturer_link_flag", "number_devices_in_event", "number_patients_in_event",
    "pma_pmn_number", "exemption_number", "removal_correction_number", "event_key", "suppl_dates_fda_received",
    "suppl_dates_mfr_received", "manufacturer_name", "manufacturer_country", "distributor_name",
}
KEPT_DEV = {
    "device_report_product_code", "brand_name", "generic_name", "manufacturer_d_name", "model_number", "lot_number",
    "catalog_number", "udi_di", "udi_public", "device_operator", "device_availability",
    "device_evaluated_by_manufacturer", "expiration_date_of_device", "implant_flag", "date_removed_flag",
    "device_age_text", "device_sequence_number", "device_event_key", "manufacturer_d_country", "other_id_number",
    "openfda.device_name", "openfda.device_class", "openfda.regulation_number",
}
KEPT_PAT = {"patient_sequence_number", "patient_age", "patient_sex", "patient_weight", "patient_race",
            "patient_ethnicity", "patient_problems", "sequence_number_outcome", "sequence_number_treatment"}
KEPT_TEXT = {"text", "text_type_code"}   # only the D5 and H10 texts are kept


def kept_path(path):
    if path.startswith("device[]."):
        return path[len("device[]."):] in KEPT_DEV
    if path.startswith("patient[]."):
        return path[len("patient[]."):] in KEPT_PAT
    if path.startswith("mdr_text[]."):
        return path[len("mdr_text[]."):] in KEPT_TEXT
    return path in KEPT_TOP


def _nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, list):
        return any(_nonempty(x) for x in v)
    if isinstance(v, dict):
        return any(_nonempty(x) for x in v.values())
    return True


def _is_star(v):
    return isinstance(v, str) and v.strip() == "*"


def walk_fill(obj, prefix, present, filled, star):
    """Count, per flattened path, whether this record has the field and whether it is filled."""
    for k, v in obj.items():
        path = prefix + k
        if isinstance(v, dict):
            present[path] += 1
            walk_fill(v, path + ".", present, filled, star)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            present[path + "[]"] += 1
            seen_present, seen_filled, seen_star = collections.Counter(), collections.Counter(), collections.Counter()
            for el in v:
                p2, f2, s2 = collections.Counter(), collections.Counter(), collections.Counter()
                walk_fill(el, path + "[].", p2, f2, s2)
                seen_present |= p2
                seen_filled |= f2
                seen_star |= s2
            for kk in seen_present:
                present[kk] += 1
            for kk in seen_filled:
                filled[kk] += 1
            for kk in seen_star:
                star[kk] += 1
        else:
            present[path] += 1
            if _nonempty(v):
                filled[path] += 1
            if _is_star(v):
                star[path] += 1


def stream_zip_records(zip_path):
    """Yield the records of one openFDA bulk zip without loading the whole file."""
    dec = json.JSONDecoder()
    with zipfile.ZipFile(zip_path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".json")][0]
        with zf.open(name) as fb:
            buf = ""
            pos = 0
            started = False
            chunk = 8 * 1024 * 1024
            while True:
                if not started:
                    m = re.search(r'"results"\s*:\s*\[', buf[pos:])
                    if m:
                        pos = pos + m.end()
                        started = True
                    if not started:
                        more = fb.read(chunk)
                        if not more:
                            return
                        buf += more.decode("utf-8", "replace")
                        continue
                # skip whitespace and commas
                while pos < len(buf) and buf[pos] in " \r\n\t,":
                    pos += 1
                if pos >= len(buf):
                    more = fb.read(chunk)
                    if not more:
                        return
                    buf = buf[pos:] + more.decode("utf-8", "replace")
                    pos = 0
                    continue
                if buf[pos] == "]":
                    return
                try:
                    obj, end = dec.raw_decode(buf, pos)
                except json.JSONDecodeError:
                    more = fb.read(chunk)
                    if not more:
                        return
                    buf = buf[pos:] + more.decode("utf-8", "replace")
                    pos = 0
                    continue
                pos = end
                yield obj
                if pos > 4 * chunk:
                    buf = buf[pos:]
                    pos = 0


def part1_raw_zip(zip_path, codes):
    log(f"streaming raw zip {zip_path.name} ({zip_path.stat().st_size / 1e6:.0f} MB) ...")
    present, filled, star = collections.Counter(), collections.Counter(), collections.Counter()
    c_present, c_filled, c_star = collections.Counter(), collections.Counter(), collections.Counter()
    text_types, text_types_cgm = collections.Counter(), collections.Counter()
    n_all = n_cgm = 0
    for r in stream_zip_records(zip_path):
        n_all += 1
        walk_fill(r, "", present, filled, star)
        is_cgm = any(d.get("device_report_product_code") in codes for d in (r.get("device") or []))
        for t in r.get("mdr_text") or []:
            text_types[t.get("text_type_code") or ""] += 1
            if is_cgm:
                text_types_cgm[t.get("text_type_code") or ""] += 1
        if is_cgm:
            n_cgm += 1
            walk_fill(r, "", c_present, c_filled, c_star)
        if n_all % 20000 == 0:
            log(f"  {n_all:,} records ({n_cgm:,} CGM)")
    log(f"zip done: {n_all:,} records, {n_cgm:,} CGM records")
    rows = []
    for path in sorted(present):
        rows.append({
            "raw_field": path, "kept_by_clean_step": "yes" if kept_path(path) else "no",
            "all_devices_n": n_all, "all_devices_fill_pct": pct(filled[path], n_all),
            "all_devices_star_pct": pct(star[path], n_all),
            "cgm_n": n_cgm, "cgm_fill_pct": pct(c_filled[path], n_cgm), "cgm_star_pct": pct(c_star[path], n_cgm),
        })
    tt = pd.DataFrame([{"text_type_code": k, "all_devices_n": v, "cgm_n": text_types_cgm.get(k, 0),
                        "kept_by_clean_step": "yes" if k in ("Description of Event or Problem", "Additional Manufacturer Narrative") else "no"}
                       for k, v in text_types.most_common()])
    return pd.DataFrame(rows), tt, {"zip": zip_path.name, "records_all": n_all, "records_cgm": n_cgm}


# ----------------------------------------------------------------------------
# Part 2: demographics
# ----------------------------------------------------------------------------
def load_full_demo():
    """The columns of clean/full.parquet needed for demographics and part 5 (3.38 M rows, categoricals)."""
    log("loading demographic columns of clean/full.parquet ...")
    cols = ["mdr_report_key", "event_type", "manufacturer", "brand_name", "date_received", "patient_age_value",
            "patient_age_unit", "patient_sex", "patient_race", "patient_ethnicity", "patient_weight", "source_type",
            "reporter_occupation_code", "health_professional", "device_evaluated_by_manufacturer",
            "device_availability", "remedial_action", "product_problems", "event_text_len", "mfr_narrative_len",
            "patient_outcome", "reporter_country_code"]
    t = pq.read_table(CLEAN / "full.parquet", columns=cols)
    try:   # keys are digits; an int column is far lighter than 3.38 M unique strings
        key_int = pc.cast(t["mdr_report_key"], pa.int64())
        t = t.drop(["mdr_report_key"]).append_column("mdr_report_key", key_int)
    except Exception:
        pass
    year = pc.utf8_slice_codeunits(t["date_received"], 0, 4)
    acc = None
    for term in ACCURACY_TERMS:
        m = pc.match_substring(pc.fill_null(t["product_problems"], ""), term)
        acc = m if acc is None else pc.or_(acc, m)
    weight_filled = pc.is_valid(t["patient_weight"])
    race_filled = pc.is_valid(t["patient_race"])
    eth_filled = pc.is_valid(t["patient_ethnicity"])
    t = t.drop(["date_received", "product_problems", "patient_weight", "patient_race", "patient_ethnicity"])
    t = t.append_column("year", year).append_column("accuracy_code", acc)
    t = t.append_column("weight_filled", weight_filled).append_column("race_filled", race_filled).append_column("eth_filled", eth_filled)
    df = t.to_pandas(strings_to_categorical=True)
    df["mdr_report_key"] = df["mdr_report_key"].astype(str)
    brand_maker = {(m, b): maker_of(m, b) for m, b in set(zip(df["manufacturer"].astype(str), df["brand_name"].astype(str)))}
    df["maker"] = pd.Categorical([brand_maker[(m, b)] for m, b in zip(df["manufacturer"].astype(str), df["brand_name"].astype(str))])
    fam = {(b, m): family_of(b, m) for b, m in set(zip(df["brand_name"].astype(str), df["maker"].astype(str)))}
    df["family"] = pd.Categorical([fam[(b, m)] for b, m in zip(df["brand_name"].astype(str), df["maker"].astype(str))])
    df["age_years"] = age_years(df["patient_age_value"], df["patient_age_unit"].astype("string"))
    df["age_filled"] = df["age_years"].notna()
    sex = df["patient_sex"].astype("string").str.strip()
    df["sex"] = pd.Categorical(np.where(sex.isin(["Female", "Male"]), sex, np.where(sex.notna(), "Prefer not / other", "blank")))
    df["sex_filled"] = df["sex"].isin(["Female", "Male"])
    df["event_type"] = df["event_type"].astype("string").fillna("blank")
    df["year_num"] = pd.to_numeric(df["year"].astype("string"), errors="coerce")
    df["text_chars"] = df["event_text_len"].fillna(0) + df["mfr_narrative_len"].fillna(0)
    st = df["source_type"].astype("string").str.upper().fillna("")
    df["foreign_flag"] = st.str.contains("FOREIGN")
    cc = df["reporter_country_code"].astype("string").fillna("").str.strip().str.upper().to_numpy(dtype=object)
    df["country_group"] = pd.Categorical(np.where(cc == "", "blank", np.where(cc == "US", "US", "not US")))
    df["age_band"] = age_band(df["age_years"])
    log(f"full table: {len(df):,} reports; age filled {df['age_filled'].mean() * 100:.1f} %, sex filled {df['sex_filled'].mean() * 100:.1f} %")
    return df


def country_per_report(df):
    """Country of the reporter, per report (the bulk pull keeps it; the README said it was missing)."""
    rows = []
    for label, part in [("all reports", df), ("death + injury", df[df["event_type"].isin(["Death", "Injury"])]),
                        ("deaths", df[df["event_type"] == "Death"])] +                        [(f"{m} (all)", g) for m, g in df.groupby("maker", observed=True)] +                        [(f"{m} (death + injury)", g[g["event_type"].isin(["Death", "Injury"])]) for m, g in df.groupby("maker", observed=True)]:
        n = len(part)
        cg = part["country_group"].value_counts()
        cc = part["reporter_country_code"].astype("string").fillna("").str.strip().str.upper()
        top = cc[(cc != "") & (cc != "US")].value_counts().head(6)
        rows.append({"group": label, "n_reports": n, "us_pct": pct(cg.get("US", 0), n), "not_us_pct": pct(cg.get("not US", 0), n),
                     "blank_pct": pct(cg.get("blank", 0), n),
                     "top_non_us_codes": " | ".join(f"{k} ({v:,})" for k, v in top.items())})
    return pd.DataFrame(rows)


def demo_fill_rates(df):
    rows = []

    def add(group_by, g, part):
        n = len(part)
        rows.append({
            "group_by": group_by, "group": str(g), "n_reports": n,
            "age_fill_pct": pct(part["age_filled"].sum(), n), "sex_fill_pct": pct(part["sex_filled"].sum(), n),
            "both_fill_pct": pct((part["age_filled"] & part["sex_filled"]).sum(), n),
            "weight_fill_pct": pct(part["weight_filled"].sum(), n), "race_fill_pct": pct(part["race_filled"].sum(), n),
            "ethnicity_fill_pct": pct(part["eth_filled"].sum(), n),
            "sex_prefer_not_pct": pct((part["sex"] == "Prefer not / other").sum(), n),
        })

    add("all", "all reports", df)
    for col in ["maker", "family", "event_type", "year"]:
        for g, part in df.groupby(col, observed=True):
            if col == "year" and (pd.isna(g) or str(g) < "2008"):
                continue
            add(col, g, part)
    for (m, e), part in df.groupby(["maker", "event_type"], observed=True):
        add("maker x event_type", f"{m} | {e}", part)
    return pd.DataFrame(rows)


def demo_age_sex(df):
    """Age bands and sex split, by maker and by event type (filled reports only)."""
    rows = []
    bands = ["< 18", "18-39", "40-64", "65+"]

    def add(group_by, g, part):
        a = part[part["age_filled"]]
        s = part[part["sex_filled"]]
        row = {"group_by": group_by, "group": str(g), "n_reports": len(part), "n_age_filled": len(a),
               "age_median": round(float(a["age_years"].median()), 1) if len(a) else float("nan"),
               "age_mean": round(float(a["age_years"].mean()), 1) if len(a) else float("nan")}
        vc = a["age_band"].value_counts()
        for b in bands:
            row[f"age_{b}_pct"] = pct(vc.get(b, 0), len(a))
        row["n_sex_filled"] = len(s)
        row["female_pct"] = pct((s["sex"] == "Female").sum(), len(s))
        row["male_pct"] = pct((s["sex"] == "Male").sum(), len(s))
        rows.append(row)

    add("all", "all reports", df)
    for col in ["maker", "family", "event_type"]:
        for g, part in df.groupby(col, observed=True):
            add(col, g, part)
    for (m, e), part in df.groupby(["maker", "event_type"], observed=True):
        add("maker x event_type", f"{m} | {e}", part)
    yr_str = df["year"].astype(str)
    for yr in ["2019", "2021", "2023", "2025", "2026"]:
        add("year", yr, df[yr_str == yr])
    return pd.DataFrame(rows)


def demo_filled_vs_unfilled(df, llm):
    """Are reports with age/sex filled different from the rest?"""
    rows = []
    pair_keys = set(llm.loc[llm["has_pair"], "mdr_report_key"]) if llm is not None else set()
    for label, mask in [("age filled", df["age_filled"]), ("age blank", ~df["age_filled"]),
                        ("sex filled", df["sex_filled"]), ("sex blank", ~df["sex_filled"])]:
        part = df[mask]
        n = len(part)
        et = part["event_type"].value_counts()
        mk = part["maker"].value_counts()
        serious = part[part["event_type"].isin(["Death", "Injury"])]
        rows.append({
            "group": label, "n_reports": n,
            "death_pct": pct(et.get("Death", 0), n), "injury_pct": pct(et.get("Injury", 0), n),
            "malfunction_pct": pct(et.get("Malfunction", 0), n),
            "abbott_pct": pct(mk.get("Abbott", 0), n), "dexcom_pct": pct(mk.get("Dexcom", 0), n),
            "medtronic_pct": pct(mk.get("Medtronic", 0), n),
            "median_year_received": float(part["year_num"].median()),
            "foreign_source_pct": pct(part["foreign_flag"].sum(), n),
            "accuracy_code_pct": pct(part["accuracy_code"].fillna(False).sum(), n),
            "median_text_chars": float(part["text_chars"].median()),
            "serious_with_sensor_meter_pair_pct": pct(serious["mdr_report_key"].isin(pair_keys).sum(), len(serious)),
            "device_returned_pct": pct((part["device_availability"].astype("string") == "Device was returned to manufacturer").sum(), n),
            "not_us_pct": pct((part["country_group"] == "not US").sum(), n),
        })
    return pd.DataFrame(rows)


RE_AGE_TEXT = re.compile(
    r"\b(\d{1,3})\s*[- ]?\s*(?:YEAR|YR|Y)S?\s*[- ]?\s*OLD\b|\b(?:AGE|AGED)\s*(?:OF|:|IS|WAS)?\s*(\d{1,3})\b|\b(\d{1,3})\s*(?:YO|Y/O|YOA|Y\.O\.)\b")
RE_PEDIATRIC_WORD = re.compile(r"\b(?:CHILD|KID|TODDLER|INFANT|BABY|TEEN(?:AGER)?|ADOLESCENT|P(?:A)?EDIATRIC|MY SON|MY DAUGHTER|HER SON|HIS SON|HER DAUGHTER|HIS DAUGHTER|SCHOOL NURSE|DAYCARE)\b")


def age_from_text(text):
    for m in RE_AGE_TEXT.finditer(text):
        v = next(g for g in m.groups() if g)
        v = int(v)
        if 0 <= v <= 110:
            return v
    return None


def demo_age_in_text(serious):
    """How often does the text give an age when the field is blank? (serious reports)"""
    rows = []
    s = serious.copy()
    s["age_val"] = age_years(s["patient_age_value"], s["patient_age_unit"].astype("string"))
    s["age_filled"] = s["age_val"].notna()
    s["age_text"] = [age_from_text(t) if t else None for t in s["text"]]
    s["pediatric_word"] = [bool(RE_PEDIATRIC_WORD.search(t)) if t else False for t in s["text"]]
    for g, part in [("all serious", s)] + list(s.groupby("maker4")):
        blank = part[~part["age_filled"]]
        both = part[part["age_filled"] & part["age_text"].notna()]
        agree = (np.abs(both["age_val"] - both["age_text"]) <= 1).sum() if len(both) else 0
        rows.append({
            "group": g, "n_reports": len(part), "age_field_blank_n": len(blank),
            "age_in_text_when_blank_n": int(blank["age_text"].notna().sum()),
            "age_in_text_when_blank_pct": pct(blank["age_text"].notna().sum(), len(blank)),
            "age_in_text_under_18_when_blank_n": int((blank["age_text"] < 18).sum()),
            "pediatric_word_when_blank_pct": pct(blank["pediatric_word"].sum(), len(blank)),
            "field_and_text_both_n": len(both), "field_and_text_agree_within_1yr_pct": pct(agree, len(both)),
        })
    return pd.DataFrame(rows), s[["mdr_report_key", "age_text"]]


def trial_demographics():
    """REPLACE-BG randomised participants: age bands, sex, race, from the raw roster (read only)."""
    ro, sc = TRIAL_DIR / "HPtRoster.txt", TRIAL_DIR / "HScreening.txt"
    if not (ro.exists() and sc.exists()):
        log("trial roster not on this machine; trial column left as 'see analysis/DEMOGRAPHICS_DEEP.md (in progress)'")
        return None
    r = pd.read_csv(ro, sep="|")
    s = pd.read_csv(sc, sep="|")
    p = r.merge(s.drop(columns=[c for c in ["RecID", "SiteID"] if c in s.columns]), on="PtID", how="left")
    p = p[p["RandDtDaysAfterEnroll"].notna()].drop_duplicates("PtID")
    n = len(p)
    band = age_band(p["AgeAsOfEnrollDt"]).value_counts()
    out = {"n": n, "age_median": float(p["AgeAsOfEnrollDt"].median()), "age_mean": round(float(p["AgeAsOfEnrollDt"].mean()), 1),
           "age_min": float(p["AgeAsOfEnrollDt"].min()), "age_max": float(p["AgeAsOfEnrollDt"].max())}
    for b in ["< 18", "18-39", "40-64", "65+"]:
        out[f"age_{b}_pct"] = pct(band.get(b, 0), n)
    out["female_pct"] = pct((p["Gender"] == "F").sum(), n)
    out["male_pct"] = pct((p["Gender"] == "M").sum(), n)
    out["white_pct"] = pct((p["Race"] == "White").sum(), n)
    out["race_filled_pct"] = pct(p["Race"].notna().sum(), n)
    out["hispanic_pct"] = pct((p["Ethnicity"] == "Hispanic or Latino").sum(), n)
    out["ethnicity_filled_pct"] = pct(p["Ethnicity"].notna().sum(), n)
    log(f"trial roster: {n} randomised participants, median age {out['age_median']:.0f}")
    return out


def side_by_side(df, trial):
    """MAUDE (all, serious, Dexcom G4 only) vs the trial cohort."""
    cols = []

    def maude_col(label, part):
        a = part[part["age_filled"]]
        s = part[part["sex_filled"]]
        vc = a["age_band"].value_counts()
        c = {"column": label, "n_reports_or_people": len(part), "age_known_pct": pct(len(a), len(part)),
             "age_median": round(float(a["age_years"].median()), 1) if len(a) else float("nan"),
             "age_mean": round(float(a["age_years"].mean()), 1) if len(a) else float("nan")}
        for b in ["< 18", "18-39", "40-64", "65+"]:
            c[f"age_{b}_pct_of_known"] = pct(vc.get(b, 0), len(a))
        c["sex_known_pct"] = pct(len(s), len(part))
        c["female_pct_of_known"] = pct((s["sex"] == "Female").sum(), len(s))
        c["race_known_pct"] = pct(part["race_filled"].sum(), len(part))
        c["white_pct_of_known"] = float("nan")
        c["ethnicity_known_pct"] = pct(part["eth_filled"].sum(), len(part))
        c["type_1_pct"] = float("nan")
        c["device"] = "all CGM codes"
        return c

    cols.append(maude_col("MAUDE, all reports", df))
    cols.append(maude_col("MAUDE, death + injury", df[df["event_type"].isin(["Death", "Injury"])]))
    cols.append(maude_col("MAUDE, deaths", df[df["event_type"] == "Death"]))
    g4 = df[df["family"].astype(str) == "Dexcom G4"]
    c = maude_col("MAUDE, Dexcom G4 (the trial sensor)", g4)
    c["device"] = "Dexcom G4"
    cols.append(c)
    if trial:
        c = {"column": "REPLACE-BG trial (randomised)", "n_reports_or_people": trial["n"], "age_known_pct": 100.0,
             "age_median": trial["age_median"], "age_mean": trial["age_mean"]}
        for b in ["< 18", "18-39", "40-64", "65+"]:
            c[f"age_{b}_pct_of_known"] = trial[f"age_{b}_pct"]
        c["sex_known_pct"] = 100.0
        c["female_pct_of_known"] = trial["female_pct"]
        c["race_known_pct"] = trial["race_filled_pct"]
        c["white_pct_of_known"] = trial["white_pct"]
        c["ethnicity_known_pct"] = trial["ethnicity_filled_pct"]
        c["type_1_pct"] = 100.0
        c["device"] = "Dexcom G4 (study-provided)"
    else:
        c = {"column": "REPLACE-BG trial (randomised)", "device": "Dexcom G4",
             "note": "see analysis/DEMOGRAPHICS_DEEP.md (in progress)"}
    cols.append(c)
    return pd.DataFrame(cols)


# ----------------------------------------------------------------------------
# Part 3: the 300-report reading sample
# ----------------------------------------------------------------------------
ALLOCATION = {  # (event type, maker4): target count. Adds up to 300.
    ("Death", "Abbott"): 12, ("Death", "Dexcom"): 12, ("Death", "Medtronic"): 10, ("Death", "Other"): 1,
    ("Injury", "Abbott"): 50, ("Injury", "Dexcom"): 50, ("Injury", "Medtronic"): 25, ("Injury", "Other"): 15,
    ("Malfunction", "Abbott"): 45, ("Malfunction", "Dexcom"): 50, ("Malfunction", "Medtronic"): 20, ("Malfunction", "Other"): 10,
}


def draw_sample_300(serious, sample):
    rng = np.random.RandomState(SEED)
    pool_s = serious[serious["has_text"]][["mdr_report_key", "event_type", "maker4", "brand_name", "text"]].copy()
    pool_s["source"] = "serious.csv.gz"
    sm = sample[sample["text"].str.strip().str.len() > 4][["mdr_report_key", "event_type", "maker4", "brand_name", "text"]].copy()
    sm["mdr_report_key"] = sm["mdr_report_key"].astype(str)
    sm["event_type"] = "Malfunction"
    sm["source"] = "sample_local.parquet"
    pool = pd.concat([pool_s, sm], ignore_index=True).sort_values("mdr_report_key").reset_index(drop=True)
    picks = []
    shortfall = collections.Counter()
    for (et, mk), target in ALLOCATION.items():
        cand = pool[(pool["event_type"] == et) & (pool["maker4"] == mk)]
        k = min(target, len(cand))
        if k < target:
            shortfall[et] += target - k
        idx = rng.choice(cand.index.values, size=k, replace=False) if k else []
        picks.extend(list(idx))
    for et, short in shortfall.items():   # fill from the same event type, any maker, not yet picked
        cand = pool[(pool["event_type"] == et) & ~pool.index.isin(picks)]
        idx = rng.choice(cand.index.values, size=min(short, len(cand)), replace=False)
        picks.extend(list(idx))
    out = pool.loc[sorted(picks)].copy()
    out["stratum"] = out["event_type"] + " | " + out["maker4"]
    log(f"reading sample: {len(out)} reports " + ", ".join(f"{k}={v}" for k, v in out['event_type'].value_counts().items()))
    return out


# ----------------------------------------------------------------------------
# Part 4: text themes as patterns. All matching on UPPERCASE text.
# Patterns were written, then checked by hand on the 300-report reading sample (2026-11-06),
# then tightened: maker boilerplate sentences are removed first (BOILERPLATE), because they
# contain words like TESTING, SOFTWARE, SPECIFICATION and NON-HEALTHCARE PROFESSIONAL.
# ----------------------------------------------------------------------------
BOILERPLATE = [re.compile(p) for p in [
    # Abbott: the standard "most probable root causes ... positive benefit/risk ratio" paragraph
    r"THE MOST PROBABLE ROOT CAUSES ASSOCIATED WITH THIS (?:FAILURE MODE|INCIDENT) ARE .{0,250}?(?:POSITIVE BENEFIT/ ?RISK RATIO\.|RISK PROFILES REMAIN ACCEPTABLE[^.]*\.)",
    r"THERE ARE MITIGATIONS IN PLACE TO REDUCE AND PREVENT ISSUES SUCH AS .{0,250}?(?:POSITIVE BENEFIT/ ?RISK RATIO\.|RISK PROFILES REMAIN ACCEPTABLE[^.]*\.)",
    r"ALL VITAL (?:MANUFACTURING STEPS|FUNCTIONS) ARE [^.]*\.",
    r"LABELING IS PROVIDED TO INSTRUCT THE USER ON THE INTENDED USE[^.]*\.",
    r"ALL COMPLAINTS AND COMPLAINT TRENDS ARE INVESTIGATED[^.]*\.",
    r"IF A PRODUCT DEFECT/ ?DEFICIENCY IS IDENTIFIED, A RISK EVALUATION[^.]*\.",
    r"ADDITIONALLY, AS A PART OF ABBOTT.S POST-MARKET SURVEILLANCE PROCESS[^.]*\.",
    r"THESE MONITORING PROCESSES ENSURE[^.]*\.",
    r"EXTRACTED DATA FROM THE RETURNED SENSOR USING APPROVED SOFTWARE\.",
    r"N/A WAS SELECTED FOR (?:SECTION )?G4[^.]*\.",
    r"THE DEVICE (?:MFG|MANUFACTURING) DATE (?:IS UNKNOWN|DOES NOT APPLY|IS NOT APPLICABLE)\.",
    r"THE DATE ENTERED (?:IN SECTION [A-Z0-9]+ )?IS (?:THE DATE|PER THE)[^.]*\.",
    r"ALL PERTINENT INFORMATION AVAILABLE TO (?:ABBOTT DIABETES CARE|ADC) HAS BEEN SUBMITTED\.",
    r"THERE WAS NO REPORT OF DEATH[^.]*\.",
    r"LABELING INDICATES: INSERTING THE SENSOR AND WEARING THE ADHESIVE PATCH[^.]*\.",
    r"A TRIPPED TREND REVIEW WAS (?:CONDUCTED|COMPLETED)[^.]*\.",
    r"DIABETES MELLITUS IS A KNOWN CAUSE OF [A-Z ,/]+\.",
    # Dexcom: the calibration sentence and the problem-code note
    r"THE DATA INVESTIGATION DID NOT FIND BLOOD GLUCOSE CALIBRATION VALUES[^.]*\.",
    r"MEDICAL DEVICE PROBLEM CODE[^.]*3191[^.]*\.",
    # Medtronic: the legal paragraph at the end of every report
    r"MEDTRONIC,? (?:INC\. )?\(?MEDTRONIC\)? (?:IS SUBMITTING|SUBMITS) THIS REPORT TO COMPLY WITH.{0,2500}?(?:FREEDOM OF INFORMATION ACT\.|BECOMES KNOWN\.)",
    r"ANY REQUIRED FIELDS THAT ARE UNPOPULATED ARE BLANK[^.]*\.",
    # Senseonics: the form-code trailer
    r"H6\. (?:TYPE OF INVESTIGATION|INVESTIGATION (?:FINDINGS|CONCLUSIONS)) UPDATED TO [0-9, ]+\.?",
]]


def strip_boilerplate(t):
    for rx in BOILERPLATE:
        t = rx.sub(" ", t)
    return t


THEMES = {
    # --- the maker's device evaluation (mostly in the H10 manufacturer narrative)
    "eval_device_returned": (
        "Device was returned to the maker and looked at",
        r"(?<!NOT )(?<!NOT BE )(?<!NOT BEEN )(?<!WILL BE )(?<!TO BE )(?<!YET BEEN )(?<!NO PRODUCT )(?<!NO DEVICE )(?<!NO SENSOR )(?<!NO SAMPLE )(?:HAS BEEN|HAVE BEEN|WAS|WERE) RETURNED"
        r"|(?<!BE )(?<!NOT )RETURNED (?:AND|FOR) (?:INVESTIGAT|EVALUAT|ANALYSIS|TESTING|PRODUCT)|(?<!NOT )(?<!NO )RETURNED TO (?:THE )?(?:MANUFACTURER|ADC|DEXCOM|MEDTRONIC|SENSEONICS|ANIMAS)"
        r"|RETURNED (?:SENSOR|DEVICE|UNIT|PRODUCT|TRANSMITTER|RECEIVER|READER|METER|BATTERY)|(?<!NO )(?:THE )?PRODUCT WAS (?:PROVIDED|RECEIVED|EVALUATED)|(?<!NO )PRODUCT HAS BEEN RECEIVED"
        r"|(?<!NO )(?:DEVICE|UNIT|PRODUCT|SENSOR|TRANSMITTER|RECEIVER|READER|METER|PUMP) (?:WAS |HAS BEEN |HAVE BEEN |WERE )(?:RECEIVED|INVESTIGATED|TESTED|RETURNED AND)\b"
        r"|UPON RECEIPT|RMA WAS RECEIVED|DEVICE RECEIVED ON|UNIT RECEIVED|PLACED (?:THE )?UNIT UNDER|VISUAL INSPECTION WAS PERFORMED|VOLTAGE TEST WAS PERFORMED|FUNCTIONAL TEST(?:ING)? WAS PERFORMED|IN-HOUSE (?:TESTING|INVESTIGATION)"),
    "eval_not_returned": (
        "Device was NOT returned, discarded or not provided",
        r"NOT (?:YET )?(?:BEEN )?RETURNED|NOT (?:BE )?RETURNED|NO PRODUCT (?:HAS BEEN |WAS |HAD BEEN )?(?:RETURNED|PROVIDED|RECEIVED)|NO (?:PRODUCT OR DATA|DATA OR PRODUCT) (?:WAS |WERE )?(?:PROVIDED|AVAILABLE|RECEIVED)"
        r"|NO (?:DEVICE|SENSOR|SAMPLE|UNIT|TRANSMITTER)S? (?:WAS |WERE |HAS BEEN |HAVE BEEN )?(?:RETURNED|PROVIDED|RECEIVED)|WILL NOT BE RETURNED|NOT EXPECTED TO BE RETURNED|RETURN (?:FOR [A-Z0-9_\-, ]+ )?IS NOT EXPECTED|NO PRODUCT RETURN IS REQUIRED"
        r"|UNAVAILABLE FOR (?:EVALUATION|ANALYSIS|RETURN)|NOT (?:BE )?AVAILABLE FOR (?:EVALUATION|ANALYSIS|RETURN|FURTHER)|DISCARDED|DISPOSED|THROWN (?:AWAY|OUT)|(?:HAS|HAVE) NOT (?:YET )?BEEN RECEIVED|WAS NOT RECEIVED|NOT RECEIVED AT|DECLINED TO RETURN|AUTHORIZED BUT NOT RECEIVED|NOT RETURNED"),
    "eval_remote_data_review": (
        "Maker reviewed the device's data remotely (share logs, cloud data, performance data)",
        r"DATA WAS (?:EVALUATED|PROVIDED|REVIEWED|RECEIVED|DOWNLOADED)|PERFORMANCE DATA|SHARE LOGS?|BIN FILE|(?:RECEIVER|TRANSMITTER|DIAGNOSTIC) (?:DATA )?LOGS?|DATA LOG|DATA INVESTIGATION|DMS (?:REVIEW|DATA)|DATA MANAGEMENT SYSTEM|IN[- ]VIVO (?:SENSOR )?DATA|(?:CONFIRMED|UNDETERMINED|NOT CONFIRMED) VIA DATA|(?:HISTORY|BLACK BOX)(?: FILES?)? (?:WAS|WERE) (?:CHECKED|DOWNLOADED|REVIEWED)|REVIEW OF (?:THE )?(?:GLUCOSE|SYNCED|AVAILABLE|SYSTEM) (?:TREND )?(?:DATA|DIAGNOSTICS)|DATA HAS BEEN (?:REQUESTED|RECEIVED)"),
    "eval_no_defect_found": (
        "Evaluation found no defect / within specification / could not confirm or reproduce",
        r"NO INDICATION THAT THE PRODUCT DID NOT MEET SPECIFICATION|WITHIN (?:THE )?(?:REQUIRED |RANGE )?SPECIFICATIONS?|(?<!NOT )(?<!NOT MEET )(?:MET|MEETS) (?:ALL )?(?:PRODUCT |DESIGN |RELEASE |ITS )?(?:SPECIFICATION|REQUIREMENTS)|PASSED (?:ALL )?(?:REQUIRED |FUNCTIONAL |RELEVANT |THE )?TEST"
        r"|(?:WAS|IS|WERE|ISSUE|COMPLAINT|ALLEGATION|PROBLEM|EVENT|MALFUNCTION) (?:IS |WAS )?NOT CONFIRMED|COULD NOT BE CONFIRMED|CANNOT BE CONFIRMED|NO (?:DEFECT|MALFUNCTION|PRODUCT DEFICIENCY|FAILURE|ISSUE|ANOMAL|DAMAGE|NEW ISSUE)\w* (?:OR [A-Z ]+ )?(?:WAS |WERE |HAS BEEN |HAVE BEEN )?(?:FOUND|IDENTIFIED|DETECTED|OBSERVED|NOTED|REVEALED)"
        r"|DID NOT (?:REVEAL|IDENTIFY|FIND|SHOW) (?:ANY |A |THE )?(?:DEFECT|ISSUE|PROBLEM|ANOMAL|MALFUNCTION|ABNORMAL|FAILURE)|FUNCTION(?:ED|ING|S)? (?:NORMALLY|AS (?:EXPECTED|INTENDED|DESIGNED)|PROPERLY|CORRECTLY)|PERFORM(?:ED|ING|S)? (?:NORMALLY|AS (?:EXPECTED|INTENDED|DESIGNED)|PROPERLY|WITHIN)|OPERAT(?:ED|ING|ES) (?:NORMALLY|AS (?:EXPECTED|INTENDED)|WITHIN)|WORKING (?:NORMALLY|AS EXPECTED|WITHIN EXPECTATIONS|AS INTENDED)"
        r"|(?:NOT|COULD NOT BE|CANNOT BE|UNABLE TO BE) (?:REPRODUCED|DUPLICATED|REPLICATED)|UNABLE TO (?:REPLICATE|REPRODUCE|DUPLICATE)|NOT (?:DEVICE|PRODUCT)[- ]RELATED|NO (?:DEVICE|PRODUCT|SOFTWARE) (?:ISSUE|MALFUNCTION|DEFECT)|NO TRENDS WERE IDENTIFIED|NO (?:ADVERSE )?TRENDS? (?:THAT|WAS|WERE)|NO NON-?CONFORMANCES?|NO ALLEGED (?:DEVICE )?MALFUNCTION|KNOWN AND ANTICIPATED"),
    "eval_defect_confirmed": (
        "Evaluation confirmed the problem or named a cause (incl. a known field-action defect)",
        r"(?:ALLEGATION|COMPLAINT|EVENT|FAILURE|ISSUE|MALFUNCTION|PROBLEM|DEFECT|ANOMALY|INACCURACY|LOSS OF CONNECTION|ERROR) (?:WAS |HAS BEEN |IS |COULD BE )?CONFIRMED(?! (?:TO BE|THAT (?:LIBRE|FREESTYLE|THE PRODUCT)))|CONFIRMED (?:VIA|BY|DURING|THROUGH) (?:DATA|PHOTO|LOG|REVIEW|IN-VIVO|IN VIVO|TESTING)|CONFIRMED (?:THE |A )?(?:REPORTED |CUSTOMER'?S? )?(?:DEFECT|FAILURE|ISSUE|MALFUNCTION|COMPLAINT|PROBLEM|EVENT|VALUE)"
        r"|ROOT CAUSE (?:WAS |IS |HAS BEEN )?(?:DETERMINED TO BE|IDENTIFIED|ATTRIBUTED|FOUND|LIKELY|MOST LIKELY|POTENTIALLY|MAY BE RELATED)|PROBABLE CAUSE (?:WAS|IS) (?:DETERMINED TO BE |THE |A |DUE TO |RELATED TO )|ATTRIBUTED TO|OUT OF SPECIFICATION|MAY NOT MEET (?:PRODUCT )?(?:DESIGN )?SPECIFICATIONS?"
        r"|(?:VOLTAGE|FUNCTIONAL|HIGH PRESSURE|PRIME|DISPLACEMENT|OCCLUSION|PAIRING|BOOT|CHARGE) TEST (?:WAS PERFORMED AND )?FAILED|FAILED (?:THE )?(?:VOLTAGE|FUNCTIONAL|HIGH PRESSURE|PRIME|DISPLACEMENT|OCCLUSION|PAIRING|BOOT) TEST|DUE TO (?:A |AN )?(?:LOW TRANSMITTER BATTERY|INTERNAL DEFECT|CODING ISSUE|MOISTURE|CORROSION|CONTAMINATION|FAULTY|DAMAGE)"
        r"|(?:LOW|EARLY|PREMATURE|LOSS OF) (?:SENSOR )?SENSITIVITY|SENSITIVITY (?:LOSS|DRIFT|DECLINE|DROP)|HYDROGEL (?:OXIDATION|HYDRATION)|MISSING HYDRO-?GEL|OPTICAL INSTABILITY|TRANSIENT SHIFTS|MANUFACTURING (?:DEFECT|ISSUE)|(?<!NO )(?<!NO PHYSICAL )(?:DAMAGE|CRACK|CORROSION|CORRODED|MOISTURE|LIQUID INGRESS|CONTAMINATION|DRIED BLOOD)\w* (?:WAS |WERE |DEBRIS )?(?:FOUND|OBSERVED|NOTED|IDENTIFIED|INSIDE|ON THE)"
        r"|FIELD ACTION|FA\d{4}-\d{4}|WITHIN THE SCOPE OF (?:THE )?(?:INVESTIGATION|ADC)|KNOWN ISSUE FOR THE SERIAL|TRIPPED TREND[^.]{0,60}(?:CORRECTIVE ACTION|INVESTIGATION WAS CONDUCTED)|MOST LIKELY CONTRIBUTED|LIKELY (?:NOISE|CONTRIBUTED|DUE TO|CAUSED|RELATED TO)|(?:WAS|WERE) (?:DETERMINED|FOUND) TO BE (?:A |AN )?(?:FAULTY|DEFECTIVE|DAMAGED|LOW|CORRODED|CONTAMINATED)|MALFUNCTION WAS CONFIRMED"),
    "eval_root_cause_not_determined": (
        "Cause could not be determined / undetermined / no conclusion / not enough information",
        r"(?:ROOT |PROBABLE |DEFINITIVE |SPECIFIC )?CAUSE (?:OF (?:THE |THIS )?(?:EVENT|FAILURE|ISSUE|PROBLEM|COMPLAINT|INCIDENT|REPORTED \w+) )?(?:COULD NOT|CAN ?NOT|CANNOT|WAS NOT|HAS NOT BEEN|WAS UNABLE TO) (?:BE )?(?:DETERMINED|IDENTIFIED|ESTABLISHED|CONFIRMED|ASSIGNED|ISOLATED)"
        r"|(?:UNABLE|NOT POSSIBLE) TO (?:DETERMINE|IDENTIFY|ESTABLISH) (?:THE |A )?(?:ROOT |PROBABLE |DEFINITIVE |SPECIFIC )?CAUSE|NO (?:ROOT |DEFINITIVE |SPECIFIC )?CAUSE (?:COULD BE|WAS|HAS BEEN|CAN BE) (?:DETERMINED|IDENTIFIED|ESTABLISHED|FOUND)|INCONCLUSIVE|(?:UNKNOWN|UNDETERMINED|INDETERMINATE) (?:ROOT )?CAUSE|ROOT CAUSE (?:IS |WAS |REMAINS )?(?:UNKNOWN|UNDETERMINED|INDETERMINATE|UNCLEAR)"
        r"|(?:ALLEGATION|COMPLAINT|CONFIRMATION|EVENT|ISSUE) (?:WAS |IS |AND [A-Z ]+ )?UNDETERMINED|CANNOT (?:DRAW|MAKE) (?:ANY )?CONCLUSIONS? IN REGARDS|CANNOT BE (?:CONFIRMED OR EXCLUDED|REASONABLY SUGGESTED)|INSUFFICIENT (?:INFORMATION|TO CONDUCT)|NOT ENOUGH INFORMATION|LIMITED INFORMATION|LACK OF (?:INFORMATION|THE OS|THE FULL)|UNABLE TO TEST"),
    "eval_investigation_pending": (
        "Investigation still open; follow-up or supplemental report promised (not the conditional boilerplate)",
        r"(?:INVESTIGATION|ANALYSIS|EVALUATION|REVIEW) (?:IS |REMAINS |STILL |WAS )?(?:ONGOING|PENDING|IN PROGRESS|CONTINUING|UNDERWAY|NOT (?:YET )?COMPLETE|INCOMPLETE)|PENDING (?:EVALUATION|INVESTIGATION|ANALYSIS|DEVICE)|NOT YET (?:BEEN )?EVALUATED|CURRENTLY PERFORMING AN INVESTIGATION|RESULTS (?:ARE|IS|WILL BE) (?:PENDING|PROVIDED (?:IN|WITH) THE SUPPLEMENTAL)"
        r"|(?:FOLLOW[- ]?UP|SUPPLEMENTAL|FOLLOWUP) (?:INVESTIGATION )?(?:REPORT )?(?:WILL|SHALL) BE (?:SUBMITTED|SENT|PROVIDED|FILED|ISSUED)(?! IF)|FURTHER INFORMATION WILL FOLLOW|(?:HAS|HAVE) BEEN REQUESTED (?:BACK )?FOR (?:AN )?INVESTIGATION|RETURN GOODS KIT|RMA WAS (?:AUTHORIZED|ISSUED)|WILL BE RETURNED FOR ANALYSIS|AGREED TO RETURN"),
    # --- how the user found out
    "symptoms_described": (
        "Symptoms described (felt low, high or unwell; includes mismatch with the reading)",
        r"(?<!NO )(?<!UNSPECIFIED )(?<!REPORT )(?<!REPORT ANY )\bSYMPTOMS? (?:OF|DESCRIBED|INCLUDING|SUCH AS|LIKE|WERE|WAS|INCLUDED|CONSISTENT|THAT)|(?:DID NOT|DIDN'?T|DOES NOT|DOESN'?T|DO NOT|DON'?T|NOT) (?:FEEL|MATCH|CORRELATE|CORRESPOND|REFLECT|AGREE)|FELT (?:LOW|HIGH|SHAKY|DIZZY|FINE|OK|OKAY|NORMAL|SICK|SWEATY|WEAK|CONFUSED|NAUSEOUS|NAUSEATED|OFF|FUNNY|WEIRD|BAD|TERRIBLE|LIGHTHEADED|LIGHT-HEADED|UNWELL|TIRED|HOT|COLD|ILL)"
        r"|FEELING (?:LOW|HIGH|SHAKY|DIZZY|FINE|OK|OKAY|NORMAL|SICK|SWEATY|WEAK|CONFUSED|NAUSEOUS|OFF|FUNNY|WEIRD|BAD|TERRIBLE|LIGHTHEADED|UNWELL|TIRED|HOT|COLD|ILL|VERY)|HOW (?:HE|SHE|THEY|I) (?:WAS|WERE|AM|FELT|FEEL)|SHAK(?:Y|ING|INESS)|SWEAT(?:Y|ING)|DIAPHORE|DIZZ(?:Y|INESS)|CONFUS(?:ED|ION)|BLURR(?:Y|ED) VISION|TREMBL|NAUSEA|VOMIT|THIRST|PALPITATION|HEADACHE|LETHARG|WEAKNESS|SOMNOLEN|ASTHENI|DISORIENT|SLURR|NUMBNESS|HUNGRY|HUNGER|RESTLESS"),
    "symptoms_mismatch_explicit": (
        "The person says the reading did NOT match how they felt (explicit)",
        r"(?:DID NOT|DIDN'?T|DOES NOT|DOESN'?T|DO NOT|DON'?T|NOT) (?:MATCH|CORRELATE|CORRESPOND|REFLECT|AGREE)|(?:KNEW|FELT|THOUGHT|BELIEVED|SUSPECTED) (?:THAT )?(?:THE |HER |HIS |THEIR |MY )?(?:SENSOR|CGM|READING|VALUE|DEVICE|NUMBER)S? (?:WAS|WERE|IS|ARE|SEEMED|LOOKED|MUST BE|HAD TO BE) (?:INACCURATE|WRONG|OFF|INCORRECT|NOT (?:RIGHT|ACCURATE|CORRECT)|TOO (?:HIGH|LOW)|JUMPY|ERRATIC|READING INACCURATELY)"
        r"|(?:NOT|NO) (?:EXPERIENCING |HAVING |FEELING )?(?:ANY )?SYMPTOMS (?:OF|CONSISTENT)|DID NOT FEEL (?:LOW|HIGH|HYPO|HYPER|LIKE|RIGHT|WELL)|(?:FELT|FEELING|FEEL) (?:FINE|OK|OKAY|NORMAL|WELL)\b[^.]{0,80}(?:LOW|HIGH|READING|CGM|SENSOR)|(?:THOUGHT|BELIEVED) (?:SHE|HE|THEY) (?:WAS|WERE) FINE|HOW (?:HE|SHE|THEY|I) (?:WAS|WERE|AM) FEELING|READING INACCURATELY DUE TO"),
    "lab_or_clinic_value": (
        "A lab draw, venous, hospital or HCP meter value is quoted",
        r"\bLAB(?:ORATORY|S)?\b|BLOOD ?WORK|\bVENOUS\b|PLASMA GLUCOSE|HOSPITAL (?:METER|GLUCOMETER|LAB|TEST)|HCP METER|HEALTHCARE (?:PROFESSIONAL )?METER|SERUM GLUCOSE|\bBMP\b|METABOLIC PANEL|POINT[- ]OF[- ]CARE|AT THE (?:ER|HOSPITAL|CLINIC)[^.]{0,60}(?:BG|BLOOD GLUCOSE|FINGER ?STICK)[^.]{0,30}(?:WAS|READ|OF) \d|BLOOD TESTS?"),
    "alarm_prompted_check": (
        "An alarm or alert fired and prompted the check (alarm worked)",
        r"(?:RECEIVED|GOT|HEARD|WOKE (?:UP )?TO|WOKEN (?:UP )?BY|AWAKENED BY|ALERTED BY)\b[^.]{0,30}\b(?:LOW|HIGH|URGENT LOW|GLUCOSE|HYPO\w*|HYPER\w*)[^.]{0,12}(?:ALARM|ALERT)|(?:LOW|HIGH|URGENT LOW|GLUCOSE|HYPO\w*)[^.]{0,20}(?:ALARM|ALERT)S? (?:WENT OFF|SOUNDED|WOKE|TRIGGERED|NOTIFIED|WAS RECEIVED|WERE RECEIVED|ALERTED|WARNED|WAS ASSERTED|WAS DELIVERED|WERE DELIVERED|FIRED)|(?:APP|SYSTEM|DEVICE|CGM|RECEIVER) (?:DELIVERED|ASSERTED|ISSUED|PROVIDED|DID ALERT)[^.]{0,30}(?:URGENT LOW|LOW|HIGH|GLUCOSE)[^.]{0,12}(?:ALERT|ALARM)|CGM (?:DID )?ALERT(?:ED)? (?:PATIENT|HER|HIM|THEM|FOR LOW|TO THE)|WAS ALERTED BY THE (?:CGM|CONTINUOUS GLUCOSE)|ALARM(?:ED)? FOR (?:LOW|HIGH|HYPO)|HEARD (?:THE|AN|HER|HIS) (?:LOW |HIGH )?(?:ALARM|ALERT)"),
    # --- timing finer than the wear day
    "time_hours_or_minutes_after_start": (
        "Failure timed in hours or minutes after insertion, start or warm-up (incl. same day)",
        r"(?:WITHIN|AFTER|ABOUT|APPROXIMATELY|ONLY|LESS THAN|JUST|LASTED)\s+(?:A FEW |SEVERAL |ONE |TWO |THREE |FOUR |FIVE |SIX |TWELVE |\d{1,2} |AN? |A COUPLE (?:OF )?|HALF AN? )?(?:HOURS?|HRS?|MINUTES?|MINS?)\s+(?:OF|AFTER|FROM|INTO|FOLLOWING|SINCE|POST)\s+(?:THE |SENSOR |ITS |BEING |A )?(?:INSERTION|APPLICATION|APPLYING|INSERTING|INSERTED|APPLIED|START|STARTING|WARM[- ]?UP|ACTIVATION|PLACEMENT|PLACED|WEAR|USE|USING|REPORTED SENSOR FAILURE)"
        r"|WARM[- ]?UP|FIRST (?:FEW )?(?:HOURS?|12 HOURS|24 HOURS|NIGHT)\b|(?:HOURS|MINUTES) (?:AFTER|INTO|OF) (?:INSERTION|APPLICATION|THE SESSION|WEAR|STARTING|PLACING|APPLYING|INSERTING)|(?:ON THE )?SAME DAY (?:OF USE|AS|THE SENSOR WAS INSERTED|OF INSERTION)|(?:DURING|IN) (?:THE )?(?:SENSOR )?STARTUP|HOURS BEFORE THE SENSOR"),
    "sensor_ended_early_or_error_message": (
        "Sensor ended early, failed, or showed an error message (replace sensor, sensor error, scan again, ...)",
        r"REPLACE SENSOR|SENSOR (?:ERROR|FAIL(?:ED|URE)?|RETIREMENT|REPLACEMENT ALERT|EXPIRATION|EXPIRED|ENDED|NO LONGER WORKING|STOPPED WORKING)|EARLY (?:SENSOR )?(?:EXPIRATION|REPLACEMENT|REMOVAL|RETIREMENT|END|TERMINATION|SHUT ?OFF|SHUT ?DOWN|FAIL)|SCAN ?AGAIN IN|INCOMPATIBLE SENSOR|NO ACTIVE SENSOR|SCANFOUT|WEARABLE FAILURE|SENSOR (?:ENDED|FAILED|STOPPED|QUIT|DIED|TERMINATED|SHUT (?:OFF|DOWN)) (?:EARLY|PREMATURELY|AFTER|ON DAY|BEFORE|UNEXPECTEDLY|WITHIN)|PREMATURE(?:LY)?\b"
        r"|(?:LASTED|WORKED|FUNCTIONED|STAYED ON) (?:FOR )?(?:ONLY |JUST |ABOUT |APPROXIMATELY |LESS THAN )?(?:A FEW |\d{1,2} |ONE |TWO |THREE |FOUR |FIVE |SIX |SEVEN |EIGHT |NINE )?(?:HOURS?|DAYS?)\b|BEFORE (?:THE |ITS )?(?:\d{1,2}[- ]DAY |10[- ]DAY |14[- ]DAY |15[- ]DAY |FULL )?(?:WEAR (?:PERIOD|TIME)|EXPIRATION|EXPIRY|SESSION (?:ENDED|WAS OVER|END)|END OF (?:THE )?(?:SESSION|WEAR))|UNABLE TO OBTAIN (?:SENSOR |GLUCOSE )?READINGS|NO READINGS|NOT GIVING READINGS"),
    # --- adhesive, insertion, skin
    "adhesive_or_fell_off": (
        "Adhesive problem, sensor detached, fell off or was knocked off",
        r"FELL OFF|FALL(?:S|ING)? OFF|FALLEN OFF|CAME OFF|COME OFF|COMING OFF|(?<!RETURNED SENSOR )(?<!PATCH )(?<!THE )ADHESI(?:VE|ON)\b(?! OF THE FREESTYLE)(?! PATCH MIGHT)|ADHESIVE (?:ISSUE|PROBLEM|FAIL|DID NOT|WOULD NOT|WAS NOT|LOST|LOSS)|DISLODG|DETACH(?:ED|MENT)?\b(?! (?:OR MISSING |OR BROKEN )?(?:SENSOR )?WIRE)|KNOCKED (?:OFF|LOOSE|OUT)|RIPPED (?:OFF|OUT)|PULLED (?:OFF|OUT)|NOT STAY(?:ING)? (?:ON|STUCK|ATTACHED)|WOULD NOT STAY|WOULDN'?T STAY|OVER[- ]?PATCH|OVER[- ]?TAPE|SKIN ?TAC|\bTAPE\b|LIFT(?:ED|ING) (?:OFF|UP|FROM)|STICK(?:Y|ING|S)? (?:TO|ON) (?:THE )?SKIN|BUMPED INTO|LOOSE AFTER|SENSOR (?:WAS |IS )?LOOSE|GAUZE TO SECURE"),
    "skin_reaction_or_infection": (
        "Rash, itching, allergy, blister, redness, infection, abscess or scar at the site",
        r"RASH|ITCH|BLISTER|ALLERG|IRRITAT|REDNESS|\bRED\b (?:MARK|AREA|SPOT|RING|CIRCLE|BUMP|SKIN|WELT|AROUND|AND)|SWELL|SWOLLEN|HIVES|WELT|BURN(?:ING|ED|S|T)?\b|DERMATITIS|CONTACT (?:ALLERGY|REACTION)|SKIN (?:REACTION|IRRITATION|DAMAGE|BREAKDOWN|TEAR|INFECTION)|ECZEMA|OOZ|WEEP(?:ING)?\b|SCAB|\bSCAR(?:S|RING|RED| TISSUE)?\b|DISCOLOR|HARD(?:ENED)? (?:LUMP|KNOT|SPOT|AREA|BUMP)|\bLUMP\b|\bBUMPS?\b|SORE\b|TENDER|INFECT|ABSCESS|CELLULITIS|\bPUS\b|PIMPLE|INFLAM|OPEN WOUND|WOUND|ANTIBIOTIC|ERYTHEMA|PENICILLIN|CEPHALEXIN|FLUCLOXACILLIN|AMOXICILLIN"),
    "bleeding_or_bruise": (
        "Bleeding, blood at the site or bruising",
        r"BLEED|\bBLED\b|BLOOD (?:AT|FROM|UNDER|ON|AROUND|CAME|POOL|FILLED|IN THE|WAS (?:PRESENT|OBSERVED|NOTED|SEEN)|ALL OVER|DRIPP|GUSH|SPURT|DEBRIS)|BRUIS|HEMATOMA|HAEMATOMA|BLOODY|HEMORRHAGE|HAEMORRHAGE|SATURATED THE SENSOR|DRIED BLOOD"),
    "sensor_wire_retained_detached_or_broken": (
        "Sensor wire or filament detached, missing, broken or left in the skin",
        r"FILAMENT|(?:DETACHED|MISSING|BROKEN|BENT|RETAINED) (?:OR [A-Z]+ )?(?:SENSOR )?(?:WIRE|NEEDLE|CANNULA|PROBE|TIP|FRAGMENT)|(?:NEEDLE|WIRE|CANNULA|PROBE|TIP|INTRODUCER|FRAGMENT|PIECE|PART|SLIVER) (?:WAS |IS |HAD |REMAINED |STAYED |GOT |WERE |BECAME |STILL )?(?:STUCK|LEFT|REMAINED|RETAINED|LODGED|EMBEDDED|BENT|BROKE|BROKEN|STILL IN|IN (?:THE |HIS |HER |THEIR |MY )?(?:SKIN|ARM|BODY|ABDOMEN|SITE|TISSUE))"
        r"|(?:LEFT|REMAINED|RETAINED|LODGED|EMBEDDED|STUCK|STILL) (?:IN|UNDER|INSIDE|BEHIND IN) (?:THE |HIS |HER |THEIR |MY )?(?:SKIN|ARM|BODY|ABDOMEN|SITE|TISSUE|PATIENT)|WIRE (?:WAS |HAD BEEN )?SURGICALLY REMOVED|SENSOR WIRE (?:DETACHED|REMAINED|STUCK|STILL IN|WAS STILL|VISIBLE|REMOVED)|FOREIGN BODY|BENT NEEDLE|NEEDLE (?:DID NOT|DIDN'?T|FAILED TO) RETRACT|(?:SURGICAL|SURGER|INCISION|X[- ]?RAY|ULTRASOUND|IMAGING|CT SCAN)\w*\b[^.]{0,80}(?:REMOV|LOCAT|FIND|FOUND|WIRE|CONFIRM|NEGATIVE)"),
    "insertion_pain": (
        "Pain, burning or discomfort at insertion or while wearing",
        r"\bPAIN(?:FUL)?\b[^.]{0,60}(?:SITE|INSERT|SENSOR|ARM|SKIN|PATCH|REMOV|WEAR)|(?:SITE|INSERT|SENSOR|ARM|SKIN|PATCH|REMOV|WEARING)[^.]{0,60}\bPAIN(?:FUL)?\b|MORE PAINFUL|BURNING SENSATION|\bSTING(?:ING)?\b|DISCOMFORT|EXCRUCIAT|\bHURT\b[^.]{0,40}(?:SITE|INSERT|SENSOR|ARM)"),
    "applicator_or_insertion_failure": (
        "Applicator or inserter failed, jammed, misfired, bent the tip, or sensor stayed in the tool",
        r"(?:APPLICATOR|INSERTER|INSERTION (?:DEVICE|TOOL)|AUTO[- ]?APPLICATOR|SENSOR APPLICATOR) (?:FAILED|DID NOT|DIDN'?T|MALFUNCTION|JAMMED|STUCK|WOULD NOT|WOULDN'?T|MISFIRED|WENT OFF|DEPLOYED|DID NOT DEPLOY|BROKE|WAS (?:STUCK|DEFECTIVE|BROKEN|EMPTY)|NEVER)|(?:FAILED|JAMMED|STUCK|DEFECTIVE|BROKEN) APPLICATOR|APPLICATOR (?:ISSUE|PROBLEM|ERROR|FAILURE|MALFUNCTION)|DID NOT (?:DEPLOY|INSERT|FIRE|RELEASE)|(?:SENSOR|FILAMENT|NEEDLE) (?:STAYED|REMAINED|WAS STUCK|WAS LEFT) (?:IN|INSIDE) THE (?:APPLICATOR|INSERTION TOOL|INSERTER)|DEPLOYED ON ITS OWN|BENT (?:SENSOR )?TIP|SENSOR (?:TIP|FILAMENT|NEEDLE) (?:WAS |IS )?BENT|UNABLE TO APPLY|DAMAGED OR BENT"),
    # --- causes people or makers name
    "compression_or_lying_on_sensor": (
        "Compression low: pressure on, lying on, or bumping the sensor",
        r"COMPRESSION|PRESSURE (?:LOW|WAS APPLIED|ON THE SENSOR|INDUCED|ARTIFACT|FROM|BEING APPLIED|APPLIED TO)|(?:SLEEP|SLEEPING|SLEPT|LAYING|LYING|LAY|LAID|LEANING|LEANED|ROLLED|ROLLING|RESTING|RESTED|PRESSING|PRESSED|RUBBED|BUMPED|RUBBED/BUMPED/LAID) (?:ON|AGAINST|ONTO) (?:THE |HIS |HER |THEIR |MY |THAT )?(?:SENSOR|ARM|SIDE|SITE|TRANSMITTER|DEVICE|WEARABLE)|LAYING ON IT|LYING ON IT|SLEEPING ON IT|IMPACT(?:S)? TO THE (?:INSERTION )?SITE"),
    "night_or_sleep": (
        "Event at night, during sleep, or on waking",
        r"(?:WHILE|WHEN|DURING|IN) (?:HE WAS |SHE WAS |THEY WERE |I WAS |HIS |HER )?(?:SLEEPING|ASLEEP|SLEEP\b|THE NIGHT|OVERNIGHT|AT NIGHT|THE MIDDLE OF THE NIGHT|THE MORNING)|OVERNIGHT|MIDDLE OF THE NIGHT|\bNIGHT(?:TIME)?\b|WOKE (?:UP)?|AWAKEN|AWOKE|\bASLEEP\b|BEDTIME|IN BED\b|OUT OF BED|EARLY IN THE MORNING|\b(?:[1-9]|1[0-2]|0?[0-5]:\d\d|1[0-2]:\d\d)\s?(?:AM|A\.M\.)\b|SLEPT THROUGH"),
    "interfering_substance_or_dialysis": (
        "Interfering substance named (acetaminophen, vitamin C, hydroxyurea, ...) or dialysis",
        r"ACETAMINOPHEN|TYLENOL|PARACETAMOL|VITAMIN C|ASCORBIC|HYDROXYUREA|HYDROXYCARBAMIDE|SALICYL|ASPIRIN|MANNITOL|SORBITOL|INTERFER(?:ING|ENCE|E|ES|ED)\b[^.]{0,60}(?:SUBSTANCE|MEDICATION|DRUG|SUPPLEMENT|VITAMIN)|(?:SUBSTANCE|MEDICATION|DRUG|SUPPLEMENT|VITAMIN)S?\b[^.]{0,60}INTERFER|INTERFERING SUBSTANCE|TETRACYCLINE|DIALYSIS|BLOOD THINNER|ANTICOAGULANT"),
    "exercise_water_heat": (
        "Exercise, swimming, shower, bath, heat or sweat named as context",
        r"EXERCIS|WORK(?:ING)? ?OUT|\bGYM\b|\bRUNNING\b(?! (?:LOW|HIGH|OUT|ERRANDS))|JOGGING|SWIM|SHOWER|\bBATH(?:TUB|S|ING|ED)?\b|\bPOOL\b|HOT TUB|SAUNA|\bSPORTS?\b|BIKING|CYCLING|HIKING|\bOCEAN\b|\bBEACH\b|\bHEAT\b|HOT WEATHER|SUNBURN|DEHYDRAT|TRIATHLON|(?:SHORT|LONG) WALK|\bWALKING\b"),
    "placement_off_label_site": (
        "Sensor worn on a site other than the labelled one, or maker says off-label",
        r"(?:APPLIED|PLACED|INSERTED|WORN|WEARING|WORE|PUT) (?:IT |THE SENSOR |SENSOR |INTO |IN |ON |TO )?(?:THE |HIS |HER |MY |THEIR )?(?:THIGH|LEG|BUTTOCKS?|CHEST|FOREARM|LOWER BACK|HIP|CALF|BREAST|FLANK)|INSERTED INTO THE (?:UPPER )?(?:BUTTOCKS?|ARM|ABDOMEN)[^.]{0,20}OFF-?LABEL|OFF[- ]LABEL|NOT (?:AN |THE )?(?:APPROVED|INDICATED|RECOMMENDED|LABELED|LABELLED) (?:SITE|LOCATION|AREA|PLACEMENT|BODY)|UNAPPROVED (?:SITE|LOCATION)|IMPROPER SITE SELECTION|SAME APPLICATION SITE"),
    # --- hardware, app, alarms, pump
    "app_phone_bluetooth": (
        "App, phone, Bluetooth, software update, compatibility or pairing problem",
        r"BLUETOOTH|\bAPP\b (?:CRASH|VERSION|WAS|IS|DID|DOES|KEPT|KEEPS|STOPPED|CLOSED|FROZE|CLOSES|FAILED|NOT|NO LONGER|ALERT|ALARM|DELIVERED|DISPLAY|SHOWED|READ|ONLY|AND)|(?:THE|THEIR|HIS|HER|MY|G7|G6|G5|G4|LIBRE ?3|LIBRE ?2|LIBRELINK|DEXCOM|CGM|MOBILE|FOLLOW|SHARE|CLARITY|FREESTYLE) (?:CGM )?APP\b|APP CRASH|MOBILE APPLICATION|(?:LIBRELINK|G7 CGM|G6|FOLLOW|CLARITY|CARELINK) APPLICATION|APPLICATION (?:CRASH|CLOSED|SHUT|FROZE|WOULD|DID|KEEPS|STOPPED|UPDATE|WAS|IS|ON|NOT|VERSION|THAT WOULD)"
        r"|I?PHONE\b|ANDROID|SMART ?PHONE|SMART DEVICE|\bIOS\b|SAMSUNG|GALAXY|PIXEL|CELL ?PHONE|MOBILE (?:PHONE|DEVICE)|(?:APP|PHONE|IOS|ANDROID|SYSTEM|SOFTWARE|FIRMWARE|TRANSMITTER) (?:UPDATE|UPGRADE)|UPDATE[DS]? (?:THE |HIS |HER |MY |THEIR )?(?:APP|PHONE|SOFTWARE|IOS|ANDROID|FIRMWARE)|AUTO-?UPDATE|\bPAIR(?:ING|ED)\b|UNPAIR|OPERATING SYSTEM|APPLE WATCH|SMART ?WATCH|CLARITY|LIBREVIEW|LIBRE ?LINK|FOLLOW(?:ER)? APP|SHARE APP|DEXCOM SHARE|CARELINK|MINIMED MOBILE|LOGGED OUT|LOG ?IN\b|PASSWORD|USER ACCOUNT|SERVER|CLOUD|COMPATIBILITY|INCOMPATIB|FIRMWARE|CODING ISSUE|SOFTWARE (?:ISSUE|BUG|ERROR|GLITCH|MALFUNCTION|PROBLEM|VERSION)|UNSUPPORTED"),
    "receiver_reader_hardware": (
        "Receiver, reader, transmitter hardware, screen, battery, charging or overheating problem",
        r"(?:RECEIVER|READER) (?:WAS |IS |HAD |HAS |KEEPS |WOULD |DID |DOES )?(?:NOT|FAILED|BATTERY|SCREEN|TURNING|TOO HOT|DISPLAYED|SHOWED|ERROR|ERR|HARDWARE|DEAD|FROZE|BLACK|BLANK|NO LONGER|WON'?T|BROKE|WOULD NOT|DID NOT|DOES NOT|RECALL)|(?:RECEIVER|READER)'?S? (?:BUILT-IN )?(?:BATTERY|SCREEN|DISPLAY|SPEAKER)|HANDHELD|DISPLAY DEVICE|TOUCH ?SCREEN|SCREEN (?:WENT|WAS|IS|TURNED|HAS GONE|KEEPS GOING) (?:BLACK|BLANK|FROZE|FROZEN|DARK|WHITE|OFF)|DISPLAY WENT BLANK|(?:WOULD|WILL|DOES|DID|COULD) ?(?:NOT|N'?T) (?:TURN|POWER|CHARGE|HOLD A CHARGE|STAY) (?:ON|UP|OFF)?|NOT POWER(?:ING)? ON|BATTERY|\bCHARG(?:E|ING|ER|ED)\b|OVERHEAT|TOO HOT|SWELL(?:ING|ED)? BATTERY|SMOKE|(?:CAUGHT|ON) FIRE|FIRE HAZARD|MELT|TRANSMITTER (?:FAILED|FAILURE|ERROR|BATTERY)|HARDWARE (?:ERROR|FAILURE)|ERR ?HWBBT|ERR\d{3}|\bLED\b DID NOT|VIBRAT\w+ (?:ALERT|MOTOR)|VIBE"),
    "alarm_failed": (
        "Alarm or alert did not sound, was not heard, missed, or too quiet",
        r"(?:NO|NOT|NEVER|DID NOT|DIDN'?T|DIDNT|FAILED TO|WITHOUT|MISSED|MISSING|WAS NOT|WERE NOT|HAVEN'?T|HASN'?T|DON'?T|DOESN'?T|WOULD NOT|WOULDN'?T|UNABLE TO) (?:RECEIVE[D]? |RECEIVING |GET |GOT |GETTING |HEAR |HEARD |GIVE |GIVEN |SOUND |TRIGGER |SEND |SENT |ANY |AN |THE |A |HAVE |HAD |BEEN |LONGER |ALERTED (?:OF |TO )|ALERT (?:OF |TO ))?(?:ALARM|ALERT|ALERTED|ALARMED|WARNING|NOTIF|CHANGES IN GLUCOSE)"
        r"|(?:ALARM|ALERT|NOTIFICATION)S? (?:DID NOT|DIDN'?T|DIDNT|FAILED|NEVER|WAS NOT|WERE NOT|WASN'?T|WEREN'?T|NOT|HAD NOT|HAS NOT|HAVE NOT|WOULD NOT|WOULDN'?T|DO NOT|DON'?T|DOES NOT|DOESN'?T) (?:GO OFF|GOING OFF|SOUND|WORK|TRIGGER|WAKE|ALERT|NOTIFY|OCCUR|ACTIVATE|RECEIVED|HEARD|FIRE|FUNCTION|COME|BEEN|GONE|PROVIDED|DELIVERED|AUDIBLE)"
        r"|NO (?:AUDIBLE |LOW |HIGH |URGENT LOW |AUDIO )?(?:ALARM|ALERT|WARNING|NOTIFICATION|AUDIO OUTPUT)S?\b|SLEPT THROUGH|DID NOT WAKE|DIDN'?T WAKE|FAILED TO WAKE|FAILURE TO ALERT|FAILED TO ALERT|(?:WAS|WERE) NOT ALERTED|NOT ALERTED|(?:ALARM|ALERT)S? (?:WAS|WERE|IS|ARE) (?:TOO )?(?:QUIET|SILENT|MUTED|SILENCED|LOW VOLUME|NOT LOUD|FAINT|INAUDIBLE|NOT (?:PROVIDED|HEARD|RECEIVED|DELIVERED|AUDIBLE|TRIGGERED))|INAUDIBLE|SPEAKER|VOLUME|INTERMITTENT AUDIO|DENIED HAVING HEARD|ALARM BEING INAUDIBLE|SYSTEM DID NOT ALERT|DID NOT (?:ALARM|ALERT)\b"),
    "alarm_any_mention": (
        "Any mention of an alarm or alert (reference row)",
        r"ALARM|ALERT|NOTIFICATION"),
    "pump_automation": (
        "Insulin pump automation (auto mode, closed loop, Control-IQ, SmartGuard, suspend) acted on the reading",
        r"AUTO ?MODE|SMART ?GUARD|CONTROL[- ]?IQ|BASAL[- ]?IQ|OMNIPOD ?5|CLOSED[- ]?LOOP|HYBRID CLOSED|AUTOMATED INSULIN|AUTOMATIC (?:BASAL|CORRECTION|DELIVERY|BOLUS|INSULIN|MODE)|AUTO[- ]?(?:BASAL|BOLUS|CORRECTION|INSULIN)|AUTOMATICALLY (?:GIVES?|DELIVERS?|DOSES?|ADJUSTS?|GAVE|DELIVERED)|\bILET\b|BETA BIONICS|\b(?:780|770|670)\s?G\b|MINIMED (?:780|770|670)|CAMAPS|DIY LOOP|\bLOOP\b|TWIIST"
        r"|SUSPEND(?:ED|S|ING)? (?:INSULIN|BASAL|DELIVERY|THE PUMP)|INSULIN (?:WAS |WERE |DELIVERY (?:WAS )?)?(?:SUSPENDED|STOPPED|HALTED|PAUSED)|(?:PUMP|ALGORITHM) (?:DELIVERED|GAVE|SUSPENDED|STOPPED|INCREASED|DECREASED|REDUCED|ADJUSTED|DOSED|ADMINISTERED|CALCULATED|AUTOMATICALLY|AUTO|DID NOT COUNTER)|SYSTEM (?:DELIVERED|SUSPENDED|ADJUSTED|INCREASED|DECREASED|GAVE) (?:THE |A |AN )?(?:INSULIN|BASAL|BOLUS|CORRECTION)|BASED ON (?:ITS|THE CGM|THE SENSOR|CGM) (?:INPUT|READING|VALUE)S?|PREDICTIVE LOW GLUCOSE (?:SUSPEND|MANAGEMENT)|LOW GLUCOSE SUSPEND|SUSPEND BEFORE LOW|\bPLGS\b|AUTO ?CORRECT|AUTOCORRECTION|INCORRECT INSULIN DELIVERY|CONNECTED TO (?:MY|THE|HIS|HER) (?:INSULIN )?PUMP"),
    "pump_any_mention": (
        "Any mention of an insulin pump (reference row)",
        r"\bPUMP|OMNIPOD|TANDEM|MINIMED|MEDTRONIC (?:7|6)\d\dG|PATCH PUMP|\bPOD\b|INFUSION SET|BOLUS"),
    # --- who is talking
    "voice_first_person": (
        "Written in the first person (patient or carer wrote it)",
        r"\bI\b (?:WAS|HAD|HAVE|AM|WENT|CHECKED|TESTED|FELT|FEEL|NOTICED|CALLED|TOOK|ATE|DID|USED|USE|WOKE|GOT|COULD|WOULD|NEVER|ALWAYS|THINK|BELIEVE|KNOW|KNEW|DON'?T|DIDN'?T|CAN'?T|COULDN'?T|HAVEN'?T|WEAR|WORE|STARTED|PUT|REPLACED|CONTACTED|PLACED|APPLIED|INSERTED|SCANNED|LOOKED|SAW|ENDED|DECIDED|ALMOST|NEARLY|JUST|THEN|ALSO|ONLY|STILL|BOUGHT|REPORTED|SPOKE|TALKED|ASKED|TOLD|LOST|PASSED|DRANK|FOUND|SWITCHED|COMPARED|INITIALLY|APPRECIATE|SHOULDN'?T|NOW|REMOVED)"
        r"|\bMY (?:SENSOR|LIBRE|DEXCOM|CGM|G6|G7|G5|G4|GUARDIAN|BLOOD|GLUCOSE|SUGAR|BG|ARM|METER|PUMP|DOCTOR|ENDO|PHONE|READER|RECEIVER|APP|ALARM|INSULIN|SON|DAUGHTER|CHILD|HUSBAND|WIFE|MOTHER|FATHER|MOM|DAD|SISTER|BROTHER|LIFE|BODY|SKIN|NUMBERS?|READINGS?|LEVELS?|SITE|TRANSMITTER|HEALTH|OPINION|NAME|EXPERIENCE|PHYSICIAN|TELEPHONE)\b|\bME\b|\bMYSELF\b|\bI'?M\b|\bI'?VE\b|\bI'?D\b|\bI'?LL\b|\bMINE\b"),
    "voice_caregiver": (
        "A parent, spouse, family member, friend or carer is speaking or involved",
        r"\bMY (?:SON|DAUGHTER|CHILD|KID|HUSBAND|WIFE|MOTHER|FATHER|MOM|DAD|GRAND\w+|PARTNER|PATIENT|BROTHER|SISTER|TODDLER|BABY|TEEN\w*)\b|(?:HIS|HER|THEIR|THE PATIENT'?S|THE CUSTOMER'?S|PATIENT'?S|CUSTOMER'?S|THE CAREGIVER'?S) (?:MOTHER|FATHER|MOM|DAD|PARENTS?|WIFE|HUSBAND|CAREGIVER|SPOUSE|GUARDIAN|SON|DAUGHTER(?:-IN-LAW)?|FAMILY|SIBLING|BROTHER|SISTER|GRANDPARENTS?|FRIEND|PARTNER|RESIDENT ASSISTANT)|CAREGIVER|\bPARENTS?\b|\bCARER\b|FAMILY MEMBER|SPOUSE|(?:BY|FROM) (?:A |THE |THEIR |HIS |HER )?(?:RELATIVE|NEIGHBOR|FRIEND|THIRD[- ]PARTY|NON-HEALTHCARE PROFESSIONAL|PARTNER)|THIRD[- ]PARTY (?:TREATMENT|ADMINISTRATION)|FOUND (?:HIM|HER|THEM|THE PATIENT) (?:UNRESPONSIVE|UNCONSCIOUS|ON THE FLOOR|DECEASED|DEAD|PASSED OUT)"),
    "voice_clinician": (
        "A clinician (HCP, nurse, physician, clinic, hospital staff) is named as reporter or actor",
        r"\bHCP\b|(?<!NON-)(?<!NON )HEALTH ?CARE (?:PROVIDER|PROFESSIONAL|PRACTITIONER)|PHYSICIAN|ENDOCRINOLOGIST|\bNURSE|\bRN\b|\bCDE\b|\bCDCES\b|CLINIC(?:IAN)?\b|PRESCRIBER|DOCTOR|\bMD\b|\bPCP\b|PRIMARY CARE|DIABETES EDUCATOR|PRACTITIONER|REPORTED BY (?:A |THE |AN )?(?:PHYSICIAN|NURSE|DOCTOR|HCP|CLINICIAN|HEALTH)|\bDR\.? [A-Z]|SURGEON|MEDICAL STAFF|PRESCRIBED|HOSPITAL (?:STAFF|DIABETES EDUCATOR)|ER STAFF"),
    "voice_maker_template": (
        "Maker-written third-person wording (customer reported, it was reported ...)",
        r"(?:CUSTOMER|CONSUMER|USER|COMPLAINANT|CALLER|PATIENT|REPORTER) (?:REPORTED|STATED|INDICATED|CALLED|CONTACTED|NOTED|CLAIMED|MENTIONED|ADVISED|INFORMED|EXPLAINED|ALSO REPORTED|FURTHER REPORTED|REPORTS)|IT WAS REPORTED|WAS REPORTED THAT|REPORTED (?:TO|THAT) (?:ABBOTT|DEXCOM|MEDTRONIC|MINIMED|SENSEONICS)|RECEIVED A (?:REPORT|COMPLAINT|CALL|MEDWATCH)|(?:ABBOTT|DEXCOM|MEDTRONIC|SENSEONICS|ANIMAS|ADC) (?:WAS|HAS BEEN|BECAME) (?:NOTIFIED|INFORMED|CONTACTED|MADE AWARE|AWARE)|INFORMATION RECEIVED BY MEDTRONIC|A COMPLAINT WAS RECEIVED|SENSEONICS WAS MADE AWARE"),
    # --- severity markers
    "ems_or_hospital": (
        "EMS, 911, ambulance, ER, urgent care, admission, ICU or hospital",
        r"\bEMS\b|PARAMEDIC|AMBULANCE|\b911\b|EMERGENCY (?:ROOM|DEPARTMENT|DEPT|SERVICES|MEDICAL|RESPONDERS?|CARE|PERSONNEL|DOCTOR)|\bER\b|\bED\b|\bA&E\b|URGENT CARE|HOSPITALI[SZ]|ADMITTED|\bICU\b|INTENSIVE CARE|FIRST RESPONDER|FIRE DEPARTMENT|FIREFIGHTER|POLICE|RUSHED TO|TAKEN TO (?:THE )?HOSPITAL|WENT TO (?:THE )?HOSPITAL|\bHOSPITAL\b|\bIV\b (?:FLUIDS?|GLUCOSE|DEXTROSE|THERAPY|TREATMENT|INSULIN|DRIP)|INTRAVENOUS|GLUCOSE DRIP|\bD50\b"),
    "glucagon_given": (
        "Glucagon (any brand) was used",
        r"GLUCAGON|BAQSIMI|GVOKE|ZEGALOGUE|GLUCAGEN|DASIGLUCAGON"),
    "severe_hypo_signs": (
        "Seizure, unconsciousness, unresponsive, collapse, coma or passed out",
        r"SEIZURE|SEIZING|CONVULS|UNCONSCIOUS|PASSED OUT|PASS OUT|UNRESPONSIVE|\bCOMA\b|COMATOSE|LOSS OF CONSCIOUSNESS|LOST CONSCIOUSNESS|LOSS HER CONSCIOUSNESS|BLACKED OUT|BLACK OUT|FAINT|SYNCOP|COLLAPSE|INCAPACITAT|COULD NOT (?:SPEAK|TALK|WALK|STAND|WAKE|MOVE|THINK)|COULDN'?T (?:SPEAK|TALK|WALK|STAND|WAKE|MOVE|THINK)|UNABLE TO (?:MOVE|SPEAK|SEE)|INABILITY TO MOVE|SHOCK\b|BRAIN (?:DEATH|DAMAGE|INJURY|ENCEPHALOPATHY)|CAME TO\b|REGAINED CONSCIOUSNESS|COULDN'?T WAKE"),
    "dka_or_ketones": (
        "DKA or ketones named",
        r"\bDKA\b|KETOACIDOSIS|KETONES?\b|KETOTIC"),
    "driving_or_fall_injury": (
        "Driving, a car, a fall, a head injury or a fracture is involved",
        r"\bDRIV(?:E|ING|ER|ERS)\b|\bDROVE\b|CAR ACCIDENT|MOTOR VEHICLE|BEHIND THE WHEEL|IN (?:HER|HIS|THE) CAR|CRASH(?:ED)? (?:THE |HIS |HER |MY |A |INTO )?(?:CAR|VEHICLE|TRUCK|INTO)|PULLED OVER|WHILE DRIVING|\bACCIDENT\b|\bFELL\b (?:DOWN|AND|TO THE|OUT OF|OFF|WHILE)|\bFALL\b (?:DOWN|AND HIT|RESULT|OUT OF|THAT)|TRIPPED(?! TREND)|HIT (?:HIS|HER|MY|THEIR) HEAD|HEAD (?:INJURY|PAIN)|BUMP ON (?:HIS|HER|THE) HEAD|BLACK EYE|FRACTUR|BROKEN (?:LEG|ARM|HIP|WRIST|BONE|NOSE)|BROKE (?:HIS|HER|MY|THEIR|A) (?:ARM|LEG|HIP|WRIST|BONE|NOSE|TOOTH|TEETH)"),
    "pregnancy": (
        "Pregnancy, fetus or breastfeeding",
        r"PREGNAN|GESTATION|TRIMESTER|POSTPARTUM|BREAST ?FEED|\bFETUS|\bFETAL|UNBORN|MISCARRIAGE|INDUCED LABOR"),
    # --- what the maker told the user, labels, replacement, repeats, channels
    "maker_advised_meter_or_calibration": (
        "Maker advised the user to use a meter / fingerstick / calibrate properly / charge or change the device",
        r"\b(?:ADVISED|INSTRUCTED|RECOMMENDED|REMINDED|INFORMED|TOLD|EDUCATED|COUNSELED|ENCOURAGED|DIRECTED|SUGGESTED|REINFORCED|ASSISTED|EXPLAINED)\b[^.]{0,120}?\b(?:FINGER ?STICK|FINGER ?PRICK|BLOOD GLUCOSE METER|BG METER|GLUCOSE METER|GLUCOMETER|\bMETER\b|CALIBRAT|TREATMENT DECISIONS?|CONFIRM(?:ED|ING)? (?:WITH|USING|BY|VIA) (?:A |THE )?(?:METER|FINGER|BLOOD)|CHANGE (?:THE |OUT THE )?SENSOR|REPLACE (?:THE )?SENSOR|CHARGE|CORRECT (?:THE )?TIME|TIME CORRECTION|POSSIBLE CAUSES|RE-?LINK|TRUE (?:BG|FINGER))"
        r"|SYMPTOMS (?:THAT )?(?:DO|DID|DOES) NOT MATCH|(?:DO|DOES|DID) NOT MATCH (?:THEIR |YOUR |HIS |HER )?SYMPTOMS|ALWAYS (?:CONFIRM|VERIFY|CHECK)[^.]{0,40}(?:METER|FINGER|BLOOD GLUCOSE)|(?:USE|PERFORM|TAKE|OBTAIN) (?:A |THE )?(?:BLOOD GLUCOSE |BG |GLUCOSE )?(?:METER|FINGER ?STICK|FINGER ?PRICK)[^.]{0,60}(?:BEFORE|PRIOR TO|TO (?:CONFIRM|VERIFY|MAKE))|IMPORTANT FOR THE USER TO ENTER|ENTER CALIBRATIONS WITH|CUSTOMER WAS RECOMMENDED"),
    "maker_cites_label": (
        "Maker cites the label / instructions for use (known risk, warned-about use)",
        r"LABELING (?:INDICATES|STATES|WARNS|PROVIDES|INSTRUCTS)|LABELLING|PER (?:THE )?(?:LABELING|IFU|INSTRUCTIONS FOR USE|USER GUIDE)|INSTRUCTIONS FOR USE|USER (?:GUIDE|MANUAL)|\bIFU\b|MITIGATED THROUGH THE[^.]{0,40}LABEL|KNOWN (?:AND ANTICIPATED )?(?:POTENTIAL )?(?:ADVERSE (?:EFFECT|EVENT)|RISK|SIDE EFFECT)|KNOWN ANTICIPATED|PRODUCT INSERT|COMPATIBILITY GUIDE|NO WARNING LABEL"),
    "user_error_or_misuse_claimed": (
        "Maker attributes the event to user error, misuse, off-label use, unsupported phone or bad calibration",
        r"USER ERROR|MISUSE OF THE DEVICE|WHICH IS MISUSE|IS MISUSE|OFF-?LABEL USAGE|OFF-?LABEL|UNSUPPORTED (?:OPERATING SYSTEM|OS|DEVICE|PHONE)|NOT (?:A )?SUPPORTED (?:SYSTEM|DEVICE)|NOT COMPATIBLE|NOT CALIBRATING PROPERLY|CALIBRAT\w+ (?:INCONSISTENC|INCORRECTLY|IMPROPERLY)|ESTIMATED VALUES[^.]{0,80}(?:CALIBRATION|ENTERED)|ENTERED AS CALIBRATIONS|WRONG TIME PROGRAMMED|TIME ON THE INSULIN PUMP WAS INCORRECT|NOT COUNTING (?:THE )?CARB|DUE TO USER|NOT MANAGING (?:HER|HIS|THEIR) DIABETES|DID NOT (?:CHANGE|TREAT|PERFORM A FINGERSTICK|CHECK (?:THE |HER |HIS )?BG)|WAS NOT (?:USING|ENTERING TRUE)|DOESN'?T CALIBRATE CORRECTLY|IMPROPER SITE SELECTION|SAME APPLICATION SITE|PHONE WAS COVERED|COVERED UNDER"),
    "replacement_or_refund": (
        "Replacement, credit or refund given, offered, requested or refused",
        r"REPLACEMENT|\bREPLACED\b|\bREPLACE\b(?! SENSOR\b)|REFUND|\bCREDIT(?:ED)?\b|REIMBURS|SENT (?:A |THE |AN |OUT A )?NEW|NEW (?:SENSOR|TRANSMITTER|RECEIVER|READER) (?:WAS |WILL BE |HAS BEEN )?(?:SENT|SHIPPED|PROVIDED|ISSUED|MAILED|GIVEN|INSERTED)|(?:SHIPPED|SENT|PROVIDED|ISSUED|OFFERED|MAILED|GIVEN) (?:A |THE |AN )?(?:REPLACEMENT|NEW)|WARRANTY"),
    "repeat_failures": (
        "Several sensors failed or the problem keeps happening (not a one-off)",
        r"(?:SECOND|THIRD|FOURTH|FIFTH|ANOTHER|MULTIPLE|SEVERAL|NUMEROUS|EVERY|EACH|TWO|THREE|FOUR|FIVE|SIX|REPEATED|CONSECUTIVE|LAST FEW|PAST FEW|SAME|PREVIOUS|PRIOR|FIRST 2|FIRST TWO) (?:\w+ )?SENSORS?\b[^.]{0,80}(?:FAIL|ISSUE|PROBLEM|SAME|ALSO|AGAIN|ERROR|INACCUR|FELL|LOW|HIGH|STOPPED|ENDED|OFF|READ|WORK|DID NOT|DIDN'?T|LASTED|REPLACED)"
        r"|(?:THIS|IT) (?:HAS |HAD )?(?:HAPPENED|OCCURRED) (?:BEFORE|AGAIN|MULTIPLE|SEVERAL|MANY|TWICE|\d|ON)|(?:MULTIPLE|SEVERAL|NUMEROUS|MANY|REPEATED|REPEAT|RECURR\w*|ONGOING|CONTINUED|FREQUENT(?:LY)?|CONSTANT|COUNTLESS) (?:TIMES|OCCASIONS|SENSORS|FAILURES|ISSUES|OCCURRENCES|INCIDENTS|EVENTS|COMPLAINTS|PROBLEMS|ERRORS|EPISODES|INSTANCES|MOTOR ERROR|NO DELIVERY|ALARMS|CALIBRATION ERRORS)|KEEPS? (?:HAPPENING|FAILING|OCCURRING|GIVING|READING|SHOWING|SAYING|DOING|GOING|LOSING|FALLING|COMING)|KEEP FAILING|(?:EVERY|EACH) SENSOR|EVERY SINGLE SENSOR|(?:THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|\d{1,2}) (?:FAULTY |FAILED |BAD )?SENSORS\b|\d+(?:ST|ND|RD|TH) SENSOR|NOT THE FIRST TIME|(?:SAME|SIMILAR) (?:ISSUE|PROBLEM|THING|EVENT|COMPLAINT|PROBLEMS) (?:WITH|HAPPENED|OCCURRED|AGAIN|BEFORE|EVERY|EACH|ON)|\d+ (?:FAIL|FAILED|FAILURES) IN A ROW|IN A ROW|FOR WEEKS|AS USUAL|FAILED HIM FOR|SIGNAL LOSS OCCURRED FREQUENTLY|OCCURRED FREQUENTLY|MULTIPLE (?:MOTOR ERROR|NO DELIVERY|CALIBRATION ERROR|SENSOR ERROR)S?"),
    "libre_scan": (
        "Scanning (Libre reader or phone scan) named",
        r"(?<!CT )(?<!CAT )(?<!MRI )(?<!PET )\bSCAN(?:NED|NING|S)?\b"),
    "recall_or_field_action": (
        "A recall, field action, safety notice or corrections-and-removals number is cited",
        r"RECALL(?:ED|S)?\b|FIELD ACTION|FA\d{4}-\d{4}|FSCA|CORRECTIONS? AND REMOVAL|REMOVAL NUMBER|NOTIFICATION (?:QD|FA)\d|QD\d{4}-\d{4}|SAFETY NOTICE|URGENT MEDICAL DEVICE|QUALITY RECORD|\bQR\d{6,}"),
    "death_investigation": (
        "Coroner, medical examiner, autopsy, death certificate or post-mortem named",
        r"CORONER|MEDICAL (?:EXAMINER|INVESTIGATOR)|AUTOPSY|DEATH CERTIFICAT|POST[- ]?MORTEM|CAUSE OF (?:THE )?DEATH|PRONOUNCED DEAD|OBITUARY|PASSED AWAY|DECEASED|\bDIED\b"),
    "legal_or_escalation": (
        "Lawyer, lawsuit, 'report to FDA', 'should be recalled' or similar escalation language",
        r"ATTORNEY|LAWYER|LAWSUIT|\bLEGAL\b|LITIGATION|\bSUE\b|SUING|CLASS ACTION|BETTER BUSINESS|\bBBB\b|(?:CONTACT|REPORT)(?:ED|ING)? (?:THIS |IT |THE MATTER )?TO (?:THE )?FDA|FDA (?:SHOULD|NEEDS|MUST)|SHOULD (?:NOT )?BE (?:ALLOWED|RECALLED|SOLD)|NEEDS TO BE RECALLED|WARN OTHERS|PROTECT (?:ME|OTHERS)|INVESTIGATION INTO THE MATTER|PUTS MY LIFE IN DANGER|HORRENDOUS|INFERIOR|POOR FUNCTIONING|USED AS EVIDENCE"),
    "report_channel_named": (
        "How the complaint came in: social media, web form, email, MedWatch, distributor, HCP office",
        r"SOCIAL MEDIA|ONLINE (?:ARTICLE|POST|REVIEW)|WEB ?FORM|VIA E-?MAIL|MEDWATCH|\bMW\d{7}\b|FDA SAFETY REPORT|VOLUNTARY (?:MDR|REPORT)|FOREIGN DISTRIBUTOR|DISTRIBUTOR CONTACTED|HCP OFFICE|TECHNICAL SUPPORT|CUSTOMER SERVICE|VIA (?:PHONE CALL|TELEPHONE|LETTER)|RETROSPECTIVE(?:LY)? (?:REPORTING|AS PART)|INTERNAL REVIEW"),
    "reporter_unreachable_or_info_withheld": (
        "Reporter could not be reached, declined follow-up, or patient details withheld (privacy rules)",
        r"PRIVACY REGULATIONS|DID NOT CONSENT|DIDN'?T CONSENT|DECLINED (?:FURTHER CONTACT|TO (?:BE CONTACTED|PROVIDE|CONTINUE)|FURTHER)|NO CONTACT INFORMATION WAS PROVIDED|UNABLE TO (?:ATTEMPT|PURSUE) (?:ANY )?FOLLOW[- ]?UP|FOLLOW[- ]?UP ATTEMPTS WERE UNSUCCESSFUL|ATTEMPTS (?:BY ADC )?TO (?:CONTACT|OBTAIN|GATHER)[^.]{0,80}UNSUCCESSFUL|DID NOT RESPOND|UNRESPONSIVE DESPITE|NO RESPONSE WAS RECEIVED|UNABLE TO PROVIDE ANY FURTHER|PATIENT INFORMATION CANNOT BE PROVIDED"),
    "report_submitted_in_error": (
        "Maker later said the report was submitted in error / not reportable",
        r"SUBMITTED IN ERROR|REPORTED IN ERROR|NOT (?:A )?REPORTABLE|DOES NOT MEET THE CRITERIA OF A REPORTABLE|DEEMED NOT REPORTABLE|NO LONGER CONSTITUTE AN ADVERSE EVENT|PLEASE DISREGARD"),
}
COMPILED = {k: re.compile(v[1]) for k, v in THEMES.items()}
# Themes matched on the raw text (the boilerplate they look for is the point); all others on the stripped text.
THEMES_ON_RAW = {"maker_cites_label", "reporter_unreachable_or_info_withheld", "voice_maker_template", "report_submitted_in_error"}


def theme_flags(texts):
    """DataFrame of 0/1 flags, one column per theme. Boilerplate sentences are removed first."""
    stripped = [strip_boilerplate(t) for t in texts]
    out = {}
    for k, rx in COMPILED.items():
        src = texts if k in THEMES_ON_RAW else stripped
        out[k] = np.fromiter((1 if rx.search(t) else 0 for t in src), dtype=np.int8, count=len(src))
    return pd.DataFrame(out)


def theme_rates(flags, groups, weights=None, label=""):
    """Hit rate per theme per group (weighted if weights given)."""
    rows = []
    g = pd.Series(groups).reset_index(drop=True)
    w = pd.Series(weights).reset_index(drop=True) if weights is not None else pd.Series(np.ones(len(flags)))
    f = flags.reset_index(drop=True)
    for grp in ["all"] + sorted(g.unique()):
        m = np.ones(len(f), dtype=bool) if grp == "all" else (g == grp).values
        ww = w[m]
        n = int(m.sum())
        for k in THEMES:
            hits = f.loc[m, k].values
            rows.append({"table": label, "group": grp, "n_reports": n, "weighted_n": round(float(ww.sum())),
                         "theme": k, "theme_label": THEMES[k][0],
                         "hits_n": int(hits.sum()),
                         "hit_pct": round(100.0 * float((hits * ww.values).sum()) / float(ww.sum()), 1) if ww.sum() else float("nan")})
    return pd.DataFrame(rows)


def eval_crosstab(serious, flags):
    """The maker's structured 'device evaluated' code vs the text evaluation themes (serious reports)."""
    code = serious["device_evaluated_by_manufacturer"].astype("string").fillna("blank").str.strip()
    code_label = code.map({"Y": "Y = evaluated", "N": "N = not evaluated", "R": "R = device not returned", "*": "* = not provided", "blank": "blank"}).fillna(code)
    avail = serious["device_availability"].astype("string").fillna("blank")
    rows = []
    for name, series in [("device_evaluated_by_manufacturer", code_label), ("device_availability", avail)]:
        for g, idx in series.groupby(series).groups.items():
            part = flags.loc[idx]
            n = len(part)
            row = {"structured_field": name, "value": str(g), "n_reports": n, "pct_of_serious": pct(n, len(serious))}
            for k in ["eval_device_returned", "eval_not_returned", "eval_no_defect_found", "eval_defect_confirmed",
                      "eval_root_cause_not_determined", "eval_investigation_pending"]:
                row[f"text_{k}_pct"] = pct(part[k].sum(), n)
            rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Part 5: beyond death + injury
# ----------------------------------------------------------------------------
def malfunction_text_dedup(full_demo):
    """Hash every report's text; find template texts and the real pool for a bigger text run."""
    log("hashing the texts of all 3.38 M reports (row groups; about 1 to 2 minutes) ...")
    pf = pq.ParquetFile(CLEAN / "full.parquet")
    hashes, keys = [], []
    for i, batch in enumerate(pf.iter_batches(batch_size=250000, columns=["mdr_report_key", "event_text", "mfr_narrative"])):
        d5 = pc.fill_null(batch.column("event_text"), "")
        h10 = pc.fill_null(batch.column("mfr_narrative"), "")
        joined = pc.binary_join_element_wise(d5, h10, " || ")
        s = pd.Series(joined.to_pandas())
        hashes.append(pd.util.hash_pandas_object(s, index=False).values)
        keys.append(batch.column("mdr_report_key").to_pandas().astype(str).values)
        if i % 4 == 3:
            log(f"  {(i + 1) * 250000:,} rows hashed")
    keys = np.concatenate(keys)
    hashes = np.concatenate(hashes)
    df = full_demo[["mdr_report_key", "event_type", "maker", "family", "accuracy_code", "text_chars"]].copy()
    if len(keys) == len(df) and np.array_equal(df["mdr_report_key"].values.astype(str), keys):
        df["text_hash"] = hashes          # same row order as the parquet file
    else:
        df = df.merge(pd.DataFrame({"mdr_report_key": keys, "text_hash": hashes}), on="mdr_report_key", how="left")
    mal = df[df["event_type"] == "Malfunction"].copy()
    counts = mal["text_hash"].value_counts()
    mal["copies"] = mal["text_hash"].map(counts).fillna(1).astype(int)
    mal["is_template"] = mal["copies"] >= TEMPLATE_MIN_COPIES
    mal["long_enough"] = mal["text_chars"] >= MIN_TEXT_CHARS
    mal["unique_story"] = ~mal["is_template"] & mal["long_enough"]
    rows = []
    for g, part in [("all makers", mal)] + list(mal.groupby("maker", observed=True)):
        n = len(part)
        acc = part["accuracy_code"].fillna(False).astype(bool)
        rows.append({
            "maker": g, "malfunction_reports": n,
            "distinct_texts": int(part["text_hash"].nunique()),
            "template_text_pct": pct(part["is_template"].sum(), n),
            "n_templates": int((part.loc[part["is_template"], "text_hash"]).nunique()),
            "short_text_under_120_chars_pct": pct((~part["long_enough"]).sum(), n),
            "unique_story_pct": pct(part["unique_story"].sum(), n),
            "unique_story_n": int(part["unique_story"].sum()),
            "accuracy_code_pct": pct(acc.sum(), n),
            "accuracy_code_n": int(acc.sum()),
            "accuracy_code_and_unique_story_n": int((acc & part["unique_story"]).sum()),
            "accuracy_code_and_unique_story_pct_of_malfunction": pct((acc & part["unique_story"]).sum(), n),
            "median_text_chars": float(part["text_chars"].median()),
        })
    dedup = pd.DataFrame(rows)
    top = counts.head(15)      # the most-copied malfunction texts, for the memo
    return dedup, mal, top


def template_examples(mal, top):
    """Fetch the first 100 characters of the 15 most-copied malfunction texts (by key)."""
    keys = [mal.loc[mal["text_hash"] == h, "mdr_report_key"].iloc[0] for h in top.index]
    want = set(keys)
    found = {}
    pf = pq.ParquetFile(CLEAN / "full.parquet")
    for batch in pf.iter_batches(batch_size=250000, columns=["mdr_report_key", "event_text", "mfr_narrative", "manufacturer", "brand_name"]):
        k = batch.column("mdr_report_key").to_pandas().astype(str)
        m = k.isin(want)
        if m.any():
            b = batch.to_pandas()[m.values]
            for _, r in b.iterrows():
                found[str(r["mdr_report_key"])] = (maker_of(r["manufacturer"], r["brand_name"]),
                                                   (str(r["event_text"] or "")[:100]), (str(r["mfr_narrative"] or "")[:60]))
        if len(found) == len(want):
            break
    rows = []
    for h, k in zip(top.index, keys):
        mk, d5, h10 = found.get(k, ("", "", ""))
        rows.append({"copies": int(top[h]), "maker": mk, "example_key": k, "event_text_first_100_chars": d5,
                     "mfr_narrative_first_60_chars": h10})
    return pd.DataFrame(rows)


def beyond_serious(llm, sample, serious):
    """Weighted fault mix and error sizes in the malfunction sample vs serious reports; cost of more text."""
    if llm is None:
        return pd.DataFrame(), pd.DataFrame()
    sm = sample[["mdr_report_key", "maker4", "weight"]].copy()
    sm["mdr_report_key"] = sm["mdr_report_key"].astype(str)
    m = llm[llm["split"] == "sample"].merge(sm, on="mdr_report_key", how="inner")
    s = llm[llm["split"] != "sample"].copy()
    s["weight"] = 1.0
    s = s.merge(serious[["mdr_report_key", "maker4"]], on="mdr_report_key", how="left")
    wrong = {"reads_low", "reads_high", "erratic", "stuck"}
    rows = []

    def wpct(mask, w):
        return round(100.0 * float(w[mask].sum()) / float(w.sum()), 1) if w.sum() else float("nan")

    def wquant(vals, w, q):
        vals = np.asarray(vals, float)
        w = np.asarray(w, float)
        ok = ~np.isnan(vals)
        vals, w = vals[ok], w[ok]
        if len(vals) == 0:
            return float("nan")
        o = np.argsort(vals)
        cw = np.cumsum(w[o]) / w[o].sum()
        return round(float(vals[o][np.searchsorted(cw, q)]), 1)

    for label, part in [("Malfunction sample (weighted), all", m)] + [(f"Malfunction sample (weighted), {k}", g) for k, g in m.groupby("maker4")] + \
                       [("Serious (death + injury), all", s)] + [(f"Serious, {k}", g) for k, g in s.groupby("maker4")]:
        w = part["weight"]
        ft = part["fault_type"].fillna("unclear")
        pairs = part[part["has_pair"]]
        rows.append({
            "group": label, "n_reports": len(part), "weighted_reports": round(float(w.sum())),
            "wrong_reading_pct": wpct(ft.isin(wrong), w), "reads_low_pct": wpct(ft == "reads_low", w),
            "reads_high_pct": wpct(ft == "reads_high", w), "signal_loss_pct": wpct(ft == "signal_loss", w),
            "sensor_error_early_end_pct": wpct(ft == "sensor_error_or_early_end", w),
            "unclear_pct": wpct(ft == "unclear", w),
            "both_values_pct": wpct(part["has_pair"], w), "pairs_n": len(pairs),
            "err_pct_p10": wquant(pairs["err_pct"], pairs["weight"], 0.10),
            "err_pct_median": wquant(pairs["err_pct"], pairs["weight"], 0.50),
            "err_pct_p90": wquant(pairs["err_pct"], pairs["weight"], 0.90),
            "err_mgdl_median": wquant(pairs["err_mgdl"], pairs["weight"], 0.50),
            "sensor_below_meter_pct": wpct(pairs["err_mgdl"] < 0, pairs["weight"]) if len(pairs) else float("nan"),
            "beyond_20pct_pct": wpct(pairs["err_pct"].abs() > 20, pairs["weight"]) if len(pairs) else float("nan"),
            "outcome_none_pct": wpct(part["outcome"].fillna("not_stated") == "none", w),
        })
    return pd.DataFrame(rows), m


def cost_table(dedup):
    """What a bigger text run would cost at the measured speed."""
    rows = []
    allrow = dedup[dedup["maker"] == "all makers"].iloc[0]
    options = [
        ("A. Every malfunction report", int(allrow["malfunction_reports"])),
        ("B. Malfunction reports with a real story (not a template text, 120+ characters)", int(allrow["unique_story_n"])),
        ("C. Malfunction reports with a wrong-readings code", int(allrow["accuracy_code_n"])),
        ("D. Wrong-readings code AND a real story", int(allrow["accuracy_code_and_unique_story_n"])),
        ("E. Option D, Abbott only", int(dedup.loc[dedup["maker"] == "Abbott", "accuracy_code_and_unique_story_n"].iloc[0]) if (dedup["maker"] == "Abbott").any() else 0),
        ("F. Option D, 10 % random sample (weighted)", int(round(allrow["accuracy_code_and_unique_story_n"] * 0.10))),
    ]
    for label, n in options:
        minutes = n / REPORTS_PER_MINUTE
        rows.append({"option": label, "reports": n, "gpu_hours": round(minutes / 60, 1), "gpu_days_8h": round(minutes / 60 / 8, 1),
                     "calendar_days_24h": round(minutes / 60 / 24, 1)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", type=Path, default=None, help=f"one raw openFDA bulk zip to stream (default {DEFAULT_ZIP.name} if present)")
    ap.add_argument("--skip-zip", action="store_true", help="do not stream a raw zip")
    ap.add_argument("--write-texts", type=Path, default=None, help="write the 300 sample texts to this file (not in git)")
    ap.add_argument("--skip-hash", action="store_true", help="skip the 3.38 M text hashing step (part 5 dedup)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    stats = {"seed": SEED, "date": "2026-11-06"}
    codes = set(json.load(open(HERE / "config.json"))["product_codes"])

    serious = load_serious()
    sample = load_sample()
    llm = load_llm()

    # ---- Part 1: field inventory
    log("part 1: field inventory")
    inv_s = fill_table(serious.drop(columns=["text", "has_text", "maker4", "year"]), label="serious.csv.gz")
    write_csv(inv_s, "fill_rates_serious.csv")
    inv_m = fill_table(sample.drop(columns=["text", "maker4", "year"]), weights=sample["weight"], label="sample_local.parquet (malfunction, weighted)")
    write_csv(inv_m, "fill_rates_sample_weighted.csv")
    key_cols = ["patient_age", "patient_sex", "patient_weight", "patient_race", "patient_ethnicity", "device_evaluated_by_manufacturer",
                "device_availability", "remedial_action", "lot_number", "model_number", "udi_di", "date_of_event", "reporter_occupation_code",
                "health_professional", "source_type", "event_location", "device_age_text", "mfr_narrative", "event_text"]
    fb = pd.concat([fill_by_group(serious, key_cols, "maker", "serious"), fill_by_group(serious, key_cols, "event_type", "serious"),
                    fill_by_group(serious, key_cols, "year", "serious")], ignore_index=True)
    write_csv(fb, "fill_rates_serious_by_group.csv")
    stats["serious_rows"] = int(len(serious))
    stats["serious_columns"] = int(inv_s.shape[0])
    stats["serious_fill"] = {r["column"]: r["fill_pct"] for _, r in inv_s.iterrows()}

    zip_path = None if args.skip_zip else (args.zip or (DEFAULT_ZIP if DEFAULT_ZIP.exists() else None))
    if zip_path and zip_path.exists():
        raw_fields, text_types, zinfo = part1_raw_zip(zip_path, codes)
        write_csv(raw_fields, "raw_fields_one_zip.csv")
        write_csv(text_types, "raw_text_types_one_zip.csv")
        stats["raw_zip"] = zinfo
        stats["raw_fields_total"] = int(len(raw_fields))
        stats["raw_fields_dropped"] = int((raw_fields["kept_by_clean_step"] == "no").sum())
        stats["raw_fields_dropped_filled_in_cgm_over_5pct"] = raw_fields[(raw_fields["kept_by_clean_step"] == "no") & (raw_fields["cgm_fill_pct"] >= 5)]["raw_field"].tolist()
    else:
        log("no raw zip streamed (use --zip PATH)")

    # ---- Part 2: demographics
    log("part 2: demographics")
    full = load_full_demo()
    write_csv(country_per_report(full), "country_per_report.csv")
    write_csv(demo_fill_rates(full), "demographics_fill_rates.csv")
    write_csv(demo_age_sex(full), "demographics_age_sex.csv")
    write_csv(demo_filled_vs_unfilled(full, llm), "demographics_filled_vs_unfilled.csv")
    age_txt, age_txt_keys = demo_age_in_text(serious)
    write_csv(age_txt, "demographics_age_in_text.csv")
    trial = trial_demographics()
    write_csv(side_by_side(full, trial), "demographics_trial_side_by_side.csv")
    stats["age_fill_pct_all"] = pct(full["age_filled"].sum(), len(full))
    stats["sex_fill_pct_all"] = pct(full["sex_filled"].sum(), len(full))
    stats["trial"] = trial

    # ---- Part 3: the 300 reading sample
    log("part 3: reading sample")
    s300 = draw_sample_300(serious, sample)
    with open(OUT / "sample_300_keys.txt", "w", encoding="utf-8") as f:
        f.write("# 300 MAUDE report keys (mdr_report_key) read by hand for FIELD_INVENTORY.md. Seed 20261106.\n")
        f.write("# Columns: mdr_report_key, event_type, maker, source table.\n")
        for _, r in s300.iterrows():
            f.write(f"{r['mdr_report_key']}\t{r['event_type']}\t{r['maker4']}\t{r['source']}\n")
    log(f"wrote {OUT / 'sample_300_keys.txt'}")
    f300 = theme_flags(s300["text"].tolist())
    f300.insert(0, "mdr_report_key", s300["mdr_report_key"].values)
    f300.insert(1, "stratum", s300["stratum"].values)
    write_csv(f300, "theme_hits_sample300_by_report.csv")
    if args.write_texts:
        args.write_texts.parent.mkdir(parents=True, exist_ok=True)
        with open(args.write_texts, "w", encoding="utf-8") as f:
            for i, (_, r) in enumerate(s300.iterrows(), 1):
                f.write(f"\n===== #{i} key={r['mdr_report_key']} | {r['event_type']} | {r['maker4']} | {str(r['brand_name'])[:50]} =====\n")
                f.write(r["text"][:6000] + "\n")
        log(f"wrote sample texts to {args.write_texts}")

    # ---- Part 4: themes at scale
    log("part 4: running the theme patterns over all serious reports (about 2 to 4 minutes) ...")
    has = serious["has_text"].values
    flags_s = theme_flags(serious.loc[has, "text"].tolist())
    flags_s.index = serious.index[has]
    rates_s = theme_rates(flags_s, serious.loc[has, "maker4"], label="serious (death + injury), unweighted")
    rates_e = theme_rates(flags_s, serious.loc[has, "event_type"], label="serious by event type")
    write_csv(pd.concat([rates_s, rates_e], ignore_index=True), "theme_hits_serious.csv")
    log("part 4: themes over the weighted malfunction sample ...")
    has_m = (sample["text"].str.strip().str.len() > 4).values
    flags_m = theme_flags(sample.loc[has_m, "text"].tolist())
    rates_m = theme_rates(flags_m, sample.loc[has_m, "maker4"], weights=sample.loc[has_m, "weight"], label="malfunction sample (weighted)")
    write_csv(rates_m, "theme_hits_sample_weighted.csv")
    write_csv(eval_crosstab(serious.loc[has], flags_s), "eval_code_vs_text.csv")
    # theme pattern list, for reuse and for the memo
    write_csv(pd.DataFrame([{"theme": k, "label": v[0], "pattern": v[1]} for k, v in THEMES.items()]), "theme_patterns.csv")
    stats["theme_hit_pct_serious_all"] = {r["theme"]: r["hit_pct"] for _, r in rates_s[rates_s["group"] == "all"].iterrows()}
    stats["theme_hit_pct_sample_all_weighted"] = {r["theme"]: r["hit_pct"] for _, r in rates_m[rates_m["group"] == "all"].iterrows()}

    # ---- Part 5: beyond death + injury
    log("part 5: beyond death + injury")
    bs, _ = beyond_serious(llm, sample, serious)
    write_csv(bs, "beyond_serious_fault_mix.csv")
    if not args.skip_hash:
        dedup, mal, top = malfunction_text_dedup(full)
        write_csv(dedup, "malfunction_text_dedup.csv")
        write_csv(template_examples(mal, top), "malfunction_template_texts.csv")
        write_csv(cost_table(dedup), "bigger_text_run_cost.csv")
        stats["malfunction_dedup"] = dedup.to_dict("records")

    with open(OUT / "inventory_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1, default=str)
    log(f"done. Outputs in {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
