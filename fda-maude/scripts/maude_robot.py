"""
MAUDE robot for BMEN 600 Group 24.

What it does (plain words):
- Asks the openFDA web service (API) for FDA reports about CGM sensors.
  CGM = continuous glucose monitor. MAUDE = FDA database of device problem reports.
- Saves what it gets to files. Can stop and pick up again later.
- Counts every call it makes. Stops before the daily limit.

How to run (from the fda-maude folder):
    py -3.11 scripts/maude_robot.py status
    py -3.11 scripts/maude_robot.py counts     (tier 1: count tables, no reports)
    py -3.11 scripts/maude_robot.py recalls    (tier 4: recall records)
    py -3.11 scripts/maude_robot.py serious    (tier 2: all death + injury reports)
    py -3.11 scripts/maude_robot.py sample     (tier 3: random sample of malfunction reports)
    py -3.11 scripts/maude_robot.py full       (tier 5: every CGM report; add --workers 4)
    py -3.11 scripts/maude_robot.py clean      (one tidy table per tier)
    py -3.11 scripts/maude_robot.py tables     (rebuild results/counts/*.csv from raw/counts/, no calls)
Add --codes SBH,QCD to run only some product codes (for testing).

Settings live in scripts/config.json.
Optional: set the environment variable OPENFDA_API_KEY to use a free API key.
The key is sent in a hidden header (HTTP "basic auth"), never in the web address.
So it never ends up in query_log.jsonl or in printed messages.
"""

import argparse
import bisect
import csv
import datetime as dt
import gzip
import json
import math
import os
import random
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # the fda-maude folder
API = "https://api.fda.gov"
EVENT = "/device/event.json"
CODE_FIELD = "device.device_report_product_code"
MISSING = {"", "na", "n/a", "unknown", "unk", "none"}


# ---------------------------------------------------------------- setup

def load_config():
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    for k, v in cfg["paths"].items():
        cfg["paths"][k] = (ROOT / v).resolve()
    return cfg


def write_json_atomic(path, obj):
    """Write to a temp file, then rename. A crash never leaves half a file."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    replace_retry(tmp, path)


def replace_retry(tmp, path):
    """Rename tmp -> path. Windows refuses this while another program (e.g. 'status')
    is reading the file. So try again a few times."""
    for i in range(50):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.2)
    os.replace(tmp, path)


def read_json_retry(path):
    for i in range(20):
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except (PermissionError, ValueError):
            time.sleep(0.2)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def pid_alive(pid):
    """True if a process with this ID is still running (Windows and others)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)  # 0x1000 = ask only for basic info
        if not h:
            return False
        code = ctypes.c_ulong()
        k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return code.value == 259  # 259 = "still running"
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def write_jsonl_gz_atomic(path, records):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    replace_retry(tmp, path)


def read_jsonl_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_key_into_env():
    """The API key comes from the environment variable OPENFDA_API_KEY.
    On Windows, if a program was started without it, read the saved user setting.
    The key is kept in memory only. It is never written to a file."""
    if os.environ.get("OPENFDA_API_KEY") or os.name != "nt":
        return
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, _ = winreg.QueryValueEx(k, "OPENFDA_API_KEY")
        if val:
            os.environ["OPENFDA_API_KEY"] = val
    except OSError:
        pass


class CapReached(Exception):
    """Raised when today's call limit is used up."""


class State:
    """Small JSON file that remembers call counts and finished work."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()  # several workers share this file
        if self.path.exists():
            self.d = read_json_retry(self.path)
        else:
            self.d = {"calls_by_date": {}, "done": {}}

    def save(self):
        with self.lock:
            write_json_atomic(self.path, self.d)

    def is_done(self, tier, key):
        return key in self.d["done"].get(tier, {})

    def mark_done(self, tier, key, info):
        with self.lock:
            self.d["done"].setdefault(tier, {})[key] = info
            self.save()


def strip_key(text):
    """Remove any api_key=... from a web address or message, so the key is never saved."""
    if text is None:
        return None
    text = re.sub(r"[?&]api_key=[^&\s'\"]*", "", str(text))
    key = os.environ.get("OPENFDA_API_KEY")
    return text.replace(key, "KEY") if key else text


class Api:
    """Polite openFDA caller: waits between calls, retries, counts, logs.
    Safe to use from several workers (threads) at once."""

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.key = os.environ.get("OPENFDA_API_KEY") or None
        self.lock = threading.Lock()
        self.next_slot = 0.0       # earliest time the next call may start (all workers)
        self.cooldown_until = 0.0  # after a "too many requests" answer, all workers pause
        self.local = threading.local()  # one web session per worker
        self.log_path = cfg["paths"]["raw"] / "query_log.jsonl"

    @property
    def session(self):
        s = getattr(self.local, "session", None)
        if s is None:
            s = requests.Session()
            s.headers["User-Agent"] = "bmen600-group24-maude-robot"
            if self.key:
                s.auth = (self.key, "")  # key goes in a header, not in the address
            self.local.session = s
        return s

    @staticmethod
    def today():
        return dt.date.today().isoformat()

    def cap(self):
        if self.key:
            return self.cfg["daily_call_cap_with_key"]
        return self.cfg["daily_call_cap_by_date"].get(self.today(), self.cfg["daily_call_cap"])

    def calls_today(self):
        return self.state.d["calls_by_date"].get(self.today(), 0)

    def calls_left(self):
        return self.cap() - self.calls_today()

    def url(self, path, params):
        parts = []
        for k, v in params.items():
            safe = ':+[]"()*.-_' if k == "search" else ":.-_"
            parts.append(f"{k}={quote(str(v), safe=safe)}")
        return API + path + "?" + "&".join(parts)

    def get(self, path=None, params=None, url=None):
        """Returns (status, json, headers). 404 'no matches' gives empty results."""
        if url is None:
            url = self.url(path, params)
        url = strip_key(url)  # the key travels in the auth header only
        wait = 10
        for attempt in range(self.cfg["max_retries"] + 1):
            with self.lock:
                if self.calls_today() >= self.cap():
                    raise CapReached(f"daily call cap {self.cap()} reached")
                now = time.time()
                start = max(now, self.next_slot, self.cooldown_until)
                self.next_slot = start + self.cfg["min_seconds_between_calls"]
            if start > now:
                time.sleep(start - now)
            t0 = time.time()
            status, data, headers, err = None, None, {}, None
            try:
                r = self.session.get(url, timeout=180)
                status, headers = r.status_code, dict(r.headers)
                try:
                    data = r.json()
                except ValueError:
                    data = None
            except requests.RequestException as e:
                err = strip_key(repr(e))[:300]
            # count and log every attempt
            n = len(data.get("results", [])) if isinstance(data, dict) and isinstance(data.get("results"), list) else None
            with self.lock:
                day = self.today()
                self.state.d["calls_by_date"][day] = self.state.d["calls_by_date"].get(day, 0) + 1
                self.state.save()
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"time": dt.datetime.now().isoformat(timespec="seconds"),
                                        "url": url, "status": status, "n": n,
                                        "secs": round(time.time() - t0, 1), "error": err}) + "\n")
            if status == 200:
                return status, data, headers
            if status == 404:  # openFDA says "no matches found" this way
                return status, {"results": []}, headers
            if status in (429, 500, 502, 503, 504) or err:
                if status == 429:  # "too many requests": every worker waits
                    with self.lock:
                        self.cooldown_until = max(self.cooldown_until, time.time() + wait)
                print(f"  retry {attempt + 1}: status={status} err={err} wait {wait}s", flush=True)
                time.sleep(wait)
                wait *= 3
                continue
            raise RuntimeError(f"HTTP {status} for {url}: {strip_key(str(data))[:300]}")
        raise RuntimeError(f"gave up after retries: {url}")

    def fetch_all(self, path, search, extra=None):
        """All records for one search. Pages with the 'Link' header (search_after)."""
        size = self.cfg["page_size"]
        params = {"search": search, "limit": size}
        params.update(extra or {})
        url = self.url(path, params)
        out = []
        while url:
            status, data, headers = self.get(url=url)
            res = data.get("results", [])
            out.extend(res)
            m = re.search(r"<([^>]+)>", headers.get("Link", "") or "")
            url = m.group(1) if (m and len(res) == size) else None
        return out

    def fetch_to_file(self, path, search, tag):
        """Like fetch_all, but writes trimmed records straight to a gzipped file
        (so big slices never sit in memory). The real file appears only at the end.
        Returns (reports written, calls used)."""
        size = self.cfg["page_size"]
        url = self.url(EVENT, {"search": search, "limit": size})
        path = Path(path)
        tmp = path.with_suffix(path.suffix + ".tmp")
        n = calls = 0
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            while url:
                status, data, headers = self.get(url=url)
                calls += 1
                res = data.get("results", [])
                for r in res:
                    t = trim(r)
                    t["_slice"] = tag
                    f.write(json.dumps(t, ensure_ascii=False) + "\n")
                n += len(res)
                m = re.search(r"<([^>]+)>", headers.get("Link", "") or "")
                url = m.group(1) if (m and len(res) == size) else None
        replace_retry(tmp, path)
        return n, calls


# ---------------------------------------------------------------- record trimming

TOP_KEEP = ["mdr_report_key", "report_number", "date_received", "date_of_event", "date_report",
            "date_manufacturer_received", "event_type", "report_source_code", "source_type",
            "type_of_report", "mfr_report_type", "adverse_event_flag", "product_problem_flag",
            "product_problems", "number_devices_in_event", "number_patients_in_event",
            "reporter_occupation_code", "health_professional", "event_location", "remedial_action",
            "reporter_country_code"]  # country of the reporter (FIPS or ISO 2-letter code); added 2026-10-20
DEV_KEEP = ["device_report_product_code", "brand_name", "generic_name", "manufacturer_d_name",
            "model_number", "catalog_number", "lot_number", "udi_di", "device_operator",
            "device_availability", "device_evaluated_by_manufacturer", "expiration_date_of_device",
            "implant_flag", "date_removed_flag"]
PAT_KEEP = ["patient_sequence_number", "patient_age", "patient_sex", "patient_weight", "patient_race",
            "patient_ethnicity", "sequence_number_outcome", "sequence_number_treatment", "patient_problems"]


def trim(r):
    """Keep only the fields we need. Cuts file size a lot."""
    o = {k: r.get(k) for k in TOP_KEEP if k in r}
    o["device"] = [{k: d.get(k) for k in DEV_KEEP if k in d} for d in r.get("device", [])]
    o["patient"] = [{k: p.get(k) for k in PAT_KEEP if k in p} for p in r.get("patient", [])]
    o["mdr_text"] = [{"text_type_code": t.get("text_type_code"), "text": t.get("text")}
                     for t in r.get("mdr_text", [])]
    return o


# ---------------------------------------------------------------- tier 1: counts

COUNT_QUERIES = {
    # name: (count field, extra search filter)
    "received_all": ("date_received", None),
    "received_malfunction": ("date_received", "event_type:Malfunction"),
    "received_injury": ("date_received", "event_type:Injury"),
    "received_death": ("date_received", "event_type:Death"),
    "event_date_all": ("date_of_event", None),
    "event_type": ("event_type.exact", None),
    "brand_name": ("device.brand_name.exact", None),
    "product_problems": ("product_problems.exact", None),
    "patient_outcome": ("patient.sequence_number_outcome.exact", None),
    "patient_sex": ("patient.patient_sex.exact", None),
    "patient_age": ("patient.patient_age.exact", None),
    "patient_race": ("patient.patient_race.exact", None),
    "patient_ethnicity": ("patient.patient_ethnicity.exact", None),
}


def counts_path(cfg, code, name):
    return cfg["paths"]["raw"] / "counts" / f"{code}__{name}.json"


def load_counts(cfg, code, name):
    p = counts_path(cfg, code, name)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))["results"]


def cmd_counts(cfg, api, state, codes):
    (cfg["paths"]["raw"] / "counts").mkdir(parents=True, exist_ok=True)
    for code in codes:
        for name, (field, filt) in COUNT_QUERIES.items():
            key = f"{code}__{name}"
            if state.is_done("counts", key) and counts_path(cfg, code, name).exists():
                continue
            search = f"{CODE_FIELD}:{code}" + (f"+AND+{filt}" if filt else "")
            params = {"search": search, "count": field}
            if not field.startswith("date_"):
                params["limit"] = cfg["count_limit"]
            status, data, _ = api.get(EVENT, params)
            res = data.get("results", [])
            write_json_atomic(counts_path(cfg, code, name),
                              {"query": api.url(EVENT, params), "fetched": dt.datetime.now().isoformat(timespec="seconds"),
                               "results": res})
            state.mark_done("counts", key, {"rows": len(res), "total": sum(r["count"] for r in res)})
            print(f"  counts {key}: {len(res)} rows, sum {sum(r['count'] for r in res):,}", flush=True)
    write_count_tables(cfg)


def write_count_tables(cfg):
    """Turn raw count files into small tidy CSV tables in results/counts/."""
    import pandas as pd
    out = cfg["paths"]["results"] / "counts"
    out.mkdir(parents=True, exist_ok=True)
    codes = cfg["product_codes"]
    if not any(counts_path(cfg, code, "received_all").exists() for code in codes):
        print(f"  no raw count files in {cfg['paths']['raw'] / 'counts'}. Nothing written.\n"
              f"  Copy fda-maude/raw/counts/ from the old machine, or run 'counts' first (about 170 calls).", flush=True)
        return

    rows = []
    for code in codes:
        for name, et in [("received_all", "All"), ("received_malfunction", "Malfunction"),
                         ("received_injury", "Injury"), ("received_death", "Death")]:
            for r in load_counts(cfg, code, name) or []:
                rows.append((code, et, r["time"][:4] + "-" + r["time"][4:6], r["count"]))
    if rows:
        df = pd.DataFrame(rows, columns=["product_code", "event_type", "month", "reports"])
        df.groupby(["product_code", "event_type", "month"], as_index=False)["reports"].sum() \
          .to_csv(out / "reports_by_month_received.csv", index=False)

    rows = []
    for code in codes:
        for r in load_counts(cfg, code, "event_date_all") or []:
            rows.append((code, r["time"][:4] + "-" + r["time"][4:6], r["count"]))
    if rows:
        df = pd.DataFrame(rows, columns=["product_code", "month", "reports"])
        df.groupby(["product_code", "month"], as_index=False)["reports"].sum() \
          .to_csv(out / "reports_by_month_event_date.csv", index=False)

    for name, col in [("event_type", "event_type"), ("brand_name", "brand_name"),
                      ("product_problems", "product_problem"), ("patient_outcome", "patient_outcome"),
                      ("patient_sex", "patient_sex"), ("patient_age", "patient_age"),
                      ("patient_race", "patient_race"), ("patient_ethnicity", "patient_ethnicity")]:
        rows = [(code, r["term"], r["count"]) for code in codes for r in (load_counts(cfg, code, name) or [])]
        if rows:
            pd.DataFrame(rows, columns=["product_code", col, "reports"]).to_csv(out / f"{name}.csv", index=False)

    # one line per product code
    rows = []
    for code in codes:
        tot = {n: sum(r["count"] for r in (load_counts(cfg, code, n) or []))
               for n in ["received_all", "received_malfunction", "received_injury", "received_death", "event_date_all"]}
        if load_counts(cfg, code, "received_all") is None:
            continue
        months = sorted(r["time"][:6] for r in load_counts(cfg, code, "received_all"))
        rows.append({"product_code": code, "reports": tot["received_all"], "deaths": tot["received_death"],
                     "injuries": tot["received_injury"], "malfunctions": tot["received_malfunction"],
                     "other_or_blank": tot["received_all"] - tot["received_death"] - tot["received_injury"] - tot["received_malfunction"],
                     "with_event_date": tot["event_date_all"],
                     "first_received": months[0][:4] + "-" + months[0][4:] if months else "",
                     "last_received": months[-1][:4] + "-" + months[-1][4:] if months else ""})
    if rows:
        pd.DataFrame(rows).to_csv(out / "code_totals.csv", index=False)
    print(f"  wrote count tables to {out}", flush=True)


# ---------------------------------------------------------------- tier 2: serious

def daily_counts(cfg, code, names):
    d = Counter()
    for n in names:
        res = load_counts(cfg, code, n)
        if res is None:
            raise SystemExit(f"Missing counts for {code} ({n}). Run 'counts' first.")
        for r in res:
            d[r["time"]] += r["count"]
    return d


def plan_serious(cfg, codes):
    """Slices = product code x year received. Big years are cut into date ranges."""
    slices = []
    names = ["received_" + t.lower() for t in cfg["serious_event_types"]]
    for code in codes:
        daily = daily_counts(cfg, code, names)
        by_year = defaultdict(list)
        for day in sorted(daily):
            if daily[day]:
                by_year[day[:4]].append((day, daily[day]))
        for year, days in sorted(by_year.items()):
            chunk, n = [], 0
            for day, c in days:
                if chunk and n + c > cfg["serious_max_slice"]:
                    slices.append((code, chunk[0], chunk[-1], n))
                    chunk, n = [], 0
                chunk.append(day)
                n += c
            if chunk:
                # first/last day of the chunk; widen to full year edges for the year's first/last chunk
                slices.append((code, chunk[0], chunk[-1], n))
    # widen date ranges so no day is ever missed between chunks of the same year
    out = []
    for i, (code, a, b, n) in enumerate(slices):
        prev_same = i > 0 and slices[i - 1][0] == code and slices[i - 1][1][:4] == a[:4]
        next_same = i + 1 < len(slices) and slices[i + 1][0] == code and slices[i + 1][1][:4] == a[:4]
        start = a if prev_same else a[:4] + "0101"
        end = (dt.date.fromisoformat(f"{slices[i + 1][1][:4]}-{slices[i + 1][1][4:6]}-{slices[i + 1][1][6:]}")
               - dt.timedelta(days=1)).strftime("%Y%m%d") if next_same else a[:4] + "1231"
        out.append({"key": f"{code}_{start}_{end}", "code": code, "start": start, "end": end, "expected": n})
    return out


def cmd_serious(cfg, api, state, codes):
    folder = cfg["paths"]["raw"] / "serious"
    folder.mkdir(parents=True, exist_ok=True)
    types = "+".join(f"event_type:{t}" for t in cfg["serious_event_types"])
    slices = plan_serious(cfg, codes)
    print(f"  serious: {len(slices)} slices, {sum(s['expected'] for s in slices):,} reports expected", flush=True)
    for s in slices:
        path = folder / f"{s['key']}.jsonl.gz"
        if state.is_done("serious", s["key"]) and path.exists():
            continue
        search = f"{CODE_FIELD}:{s['code']}+AND+({types})+AND+date_received:[{s['start']}+TO+{s['end']}]"
        t0 = time.time()
        recs = [trim(r) for r in api.fetch_all(EVENT, search)]
        for r in recs:
            r["_slice"] = s["key"]
        write_jsonl_gz_atomic(path, recs)
        state.mark_done("serious", s["key"], {"expected": s["expected"], "got": len(recs),
                                              "fetched": dt.datetime.now().isoformat(timespec="seconds")})
        flag = "" if len(recs) == s["expected"] else f"  (expected {s['expected']})"
        print(f"  serious {s['key']}: {len(recs):,} reports in {time.time() - t0:.0f}s{flag}", flush=True)


# ---------------------------------------------------------------- tier 3: sample

def allocate(sizes, n, floor_min):
    """Proportional allocation. Strata with >= floor_min reports get at least floor_min.
    No stratum gets more than its size. Rounds so the total is exactly n."""
    fixed = {}
    free = {h: N for h, N in sizes.items() if N > 0}
    while True:
        rem = n - sum(fixed.values())
        tot = sum(free.values())
        if not free or tot == 0:
            break
        changed = False
        for h, N in list(free.items()):
            share = rem * N / tot
            fl = floor_min if N >= floor_min else 0
            if share < fl:
                fixed[h] = fl
                del free[h]
                changed = True
            elif share > N:
                fixed[h] = N
                del free[h]
                changed = True
        if not changed:
            break
    rem = n - sum(fixed.values())
    tot = sum(free.values())
    shares = {h: rem * N / tot for h, N in free.items()} if tot else {}
    alloc = {h: int(math.floor(v)) for h, v in shares.items()}
    left = rem - sum(alloc.values())
    for h in sorted(shares, key=lambda h: shares[h] - alloc[h], reverse=True)[:left]:
        alloc[h] += 1
    alloc.update(fixed)
    return {h: alloc.get(h, 0) for h in sizes}


def plan_sample(cfg, codes_all):
    strata = {}
    for code in codes_all:
        daily = daily_counts(cfg, code, ["received_malfunction"])
        for day in sorted(daily):
            if daily[day]:
                strata.setdefault(f"{code}_{day[:4]}", []).append((day, daily[day]))
    sizes = {h: sum(c for _, c in days) for h, days in strata.items()}
    alloc = allocate(sizes, cfg["sample_size"], cfg["sample_min_per_stratum"])
    return strata, sizes, alloc


def day_records(api, code, day, skip, k, sort_dir):
    search = f"{CODE_FIELD}:{code}+AND+event_type:Malfunction+AND+date_received:{day}"
    params = {"search": search, "sort": f"mdr_report_key.exact:{sort_dir}", "skip": skip, "limit": k}
    status, data, _ = api.get(EVENT, params)
    total = (data.get("meta") or {}).get("results", {}).get("total")
    return data.get("results", []), total


def run_stratum(cfg, api, state, h, days, N, n_h):
    """Pull one stratum. Two ways:
    A) Small stratum: download all of it, then pick n_h at random.
    B) Big stratum: random 'clusters' of up to 10 reports in a row from one day."""
    folder = cfg["paths"]["raw"] / "sample"
    code, year = h.split("_")
    rng = random.Random(f"{cfg['sample_seed']}|{h}")
    k_max = cfg["sample_cluster_size"]
    final = folder / f"{h}.jsonl.gz"

    if math.ceil(N / cfg["page_size"]) <= math.ceil(n_h / k_max):
        search = f"{CODE_FIELD}:{code}+AND+event_type:Malfunction+AND+date_received:[{year}0101+TO+{year}1231]"
        allr = sorted((trim(r) for r in api.fetch_all(EVENT, search)), key=lambda r: r["mdr_report_key"])
        uniq = list({r["mdr_report_key"]: r for r in allr}.values())
        pick = rng.sample(uniq, min(n_h, len(uniq)))
        pi = len(pick) / len(uniq)
        for r in pick:
            r.update({"_stratum": h, "_method": "full_list_srs", "_N_h": len(uniq), "_n_h": n_h,
                      "_sel_prob": pi, "_weight": 1 / pi, "_weight_norm": 1 / pi})
        write_jsonl_gz_atomic(final, pick)
        state.mark_done("sample", h, {"method": "full_list_srs", "N": len(uniq), "n": len(pick), "calls_draws": None})
        print(f"  sample {h}: SRS {len(pick)} of {len(uniq)}", flush=True)
        return

    # method B: cluster draws, saved one line per draw so we can resume
    parts = folder / f"{h}.parts.jsonl"
    done = []
    if parts.exists():
        for line in parts.read_text(encoding="utf-8").splitlines():
            try:
                done.append(json.loads(line))
            except ValueError:
                break  # half-written last line from a crash: ignore it
    cum, acc = [], 0
    for _, c in days:
        acc += c
        cum.append(acc)
    seen = {}
    draw = 0
    while len(seen) < n_h:
        if draw > 50 * math.ceil(n_h / k_max) + 50:
            print(f"  sample {h}: too many draws, stopping stratum", flush=True)
            break
        u = rng.randrange(N)
        if draw < len(done):
            rec = done[draw]
            if rec["u"] != u:
                raise SystemExit(f"Resume mismatch in {h} draw {draw}. Delete {parts} and rerun.")
        else:
            i = bisect.bisect_right(cum, u)
            day, c = days[i]
            pos = u - (cum[i] - c)
            k = min(k_max, c - pos)
            if pos <= 25000:
                res, total = day_records(api, code, day, pos, k, "asc")
                got = [(pos + j, r) for j, r in enumerate(res)]
            elif c - pos - k <= 25000:
                res, total = day_records(api, code, day, c - pos - k, k, "desc")
                got = [(pos + k - 1 - j, r) for j, r in enumerate(res)]
            else:
                total, got = None, []  # day too big to reach; skipped (logged)
            rec = {"draw": draw, "u": u, "day": day, "pos": pos, "c": c, "k": k, "api_total": total,
                   "records": [dict(trim(r), _pos_in_day=p) for p, r in got]}
            with open(parts, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if total is not None and total != c:
                print(f"  note {h} {day}: day count now {total}, plan used {c}", flush=True)
        for r in rec["records"]:
            seen.setdefault(r["mdr_report_key"], r)
        draw += 1

    m = draw
    out = []
    for r in seen.values():
        p = min(r["_pos_in_day"] + 1, k_max) / N  # chance one draw covers this report
        pi = 1 - (1 - p) ** m                      # chance at least one of m draws covers it
        r.update({"_stratum": h, "_method": "day_cluster", "_N_h": N, "_n_h": n_h, "_draws": m,
                  "_sel_prob": pi, "_weight": 1 / pi})
        out.append(r)
    wsum = sum(r["_weight"] for r in out)
    for r in out:
        r["_weight_norm"] = r["_weight"] * N / wsum  # scaled so weights add up to N_h
    write_jsonl_gz_atomic(final, out)
    state.mark_done("sample", h, {"method": "day_cluster", "N": N, "n": len(out), "draws": m})
    print(f"  sample {h}: {len(out)} reports from {m} draws (N={N:,})", flush=True)


def cmd_sample(cfg, api, state, codes):
    folder = cfg["paths"]["raw"] / "sample"
    folder.mkdir(parents=True, exist_ok=True)
    strata, sizes, alloc = plan_sample(cfg, cfg["product_codes"])  # plan always uses all codes
    plan = [{"stratum": h, "N": sizes[h], "n": alloc[h]} for h in sorted(sizes)]
    write_json_atomic(folder / "sample_plan.json", {"seed": cfg["sample_seed"], "size": cfg["sample_size"],
                                                     "strata": plan})
    print(f"  sample plan: {sum(alloc.values())} reports over {sum(1 for v in alloc.values() if v)} strata", flush=True)
    for h in sorted(sizes):
        if h.split("_")[0] not in codes or alloc[h] == 0:
            continue
        if state.is_done("sample", h) and (folder / f"{h}.jsonl.gz").exists():
            continue
        run_stratum(cfg, api, state, h, strata[h], sizes[h], alloc[h])


# ---------------------------------------------------------------- tier 5: full pull

def plan_full(cfg, codes):
    """Slices = product code x month received. A month with more than
    full_max_slice reports is cut into date ranges (whole days).
    Sizes come from the tier 1 daily counts."""
    mx = cfg["full_max_slice"]
    out = []
    for code in codes:
        daily = daily_counts(cfg, code, ["received_all"])
        by_month = defaultdict(list)
        for day in sorted(daily):
            if daily[day]:
                by_month[day[:6]].append((day, daily[day]))
        for month, days in sorted(by_month.items()):
            chunks, chunk, n = [], [], 0
            for day, c in days:
                if chunk and n + c > mx:
                    chunks.append((chunk[0], n))
                    chunk, n = [], 0
                chunk.append(day)
                n += c
            chunks.append((chunk[0], n))
            y, m = int(month[:4]), int(month[4:])
            last = (dt.date(y + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)).strftime("%Y%m%d")
            for i, (first, n) in enumerate(chunks):
                # chunks touch each other, so no day is ever left out
                start = month + "01" if i == 0 else first
                if i == len(chunks) - 1:
                    end = last
                else:
                    nxt = chunks[i + 1][0]
                    end = (dt.date(int(nxt[:4]), int(nxt[4:6]), int(nxt[6:])) - dt.timedelta(days=1)).strftime("%Y%m%d")
                out.append({"key": f"{code}_{start}_{end}", "code": code, "start": start, "end": end, "expected": n})
    return out


def cmd_full(cfg, api, state, codes, workers):
    """Tier 5: every report for the CGM codes, all event types.
    Several workers fetch different slices at the same time."""
    folder = cfg["paths"]["raw"] / "full"
    folder.mkdir(parents=True, exist_ok=True)
    slices = plan_full(cfg, codes)
    print(f"  full: {len(slices)} slices, {sum(s['expected'] for s in slices):,} reports expected, "
          f"{workers} workers", flush=True)
    stop = threading.Event()

    def work(s):
        if stop.is_set():
            return
        path = folder / f"{s['key']}.jsonl.gz"
        search = f"{CODE_FIELD}:{s['code']}+AND+date_received:[{s['start']}+TO+{s['end']}]"
        t0 = time.time()
        n, calls = api.fetch_to_file(path, search, s["key"])
        secs = time.time() - t0
        state.mark_done("full", s["key"], {"expected": s["expected"], "got": n, "calls": calls,
                                           "secs": round(secs, 1),
                                           "fetched": dt.datetime.now().isoformat(timespec="seconds")})
        flag = "" if n == s["expected"] else f"  (expected {s['expected']:,})"
        print(f"  [{dt.datetime.now():%H:%M:%S}] full {s['key']}: {n:,} reports, {calls} calls, {secs:.0f}s{flag}",
              flush=True)

    cap_hit = None
    for round_no in range(3):  # failed slices get two more tries
        todo = [s for s in slices
                if not (state.is_done("full", s["key"]) and (folder / f"{s['key']}.jsonl.gz").exists())]
        if not todo:
            break
        print(f"  full round {round_no + 1}: {len(todo)} slices to do", flush=True)
        failed = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(work, s): s for s in todo}
            for fu in as_completed(futs):
                try:
                    fu.result()
                except CapReached as e:
                    cap_hit = e
                    stop.set()
                except Exception as e:  # one bad slice must not stop the others
                    failed.append(futs[fu]["key"])
                    print(f"  FAILED {futs[fu]['key']}: {strip_key(repr(e))[:300]}", flush=True)
        if cap_hit:
            raise cap_hit
        if not failed:
            break
        print(f"  {len(failed)} slices failed. Waiting 60 s, then trying them again.", flush=True)
        time.sleep(60)
    left = [s["key"] for s in slices if not state.is_done("full", s["key"])]
    if left:
        print(f"  full: {len(left)} slices still not done. Run 'full' again to retry them.", flush=True)
    else:
        print("  full: all slices done.", flush=True)


# ---------------------------------------------------------------- tier 4: recalls

def cmd_recalls(cfg, api, state):
    import pandas as pd
    raw = cfg["paths"]["raw"] / "recalls"
    raw.mkdir(parents=True, exist_ok=True)
    cache_p = raw / "recalls_raw.json"
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {"recall": {}, "enf": {}, "enf_missing": []}

    # 1) recall.json by product code (+ stray sensors under pump code OZP)
    if not cache["recall"]:
        codes = cfg["product_codes"] + cfg["recall_extra_codes"]
        queries = ["+".join(f"product_code:{c}" for c in codes)] + cfg["recall_extra_queries"]
        for q in queries:
            recs = api.fetch_all("/device/recall.json", q)
            for r in recs:
                r.pop("code_info", None)
                r["_found_by"] = q
                cache["recall"].setdefault(r["product_res_number"], r)
        write_json_atomic(cache_p, cache)
    rec = cache["recall"]

    # 2) enforcement.json (has the recall class). Text searches first, then one-by-one look-ups.
    if not cache["enf"]:
        for q in cfg["enforcement_text_queries"]:
            for r in api.fetch_all("/device/enforcement.json", q):
                if r.get("recall_number") in rec:
                    r.pop("code_info", None)
                    r.pop("more_code_info", None)
                    cache["enf"][r["recall_number"]] = r
        write_json_atomic(cache_p, cache)
    for num in sorted(rec):
        if num in cache["enf"] or num in cache["enf_missing"]:
            continue
        status, data, _ = api.get("/device/enforcement.json", {"search": f'recall_number.exact:"{num}"', "limit": 1})
        if data.get("results"):
            r = data["results"][0]
            r.pop("code_info", None)
            r.pop("more_code_info", None)
            cache["enf"][num] = r
        else:
            cache["enf_missing"].append(num)
        write_json_atomic(cache_p, cache)

    excl = cfg["recall_exclude_events"]
    rows = []
    for num, r in rec.items():
        e = cache["enf"].get(num, {})
        rows.append({
            "recall_number": num,
            "recall_event_id": r.get("res_event_number"),
            "recall_class": e.get("classification", ""),
            "date_initiated": r.get("event_date_initiated", ""),
            "date_posted": r.get("event_date_posted", ""),
            "date_classified": e.get("center_classification_date", ""),
            "date_terminated": r.get("event_date_terminated", ""),
            "recall_status": r.get("recall_status", ""),
            "firm": r.get("recalling_firm", ""),
            "product_code": r.get("product_code", ""),
            "product_description": (r.get("product_description") or "").replace("\n", " "),
            "reason_for_recall": (r.get("reason_for_recall") or "").replace("\n", " "),
            "root_cause": r.get("root_cause_description", ""),
            "action": (r.get("action") or "").replace("\n", " "),
            "quantity_in_commerce": r.get("product_quantity", ""),
            "distribution": (r.get("distribution_pattern") or "").replace("\n", " "),
            "k_numbers": "; ".join(r.get("k_numbers") or []),
            "voluntary_or_mandated": e.get("voluntary_mandated", ""),
            "firm_notification": e.get("initial_firm_notification", ""),
            "cdrh_id": r.get("cfres_id", ""),
            "found_by": r.get("_found_by", ""),
        })
    df = pd.DataFrame(rows)
    dropped = df[df["recall_event_id"].astype(str).isin(excl)]
    df = df[~df["recall_event_id"].astype(str).isin(excl)].sort_values(["date_initiated", "recall_number"], ascending=[False, True])
    out = cfg["paths"]["results"]
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "recalls_cgm.csv", index=False)
    print(f"  recalls: {len(rec)} records found, {len(dropped)} dropped (non-CGM), kept {len(df)} records "
          f"in {df['recall_event_id'].nunique()} events", flush=True)
    ev_class = df.groupby("recall_event_id")["recall_class"].agg(lambda s: "/".join(sorted({x for x in s if x})) or "none")
    print(f"  events by class: {dict(Counter(ev_class))}", flush=True)

    manual = out / "recall_harm_manual.csv"
    if not manual.exists():  # never overwrite: the team fills this in by hand
        pd.DataFrame([{
            "recall_numbers": "Z-1020-2026; Z-1021-2026; Z-1022-2026; Z-1023-2026",
            "firm": "Abbott Diabetes Care, Inc.",
            "product": "FreeStyle Libre 3 and Libre 3 Plus sensors",
            "injuries": 860, "deaths": 7, "as_of_date": "2026-01-07",
            "source_url": "https://www.fda.gov/medical-devices/medical-device-recalls-and-early-alerts/"
                          "glucose-monitor-sensor-recall-abbott-diabetes-care-removes-certain-freestyle-libre-3-and-freestyle",
        }]).to_csv(manual, index=False)
        print(f"  wrote {manual}", flush=True)
    state.mark_done("recalls", "all", {"records": len(df), "events": int(df["recall_event_id"].nunique())})


# ---------------------------------------------------------------- clean

def miss(v):
    if v is None:
        return None
    v = str(v).strip()
    return None if v.lower() in MISSING else v


def join_unique(vals):
    seen = []
    for v in vals:
        v = miss(v)
        if v and v not in seen:
            seen.append(v)
    return "; ".join(seen) if seen else None


def clean_row(r, codes):
    devs = r.get("device") or [{}]
    dev = next((d for d in devs if d.get("device_report_product_code") in codes), devs[0])
    pats = r.get("patient") or []
    p0 = pats[0] if pats else {}
    texts = r.get("mdr_text") or []
    return {
        "mdr_report_key": r.get("mdr_report_key"),
        "report_number": miss(r.get("report_number")),
        "date_received": miss(r.get("date_received")),
        "date_of_event": miss(r.get("date_of_event")),
        "event_type": miss(r.get("event_type")),
        "product_code": miss(dev.get("device_report_product_code")),
        "brand_name": miss(dev.get("brand_name")),
        "generic_name": miss(dev.get("generic_name")),
        "manufacturer": miss(dev.get("manufacturer_d_name")),
        "model_number": miss(dev.get("model_number")),
        "lot_number": miss(dev.get("lot_number")),
        "product_problems": join_unique(r.get("product_problems") or []),
        "patient_outcome": join_unique(o for p in pats for o in (p.get("sequence_number_outcome") or [])),
        "patient_problems": join_unique(o for p in pats for o in (p.get("patient_problems") or [])),
        "patient_age": miss(p0.get("patient_age")),
        "patient_sex": miss(p0.get("patient_sex")),
        "patient_weight": miss(p0.get("patient_weight")),
        "patient_race": miss(p0.get("patient_race")),
        "patient_ethnicity": miss(p0.get("patient_ethnicity")),
        "report_source_code": miss(r.get("report_source_code")),
        "reporter_country_code": miss(r.get("reporter_country_code")),  # empty until raw files are re-pulled
        "n_devices": len(devs),
        "n_patients": len(pats),
        "event_text": " | ".join(t["text"] for t in texts
                                 if t.get("text_type_code") == "Description of Event or Problem" and t.get("text")) or None,
        "mfr_narrative": " | ".join(t["text"] for t in texts
                                    if t.get("text_type_code") == "Additional Manufacturer Narrative" and t.get("text")) or None,
    }


def cmd_clean(cfg, state, tiers):
    """tiers = which tables to build: any of serious, sample, full."""
    import pandas as pd
    raw, out = cfg["paths"]["raw"], cfg["paths"]["clean"]
    out.mkdir(parents=True, exist_ok=True)
    codes = set(cfg["product_codes"])
    for tier, extra in [("serious", []), ("sample", ["_stratum", "_method", "_N_h", "_n_h", "_sel_prob", "_weight", "_weight_norm"])]:
        if tier not in tiers:
            continue
        files = sorted(p for p in (raw / tier).glob("*.jsonl.gz") if state.is_done(tier, p.name[:-len(".jsonl.gz")]))
        rows = []
        for p in files:
            for r in read_jsonl_gz(p):
                row = clean_row(r, codes)
                for k in extra:
                    row[k.lstrip("_")] = r.get(k)
                rows.append(row)
        if not rows:
            print(f"  clean {tier}: nothing finished yet", flush=True)
            continue
        df = pd.DataFrame(rows)
        n0 = len(df)
        df = df.drop_duplicates("mdr_report_key", keep="first")
        df["repeated_report_number"] = df["report_number"].notna() & df.duplicated("report_number", keep=False)
        df = df.sort_values(["date_received", "mdr_report_key"])
        df.to_csv(out / f"{tier}.csv.gz", index=False, compression="gzip")
        print(f"  clean {tier}: {len(df):,} reports from {len(files)} files ({n0 - len(df)} duplicate keys removed, "
              f"{int(df['repeated_report_number'].sum())} rows share a report_number)", flush=True)
    if "full" in tiers:
        clean_full(cfg, state, codes)


def clean_full(cfg, state, codes):
    """Tier 5 is too big for memory (3.4 million reports with stories).
    So it is cleaned in a stream, one report at a time, in two passes:
    pass 1 writes rows (duplicate keys skipped) and notes repeated report numbers,
    pass 2 adds the repeated_report_number column.
    Rows are in slice order (product code, then month received), not sorted by date."""
    raw, out = cfg["paths"]["raw"], cfg["paths"]["clean"]
    files = sorted(p for p in (raw / "full").glob("*.jsonl.gz") if state.is_done("full", p.name[:-len(".jsonl.gz")]))
    if not files:
        print("  clean full: nothing finished yet", flush=True)
        return
    csv.field_size_limit(2 ** 31 - 1)  # some stories are very long
    cols = list(clean_row({}, codes).keys())
    seen_keys, seen_rn, dup_rn = set(), set(), set()
    n_in = n_out = 0
    part1 = out / "full.pass1.csv.gz"
    t0 = time.time()
    with gzip.open(part1, "wt", encoding="utf-8", newline="", compresslevel=1) as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for i, p in enumerate(files):
            with gzip.open(p, "rt", encoding="utf-8") as g:
                for line in g:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    n_in += 1
                    k = str(r.get("mdr_report_key"))
                    k = int(k) if k.isdigit() else k  # numbers use less memory than text
                    if k in seen_keys:
                        continue
                    seen_keys.add(k)
                    row = clean_row(r, codes)
                    rn = row["report_number"]
                    if rn:
                        (dup_rn if rn in seen_rn else seen_rn).add(rn)
                    w.writerow(row)
                    n_out += 1
            if (i + 1) % 200 == 0:
                print(f"  clean full pass 1: {i + 1} of {len(files)} files, {n_out:,} reports, "
                      f"{time.time() - t0:.0f}s", flush=True)
    del seen_keys, seen_rn
    final = out / "full.csv.gz"
    tmp = out / "full.csv.gz.tmp"
    n_flag = 0
    with gzip.open(part1, "rt", encoding="utf-8", newline="") as fin, \
            gzip.open(tmp, "wt", encoding="utf-8", newline="") as fout:
        rd = csv.reader(fin)
        wr = csv.writer(fout, lineterminator="\n")
        header = next(rd)
        rn_i = header.index("report_number")
        wr.writerow(header + ["repeated_report_number"])
        for row in rd:
            flag = bool(row[rn_i]) and row[rn_i] in dup_rn
            n_flag += flag
            wr.writerow(row + [flag])
    replace_retry(tmp, final)
    part1.unlink()
    print(f"  clean full: {n_out:,} reports from {len(files)} files ({n_in - n_out:,} duplicate keys removed, "
          f"{n_flag} rows share a report_number), {time.time() - t0:.0f}s -> {final}", flush=True)


# ---------------------------------------------------------------- status

def cmd_status(cfg, api, state):
    print(f"Today {api.today()}: {api.calls_today()} calls used by the robot, cap {api.cap()}, "
          f"{api.calls_left()} left. API key: {'yes' if api.key else 'no'}")
    done = state.d["done"]
    n_counts = len(cfg["product_codes"]) * len(COUNT_QUERIES)
    print(f"Tier 1 counts : {len(done.get('counts', {}))} of {n_counts} count queries done")
    print(f"Tier 4 recalls: {'done' if done.get('recalls') else 'not done'}")
    try:
        sl = plan_serious(cfg, cfg["product_codes"])
        ds = [s for s in sl if s["key"] in done.get("serious", {})]
        got = sum(done["serious"][s["key"]]["got"] for s in ds)
        print(f"Tier 2 serious: {len(ds)} of {len(sl)} slices done, {got:,} of "
              f"{sum(s['expected'] for s in sl):,} reports")
    except SystemExit as e:
        print(f"Tier 2 serious: cannot plan yet ({e})")
    try:
        strata, sizes, alloc = plan_sample(cfg, cfg["product_codes"])
        want = [h for h in sizes if alloc[h]]
        ds = [h for h in want if h in done.get("sample", {})]
        got = sum(done["sample"][h]["n"] for h in ds)
        print(f"Tier 3 sample : {len(ds)} of {len(want)} strata done, {got:,} of {sum(alloc.values()):,} reports")
    except SystemExit as e:
        print(f"Tier 3 sample : cannot plan yet ({e})")
    try:
        sl = plan_full(cfg, cfg["product_codes"])
        fd = done.get("full", {})
        ds = [s for s in sl if s["key"] in fd]
        got = sum(fd[s["key"]]["got"] for s in ds)
        calls = sum(fd[s["key"]].get("calls", 0) for s in ds)
        want = sum(s["expected"] for s in sl)
        left = want - sum(s["expected"] for s in ds)
        print(f"Tier 5 full   : {len(ds)} of {len(sl)} slices done, {got:,} of {want:,} reports, "
              f"{calls:,} calls for finished slices")
        # speed = reports in slices finished in the last 30 minutes / time since the first of them started
        now = dt.datetime.now()
        recent = [fd[k] for k in fd if (now - dt.datetime.fromisoformat(fd[k]["fetched"])).total_seconds() < 1800]
        if recent and left > 0:
            first = min(dt.datetime.fromisoformat(i["fetched"]) - dt.timedelta(seconds=i.get("secs", 0)) for i in recent)
            span = (now - first).total_seconds()
            rate = sum(i["got"] for i in recent) / span if span > 0 else 0
            if rate > 0:
                hrs = left / rate / 3600
                print(f"                speed last 30 min: {rate * 3600:,.0f} reports/hour. "
                      f"guess: {hrs:.1f} hours left (finish about {now + dt.timedelta(hours=hrs):%Y-%m-%d %H:%M})")
        mism = [s["key"] for s in ds if fd[s["key"]]["got"] != s["expected"]]
        if mism:
            print(f"                {len(mism)} finished slices got a different number than planned "
                  f"(normal if FDA updated its data). First: {mism[:3]}")
    except SystemExit as e:
        print(f"Tier 5 full   : cannot plan yet ({e})")
    lock = cfg["paths"]["raw"] / "robot.lock"
    if lock.exists():
        pid = lock.read_text().strip()
        print(f"Robot running now: {'yes' if pid_alive(pid) else 'NO (old lock file left over)'}, process ID {pid}")
    else:
        print("Robot running now: no")
    print(f"Calls by date: {state.d['calls_by_date']}")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="FDA MAUDE + recall robot for CGM sensors")
    ap.add_argument("command", choices=["counts", "serious", "sample", "full", "recalls", "clean", "status", "tables"])
    ap.add_argument("--codes", help="comma list of product codes to run (default: all in config)")
    ap.add_argument("--workers", type=int, default=None,
                    help="full only: how many slices to fetch at the same time (default in config)")
    ap.add_argument("--tiers", default="serious,sample,full",
                    help="clean only: which tables to build (default: serious,sample,full)")
    args = ap.parse_args()

    load_key_into_env()
    cfg = load_config()
    if args.command == "full":  # full pull may call a bit faster (still far below FDA's 240 per minute)
        cfg["min_seconds_between_calls"] = cfg["full_min_seconds_between_calls"]
    cfg["paths"]["raw"].mkdir(parents=True, exist_ok=True)
    state = State(cfg["paths"]["raw"] / "state.json")
    api = Api(cfg, state)
    codes = args.codes.split(",") if args.codes else cfg["product_codes"]

    lock = cfg["paths"]["raw"] / "robot.lock"
    if args.command in ("counts", "serious", "sample", "full", "recalls"):
        if lock.exists():
            old = lock.read_text().strip()
            if pid_alive(old):
                raise SystemExit(f"Another run is active (process ID {old}). Stop it first, or wait.")
            print(f"  old lock file from stopped run {old} found. Taking over.", flush=True)
        lock.write_text(str(os.getpid()))
    print(f"[{dt.datetime.now():%H:%M:%S}] {args.command}: start. Calls left today: {api.calls_left()}", flush=True)
    try:
        if args.command == "counts":
            cmd_counts(cfg, api, state, codes)
        elif args.command == "tables":
            write_count_tables(cfg)
        elif args.command == "serious":
            cmd_serious(cfg, api, state, codes)
        elif args.command == "sample":
            cmd_sample(cfg, api, state, codes)
        elif args.command == "recalls":
            cmd_recalls(cfg, api, state)
        elif args.command == "full":
            w = args.workers or cfg["full_workers"]
            if w < 1 or w > 8:
                raise SystemExit("--workers must be 1 to 8 (FDA allows 240 calls per minute; stay far below)")
            cmd_full(cfg, api, state, codes, w)
        elif args.command == "clean":
            cmd_clean(cfg, state, set(args.tiers.split(",")))
        elif args.command == "status":
            cmd_status(cfg, api, state)
    except CapReached as e:
        print(f"STOPPED: {e}. Run the same command again tomorrow to continue.", flush=True)
        sys.exit(2)
    finally:
        if lock.exists() and lock.read_text() == str(os.getpid()):
            lock.unlink()
    print(f"[{dt.datetime.now():%H:%M:%S}] {args.command}: finished. Calls used today: {api.calls_today()}", flush=True)


if __name__ == "__main__":
    main()
