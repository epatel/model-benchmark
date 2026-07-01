#!/usr/bin/env bash
# Consolidate all model/* branches + reports into ONE combined evaluation doc:
# leaderboard, failure detail, and every model's per-task diff vs the clean
# branch. Written to evaluations/<date>.md on the results branch (git plumbing,
# so the working tree / current branch are never touched).
#
#   ./scripts/evaluate.sh              # today's date
#   ./scripts/evaluate.sh 2026-07-01   # explicit date/label
#   EVAL_BRANCH=results ./scripts/evaluate.sh
set -uo pipefail
cd "$(dirname "$0")/.."

DATE="${1:-$(date +%F)}"
BRANCH="${EVAL_BRANCH:-results}"
REL="evaluations/$DATE.md"

if git rev-parse --verify -q main >/dev/null; then BASE=main; else BASE=base; fi

models=$(ls reports/*.results.json 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/\.results\.json$//')
[ -n "$models" ] || { echo "no reports/ to evaluate"; exit 1; }
projects=$(ls -d projects/*/ | sed 's#projects/##; s#/##' | sort)

status_of() { python3 -c "import json,sys; r=json.load(open('reports/$1.results.json')); print(next((x['status'] for x in r if x['project']=='$2'),'?'))"; }
fails_of()  { python3 -c "import json;   r=json.load(open('reports/$1.results.json')); print(' '.join(x['project'] for x in r if x['status']!='pass'))"; }

TMP="$(mktemp)"
{
  echo "# Combined evaluation — $DATE"
  echo
  echo "$(echo "$models" | wc -w | tr -d ' ') models × $(echo "$projects" | wc -w | tr -d ' ') tasks. Grading = hidden-test oracle; diffs are each model's edits vs \`$BASE\`."
  echo
  echo "## Leaderboard"
  echo
  echo '```'
  python3 scripts/summarize.py
  echo '```'
  echo
  echo "## Failure detail"
  echo
  anyfail=0
  for m in $models; do
    for t in $(fails_of "$m"); do
      anyfail=1
      echo "### $m — $t"
      echo '```'
      wt="$(mktemp -d)"
      if git worktree add -q --detach "$wt" "grade/$m" 2>/dev/null; then
        ( cd "$wt" && bash "projects/$t/run_tests.sh" 2>&1 \
          | grep -iE 'fail|error|assert|expected|want|got|deadlock|Traceback|!=' | head -12 )
        git worktree remove --force "$wt" 2>/dev/null || true
      else
        echo "(no grade/$m branch — cannot reproduce)"; rm -rf "$wt"
      fi
      echo '```'
      echo
    done
  done
  [ "$anyfail" = 0 ] && echo "None — every model passed every task. 🎉"
  echo
  echo "## Solutions by task"
  for t in $projects; do
    echo
    echo "### $t"
    for m in $models; do
      git rev-parse --verify -q "model/$m" >/dev/null || continue
      diff="$(git diff "$BASE" "model/$m" -- "projects/$t")"
      [ -n "$diff" ] || continue
      st="$(status_of "$m" "$t" | tr '[:lower:]' '[:upper:]')"
      echo
      echo "#### $m — $st"
      echo '```diff'
      echo "$diff"
      echo '```'
    done
  done
} > "$TMP"

# --- commit to the results branch via plumbing (no checkout) ---
blob="$(git hash-object -w "$TMP")"
idx="$(mktemp -u)"; export GIT_INDEX_FILE="$idx"
parent=""
if git rev-parse --verify -q "refs/heads/$BRANCH" >/dev/null; then
  parent="$(git rev-parse "refs/heads/$BRANCH")"; git read-tree "$BRANCH"
fi
git update-index --add --cacheinfo "100644,$blob,$REL"
tree="$(git write-tree)"
if [ -n "$parent" ]; then
  commit="$(git commit-tree "$tree" -p "$parent" -m "evaluation $DATE")"
else
  commit="$(git commit-tree "$tree" -m "evaluation $DATE")"
fi
git update-ref "refs/heads/$BRANCH" "$commit"
unset GIT_INDEX_FILE; rm -f "$idx" "$TMP"

echo "evaluation: $REL -> branch '$BRANCH' ($(git rev-parse --short "$commit"))"
echo "view:  git show $BRANCH:$REL"
