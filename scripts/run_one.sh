#!/usr/bin/env bash
# Run one project's tests (visible + hidden) and report pass/fail + duration.
# Usage: scripts/run_one.sh projects/01-lru-cache
set -uo pipefail

dir="${1:?usage: run_one.sh <project-dir>}"
dir="${dir%/}"
name="$(basename "$dir")"

if [[ ! -x "$dir/run_tests.sh" && ! -f "$dir/run_tests.sh" ]]; then
  echo "FAIL  $name  (no run_tests.sh)"
  exit 2
fi

start=$(date +%s)
out="$(bash "$dir/run_tests.sh" 2>&1)"
code=$?
end=$(date +%s)
dur=$((end - start))

if [[ $code -eq 0 ]]; then
  echo "PASS  $name  (${dur}s)"
else
  echo "FAIL  $name  (${dur}s, exit $code)"
  echo "----- output -----"
  echo "$out" | tail -n 30
  echo "------------------"
fi
exit $code
