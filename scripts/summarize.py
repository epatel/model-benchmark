#!/usr/bin/env python3
"""Comparison tables from reports/: results grid + efficiency (time/tokens/cost)."""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")


def _read(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def load(model):
    results = _read(os.path.join(REPORTS, f"{model}.results.json")) or []
    metrics = _read(os.path.join(REPORTS, f"{model}.metrics.json")) or {}
    usage = _read(os.path.join(REPORTS, f"{model}.usage.json")) or {}
    return results, metrics.get("total"), usage


def k(n):
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def main():
    models = sorted(
        os.path.basename(p)[: -len(".results.json")]
        for p in glob.glob(os.path.join(REPORTS, "*.results.json"))
    )
    if not models:
        print("no reports yet — run ./run_models.sh first")
        return

    projects = [r["project"] for r in load(models[0])[0]]
    short = [p.split("-", 1)[1] if "-" in p else p for p in projects]
    w = max(len(m) for m in models + ["model"])

    # --- Table 1: results grid ---
    head = "model".ljust(w) + " | " + " | ".join(s[:8].center(8) for s in short)
    head += " | pass | edits(+/-)"
    print(head)
    print("-" * len(head))
    for m in models:
        results, edits, _ = load(m)
        by = {r["project"]: r["status"] for r in results}
        passed = sum(by.get(p) == "pass" for p in projects)
        cells = [("PASS" if by.get(p) == "pass" else "FAIL").center(8) for p in projects]
        edit_str = f"+{edits['insertions']}/-{edits['deletions']} ({edits['files']}f)" if edits else "-"
        print(m.ljust(w) + " | " + " | ".join(cells) + f" | {passed}/{len(projects)} | {edit_str}")

    # --- Table 2: efficiency ---
    print()
    head2 = (f"{'model'.ljust(w)} | {'time':>7} | {'in tok':>8} | {'out tok':>8} "
             f"| {'turns':>5} | {'cost USD':>9}")
    print(head2)
    print("-" * len(head2))
    tot = {"in": 0, "out": 0, "cost": 0.0, "s": 0.0, "turns": 0}
    have_usage = False
    for m in models:
        _, _, u = load(m)
        if not u:
            print(f"{m.ljust(w)} | {'-':>7} | {'-':>8} | {'-':>8} | {'-':>5} | {'-':>9}")
            continue
        have_usage = True
        secs = u.get("duration_ms", 0) / 1000
        intok = u.get("input_tokens", 0) + u.get("cache_read", 0) + u.get("cache_creation", 0)
        outtok = u.get("output_tokens", 0)
        cost = u.get("cost_usd", 0.0)
        turns = u.get("num_turns", 0)
        tot["s"] += secs; tot["in"] += intok; tot["out"] += outtok
        tot["cost"] += cost; tot["turns"] += turns
        print(f"{m.ljust(w)} | {secs:6.0f}s | {k(intok):>8} | {k(outtok):>8} "
              f"| {turns:>5} | {cost:9.4f}")
    if have_usage:
        print("-" * len(head2))
        print(f"{'TOTAL'.ljust(w)} | {tot['s']:6.0f}s | {k(tot['in']):>8} | {k(tot['out']):>8} "
              f"| {tot['turns']:>5} | {tot['cost']:9.4f}")


if __name__ == "__main__":
    main()
