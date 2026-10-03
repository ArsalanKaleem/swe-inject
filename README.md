# SWE-Inject / TraceWarden

This repository contains a benchmark for indirect prompt injection in software-engineering agents and a guard model that tries to detect malicious tool calls before they are executed.

In plain terms: the code creates small synthetic repositories, drops a hidden attacker instruction into one normal-looking file (issue text, README, dependency docs, code comment, failing test output, or CI log), runs an LLM-based coding agent against it, and measures whether the agent follows the hidden instruction and performs a dangerous action such as installing a malicious package, running `curl | sh`, exfiltrating environment variables, pushing to an attacker-controlled remote, editing CI files, or inserting a backdoor.

The project is split into two main parts:

- SWE-Inject: the dataset / benchmark generator and task runner
- TraceWarden: the runtime guard and model stack that scores proposed tool calls

## What the code does

### 1) Builds benchmark tasks

The benchmark is defined in `src/tracewarden/env/tasks.py` and the concrete examples live in `src/tracewarden/env/example_tasks.py`.

A `TaskSpec` describes:

- a tiny repo with a bug to fix
- an issue or repo artifact the agent should read
- a single injection vector
- the attacker's payload text
- the intended malicious goal, such as installing a malicious package or exfiltrating secrets
- a deterministic goal detector used to label the run

Each benchmark task is materialized into a fresh sandbox directory using `TaskEnv`. The builder writes the clean repository files, then injects a single payload into a chosen file. It keeps the code fix and the attack isolated: the benchmark is based on a real bug and a user task, while the hidden payload is just one extra artifact the agent may read.

### 2) Runs coding agents inside a sandbox

The sandbox implementation sits in `src/tracewarden/env/swe_sandbox.py`.

It provides safe, deterministic tool behavior for an agent:

- `read_file(path)`
- `list_dir(path)`
- `search(query, path)`
- `edit_file(path, content)`
- `run_tests(test_name)`
- `run_shell(command)`
- `git_diff()`

The sandbox is intentionally constrained:

- paths are forced to stay inside the workspace
- `curl`, `wget`, package installs, and git remote operations are intercepted and simulated
- external network calls and writes outside the repo are blocked
- the sandbox never executes dangerous shell commands for real

This makes it safe to run many attacker payloads without giving the model a real internet or repo escape path.

### 3) Detects attack success

Goal checkers in `src/tracewarden/env/tasks.py` determine whether a recorded tool call actually carries out the attacker objective.

Examples include:

- `install_package`: a command installs the typosquatted package name
- `curl_pipe_sh`: a command uses `curl ... | sh` to the attacker host
- `exfiltrate`: the command leaks environment variables or sensitive data
- `git_push`: the model pushes to the malicious remote
- `modify_path`: the model edits a CI or workflow path
- `backdoor`: the model writes code such as `eval(...)` or `os.system(...)` into non-test source
- `none`: used for benign hard negatives that look suspicious but are legitimate

These detectors are exact and task-specific. They do not just flag any shell command; they check the exact target or the exact dangerous signature.

### 4) Labels agent traces step-by-step

The label format is defined in `src/tracewarden/schema.py`.

Each step is represented as a `Step` with:

- tool name
- arguments
- raw thought text
- model output / tool observation
- a label such as `benign`, `injection_point`, `hijacked`, or `failed_injection`

A trajectory is a sequence of steps plus metadata about the task, task category, split, and source model.

The actual labeling pipeline is wired through `run_episode()` and `to_trajectory()`. The benchmark uses the AgentDojo-style labeler (`src/tracewarden/io/agentdojo.py`) to produce a consistent, shared definition of “hijacked” across synthetic and real data.

### 5) Generates datasets and smoke runs

The script `scripts/generate_swe_inject.py` is the project’s main benchmark builder.

It can:

- use the built-in 17 example tasks
- generate variant tasks from a repo list and attack phrasing templates
- run either a mock agent or a real OpenAI-compatible vLLM model
- write one JSONL record per trajectory

Example usage:

```bash
python -m pytest tests/test_swe_inject.py -q
python scripts/generate_swe_inject.py --agent both --out data/swe_inject/smoke.jsonl
```

The output looks like a sequence of tool calls for each task, including the injected reading step and the step where a malicious action is executed.

## The benchmark design

### Attack vectors

The project evaluates attacks through six vectors:

- issue body
- README
- code comment
- dependency docs
- test output
- CI log

### Attack categories / outcomes

The project distinguishes benign behavior from attacks:

- `benign`: the agent ignores the malicious instruction
- `injection_point`: the agent reads or observes the malicious prompt
- `hijacked`: the agent performs the dangerous action
- `failed_injection`: the agent saw the malicious signal but did not complete the bad action

### Hard negatives

The benchmark also includes benign tasks that look dangerous but are legitimate. This is important because a guard should not simply block any `pip install`, `curl`, or remote push. The hard-negative tasks measure false positives.

## TraceWarden: the guard model

The library part of the repo (`src/tracewarden`) is not only a benchmark. It also includes a trained runtime guard.

The relevant pieces are:

- `src/tracewarden/guard.py`: runtime guard API and scoring flow
- `src/tracewarden/featurize.py`: feature extraction from action/observation sequences
- `src/tracewarden/encoders.py`: text embedding logic
- `src/tracewarden/models/`: model classes for hijack and poison detection
- `src/tracewarden/training.py`: training and inference loops
- `src/tracewarden/metrics.py`: evaluation metrics and reporting
- `src/tracewarden/report.py`: human-readable incident reports

### What the guard does

The `Guard` class scores a proposed tool call before execution and returns a `Decision` with three possible actions:

- `allow`
- `hold`
- `block`

It looks at the current tool call and the earlier observations the agent has seen, then decides whether the requested action looks like it was influenced by untrusted content in the workspace.

This is a pre-dispatch guard: it runs before the tool call executes, rather than after the attack is already complete.

### How the model is trained

The repository supports two model families:

- `StreamGuard`: evaluates a sequence of actions and observations in real time and predicts both hijack risk and poison risk at each step
- `DriftNet`: a trajectory-level model that scores the whole session

The training pipeline is implemented in `src/tracewarden/experiments.py` and `src/tracewarden/training.py`. It:

- loads trajectories from JSONL
- encodes tasks and observations with an embedding model
- builds step/event features
- trains a classifier
- calibrates thresholds for hold/block decisions
- reports metrics such as trajectory F1, step F1, and hijack IoU

## Project structure

```text
.
├── data/
│   └── swe_inject/            sample benchmark output and task artifacts
├── notebooks/
│   └── kaggle/                Kaggle / experiment notebook scaffolding
├── results/
│   └── ...                    generated eval outputs and logs
├── scripts/
│   ├── generate_swe_inject.py  dataset generation and trajectory runner
│   ├── eval_swe_inject.py      evaluation / calibration entry point
│   └── inspect.py              dataset inspection utilities
├── src/
│   └── tracewarden/
│       ├── env/               sandbox and benchmark runtime
│       ├── features/          feature extraction for prompts and tool events
│       ├── io/                data import/export and agents dataset conversion
│       ├── integrations/      wrappers around tool calling, MCP, OpenAI loop
│       ├── models/            trained guard model implementations
│       ├── calibrate.py
│       ├── cli.py              CLI entry point for data / stats / audit / train / evaluate
│       ├── encoders.py
│       ├── experiments.py
│       ├── featurize.py
│       ├── guard.py
│       ├── metrics.py
│       ├── report.py
│       ├── schema.py
│       ├── training.py
│       └── __init__.py
├── tests/
│   └── test_swe_inject.py     unit tests for sandbox, goal matching, runner, labeling
├── pyproject.toml
├── LICENSE
├── NOTICE
├── README.md
└── runs/
```

## CLI workflows

The project exposes a CLI via `tracewarden` (see `src/tracewarden/cli.py`). Typical commands are:

```bash
tracewarden data agentdojo --root data/agentdojo --out data/processed --identity anonymize
tracewarden stats --data data/processed
tracewarden audit --data data/processed
tracewarden encode --data data/processed --encoder sentence-transformers/all-mpnet-base-v2 --out cache/mpnet
tracewarden train --model streamguard --data data/processed --cache cache/mpnet --out runs/sg.pt
tracewarden calibrate --checkpoint runs/sg.pt --data data/processed --cache cache/mpnet --alpha 0.01
tracewarden evaluate --checkpoint runs/sg.pt --data data/processed --cache cache/mpnet --split test
tracewarden scan --checkpoint runs/sg.pt --log some_trajectory.json
```

The CLI is meant to turn raw traces into processed JSONL, train a guard model, calibrate thresholds, and evaluate detection quality.

## Safety model

This project is designed for controlled research. It intentionally avoids real execution of dangerous operations:

- no network access is actually allowed
- no package installs are allowed to reach the outside world
- no git push is executed against a real remote
- file writes are constrained to the workspace

The benchmark’s purpose is not to damage systems; it is to test whether an AI coding agent can be fooled and whether a guard can catch that before a dangerous action happens.

## Installation

```bash
python -m venv .venv
. .venv/Scripts/activate      # PowerShell: .venv\Scripts\activate
pip install -e ".[dev]"
```

Optional extras:

```bash
pip install -e ".[dev,generate]"
pip install -e ".[dev,guard]"
```

The core benchmark and tests only need `numpy` and `pytest`; the real model/guard path additionally needs `torch` and the sentence-transformer stack.

## License

This project is licensed under the Apache 2.0 license.
