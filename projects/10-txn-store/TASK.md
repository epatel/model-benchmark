# Task: Make transaction commits actually serializable (and begin() cheap)

`store.py` + `txn.py` implement an in-memory key-value store with
transactions: `Store.begin()` returns a `Txn` with `get` / `put` / `delete` /
`commit` / `abort`.

Users report two problems in production:

1. **Anomalies under concurrent load.** Occasionally two transactions both
   commit when one of them should have been rejected, leaving the store in a
   state that no serial order of the transactions could produce.
2. **`begin()` is slow on large stores.** Starting a transaction on a store
   with a million keys takes hundreds of milliseconds.

Fix the implementation so it satisfies the SPEC below. Do not change the
public API: tests import `Store`, `Conflict`, `TxnClosed` from `store` and
use the `Txn` methods shown above.

## SPEC

**Reads.** `txn.get(key)` returns the transaction's own uncommitted write for
that key if it has one (`None` after its own `delete`), otherwise the value
the key had **when the transaction began** (`None` if it was absent then).
Commits by other transactions after begin are never visible inside a running
transaction.

**Writes.** `put`/`delete` buffer writes; nothing touches the store until
`commit()`.

**Commit.** `commit()` must be first-committer-wins serializable:

- It raises `Conflict` if any key this transaction **read or wrote** was
  changed (put **or** delete) by another transaction's commit after this
  transaction began. "Changed" means a commit touched the key — even if the
  value was later changed back to what it was at begin time.
- A key counts as read if `get()` consulted the begin-time state for it —
  including reads of keys that were absent. Reads served entirely from the
  transaction's own writes do not count.
- A transaction with no writes (read-only) always commits successfully,
  regardless of what changed meanwhile.
- On success, all buffered writes are applied atomically. On `Conflict`,
  nothing is applied.
- After `commit()` returns or raises, and after `abort()`, the transaction is
  closed: any further method call raises `TxnClosed`.

**Cost.** `begin()` must do O(1) work — it must not copy or scan the store's
contents. Reads and commits may only do work proportional to the keys the
transaction actually touched.

## Constraints

- Pure Python standard library; keep the `store.py` / `txn.py` split.
- Single-threaded usage: transactions interleave, but calls never run
  concurrently. No locking is needed.
- Do not modify the tests or `run_tests.sh`.

Run the visible tests with `./run_tests.sh`.
