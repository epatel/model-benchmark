#!/usr/bin/env bash
# Optional HTML version of the combined evaluation: real tables + side-by-side
# diffs. Writes evaluations/<date>.html to the results branch via git plumbing
# (working tree / current branch never touched).
#
#   ./scripts/evaluate_html.sh              # today's date
#   ./scripts/evaluate_html.sh 2026-07-01   # explicit date/label
#   EVAL_BRANCH=results ./scripts/evaluate_html.sh
set -uo pipefail
cd "$(dirname "$0")/.."

DATE="${1:-$(date +%F)}"
BRANCH="${EVAL_BRANCH:-results}"
REL="evaluations/$DATE.html"

ls reports/*.results.json >/dev/null 2>&1 || { echo "no reports/ to evaluate"; exit 1; }

TMP="$(mktemp)"
python3 scripts/report_html.py "$DATE" > "$TMP"

blob="$(git hash-object -w "$TMP")"
idx="$(mktemp -u)"; export GIT_INDEX_FILE="$idx"
parent=""
if git rev-parse --verify -q "refs/heads/$BRANCH" >/dev/null; then
  parent="$(git rev-parse "refs/heads/$BRANCH")"; git read-tree "$BRANCH"
fi
git update-index --add --cacheinfo "100644,$blob,$REL"
tree="$(git write-tree)"
if [ -n "$parent" ]; then
  commit="$(git commit-tree "$tree" -p "$parent" -m "evaluation (html) $DATE")"
else
  commit="$(git commit-tree "$tree" -m "evaluation (html) $DATE")"
fi
git update-ref "refs/heads/$BRANCH" "$commit"
unset GIT_INDEX_FILE; rm -f "$idx" "$TMP"

echo "html evaluation: $REL -> branch '$BRANCH' ($(git rev-parse --short "$commit"))"
echo "open:  git show $BRANCH:$REL > /tmp/eval.html && open /tmp/eval.html"
