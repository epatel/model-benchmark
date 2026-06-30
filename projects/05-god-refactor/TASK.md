# Task: Refactor `process_order`

`pricing.py` contains a single long, deeply-nested `process_order` function that
computes an order summary (subtotal, discount, tax, shipping, total).

Refactor it for readability and maintainability **without changing its
behavior**:

- Keep the public function `process_order(items, customer_type, coupon)` with
  the same signature and the same return value (a dict with keys `subtotal`,
  `discount`, `tax`, `shipping`, `total`, each rounded to 2 decimals).
- Break the logic into small, well-named helper functions and/or use data
  structures (e.g. a discount-rate lookup) to remove the nested `if`/`else`
  ladders and duplication.
- Do not add new dependencies.

The existing tests must still pass exactly. Run:

```bash
python3 -m unittest test_pricing.py
```

You are being evaluated on correctness (tests stay green) **and** on whether the
result is genuinely cleaner: less nesting, less duplication, clear names.
