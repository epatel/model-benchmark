#!/usr/bin/env python3
"""Solve one benchmark task with a (non-agentic) OpenAI model.

Same shape as ollama_solve.py (whose prompt/parse helpers it reuses):
  1. reads TASK.md + the editable source files of a project,
  2. asks the model to return the full updated contents of any file it changes,
  3. writes those files back (source files only — never tests),
  4. emits a usage log in the same schema as `claude --output-format json`
     (so scripts/usage.py + summarize.py aggregate it unchanged).

Uses the Responses API (required for gpt-5.6; recommended for all gpt-5.x).

Usage: openai_solve.py <model> <project_dir> <usage_log_path>
Env:   OPENAI_API_KEY (required)
       OPENAI_URL     (default https://api.openai.com/v1)
       OPENAI_TIMEOUT (default 900)
       OPENAI_EFFORT  reasoning effort (e.g. low/medium/high; default: model's
                      own default, medium on gpt-5.x — pin it for fair
                      cross-run comparisons)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

from ollama_solve import build_prompt, parse_files, source_files

URL = os.environ.get("OPENAI_URL", "https://api.openai.com/v1")
TIMEOUT = float(os.environ.get("OPENAI_TIMEOUT", "900"))
EFFORT = os.environ.get("OPENAI_EFFORT", "")


def chat(model, prompt, retries=2):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set")
    # No temperature: gpt-5.x models only accept the default.
    payload = {"model": model, "input": prompt}
    if EFFORT:
        payload["reasoning"] = {"effort": EFFORT}
    body = json.dumps(payload).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            URL + "/responses", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            if attempt == retries or e.code < 500 and e.code != 429:
                sys.exit(f"OpenAI API error {e.code}: {detail}")
            print(f"    (attempt {attempt + 1} failed: {e.code} — retrying)",
                  file=sys.stderr)
        except (TimeoutError, OSError) as e:
            if attempt == retries:
                raise
            print(f"    (attempt {attempt + 1} failed: {e} — retrying)",
                  file=sys.stderr)
        time.sleep(5 * (attempt + 1))


def output_text(resp):
    """Concatenate all output_text parts from a Responses API result."""
    parts = []
    for item in resp.get("output") or []:
        if item.get("type") != "message":
            continue
        for c in item.get("content") or []:
            if c.get("type") == "output_text":
                parts.append(c.get("text", ""))
    return "".join(parts)


def write_usage(path, resp, dur_ms):
    u = resp.get("usage", {}) or {}
    cached = (u.get("input_tokens_details") or {}).get("cached_tokens", 0)
    usage = {
        "duration_ms": dur_ms,
        "num_turns": 1,
        "total_cost_usd": 0.0,
        "usage": {
            "input_tokens": u.get("input_tokens", 0) - cached,
            "output_tokens": u.get("output_tokens", 0),
            "cache_read_input_tokens": cached,
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
    t0 = time.monotonic()
    resp = chat(model, prompt)
    write_usage(usage_log, resp, int((time.monotonic() - t0) * 1000))

    if resp.get("status") not in (None, "completed"):
        print(f"  !! response status {resp.get('status')}: "
              f"{(resp.get('incomplete_details') or {}).get('reason', '')}")
    content = output_text(resp)
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
