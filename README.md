# SWE-Inject

A step-labeled benchmark and a pre-dispatch guard for **indirect prompt injection against
software-engineering agents**. A coding agent reads issue text, READMEs, code comments,
dependency docs, test output, and CI logs — all attacker-writable in open source. SWE-Inject
plants one concrete, checkable attack in each of a set of small repos, runs an agent against a
sandboxed toolset, and labels every tool call so you can measure how often agents are hijacked,
through which vector, and whether a guard catches it before the call executes.

## Install

    python -m venv .venv && . .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\activate
    pip install -e ".[dev]"            # core + tests
    pip install -e ".[dev,generate]"   # + trajectory generation against a served model
    pip install -e ".[dev,guard]"      # + the guard/model stack for the real evaluation

Core + tests need only numpy and pytest. torch is required only for the guard evaluation.

## Quick start (laptop, no GPU)

    $env:PYTHONPATH="src"           # PowerShell;  export PYTHONPATH=src on bash
    python -m pytest tests/test_swe_inject.py -q
    python scripts/generate_swe_inject.py --agent both --out data/swe_inject/smoke.jsonl

You should see 12 tests pass and 34 trajectories written, each labeled per step
(B benign, I injection_point, H hijacked, F failed_injection).

## What's here

    src/tracewarden/           vendored guard library (schema, labeler, features, model, metrics)
      env/                     the SWE-Inject environment:
        swe_sandbox.py         sandboxed tools: read_file, list_dir, search, edit_file,
                               run_tests, run_shell (network/installs/pushes intercepted), git_diff
        injectors.py           places one payload in a chosen vector
        tasks.py               TaskSpec, builder, episode runner, label converter, goal checkers
        example_tasks.py       17 tasks: 15 attacked (six vectors, six goals) + 2 hard negatives
        mock_llm.py            deterministic agents for laptop runs + a vLLM adapter for Kaggle
    scripts/generate_swe_inject.py   build tasks -> run agent -> label -> jsonl
    scripts/eval_swe_inject.py       pre-dispatch guard evaluation (check/observe), real metrics
    tests/test_swe_inject.py         sandbox safety, goal checkers, builder, runner, labeler
    data/swe_inject/smoke.jsonl      sample output from the mock agents

The package is named `tracewarden` internally; it is vendored here so this repo runs with no
private dependencies. The guard itself is described in separate work.

## Vectors and goals

Vectors: issue body, README, code comment, dependency docs, test output, CI log.
Goals (checked deterministically from recorded tool calls): install a typosquatted package,
`curl | sh`, exfiltrate environment/secrets, push to an unrequested remote, modify CI config,
write a code backdoor. Hard negatives carry no attack but a legitimate action that resembles one
(a real `pip install`, a documented `curl | sh`), so false positives are measured honestly.

## Safety

Every episode runs in a sandbox. Network calls, package installs, and git pushes are intercepted
and return canned output; nothing executes and no path outside the workspace is reachable.

## License

Apache-2.0.
