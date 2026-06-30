#!/usr/bin/env bash
# Umbrella runner: for each model, solve every task with headless `claude`,
# then grade. Produces reports/<model>.* and a comparison table.
#
#   ./run_models.sh                       # default models: haiku sonnet opus
#   ./run_models.sh sonnet opus           # explicit list
#   ./run_models.sh claude-sonnet-5       # full model ids work too
#
# Each model gets its own model/<model> branch (cut from base). For every
# projects/* dir we cd in and run `claude -p` scoped to that directory, so it
# only sees that one task (TASK.md + source). Answers (SOLUTION.md, hidden
# tests) are not on the branch, so the model cannot see them. bench.sh grade
# auto-commits the edits, applies the hidden tests, and runs every oracle.
set -uo pipefail
cd "$(dirname "$0")"

MODELS=("$@")
[ ${#MODELS[@]} -eq 0 ] && MODELS=(haiku sonnet opus)

PROMPT='Read the file TASK.md in the current directory and make the code change it describes. Edit the source file(s) directly. Do NOT modify any test file (test_*, *_test.go, *.test.js) or run_tests.sh. Make the smallest change that satisfies the task. Do not run git or commit; just leave the edited files in place.'

for model in "${MODELS[@]}"; do
  echo "============================================================"
  echo "MODEL: $model"
  echo "============================================================"
  ./bench.sh start "$model" >/dev/null
  mkdir -p "reports/$model.logs"

  for proj in projects/*/; do
    proj="${proj%/}"
    name="$(basename "$proj")"
    echo "  -> $model solving $name ..."
    ( cd "$proj" && claude --model "$model" -p "$PROMPT" --dangerously-skip-permissions ) \
      >"reports/$model.logs/$name.log" 2>&1 \
      || echo "     (claude exited non-zero on $name; see reports/$model.logs/$name.log)"
  done

  echo "  -> grading $model"
  ./bench.sh grade "$model"
  echo
done

echo "============================================================"
echo "SUMMARY"
echo "============================================================"
python3 scripts/summarize.py
