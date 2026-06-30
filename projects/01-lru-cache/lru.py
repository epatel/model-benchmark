from collections import OrderedDict


class LRUCache:
    """A least-recently-used cache with a fixed capacity.

    The cache holds at most ``capacity`` entries. When a new key is inserted
    and the cache is full, the least-recently-used entry is evicted. A key is
    "used" when it is read with ``get`` or written with ``put``.
    """

    def __init__(self, capacity):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._store = OrderedDict()

    def get(self, key):
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key, value):
        if key in self._store:
            self._store[key] = value
            self._store.move_to_end(key)
            return
        self._store[key] = value
        if len(self._store) > self.capacity + 1:
            self._store.popitem(last=False)

    def __len__(self):
        return len(self._store)
