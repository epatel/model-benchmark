package ledger

// Ledger tracks integer balances for named accounts. It is meant to be safe to
// use from multiple goroutines concurrently (deposits and transfers happening
// at the same time), and money must always be conserved: a transfer moves an
// amount from one account to another without creating or destroying value.
type Ledger struct {
	balances map[string]int
}

func New() *Ledger {
	return &Ledger{balances: map[string]int{}}
}

func (l *Ledger) Deposit(acct string, amount int) {
	l.balances[acct] += amount
}

// Transfer moves amount from one account to another.
func (l *Ledger) Transfer(from, to string, amount int) {
	l.balances[from] -= amount
	l.balances[to] += amount
}

func (l *Ledger) Balance(acct string) int {
	return l.balances[acct]
}

// Total returns the sum of all account balances.
func (l *Ledger) Total() int {
	sum := 0
	for _, v := range l.balances {
		sum += v
	}
	return sum
}
