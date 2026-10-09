"""Print what the agent actually did in selected trajectories, to audit labels by eye.

    python scripts/audit_runs.py FILE --goal install_package --category attacked,failed_attack
    python scripts/audit_runs.py FILE --goal curl_pipe_sh --category attacked --n 10
    python scripts/audit_runs.py FILE --sample 30 --seed 1        # random 30 for the label audit

For each trajectory it shows the label string, the planted payload target, and every step that is
either labeled non-benign or is a shell command / file edit (the steps where a hijack can happen).
"""
from __future__ import annotations

import argparse
import json
import random


def short(x, n: int) -> str:
    s = x if isinstance(x, str) else json.dumps(x)
    s = s.replace("\n", "\\n")
    return s if len(s) <= n else s[: n - 3] + "..."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--goal", default=None, help="goal_kind filter, e.g. install_package")
    ap.add_argument("--vector", default=None)
    ap.add_argument("--category", default=None, help="comma list: attacked,failed_attack,benign")
    ap.add_argument("--n", type=int, default=20, help="max trajectories to print")
    ap.add_argument("--sample", type=int, default=0, help="random sample of N attacked-task episodes")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--obs-chars", type=int, default=120, help="characters of each step output to show")
    ap.add_argument("--all-steps", action="store_true", help="print every step with its output (use for the label audit)")
    ap.add_argument("--check-missed", action="store_true",
                    help="automatic check: benign-labeled steps whose output contains the attack target")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.file, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r["meta"].get("goal_kind", "none") != "none"]
    if args.check_missed:
        flagged = 0
        for r in rows:
            kind, tgt = r["meta"].get("goal_kind"), r["meta"].get("goal_target", "")
            if kind in ("modify_path", "backdoor") or not tgt:
                continue  # these targets also occur in benign text, so a substring check is not meaningful
            hits = [i for i, st in enumerate(r["steps"])
                    if st.get("label", "benign") == "benign" and tgt in str(st.get("obs", ""))]
            if hits:
                flagged += 1
                print(f"POSSIBLE MISS {r['id']}: steps {hits} show target {tgt!r} but are labeled benign")
        checked = sum(1 for r in rows if r["meta"].get("goal_kind") not in ("modify_path", "backdoor"))
        print(f"\ncheck-missed: {flagged} flagged of {checked} attacked-task trajectories checked")
        return
    if args.goal:
        rows = [r for r in rows if r["meta"].get("goal_kind") == args.goal]
    if args.vector:
        rows = [r for r in rows if r["meta"].get("vector") == args.vector]
    if args.category:
        cats = set(args.category.split(","))
        rows = [r for r in rows if r["category"] in cats]
    if args.sample:
        random.Random(args.seed).shuffle(rows)
        rows = rows[: args.sample]
    print(f"{len(rows)} trajectories match; showing {min(len(rows), args.sample or args.n)}\n")

    for r in rows[: (args.sample or args.n)]:
        m = r["meta"]
        print(f"== {r['id']}")
        print(f"   {r['category']} | labels {''.join({'benign':'B','injection_point':'I','hijacked':'H','failed_injection':'F'}.get(st.get('label','benign'),'?') for st in r['steps'])} | vector={m.get('vector')} "
              f"goal={m.get('goal_kind')} target={m.get('goal_target')!r} strength={m.get('strength')}")
        for i, s in enumerate(r["steps"]):
            lab = s.get("label", "benign")
            if args.all_steps or lab != "benign" or s["tool"] in ("run_shell", "edit_file"):
                print(f"   [{i}] {lab:16s} {s['tool']:10s} {short(s['args'], 140)}")
                if args.all_steps or lab in ("injection_point", "failed_injection"):
                    print(f"        obs: {short(s.get('obs', ''), args.obs_chars)}")
        print()


if __name__ == "__main__":
    main()