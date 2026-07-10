"""An in-memory key-value store with optimistic transactions.

Transactions are started with ``Store.begin()`` and provide snapshot reads
(a transaction sees the store as it was when it began, plus its own writes)
and first-committer-wins conflict detection at commit time.
"""

from txn import Txn


class Conflict(Exception):
    """Raised by commit() when the transaction lost a conflict."""


class TxnClosed(Exception):
    """Raised when a transaction is used after commit() or abort()."""


class Store:
    def __init__(self):
        self._data = {}

    def begin(self):
        return Txn(self)

    def _commit(self, txn):
        for key in txn._writes:
            before = txn._snapshot.get(key)
            now = self._data.get(key)
            if now != before:
                raise Conflict(f"key {key!r} was modified concurrently")
        for key, value in txn._writes.items():
            if value is Txn.TOMBSTONE:
                self._data.pop(key, None)
            else:
                self._data[key] = value
