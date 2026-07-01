# Model Benchmark Kit

A small, self-contained suite of coding tasks for evaluating AI model output.
Each project has a **ground-truth oracle** (a test suite or stress harness) so
scoring is objective rather than eyeballed. Answers (`SOLUTION.md` + hidden
tests) live on a separate `grading` branch, so a model working on the clean
`main` branch can't see them.

## Requirements

- **python3** — projects 01/03/05/07/08 and all scoring scripts
- **go** — projects 02, 06 (`go test -race`)
- **node** — project 04 (`node --test`)
- **claude** CLI — for `run_models.sh` (agentic runner)
- **ollama** ≥ 0.30 — for `run_ollama.sh` (local models, or `:cloud` models after sign-in)

## Latest results (2026-07-01)

Snapshotted on the `results` branch (`runs/2026-07-01.md`); regenerate with
`python3 scripts/summarize.py`.

```
model                  | pass |    time |   in tok |  out tok | turns |  cost USD |    edits(+/-)
sonnet                 |  8/8 |    164s |  1693.2k |     8.3k |    45 |    1.6244 | +124/-67 (9f)
opus                   |  8/8 |    174s |   941.1k |     7.7k |    37 |    1.9983 | +128/-66 (9f)
haiku                  |  8/8 |    227s |  1288.3k |    17.0k |    44 |    0.4335 | +124/-65 (9f)
gemma4:31b-cloud       |  7/8 |     33s |     5.0k |     2.8k |     8 |    0.0000 | +116/-60 (8f)   (failed: 06-deadlock)
glm-5.2:cloud          |  7/8 |    328s |     4.4k |    12.5k |     8 |    0.0000 | +165/-72 (9f)   (failed: 03-csv-parser)
nemotron-3-super:cloud |  7/8 |    468s |     4.7k |    24.9k |     8 |    0.0000 | +131/-66 (8f)   (failed: 03-csv-parser)
kimi-k2.7-code:cloud   |  6/8 |     99s |     4.4k |     8.3k |     8 |    0.0000 |  +94/-19 (7f)   (failed: 03-csv, 06-deadlock)
```

The three Claude models sweep 8/8; cloud models each drop a different task —
concurrency (02/06) and the csv edge case (03) are the dividers. Cloud `cost`
shows `$0` because Ollama does not report pricing.

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

The canonical model list lives in **`models.txt`** — one `<runner> <model>` per
line (`claude` or `ollama`). Run **every** listed model and print the combined
leaderboard with one command:

```bash
./run_all.sh                 # runs everything in models.txt
./run_all.sh my-models.txt   # a different list
DRY=1 ./run_all.sh           # print the plan, run nothing
```

`run_all.sh` calls the two runners below in sequence (they share the git repo
and must not overlap). To run a subset directly, call a runner with explicit
model args instead.

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
Ollama together) — sorted best-first, with time / tokens / cost / edits:

```bash
python3 scripts/summarize.py
```

To run every model in one shot, use `./run_all.sh` (above) instead of chaining
the runners by hand.

Notes when comparing across runners: Ollama models return whole files, so their
**edit-count** looks larger than Claude's surgical diffs; and cloud **cost**
shows `$0` (Ollama does not report pricing).

## Consolidating results into a branch

Snapshot the current `reports/` into a dated markdown file on a dedicated
`results` branch (leaderboard + per-model pass/fail), so run history is versioned
separately from the code:

```bash
./scripts/snapshot.sh                 # runs/<today>.md on branch `results`
./scripts/snapshot.sh 2026-07-01      # explicit date/label
```

It uses git plumbing — the working tree and current branch are never touched.
Browse snapshots without checking the branch out:

```bash
git ls-tree -r --name-only results        # list all runs/*.md
git show results:runs/2026-07-01.md       # view one
```

The `results` branch contains no answers, so it is safe to `git push origin results`.

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

## See also

- **`WORKFLOW.md`** — the git branch model (`main` / `grading` / `model/*` /
  `grade/*`), how grading cherry-picks the hidden tests, and the anti-tamper step.
- **`PLAN.md`** — roadmap and what's done (tiers, runners, snapshots, next steps).
- **`models.txt`** — the canonical list of models to benchmark.
