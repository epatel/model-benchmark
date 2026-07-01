# AGENTS.md — instructions for agents working in this repo

This is a benchmark that scores AI models on small coding tasks with
ground-truth test oracles. Read `README.md` and `WORKFLOW.md` first for the
big picture. This file is the **runbook for adding a new task ("project")**.

## Golden rules (do not violate)

1. **Answers never touch `main`.** A task's `SOLUTION.md` and its hidden tests
   (`*_hidden*`, `*.hidden.*`) live ONLY on the `grading` branch. `main` is the
   clean state a model sees.
2. **`grading` = `main` + exactly ONE additive commit** that adds only answer
   files (hidden tests + `SOLUTION.md`). Never let it modify or delete a `main`
   file. `bench.sh grade` cherry-picks that one commit; keeping it additive is
   what makes grading conflict-free.
3. **Every oracle must be verified BOTH ways** before you're done: the seeded
   code must FAIL and a reference fix must PASS (visible + hidden).
4. **No telltale comments** in the seeded source (don't write `// BUG:` etc.).
5. **Shell scripts run under `bash`** (`#!/usr/bin/env bash`). Do not rely on
   zsh behavior; note that unquoted `$var` word-splits in bash but NOT in zsh.

## Anatomy of a project

`projects/NN-name/` (two-digit number, next free index; `kebab-case`):

| File | Branch | Purpose |
|------|--------|---------|
| source file(s) | main | the seeded defect / incomplete feature (no telltale comments) |
| `TASK.md` | main | the prompt shown to the model |
| visible tests (`test_*.py` / `*_test.go` / `*.test.js`) | main | model may see these |
| `run_tests.sh` | main | **branch-agnostic**: runs whatever tests are present |
| hidden tests (`*_hidden*` / `*.hidden.*`) | grading | catch overfitting / carry the difficulty |
| `SOLUTION.md` | grading | the answer key + why (never shown to the model) |

`run_tests.sh` must run *all present* test files so it works on both branches
(visible-only on `main`, visible+hidden after the grading commit is applied):

- Python: `python3 -m unittest discover -s . -p 'test_*.py'`
- Go:     `go test -race -count=5 ./...`  (add a watchdog in tests for deadlocks)
- Node:   `node --test`

Runners (`run_all.sh`, `run_models.sh`, `run_ollama.sh`) and `scripts/summarize.py`
auto-discover `projects/*`, so you do NOT edit them for a new project.

## Design principles for a good task

- **Deterministic oracle.** Table-driven asserts; for concurrency use a bounded
  watchdog so a bug FAILS fast instead of hanging; for perf use a *generous*
  time budget with a huge margin (O(n²) vs O(n)) so it's not machine-flaky.
- **Put difficulty in the hidden tests.** The strongest discriminators (see
  `07-perf-dedup`, `08-event-bus`) pass their *visible* tests on the broken code
  and only fail a *hidden* edge case — that catches models that chase visible-green.
- **Small and self-contained.** One language, few files, fast to run.
- **Reject cheap fake fixes** in `SOLUTION.md` (e.g. `time.sleep`, lowering
  goroutine counts, special-casing test inputs).

## Procedure to add project `NN-name`

Work on `main`. Create the whole project on disk first (including hidden +
SOLUTION), then split answers onto `grading`.

```bash
cd <repo>
git checkout main
mkdir -p projects/NN-name
# ... write: source, TASK.md, visible tests, run_tests.sh, hidden tests, SOLUTION.md ...
chmod +x projects/NN-name/run_tests.sh
```

1. **Anti-tamper.** Add the new `run_tests.sh` and the *visible* test file to the
   `CANON` array in `bench.sh` (grading restores these from `main` so a model
   can't fake a pass by editing tests).

2. **Commit source to `main`, holding answers aside** (a holding dir OUTSIDE the
   repo so they aren't committed):

   ```bash
   HOLD="$(mktemp -d)"
   find projects/NN-name -type f \( -name 'SOLUTION.md' -o -name '*hidden*' \) -print0 \
   | while IFS= read -r -d '' f; do mkdir -p "$HOLD/$(dirname "$f")"; mv "$f" "$HOLD/$f"; done
   git add -A
   git commit -m "add project NN-name"
   ```

3. **Fold answers into the single grading commit:**

   ```bash
   git rebase main grading                     # replay the one answer commit onto new main
   ( cd "$HOLD" && find . -type f | sed 's|^\./||' ) \
   | while IFS= read -r f; do mkdir -p "$(dirname "$f")"; mv "$HOLD/$f" "$f"; done
   git add -A
   git commit --amend --no-edit                # keep grading = main + ONE commit
   git checkout main
   ```

4. **Verify structure:** `grading` must add ONLY answer files and be 1 commit ahead:

   ```bash
   git rev-list --count main..grading                 # -> 1
   git diff --name-only main grading | grep -vE 'SOLUTION|hidden'   # -> (empty)
   git ls-tree -r --name-only main | grep -E 'SOLUTION|hidden'      # -> (empty)
   ```

5. **Verify the oracle BOTH ways** via the real harness:

   ```bash
   ./bench.sh start _probe
   # (a) no fix -> the new task must FAIL
   ./bench.sh grade _probe            # inspect the NN-name row == FAIL
   # (b) apply the reference fix from SOLUTION.md to the source, then:
   ./bench.sh grade _probe            # NN-name row must now PASS (visible + hidden)
   ./bench.sh clean _probe
   ```

6. **Docs:** update the projects table in `README.md` and tick `PLAN.md`.

## Gotchas

- If `main` advances after `grading` exists, re-run `git rebase main grading`
  so `grading` stays one additive commit on top (verify with the checks above).
- Don't run two model runners at once — they share the repo and check out
  branches. Runs are sequential (`run_all.sh` handles this).
- The clean-task branch is auto-detected by `bench.sh` (prefers `main`, falls
  back to `base`; override `BENCH_BASE`). Use `$BASE`, never a hardcoded name.
- Never push `grading` to a remote — it's the answer key.
