"""Pre-dispatch evaluation of a StreamGuard checkpoint on SWE-Inject trajectories.

Replays each LABELED trajectory through the live Session API: check() BEFORE each call,
observe() after, skip() when the guard holds/blocks. Records the actual allow/hold/block
decision per step and the hijack score, then computes the same metrics as the AISTATS work
(trajectory F1, step F1, localization, prevention) against the gold labels.

This replaces the old eval_streamguard.py, which (a) read non-existent Report attributes and
defaulted to 0 flagged, and (b) used post-hoc scan() instead of the pre-dispatch path.

    python scripts/eval_swe_inject.py --checkpoint runs/sg.pt \
        --trajectories data/swe_inject/labeled.jsonl --threshold 0.5 --out eval.json
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from tracewarden import Guard
from tracewarden.metrics import full_report, format_report
from tracewarden.schema import LABEL2ID, Trajectory, load_jsonl

H = LABEL2ID["hijacked"]


def _gold_steps(t: Trajectory) -> np.ndarray:
    return np.array([LABEL2ID[s.label] for s in t.steps], dtype=int)


def replay(guard: Guard, t: Trajectory) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Return (pred_step_ids, hijack_probs, per_decision_latency_ms) for one trajectory.

    pred label ids: block/hold on an action -> 'hijacked'(H); everything else -> 'benign'.
    (We score actions; observation rows keep gold's benign/injection_point unchanged below.)
    """
    sess = guard.session(user_task=t.user_task, world=t.world, session_id=t.id)
    pred = np.zeros(len(t.steps), dtype=int)
    probs = np.zeros(len(t.steps), dtype=float)
    lat: list[float] = []
    for i, s in enumerate(t.steps):
        start = time.perf_counter()
        d = sess.check(s.tool, s.args, thought=s.thought)
        lat.append((time.perf_counter() - start) * 1000.0)
        probs[i] = d.score
        if d.action in ("hold", "block"):
            pred[i] = H
            sess.skip()                 # the call would not have executed
        else:
            sess.observe(s.obs)         # let the guard see what the agent saw
    return pred, probs, lat


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trajectories", required=True)
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threshold", type=float, default=0.5, help="hijack-prob threshold for prevention metrics")
    ap.add_argument("--taint-policy", choices=["hold", "block"], default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    for p in (args.trajectories, args.checkpoint):
        if not Path(p).exists():
            raise FileNotFoundError(p)

    guard = Guard.load(args.checkpoint, device=args.device, taint_policy=args.taint_policy)
    trajs = load_jsonl(args.trajectories)
    if not trajs:
        raise SystemExit("no trajectories loaded")
    if not all(t.labeled for t in trajs):
        n = sum(1 for t in trajs if not t.labeled)
        raise SystemExit(f"{n} trajectories are unlabeled; run the labeler/converter first")

    gold_steps, pred_steps, hijack_probs = [], [], []
    y_true, y_pred, categories = [], [], []
    all_lat: list[float] = []

    for t in trajs:
        g = _gold_steps(t)
        p, probs, lat = replay(guard, t)
        # keep gold's non-action labels (injection_point/failed_injection) in the pred vector
        # so step-F1 for those classes is comparable; we only *predict* the hijacked class.
        for i in range(len(g)):
            if g[i] in (LABEL2ID["injection_point"], LABEL2ID["failed_injection"]) and p[i] != H:
                p[i] = g[i]
        gold_steps.append(g)
        pred_steps.append(p)
        hijack_probs.append(probs)
        all_lat.extend(lat)
        y_true.append(int((g == H).any()))
        y_pred.append(int((p == H).any()))
        categories.append(t.category or ("attacked" if (g == H).any() else "benign"))

    rep = full_report(gold_steps, pred_steps, y_true, y_pred, categories,
                      hijack_probs=hijack_probs, threshold=args.threshold)
    lat_arr = np.array(all_lat)
    rep["latency/mean_ms"] = float(lat_arr.mean())
    rep["latency/median_ms"] = float(np.median(lat_arr))
    rep["n_trajectories"] = len(trajs)
    rep["n_steps"] = int(sum(len(g) for g in gold_steps))
    rep["n_attacked"] = int(sum(y_true))

    print(format_report(rep))
    print(f"\nper-decision latency: mean {rep['latency/mean_ms']:.2f} ms, "
          f"median {rep['latency/median_ms']:.2f} ms over {len(all_lat)} decisions")
    if args.out:
        Path(args.out).write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print(f"[INFO] wrote {args.out}")


if __name__ == "__main__":
    main()
