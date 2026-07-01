# Task: Make `dedupe` scale

`dedupe(items)` removes duplicates while preserving first-seen order. It is
**correct** but too slow: the `x not in result` membership check scans a growing
list, making it O(n²). On large inputs (hundreds of thousands of items) it takes
many seconds.

Make it fast (linear time) **without changing its behavior**:

- Same result for every input: duplicates removed, first-seen order preserved.
- Must handle large inputs quickly — the hidden performance test builds an
  80,000-item list and requires `dedupe` to finish in well under a second.
- Keep the signature `dedupe(items) -> list`.

Note: the visible correctness tests already pass on the slow version — the
speed requirement is the real target here. Assume items are hashable.

Run `python3 -m unittest discover -s . -p 'test_*.py'`.
