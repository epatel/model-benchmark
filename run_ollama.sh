#!/usr/bin/env bash
# Umbrella runner for Ollama models (local or :cloud). Same grading + reports as
# run_models.sh, but the "solve" step uses scripts/ollama_solve.py (Ollama models
# are not agentic, so the adapter feeds them the task and writes back their edits).
#
#   ./run_ollama.sh                       # default: glm-5.2:cloud
#   ./run_ollama.sh glm-5.2:cloud kimi-k2.5:cloud
#   ./run_ollama.sh llama3.1            # a local model
#
# Env: OLLAMA_URL (default http://localhost:11434)
set -uo pipefail
cd "$(dirname "$0")"

MODELS=("$@")
[ ${#MODELS[@]} -eq 0 ] && MODELS=(glm-5.2:cloud)

for model in "${MODELS[@]}"; do
  # branch/report label: ':' and '/' are awkward in git refs
  label="$(printf '%s' "$model" | tr ':/ ' '___')"
  echo "============================================================"
  echo "OLLAMA MODEL: $model   (label: $label)"
  echo "============================================================"
  ./bench.sh start "$label" >/dev/null
  mkdir -p "reports/$label.logs"

  for proj in projects/*/; do
    proj="${proj%/}"
    name="$(basename "$proj")"
    echo "  -> $model solving $name ..."
    python3 scripts/ollama_solve.py "$model" "$proj" "reports/$label.logs/$name.json" \
      2>&1 | tee "reports/$label.logs/$name.txt" \
      || echo "     (solve failed on $name; see reports/$label.logs/$name.txt)"
  done

  python3 scripts/usage.py "$label"
  echo "  -> grading $label"
  ./bench.sh grade "$label"
  echo
done

echo "============================================================"
echo "SUMMARY"
echo "============================================================"
python3 scripts/summarize.py
