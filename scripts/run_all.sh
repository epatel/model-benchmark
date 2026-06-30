#!/usr/bin/env bash
# Run every project's tests and write results.json with pass/fail + duration.
# Usage: scripts/run_all.sh
set -uo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

results="results.json"
echo "[" > "$results"
first=1
overall=0

for dir in projects/*/; do
  dir="${dir%/}"
  name="$(basename "$dir")"
  [[ -f "$dir/run_tests.sh" ]] || continue

  start=$(date +%s)
  out="$(bash "$dir/run_tests.sh" 2>&1)"
  code=$?
  end=$(date +%s)
  dur=$((end - start))

  if [[ $code -eq 0 ]]; then
    status="pass"; echo "PASS  $name  (${dur}s)"
  else
    status="fail"; overall=1
    echo "FAIL  $name  (${dur}s, exit $code)"
  fi

  [[ $first -eq 0 ]] && echo "," >> "$results"
  first=0
  printf '  {"project": "%s", "status": "%s", "exit": %d, "seconds": %d}' \
    "$name" "$status" "$code" "$dur" >> "$results"
done

echo "" >> "$results"
echo "]" >> "$results"
echo "wrote $root/$results"
exit $overall
