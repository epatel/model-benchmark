class HandlerRegistry:
    """Stores handlers per event name, preserving subscription order.

    Each entry is a dict: {"fn": handler, "once": bool}.
    """

    def __init__(self):
        self._handlers = {}  # event -> list[entry]

    def add(self, event, handler, once=False):
        self._handlers.setdefault(event, []).append({"fn": handler, "once": once})

    def handlers(self, event):
        """Return a snapshot (copy) of the entries for an event."""
        return list(self._handlers.get(event, []))

    def remove(self, event, handler):
        raise NotImplementedError("remove is not implemented yet")
