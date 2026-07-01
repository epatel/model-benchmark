#!/usr/bin/env bash
# Emit a self-contained analysis input = the reusable prompt + this run's data
# (leaderboard, reproduced failures, per-task diffs, and raw usage JSON for
# token normalization). Pipe it to a model, or paste it.
#
#   ./scripts/analyze_run.sh                 # latest run on the results branch
#   ./scripts/analyze_run.sh 2026-07-01      # a specific run
#   ./scripts/analyze_run.sh | claude -p -   # analyze with Claude (stdin)
#   claude -p "$(./scripts/analyze_run.sh)"  # or as an argument
#   ./scripts/analyze_run.sh | pbcopy        # copy to clipboard (macOS)
set -euo pipefail
cd "$(dirname "$0")/.."

BRANCH="${EVAL_BRANCH:-results}"
DATE="${1:-}"
if [ -z "$DATE" ]; then
  DATE="$(git ls-tree -r --name-only "$BRANCH" 2>/dev/null \
          | grep -E '^evaluations/.*\.md$' | sed -E 's#evaluations/(.*)\.md#\1#' \
          | sort -r | head -1)"
fi
[ -n "$DATE" ] || { echo "no evaluations/*.md on branch '$BRANCH' — run scripts/evaluate.sh first" >&2; exit 1; }

cat prompts/analyze-run.md
echo
echo "==================== RUN DATA ($DATE) ===================="
echo "n_tasks = $(ls -d projects/*/ | wc -l | tr -d ' ')"
echo
echo "### Combined evaluation (leaderboard + failures + per-task diffs)"
echo
git show "$BRANCH:evaluations/$DATE.md"
echo
echo "### Raw per-model usage JSON (for token/cost normalization)"
echo '```json'
for u in reports/*.usage.json; do
  [ -e "$u" ] || continue
  m="$(basename "$u" .usage.json)"
  echo "$m: $(cat "$u")"
done
echo '```'
