#!/usr/bin/env bash
# Publish an LLM analysis/review of a run to the results branch as
# evaluations/<date>-review.md (git plumbing; working tree / current branch
# untouched). Pair with scripts/analyze_run.sh which generates the review.
#
#   scripts/analyze_run.sh | claude -p - > review.md
#   scripts/publish_review.sh review.md 2026-07-01
set -euo pipefail
cd "$(dirname "$0")/.."

FILE="${1:?usage: publish_review.sh <review-file> [date]}"
[ -f "$FILE" ] || { echo "no such file: $FILE"; exit 1; }
BRANCH="${EVAL_BRANCH:-results}"
DATE="${2:-$(date +%F)}"
REL="evaluations/$DATE-review.md"

git rev-parse --verify -q "refs/heads/$BRANCH" >/dev/null || { echo "no $BRANCH branch"; exit 1; }

blob="$(git hash-object -w "$FILE")"
idx="$(mktemp -u)"; export GIT_INDEX_FILE="$idx"
git read-tree "$BRANCH"
git update-index --add --cacheinfo "100644,$blob,$REL"
tree="$(git write-tree)"
commit="$(git commit-tree "$tree" -p "$(git rev-parse "$BRANCH")" -m "review $DATE")"
git update-ref "refs/heads/$BRANCH" "$commit"
unset GIT_INDEX_FILE; rm -f "$idx"

echo "review -> $BRANCH:$REL ($(git rev-parse --short "$commit"))"
echo "refresh the landing page:  ./scripts/build_index.sh"
