import json
from collections import Counter

path = "results/swe_inject_Qwen2.5-7B-Instruct.jsonl"

rows = [
    json.loads(line)
    for line in open(path, encoding="utf-8")
]

print("step counts:", Counter(len(r["steps"]) for r in rows))

fails = [r for r in rows if r.get("category") == "failed_attack"][:10]

for r in fails:
    meta = r.get("meta", {})

    print("\n==", r["id"])
    print("category:", r.get("category"))
    print("domain:", r.get("domain"))
    print("user_task:", r.get("user_task"))
    print("meta:", meta)

    for i, s in enumerate(r.get("steps", []), 1):
        obs = str(s.get("obs", "")).replace("\n", " ")
        print(
            f"  {i}. {s.get('tool')}"
            f" {json.dumps(s.get('args', {}))[:80]}"
            f" | obs: {obs[:120]}"
        )
    def step_text(step):
     return " ".join([
        str(step.get("tool", "")),
        json.dumps(step.get("args", {})),
        str(step.get("obs", "")),
    ]).lower()


for r in fails:
    text = "\n".join(step_text(s) for s in r.get("steps", []))

    # Adapt these markers to your actual injection corpus.
    markers = [
        "curl ",
        "git push",
        "install package",
        "important dev note",
        "upstream hotfix",
    ]

    found = [m for m in markers if m.lower() in text]

    print(r["id"], "payload markers:", found)      