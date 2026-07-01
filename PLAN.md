# Plan — model-benchmark

Living plan for the AI-model coding benchmark. Check items off as they land.

## Done

- [x] **Tier-1 task suite** — 5 self-contained projects, each with a ground-truth oracle:
      `01-lru-cache` (Py, off-by-one), `02-bank-ledger` (Go, race), `03-csv-parser`
      (Py, feature+edge), `04-rest-pagination` (Node, feature), `05-god-refactor`
      (Py, refactor). Each has `TASK.md`, seeded defect, visible + hidden tests.
- [x] **Git workflow** — `base` (task as seen), `grading` (additive commit: hidden
      tests + `SOLUTION.md`). Grading = conflict-free cherry-pick onto a model branch.
      See `WORKFLOW.md`.
- [x] **`bench.sh`** — `start` / `grade` / `list` / `clean`. Anti-tamper: restores
      harness + visible tests from `base` before scoring.
- [x] **Scoring** — per-project pass/fail + timing (`scripts/run_all.sh` → results.json)
      and edit-count capture (`git diff --stat` → `<model>.metrics.json`).
- [x] **Umbrella runner** — `run_models.sh` drives headless `claude -p` per task per
      model, then grades. `scripts/summarize.py` prints results grid + efficiency table.
- [x] **Time + token capture** — `--output-format json` → `scripts/usage.py` aggregates
      duration / turns / cost / tokens into `<model>.usage.json`.
- [x] **Validated** — haiku/sonnet/opus all 5/5 on tier-1 (harness proven end-to-end).

## Done (tier-2)

- [x] **Harder second tier that discriminates between frontier models** — three tasks
      whose oracles catch subtle failure modes, each verified both ways
      (seeded → fail, reference fix → pass):
    - `06-deadlock` (Go) — lock-ordering deadlock; oracle is a 5s-watchdog stress test
      that fails (not hangs) on the wrong fix. Fix = consistent lock ordering.
    - `07-perf-dedup` (Py) — correct-but-O(n²); visible correctness tests pass on the
      slow code, hidden test asserts an 80k-item time budget. Fix = set/`dict.fromkeys`.
    - `08-event-bus` (Py, 2 files) — multi-file feature (unsubscribe + once) with
      snapshot-during-iteration and raise-safety invariants in the hidden tests.

## Next

## Backlog / ideas

- [ ] LLM-as-judge rubric for the refactor task (structure quality, not just tests).
- [ ] Overfit detector: flag models that pass visible but fail hidden tests.
- [ ] Hardened integrity run: hand the model a `.git`-stripped copy of `base` so it
      can't `git show grading`.
- [ ] `--max-turns` / timeout guards around headless `claude` calls.
- [ ] Aggregate multiple seeds/runs per model (variance, not a single sample).
