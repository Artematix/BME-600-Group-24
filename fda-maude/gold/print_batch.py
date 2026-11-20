"""Print MAUDE sample reports in full, for careful reading.
Usage: python print_batch.py START END   (0-based index, END exclusive)
       python print_batch.py --keys KEY1 KEY2 ...   (print specific mdr_report_keys)
       python print_batch.py --order FILE START END  (print in the order of keys listed in FILE, one per line)
"""
import json, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "sample_narratives.jsonl")

def load():
    rows = []
    with open(DATA, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def show(i, r):
    print("=" * 100)
    print(f"[{i}] key={r['mdr_report_key']} | {r['brand_label']} | split={r['split']} | event_type={r['event_type']} | received={r['date_received']} | event_date={r.get('date_of_event','')}")
    print(f"    brand_name={r.get('brand_name','')} | mfr={r.get('manufacturer_d_name','')} | source={r.get('source_type')}")
    print(f"    product_problems={r.get('product_problems')} | patient_problems={r.get('patient_problems')} | outcome={r.get('patient_outcome')}")
    for t in r.get("mdr_text", []):
        print(f"  --- {t.get('type')} ---")
        print("  " + (t.get("text") or "").replace("\n", " "))
    print()

def main():
    rows = load()
    args = sys.argv[1:]
    if args and args[0] == "--keys":
        want = set(args[1:])
        for i, r in enumerate(rows):
            if r["mdr_report_key"] in want:
                show(i, r)
        return
    if args and args[0] == "--order":
        keys = [k.strip() for k in open(args[1]) if k.strip()]
        start, end = int(args[2]), int(args[3])
        bykey = {r["mdr_report_key"]: (i, r) for i, r in enumerate(rows)}
        for k in keys[start:end]:
            i, r = bykey[k]
            show(i, r)
        return
    start = int(args[0]) if args else 0
    end = int(args[1]) if len(args) > 1 else len(rows)
    for i in range(start, min(end, len(rows))):
        show(i, rows[i])

if __name__ == "__main__":
    main()
