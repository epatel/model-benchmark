#!/usr/bin/env python3
"""Print a comparison table from reports/<model>.results.json + .metrics.json."""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")


def load(model):
    with open(os.path.join(REPORTS, f"{model}.results.json")) as f:
        results = json.load(f)
    edits = None
    mpath = os.path.join(REPORTS, f"{model}.metrics.json")
    if os.path.exists(mpath):
        with open(mpath) as f:
            edits = json.load(f).get("total")
    return results, edits


def main():
    models = sorted(
        os.path.basename(p)[: -len(".results.json")]
        for p in glob.glob(os.path.join(REPORTS, "*.results.json"))
    )
    if not models:
        print("no reports yet — run ./run_models.sh first")
        return

    # project order from the first model's results
    projects = [r["project"] for r in load(models[0])[0]]
    short = [p.split("-", 1)[1] if "-" in p else p for p in projects]

    w = max(len(m) for m in models + ["model"])
    header = "model".ljust(w) + " | " + " | ".join(s[:8].center(8) for s in short)
    header += " | pass | edits(+/-)"
    print(header)
    print("-" * len(header))

    for m in models:
        results, edits = load(m)
        by = {r["project"]: r["status"] for r in results}
        cells = []
        passed = 0
        for p in projects:
            ok = by.get(p) == "pass"
            passed += ok
            cells.append(("PASS" if ok else "FAIL").center(8))
        edit_str = "-"
        if edits:
            edit_str = f"+{edits['insertions']}/-{edits['deletions']} ({edits['files']}f)"
        row = m.ljust(w) + " | " + " | ".join(cells)
        row += f" | {passed}/{len(projects)} | {edit_str}"
        print(row)


if __name__ == "__main__":
    main()
