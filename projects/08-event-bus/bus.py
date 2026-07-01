from registry import HandlerRegistry


class EventBus:
    """A tiny synchronous publish/subscribe event bus."""

    def __init__(self):
        self._registry = HandlerRegistry()

    def subscribe(self, event, handler):
        """Register handler to be called on every publish of event."""
        self._registry.add(event, handler, once=False)

    def subscribe_once(self, event, handler):
        """Register handler to be called on the NEXT publish only, then removed."""
        raise NotImplementedError("subscribe_once is not implemented yet")

    def unsubscribe(self, event, handler):
        """Remove handler from event. No-op if it is not subscribed."""
        raise NotImplementedError("unsubscribe is not implemented yet")

    def publish(self, event, *args, **kwargs):
        """Call every handler subscribed to event, in subscription order."""
        for entry in self._registry.handlers(event):
            entry["fn"](*args, **kwargs)
