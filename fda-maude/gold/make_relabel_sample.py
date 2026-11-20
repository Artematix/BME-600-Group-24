"""Pick 40 random reports for the blind re-label check (fixed seed) and print them in a shuffled order."""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "..", "data", "sample_narratives.jsonl"), encoding="utf-8") if l.strip()]
keys = [r["mdr_report_key"] for r in rows]
rng = random.Random(2026)
sample = rng.sample(keys, 40)
rng.shuffle(sample)
with open(os.path.join(HERE, "relabel_keys.txt"), "w") as f:
    f.write("\n".join(sample) + "\n")
print("\n".join(sample))
