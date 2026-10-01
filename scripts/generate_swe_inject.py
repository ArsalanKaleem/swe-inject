"""Generate SWE-Inject trajectories: materialize each task, run an agent, label, save.

Laptop smoke test (no GPU), two deterministic agents so every task yields one attacked
and one benign trajectory, and you can read labels before any Kaggle run:

    python scripts/generate_swe_inject.py --agent both --out data/swe_inject/smoke.jsonl

Kaggle, real model over an OpenAI-compatible vLLM endpoint:

    python scripts/generate_swe_inject.py --agent vllm \
        --model google/gemma-4-E4B-it --tool-parser gemma4 \
        --base-url http://localhost:8000/v1 --out /kaggle/working/swe_inject_gemma4.jsonl

Writes one JSON line per trajectory via schema.save_jsonl format. Records model id and
metadata in each trajectory so the dataset is self-describing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tracewarden.env.example_tasks import TASKS
from tracewarden.env.mock_llm import BenignAgent, GullibleAgent, VLLMAgent
from tracewarden.env.tasks import TaskEnv, load_tasks, run_episode, to_trajectory


def agent_factories(kind: str, args):
    """Return [(model_name, make_agent)]; make_agent is called fresh per task so no
    per-episode state (e.g. GullibleAgent._fired) leaks between tasks."""
    if kind == "benign":
        return [("benign", BenignAgent)]
    if kind == "gullible":
        return [("gullible", GullibleAgent)]
    if kind == "both":
        return [("gullible", GullibleAgent), ("benign", BenignAgent)]
    if kind == "vllm":
        from openai import OpenAI
        client = OpenAI(base_url=args.base_url, api_key="x")
        return [(args.model, lambda: VLLMAgent(client, args.model))]
    raise ValueError(kind)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=None, help="tasks jsonl; default uses the built-in example tasks")
    ap.add_argument("--agent", choices=["benign", "gullible", "both", "vllm"], default="both")
    ap.add_argument("--model", default="mock")
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--tool-parser", default=None, help="informational; serving uses it, recorded in meta")
    ap.add_argument("--max-steps", type=int, default=20)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    specs = load_tasks(args.tasks) if args.tasks else TASKS
    factories = agent_factories(args.agent, args)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for spec in specs:
            for model_name, make_agent in factories:
                env = TaskEnv(spec)
                ep = run_episode(env, make_agent(), model_name, max_steps=args.max_steps)
                traj = to_trajectory(env, ep)
                if args.tool_parser:
                    traj.meta["tool_parser"] = args.tool_parser
                f.write(traj.to_json() + "\n")
                n += 1
                print(f"{spec.task_id} [{model_name}] steps={len(traj.steps)} "
                      f"labels={traj.label_string} category={traj.category}")
    print(f"\n[INFO] wrote {n} trajectories to {out_path}")


if __name__ == "__main__":
    main()
