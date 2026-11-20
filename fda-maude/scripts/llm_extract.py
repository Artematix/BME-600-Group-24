#!/usr/bin/env python
"""
llm_extract.py : the model layer of the MAUDE text step (Phase 1, BMEN 600 Group 24).

What it does
- Sends each report text to a local open model served by Ollama.
- The model fills the fixed form. The form is a JSON schema (fda-maude/prompts/<version>_schema.json).
  Ollama's `format` option forces the answer to fit the schema.
- Prompt versions: --prompt-version v1 | v2 | ... (files in fda-maude/prompts/). v2 and later ask for the
  raw number and its unit; the code converts mmol/L to mg/dL (x 18) and fills sensor_value_mgdl /
  meter_value_mgdl, so the output form has the same fields for every version.
- Guards: every number the model returns must appear as digits in the report text. A wear day must sit
  next to the word DAY (not inside a date or time). A Parkes zone letter must appear as "X ZONE" or
  "ZONE X". Failed values become null and are listed in `guard_dropped`.
- Combined rule (`final`): when the Abbott template matched, numbers, multiple_pairs, zone and wear day
  come from the regex layer (extract_regex.py); otherwise from the model. Zone and wear day: regex when
  found, else model. Regex values that are bounds ("OVER 600") become null. `final_source` says where
  each value came from. The judgement fields always come from the model.
- Compares the model's numbers, zone and wear day with the regex layer (`disagree_fields`, `role_swap`).
- Resumable: results go to a JSONL file (one line per report). Reports already in the file are
  skipped on restart. The file is flushed every --checkpoint-every reports.
- Parallel: --parallel N sends N requests at once. The server must allow it: start it with
  OLLAMA_NUM_PARALLEL=N (scripts/start_ollama_server.ps1).
- Temperature 0 and a fixed seed in every request. Per-report latency and token counts, model digest,
  progress with throughput and ETA to the console and to --log. Writes <output>_summary.json.

Usage
  python fda-maude/scripts/llm_extract.py INPUT OUTPUT.jsonl [--model qwen2.5:7b-instruct]
      [--parallel 1] [--limit N] [--prompt-version v2] [--checkpoint-every 10] [--tag seq]
      [--regex-csv fda-maude/results/text/regex_sample.csv] [--restart] [--log run.log]
      [--num-ctx 5120] [--combine-rule template|anypair]
  INPUT = JSONL (API shape) or CSV/CSV.GZ (clean shape), same as extract_regex.py.
"""

import argparse
import collections
import csv
import datetime
import hashlib
import json
import re
import statistics
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract_regex import load_reports, extract_report, is_bound_raw  # noqa: E402

import ollama  # noqa: E402

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
DEFAULT_MODEL = "qwen2.5:7b-instruct"
DEFAULT_HOST = "http://127.0.0.1:11434"
PROMPT_DIR = SCRIPT_DIR.parent / "prompts"
DEFAULT_PROMPT_VERSION = "v2"
DEFAULT_NUM_CTX = 5120    # context window per request (v2 prefix ~2,000 tokens + text up to ~1,500 + answer)
NUM_PREDICT = 350         # answer cap in tokens (the form needs about 100 to 150)
TEMPERATURE = 0.0
SEED = 42                 # retry uses SEED + 1
MAX_TEXT_CHARS = 6000     # report text is cut here (about 1500 tokens)
KEEP_ALIVE = "30m"
REQUEST_TIMEOUT_S = 900
MMOL_FACTOR = 18.0
ALL_NUMERIC = ("sensor_value_mgdl", "meter_value_mgdl", "sensor_value_raw", "meter_value_raw", "wear_day")
WEAR_DAY_RANGE = (0, 30)
DEFAULTS_ON_BAD_VALUE = {"fault_type": "unclear", "multiple_pairs": "no", "parkes_zone_stated": None,
                         "sensor_unit": None, "meter_unit": None,
                         "fingerstick_check_done": "not_stated", "user_action": "not_stated",
                         "outcome_severity": "not_stated", "confidence": "low"}
REGEX_FIELDS_KEPT = ("regex_template", "pair_found", "sensor_value_mgdl", "meter_value_mgdl", "multiple_pairs",
                     "parkes_zone_stated", "wear_day", "sensor_display_word", "sensor_value_raw", "meter_value_raw")
FINAL_FIELDS = ("fault_type", "sensor_value_mgdl", "meter_value_mgdl", "multiple_pairs", "parkes_zone_stated",
                "wear_day", "fingerstick_check_done", "user_action", "outcome_severity", "confidence")

_thread_local = threading.local()


# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
class Logger:
    """Prints to the console and appends to a log file (if given)."""

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg):
        line = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")


# ----------------------------------------------------------------------------
# Prompt and model info
# ----------------------------------------------------------------------------
def sha256(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def load_prompt(version):
    """Read <version>_system.txt, <version>_user_template.txt, <version>_schema.json from prompts/."""
    system = (PROMPT_DIR / f"{version}_system.txt").read_text(encoding="utf-8")
    user_template = (PROMPT_DIR / f"{version}_user_template.txt").read_text(encoding="utf-8")
    schema = json.loads((PROMPT_DIR / f"{version}_schema.json").read_text(encoding="utf-8"))
    return {"version": version, "system": system, "user_template": user_template, "schema": schema,
            "raw_units": "sensor_value_raw" in schema["properties"],
            "system_sha256": sha256(system), "schema_sha256": sha256(json.dumps(schema, sort_keys=True))}


def build_messages(prompt, rep):
    """System prompt (fixed, cached by the server) + user message with the report at the end."""
    text = (rep.get("text") or "")[:MAX_TEXT_CHARS]
    user = prompt["user_template"].format(maker=rep.get("maker") or "unknown", brand=rep.get("brand_name") or "unknown",
                                          event_type=rep.get("event_type") or "unknown", text=text)
    return [{"role": "system", "content": prompt["system"]}, {"role": "user", "content": user}]


def model_info(host, model):
    """Ollama version, model digest, size and details (for the output and the summary)."""
    info = {"model": model, "host": host}
    try:
        with urllib.request.urlopen(host + "/api/version", timeout=10) as r:
            info["ollama_version"] = json.loads(r.read())["version"]
    except Exception as e:  # noqa: BLE001
        info["ollama_version"] = f"unknown ({e})"
    try:
        client = ollama.Client(host=host, timeout=60)
        show = client.show(model)
        info["details"] = show.details.model_dump() if show.details else {}
        info["modified_at"] = str(show.modified_at)
        for m in client.list().models:
            if m.model == model:
                info["digest"] = m.digest
                info["size_bytes"] = m.size
    except Exception as e:  # noqa: BLE001
        info["show_error"] = str(e)[:200]
    return info


# ----------------------------------------------------------------------------
# Model call
# ----------------------------------------------------------------------------
def get_client(host):
    """One Ollama client per thread."""
    c = getattr(_thread_local, "client", None)
    if c is None:
        c = ollama.Client(host=host, timeout=REQUEST_TIMEOUT_S)
        _thread_local.client = c
    return c


def call_model(host, model, messages, schema, seed, num_ctx):
    """One chat request with schema-constrained output, temperature 0, fixed seed. Returns (content, meta)."""
    client = get_client(host)
    t0 = time.perf_counter()
    resp = client.chat(model=model, messages=messages, format=schema,
                       options={"temperature": TEMPERATURE, "seed": seed, "num_ctx": num_ctx, "num_predict": NUM_PREDICT},
                       keep_alive=KEEP_ALIVE)
    latency = time.perf_counter() - t0
    ns = lambda x: round((x or 0) / 1e9, 3)  # noqa: E731
    meta = {"latency_s": round(latency, 3), "prompt_tokens": resp.prompt_eval_count, "output_tokens": resp.eval_count,
            "prompt_eval_s": ns(resp.prompt_eval_duration), "eval_s": ns(resp.eval_duration),
            "total_s": ns(resp.total_duration), "load_s": ns(resp.load_duration), "done_reason": resp.done_reason}
    return resp.message.content, meta


# ----------------------------------------------------------------------------
# Guards and checks
# ----------------------------------------------------------------------------
RE_NUM_TOKEN = re.compile(r"\d+(?:[.,]\d+)?")


def numbers_in_text(text, allow_mmol=True):
    """All numbers written in the text, as floats. '1,000' -> 1000, '80.00' -> 80, '5,6' -> 5.6.
    With allow_mmol (v1 only) the x18 conversions are added when the text mentions mmol/L."""
    vals = set()
    has_mmol = allow_mmol and re.search(r"MMOL", text, re.I) is not None
    for tok in RE_NUM_TOKEN.findall(text):
        s = tok
        if "," in s:
            head, tail = s.split(",", 1)
            s = head + tail if len(tail) == 3 else head + "." + tail
        try:
            v = float(s)
        except ValueError:
            continue
        vals.add(v)
        if has_mmol:
            vals.add(float(round(v * 18)))
            vals.add(round(v * 18, 1))
    for tok in re.findall(r"\d+", text):     # plain digit runs too ("1,000" -> 1 and 000)
        vals.add(float(tok))
    return vals


def wear_day_supported(text, day):
    """Stricter wear-day guard: the digits must stand alone (not inside a date, time or decimal) and sit
    right before DAY/DAYS ("12 DAYS", "3RD DAY") or right after DAY ("DAY 3")."""
    n = int(day)
    t = text.upper()
    rx = re.compile(rf"(?<![\d/:.\-]){n}(?![\d/:.])(?:ST|ND|RD|TH)?\s*-?\s*DAYS?\b|\bDAY\s+#?{n}(?![\d/:.])")
    return rx.search(t) is not None


def zone_supported(text, zone):
    """Stricter zone guard: the letter must appear as "X ZONE" or "ZONE X" (quotes allowed)."""
    z = str(zone).upper()
    t = text.upper()
    rx = re.compile(rf"(?<![A-Z])[\"']?{z}[\"']?\s+ZONE\b|\bZONE\s+[\"']?{z}(?![A-Z])")
    return rx.search(t) is not None


def numeric_fields(schema):
    return [k for k in ALL_NUMERIC if k in schema["properties"]]


def validate_answer(ans, schema):
    """Fix values outside the schema (bad enum, wrong type, missing key). Returns (ans, list of fixed fields)."""
    fixed = []
    props = schema["properties"]
    for k, spec in props.items():
        if k not in ans:
            ans[k] = DEFAULTS_ON_BAD_VALUE.get(k)
            fixed.append(k + ":missing")
            continue
        if "enum" in spec and ans[k] not in spec["enum"]:
            ans[k] = DEFAULTS_ON_BAD_VALUE.get(k)
            fixed.append(k + ":enum")
    for k in numeric_fields(schema):
        v = ans.get(k)
        if isinstance(v, bool) or not isinstance(v, (int, float, type(None))):
            try:
                ans[k] = float(str(v).replace(",", ""))
            except (TypeError, ValueError):
                ans[k] = None
            fixed.append(k + ":type")
    for k in list(ans):
        if k not in props:
            ans.pop(k)
            fixed.append(k + ":extra")
    return ans, fixed


def guard_numbers(ans, text, schema, allow_mmol):
    """Every number must appear as digits in the text, else null. Wear day and zone get the stricter
    guards. Returns (ans, dropped fields)."""
    nums = numbers_in_text(text, allow_mmol=allow_mmol)
    dropped = []
    for f in numeric_fields(schema):
        v = ans.get(f)
        if v is None:
            continue
        if float(v) not in nums:
            ans[f] = None
            dropped.append(f)
    wd = ans.get("wear_day")
    if wd is not None:
        if not (WEAR_DAY_RANGE[0] <= wd <= WEAR_DAY_RANGE[1]):
            ans["wear_day"] = None
            dropped.append("wear_day:range")
        elif not wear_day_supported(text, wd):
            ans["wear_day"] = None
            dropped.append("wear_day:context")
    z = ans.get("parkes_zone_stated")
    if z is not None and not zone_supported(text, z):
        ans["parkes_zone_stated"] = None
        dropped.append("parkes_zone_stated:context")
    return ans, dropped


def convert_units(ans):
    """v2+: fill sensor_value_mgdl / meter_value_mgdl from the raw value and unit (mmol/L x 18, rounded).
    A unit of null or "not_written" is read as mg/dL. Returns the list of converted fields."""
    converted = []
    for side in ("sensor", "meter"):
        raw, unit = ans.get(f"{side}_value_raw"), ans.get(f"{side}_unit")
        if raw is None:
            ans[f"{side}_value_mgdl"] = None
            continue
        if unit == "mmol/L":
            ans[f"{side}_value_mgdl"] = float(round(float(raw) * MMOL_FACTOR))
            converted.append(side)
        else:
            ans[f"{side}_value_mgdl"] = float(raw)
    return converted


def final_values(ans, rx, rule):
    """Combined rule. Returns (final dict, source dict). Regex values that are bounds become null."""
    def num(s):
        return float(s) if s not in ("", None) else None

    final = {f: ans.get(f) for f in FINAL_FIELDS}
    source = {f: "llm" for f in FINAL_FIELDS}
    if not rx:
        return final, source
    if rule == "template":
        use_regex = rx.get("regex_template") == "abbott_template"
    else:
        use_regex = rx.get("pair_found") == "yes" or rx.get("regex_template") == "abbott_template"
    if use_regex:
        for f, raw_col in (("sensor_value_mgdl", "sensor_value_raw"), ("meter_value_mgdl", "meter_value_raw")):
            v = num(rx.get(f))
            if v is not None and is_bound_raw(rx.get(raw_col)):
                v = None
                source[f] = "regex_bound_nulled"
            else:
                source[f] = "regex"
            final[f] = v
        final["multiple_pairs"] = rx.get("multiple_pairs") or "no"
        source["multiple_pairs"] = "regex"
    for f in ("parkes_zone_stated", "wear_day"):
        r = rx.get(f)
        if r not in ("", None):
            final[f] = num(r) if f == "wear_day" else r
            source[f] = "regex"
    return final, source


def compare_with_regex(ans, rx):
    """Compare numbers, zone and wear day with the regex row. Returns cmp_* statuses and disagree_fields."""
    def num(s):
        return float(s) if s not in ("", None) else None

    out, disagree = {}, []
    checks = [("sensor_value_mgdl", num(rx.get("sensor_value_mgdl")), True),
              ("meter_value_mgdl", num(rx.get("meter_value_mgdl")), True),
              ("wear_day", num(rx.get("wear_day")), True),
              ("parkes_zone_stated", rx.get("parkes_zone_stated") or None, False)]
    for f, r, numeric in checks:
        a = ans.get(f)
        if numeric and a is not None:
            a = float(a)
        if a is None and r is None:
            st = "both_null"
        elif a is None:
            st = "regex_only"
        elif r is None:
            st = "llm_only"
        elif a == r:
            st = "agree"
        else:
            st = "disagree"
            disagree.append(f)
        out["cmp_" + f] = st
    s_r, m_r = num(rx.get("sensor_value_mgdl")), num(rx.get("meter_value_mgdl"))
    s_a, m_a = ans.get("sensor_value_mgdl"), ans.get("meter_value_mgdl")
    out["role_swap"] = "yes" if (None not in (s_r, m_r, s_a, m_a) and s_r != m_r
                                 and float(s_a) == m_r and float(m_a) == s_r) else "no"
    out["disagree_fields"] = disagree
    return out


# ----------------------------------------------------------------------------
# One report
# ----------------------------------------------------------------------------
def process_one(rep, rx_row, prompt, args):
    """Call the model (one retry), validate, guard, convert units, combine with the regex, compare."""
    messages = build_messages(prompt, rep)
    result = {"mdr_report_key": rep["mdr_report_key"], "maker": rep["maker"], "brand_name": rep["brand_name"],
              "event_type": rep["event_type"], "split": rep.get("split", ""), "model": args.model,
              "prompt_version": prompt["version"], "run_tag": args.tag, "parallel": args.parallel, "attempts": 0, "error": ""}
    content, meta, ans, err = None, {}, None, ""
    for attempt in range(2):
        result["attempts"] = attempt + 1
        try:
            content, meta = call_model(args.host, args.model, messages, prompt["schema"], SEED + attempt, args.num_ctx)
            ans = json.loads(content)
            if not isinstance(ans, dict):
                raise ValueError("answer is not a JSON object")
            err = ""
            break
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {str(e)[:300]}"
            ans = None
    result.update(meta)
    result["raw_answer"] = content
    if ans is None:
        result["error"] = err
        result["llm"] = None
        return result
    text = rep.get("text") or ""
    ans, fixed = validate_answer(ans, prompt["schema"])
    ans, dropped = guard_numbers(ans, text, prompt["schema"], allow_mmol=not prompt["raw_units"])
    converted = convert_units(ans) if prompt["raw_units"] else []
    result["llm"] = ans
    result["guard_dropped"] = dropped
    result["schema_fixed"] = fixed
    result["mmol_converted"] = converted
    result["regex"] = {k: rx_row.get(k, "") for k in REGEX_FIELDS_KEPT}
    result.update(compare_with_regex(ans, rx_row))
    final, source = final_values(ans, rx_row, args.combine_rule)
    result["final"] = final
    result["final_source"] = source
    return result


# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
def summarize(results, wall_s, args, prompt, info, warmup_s):
    ok = [r for r in results if r.get("llm")]
    lat = sorted(r["latency_s"] for r in ok if "latency_s" in r)
    out_tok = sum(r.get("output_tokens") or 0 for r in ok)
    in_tok = sum(r.get("prompt_tokens") or 0 for r in ok)
    eval_s = sum(r.get("eval_s") or 0 for r in ok)
    cnt = collections.Counter

    def pct_idx(p):
        return lat[min(len(lat) - 1, int(p * len(lat)))] if lat else None

    s = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "run_tag": args.tag, "model": args.model, "model_info": info,
        "prompt_version": prompt["version"], "system_sha256": prompt["system_sha256"], "schema_sha256": prompt["schema_sha256"],
        "settings": {"parallel": args.parallel, "num_ctx": args.num_ctx, "num_predict": NUM_PREDICT, "temperature": TEMPERATURE,
                     "seed": SEED, "max_text_chars": MAX_TEXT_CHARS, "combine_rule": args.combine_rule,
                     "input": str(args.input), "output": str(args.output)},
        "n_requested": len(results), "n_ok": len(ok), "n_errors": len(results) - len(ok),
        "warmup_s": round(warmup_s, 1), "wall_s": round(wall_s, 1),
        "reports_per_min": round(60.0 * len(results) / wall_s, 1) if wall_s else None,
        "latency_mean_s": round(statistics.mean(lat), 2) if lat else None,
        "latency_p50_s": pct_idx(0.5), "latency_p90_s": pct_idx(0.9),
        "prompt_tokens_total": in_tok, "prompt_tokens_max": max((r.get("prompt_tokens") or 0 for r in ok), default=0),
        "output_tokens_total": out_tok,
        "output_tokens_mean": round(out_tok / len(ok), 1) if ok else None,
        "output_tok_per_s_aggregate": round(out_tok / wall_s, 1) if wall_s else None,
        "output_tok_per_s_per_request": round(out_tok / eval_s, 1) if eval_s else None,
        "done_reason_counts": dict(cnt(r.get("done_reason") for r in ok)),
        "guard_drop_reports": sum(1 for r in ok if r.get("guard_dropped")),
        "guard_drop_rate": round(sum(1 for r in ok if r.get("guard_dropped")) / len(ok), 3) if ok else None,
        "guard_drops_by_field": dict(cnt(f for r in ok for f in r.get("guard_dropped", []))),
        "mmol_converted_reports": sum(1 for r in ok if r.get("mmol_converted")),
        "schema_fixed_reports": sum(1 for r in ok if r.get("schema_fixed")),
        "retries": sum(1 for r in results if r.get("attempts", 1) > 1),
        "cmp_sensor_value_mgdl": dict(cnt(r.get("cmp_sensor_value_mgdl") for r in ok)),
        "cmp_meter_value_mgdl": dict(cnt(r.get("cmp_meter_value_mgdl") for r in ok)),
        "cmp_parkes_zone_stated": dict(cnt(r.get("cmp_parkes_zone_stated") for r in ok)),
        "cmp_wear_day": dict(cnt(r.get("cmp_wear_day") for r in ok)),
        "role_swap_reports": sum(1 for r in ok if r.get("role_swap") == "yes"),
        "final_source_counts": {f: dict(cnt(r["final_source"].get(f) for r in ok if r.get("final_source"))) for f in ("sensor_value_mgdl", "meter_value_mgdl", "parkes_zone_stated", "wear_day")},
        "fault_type_counts": dict(cnt(r["llm"].get("fault_type") for r in ok)),
        "outcome_severity_counts": dict(cnt(r["llm"].get("outcome_severity") for r in ok)),
        "user_action_counts": dict(cnt(r["llm"].get("user_action") for r in ok)),
        "confidence_counts": dict(cnt(r["llm"].get("confidence") for r in ok)),
    }
    return s


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="LLM form-filling for MAUDE CGM report texts (Ollama, JSON schema).")
    ap.add_argument("input", help="JSONL (API shape) or CSV/CSV.GZ (clean shape)")
    ap.add_argument("output", help="output JSONL (resumable)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--parallel", type=int, default=1, help="requests sent at once (server needs OLLAMA_NUM_PARALLEL >= this)")
    ap.add_argument("--limit", type=int, default=None, help="only the first N reports")
    ap.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    ap.add_argument("--num-ctx", type=int, default=DEFAULT_NUM_CTX, help="context window per request")
    ap.add_argument("--checkpoint-every", type=int, default=10, help="flush the output file and print progress every N reports")
    ap.add_argument("--tag", default="", help="free label for this run (saved in every row and the summary)")
    ap.add_argument("--regex-csv", default=None, help="reuse an extract_regex.py output; else the regex runs inline")
    ap.add_argument("--combine-rule", default="template", choices=["template", "anypair"], help="when the regex numbers win in `final`")
    ap.add_argument("--log", default=None, help="append progress lines to this file")
    ap.add_argument("--restart", action="store_true", help="ignore an existing output file and overwrite it")
    args = ap.parse_args()
    log = Logger(args.log)

    t_start = time.time()
    prompt = load_prompt(args.prompt_version)
    reports = load_reports(args.input, args.limit)
    log(f"loaded {len(reports)} reports in {time.time() - t_start:.0f} s; prompt {prompt['version']} "
        f"(system {prompt['system_sha256']}, schema {prompt['schema_sha256']}, raw units {prompt['raw_units']})")

    # regex layer: reuse a CSV or run inline (fast)
    rx = {}
    if args.regex_csv:
        csv.field_size_limit(10_000_000)
        with open(args.regex_csv, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rx[r["mdr_report_key"]] = r
        log(f"regex rows from {args.regex_csv}: {len(rx)}")
    else:
        t0 = time.time()
        for rep in reports:
            rx[rep["mdr_report_key"]] = extract_report(rep)
        log(f"regex run inline for {len(rx)} reports in {time.time() - t0:.0f} s")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists() and not args.restart:
        with open(out, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        done.add(json.loads(line)["mdr_report_key"])
                    except (ValueError, KeyError):
                        pass   # a half-written last line is redone
        log(f"resume: {len(done)} reports already in {out}")
    todo = [r for r in reports if r["mdr_report_key"] not in done]
    log(f"to do: {len(todo)} reports, parallel {args.parallel}, model {args.model}, num_ctx {args.num_ctx}, combine rule {args.combine_rule}")
    if not todo:
        log("nothing to do")
        return

    info = model_info(args.host, args.model)
    log(f"ollama {info.get('ollama_version')}, model digest {str(info.get('digest', ''))[:12]}, details {info.get('details')}")

    # warm-up: loads the model so load time does not count in the throughput
    t0 = time.time()
    call_model(args.host, args.model, [{"role": "system", "content": prompt["system"]},
                                       {"role": "user", "content": "Say hi."}], prompt["schema"], SEED, args.num_ctx)
    warmup_s = time.time() - t0
    log(f"warm-up (model load) {warmup_s:.1f} s")

    results, lock = [], threading.Lock()
    mode = "w" if args.restart else "a"
    t_run = time.time()
    with open(out, mode, encoding="utf-8") as f, ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futures = {ex.submit(process_one, rep, rx.get(rep["mdr_report_key"], {}), prompt, args): rep for rep in todo}
        n = 0
        for fut in as_completed(futures):
            res = fut.result()
            with lock:
                results.append(res)
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
                n += 1
                if n % args.checkpoint_every == 0:
                    f.flush()
                    el = time.time() - t_run
                    rate = n / el
                    eta_s = (len(todo) - n) / rate if rate else 0
                    eta_at = (datetime.datetime.now() + datetime.timedelta(seconds=eta_s)).strftime("%m-%d %H:%M")
                    lat = [r["latency_s"] for r in results[-args.checkpoint_every:] if "latency_s" in r]
                    log(f"  {n}/{len(todo)} done ({len(done) + n} in file), {el / 60:.1f} min, {60 * rate:.1f} reports/min, "
                        f"ETA {eta_s / 3600:.2f} h (~{eta_at}), recent latency {statistics.mean(lat) if lat else 0:.2f} s, "
                        f"errors {sum(1 for r in results if r['error'])}")
        f.flush()
    wall = time.time() - t_run

    summary = summarize(results, wall, args, prompt, info, warmup_s)
    sum_path = out.with_name(out.stem + "_summary.json")
    if sum_path.exists() and not args.restart:   # keep earlier runs of a resumed file
        try:
            old = json.loads(sum_path.read_text(encoding="utf-8"))
            summary["previous_runs"] = (old.get("previous_runs") or []) + [{k: old.get(k) for k in ("timestamp", "run_tag", "n_requested", "wall_s", "reports_per_min")}]
        except Exception:  # noqa: BLE001
            pass
    sum_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"run done: {len(results)} reports in {wall:.1f} s = {summary['reports_per_min']} reports/min; "
        f"output tokens {summary['output_tokens_total']} ({summary['output_tok_per_s_aggregate']} tok/s aggregate, "
        f"{summary['output_tok_per_s_per_request']} tok/s per request); max prompt tokens {summary['prompt_tokens_max']}; "
        f"errors {summary['n_errors']}; guard-drop rate {summary['guard_drop_rate']}; total {time.time() - t_start:.0f} s")
    log(f"wrote {out} and {sum_path}")


if __name__ == "__main__":
    main()
