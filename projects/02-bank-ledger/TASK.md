# Task: Make the ledger concurrency-safe

`ledger.go` implements a simple in-memory account ledger. It is supposed to be
safe to use from many goroutines at once, but it is **not**: concurrent
`Deposit`/`Transfer`/`Balance` calls race on the shared `balances` map. Under
load this corrupts balances (money is not conserved) and can crash with
`fatal error: concurrent map writes`.

Fix the data race so that:

- concurrent operations never lose or create money (the `Total()` is conserved),
- there are no races under `go test -race`, and
- the public API is unchanged.

Do **not** "fix" it by sleeping, lowering goroutine counts, or weakening the
tests. Run the oracle:

```bash
go test -race -count=20 ./...
```
