#!/usr/bin/env bash
# Umbrella runner for OpenAI models. Same grading + reports as run_models.sh,
# but the "solve" step uses scripts/openai_solve.py (one-shot adapter, same
# format as the Ollama one — the model returns whole files, the adapter writes
# them back).
#
#   ./run_openai.sh                       # default: gpt-5.5
#   ./run_openai.sh gpt-5.5 gpt-5.4
#
# Env: OPENAI_API_KEY (required), OPENAI_URL (default https://api.openai.com/v1),
#      OPENAI_EFFORT (pin reasoning effort, e.g. medium; default: model default)
set -uo pipefail
cd "$(dirname "$0")"

[ -n "${OPENAI_API_KEY:-}" ] || { echo "OPENAI_API_KEY is not set"; exit 1; }

MODELS=("$@")
[ ${#MODELS[@]} -eq 0 ] && MODELS=(gpt-5.5)

for model in "${MODELS[@]}"; do
  # branch/report label: ':' and '/' are awkward in git refs
  label="$(printf '%s' "$model" | tr ':/ ' '___')"
  echo "============================================================"
  echo "OPENAI MODEL: $model   (label: $label)"
  echo "============================================================"
  ./bench.sh start "$label" >/dev/null
  mkdir -p "reports/$label.logs"

  for proj in projects/*/; do
    proj="${proj%/}"
    name="$(basename "$proj")"
    echo "  -> $model solving $name ..."
    python3 scripts/openai_solve.py "$model" "$proj" "reports/$label.logs/$name.json" \
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
