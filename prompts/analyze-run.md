# Prompt: analyze a benchmark run

You are a senior engineer reviewing ONE run of this coding benchmark (see the
repo README for context). You are given the combined evaluation for the run
(leaderboard + reproduced failures + every model's per-task solution diff) and
the raw per-model usage JSON. Produce a rigorous, skeptical review.

The task count for this run is given in the RUN DATA below (`n_tasks`) —
tier-1 (`01`–`05`: LRU off-by-one, race, csv parser, pagination, refactor),
tier-2 (`06` deadlock, `07` O(n²) perf, `08` multi-file event-bus), tier-3
(`09` exponential→polynomial glob matcher, exact semantics preserved). Each
model solved on a clean branch and was graded by hidden-test oracles it
never saw.

## Providers report differently — NORMALIZE before comparing

Do not compare raw numbers across the two runner types:

- **Claude models** (agentic, `claude -p`): solve over many turns (`num_turns` ≫
  n_tasks), re-reading context each turn, so `input_tokens` + `cache_read` are
  large and dominated by CHEAP cached reads. They report real `cost_usd`.
- **Ollama models** (`*_cloud` or local, one-shot adapter): exactly one call per
  task (`num_turns` == n_tasks), tiny input, and `cost_usd == 0` because Ollama
  does not report pricing. They return WHOLE files, inflating output tokens and
  the edit counts.

Detect the provider per model: `cost_usd > 0` or `num_turns > n_tasks` ⇒ Claude
(agentic); `cost_usd == 0` and `num_turns == n_tasks` ⇒ Ollama (one-shot).

Normalization rules (always state n_tasks; label cross-provider numbers as
*indicative, not exact*):

- **Cost** — rank by USD **only within Claude**. For Ollama mark `n/a (unmetered)`.
  If a proxy is wanted, estimate `output_tokens × <assumed $/token>` and clearly
  LABEL it an estimate with the assumed price.
- **Input tokens** — never headline the summed input. Split Claude into
  `fresh = input_tokens + cache_creation` vs `cached = cache_read` (cheap), and
  compare Ollama's input only against Claude's *fresh*.
- **Output tokens** — the most comparable "work" signal: report
  `output_tokens / n_tasks`, but note Ollama emits whole files (inflated) vs
  Claude's targeted edits.
- **Turns** — report but don't rank (different execution models).
- **Time** — use wall-seconds per task; note cloud cold-start/queue variance and
  agentic tool round-trips add noise.
- **Edits (+/-)** — normalize per task; whole-file vs surgical means edit-count
  structurally favors Claude — treat it as a churn signal, not correctness.

## Produce (markdown)

1. **Executive summary** — 3–5 sentences: headline results + the single most
   interesting finding.
2. **Results breakdown** — table: `model | provider | pass/N | failed tasks`.
   Call out which tasks were hardest across models (tier-2 especially).
3. **Solution review** —
   - For every FAILURE: root-cause it from the diff + reproduced output
     (e.g. "compiled but wrong", "overfit to visible tests", "deadlocked /
     watchdog", "wrong edge case").
   - For notable PASSES: judge quality — surgical vs sprawling, idiomatic,
     over-engineered, or risky-but-passing. Compare approaches on the hard tasks
     (`06` lock ordering, `07` set vs dict.fromkeys, `08` snapshot + raise-safety).
4. **Efficiency (normalized)** — one table applying the rules above (per-task
   where noted), Claude and Ollama grouped separately, plus a one-line "how to
   read this".
5. **Rankings** — best correctness; best correctness-per-dollar (Claude only);
   fastest (wall/task); most surgical (edits/task). Each with a caveat.
6. **Caveats** — single sample + temperature ⇒ results vary run-to-run; the
   provider reporting asymmetry; whole-file vs surgical; any oracle limitation
   you noticed (e.g. a task that a fake fix could pass).

Be concrete — cite task ids and model names. Prefer "I can't tell from this
data" over guessing. Keep it tight.
