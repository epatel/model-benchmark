#!/usr/bin/env bash
# Run EVERY model listed in models.txt (both runners), then print the combined
# leaderboard. This is the top-level entry point.
#
# (Not to be confused with scripts/run_all.sh, which runs the 8 project TESTS
#  during grading.)
#
#   ./run_all.sh                 # use models.txt
#   ./run_all.sh my-models.txt   # use a different list
#   DRY=1 ./run_all.sh           # just print the plan, run nothing
set -uo pipefail
cd "$(dirname "$0")"

CONF="${1:-models.txt}"
[ -f "$CONF" ] || { echo "no such model list: $CONF"; exit 1; }

claude_models=()
ollama_models=()
while read -r runner model _rest; do
  [ -z "${runner:-}" ] && continue
  case "$runner" in
    \#*) continue ;;
    claude) claude_models+=("$model") ;;
    ollama) ollama_models+=("$model") ;;
    *) echo "warning: unknown runner '$runner' (model '$model') — skipped" ;;
  esac
done < "$CONF"

if [ ${#ollama_models[@]} -gt 0 ]; then echo "ollama: ${ollama_models[*]}"; else echo "ollama: (none)"; fi
if [ ${#claude_models[@]} -gt 0 ]; then echo "claude: ${claude_models[*]}"; else echo "claude: (none)"; fi

if [ -n "${DRY:-}" ]; then
  echo "(dry run — nothing executed)"
  exit 0
fi

# Sequential: the two runners share the git repo and must not overlap.
if [ ${#ollama_models[@]} -gt 0 ]; then ./run_ollama.sh "${ollama_models[@]}"; fi
if [ ${#claude_models[@]} -gt 0 ]; then ./run_models.sh "${claude_models[@]}"; fi

echo "============================================================"
echo "COMBINED LEADERBOARD"
echo "============================================================"
python3 scripts/summarize.py
echo
echo "Tip: snapshot this run with  ./scripts/snapshot.sh"
