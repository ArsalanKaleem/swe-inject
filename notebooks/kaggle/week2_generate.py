# SWE-Inject Week 2: generate real trajectories on Kaggle (Gemma 4, Qwen fallback).
# This file is written as separated cells. In the Kaggle editor, make a new cell at each
# "# %% CELL N" marker and paste that block. Run cells in order.
#
# Prereqs (do these in the Kaggle UI, see the tutorial):
#   - Add your repo as a dataset:  arsalankaleem/swe-inject-src   (slug may differ; cell 1 auto-finds it)
#   - Settings: Accelerator = GPU T4 x2; Internet = ON (then Run > Restart session once)
#   - Add secret: label  tracewarden-token-huggingface   (your HF write token)


# %% CELL 1 ---------------------------------------------------------------- setup + find repo
import os, sys, time, json, glob, subprocess, urllib.request

# locate the repo package shipped as a Kaggle dataset (mount path differs from the slug)
hits = glob.glob("/kaggle/input/**/swe-inject/src/tracewarden/__init__.py", recursive=True)
if not hits:
    hits = glob.glob("/kaggle/input/**/tracewarden/__init__.py", recursive=True)
assert hits, "couldn't find the repo. Add your swe-inject dataset to the notebook (Data panel)."
SRC = os.path.abspath(os.path.join(os.path.dirname(hits[0]), ".."))  # .../src
REPO = os.path.abspath(os.path.join(SRC, ".."))                      # repo root (has scripts/)
sys.path.insert(0, SRC)
print("repo src:", SRC)
print("repo root:", REPO)

# /kaggle/input is read-only; copy scripts to working so we can run them
os.makedirs("/kaggle/working/scripts", exist_ok=True)
for f in glob.glob(os.path.join(REPO, "scripts", "*.py")):
    subprocess.run(["cp", f, "/kaggle/working/scripts/"], check=True)
import tracewarden
print("tracewarden:", tracewarden.__file__)


# %% CELL 2 ---------------------------------------------------------------- install vLLM
# Internet must be ON and the session restarted once after enabling it.
get_ipython().system('pip install -q -U vllm openai')
import vllm
print("vLLM", vllm.__version__)


# %% CELL 3 ---------------------------------------------------------------- HF login (secret)
from kaggle_secrets import UserSecretsClient
from huggingface_hub import login, HfApi
HF_TOKEN = UserSecretsClient().get_secret("tracewarden-token-huggingface")
login(token=HF_TOKEN)
os.environ["HF_TOKEN"] = HF_TOKEN
HF_DATASET_REPO = "ArsalanKaleem/swe-inject-steps-raw"   # change to your target dataset repo
api = HfApi()
api.create_repo(HF_DATASET_REPO, repo_type="dataset", private=True, exist_ok=True)
print("HF dataset:", HF_DATASET_REPO)


# %% CELL 4 ---------------------------------------------------------------- serve the model
# Primary: Gemma 4 E4B with the gemma4 parser. Fallback: Qwen2.5-Coder-7B with hermes.
MODEL = "google/gemma-4-E4B-it"      # fallback: "Qwen/Qwen2.5-Coder-7B-Instruct"
PARSER = "gemma4"                      # fallback: "hermes"
TP = 2                                 # E4B bf16 ~18GB -> split across both T4s
PORT = 8000

env = os.environ.copy()
env["VLLM_USE_V1"] = "0"               # legacy engine, more reliable on dual T4
cmd = [sys.executable, "-m", "vllm.entrypoints.openai.api_server",
       "--model", MODEL, "--dtype", "half", "--tensor-parallel-size", str(TP),
       "--max-model-len", "8192", "--gpu-memory-utilization", "0.90",
       "--enforce-eager", "--enable-auto-tool-choice", "--tool-call-parser", PARSER,
       "--port", str(PORT)]
logf = open("/kaggle/working/vllm_server.log", "w")
proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env=env)

for i in range(240):  # up to ~20 min for download + load
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/v1/models", timeout=2); print("\nserver up"); break
    except Exception:
        if proc.poll() is not None:
            print("=== vLLM crashed; last 40 log lines ===")
            print("".join(open("/kaggle/working/vllm_server.log").readlines()[-40:]))
            raise SystemExit("vLLM died during startup. If it's a tool-parser error, switch to the Qwen fallback in this cell.")
        if i % 6 == 0: print(f"loading... {i*5}s")
        time.sleep(5)
else:
    raise SystemExit("server did not come up in time")


# %% CELL 5 ---------------------------------------------------------------- tool-calling smoke test
# Few-minute check that the parser works before spending hours generating.
from openai import OpenAI
client = OpenAI(base_url=f"http://localhost:{PORT}/v1", api_key="x")
from tracewarden.env.swe_sandbox import SWESandbox
import tempfile
sb = SWESandbox(tempfile.mkdtemp()); TOOLS = sb.get_tool_definitions()

def ask(msgs):
    r = client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS,
                                       tool_choice="auto", temperature=0.0, max_tokens=512, stream=False)
    m = r.choices[0].message
    calls = [(c.function.name, c.function.arguments) for c in (m.tool_calls or [])]
    return m, calls

sys_msg = {"role": "system", "content": "You are a coding agent. Use tools to inspect and fix the repo."}
m, calls = ask([sys_msg, {"role": "user", "content": "Open src/app.py and tell me what it does."}])
print("tool_calls:", calls)
print("leaked into content:", (m.content or "")[:200])
assert calls, "no tool call parsed -> parser problem. Switch cell 4 to the Qwen fallback and re-run from cell 4."
print("[PASS] tool calling works")


# %% CELL 6 ---------------------------------------------------------------- 2-task generation smoke
# Generate just two tasks, read the labels by hand before any long run (your Kaggle lesson).
rc = subprocess.run([sys.executable, "/kaggle/working/scripts/generate_swe_inject.py",
                     "--variants", "--max-per-repo", "1", "--agent", "vllm",
                     "--model", MODEL, "--tool-parser", PARSER,
                     "--base-url", f"http://localhost:{PORT}/v1",
                     "--seed", "0", "--out", "/kaggle/working/smoke_real.jsonl"],
                    env={**env, "PYTHONPATH": SRC}, capture_output=True, text=True)
print(rc.stdout[-3000:]); print(rc.stderr[-2000:])
# read a couple of trajectories by hand
from tracewarden.schema import load_jsonl
for t in load_jsonl("/kaggle/working/smoke_real.jsonl")[:3]:
    print("\n==", t.id, t.category, t.label_string)
    for s in t.steps:
        print("  ", s.tool, json.dumps(s.args)[:60], "| obs:", s.obs[:70].replace("\n", " "))


# %% CELL 7 ---------------------------------------------------------------- full run + upload
# Generate the full variant set. Upload is incremental: cell writes one file, then pushes to HF.
# If the session dies, re-run from cell 1; already-uploaded files stay on HF.
OUT = "/kaggle/working/swe_inject_gemma4.jsonl"   # rename per model so a rerun can't overwrite
rc = subprocess.run([sys.executable, "/kaggle/working/scripts/generate_swe_inject.py",
                     "--variants", "--phrasings-per-goal", "2", "--agent", "vllm",
                     "--model", MODEL, "--tool-parser", PARSER,
                     "--base-url", f"http://localhost:{PORT}/v1",
                     "--seed", "0", "--out", OUT],
                    env={**env, "PYTHONPATH": SRC}, capture_output=True, text=True)
print(rc.stdout[-4000:]); print(rc.stderr[-2000:])

# upload immediately (distinct filename on HF so nothing is overwritten)
stamp = time.strftime("%Y%m%d-%H%M%S")
api.upload_file(path_or_fileobj=OUT, repo_id=HF_DATASET_REPO, repo_type="dataset",
                path_in_repo=f"gemma4/{stamp}.jsonl")
api.upload_file(path_or_fileobj="/kaggle/working/vllm_server.log", repo_id=HF_DATASET_REPO,
                repo_type="dataset", path_in_repo=f"gemma4/{stamp}.vllm.log")
print("uploaded to HF:", HF_DATASET_REPO, stamp)


# %% CELL 8 ---------------------------------------------------------------- quick distribution check
from collections import Counter
rows = [json.loads(l) for l in open(OUT)]
print("total", len(rows))
print("by category", Counter(r["category"] for r in rows))
att = [r for r in rows if r["category"] == "attacked"]
print("attacked by vector", dict(Counter(r["meta"]["vector"] for r in att)))
print("attacked by goal", dict(Counter(r["meta"]["goal_kind"] for r in att)))
print("model in records:", {r["meta"].get("model") for r in rows})
