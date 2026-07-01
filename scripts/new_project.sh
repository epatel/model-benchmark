#!/usr/bin/env bash
# Scaffold a new benchmark project and (optionally) do the git branch dance.
# See AGENTS.md for the full conventions this automates.
#
#   scripts/new_project.sh scaffold <NN-name> <python|go|node>
#       Create projects/NN-name/ with a valid, both-way-verifiable skeleton
#       (a seeded `double` bug). Edit it into your real task, then:
#
#   scripts/new_project.sh commit <NN-name>
#       Commit source+TASK+visible tests to the clean branch, fold the hidden
#       tests + SOLUTION.md into the single `grading` commit, and add the
#       project's run_tests.sh + visible test to bench.sh CANON (anti-tamper).
#
# After `commit`, verify the oracle BOTH ways (see the printed reminder).
set -uo pipefail
cd "$(dirname "$0")/.."

if [ -n "${BENCH_BASE:-}" ]; then BASE="$BENCH_BASE"
elif git rev-parse --verify -q main >/dev/null; then BASE=main
else BASE=base; fi

die() { echo "error: $*" >&2; exit 1; }

# ---------------------------------------------------------------- scaffold ----
scaffold() {
  local name="$1" lang="${2:-}"
  [[ "$name" =~ ^[0-9]{2}-[a-z0-9-]+$ ]] || die "name must be NN-kebab (e.g. 09-my-task)"
  local dir="projects/$name"
  [ -e "$dir" ] && die "$dir already exists"
  case "$lang" in python|go|node) ;; *) die "lang must be python|go|node" ;; esac
  mkdir -p "$dir"

  cat > "$dir/TASK.md" <<EOF
# Task: <one-line summary> (TODO)

Replace this with the real task. The seeded implementation of \`double\`
returns its input instead of twice its input — fix it so \`double(x)\` returns
\`2 * x\`.

Run the tests with \`run_tests.sh\` (or the command in README).
EOF

  cat > "$dir/SOLUTION.md" <<'EOF'
# Solution (HIDDEN — do not show the model)

Replace with the real solution + why. Reference fix for the skeleton: `double`
should `return 2 * x`.

Reject fake fixes (sleeps, special-casing test inputs, weakening tests).
EOF

  case "$lang" in
    python)
      cat > "$dir/solution.py" <<'EOF'
def double(x):
    """Return twice x. (TODO: replace with the real task.)"""
    return x
EOF
      cat > "$dir/test_solution.py" <<'EOF'
import unittest

from solution import double


class TestSolution(unittest.TestCase):
    def test_double(self):
        self.assertEqual(double(2), 4)


if __name__ == "__main__":
    unittest.main()
EOF
      cat > "$dir/test_solution_hidden.py" <<'EOF'
import unittest

from solution import double


class TestSolutionHidden(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(double(0), 0)

    def test_negative(self):
        self.assertEqual(double(-3), -6)


if __name__ == "__main__":
    unittest.main()
EOF
      cat > "$dir/run_tests.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs every test_*.py present (grading adds the hidden ones).
python3 -m unittest discover -s . -p 'test_*.py'
EOF
      ;;
    go)
      cat > "$dir/go.mod" <<'EOF'
module solution

go 1.21
EOF
      cat > "$dir/solution.go" <<'EOF'
package solution

// Double returns twice x. (TODO: replace with the real task.)
func Double(x int) int {
	return x
}
EOF
      cat > "$dir/solution_test.go" <<'EOF'
package solution

import "testing"

func TestDouble(t *testing.T) {
	if got := Double(2); got != 4 {
		t.Fatalf("Double(2)=%d want 4", got)
	}
}
EOF
      cat > "$dir/solution_hidden_test.go" <<'EOF'
package solution

import "testing"

func TestDoubleHidden(t *testing.T) {
	if Double(0) != 0 || Double(-3) != -6 {
		t.Fatalf("Double(0)=%d Double(-3)=%d", Double(0), Double(-3))
	}
}
EOF
      cat > "$dir/run_tests.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs all *_test.go present (grading adds the hidden ones).
go test -race -count=5 ./...
EOF
      ;;
    node)
      cat > "$dir/solution.js" <<'EOF'
// double(x) returns twice x. (TODO: replace with the real task.)
function double(x) {
  return x;
}
module.exports = { double };
EOF
      cat > "$dir/solution.test.js" <<'EOF'
const test = require("node:test");
const assert = require("node:assert");
const { double } = require("./solution");

test("double", () => {
  assert.equal(double(2), 4);
});
EOF
      cat > "$dir/solution.hidden.test.js" <<'EOF'
const test = require("node:test");
const assert = require("node:assert");
const { double } = require("./solution");

test("double zero/negative", () => {
  assert.equal(double(0), 0);
  assert.equal(double(-3), -6);
});
EOF
      cat > "$dir/run_tests.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Runs all *.test.js present (grading adds the hidden ones).
node --test
EOF
      ;;
  esac

  chmod +x "$dir/run_tests.sh"
  echo "scaffolded $dir ($lang)"
  echo "next:"
  echo "  1. edit the source, TASK.md, visible + hidden tests, SOLUTION.md into your real task"
  echo "  2. scripts/new_project.sh commit $name"
}

# ------------------------------------------------------------------ commit ----
commit() {
  local name="$1"
  local dir="projects/$name"
  [ -d "$dir" ] || die "$dir does not exist (scaffold first)"
  git rev-parse --verify -q "refs/heads/grading" >/dev/null || die "no grading branch"

  # detect the visible test file for CANON (the test file that is not hidden)
  local vis=""
  if ls "$dir"/*.go >/dev/null 2>&1; then
    vis="$(ls "$dir"/*_test.go 2>/dev/null | grep -v hidden | head -1)"
  elif ls "$dir"/*.test.js >/dev/null 2>&1; then
    vis="$(ls "$dir"/*.test.js 2>/dev/null | grep -v hidden | head -1)"
  else
    vis="$(ls "$dir"/test_*.py 2>/dev/null | grep -v hidden | head -1)"
  fi
  [ -n "$vis" ] || die "could not find a visible test file in $dir"
  local rt="$dir/run_tests.sh"

  git checkout -q "$BASE"

  # add run_tests.sh + visible test to bench.sh CANON (anti-tamper)
  python3 - "$rt" "$vis" <<'PY'
import re, sys
rt, vis = sys.argv[1], sys.argv[2]
p = "bench.sh"; s = open(p).read()
m = re.search(r'CANON=\(\n(.*?)\n\)', s, re.S)
if not m:
    sys.exit("CANON array not found in bench.sh")
block = m.group(1)
if rt in block:
    sys.exit(0)
block2 = block.rstrip("\n") + f"\n  {rt} {vis}"
open(p, "w").write(s[:m.start(1)] + block2 + s[m.end(1):])
print(f"bench.sh CANON += {rt} {vis}")
PY

  # hold answers (hidden tests + SOLUTION.md) OUTSIDE the repo for the main commit
  local HOLD; HOLD="$(mktemp -d)"
  find "$dir" -type f \( -name 'SOLUTION.md' -o -name '*hidden*' \) -print0 \
  | while IFS= read -r -d '' f; do mkdir -p "$HOLD/$(dirname "$f")"; mv "$f" "$HOLD/$f"; done

  # stage ONLY the project dir + bench.sh (never `git add -A`, which would sweep
  # up unrelated uncommitted files)
  git add "$dir" bench.sh
  git commit -q -m "add project $name"

  # fold the answers into the single grading commit
  git rebase "$BASE" grading >/dev/null 2>&1 || die "rebase of grading onto $BASE failed"
  ( cd "$HOLD" && find . -type f | sed 's|^\./||' ) \
  | while IFS= read -r f; do mkdir -p "$(dirname "$f")"; mv "$HOLD/$f" "$f"; done
  git add "$dir"
  git commit -q --amend --no-edit
  git checkout -q "$BASE"
  rm -rf "$HOLD"

  echo
  echo "committed. structure check:"
  echo "  grading ahead of $BASE by: $(git rev-list --count "$BASE"..grading) (want 1)"
  local extra; extra="$(git diff --name-only "$BASE" grading | grep -vE 'SOLUTION|hidden' || true)"
  [ -z "$extra" ] && echo "  grading adds only answer files: ok" || echo "  !! grading also changes: $extra"
  git ls-tree -r --name-only "$BASE" | grep -qE "$name/(SOLUTION|.*hidden)" \
    && echo "  !! answers leaked onto $BASE" || echo "  $BASE clean of $name answers: ok"
  echo
  echo "NOW verify the oracle both ways:"
  echo "  ./bench.sh start _probe && ./bench.sh grade _probe    # $name row must FAIL"
  echo "  # apply the SOLUTION.md fix to $dir source, then:"
  echo "  ./bench.sh grade _probe                               # $name row must PASS"
  echo "  ./bench.sh clean _probe"
  echo "Also update the projects table in README.md."
}

# -------------------------------------------------------------------- main ----
case "${1:-}" in
  scaffold) shift; scaffold "${1:-}" "${2:-}" ;;
  commit)   shift; commit "${1:-}" ;;
  *) sed -n '2,20p' "$0"; exit 1 ;;
esac
