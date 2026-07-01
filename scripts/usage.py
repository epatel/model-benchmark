#!/usr/bin/env python3
"""Aggregate time + token usage for one model from its headless-claude JSON logs.

Reads reports/<model>.logs/<project>.json (each a `claude -p --output-format json`
result), sums duration / turns / cost / tokens, and writes
reports/<model>.usage.json (with a per-project breakdown).
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIELDS = ("duration_ms", "num_turns", "cost_usd",
          "input_tokens", "output_tokens", "cache_read", "cache_creation")


def main():
    model = sys.argv[1]
    logdir = os.path.join(ROOT, "reports", f"{model}.logs")
    agg = {k: 0 for k in FIELDS}
    agg["cost_usd"] = 0.0
    agg["by_project"] = {}

    for f in sorted(glob.glob(os.path.join(logdir, "*.json"))):
        name = os.path.basename(f)[: -len(".json")]
        try:
            d = json.load(open(f))
        except Exception:
            agg["by_project"][name] = {"error": "unparseable"}
            continue
        u = d.get("usage", {}) or {}
        row = {
            "duration_ms": d.get("duration_ms", 0),
            "num_turns": d.get("num_turns", 0),
            "cost_usd": d.get("total_cost_usd", 0.0),
            "input_tokens": u.get("input_tokens", 0),
            "output_tokens": u.get("output_tokens", 0),
            "cache_read": u.get("cache_read_input_tokens", 0),
            "cache_creation": u.get("cache_creation_input_tokens", 0),
        }
        agg["by_project"][name] = row
        for k in FIELDS:
            agg[k] += row[k]

    out = os.path.join(ROOT, "reports", f"{model}.usage.json")
    with open(out, "w") as fh:
        json.dump(agg, fh, indent=2)

    in_tok = agg["input_tokens"] + agg["cache_read"] + agg["cache_creation"]
    print(f"  usage: {agg['duration_ms']/1000:.0f}s, "
          f"in {in_tok}, out {agg['output_tokens']}, "
          f"{agg['num_turns']} turns, ${agg['cost_usd']:.4f}")


if __name__ == "__main__":
    main()
