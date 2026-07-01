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

## Next

- [ ] **Add a harder second tier (tier-2) that actually discriminates between frontier
      models.** Tier-1 is too easy (everyone scores 5/5), so add `projects/` tasks whose
      oracles catch subtle failure modes the way `-race` catches tier-1's race:
    - Subtler concurrency: a lock-ordering **deadlock** or an ABA / lost-wakeup bug
      (oracle: bounded-time stress harness that hangs/deadlocks on the wrong fix).
    - Multi-file feature: a change spanning 3–4 files with a cross-cutting invariant
      (oracle: integration tests + a property/invariant check).
    - Invariant-heavy refactor: preserve behavior on a module with tricky edge cases
      (oracle: large golden/property suite; mutation-style hidden tests).
    - Performance bug: correct-but-O(n²) code that must stay correct AND meet a time
      budget (oracle: perf assertion on a large input).
    - Keep the same shape: `TASK.md` + seeded defect + visible tests on `base`; hidden
      tests + `SOLUTION.md` added to the `grading` commit. Number them `06-…`, `07-…`.
      Confirm each oracle both ways (seeded → fail, reference fix → pass) before locking.

## Backlog / ideas

- [ ] LLM-as-judge rubric for the refactor task (structure quality, not just tests).
- [ ] Overfit detector: flag models that pass visible but fail hidden tests.
- [ ] Hardened integrity run: hand the model a `.git`-stripped copy of `base` so it
      can't `git show grading`.
- [ ] `--max-turns` / timeout guards around headless `claude` calls.
- [ ] Aggregate multiple seeds/runs per model (variance, not a single sample).
