# Model Benchmark Kit

A small, self-contained suite of coding tasks for evaluating AI model output.
Each project has a **ground-truth oracle** (a test suite or stress harness) so
scoring is objective rather than eyeballed.

## Projects

| # | Project | Lang | Task type | Oracle |
|---|---------|------|-----------|--------|
| 01 | `lru-cache` | Python | Bug fix (off-by-one eviction) | `unittest` |
| 02 | `bank-ledger` | Go | Bug fix (race condition) | `go test -race -count=20` |
| 03 | `csv-parser` | Python | Feature + edge-case bug | `unittest` |
| 04 | `rest-pagination` | Node/JS | Add a feature | `node --test` |
| 05 | `god-refactor` | Python | Refactor (behavior preserved) | `unittest` |

## How to run a model against the kit

1. Start from a **clean checkout** of a project (no prior model's edits).
2. Give the model the contents of that project's `TASK.md` as the prompt,
   plus access to the project directory **excluding** `SOLUTION.md` and the
   `*_hidden*` test files.
3. After the model finishes, score it:

   ```bash
   ./scripts/run_all.sh            # run every project, write results.json
   ./scripts/run_one.sh projects/01-lru-cache
   ```

   `run_one.sh` runs both the **visible** and **hidden** tests and reports
   pass/fail + duration. Passing visible but failing hidden = overfit.

## Files in each project

- `TASK.md` — the prompt shown to the model.
- `SOLUTION.md` — **hidden**: where the bug is / what "done" means. Don't show the model.
- source file(s) — contain the seeded defect (no telltale comments).
- `test_*.py` / `*_test.go` / `*.test.js` — **visible** tests (model may see).
- `*_hidden*` — **hidden** tests (catch overfitting). Don't show the model.
- `run_tests.sh` — runs visible + hidden tests; exit 0 = pass.

## Scoring guidance

Test pass/fail is the hard gate. For richer comparison also capture per run:
edits made, files touched, whether unrelated tests broke, time/tokens.
For the refactor (05), gate on tests then judge structure separately
(complexity/duplication reduction), optionally with an LLM-as-judge rubric.
