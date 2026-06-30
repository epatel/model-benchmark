package ledger

import (
	"sync"
	"testing"
)

func TestConcurrentTransfersConserveMoney(t *testing.T) {
	l := New()
	l.Deposit("a", 1_000_000)

	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			l.Transfer("a", "b", 1)
		}()
	}
	wg.Wait()

	if got := l.Total(); got != 1_000_000 {
		t.Fatalf("money not conserved: total=%d want 1000000", got)
	}
	if got := l.Balance("b"); got != 1000 {
		t.Fatalf("b=%d want 1000", got)
	}
	if got := l.Balance("a"); got != 999_000 {
		t.Fatalf("a=%d want 999000", got)
	}
}
