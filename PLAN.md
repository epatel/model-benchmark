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
- [x] **Ollama runner (local + `:cloud`)** — `run_ollama.sh` + `scripts/ollama_solve.py`
      adapt non-agentic models (feed task + source, write back their edits), then grade
      + report identically. Usage log mapped to the same schema (tokens from
      `prompt_eval_count`/`eval_count`).
- [x] **Results consolidation** — `scripts/snapshot.sh` writes `runs/<date>.md`
      (leaderboard + per-model pass/fail) to a dedicated `results` branch via git
      plumbing (working tree untouched). Answer-free, so safe to push.
- [x] **Combined evaluation + HTML + Pages** — `scripts/evaluate.sh` (markdown) and
      `scripts/evaluate_html.sh` (real tables + side-by-side diffs) consolidate all
      `model/*` branches into `evaluations/<date>.*`. `scripts/build_index.sh` builds
      the runs landing page; served via GitHub Pages from the `results` branch at
      https://epatel.github.io/model-benchmark/ (repo homepage).
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

## Done (tier-4)

- [x] **`10-txn-store` (Py, 2 files)** — MVCC rewrite under an exact isolation spec,
      added after 2026-07-10 put 8/15 entries at 9/9. Three interacting seeded
      defects (value-based validation → ABA, no read set → write skew, full-copy
      snapshots → O(n) begin); hidden probes punish naive fixes, over-fixes, and
      under-fixes. Verified both ways via `bench.sh` `_probe`.
- [x] **Tier-4 run across the full matrix** — splits on harness: every frontier
      one-shot entry except kimi fails the snapshot trap; the same models agentic
      pass. 10/10 club: kimi (both harnesses), gpt-5.4-cc, gpt-5.5-cc.

## Done (tooling)

- [x] **`scripts/matrix.py`** — menu/CLI matrix driver: any models × projects slice
      (per model+harness, per task, or single cell), resume-aware (`-p NN` folds a
      new task into existing model branches without re-solving 1..N-1), plus
      grade / status / summarize / evaluate / analyze / publish / pipeline.
      Manages the openai-cc LiteLLM proxy lifecycle itself.

## Next

## Backlog / ideas

- [ ] LLM-as-judge rubric for the refactor task (structure quality, not just tests).
- [ ] Overfit detector: flag models that pass visible but fail hidden tests.
- [ ] Hardened integrity run: hand the model a `.git`-stripped copy of `base` so it
      can't `git show grading`.
- [ ] `--max-turns` / timeout guards around headless `claude` calls.
- [ ] Aggregate multiple seeds/runs per model (variance, not a single sample).
