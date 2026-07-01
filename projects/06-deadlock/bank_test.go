package bank

import (
	"sync"
	"testing"
	"time"
)

// withinDeadline runs fn in a goroutine and fails the test if it does not finish
// within d (i.e. it deadlocked).
func withinDeadline(t *testing.T, d time.Duration, what string, fn func()) {
	t.Helper()
	done := make(chan struct{})
	go func() { fn(); close(done) }()
	select {
	case <-done:
	case <-time.After(d):
		t.Fatalf("deadlock: %s did not complete within %s", what, d)
	}
}

func TestNoDeadlockOpposingTransfers(t *testing.T) {
	b := New("a", "b")
	b.Deposit("a", 1000)
	b.Deposit("b", 1000)

	withinDeadline(t, 5*time.Second, "opposing transfers", func() {
		var wg sync.WaitGroup
		for i := 0; i < 1000; i++ {
			wg.Add(2)
			go func() { defer wg.Done(); b.Transfer("a", "b", 1) }()
			go func() { defer wg.Done(); b.Transfer("b", "a", 1) }()
		}
		wg.Wait()
	})

	if got := b.Total(); got != 2000 {
		t.Fatalf("money not conserved: total=%d want 2000", got)
	}
}
