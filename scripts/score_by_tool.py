"""Show which steps the guard scores high: score summary by (tool, hijacked) and the top-scoring steps.

    python scripts/score_by_tool.py results/scores_32B.jsonl [--top 10]
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scores")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.scores, encoding="utf-8") if l.strip()]
    groups: dict[tuple[str, bool], list[float]] = defaultdict(list)
    for r in rows:
        groups[(r["tool"], r["hijacked"])].append(r["score"])
    print(f"{'tool':12s} {'hijacked':8s} {'n':>5s} {'mean':>8s} {'median':>8s} {'max':>8s}")
    for (tool, hij), v in sorted(groups.items()):
        print(f"{tool:12s} {str(hij):8s} {len(v):5d} {statistics.mean(v):8.4f} "
              f"{statistics.median(v):8.4f} {max(v):8.4f}")
    print(f"\ntop {args.top} scores:")
    for r in sorted(rows, key=lambda r: r["score"], reverse=True)[: args.top]:
        print(f"  {r['score']:.4f}  {r['tool']:10s} hijacked={r['hijacked']!s:5s}  {r['id']} step {r['step']}")


if __name__ == "__main__":
    main()
