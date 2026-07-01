#!/usr/bin/env bash
# Build/refresh index.html on the results branch — a landing page linking every
# run (combined HTML evaluation + markdown snapshot). Committed via git plumbing
# so the working tree / current branch are never touched. Intended as the
# GitHub Pages home for the results branch.
set -uo pipefail
cd "$(dirname "$0")/.."

BRANCH="${EVAL_BRANCH:-results}"
REPO_URL="${REPO_URL:-https://github.com/epatel/model-benchmark}"

git rev-parse --verify -q "refs/heads/$BRANCH" >/dev/null || { echo "no $BRANCH branch"; exit 1; }
files="$(git ls-tree -r --name-only "$BRANCH")"
dates="$(echo "$files" | grep -E '^evaluations/.*\.html$' | sed -E 's#evaluations/(.*)\.html#\1#' | sort -ru)"

TMP="$(mktemp)"
{
  cat <<'HTML'
<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Model Benchmark — runs</title>
<style>
:root{color-scheme:light dark}
body{font:16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;max-width:760px;margin:48px auto;padding:0 20px}
h1{margin:0 0 4px}.sub{color:#888;margin-bottom:28px}
ul{list-style:none;padding:0}
li{border:1px solid #8883;border-radius:8px;padding:14px 16px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.date{font-weight:600;font-size:17px}
a{color:#2f81f7;text-decoration:none}a:hover{text-decoration:underline}
.links a{margin-left:14px}
footer{color:#888;margin-top:32px;font-size:13px}
</style></head><body>
<h1>Model Benchmark — runs</h1>
<div class=sub>Coding-task benchmark for AI models (Claude + Ollama). Each run:
pass/fail per task, a leaderboard (time/tokens/cost), and side-by-side solution diffs.</div>
<ul>
HTML
  if [ -z "$dates" ]; then
    echo "<li>No runs yet.</li>"
  else
    for d in $dates; do
      echo "<li><span class=date>$d</span><span class=links>"
      echo "<a href=\"evaluations/$d.html\">combined evaluation &rarr;</a>"
      echo "<a href=\"$REPO_URL/blob/$BRANCH/runs/$d.md\">snapshot</a>"
      echo "</span></li>"
    done
  fi
  cat <<HTML
</ul>
<footer>Source: <a href="$REPO_URL">$REPO_URL</a> · pages served from the <code>$BRANCH</code> branch.</footer>
</body></html>
HTML
} > "$TMP"

blob="$(git hash-object -w "$TMP")"
idx="$(mktemp -u)"; export GIT_INDEX_FILE="$idx"
git read-tree "$BRANCH"
git update-index --add --cacheinfo "100644,$blob,index.html"
tree="$(git write-tree)"
commit="$(git commit-tree "$tree" -p "$(git rev-parse "$BRANCH")" -m "index: refresh runs landing page")"
git update-ref "refs/heads/$BRANCH" "$commit"
unset GIT_INDEX_FILE; rm -f "$idx" "$TMP"

echo "index.html -> branch '$BRANCH' ($(git rev-parse --short "$commit")); $(echo "$dates" | wc -w | tr -d ' ') run(s) linked"
