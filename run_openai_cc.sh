#!/usr/bin/env bash
# Agentic OpenAI runner: drive OpenAI models through the SAME `claude` CLI
# harness as the Claude models. OpenAI has no Anthropic-compatible endpoint
# (unlike Ollama), so this runner starts a local LiteLLM proxy that speaks
# Anthropic /v1/messages on the front and the OpenAI API on the back.
#
#   ./run_openai_cc.sh gpt-5.5 gpt-5.4 ...
#
# Labels get a `-cc` suffix (e.g. gpt-5.5-cc) so results never collide with
# the one-shot adapter runs of the same model (run_openai.sh).
#
# Env: OPENAI_API_KEY (required), LITELLM_PORT (default 4141)
# Needs litellm on PATH, or uv (the proxy is then run via uvx).
#
# Caveats vs the native Claude runner (same as run_ollama_cc.sh, plus one):
#   - cost_usd is zeroed (the CLI prices unknown models with bogus numbers)
#   - no prompt caching: cache_read/cache_creation are 0 and input_tokens is
#     all-fresh — compare input against Claude's fresh (input+cache_creation)
#   - tool calls cross an Anthropic->OpenAI schema translation (LiteLLM), so
#     results measure the model THROUGH that bridge, not its native harness
set -uo pipefail
cd "$(dirname "$0")"

[ -n "${OPENAI_API_KEY:-}" ] || { echo "OPENAI_API_KEY is not set"; exit 1; }

MODELS=("$@")
[ ${#MODELS[@]} -eq 0 ] && { echo "usage: run_openai_cc.sh <model> [model...]"; exit 1; }

if command -v litellm >/dev/null 2>&1; then
  LITELLM=(litellm)
elif command -v uvx >/dev/null 2>&1; then
  LITELLM=(uvx --from 'litellm[proxy]' litellm)
else
  echo "need litellm on PATH or uv installed (brew install uv)"; exit 1
fi

PORT="${LITELLM_PORT:-4141}"
CFG="$(mktemp -t litellm-cfg-XXXXXX)"
{
  echo "model_list:"
  for m in "${MODELS[@]}"; do
    printf -- '  - model_name: %s\n    litellm_params:\n      model: openai/%s\n      api_key: os.environ/OPENAI_API_KEY\n' "$m" "$m"
  done
} > "$CFG"

mkdir -p reports
echo "starting litellm proxy on :$PORT (log: reports/litellm.log)"
"${LITELLM[@]}" --config "$CFG" --port "$PORT" >reports/litellm.log 2>&1 &
PROXY_PID=$!
trap 'kill "$PROXY_PID" 2>/dev/null; rm -f "$CFG"' EXIT

for i in $(seq 1 90); do
  curl -sf "http://localhost:$PORT/health/liveliness" >/dev/null 2>&1 && break
  kill -0 "$PROXY_PID" 2>/dev/null || { echo "litellm died; see reports/litellm.log"; exit 1; }
  sleep 1
  [ "$i" -eq 90 ] && { echo "litellm never became healthy; see reports/litellm.log"; exit 1; }
done

export ANTHROPIC_BASE_URL="http://localhost:$PORT"
export ANTHROPIC_AUTH_TOKEN=litellm

PROMPT='Read the file TASK.md in the current directory and make the code change it describes. Edit the source file(s) directly. Do NOT modify any test file (test_*, *_test.go, *.test.js) or run_tests.sh. Make the smallest change that satisfies the task. Do not run git or commit; just leave the edited files in place.'

for model in "${MODELS[@]}"; do
  label="$(echo "$model" | tr ':/' '_')-cc"
  echo "============================================================"
  echo "OPENAI-CC MODEL: $model   (label: $label)"
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
