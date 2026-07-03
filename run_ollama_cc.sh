#!/usr/bin/env bash
# Agentic Ollama runner: drive Ollama models through the SAME `claude` CLI
# harness as the Claude models, via Ollama's Anthropic-compatible endpoint
# (https://docs.ollama.com/api/anthropic-compatibility). This removes the
# one-shot-adapter asymmetry: the model reads TASK.md itself, explores, and
# edits files with real tools over multiple turns.
#
#   ./run_ollama_cc.sh glm-5.2:cloud qwen3-coder ...
#
# Labels get a `-cc` suffix (e.g. glm-5.2_cloud-cc) so results never collide
# with the one-shot adapter runs of the same model.
#
# Caveats vs the native Claude runner:
#   - cost_usd is zeroed (the CLI prices unknown models with bogus numbers;
#     Ollama reports no pricing)
#   - no prompt caching: cache_read/cache_creation are 0 and input_tokens is
#     all-fresh — compare input against Claude's fresh (input+cache_creation),
#     as with the one-shot runner.
set -uo pipefail
cd "$(dirname "$0")"

MODELS=("$@")
[ ${#MODELS[@]} -eq 0 ] && { echo "usage: run_ollama_cc.sh <model> [model...]"; exit 1; }

export ANTHROPIC_BASE_URL="${OLLAMA_URL:-http://localhost:11434}"
export ANTHROPIC_AUTH_TOKEN=ollama

PROMPT='Read the file TASK.md in the current directory and make the code change it describes. Edit the source file(s) directly. Do NOT modify any test file (test_*, *_test.go, *.test.js) or run_tests.sh. Make the smallest change that satisfies the task. Do not run git or commit; just leave the edited files in place.'

for model in "${MODELS[@]}"; do
  label="$(echo "$model" | tr ':/' '_')-cc"
  echo "============================================================"
  echo "OLLAMA-CC MODEL: $model   (label: $label)"
  echo "============================================================"
  ./bench.sh start "$label" >/dev/null
  mkdir -p "reports/$label.logs"

  for proj in projects/*/; do
    proj="${proj%/}"
    name="$(basename "$proj")"
    echo "  -> $model (agentic) solving $name ..."
    ( cd "$proj" && command claude --model "$model" -p "$PROMPT" \
        --dangerously-skip-permissions --output-format json ) \
      >"reports/$label.logs/$name.json" 2>>"reports/$label.logs/stderr.log" \
      || echo "     (claude exited non-zero on $name; see reports/$label.logs/$name.json)"
  done

  python3 scripts/usage.py "$label"
  # The CLI prices unknown models with fictitious numbers — zero them out.
  python3 - "$label" <<'EOF'
import json, sys
p = f"reports/{sys.argv[1]}.usage.json"
u = json.load(open(p))
u["cost_usd"] = 0.0
for v in u.get("by_project", {}).values():
    if isinstance(v, dict) and "cost_usd" in v:
        v["cost_usd"] = 0.0
json.dump(u, open(p, "w"), indent=1)
EOF

  echo "  -> grading $label"
  ./bench.sh grade "$label"
  echo
done

echo "============================================================"
echo "SUMMARY"
echo "============================================================"
python3 scripts/summarize.py
