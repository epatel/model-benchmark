# Task: Fix the transfer deadlock

`bank.go` gives every account its own mutex so independent transfers can run in
parallel. But `Transfer` always locks `from` first and `to` second. When two
transfers move money in opposite directions at the same time
(`Transfer("a","b")` and `Transfer("b","a")`), each grabs one lock and waits
forever for the other — a classic lock-ordering **deadlock**.

Fix `Transfer` so that concurrent transfers can never deadlock, while keeping:

- both accounts locked for the duration of the move (no other transfer may see a
  half-completed transfer), and
- money conserved (`Total()` is invariant), and
- the public API unchanged.

Do not serialize everything behind one global lock if you can avoid it — the
point is that disjoint transfers still run in parallel. (A single lock would
also pass, but the intended fix is a consistent lock ordering.)

Run the oracle:

```bash
go test -race -count=5 ./...
```

The tests use a 5-second watchdog: a deadlocked transfer makes them fail rather
than hang.
