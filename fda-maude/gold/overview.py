import json, os, collections, re
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "..", "data", "sample_narratives.jsonl"), encoding="utf-8") if l.strip()]
print("n =", len(rows))
print(collections.Counter((r["brand_label"], r["split"], r["event_type"]) for r in rows))
print("manufacturers:", collections.Counter(r["manufacturer_d_name"] for r in rows))
print("text types:", collections.Counter(t["type"] for r in rows for t in r["mdr_text"]))
print("no text:", sum(1 for r in rows if not r["mdr_text"]))
lens = sorted(sum(len(t["text"]) for t in r["mdr_text"]) for r in rows)
print("total chars:", sum(lens), "median:", lens[len(lens)//2], "max:", lens[-1])
print("mmol:", sum(1 for r in rows if re.search(r"mmol", " ".join(t["text"] for t in r["mdr_text"]), re.I)))
print("keys unique:", len(set(r["mdr_report_key"] for r in rows)))
# index ranges per group
for i, r in enumerate(rows):
    if i == 0 or (r["brand_label"], r["split"]) != (rows[i-1]["brand_label"], rows[i-1]["split"]):
        print("group starts at", i, r["brand_label"], r["split"])
