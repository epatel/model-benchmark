#!/usr/bin/env python3
"""Comparison tables from reports/: per-project grid + a sorted leaderboard
(pass / time / tokens / cost / edits in one view)."""
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
    w = max(len(m) for m in models + ["model", "TOTAL"])

    # gather everything per model
    rows = []
    for m in models:
        results, edits, u = load(m)
        by = {r["project"]: r["status"] for r in results}
        passed = sum(by.get(p) == "pass" for p in projects)
        secs = u.get("duration_ms", 0) / 1000 if u else None
        intok = (u.get("input_tokens", 0) + u.get("cache_read", 0)
                 + u.get("cache_creation", 0)) if u else None
        outtok = u.get("output_tokens", 0) if u else None
        cost = u.get("cost_usd", 0.0) if u else None
        rows.append({"m": m, "by": by, "pass": passed, "edits": edits,
                     "secs": secs, "in": intok, "out": outtok, "cost": cost})

    # best first: most passes, then fastest
    rows.sort(key=lambda r: (-r["pass"], r["secs"] if r["secs"] is not None else 9e9))

    # --- Table 1: per-project results grid ---
    head = "model".ljust(w) + " | " + " | ".join(s[:8].center(8) for s in short) + " | pass"
    print(head)
    print("-" * len(head))
    for r in rows:
        cells = [("PASS" if r["by"].get(p) == "pass" else "FAIL").center(8) for p in projects]
        print(r["m"].ljust(w) + " | " + " | ".join(cells) + f" | {r['pass']}/{len(projects)}")

    # --- Table 2: leaderboard (score + cost/speed/size in one place) ---
    print()
    head2 = (f"{'model'.ljust(w)} | {'pass':>4} | {'time':>7} | {'in tok':>8} "
             f"| {'out tok':>8} | {'turns':>5} | {'cost USD':>9} | {'edits(+/-)':>13}")
    print(head2)
    print("-" * len(head2))
    tot = {"in": 0, "out": 0, "cost": 0.0, "s": 0.0, "turns": 0}
    for r in rows:
        u_ok = r["secs"] is not None
        secs = f"{r['secs']:6.0f}s" if u_ok else f"{'-':>7}"
        intok = f"{k(r['in']):>8}" if u_ok else f"{'-':>8}"
        outtok = f"{k(r['out']):>8}" if u_ok else f"{'-':>8}"
        cost = f"{r['cost']:9.4f}" if u_ok else f"{'-':>9}"
        _, _, u = load(r["m"])
        turns = f"{u.get('num_turns', 0):>5}" if u_ok else f"{'-':>5}"
        edits = (f"+{r['edits']['insertions']}/-{r['edits']['deletions']} "
                 f"({r['edits']['files']}f)") if r["edits"] else "-"
        if u_ok:
            tot["s"] += r["secs"]; tot["in"] += r["in"]; tot["out"] += r["out"]
            tot["cost"] += r["cost"]; tot["turns"] += u.get("num_turns", 0)
        pstr = f"{r['pass']}/{len(projects)}"
        print(f"{r['m'].ljust(w)} | {pstr:>4} | {secs} | {intok} | {outtok} "
              f"| {turns} | {cost} | {edits:>13}")
    print("-" * len(head2))
    print(f"{'TOTAL'.ljust(w)} | {'':>4} | {tot['s']:6.0f}s | {k(tot['in']):>8} "
          f"| {k(tot['out']):>8} | {tot['turns']:>5} | {tot['cost']:9.4f} | {'':>13}")


if __name__ == "__main__":
    main()
