package bank

import "sync"

// Bank holds a fixed set of accounts, each guarded by its own mutex so that
// transfers between disjoint pairs of accounts can proceed in parallel. Accounts
// are created up front in New and the map is never written again, so it is safe
// to read concurrently.
type account struct {
	mu      sync.Mutex
	balance int
}

type Bank struct {
	accounts map[string]*account
}

func New(names ...string) *Bank {
	b := &Bank{accounts: make(map[string]*account, len(names))}
	for _, n := range names {
		b.accounts[n] = &account{}
	}
	return b
}

func (b *Bank) Deposit(name string, amount int) {
	a := b.accounts[name]
	a.mu.Lock()
	a.balance += amount
	a.mu.Unlock()
}

// Transfer moves amount from one account to another. It locks both accounts for
// the duration so no other transfer can observe a half-completed move.
func (b *Bank) Transfer(from, to string, amount int) {
	f := b.accounts[from]
	t := b.accounts[to]
	f.mu.Lock()
	defer f.mu.Unlock()
	t.mu.Lock()
	defer t.mu.Unlock()
	f.balance -= amount
	t.balance += amount
}

func (b *Bank) Balance(name string) int {
	a := b.accounts[name]
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.balance
}

func (b *Bank) Total() int {
	sum := 0
	for _, a := range b.accounts {
		a.mu.Lock()
		sum += a.balance
		a.mu.Unlock()
	}
	return sum
}
