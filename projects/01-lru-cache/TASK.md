# Task: Fix the LRU cache

`lru.py` implements a least-recently-used cache. It has a bug: after inserting
more keys than the capacity, the cache holds **more entries than it should**,
and the wrong entry survives eviction.

Fix the bug so that:

- the cache never holds more than `capacity` entries, and
- when full, inserting a new key evicts the *least-recently-used* key
  (reads via `get` and writes via `put` both count as "using" a key).

Do not change the public API (`LRUCache(capacity)`, `get`, `put`, `__len__`).

Run `python3 -m unittest test_lru.py` to check your work.
