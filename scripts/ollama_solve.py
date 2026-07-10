#!/usr/bin/env python3
"""Solve one benchmark task with a (non-agentic) Ollama model.

Ollama models can't edit files themselves, so this adapter:
  1. reads TASK.md + the editable source files of a project,
  2. asks the model to return the full updated contents of any file it changes,
  3. writes those files back (source files only — never tests),
  4. emits a usage log in the same schema as `claude --output-format json`
     (so scripts/usage.py + summarize.py aggregate it unchanged).

Usage: ollama_solve.py <model> <project_dir> <usage_log_path>
Env:   OLLAMA_URL (default http://localhost:11434), OLLAMA_TIMEOUT (default 900)
"""
import json
import os
import re
import sys
import time
import urllib.request

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "900"))

SKIP_EXACT = {"TASK.md", "SOLUTION.md", "run_tests.sh", "go.mod", "go.sum",
              "package.json", "package-lock.json", "README.md"}


def is_source(name):
    if name in SKIP_EXACT:
        return False
    if name.startswith("test_") or name.endswith("_test.go") or name.endswith(".test.js"):
        return False
    if "hidden" in name:
        return False
    if name.startswith(".") or name.endswith(".md"):
        return False
    return True


def source_files(proj):
    return sorted(f for f in os.listdir(proj)
                  if os.path.isfile(os.path.join(proj, f)) and is_source(f))


def build_prompt(proj, files):
    task = open(os.path.join(proj, "TASK.md")).read()
    parts = [
        "You are fixing a small coding task. Read the TASK and the current files, "
        "then output the COMPLETE updated contents of every file you change.",
        "",
        "Output format — for each changed file, and NOTHING else:",
        "<<<FILE: relative-path.ext>>>",
        "full file contents",
        "<<<END>>>",
        "",
        "Do not modify or output any test file. Do not add explanation outside the blocks.",
        "",
        "===== TASK.md =====",
        task,
        "",
        "===== CURRENT FILES =====",
    ]
    for f in files:
        parts += [f"--- {f} ---", open(os.path.join(proj, f)).read(), ""]
    return "\n".join(parts)


def chat(model, prompt, retries=2):
    body = json.dumps({
        "model": model,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    # Cloud calls occasionally stall mid-read; retry a couple of times so a
    # transient hiccup doesn't record a bogus FAIL for an unsolved task.
    for attempt in range(retries + 1):
        req = urllib.request.Request(URL + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.load(r)
        except (TimeoutError, OSError) as e:
            if attempt == retries:
                raise
            print(f"    (attempt {attempt + 1} failed: {e} — retrying)",
                  file=sys.stderr)
            time.sleep(5 * (attempt + 1))


FENCE = re.compile(r"^```[^\n]*\n(.*)\n```$", re.DOTALL)


def strip_fence(s):
    s = s.strip("\n")
    m = FENCE.match(s.strip())
    return m.group(1) if m else s


def parse_files(content, allowed):
    """Return {relpath: new_contents} for whitelisted source files only."""
    out = {}
    for m in re.finditer(r"<<<FILE:\s*(.+?)>>>\n(.*?)\n<<<END>>>", content, re.DOTALL):
        # Models that read the marker template literally emit extra trailing
        # '>' (e.g. "<<<FILE: lru.py>>>>"); the lazy path group keeps them.
        path = m.group(1).strip().rstrip(">").strip().lstrip("./")
        if path in allowed:
            out[path] = strip_fence(m.group(2))
    # Fallback: single-file task, no markers -> take the last fenced block.
    if not out and len(allowed) == 1:
        blocks = re.findall(r"```[^\n]*\n(.*?)\n```", content, re.DOTALL)
        if blocks:
            out[next(iter(allowed))] = blocks[-1]
    return out


def write_usage(path, resp):
    dur_ms = int((resp.get("total_duration") or 0) / 1_000_000)
    usage = {
        "duration_ms": dur_ms,
        "num_turns": 1,
        "total_cost_usd": 0.0,
        "usage": {
            "input_tokens": resp.get("prompt_eval_count", 0),
            "output_tokens": resp.get("eval_count", 0),
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
        },
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(usage, f)


def main():
    model, proj, usage_log = sys.argv[1], sys.argv[2].rstrip("/"), sys.argv[3]
    files = source_files(proj)
    prompt = build_prompt(proj, files)
    resp = chat(model, prompt)
    write_usage(usage_log, resp)

    content = resp.get("message", {}).get("content", "")
    edits = parse_files(content, set(files))
    if not edits:
        print(f"  !! no parseable file edits from {model} for {os.path.basename(proj)}")
        print(content[:400])
        sys.exit(1)
    for rel, body in edits.items():
        with open(os.path.join(proj, rel), "w") as f:
            f.write(body if body.endswith("\n") else body + "\n")
        print(f"  wrote {rel} ({len(body)} bytes)")


if __name__ == "__main__":
    main()
