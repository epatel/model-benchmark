# Model Benchmark Kit

A small, self-contained suite of coding tasks for evaluating AI model output.
Each project has a **ground-truth oracle** (a test suite or stress harness) so
scoring is objective rather than eyeballed.

## Projects

**Tier 1** (baseline — current frontier models tend to ace these):

| # | Project | Lang | Task type | Oracle |
|---|---------|------|-----------|--------|
| 01 | `lru-cache` | Python | Bug fix (off-by-one eviction) | `unittest` |
| 02 | `bank-ledger` | Go | Bug fix (race condition) | `go test -race -count=20` |
| 03 | `csv-parser` | Python | Feature + edge-case bug | `unittest` |
| 04 | `rest-pagination` | Node/JS | Add a feature | `node --test` |
| 05 | `god-refactor` | Python | Refactor (behavior preserved) | `unittest` |

**Tier 2** (harder — designed to discriminate between strong models):

| # | Project | Lang | Task type | Oracle |
|---|---------|------|-----------|--------|
| 06 | `deadlock` | Go | Fix lock-ordering deadlock | `go test -race -count=5` (5s watchdog) |
| 07 | `perf-dedup` | Python | Fix O(n²) → linear (behavior preserved) | `unittest` (hidden time-budget test) |
| 08 | `event-bus` | Python | Multi-file feature + invariants | `unittest` (hidden snapshot/raise-safety) |

Tier-2 designs the *hidden* tests to carry the difficulty: 07's visible tests
pass on the slow code, and 08 hides its hard invariants — so a model that only
chases visible-green gets caught.

## Running models automatically (recommended)

Two umbrella runners drive every task for every model, then grade + tabulate.
Both share the git harness (see `WORKFLOW.md`) and write to `reports/`.

**Claude models** (agentic — edits files itself via `claude -p`):

```bash
./run_models.sh haiku sonnet opus       # or any model ids/aliases
```

**Ollama models** (local or `:cloud` — non-agentic; an adapter feeds the task
and writes back the model's file edits):

```bash
./run_ollama.sh glm-5.2:cloud kimi-k2.5:cloud   # cloud
./run_ollama.sh llama3.1                         # local
#   env: OLLAMA_URL (default http://localhost:11434)
```

Each model run produces, in `reports/`:
- `<model>.txt` — test log + `git diff --stat`
- `<model>.results.json` — per-project pass/fail + seconds
- `<model>.metrics.json` — edit counts (files / insertions / deletions)
- `<model>.usage.json` — time / tokens / turns / cost (mapped to one schema)

**Combined comparison table** across every model that has reports (Claude +
Ollama together):

```bash
python3 scripts/summarize.py            # results grid + efficiency table
```

To run everything for one big table (sequentially — the runners share the git
repo and must not overlap):

```bash
./run_ollama.sh kimi-k2.5:cloud gemma4:31b-cloud nemotron-3-super:cloud \
  && ./run_models.sh haiku sonnet opus \
  && python3 scripts/summarize.py
```

Notes when comparing across runners: Ollama models return whole files, so their
**edit-count** looks larger than Claude's surgical diffs; and cloud **cost**
shows `$0` (Ollama does not report pricing).

## How to run a single model by hand

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
