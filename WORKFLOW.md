# Git workflow

Answers live on a separate branch so the model never sees them, and grading is a
conflict-free cherry-pick because hidden tests are **new files**.

> **Branch name:** the clean-task branch is now **`main`** (originally `base`;
> it was renamed). `bench.sh` auto-detects it (prefers `main`, falls back to
> `base`, override with `BENCH_BASE=<branch>`). Wherever this doc says `base`,
> read it as "the clean-task branch" = `main`.

## Branches

| Branch | Contents |
|--------|----------|
| `base` | Tasks with seeded defects + `TASK.md` + **visible** tests. What the model gets. No answers on disk. |
| `grading` | `base` + **one additive commit**: hidden tests (`*_hidden*`, `*.hidden.*`) + every `SOLUTION.md`. |
| `model/<name>` | `base` + a model's edits. |
| `grade/<name>` | `model/<name>` + the cherry-picked grading commit. Disposable, used only for scoring. |

```mermaid
gitGraph
    commit id: "base"
    branch grading
    commit id: "hidden + solutions"
    checkout base
    branch model/opus
    commit id: "model edits"
    branch grade/opus
    commit id: "cherry-pick grading"
    commit id: "run all tests"
```

## Run a model

```bash
./bench.sh start opus        # clean task branch model/opus off base
#   ... point the model at this working tree (TASK.md per project) ...
#   ... it edits source; no need to commit, grade auto-commits pending edits ...
./bench.sh grade opus        # model work + hidden tests, runs all -> reports/opus.txt
```

`grade` produces three artifacts per model:

- `reports/opus.txt` — human log (test results + a `git diff --stat`).
- `reports/opus.results.json` — per-project pass/fail + seconds.
- `reports/opus.metrics.json` — edit counts (files / insertions / deletions),
  total and per-project, of the model's pure edits vs `base`. Surgical fixes
  score low here; a passing 1-line fix beats a passing 200-line rewrite.

```json
{
  "total": {"files": 1, "insertions": 1, "deletions": 1},
  "by_project": { "01-lru-cache": {"files": 1, "insertions": 1, "deletions": 1} }
}
```

Repeat for each model, then compare reports.

```bash
./bench.sh list              # show model/ and grade/ branches
./bench.sh clean opus        # delete model/opus and grade/opus
```

## Why it's tamper-resistant

Before running, `grade` restores the harness scripts and the **visible** test
files from `base` (the `CANON` list in `bench.sh`), so a model can't edit a test
or `run_tests.sh` to fake a pass. Hidden tests are added by the grading commit,
which the model never had access to. A model that passes visible but fails
hidden tests overfit to the examples.

## Notes / caveats

- A model with shell access to this repo could in principle inspect other
  branches (`git show grading`). For a hardened run, hand the model a checkout
  of `base` with `.git` removed, or run it in a worktree of `base` only.
- `base` history contains no answers; the grading commit is the only place they
  live, kept off `base`.
- Keep `grading` to a single commit on top of `base` so `bench.sh grade` can
  cherry-pick it by name. If you add tasks, recommit `grading` as one commit.
