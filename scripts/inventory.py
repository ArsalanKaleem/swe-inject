import json, glob, os
from collections import Counter

files = sorted(glob.glob("data/hf_raw/**/*.jsonl", recursive=True))
print(f"found {len(files)} jsonl files\n")
grand = Counter()
for f in files:
    rows = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
    cat = Counter(r["category"] for r in rows)
    models = {r["meta"].get("model") for r in rows}
    att = [r for r in rows if r["category"] == "attacked"]
    vec = Counter(r["meta"].get("vector") for r in att)
    print(f"{os.path.relpath(f, 'data/hf_raw')}")
    print(f"   model: {models}")
    print(f"   total {len(rows)} | {dict(cat)}")
    if att:
        rate = len(att) / max(1, sum(1 for r in rows if r['category'] in ('attacked','failed_attack')))
        print(f"   hijack rate (attacked / attacked+failed): {rate:.1%} | by vector: {dict(vec)}")
    print()
    grand[str(models)] += len(rows)
print("totals by model:", dict(grand))