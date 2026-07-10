#!/usr/bin/env python3
"""Matrix driver for the benchmark: run any models x projects slice, grade,
analyze, evaluate, publish — from a menu or the CLI.

CLI:
  scripts/matrix.py                          interactive menu
  scripts/matrix.py run                      everything in models.txt, all projects
  scripts/matrix.py run -m gpt-5.4 -m fable  subset of models (label or model id)
  scripts/matrix.py run -p 10                one project, all models (resumes each
                                             model's branch; earlier solutions kept)
  scripts/matrix.py run -m gpt-5.4 -p 10 --fresh   fresh branch (re-solve from seed)
  scripts/matrix.py grade [-m ...]           re-grade only (no solving)
  scripts/matrix.py status                   pass/fail matrix from reports/
  scripts/matrix.py summarize                combined leaderboard
  scripts/matrix.py evaluate [DATE]          snapshot + evaluation md/html + index
  scripts/matrix.py analyze [DATE]           LLM run review (re-analyze overwrites)
  scripts/matrix.py publish                  push the results branch
  scripts/matrix.py pipeline                 run -> evaluate -> analyze -> publish

Selection flags for run/grade:
  -m/--model   repeatable; matches report label OR model id (e.g. 'gpt-5.4',
               'gpt-5.4-cc', 'glm-5.2:cloud'). Default: every models.txt entry.
  -p/--project repeatable; matches by number or name ('10', '10-txn-store').
               Default: all projects. With -p and an existing model branch the
               branch is REUSED so earlier solutions still count; --fresh resets.

Runner mechanics mirror run_models.sh / run_ollama*.sh / run_openai*.sh; the
openai-cc LiteLLM proxy is started and stopped automatically.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROMPT = (
    "Read the file TASK.md in the current directory and make the code change "
    "it describes. Edit the source file(s) directly. Do NOT modify any test "
    "file (test_*, *_test.go, *.test.js) or run_tests.sh. Make the smallest "
    "change that satisfies the task. Do not run git or commit; just leave the "
    "edited files in place."
)

LITELLM_PORT = int(os.environ.get("LITELLM_PORT", "4141"))


# ---------- model list / projects ----------

def parse_models(path="models.txt"):
    """[(runner, model, label)] from models.txt."""
    entries = []
    for line in open(os.path.join(ROOT, path)):
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        runner, model = parts[0], parts[1]
        if runner in ("ollama", "openai"):
            label = re.sub(r"[:/ ]", "_", model)
        elif runner in ("ollama-cc", "openai-cc"):
            label = re.sub(r"[:/]", "_", model) + "-cc"
        elif runner == "claude":
            label = model
        else:
            print(f"warning: unknown runner {runner!r} — skipped")
            continue
        entries.append((runner, model, label))
    return entries


def all_projects():
    pdir = os.path.join(ROOT, "projects")
    return sorted(d for d in os.listdir(pdir)
                  if os.path.isdir(os.path.join(pdir, d)))


def match_projects(wanted):
    projs = all_projects()
    if not wanted:
        return projs
    out = []
    for w in wanted:
        hits = [p for p in projs if p == w or p.startswith(w + "-") or p.startswith(w)]
        if not hits:
            sys.exit(f"no project matches {w!r} (have: {', '.join(projs)})")
        out.extend(h for h in hits if h not in out)
    return out


def match_entries(entries, wanted):
    if not wanted:
        return entries
    out = []
    for w in wanted:
        hits = [e for e in entries if e[2] == w]      # exact label first
        if not hits:
            hits = [e for e in entries if w == e[1]]  # then model id (may be 2)
        if not hits:
            sys.exit(f"no models.txt entry matches {w!r} "
                     f"(labels: {', '.join(e[2] for e in entries)})")
        out.extend(h for h in hits if h not in out)
    return out


# ---------- shell helpers ----------

def sh(cmd, **kw):
    """Run, streaming output. Raises on failure unless check=False."""
    kw.setdefault("cwd", ROOT)
    kw.setdefault("check", True)
    return subprocess.run(cmd, **kw)


def sh_out(cmd, **kw):
    kw.setdefault("cwd", ROOT)
    return subprocess.run(cmd, capture_output=True, text=True, **kw).stdout


def git(*args, check=True):
    return sh(["git", *args], check=check,
              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def branch_exists(name):
    return subprocess.run(["git", "rev-parse", "--verify", "-q",
                           f"refs/heads/{name}"],
                          cwd=ROOT, capture_output=True).returncode == 0


# ---------- litellm proxy (openai-cc) ----------

class LiteLLMProxy:
    def __init__(self, models):
        self.models = models
        self.proc = None

    def __enter__(self):
        if not os.environ.get("OPENAI_API_KEY"):
            sys.exit("OPENAI_API_KEY is not set (needed for openai-cc)")
        exe = shutil.which("litellm")
        cmd = [exe] if exe else ["uvx", "--from", "litellm[proxy]", "litellm"]
        if not exe and not shutil.which("uvx"):
            sys.exit("need litellm on PATH or uv installed (brew install uv)")
        cfg = os.path.join(ROOT, "reports", ".litellm-matrix.yaml")
        os.makedirs(os.path.dirname(cfg), exist_ok=True)
        with open(cfg, "w") as f:
            f.write("model_list:\n")
            for m in self.models:
                f.write(f"  - model_name: {m}\n    litellm_params:\n"
                        f"      model: openai/{m}\n"
                        f"      api_key: os.environ/OPENAI_API_KEY\n")
        log = open(os.path.join(ROOT, "reports", "litellm.log"), "w")
        self.proc = subprocess.Popen(
            cmd + ["--config", cfg, "--port", str(LITELLM_PORT)],
            cwd=ROOT, stdout=log, stderr=log)
        for _ in range(90):
            try:
                urllib.request.urlopen(
                    f"http://localhost:{LITELLM_PORT}/health/liveliness",
                    timeout=2)
                return self
            except OSError:
                if self.proc.poll() is not None:
                    sys.exit("litellm died; see reports/litellm.log")
                time.sleep(1)
        sys.exit("litellm never became healthy; see reports/litellm.log")

    def __exit__(self, *exc):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)


# ---------- solving ----------

def solve_project(runner, model, label, proj):
    """Solve one project in the current checkout. Returns True on success."""
    pdir = os.path.join(ROOT, "projects", proj)
    logdir = os.path.join(ROOT, "reports", f"{label}.logs")
    os.makedirs(logdir, exist_ok=True)
    jlog = os.path.join(logdir, f"{proj}.json")
    tlog = os.path.join(logdir, f"{proj}.txt")

    if runner in ("ollama", "openai"):
        script = f"scripts/{runner}_solve.py"
        with open(tlog, "w") as t:
            r = subprocess.run(["python3", os.path.join(ROOT, script),
                                model, pdir, jlog],
                               cwd=ROOT, stdout=t, stderr=subprocess.STDOUT)
        return r.returncode == 0

    env = os.environ.copy()
    if runner == "ollama-cc":
        env["ANTHROPIC_BASE_URL"] = os.environ.get(
            "OLLAMA_URL", "http://localhost:11434")
        env["ANTHROPIC_AUTH_TOKEN"] = "ollama"
    elif runner == "openai-cc":
        env["ANTHROPIC_BASE_URL"] = f"http://localhost:{LITELLM_PORT}"
        env["ANTHROPIC_AUTH_TOKEN"] = "litellm"

    with open(jlog, "w") as j, open(tlog, "a") as t:
        r = subprocess.run(["claude", "--model", model, "-p", PROMPT,
                            "--dangerously-skip-permissions",
                            "--output-format", "json"],
                           cwd=pdir, env=env, stdout=j, stderr=t)
    return r.returncode == 0


def zero_cost(label):
    """The claude CLI prices unknown models with bogus numbers."""
    p = os.path.join(ROOT, "reports", f"{label}.usage.json")
    if not os.path.exists(p):
        return
    u = json.load(open(p))
    u["cost_usd"] = 0.0
    for v in u.get("by_project", {}).values():
        if isinstance(v, dict) and "cost_usd" in v:
            v["cost_usd"] = 0.0
    json.dump(u, open(p, "w"), indent=1)


def run_entry(runner, model, label, projects, fresh):
    subset = len(projects) < len(all_projects())
    resume = subset and not fresh and branch_exists(f"model/{label}")
    print("=" * 60)
    mode = "resume" if resume else "fresh"
    print(f"{runner.upper()}: {model}  (label: {label}, {mode}, "
          f"{len(projects)} project(s))")
    print("=" * 60)

    if resume:
        git("checkout", "-q", f"model/{label}")
        for proj in projects:  # reset targets to current seeded state
            git("checkout", "main", "--", f"projects/{proj}")
    else:
        sh(["./bench.sh", "start", label], stdout=subprocess.DEVNULL)

    for proj in projects:
        print(f"  -> {model} solving {proj} ...")
        if not solve_project(runner, model, label, proj):
            print(f"     (solve failed on {proj}; see reports/{label}.logs/)")

    sh(["python3", "scripts/usage.py", label])
    if runner != "claude":
        zero_cost(label)
    print(f"  -> grading {label}")
    sh(["./bench.sh", "grade", label])
    print()


def cmd_run(entries, projects, fresh):
    cc_models = [m for r, m, _ in entries if r == "openai-cc"]
    if cc_models:
        with LiteLLMProxy(sorted(set(cc_models))):
            for e in entries:
                run_entry(*e, projects, fresh)
    else:
        for e in entries:
            run_entry(*e, projects, fresh)
    cmd_summarize()


def cmd_grade(entries):
    for _, _, label in entries:
        if not branch_exists(f"model/{label}"):
            print(f"  (no branch model/{label} — skipped)")
            continue
        sh(["./bench.sh", "grade", label])
    cmd_summarize()


# ---------- reporting ----------

def cmd_summarize():
    sh(["python3", "scripts/summarize.py"])


def cmd_status():
    projs = all_projects()
    rows = []
    rdir = os.path.join(ROOT, "reports")
    for f in sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []:
        if not f.endswith(".results.json"):
            continue
        label = f[: -len(".results.json")]
        res = {r["project"]: r["status"]
               for r in json.load(open(os.path.join(rdir, f)))}
        rows.append((label, res))
    if not rows:
        print("no reports/ yet — run something first")
        return
    w = max(len(l) for l, _ in rows)
    hdr = " ".join(p.split("-")[0] for p in projs)
    print(f"{'label'.ljust(w)}  {hdr}  pass")
    for label, res in rows:
        cells, npass = [], 0
        for p in projs:
            s = res.get(p)
            npass += s == "pass"
            cells.append({"pass": " ok ", "fail": "FAIL"}.get(s, " -- "))
        print(f"{label.ljust(w)}  {' '.join(cells)}  {npass}/{len(projs)}")


# ---------- evaluate / analyze / publish ----------

def cmd_evaluate(date):
    sh(["./scripts/snapshot.sh", date])
    sh(["./scripts/evaluate.sh", date])
    sh(["./scripts/evaluate_html.sh", date])
    sh(["./scripts/build_index.sh"])


def cmd_analyze(date):
    print(f"generating LLM review for {date} (this calls `claude -p`) ...")
    bundle = sh_out(["./scripts/analyze_run.sh", date])
    r = subprocess.run(["claude", "-p", "-"], cwd=ROOT, input=bundle,
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"review generation failed: {r.stderr[:400]}")
    out = os.path.join(ROOT, "reports", f".review-{date}.md")
    open(out, "w").write(r.stdout)
    sh(["./scripts/publish_review.sh", out, date])
    sh(["./scripts/build_index.sh"])
    print(f"review published: results:evaluations/{date}-review.md")


def cmd_publish():
    sh(["git", "push", "origin", "results"])
    print("pushed results branch (site updates via GitHub Pages)")


# ---------- menu ----------

def ask(prompt, default=""):
    try:
        v = input(prompt).strip()
    except EOFError:
        sys.exit(0)
    return v or default


def pick_entries(entries):
    print("\nmodels (from models.txt):")
    for i, (r, m, l) in enumerate(entries, 1):
        print(f"  {i:2}) {l:28} [{r}]")
    sel = ask("select (numbers/labels, comma-separated; empty = all): ")
    if not sel:
        return entries
    wanted = []
    for tok in sel.split(","):
        tok = tok.strip()
        if tok.isdigit() and 1 <= int(tok) <= len(entries):
            wanted.append(entries[int(tok) - 1][2])
        else:
            wanted.append(tok)
    return match_entries(entries, wanted)


def pick_projects():
    projs = all_projects()
    print("\nprojects:")
    for i, p in enumerate(projs, 1):
        print(f"  {i:2}) {p}")
    sel = ask("select (numbers/names, comma-separated; empty = all): ")
    if not sel:
        return projs
    wanted = []
    for tok in sel.split(","):
        tok = tok.strip()
        if tok.isdigit() and 1 <= int(tok) <= len(projs):
            wanted.append(projs[int(tok) - 1])
        else:
            wanted.append(tok)
    return match_projects(wanted)


def menu():
    entries = parse_models()
    today = datetime.date.today().isoformat()
    while True:
        print("\n=== benchmark matrix ===")
        print(" 1) run        solve + grade a models x projects slice")
        print(" 2) grade      re-grade existing model branches")
        print(" 3) status     pass/fail matrix from reports/")
        print(" 4) summarize  combined leaderboard")
        print(" 5) evaluate   snapshot + evaluation md/html + index")
        print(" 6) analyze    LLM run review (re-run to re-analyze)")
        print(" 7) publish    push results branch")
        print(" 8) pipeline   run everything -> evaluate -> analyze -> publish")
        print(" q) quit")
        c = ask("> ").lower()
        if c in ("q", "quit", ""):
            return
        elif c == "1":
            es = pick_entries(entries)
            ps = pick_projects()
            fresh = (len(ps) < len(all_projects())
                     and ask("fresh branches (re-solve from seed)? [y/N]: ").lower() == "y")
            cmd_run(es, ps, fresh)
        elif c == "2":
            cmd_grade(pick_entries(entries))
        elif c == "3":
            cmd_status()
        elif c == "4":
            cmd_summarize()
        elif c == "5":
            cmd_evaluate(ask(f"date [{today}]: ", today))
        elif c == "6":
            cmd_analyze(ask(f"date [{today}]: ", today))
        elif c == "7":
            cmd_publish()
        elif c == "8":
            cmd_run(entries, all_projects(), fresh=False)
            cmd_evaluate(today)
            cmd_analyze(today)
            cmd_publish()


# ---------- cli ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    for name in ("run", "grade"):
        p = sub.add_parser(name)
        p.add_argument("-m", "--model", action="append", default=[])
        if name == "run":
            p.add_argument("-p", "--project", action="append", default=[])
            p.add_argument("--fresh", action="store_true",
                           help="reset branches instead of resuming")
    sub.add_parser("status")
    sub.add_parser("summarize")
    for name in ("evaluate", "analyze"):
        p = sub.add_parser(name)
        p.add_argument("date", nargs="?",
                       default=datetime.date.today().isoformat())
    sub.add_parser("publish")
    sub.add_parser("pipeline")
    args = ap.parse_args()

    os.chdir(ROOT)
    if not args.cmd:
        menu()
    elif args.cmd == "run":
        cmd_run(match_entries(parse_models(), args.model),
                match_projects(args.project), args.fresh)
    elif args.cmd == "grade":
        cmd_grade(match_entries(parse_models(), args.model))
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "summarize":
        cmd_summarize()
    elif args.cmd == "evaluate":
        cmd_evaluate(args.date)
    elif args.cmd == "analyze":
        cmd_analyze(args.date)
    elif args.cmd == "publish":
        cmd_publish()
    elif args.cmd == "pipeline":
        today = datetime.date.today().isoformat()
        cmd_run(parse_models(), all_projects(), fresh=False)
        cmd_evaluate(today)
        cmd_analyze(today)
        cmd_publish()


if __name__ == "__main__":
    main()
