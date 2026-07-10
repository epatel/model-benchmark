"""Transaction handle for Store.

A Txn sees a snapshot of the store taken at begin(), overlaid with its own
uncommitted writes. commit() validates against concurrent commits and either
applies all writes atomically or raises Conflict and applies nothing.
"""


class Txn:
    TOMBSTONE = object()

    def __init__(self, store):
        self._store = store
        self._snapshot = dict(store._data)
        self._writes = {}
        self._closed = False

    def _check_open(self):
        if self._closed:
            import store as _store_mod
            raise _store_mod.TxnClosed("transaction is closed")

    def get(self, key):
        """Value of key as seen by this transaction, or None if absent."""
        self._check_open()
        if key in self._writes:
            value = self._writes[key]
            return None if value is Txn.TOMBSTONE else value
        return self._snapshot.get(key)

    def put(self, key, value):
        self._check_open()
        if value is None:
            raise ValueError("None is not a storable value; use delete()")
        self._writes[key] = value

    def delete(self, key):
        self._check_open()
        self._writes[key] = Txn.TOMBSTONE

    def commit(self):
        self._check_open()
        self._closed = True
        if self._writes:
            self._store._commit(self)

    def abort(self):
        self._check_open()
        self._closed = True
        self._writes.clear()
