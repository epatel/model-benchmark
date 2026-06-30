#!/usr/bin/env bash
# Git-based benchmark harness.
#
#   bench.sh start <model>   create a clean task branch model/<model> from base
#   bench.sh grade <model>   apply hidden tests onto the model's work, run all tests
#   bench.sh list            list model/ and grade/ branches
#   bench.sh clean <model>   delete model/<model> and grade/<model>
#
# Branch model:
#   base     -> tasks with seeded defects + visible tests (what the model sees)
#   grading  -> base + ONE additive commit: hidden tests + SOLUTION.md
#   model/X  -> base + model X's edits
#   grade/X  -> model/X + cherry-picked grading commit (disposable, for scoring)
set -euo pipefail
cd "$(dirname "$0")"

BASE=base
GRADING=grading

# Restored from base before grading so a model can't tamper with the harness or
# the visible tests to fake a pass. (Hidden tests come from the grading commit.)
CANON=(
  scripts/run_all.sh scripts/run_one.sh
  projects/01-lru-cache/run_tests.sh   projects/01-lru-cache/test_lru.py
  projects/02-bank-ledger/run_tests.sh projects/02-bank-ledger/ledger_test.go
  projects/03-csv-parser/run_tests.sh  projects/03-csv-parser/test_parser.py
  projects/04-rest-pagination/run_tests.sh projects/04-rest-pagination/api.test.js
  projects/05-god-refactor/run_tests.sh projects/05-god-refactor/test_pricing.py
)

cmd="${1:-help}"; shift || true

case "$cmd" in
  start)
    m="${1:?usage: bench.sh start <model>}"
    git checkout -q "$BASE"
    git checkout -B "model/$m" >/dev/null
    echo "On branch model/$m (clean task state)."
    echo "Let the model edit files, then: bench.sh grade $m"
    ;;

  grade)
    m="${1:?usage: bench.sh grade <model>}"
    git rev-parse --verify -q "refs/heads/model/$m" >/dev/null \
      || { echo "no branch model/$m (run: bench.sh start $m)"; exit 1; }

    # Commit any pending model edits so they are included.
    git checkout -q "model/$m"
    git add -A
    git commit -q -m "model work: $m" 2>/dev/null || true

    # Disposable grading branch = model work + hidden tests.
    git checkout -B "grade/$m" "model/$m" >/dev/null
    git cherry-pick "$GRADING" >/dev/null

    # Anti-tamper: restore canonical harness + visible tests from base.
    git checkout "$BASE" -- "${CANON[@]}"
    chmod +x bench.sh scripts/*.sh projects/*/run_tests.sh 2>/dev/null || true

    mkdir -p reports
    set +e
    ./scripts/run_all.sh | tee "reports/$m.txt"
    rc=$?
    set -e
    [[ -f results.json ]] && cp -f results.json "reports/$m.results.json"

    git checkout -q "$BASE"
    echo "Graded model/$m -> reports/$m.txt (overall exit $rc)"
    ;;

  list)
    git for-each-ref --format='%(refname:short)' refs/heads \
      | grep -E '^(model|grade)/' || echo "(no model branches yet)"
    ;;

  clean)
    m="${1:?usage: bench.sh clean <model>}"
    git checkout -q "$BASE"
    git branch -D "model/$m" "grade/$m" 2>/dev/null || true
    echo "removed model/$m and grade/$m"
    ;;

  *)
    sed -n '2,9p' "$0"
    ;;
esac
