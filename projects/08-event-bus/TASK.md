# Task: Finish the event bus (unsubscribe + once)

A small pub/sub event bus is split across two files:

- `registry.py` — `HandlerRegistry` stores ordered handler entries per event.
- `bus.py` — `EventBus` exposes `subscribe`, `subscribe_once`, `unsubscribe`, `publish`.

`subscribe` and `publish` work. Implement the two missing features (they raise
`NotImplementedError` today). You will need to change **both** files.

Required behavior and invariants:

1. `unsubscribe(event, handler)` removes `handler` from `event`. Unsubscribing a
   handler that is not subscribed is a **no-op** (no error).
2. `subscribe_once(event, handler)` fires `handler` on the next publish only,
   then it is automatically removed. It must be removed **even if the handler
   raises** (a raising once-handler still fires exactly once).
3. Handlers always fire in **subscription order**.
4. **Snapshot semantics:** if a handler unsubscribes another handler *during* a
   publish, the change takes effect on the *next* publish — the set of handlers
   invoked by an in-progress publish is fixed when that publish begins.

Keep the public API and the entry shape (`{"fn": ..., "once": ...}`) intact.

Run `python3 -m unittest discover -s . -p 'test_*.py'`.
