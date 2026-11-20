"""
Shared preprocessing for BMEN 600 Group 24 (CGM accuracy project).

What this module does
  Reads the raw REPLACE-BG tables and the Shanghai Excel files ONCE, cleans
  them, and saves tidy tables as parquet files in a cache folder. Every later
  analysis loads the cache (a few seconds) instead of re-parsing 837 MB.

Run from the repo root to build or refresh the cache
  python analysis/preprocess.py "Uncommitted Data/Raw Data Dump" analysis/cache
  python analysis/preprocess.py "Uncommitted Data/Raw Data Dump" analysis/cache --rebuild

Use from a script
  import preprocess as pp                      # (analysis/ must be on sys.path)
  cgm   = pp.load_cgm(ROOT)                    # CGM readings, duplicates dropped
  pairs = pp.verified_pairs(ROOT)              # HEADLINE pair set: verified fingerstick vs CGM, in window
  allp  = pp.build_pairs(ROOT)["meter"]        # every meter-table pair (pump entries and calibrations included)
  ppl   = pp.load_participants(ROOT)           # one row per participant

Every load_* / build_* function takes the data folder as its first argument,
reads the cache if it is valid, and otherwise builds the table from the raw
files and writes the cache. Pass rebuild=True to force a rebuild.
Full description of every cleaning rule: analysis/PREPROCESSING.md.

Headline pair rule (added 2026-10-30, CACHE_VERSION 2026-10-30.1)
  The BGM table mixes two sources: the meter's own log and "BG" values stored by
  insulin pumps. Many pump entries are CGM values typed into the pump's bolus
  calculator: in the CGM-only arm about a third of them have an error of exactly
  0, elsewhere 9-20 %. `used_for_calibration` does not catch them and
  `pump_copy_of_meter` catches only 12 %. So every BGM row and meter pair carries
    from_meter_log          = the value comes from the meter's own log (source == 'meter')
    is_verified_fingerstick = from_meter_log AND NOT used_for_calibration
  verified_pairs() = meter pairs with is_verified_fingerstick, inside the study window.
  This is the headline set for the paper (168,990 pairs, 226 people, MARD 13.3 %).
  'independent_meter' (not used for calibration, pump entries kept) stays for old code.

Terms used in the docstrings
  CGM = continuous glucose monitor (skin sensor, one reading every 5 min).
  BGM / meter = fingerstick blood glucose meter.
  Calibration = a fingerstick value typed into the Dexcom receiver.
  Pump BG entry = a glucose value stored by the insulin pump (typed by hand or sent by a linked meter).
  Sensor session = the days one sensor was worn (inferred, see PREPROCESSING.md).
"""
import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Settings. Change here, nowhere else.
# ---------------------------------------------------------------------------
CACHE_VERSION = "2026-10-30.1"      # bump this when any rule below changes; old caches are rebuilt
DEFAULT_ROOT = "Uncommitted Data/Raw Data Dump"
DEFAULT_CACHE = "analysis/cache"

WINDOW_FIRST_DAY, WINDOW_LAST_DAY = 0, 329   # study window, days from enrolment (inclusive)
REF_MIN, REF_MAX = 20, 600                   # reference (meter / calibration) values outside this are codes or unit errors
CGM_FLOOR, CGM_CEILING = 39, 401             # Dexcom G4 display limits (values are clipped here)
SESSION_GAP_S = 6900                         # a gap of >= 115 min between readings starts a new sensor session
STARTUP_CAL_WINDOW_S = 1800                  # a calibration within 30 min before a session's first reading "confirms" the start
ROC_GAP_MIN_S, ROC_GAP_MAX_S = 240, 360      # rate of change needs both neighbours 4-6 min away
NIGHT_START_H, NIGHT_END_H = 0, 6            # is_night = 00:00 to 06:00
CAL_PAIR_TOL_S = 600                         # calibration pairs: last CGM reading up to 10 min before the calibration
METER_PAIR_TOL_S = 300                       # meter pairs: nearest CGM reading within 5 min
USED_FOR_CAL_TOL_S = 300                     # meter reading = calibration if same value within 5 min
PUMP_COPY_TOL_S = 300                        # pump BG entry = copy of a meter reading if same value within 5 min
MMOL_TO_MGDL = 18.01559                      # Tidepool stores pump glucose fields in mmol/L
FAKE_EPOCH = pd.Timestamp("2000-01-01")      # day 0 (enrolment) is mapped to this date; dates are de-identified
RANGE_EDGES = [0, 54, 70, 180, 250, 10_000]
RANGE_LABELS = ["<54", "54-69", "70-180", "181-250", ">250"]

_T0 = [None]


def _log(*a):
    """Print a progress line with elapsed seconds since the first call."""
    if _T0[0] is None:
        _T0[0] = time.time()
    print(f"[preprocess {time.time() - _T0[0]:6.1f}s]", *a, flush=True)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def rb_dir(root):
    """Folder with the REPLACE-BG pipe-delimited tables."""
    return os.path.join(root, "Replace-BG Dataset", "Data Tables")


def sh_dir(root):
    """Folder with the Shanghai data (one extra sub-folder of any name inside it)."""
    return os.path.join(root, "Shanghai")


def check_raw_data(root):
    """Stop with one plain line if the raw data is not where we expect it."""
    for f in ["HPtRoster.txt", "HScreening.txt", "HDeviceCGM.txt", "HDeviceBGM.txt", "HDeviceUploads.txt"]:
        if not os.path.isfile(os.path.join(rb_dir(root), f)):
            sys.exit(f"Data not found: expected {os.path.join(rb_dir(root), f)}. "
                     f"Pass the data folder as the first argument (see analysis/REPRODUCIBILITY.md).")
    for pat in ["Shanghai_T1DM_Summary.xlsx", "Shanghai_T2DM_Summary.xlsx", "Shanghai_T1DM", "Shanghai_T2DM"]:
        if not glob.glob(os.path.join(sh_dir(root), "*", pat)):
            sys.exit(f"Data not found: expected {os.path.join(sh_dir(root), '<one sub-folder>', pat)}. "
                     f"See analysis/REPRODUCIBILITY.md for the folder layout.")


def _read_table(root, name, **kw):
    """Read one REPLACE-BG table (pipe-delimited text)."""
    return pd.read_csv(os.path.join(rb_dir(root), name), sep="|", **kw)


def seconds_from_enrol(days, tm):
    """Seconds from enrolment midnight: day number * 86400 + 'HH:MM:SS' of the device clock.

    Fast path: all time strings are exactly 8 characters, so the digits are read
    directly. Falls back to string splitting if any value has another length.
    """
    days = np.asarray(days, dtype="int64")
    s = pd.Series(tm)
    if (s.str.len() == 8).all():
        d = np.frombuffer(s.to_numpy().astype("S8").tobytes(), dtype=np.uint8).reshape(-1, 8).astype("int64") - 48
        tod = (d[:, 0] * 10 + d[:, 1]) * 3600 + (d[:, 3] * 10 + d[:, 4]) * 60 + d[:, 6] * 10 + d[:, 7]
    else:
        p = s.str.split(":", expand=True).astype("int64")
        tod = (p[0] * 3600 + p[1] * 60 + p[2]).to_numpy()
    return days * 86400 + tod


def fake_datetime(t):
    """Datetime column for plotting / resampling. Day 0 = 2000-01-01. NOT a real calendar date."""
    return FAKE_EPOCH + pd.to_timedelta(np.asarray(t, dtype="int64"), unit="s")


def glucose_range(v):
    """Bin glucose (mg/dL) into <54, 54-69, 70-180, 181-250, >250 (same bins as RESULTS.md)."""
    return pd.cut(pd.Series(np.asarray(v, dtype=float)), RANGE_EDGES, labels=RANGE_LABELS, right=False)


def add_time_columns(df, t_col="t"):
    """Add dt (fake datetime), hour (0-24, fraction) and is_night (00:00-06:00) from a seconds column."""
    tod = np.asarray(df[t_col], dtype="int64") % 86400
    df["dt"] = fake_datetime(df[t_col])
    df["hour"] = (tod / 3600).astype("float32")
    df["is_night"] = (df["hour"] >= NIGHT_START_H) & (df["hour"] < NIGHT_END_H)
    return df


def _in_window(day):
    return (np.asarray(day) >= WINDOW_FIRST_DAY) & (np.asarray(day) <= WINDOW_LAST_DAY)


# ---------------------------------------------------------------------------
# Cache machinery: parquet files + manifest.json with a version stamp
# ---------------------------------------------------------------------------
def _manifest_path(cache_dir):
    return os.path.join(cache_dir, "manifest.json")


def read_manifest(cache_dir=DEFAULT_CACHE):
    """Return the cache manifest (version, build info, data-flow counts) or {} if there is none."""
    p = _manifest_path(cache_dir)
    if not os.path.isfile(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _write_manifest(cache_dir, m):
    os.makedirs(cache_dir, exist_ok=True)
    with open(_manifest_path(cache_dir), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, default=_json_default)


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    return str(o)


def _cache_valid(cache_dir, names):
    m = read_manifest(cache_dir)
    if m.get("version") != CACHE_VERSION:
        return False
    return all(n in m.get("tables", {}) and os.path.isfile(os.path.join(cache_dir, n + ".parquet")) for n in names)


_FRESH = set()      # (cache_dir, group) pairs already rebuilt in this process; stops nested rebuild=True calls rebuilding twice


def _load_or_build(root, cache_dir, rebuild, group, names, builder):
    """Return {name: DataFrame} for the tables in `names`.

    Reads them from the cache when the manifest version matches and the files
    exist. Otherwise calls builder(root, cache_dir, rebuild) -> (tables, info),
    writes each table to <cache_dir>/<name>.parquet and records info in the manifest.
    """
    key = (os.path.abspath(cache_dir), group)
    if rebuild and key in _FRESH:
        rebuild = False
    if not rebuild and _cache_valid(cache_dir, names):
        t0 = time.time()
        out = {n: pd.read_parquet(os.path.join(cache_dir, n + ".parquet")) for n in names}
        _log(f"loaded {', '.join(names)} from cache in {time.time() - t0:.1f}s")
        return out
    t0 = time.time()
    tables, info = builder(root, cache_dir, rebuild)
    os.makedirs(cache_dir, exist_ok=True)
    for n in names:
        tables[n].to_parquet(os.path.join(cache_dir, n + ".parquet"), index=False)
    m = read_manifest(cache_dir)
    if m.get("version") != CACHE_VERSION:
        m = {"version": CACHE_VERSION, "tables": {}, "info": {}}
    m["root"] = os.path.abspath(root)
    for n in names:
        m["tables"][n] = {"rows": int(len(tables[n])), "columns": list(map(str, tables[n].columns)),
                          "built": time.strftime("%Y-%m-%d %H:%M:%S"), "build_s": round(time.time() - t0, 1)}
    m["info"][group] = info
    _write_manifest(cache_dir, m)
    _FRESH.add(key)
    _log(f"built and cached {', '.join(names)} in {time.time() - t0:.1f}s")
    return {n: tables[n] for n in names}


# ---------------------------------------------------------------------------
# CGM
# ---------------------------------------------------------------------------
def _read_cgm_file(root):
    """Read HDeviceCGM.txt (837 MB) with small dtypes. Returns CGM rows and calibration rows."""
    _log("reading HDeviceCGM.txt (837 MB) ...")
    df = pd.read_csv(
        os.path.join(rb_dir(root), "HDeviceCGM.txt"), sep="|",
        usecols=["RecID", "ParentHDeviceUploadsID", "PtID", "DeviceDtTmDaysFromEnroll", "DeviceTm", "RecordType", "GlucoseValue"],
        dtype={"RecID": "int64", "ParentHDeviceUploadsID": "int32", "PtID": "int32", "DeviceDtTmDaysFromEnroll": "int32",
               "RecordType": "category", "GlucoseValue": "float32"},
    )
    n_file = len(df)
    df["t"] = seconds_from_enrol(df.DeviceDtTmDaysFromEnroll, df.DeviceTm)
    df = df.drop(columns="DeviceTm").rename(columns={"DeviceDtTmDaysFromEnroll": "day", "ParentHDeviceUploadsID": "upload_id", "GlucoseValue": "glucose"})
    types = df.RecordType.value_counts().to_dict()
    cgm = df[df.RecordType == "CGM"].drop(columns="RecordType")
    cal = df[df.RecordType == "Calibration"].drop(columns="RecordType")
    _log(f"rows in file {n_file:,}: {types}")
    return cgm, cal, {"rows_in_file": int(n_file), "record_types": {str(k): int(v) for k, v in types.items()}}


def _build_cgm(root, cache_dir, rebuild):
    """Build the CGM table (all CGM rows, flagged) and the calibration table from HDeviceCGM.txt."""
    cgm, cal, info = _read_cgm_file(root)
    # sort by person, time, then RecID so that the kept duplicate is always the lowest RecID
    cgm = cgm.sort_values(["PtID", "t", "RecID"], kind="stable").reset_index(drop=True)
    cgm["is_duplicate"] = cgm.duplicated(["PtID", "t"], keep="first")
    cgm["in_study_window"] = _in_window(cgm.day)
    cgm["is_clipped_low"] = cgm.glucose <= CGM_FLOOR
    cgm["is_clipped_high"] = cgm.glucose >= CGM_CEILING
    cgm["glucose_missing"] = cgm.glucose.isna()
    info.update({
        "cgm_rows": int(len(cgm)),
        "duplicate_rows_dropped": int(cgm.is_duplicate.sum()),
        "duplicate_rows_pre_enrolment": int((cgm.is_duplicate & (cgm.day < 0)).sum()),
        "rows_before_day_0": int((cgm.day < 0).sum()),
        "rows_after_day_329": int((cgm.day > WINDOW_LAST_DAY).sum()),
        "rows_in_window_before_dedup": int(cgm.in_study_window.sum()),
        "duplicate_rows_in_window": int((cgm.is_duplicate & cgm.in_study_window).sum()),
        "rows_in_window_after_dedup": int((cgm.in_study_window & ~cgm.is_duplicate).sum()),
        "rows_clipped_at_39": int(cgm.is_clipped_low.sum()),
        "rows_clipped_at_401": int(cgm.is_clipped_high.sum()),
        "rows_glucose_missing": int(cgm.glucose_missing.sum()),
        "participants": int(cgm.PtID.nunique()),
    })
    # --- sensor sessions: a new session starts after a gap of >= SESSION_GAP_S (duplicates have gap 0, so they never start one)
    gap = cgm.groupby("PtID").t.diff()
    cgm["gap_s"] = gap.astype("float32")
    new_session = gap.isna() | (gap >= SESSION_GAP_S)
    cgm["session_id"] = new_session.cumsum().astype("int32")
    first_t = cgm.groupby("session_id").t.transform("min")
    last_t = cgm.groupby("session_id").t.transform("max")
    cgm["wear_day"] = ((cgm.t - first_t) // 86400 + 1).astype("int16")
    cgm["session_days"] = ((last_t - first_t) / 86400).astype("float32")
    # a session start is "confirmed" when a calibration was entered in the 30 min before its first reading
    starts = cgm.loc[new_session, ["session_id", "PtID", "t"]].sort_values("t")
    cal_sorted = cal[["PtID", "t"]].rename(columns={"t": "t_cal"}).sort_values("t_cal")
    m = pd.merge_asof(starts, cal_sorted, left_on="t", right_on="t_cal", by="PtID", direction="backward", tolerance=STARTUP_CAL_WINDOW_S)
    confirmed = set(m.loc[m.t_cal.notna(), "session_id"])
    cgm["session_confirmed_by_cal"] = cgm.session_id.isin(confirmed)
    # --- rate of change: central difference, only when both neighbours are 4-6 min away (same person, not a duplicate)
    u = cgm[~cgm.is_duplicate]
    t_prev, t_next = u.groupby("PtID").t.shift(1), u.groupby("PtID").t.shift(-1)
    g_prev, g_next = u.groupby("PtID").glucose.shift(1), u.groupby("PtID").glucose.shift(-1)
    ok = ((u.t - t_prev).between(ROC_GAP_MIN_S, ROC_GAP_MAX_S)) & ((t_next - u.t).between(ROC_GAP_MIN_S, ROC_GAP_MAX_S))
    roc = ((g_next - g_prev) / ((t_next - t_prev) / 60)).where(ok)
    cgm["rate_of_change"] = np.float32(np.nan)
    cgm.loc[u.index, "rate_of_change"] = roc.astype("float32")
    cgm = add_time_columns(cgm)
    cgm["days_since_enrolment"] = cgm.day.astype("int16")
    cgm["day"] = cgm.day.astype("int16")
    cgm["PtID"] = cgm.PtID.astype("int16")
    cgm["upload_id"] = cgm.upload_id.astype("int32")
    cgm["RecID"] = cgm.RecID.astype("int32")
    # session validation numbers (in-window, deduplicated)
    ses = cgm[cgm.in_study_window & ~cgm.is_duplicate].groupby("session_id").agg(days=("session_days", "first"), confirmed=("session_confirmed_by_cal", "first"))
    hist = pd.cut(ses.days, [0, 0.5, 1, 2, 3, 4, 5, 6, 6.5, 6.9, 7.1, 7.5, 10, 14, 400]).value_counts().sort_index()
    info["sessions"] = {
        "rule": f"new session when the gap to the previous reading is >= {SESSION_GAP_S} s ({SESSION_GAP_S / 60:.0f} min)",
        "n_sessions_in_window": int(len(ses)),
        "share_6.5_to_7.1_days": round(float(ses.days.between(6.5, 7.1).mean()), 4),
        "share_over_7.5_days": round(float((ses.days > 7.5).mean()), 4),
        "share_under_1_day": round(float((ses.days < 1).mean()), 4),
        "median_days": round(float(ses.days.median()), 2),
        "share_confirmed_by_startup_calibration": round(float(ses.confirmed.mean()), 4),
        "share_confirmed_among_6.5_to_7.1_day_sessions": round(float(ses[ses.days.between(6.5, 7.1)].confirmed.mean()), 4),
        "share_confirmed_among_under_1_day_sessions": round(float(ses[ses.days < 1].confirmed.mean()), 4),
        "length_histogram_days": {str(k): int(v) for k, v in hist.items()},
        "rows_with_rate_of_change": int(cgm.rate_of_change.notna().sum()),
    }
    cols = ["PtID", "RecID", "upload_id", "t", "dt", "day", "days_since_enrolment", "hour", "is_night", "glucose", "glucose_missing",
            "is_clipped_low", "is_clipped_high", "is_duplicate", "in_study_window", "gap_s", "session_id", "wear_day", "session_days",
            "session_confirmed_by_cal", "rate_of_change"]
    cgm = cgm[cols]
    cal = _finish_calibrations(cal, cgm, root)
    return {"cgm": cgm, "calibrations": cal}, info


def load_cgm(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False, drop_duplicates=True):
    """CGM readings (not calibrations), one row per reading, all days (use `in_study_window` to filter).

    Columns: PtID, RecID, upload_id, t (seconds from enrolment midnight), dt (fake datetime,
    day 0 = 2000-01-01), day = days_since_enrolment, hour, is_night, glucose (mg/dL),
    glucose_missing, is_clipped_low (39), is_clipped_high (401), is_duplicate,
    in_study_window (day 0..329), gap_s (seconds since the previous reading of the same
    person), session_id, wear_day (1 = first day of the sensor session), session_days,
    session_confirmed_by_cal, rate_of_change (mg/dL per min, NaN at gaps).
    drop_duplicates=True (default) removes the 1,356 repeated person+timestamp rows.
    """
    df = _load_or_build(root, cache_dir, rebuild, "cgm", ["cgm", "calibrations"], _build_cgm)["cgm"]
    if drop_duplicates:
        df = df[~df.is_duplicate].reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Calibrations
# ---------------------------------------------------------------------------
def _finish_calibrations(cal, cgm, root):
    """Tidy the calibration rows (fingerstick values typed into the receiver). Called inside the CGM build."""
    cal = cal.sort_values(["PtID", "t", "RecID"], kind="stable").reset_index(drop=True)
    cal = cal.rename(columns={"glucose": "value"})
    cal["in_study_window"] = _in_window(cal.day)
    cal["value_missing"] = cal.value.isna()
    cal["value_out_of_range"] = (cal.value < REF_MIN) | (cal.value >= REF_MAX)
    cal["minutes_since_prev_cal"] = (cal.groupby("PtID").t.diff() / 60).astype("float32")
    cal["is_startup_pair"] = cal.minutes_since_prev_cal <= 15     # G4 asks for 2 calibrations after the 2-hour warm-up
    cal = add_time_columns(cal)
    cal["PtID"] = cal.PtID.astype("int16")
    cal["day"] = cal.day.astype("int16")
    cal["RecID"] = cal.RecID.astype("int32")
    cal["upload_id"] = cal.upload_id.astype("int32")
    return cal[["PtID", "RecID", "upload_id", "t", "dt", "day", "hour", "is_night", "value", "value_missing", "value_out_of_range",
                "in_study_window", "minutes_since_prev_cal", "is_startup_pair"]]


def load_calibrations(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """Calibration entries: PtID, t, dt, day, value (mg/dL), value_out_of_range (<20 or >=600),
    in_study_window, minutes_since_prev_cal, is_startup_pair (another calibration within 15 min before)."""
    return _load_or_build(root, cache_dir, rebuild, "cgm", ["cgm", "calibrations"], _build_cgm)["calibrations"]


# ---------------------------------------------------------------------------
# BGM (meter readings)
# ---------------------------------------------------------------------------
def _uploads_lookup(root):
    """upload_id -> device manufacturer / model / type / data source (from HDeviceUploads.txt)."""
    up = _read_table(root, "HDeviceUploads.txt")[["RecID", "DeviceManufact", "DeviceModel", "DeviceType", "DataSource"]]
    return up.rename(columns={"RecID": "upload_id", "DeviceManufact": "device_manufacturer", "DeviceModel": "device_model",
                              "DeviceType": "device_type", "DataSource": "data_source"})


def _build_bgm(root, cache_dir, rebuild):
    """Build the meter table from HDeviceBGM.txt (ketone rows excluded)."""
    _log("reading HDeviceBGM.txt ...")
    df = _read_table(root, "HDeviceBGM.txt", usecols=["RecID", "ParentHDeviceUploadsID", "PtID", "DeviceDtTmDaysFromEnroll", "DeviceTm",
                                                       "RecordType", "RecordSubType", "GlucoseValue"])
    info = {"rows_in_file": int(len(df)), "record_types": df.RecordType.value_counts().to_dict()}
    df = df[df.RecordType == "BGM"].drop(columns="RecordType")
    df["t"] = seconds_from_enrol(df.DeviceDtTmDaysFromEnroll, df.DeviceTm)
    df = df.drop(columns="DeviceTm").rename(columns={"DeviceDtTmDaysFromEnroll": "day", "ParentHDeviceUploadsID": "upload_id",
                                                     "GlucoseValue": "value", "RecordSubType": "subtype"})
    df = df.merge(_uploads_lookup(root), on="upload_id", how="left")
    df["source"] = np.where(df.device_type == "bgm", "meter", "pump")      # pump rows = BG values typed into / sent to the pump
    df["subtype"] = df.subtype.fillna("(blank)")
    df["in_study_window"] = _in_window(df.day)
    df["value_below_20"] = df.value < REF_MIN
    df["value_ge_600"] = df.value >= REF_MAX                                # meter "HI" code
    df["value_out_of_range"] = df.value_below_20 | df.value_ge_600
    df["probable_mmol_entry"] = df.value < REF_MIN                          # guess: 2, 3, 8, 9 ... look like mmol/L values
    df = df.sort_values(["PtID", "t", "RecID"], kind="stable").reset_index(drop=True)
    df["is_duplicate"] = df.duplicated(["PtID", "t", "value"], keep="first")   # exact repeat (same person, time, value)
    # a meter reading was "used for calibration" if a calibration with the SAME value exists within +-5 min
    cal = load_calibrations(root, cache_dir, rebuild)[["PtID", "t", "value"]].rename(columns={"t": "t_cal"})
    cal = cal.dropna(subset=["value"]).astype({"PtID": "int64", "value": "float64"}).sort_values("t_cal")
    left = df[["PtID", "t", "value"]].astype({"PtID": "int64", "value": "float64"}).sort_values("t")
    m = pd.merge_asof(left, cal, left_on="t", right_on="t_cal", by=["PtID", "value"], direction="nearest", tolerance=USED_FOR_CAL_TOL_S)
    df["used_for_calibration"] = pd.Series(m.t_cal.notna().to_numpy(), index=left.index).reindex(df.index).to_numpy()
    # a pump BG entry is a "copy" of a meter reading if a meter row with the same value exists within +-5 min
    meter = df[df.source == "meter"][["PtID", "t", "value"]].astype({"PtID": "int64", "value": "float64"}).rename(columns={"t": "t_m"}).sort_values("t_m")
    pump = df[df.source == "pump"][["PtID", "t", "value"]].astype({"PtID": "int64", "value": "float64"}).sort_values("t")
    m = pd.merge_asof(pump, meter, left_on="t", right_on="t_m", by=["PtID", "value"], direction="nearest", tolerance=PUMP_COPY_TOL_S)
    df["pump_copy_of_meter"] = False
    df.loc[pump.index, "pump_copy_of_meter"] = m.t_m.notna().to_numpy()
    # headline reference rule (module docstring): from the meter's own log, and not a calibration fingerstick
    df["from_meter_log"] = (df.source == "meter").to_numpy()
    df["is_verified_fingerstick"] = df.from_meter_log & ~df.used_for_calibration
    df = add_time_columns(df)
    for c in ["subtype", "source", "device_manufacturer", "device_model", "device_type", "data_source"]:
        df[c] = df[c].astype("category")
    df["PtID"] = df.PtID.astype("int16")
    df["day"] = df.day.astype("int16")
    df["value"] = df.value.astype("float32")
    info.update({
        "bgm_rows": int(len(df)), "ketone_rows_excluded": int(info["record_types"].get("Ketone", 0)),
        "rows_by_source": df.source.value_counts().to_dict(), "rows_by_subtype": df.subtype.value_counts().to_dict(),
        "rows_before_day_0": int((df.day < 0).sum()), "rows_after_day_329": int((df.day > WINDOW_LAST_DAY).sum()),
        "rows_value_below_20": int(df.value_below_20.sum()), "rows_value_ge_600": int(df.value_ge_600.sum()),
        "rows_exact_duplicates": int(df.is_duplicate.sum()),
        "rows_used_for_calibration": int(df.used_for_calibration.sum()),
        "pump_rows_copying_a_meter_reading": int(df.pump_copy_of_meter.sum()),
        "rows_from_meter_log": int(df.from_meter_log.sum()),
        "rows_verified_fingerstick": int(df.is_verified_fingerstick.sum()),
        "rows_in_window_in_range": int((df.in_study_window & ~df.value_out_of_range).sum()),
        "rows_in_window_in_range_from_meter_log": int((df.in_study_window & ~df.value_out_of_range & df.from_meter_log).sum()),
        "rows_in_window_in_range_verified_fingerstick": int((df.in_study_window & ~df.value_out_of_range & df.is_verified_fingerstick).sum()),
    })
    cols = ["PtID", "RecID", "upload_id", "t", "dt", "day", "hour", "is_night", "value", "source", "subtype", "device_manufacturer",
            "device_model", "data_source", "in_study_window", "value_below_20", "value_ge_600", "value_out_of_range", "probable_mmol_entry",
            "is_duplicate", "used_for_calibration", "pump_copy_of_meter", "from_meter_log", "is_verified_fingerstick"]
    return {"bgm": df[cols]}, info


def load_bgm(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """Meter (fingerstick) readings, ketone rows excluded, all days and all values kept but flagged.

    Columns: PtID, t, dt, day, hour, is_night, value (mg/dL), source ('meter' = a glucose meter,
    'pump' = a BG value stored by the insulin pump), subtype (manual / linked / blank), device_model,
    in_study_window, value_below_20, value_ge_600, value_out_of_range, probable_mmol_entry,
    is_duplicate, used_for_calibration (same value as a calibration within 5 min), pump_copy_of_meter,
    from_meter_log (source == 'meter'), is_verified_fingerstick (from_meter_log and not used_for_calibration;
    the headline reference rule, see the module docstring).
    """
    return _load_or_build(root, cache_dir, rebuild, "bgm", ["bgm"], _build_bgm)["bgm"]


# ---------------------------------------------------------------------------
# Pump tables: bolus, basal, bolus wizard
# ---------------------------------------------------------------------------
def _pump_common(df, root, id_col="PtID"):
    """Shared tidy-up for the three pump tables: time, window flag, device info."""
    df = df.rename(columns={id_col: "PtID", "ParentHDeviceUploadsID": "upload_id", "DeviceDtTmDaysFromEnroll": "day"})
    df["t"] = seconds_from_enrol(df.day, df.DeviceTm)
    df = df.drop(columns="DeviceTm")
    df = df.merge(_uploads_lookup(root).drop(columns="device_type"), on="upload_id", how="left")
    df["in_study_window"] = _in_window(df.day)
    df = df.sort_values(["PtID", "t", "RecID"], kind="stable").reset_index(drop=True)
    df = add_time_columns(df)
    df["PtID"] = df.PtID.astype("int16")
    df["day"] = df.day.astype("int16")
    for c in ["device_manufacturer", "device_model", "data_source"]:
        df[c] = df[c].astype("category")
    return df


def _build_pump(root, cache_dir, rebuild):
    """Build the bolus, basal and wizard tables."""
    info = {}
    _log("reading HDeviceBolus.txt ...")
    bo = _pump_common(_read_table(root, "HDeviceBolus.txt"), root)
    bo["bolus_type"] = bo.BolusType.str.lower().replace({"combination": "dual/square"}).astype("category")   # Diasend names -> Tidepool names
    is_diasend = bo.data_source == "Diasend"
    bo["duration_min"] = np.where(is_diasend, bo.Duration, bo.Duration / 60000).astype("float32")           # Diasend = minutes, Tidepool = ms
    bo["expected_duration_min"] = np.where(is_diasend, bo.ExpectedDuration, bo.ExpectedDuration / 60000).astype("float32")
    bo = bo.rename(columns={"Normal": "normal_u", "ExpectedNormal": "expected_normal_u", "Extended": "extended_u", "ExpectedExtended": "expected_extended_u"})
    bo["total_u"] = bo.normal_u.fillna(0) + bo.extended_u.fillna(0)
    bo["interrupted"] = bo.expected_normal_u.notna() | bo.expected_extended_u.notna()   # pump reported an expected amount, i.e. the bolus was cut short
    bolus = bo[["PtID", "RecID", "upload_id", "t", "dt", "day", "hour", "is_night", "in_study_window", "bolus_type", "normal_u", "extended_u",
                "total_u", "expected_normal_u", "expected_extended_u", "duration_min", "expected_duration_min", "interrupted", "device_model", "data_source"]]
    info["bolus"] = {"rows": int(len(bolus)), "participants": int(bolus.PtID.nunique()), "rows_in_window": int(bolus.in_study_window.sum()),
                     "bolus_types": bolus.bolus_type.value_counts().to_dict(), "diasend_rows": int(is_diasend.sum())}

    _log("reading HDeviceBasal.txt ...")
    ba = _pump_common(_read_table(root, "HDeviceBasal.txt"), root)
    ba = ba.rename(columns={"BasalType": "basal_type", "Rate": "rate_u_per_h", "Percnt": "percent_of_scheduled", "SuprBasalType": "suppressed_type", "SuprRate": "suppressed_rate_u_per_h"})
    ba["duration_min"] = (ba.Duration / 60000).astype("float32")
    ba["expected_duration_min"] = (ba.ExpectedDuration / 60000).astype("float32")
    ba["suppressed_duration_min"] = (ba.SuprDuration / 60000).astype("float32")
    ba["duration_suspect"] = (ba.Duration < 0) | (ba.Duration > 86400000)        # negative, or longer than one day
    for c in ["basal_type", "suppressed_type"]:
        ba[c] = ba[c].astype("category")
    basal = ba[["PtID", "RecID", "upload_id", "t", "dt", "day", "hour", "is_night", "in_study_window", "basal_type", "rate_u_per_h", "duration_min",
                "expected_duration_min", "percent_of_scheduled", "suppressed_type", "suppressed_rate_u_per_h", "suppressed_duration_min", "duration_suspect",
                "device_model", "data_source"]]
    info["basal"] = {"rows": int(len(basal)), "participants": int(basal.PtID.nunique()), "rows_in_window": int(basal.in_study_window.sum()),
                     "basal_types": basal.basal_type.value_counts().to_dict(), "rows_duration_suspect": int(basal.duration_suspect.sum())}

    _log("reading HDeviceWizard.txt ...")
    wz = _pump_common(_read_table(root, "HDeviceWizard.txt"), root, id_col="PtId")
    # Tidepool stores every glucose field in mmol/L (the ReadMe says mg/dL, the data say otherwise: max 33.3 = 600 mg/dL)
    bg = wz.BgInput.where(wz.BgInput > 0)                                    # 0 = no BG entered -> NaN
    wz["bg_input_mgdl"] = (bg * MMOL_TO_MGDL).round().astype("float32")
    wz["bg_input_entered"] = wz.BgInput > 0
    wz["isf_mgdl_per_u"] = (wz.InsulinSensitivity * MMOL_TO_MGDL).round(1).astype("float32")
    wz["target_low_mgdl"] = (wz.BgTargetLow * MMOL_TO_MGDL).round().astype("float32")
    wz["target_high_mgdl"] = (wz.BgTargetHigh * MMOL_TO_MGDL).round().astype("float32")
    wz["target_mgdl"] = (wz.BgTargetTarget * MMOL_TO_MGDL).round().astype("float32")
    wz = wz.rename(columns={"CarbInput": "carb_input_g", "InsulinCarbRatio": "icr_g_per_u", "InsulinOnBoard": "iob_u", "RecommendedCarb": "rec_carb_u",
                            "RecommendedCorrection": "rec_correction_u", "RecommendedNet": "rec_net_u", "ParentHDeviceBolusID": "bolus_rec_id"})
    delivered = bolus[["RecID", "total_u", "normal_u", "extended_u"]].rename(columns={"RecID": "bolus_rec_id", "total_u": "delivered_u", "normal_u": "delivered_normal_u", "extended_u": "delivered_extended_u"})
    wz = wz.merge(delivered, on="bolus_rec_id", how="left")
    wizard = wz[["PtID", "RecID", "upload_id", "t", "dt", "day", "hour", "is_night", "in_study_window", "bg_input_mgdl", "bg_input_entered", "carb_input_g",
                 "icr_g_per_u", "isf_mgdl_per_u", "target_low_mgdl", "target_high_mgdl", "target_mgdl", "iob_u", "rec_carb_u", "rec_correction_u", "rec_net_u",
                 "bolus_rec_id", "delivered_u", "delivered_normal_u", "delivered_extended_u", "device_model", "data_source"]]
    info["wizard"] = {"rows": int(len(wizard)), "participants": int(wizard.PtID.nunique()), "rows_in_window": int(wizard.in_study_window.sum()),
                      "rows_with_bg_input": int(wizard.bg_input_entered.sum()), "rows_linked_to_a_bolus": int(wizard.delivered_u.notna().sum()),
                      "bg_input_mgdl_median": float(wizard.bg_input_mgdl.median())}
    return {"pump_bolus": bolus, "pump_basal": basal, "pump_wizard": wizard}, info


def load_pump(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """Insulin pump logs as a dict with keys 'bolus', 'basal', 'wizard'.

    bolus: bolus_type, normal_u, extended_u, total_u, duration_min, interrupted.
    basal: basal_type (scheduled / temp / suspend), rate_u_per_h, duration_min, duration_suspect.
    wizard (the pump's dose calculator): bg_input_mgdl, carb_input_g, icr_g_per_u, isf_mgdl_per_u,
      target_low/high_mgdl, iob_u, rec_carb_u, rec_correction_u, rec_net_u, delivered_u (from the linked bolus).
    All glucose fields converted from mmol/L (Tidepool) to mg/dL. All tables have t, dt, day, in_study_window.
    """
    t = _load_or_build(root, cache_dir, rebuild, "pump", ["pump_bolus", "pump_basal", "pump_wizard"], _build_pump)
    return {"bolus": t["pump_bolus"], "basal": t["pump_basal"], "wizard": t["pump_wizard"]}


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------
def _build_participants(root, cache_dir, rebuild):
    """One row per participant: demographics, history, HbA1c per visit, devices, comorbidities, CGM coverage."""
    _log("building participants table ...")
    roster = _read_table(root, "HPtRoster.txt")
    screen = _read_table(root, "HScreening.txt")
    p = roster.merge(screen.drop(columns=["RecID", "SiteID"]), on="PtID", how="left")
    out = pd.DataFrame({
        "PtID": p.PtID.astype("int16"), "site": p.SiteID.astype("int16"), "arm": p.TrtGroup, "status": p.PtStatus,
        "randomisation_day": p.RandDtDaysAfterEnroll, "age": p.AgeAsOfEnrollDt, "sex": p.Gender, "ethnicity": p.Ethnicity, "race": p.Race,
        "education": p.EduLevel, "education_not_answered": p.EduLevel.isna(), "income": p.AnnualInc, "income_not_answered": p.AnnualInc.isna(),
        "insurance_private": p.InsPrivate.notna(), "insurance_medicare": p.InsMedicare.notna(), "insurance_medicaid": p.InsMedicaid.notna(),
        "insurance_other": p[["InsMediGap", "InsSCHIP", "InsMilitary", "InsIndian", "InsState", "InsOtherGov", "InsSingleService"]].notna().any(axis=1),
        "insurance_none": p.InsNoCoverage.notna(), "insurance_not_answered": p.InsNoAns.notna(),
        "weight_kg": p.Weight, "height_cm": p.Height, "bmi": p.Weight / (p.Height / 100) ** 2,
        "diagnosis_age": p.DiagAge, "diabetes_duration_yrs": p.AgeAsOfEnrollDt - p.DiagAge,
        "cgm_use_status": p.CGMUseStatus, "cgm_use_duration": p.CGMUseDuration, "cgm_use_device": p.CGMUseDevice,
        "severe_hypo_most_recent": p.SHMostRec, "dka_most_recent": p.DKAMostRec, "other_glucose_lowering_med": p.OthGlucLowerMed == "Yes",
        "fingersticks_per_day": p.Fingerstick7DayAve,
    })
    fin = _read_table(root, "HPostRandPtFinalStatus.txt").drop_duplicates("PtID")
    out = out.merge(fin[["PtID", "HPostRandFinalStatReas", "PtWithdrawReas"]].rename(columns={"HPostRandFinalStatReas": "final_status_reason", "PtWithdrawReas": "withdraw_reason"}), on="PtID", how="left")
    ini = _read_table(root, "HInitialStudyCGM.txt").drop_duplicates("PtID")
    out = out.merge(ini[["PtID", "CGMTypeProvided"]].rename(columns={"CGMTypeProvided": "initial_study_cgm"}), on="PtID", how="left")
    ins = _read_table(root, "HInsulin.txt")
    out["pump_user"] = out.PtID.isin(ins[ins.InsRoute == "Pump"].PtID)
    out = out.merge(ins.groupby("PtID").InsName.apply(lambda s: "; ".join(sorted(set(s.dropna())))).rename("insulin_names"), on="PtID", how="left")
    fu = _read_table(root, "HFollowUp.txt").rename(columns={"PtId": "PtID"})
    out = out.merge(fu.groupby("PtID").PumpStopDtDaysFromEnroll.min().rename("pump_stop_day"), on="PtID", how="left")
    # HbA1c: local (point of care / local lab) per visit, and central lab (Sample.txt)
    hb = _read_table(root, "HLocalHbA1c.txt")
    vis = {"Screening Visit": "hba1c_screening", "Randomization": "hba1c_randomisation", "Week 13 Visit": "hba1c_week13", "Week 26 Visit": "hba1c_week26"}
    w = hb.pivot_table(index="PtID", columns="Visit", values="HbA1cTestRes", aggfunc="first").rename(columns=vis)
    out = out.merge(w[[c for c in vis.values() if c in w]], on="PtID", how="left")
    smp = _read_table(root, "Sample.txt")
    smp = smp[smp.Analyte == "HBA1C"]
    vis2 = {"Randomization": "lab_hba1c_randomisation", "Week 13 Visit": "lab_hba1c_week13", "Week 26 Visit": "lab_hba1c_week26"}
    w2 = smp.pivot_table(index="PtID", columns="Visit", values="Value", aggfunc="first").rename(columns=vis2)
    out = out.merge(w2[[c for c in vis2.values() if c in w2]], on="PtID", how="left")
    # devices
    up = _read_table(root, "HDeviceUploads.txt").rename(columns={"PtId": "PtID"}).drop_duplicates(["PtID", "DeviceModel", "DeviceType"])
    def models(mask, name):
        return up[mask].groupby("PtID").DeviceModel.apply(lambda s: "; ".join(sorted(set(s.dropna())))).rename(name)
    out = out.merge(models(up.DeviceType == "cgm", "cgm_models"), on="PtID", how="left")
    out = out.merge(models(up.DeviceType.str.contains("bgm"), "bgm_models"), on="PtID", how="left")
    out = out.merge(models(up.DeviceType.str.contains("pump"), "pump_models"), on="PtID", how="left")
    # comorbidities (HMedicalCondition): count and a few common flags
    mc = _read_table(root, "HMedicalCondition.txt").rename(columns={"PtId": "PtID"})
    mc = mc[mc.MedCond != "Type I diabetes mellitus"]
    out = out.merge(mc.groupby("PtID").size().rename("n_comorbidities"), on="PtID", how="left")
    out["n_comorbidities"] = out.n_comorbidities.fillna(0).astype("int16")
    low = mc.MedCond.str.lower()
    for name, pat in [("comorb_hyperlipidemia", "hyperlipidemia|hypercholest"), ("comorb_hypertension", "hypertension"), ("comorb_hypothyroidism", "hypothyroid"),
                      ("comorb_depression", "depression"), ("comorb_retinopathy", "retinopathy"), ("comorb_obesity", "obesity")]:
        out[name] = out.PtID.isin(mc[low.str.contains(pat, regex=True)].PtID)
    # CGM coverage inside the study window (deduplicated)
    cgm = load_cgm(root, cache_dir, rebuild)
    cw = cgm[cgm.in_study_window]
    cov = cw.groupby("PtID").agg(cgm_readings_in_window=("glucose", "size"), cgm_days_in_window=("day", "nunique"),
                                 cgm_first_day=("day", "min"), cgm_last_day=("day", "max"), cgm_sessions_in_window=("session_id", "nunique"))
    cov["cgm_readings_per_day"] = (cov.cgm_readings_in_window / cov.cgm_days_in_window).round(1)
    out = out.merge(cov, on="PtID", how="left")
    for c in ["arm", "status", "sex", "ethnicity", "race", "education", "income", "cgm_use_status", "cgm_use_duration", "cgm_use_device",
              "severe_hypo_most_recent", "dka_most_recent", "final_status_reason", "withdraw_reason", "initial_study_cgm"]:
        out[c] = out[c].astype("category")
    info = {"participants": int(len(out)), "sites": int(out.site.nunique()), "arms": out.arm.value_counts().to_dict(), "status": out.status.value_counts().to_dict(),
            "hba1c_local_missing": int(hb.HbA1cTestRes.isna().sum()), "lab_hba1c_rows": int(len(smp))}
    return {"participants": out.sort_values("PtID").reset_index(drop=True)}, info


def load_participants(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """One row per REPLACE-BG participant (226 rows).

    Demographics (age, sex, race, ethnicity, education, income, insurance_*), body size (bmi),
    diabetes history (diagnosis_age, diabetes_duration_yrs, severe_hypo_most_recent, dka_most_recent),
    prior CGM use (cgm_use_*), fingersticks_per_day at screening, arm, site, status and
    final_status_reason, pump_user / pump_models / insulin_names, HbA1c per visit (hba1c_* local,
    lab_hba1c_* central lab), device models, comorbidity count and flags, CGM coverage in the window.
    """
    return _load_or_build(root, cache_dir, rebuild, "participants", ["participants"], _build_participants)["participants"]


# ---------------------------------------------------------------------------
# Shanghai T1DM / T2DM
# ---------------------------------------------------------------------------
SH_MISSING_TOKENS = {"/", "", "nan", "NaN", "none", "None", "NA"}
SH_NUMERIC_COLS = ["Gender (Female=1, Male=2)", "Age (years)", "Height (m)", "Weight (kg)", "BMI (kg/m2)", "Smoking History (pack year)",
                   "Duration of Diabetes (years)", "Fasting Plasma Glucose (mg/dl)", "2-hour Postprandial Plasma Glucose (mg/dl)",
                   "Fasting C-peptide (nmol/L)", "2-hour Postprandial C-peptide (nmol/L)", "Fasting Insulin (pmol/L)", "2-hour Postprandial Insulin (pmol/L)",
                   "HbA1c (mmol/mol)", "Glycated Albumin (%)", "Total Cholesterol (mmol/L)", "Triglyceride (mmol/L)",
                   "High-Density Lipoprotein Cholesterol (mmol/L)", "Low-Density Lipoprotein Cholesterol (mmol/L)", "Creatinine (umol/L)",
                   "Estimated Glomerular Filtration Rate (ml/min/1.73m2)", "Uric Acid (mmol/L)", "Blood Urea Nitrogen (mmol/L)"]
SH_STANDARD_COLS = {"Date", "CGM (mg / dl)", "CBG (mg / dl)", "Blood Ketone (mmol / L)", "Dietary intake", "饮食", "Insulin dose - s.c.",
                    "Non-insulin hypoglycemic agents", "CSII - bolus insulin (Novolin R, IU)", "CSII - basal insulin (Novolin R, IU / H)", "Insulin dose - i.v."}
# how each column of a patient file is recognised: (new name, list of accepted prefixes, lower-case)
SH_COLUMN_MAP = [("ts", ["date"]), ("cgm", ["cgm"]), ("cbg", ["cbg"]), ("ketone_mmol", ["blood ketone"]), ("diet", ["dietary intake"]),
                 ("diet_cn", ["饮食", "进食量"]), ("insulin_sc", ["insulin dose - s.c"]), ("noninsulin_agents", ["non-insulin"]),
                 ("csii_bolus_u", ["csii - bolus"]), ("csii_basal_u_per_h", ["csii - basal", "胰岛素泵基础量"]), ("insulin_iv", ["insulin dose - i.v"])]


def _sh_find(cols, prefixes):
    for c in cols:
        if any(str(c).strip().lower().startswith(p) for p in prefixes):
            return c
    return None


def _sh_patient_files(root):
    """Sorted list of (group, path) for the per-patient Excel files. Lock files (~$...) are skipped."""
    out = []
    for grp in ["Shanghai_T1DM", "Shanghai_T2DM"]:
        for f in sorted(glob.glob(os.path.join(sh_dir(root), "*", grp, "*.xls*"))):
            if not os.path.basename(f).startswith("~$"):
                out.append((grp.replace("Shanghai_", ""), f))
    return out


def _sh_summary(root, name, group):
    """One summary workbook -> tidy patient table (original column names kept, whitespace collapsed)."""
    df = pd.read_excel(glob.glob(os.path.join(sh_dir(root), "*", name))[0])
    df.columns = [" ".join(str(c).split()) for c in df.columns]
    df = df.rename(columns={"Duration of diabetes (years)": "Duration of Diabetes (years)", "2-hour Postprandial insulin (pmol/L)": "2-hour Postprandial Insulin (pmol/L)"})
    for c in df.columns:
        if c in SH_NUMERIC_COLS:
            s = df[c].mask(df[c].astype(str).str.strip().isin(SH_MISSING_TOKENS))      # '/' (and blanks) -> NaN
            df[c] = pd.to_numeric(s, errors="coerce").astype("float64")
        else:
            df[c] = df[c].astype(str).str.strip()
    parts = df["Patient Number"].str.split("_", expand=True)
    df.insert(0, "group", group)
    df.insert(1, "pid", parts[0])
    df.insert(2, "visit", pd.to_numeric(parts[1], errors="coerce").astype("Int16"))
    df["sex"] = df["Gender (Female=1, Male=2)"].map({1: "F", 2: "M"})
    df["hba1c_pct"] = df["HbA1c (mmol/mol)"] / 10.929 + 2.15      # IFCC mmol/mol -> NGSP %
    df["on_insulin"] = df["Hypoglycemic Agents"].str.contains("insulin|humulin|novolin|gansulin|lantus|degludec|glargine|aspart|lispro|detemir", case=False)
    return df


def _build_shanghai(root, cache_dir, rebuild):
    """Build the Shanghai tables: patients (summary workbooks), cgm (all rows of all patient files), cbg, files."""
    _log("reading Shanghai summary workbooks ...")
    patients = pd.concat([_sh_summary(root, "Shanghai_T1DM_Summary.xlsx", "T1DM"), _sh_summary(root, "Shanghai_T2DM_Summary.xlsx", "T2DM")], ignore_index=True)
    _log("reading Shanghai patient files ...")
    frames, files = [], []
    for group, path in _sh_patient_files(root):
        raw = pd.read_excel(path)
        cols = list(raw.columns)
        odd = [str(c) for c in cols if c not in SH_STANDARD_COLS]
        df = pd.DataFrame(index=raw.index)
        for new, prefixes in SH_COLUMN_MAP:
            c = _sh_find(cols, prefixes)
            df[new] = raw[c] if c is not None else np.nan
        df["ts"] = pd.to_datetime(df.ts, errors="coerce")
        n_no_date = int(df.ts.isna().sum())
        df = df[df.ts.notna()].copy()
        for c in ["cgm", "cbg"]:                       # float64 on purpose: values are multiples of 1.8 (mmol/L * 18)
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
        for c in ["ketone_mmol", "csii_bolus_u", "csii_basal_u_per_h"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
        for c in ["diet", "diet_cn", "insulin_sc", "noninsulin_agents", "insulin_iv"]:
            df[c] = df[c].where(df[c].notna(), None).astype(object).map(lambda v: None if v is None else str(v).strip())
        unit_fix = bool(df.cgm.notna().any() and df.cgm.max() < 35)           # a file in mmol/L (none in this data)
        if unit_fix:
            df["cgm"] = df.cgm * 18.0
        if df.cbg.notna().any() and df.cbg.max() < 35:
            df["cbg"] = df.cbg * 18.0
        fname = os.path.basename(path)
        pid, visit = fname.split("_")[0], fname.split("_")[1]
        df.insert(0, "file", fname)
        df.insert(0, "pid", pid)
        df.insert(0, "group", group)
        t0 = df.ts.min()
        df["wear_day"] = ((df.ts - t0).dt.total_seconds() // 86400 + 1).astype("int16")
        df["hour"] = (df.ts.dt.hour + df.ts.dt.minute / 60).astype("float32")
        df["is_night"] = (df.hour >= NIGHT_START_H) & (df.hour < NIGHT_END_H)
        secs = (df.ts - t0).dt.total_seconds()
        t_prev, t_next, g_prev, g_next = secs.shift(1), secs.shift(-1), df.cgm.shift(1), df.cgm.shift(-1)
        ok = (secs - t_prev).between(780, 1020) & (t_next - secs).between(780, 1020)     # both neighbours 13-17 min away
        df["rate_of_change"] = ((g_next - g_prev) / ((t_next - t_prev) / 60)).where(ok).astype("float32")
        dtm = df.ts.diff().dt.total_seconds()
        files.append({"file": fname, "group": group, "pid": pid, "visit": int(visit), "extension": os.path.splitext(fname)[1],
                      "rows": int(len(raw)), "rows_no_date": n_no_date, "n_cgm": int(df.cgm.notna().sum()), "n_cbg": int(df.cbg.notna().sum()),
                      "n_cbg_lt70": int((df.cbg < 70).sum()), "n_cbg_lt54": int((df.cbg < 54).sum()),
                      "days": float((df.ts.max() - df.ts.min()).total_seconds() / 86400), "interval_min": float(dtm.median() / 60),
                      "n_gaps_over_15min": int((dtm > 900).sum()), "date_monotonic": bool(df.ts.is_monotonic_increasing),
                      "cgm_mean": float(df.cgm.mean()), "pct_lt70": float((df.cgm < 70).mean() * 100),
                      "pct_in_range": float(((df.cgm >= 70) & (df.cgm <= 180)).mean() * 100), "pct_gt180": float((df.cgm > 180).mean() * 100),
                      "nonstandard_columns": json.dumps(odd, ensure_ascii=False), "unit_converted": unit_fix})
        frames.append(df)
    cgm = pd.concat(frames, ignore_index=True)
    cgm["group"] = cgm.group.astype("category")
    cbg = cgm[cgm.cbg.notna()][["group", "pid", "file", "ts", "cbg", "cgm", "wear_day", "hour", "is_night", "rate_of_change"]].reset_index(drop=True)
    files = pd.DataFrame(files)
    info = {"files": int(len(files)), "files_by_group": files.group.value_counts().to_dict(), "patients_by_group": files.groupby("group").pid.nunique().to_dict(),
            "rows_without_date_dropped": int(files.rows_no_date.sum()), "cgm_readings": int(files.n_cgm.sum()), "cbg_readings": int(files.n_cbg.sum()),
            "files_with_nonstandard_columns": int((files.nonstandard_columns != "[]").sum()), "files_unit_converted": int(files.unit_converted.sum()),
            "files_without_cbg": int((files.n_cbg == 0).sum()), "summary_records": int(len(patients)),
            "all_cgm_values_multiples_of_1.8": bool(((cgm.cgm.dropna().astype("float64") / 1.8).round(6) % 1 == 0).all())}
    return {"shanghai_patients": patients, "shanghai_cgm": cgm, "shanghai_cbg": cbg, "shanghai_files": files}, info


def load_shanghai(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """Shanghai data as a dict: 'patients' (summary workbooks, one row per patient-visit, group / pid / visit /
    sex / hba1c_pct / on_insulin added, '/' turned into NaN in numeric columns), 'cgm' (every row of every
    patient file: ts, cgm, cbg, ketone, diet, insulin columns, wear_day, hour, is_night, rate_of_change),
    'cbg' (rows that hold a fingerstick), 'files' (one row per file with counts and layout notes).
    Nonstandard column names are mapped by prefix; lock files are skipped; rows without a date are dropped.
    """
    t = _load_or_build(root, cache_dir, rebuild, "shanghai", ["shanghai_patients", "shanghai_cgm", "shanghai_cbg", "shanghai_files"], _build_shanghai)
    pt = t["shanghai_patients"]
    for c in pt.columns:                                   # None -> NaN so text columns behave like freshly read Excel columns
        if pt[c].dtype == object:
            pt[c] = pt[c].where(pt[c].notna(), np.nan)
    return {"patients": pt, "cgm": t["shanghai_cgm"], "cbg": t["shanghai_cbg"], "files": t["shanghai_files"]}


# ---------------------------------------------------------------------------
# Pairs: CGM reading matched to a reference value
# ---------------------------------------------------------------------------
_CGM_PAIR_COLS = ["PtID", "t", "glucose", "day", "in_study_window", "is_clipped_low", "is_clipped_high", "session_id", "wear_day", "session_days",
                  "session_confirmed_by_cal", "rate_of_change"]


def _add_error_columns(p):
    """err, abs_err, rel_err_pct, abs_rel_err_pct, avg and the three range bins (ref / cgm / avg)."""
    if p.cgm.dtype != p.ref.dtype:                     # REPLACE-BG: float32 (integer mg/dL); Shanghai: float64 (multiples of 1.8)
        p["ref"] = p.ref.astype(p.cgm.dtype)
    p["err"] = p.cgm - p.ref
    p["abs_err"] = p.err.abs()
    p["rel_err_pct"] = p.err / p.ref * 100
    p["abs_rel_err_pct"] = p.rel_err_pct.abs()
    p["avg"] = (p.cgm + p.ref) / 2
    p["ref_range"] = glucose_range(p.ref).to_numpy()
    p["cgm_range"] = glucose_range(p.cgm).to_numpy()
    p["avg_range"] = glucose_range(p.avg).to_numpy()
    return p


def _pair_with_cgm(ref, cgm, direction, tolerance):
    """merge_asof of a reference table (PtID, t, ref, ...) with the CGM table; unmatched rows dropped."""
    right = cgm[_CGM_PAIR_COLS].rename(columns={"t": "t_cgm", "glucose": "cgm", "day": "day_cgm", "in_study_window": "cgm_in_window"})
    right = right.sort_values("t_cgm", kind="stable")
    ref = ref.sort_values("t", kind="stable")
    p = pd.merge_asof(ref, right, left_on="t", right_on="t_cgm", by="PtID", direction=direction, tolerance=tolerance)
    p = p.dropna(subset=["cgm"]).reset_index(drop=True)
    p["dt_s"] = (p.t - p.t_cgm).astype("int32")                     # reference time minus CGM time
    p["cgm_clipped"] = p.is_clipped_low | p.is_clipped_high
    p["in_study_window"] = _in_window(p.day)
    p["t_cgm"] = p.t_cgm.astype("int64")
    for c in ["session_id"]:
        p[c] = p[c].astype("int32")
    for c in ["wear_day"]:
        p[c] = p[c].astype("int16")
    p["is_clipped_low"] = p.is_clipped_low.astype(bool)
    p["is_clipped_high"] = p.is_clipped_high.astype(bool)
    p["session_confirmed_by_cal"] = p.session_confirmed_by_cal.astype(bool)
    p["cgm_in_window"] = p.cgm_in_window.astype(bool)
    return _add_error_columns(p)


def _build_pairs(root, cache_dir, rebuild):
    """Build the three pair tables: calibration pairs, meter pairs, Shanghai pairs."""
    cgm = load_cgm(root, cache_dir, rebuild)
    info = {}
    # 1. calibration pairs: each calibration (20 <= value < 600) with the last CGM reading up to 10 min BEFORE it
    cal = load_calibrations(root, cache_dir, rebuild)
    n_all = len(cal)
    cal = cal[~cal.value_missing & ~cal.value_out_of_range]
    ref = cal[["PtID", "t", "day", "hour", "is_night", "value", "in_study_window", "minutes_since_prev_cal", "is_startup_pair"]].rename(columns={"value": "ref"})
    pc = _pair_with_cgm(ref.drop(columns=["in_study_window"]), cgm, "backward", CAL_PAIR_TOL_S)
    pc["PtID"] = pc.PtID.astype("int16")
    info["calibration"] = {"method": f"calibration matched to the most recent CGM reading of the same person within {CAL_PAIR_TOL_S // 60} min before it",
                           "calibration_rows": int(n_all), "with_value_in_range": int(len(ref)), "pairs": int(len(pc)), "pairs_in_window": int(pc.in_study_window.sum()),
                           "participants": int(pc.PtID.nunique()), "pairs_by_ref_range": pc.ref_range.value_counts().sort_index().to_dict()}
    _log("calibration pairs:", len(pc))
    # 2. meter pairs: each meter reading (20 <= value < 600, any source) with the NEAREST CGM reading within 5 min
    bgm = load_bgm(root, cache_dir, rebuild)
    n_all = len(bgm)
    b = bgm[~bgm.value_out_of_range]
    ref = b[["PtID", "t", "day", "hour", "is_night", "value", "source", "subtype", "device_model", "used_for_calibration", "pump_copy_of_meter",
             "from_meter_log", "is_verified_fingerstick", "is_duplicate"]].rename(columns={"value": "ref", "is_duplicate": "ref_is_duplicate"})
    pm = _pair_with_cgm(ref, cgm, "nearest", METER_PAIR_TOL_S)
    pm["PtID"] = pm.PtID.astype("int16")
    for c in ["source", "subtype", "device_model"]:
        pm[c] = pm[c].astype("category")
    for c in ["from_meter_log", "is_verified_fingerstick"]:
        pm[c] = pm[c].astype(bool)
    vw = pm[pm.is_verified_fingerstick & pm.in_study_window]            # the headline set, see verified_pairs()
    info["meter"] = {"method": f"meter reading matched to the nearest CGM reading of the same person within +-{METER_PAIR_TOL_S // 60} min",
                     "meter_rows": int(n_all), "with_value_in_range": int(len(ref)), "pairs": int(len(pm)), "pairs_in_window": int(pm.in_study_window.sum()),
                     "pct_of_meter_rows_matched": round(float(len(pm) / len(ref) * 100), 2), "participants": int(pm.PtID.nunique()),
                     "pairs_used_for_calibration": int(pm.used_for_calibration.sum()), "independent_pairs": int((~pm.used_for_calibration).sum()),
                     "pairs_from_pump_rows": int((pm.source == "pump").sum()), "pairs_pump_copy_of_meter": int(pm.pump_copy_of_meter.sum()),
                     "pairs_in_window_from_meter_log": int((pm.in_study_window & pm.from_meter_log).sum()),
                     "verified_pairs_all_days": int(pm.is_verified_fingerstick.sum()),
                     "verified_pairs_in_window": int(len(vw)), "verified_participants_in_window": int(vw.PtID.nunique()),
                     "verified_in_window_mard_pct": round(float(vw.abs_rel_err_pct.mean()), 2),
                     "verified_rule": "from_meter_log (source == meter) AND NOT used_for_calibration, in the study window; the headline pair set",
                     "pairs_by_ref_range": pm.ref_range.value_counts().sort_index().to_dict()}
    _log("meter pairs:", len(pm), "of which independent of calibration:", int((~pm.used_for_calibration).sum()),
         "| verified fingerstick pairs in window:", len(vw), "from", int(vw.PtID.nunique()), "people")
    # 3. Shanghai: fingerstick (CBG) written on the same 15-min CGM row
    sh = load_shanghai(root, cache_dir, rebuild)["cgm"]
    ps = sh[sh.cbg.notna() & sh.cgm.notna()][["group", "pid", "file", "ts", "cgm", "cbg", "wear_day", "hour", "is_night", "rate_of_change"]].rename(columns={"cbg": "ref"}).reset_index(drop=True)
    ps = _add_error_columns(ps)
    info["shanghai"] = {"method": "capillary blood glucose (CBG) recorded on the same 15-min CGM row (time slack up to 7.5 min)",
                        "rows_with_cbg": int(sh.cbg.notna().sum()), "pairs": int(len(ps)), "pairs_by_group": ps.group.value_counts().to_dict(),
                        "pairs_by_ref_range": ps.ref_range.value_counts().sort_index().to_dict()}
    _log("Shanghai pairs:", len(ps))
    return {"pairs_calibration": pc, "pairs_meter": pm, "pairs_shanghai": ps}, info


def build_pairs(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """The three CGM-vs-reference pairings as a dict.

    'calibration': calibration value vs the last CGM reading up to 10 min before it (REPLACE-BG).
    'meter': meter reading vs the nearest CGM reading within 5 min (REPLACE-BG, all meter rows incl. pump BG entries).
    'independent_meter': the meter pairs whose reference was NOT used for calibration (view of 'meter';
        pump BG entries are still inside; kept so that old code runs).
    'verified': THE HEADLINE SET, same as verified_pairs(): meter pairs with is_verified_fingerstick
        (reference from the meter's own log AND not used for calibration) inside the study window.
    'shanghai': fingerstick vs the CGM value on the same 15-min row.
    Every table has cgm, ref (mg/dL), err = cgm - ref, abs_err, rel_err_pct, abs_rel_err_pct, avg,
    ref_range / cgm_range / avg_range bins, rate_of_change, wear_day, hour, is_night; REPLACE-BG tables
    also day, in_study_window, dt_s, session_id, cgm_clipped; meter pairs also source, used_for_calibration,
    pump_copy_of_meter, from_meter_log, is_verified_fingerstick.
    """
    t = _load_or_build(root, cache_dir, rebuild, "pairs", ["pairs_calibration", "pairs_meter", "pairs_shanghai"], _build_pairs)
    meter = t["pairs_meter"]
    return {"calibration": t["pairs_calibration"], "meter": meter, "independent_meter": meter[~meter.used_for_calibration].reset_index(drop=True),
            "verified": meter[meter.is_verified_fingerstick & meter.in_study_window].reset_index(drop=True),
            "shanghai": t["pairs_shanghai"]}


def verified_pairs(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """THE HEADLINE PAIR SET for the paper: verified fingerstick vs CGM pairs inside the study window.

    A meter pair is kept when its reference value
      1. comes from the meter's own log (`from_meter_log`). Pump BG entries are dropped: many of them
         are CGM values typed into the pump's bolus calculator, not fingersticks.
      2. was not used to calibrate the sensor (`used_for_calibration` is False).
      3. lies in the study window (`in_study_window`, day 0 to 329).
    Rules 1 and 2 together are the `is_verified_fingerstick` flag on the BGM table and the meter pairs.
    Expected with this data: 168,990 pairs, 226 participants, MARD 13.3 %. The counts are also in
    read_manifest()['info']['pairs']['meter'] (keys starting with 'verified_').
    Same columns as build_pairs()['meter']; identical to build_pairs()['verified'].
    """
    return build_pairs(root, cache_dir, rebuild)["verified"]


# ---------------------------------------------------------------------------
# Build everything
# ---------------------------------------------------------------------------
def build_all(root=DEFAULT_ROOT, cache_dir=DEFAULT_CACHE, rebuild=False):
    """Build (or load) every cached table. Returns the manifest dict (version, tables, data-flow counts)."""
    check_raw_data(root)
    t0 = time.time()
    load_cgm(root, cache_dir, rebuild)
    load_bgm(root, cache_dir, rebuild)
    load_pump(root, cache_dir, rebuild)
    load_participants(root, cache_dir, rebuild)
    load_shanghai(root, cache_dir, rebuild)
    build_pairs(root, cache_dir, rebuild)
    m = read_manifest(cache_dir)
    size_mb = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in os.listdir(cache_dir)) / 1e6
    m["last_build_all"] = {"seconds": round(time.time() - t0, 1), "cache_size_mb": round(size_mb, 1), "when": time.strftime("%Y-%m-%d %H:%M:%S")}
    _write_manifest(cache_dir, m)
    _log(f"all tables ready in {time.time() - t0:.1f}s; cache {size_mb:.0f} MB in {cache_dir}")
    return m


def main(argv=None):
    """Command line: python analysis/preprocess.py [data folder] [cache folder] [--rebuild]"""
    import argparse
    ap = argparse.ArgumentParser(description="Build the shared preprocessed data cache (parquet files).")
    ap.add_argument("root", nargs="?", default=DEFAULT_ROOT, help="raw data folder (default: %(default)s)")
    ap.add_argument("cache_dir", nargs="?", default=DEFAULT_CACHE, help="cache folder (default: %(default)s)")
    ap.add_argument("--rebuild", action="store_true", help="ignore any existing cache and rebuild every table")
    a = ap.parse_args(argv)
    m = build_all(a.root, a.cache_dir, a.rebuild)
    print(json.dumps({k: v for k, v in m.get("info", {}).items() if k in ("cgm", "pairs")}, indent=1, default=_json_default)[:4000])


if __name__ == "__main__":
    main()
