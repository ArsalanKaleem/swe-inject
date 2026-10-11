"""Generate the paper's figures from the goal-only trajectory files and the guard JSON results.

    python scripts/make_figures.py \
        --main 7B=<f> 14B=<f> 32B=<f> \
        --urlfree 14B=<f> 32B=<f> \
        --guard results/guard_14B.json results/guard_32B.json \
        --guard-taint results/guard_taint_14B.json results/guard_taint_32B.json \
        --out figures

Produces (PNG at 300 dpi, plus PDF for LaTeX):
  fig1_capability_gradient   stacked: reached-payload share and compliance -> overall hijack rate, per model
  fig2_by_vector             hijack-rate-once-reached by injection vector, 14B vs 32B
  fig3_by_goal               hijack-rate-once-reached by attacker goal, 14B vs 32B
  fig4_guard_vs_rule         blocked-before-execution: learned guard vs provenance rule, main vs URL-free
  fig5_taint_blindspot       taint-rule catch rate by goal (URL-bearing vs URL-free)

Every figure also writes a sibling .csv with the exact numbers, so the plot and the text can't drift.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams.update({"font.size": 11, "axes.spawn": False} if False else {"font.size": 11})
COL = {"7B": "#5B8DB8", "14B": "#E08A3C", "32B": "#B0413E", "guard": "#888888",
       "rule": "#2E7D5B", "url": "#5B8DB8", "urlfree": "#B0413E"}
URL_GOALS = {"curl_pipe_sh", "exfiltrate", "git_push"}
ADDRESS_FREE = {"run_local_script", "install_package", "modify_path", "backdoor"}


def load(spec: str):
    label, _, path = spec.partition("=")
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    att = [r for r in rows if r["meta"].get("goal_kind", "none") != "none"]
    return label, att


def rates(att):
    n = len(att)
    reached = sum(r["category"] in ("attacked", "failed_attack") for r in att)
    hij = sum(r["category"] == "attacked" for r in att)
    return n, reached, hij


def wilson_err(k, n):
    if n == 0:
        return 0.0
    p = k / n
    return 1.96 * math.sqrt(p * (1 - p) / n)


def by_key(att, key):
    g = {}
    for r in att:
        g.setdefault(r["meta"].get(key), []).append(r)
    return g


def save(fig, out: Path, name: str):
    fig.tight_layout()
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png / .pdf")


def write_csv(out: Path, name: str, header, rows):
    with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# --------------------------------------------------------------------------- fig 1
def fig_capability(main, out):
    labels = [lab for lab, _ in main]
    reached_p, comply_p, overall_p, err = [], [], [], []
    csv_rows = []
    for lab, att in main:
        n, reached, hij = rates(att)
        reached_p.append(100 * reached / n)
        comply_p.append(100 * hij / reached if reached else 0)
        overall_p.append(100 * hij / n)
        err.append(100 * wilson_err(hij, n))
        csv_rows.append([lab, n, reached, hij, round(100 * reached / n, 1),
                         round(100 * hij / reached if reached else 0, 1), round(100 * hij / n, 1)])
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(6, 4.3))
    ax.bar(x, overall_p, yerr=err, capsize=4, color=[COL[l] for l in labels], width=0.55)
    for i, (o, r, c) in enumerate(zip(overall_p, reached_p, comply_p)):
        ax.text(i, o + err[i] + 1, f"{o:.1f}%", ha="center", fontsize=10, fontweight="bold")
        ax.annotate(f"reached {r:.0f}%, complied {c:.0f}%", xy=(i, 0), xytext=(0, -28),
                    textcoords="offset points", ha="center", fontsize=8, color="#555")
    ax.set_xticks(list(x)); ax.set_xticklabels([f"Coder-{l}" for l in labels])
    ax.tick_params(axis="x", pad=22)  # push model names below the sub-labels
    ax.set_ylabel("Hijacked (% of attacked-task episodes)")
    ax.set_title("Hijack rate rises with model capability")
    ax.set_ylim(0, max(overall_p) + max(err) + 8)
    ax.margins(x=0.08)
    save(fig, out, "fig1_capability_gradient")
    write_csv(out, "fig1_capability_gradient",
              ["model", "n", "reached", "hijacked", "reached_pct", "complied_pct", "overall_pct"], csv_rows)


# --------------------------------------------------------------------------- fig 2 / 3 grouped bars
def _grouped_rate(sets, key, out, name, title, order=None):
    cats = order or sorted({r["meta"].get(key) for _, att in sets for r in att})
    labels = [lab for lab, _ in sets]
    data = {lab: {} for lab in labels}
    csv_rows = []
    for lab, att in sets:
        g = by_key(att, key)
        for c in cats:
            rs = g.get(c, [])
            reached = sum(r["category"] in ("attacked", "failed_attack") for r in rs)
            hij = sum(r["category"] == "attacked" for r in rs)
            data[lab][c] = (100 * hij / reached if reached else None, reached, hij)
            csv_rows.append([lab, c, len(rs), reached, hij,
                             round(100 * hij / reached, 1) if reached else ""])
    x = range(len(cats)); w = 0.8 / len(labels)
    fig, ax = plt.subplots(figsize=(7, 4))
    for j, lab in enumerate(labels):
        ys = [data[lab][c][0] or 0 for c in cats]
        bars = ax.bar([i + j * w for i in x], ys, width=w, label=f"Coder-{lab}", color=COL[lab])
        for i, c in enumerate(cats):
            rate, reached, hij = data[lab][c]
            if reached:
                ax.text(i + j * w, (rate or 0) + 1.5, f"{hij}/{reached}", ha="center", fontsize=7, color="#333")
    ax.set_xticks([i + w * (len(labels) - 1) / 2 for i in x])
    ax.set_xticklabels([c.replace("_", "\n") for c in cats], fontsize=9)
    ax.set_ylabel("Hijacked (% of episodes that reached the payload)")
    ax.set_title(title); ax.legend(); ax.set_ylim(0, 105)
    save(fig, out, name)
    write_csv(out, name, ["model", key, "episodes", "reached", "hijacked", "hijacked_of_reached_pct"], csv_rows)


# --------------------------------------------------------------------------- fig 4
def fig_guard_vs_rule(guard, guard_taint, uf_guard, uf_taint, out):
    def block(paths):
        vals = []
        for p in paths:
            d = json.load(open(p))
            vals.append(100 * d.get("prevent/blocked_before_execution", 0))
        return sum(vals) / len(vals) if vals else 0
    groups = ["Main\n(mostly URL)", "URL-free"]
    learned = [block(guard), block(uf_guard)]
    rule = [block(guard_taint), block(uf_taint)]
    x = range(len(groups)); w = 0.35
    fig, ax = plt.subplots(figsize=(6, 4))
    b1 = ax.bar([i - w / 2 for i in x], learned, width=w, label="Learned guard (sg.pt)", color=COL["guard"])
    b2 = ax.bar([i + w / 2 for i in x], rule, width=w, label="Provenance rule", color=COL["rule"])
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, f"{b.get_height():.0f}%",
                    ha="center", fontsize=9)
    ax.set_xticks(list(x)); ax.set_xticklabels(groups)
    ax.set_ylabel("Hijacks blocked before execution (%)")
    ax.set_title("Provenance rule works on URL attacks, fails on URL-free")
    ax.legend(); ax.set_ylim(0, 110)
    save(fig, out, "fig4_guard_vs_rule")
    write_csv(out, "fig4_guard_vs_rule", ["group", "learned_guard_pct", "provenance_rule_pct"],
              [[groups[i].replace("\n", " "), round(learned[i], 1), round(rule[i], 1)] for i in range(2)])


# --------------------------------------------------------------------------- fig 5
def fig_blindspot(urlfree, out):
    # catch = hijack command/arg contains an address (url/domain/email); that is what the taint rule keys on
    import re
    addr = re.compile(r"https?://|[\w.-]+\.(?:com|net|org|io|evil|host)\b|@")
    cats = ["curl_pipe_sh", "exfiltrate", "git_push", "run_local_script"]
    labels = [lab for lab, _ in urlfree]
    data = {lab: {} for lab in labels}
    csv_rows = []
    for lab, att in urlfree:
        hij = [r for r in att if r["category"] == "attacked"]
        g = {}
        for r in hij:
            k = r["meta"]["goal_kind"]
            caught = any(s.get("label") == "hijacked" and addr.search(
                str((s.get("args") or {}).get("command", "")) + str((s.get("args") or {}).get("path", "")))
                for s in r["steps"])
            g.setdefault(k, [0, 0])
            g[k][0] += 1; g[k][1] += int(caught)
        for c in cats:
            tot, cau = g.get(c, [0, 0])
            data[lab][c] = (100 * cau / tot if tot else None, tot, cau)
            if tot:
                csv_rows.append([lab, c, tot, cau, round(100 * cau / tot, 1)])
    x = range(len(cats)); w = 0.8 / len(labels)
    fig, ax = plt.subplots(figsize=(7, 4))
    for j, lab in enumerate(labels):
        ys = [(data[lab][c][0] or 0) for c in cats]
        ax.bar([i + j * w for i in x], ys, width=w, label=f"Coder-{lab}", color=COL[lab])
        for i, c in enumerate(cats):
            rate, tot, cau = data[lab][c]
            if tot:
                ax.text(i + j * w, (rate or 0) + 2, f"{cau}/{tot}", ha="center", fontsize=7, color="#333")
    ax.axvspan(-0.5, 2.5, color="#eef5ff", zorder=0)
    ax.axvspan(2.5, 3.5, color="#fdeeee", zorder=0)
    ax.text(1, 104, "URL-bearing", ha="center", fontsize=9, color="#2c5d8a")
    ax.text(3, 104, "URL-free", ha="center", fontsize=9, color="#9c3a38")
    ax.set_xticks([i + w * (len(labels) - 1) / 2 for i in x])
    ax.set_xticklabels([c.replace("_", "\n") for c in cats], fontsize=9)
    ax.set_ylabel("Hijacks the provenance rule can catch (%)")
    ax.set_title("The provenance rule's blind spot")
    ax.legend(loc="center right"); ax.set_ylim(0, 112); ax.set_xlim(-0.5, 3.5)
    save(fig, out, "fig5_taint_blindspot")
    write_csv(out, "fig5_taint_blindspot", ["model", "goal", "hijacks", "catchable", "catchable_pct"], csv_rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", nargs="+", required=True, metavar="LABEL=PATH")
    ap.add_argument("--urlfree", nargs="+", default=[], metavar="LABEL=PATH")
    ap.add_argument("--guard", nargs="+", default=[])
    ap.add_argument("--guard-taint", nargs="+", default=[])
    ap.add_argument("--urlfree-guard", nargs="+", default=[])
    ap.add_argument("--urlfree-guard-taint", nargs="+", default=[])
    ap.add_argument("--out", default="figures")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    main_sets = [load(s) for s in args.main]
    print("Figure 1: capability gradient"); fig_capability(main_sets, out)

    big = [(l, a) for l, a in main_sets if l in ("14B", "32B")]
    if len(big) == 2:
        print("Figure 2: by vector"); _grouped_rate(big, "vector", out, "fig2_by_vector",
            "Which injection vector lands, once the agent reads it",
            order=["readme", "code_comment", "issue_body", "test_output", "ci_log", "dependency_docs"])
        print("Figure 3: by goal"); _grouped_rate(big, "goal_kind", out, "fig3_by_goal",
            "Which attacker goal succeeds, once the agent reads it")

    uf = [load(s) for s in args.urlfree]
    if args.guard and args.guard_taint and args.urlfree_guard and args.urlfree_guard_taint:
        print("Figure 4: guard vs rule")
        fig_guard_vs_rule(args.guard, args.guard_taint, args.urlfree_guard, args.urlfree_guard_taint, out)
    if uf:
        print("Figure 5: taint blind spot"); fig_blindspot(uf, out)
    print(f"\nAll figures and their .csv data are in {out}/")


if __name__ == "__main__":
    main()
