# Task: make the glob matcher fast

`globmatch.py` implements shell-style glob matching (`*`, `?`, `[set]`,
`[!set]` — semantics documented in the module docstring). It returns the
right answers, but on patterns containing several `*` wildcards it can take
effectively forever (exponential time in the worst case), e.g.:

```python
match("a" * 40, "*a" * 20 + "*b")   # never finishes
```

Fix `match()` so it runs in polynomial time (O(len(text) * len(pattern)) or
better) on ALL inputs, including adversarial many-`*` patterns.

Requirements:

- Behavior must stay EXACTLY the same for every (text, pattern) pair —
  including all the class-bracket edge cases the current code handles
  (literal `]` first in a set, `[!...]` negation, unterminated `[`).
- Keep the public entry point: `match(text, pattern) -> bool`.
- Do NOT use `re`, `fnmatch`, `regex`, or any other pattern-matching
  library. The algorithm must be your own.
- Do not modify any test file or `run_tests.sh`.

Run the tests with `./run_tests.sh`.
