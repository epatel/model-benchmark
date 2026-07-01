#!/usr/bin/env python3
"""Generate a self-contained HTML evaluation report to stdout.

Real <table> leaderboard + results grid, and side-by-side diffs (difflib) for
every model's edits per task, each collapsible. Data comes from reports/ and the
model/* / grade/* branches via git.

Usage: report_html.py [date-label] > out.html
"""
import glob
import html
import json
import os
import subprocess
import sys
from difflib import HtmlDiff

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT,
                          capture_output=True, text=True).stdout


def has_ref(ref):
    return subprocess.run(["git", "rev-parse", "--verify", "-q", ref],
                          cwd=ROOT, capture_output=True).returncode == 0


BASE = "main" if has_ref("main") else "base"
DATE = sys.argv[1] if len(sys.argv) > 1 else "run"


def read(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def kfmt(n):
    return f"{n/1000:.1f}k" if n and n >= 1000 else str(n or 0)


models = sorted(os.path.basename(p)[:-len(".results.json")]
                for p in glob.glob(os.path.join(ROOT, "reports/*.results.json")))
projects = sorted(d for d in os.listdir(os.path.join(ROOT, "projects"))
                  if os.path.isdir(os.path.join(ROOT, "projects", d)))

data = {}
for m in models:
    res = read(f"{ROOT}/reports/{m}.results.json") or []
    usage = read(f"{ROOT}/reports/{m}.usage.json") or {}
    metrics = (read(f"{ROOT}/reports/{m}.metrics.json") or {}).get("total")
    by = {r["project"]: r for r in res}
    passed = sum(1 for r in res if r["status"] == "pass")
    data[m] = {"by": by, "pass": passed, "usage": usage, "edits": metrics}

order = sorted(models, key=lambda m: (-data[m]["pass"],
               data[m]["usage"].get("duration_ms", 9e18)))

E = html.escape
out = []
w = out.append

w("<!doctype html><html lang=en><head><meta charset=utf-8>")
w(f"<title>Evaluation {E(DATE)}</title>")
w("<style>")
w(HtmlDiff._styles)  # difflib defaults FIRST, so our rules below win
w("""
:root{color-scheme:light dark}
body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:24px;max-width:1200px;margin:auto}
h1{margin:0 0 4px}h2{margin-top:36px;border-bottom:2px solid #8884;padding-bottom:4px}
.sub{color:#888;margin-bottom:20px}
table.grid{border-collapse:collapse;margin:10px 0;font-size:13px}
table.grid th,table.grid td{border:1px solid #8883;padding:5px 9px;text-align:center;white-space:nowrap}
table.grid th{background:#8881;position:sticky;top:0}
table.grid td.model,table.grid th.model{text-align:left;font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.pass{background:#3faf4622;color:#2e7d32;font-weight:600}
.fail{background:#e5393522;color:#c62828;font-weight:600}
details{margin:6px 0;border:1px solid #8883;border-radius:6px}
details>summary{cursor:pointer;padding:6px 10px;background:#8881;border-radius:6px;font-family:ui-monospace,monospace;font-size:13px}
details[open]>summary{border-bottom:1px solid #8883;border-radius:6px 6px 0 0}
.fail-summary{color:#c62828}
pre.fail{background:#e5393511;padding:10px;overflow:auto;border-radius:0 0 6px 6px;margin:0}

/* Diffs: force a light, high-contrast (GitHub-like) surface with DARK text,
   independent of the page's dark mode, so highlighted cells stay legible. */
.diffwrap{overflow:auto;padding:0;background:#fff;border-radius:0 0 6px 6px}
.diffwrap>div{color:#57606a;padding:8px 8px 2px}
table.diff{background:#fff;color:#1f2328;border-collapse:collapse;width:100%;
           font-family:ui-monospace,SFMono-Regular,monospace;font-size:12px}
table.diff td{padding:0 6px;vertical-align:top;white-space:pre;color:#1f2328}
table.diff .diff_header{background:#f6f8fa;color:#8c959f;text-align:right;user-select:none;padding-right:8px}
table.diff .diff_next{background:#f6f8fa;color:#8c959f}
table.diff .diff_add{background:#d1f8d9;color:#1f2328}
table.diff .diff_chg{background:#fff3c9;color:#1f2328}
table.diff .diff_sub{background:#ffd0cd;color:#1f2328}
""")
w("</style></head><body>")

w(f"<h1>Combined evaluation — {E(DATE)}</h1>")
w(f"<div class=sub>{len(models)} models &times; {len(projects)} tasks · "
  f"grading = hidden-test oracle · diffs vs <code>{E(BASE)}</code></div>")

# ---- results grid ----
w("<h2>Results</h2><table class=grid><tr><th class=model>model</th>")
for p in projects:
    short = p.split("-", 1)[1] if "-" in p else p
    w(f"<th>{E(short)}</th>")
w("<th>pass</th></tr>")
for m in order:
    w(f"<tr><td class=model>{E(m)}</td>")
    for p in projects:
        st = data[m]["by"].get(p, {}).get("status", "?")
        cls = "pass" if st == "pass" else "fail"
        w(f'<td class={cls}>{"PASS" if st=="pass" else "FAIL"}</td>')
    w(f'<td class=num>{data[m]["pass"]}/{len(projects)}</td></tr>')
w("</table>")

# ---- leaderboard (efficiency) ----
w("<h2>Leaderboard</h2><table class=grid>")
w("<tr><th class=model>model</th><th>pass</th><th>time</th><th>in tok</th>"
  "<th>out tok</th><th>turns</th><th>cost USD</th><th>edits (+/-)</th></tr>")
for m in order:
    u = data[m]["usage"]
    secs = f'{u.get("duration_ms",0)/1000:.0f}s' if u else "-"
    intok = kfmt(u.get("input_tokens", 0) + u.get("cache_read", 0) + u.get("cache_creation", 0)) if u else "-"
    outtok = kfmt(u.get("output_tokens", 0)) if u else "-"
    turns = u.get("num_turns", "-") if u else "-"
    cost = f'{u.get("cost_usd",0):.4f}' if u else "-"
    ed = data[m]["edits"]
    edits = f'+{ed["insertions"]}/-{ed["deletions"]} ({ed["files"]}f)' if ed else "-"
    w(f'<tr><td class=model>{E(m)}</td><td class=num>{data[m]["pass"]}/{len(projects)}</td>'
      f'<td class=num>{secs}</td><td class=num>{intok}</td><td class=num>{outtok}</td>'
      f'<td class=num>{turns}</td><td class=num>{cost}</td><td class=num>{E(edits)}</td></tr>')
w("</table>")

# ---- failure detail ----
w("<h2>Failure detail</h2>")
anyfail = False
for m in order:
    for p in projects:
        if data[m]["by"].get(p, {}).get("status") == "pass":
            continue
        if p not in data[m]["by"]:
            continue
        anyfail = True
        detail = ""
        if has_ref(f"grade/{m}"):
            wt = subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip()
            if subprocess.run(["git", "worktree", "add", "-q", "--detach", wt, f"grade/{m}"],
                              cwd=ROOT, capture_output=True).returncode == 0:
                r = subprocess.run(["bash", f"projects/{p}/run_tests.sh"], cwd=wt,
                                   capture_output=True, text=True)
                lines = [ln for ln in (r.stdout + r.stderr).splitlines()
                         if any(t in ln.lower() for t in
                                ("fail", "error", "assert", "expected", "want", "got", "!=", "traceback"))]
                detail = "\n".join(lines[:14])
                subprocess.run(["git", "worktree", "remove", "--force", wt], cwd=ROOT, capture_output=True)
        w(f'<details><summary class=fail-summary>{E(m)} — {E(p)}</summary>'
          f'<pre class=fail>{E(detail or "(no detail)")}</pre></details>')
if not anyfail:
    w("<p>None — every model passed every task. 🎉</p>")

# ---- solutions by task (side-by-side diffs) ----
w("<h2>Solutions by task</h2>")
hd = HtmlDiff(wrapcolumn=76)
for p in projects:
    w(f"<h3>{E(p)}</h3>")
    for m in order:
        if not has_ref(f"model/{m}"):
            continue
        files = [f for f in git("diff", "--name-only", BASE, f"model/{m}",
                                "--", f"projects/{p}").splitlines() if f.strip()]
        if not files:
            continue
        st = data[m]["by"].get(p, {}).get("status", "?")
        badge = "✅ PASS" if st == "pass" else "❌ FAIL"
        cls = "" if st == "pass" else " class=fail-summary"
        w(f'<details><summary{cls}>{E(m)} — {badge} · {len(files)} file(s)</summary><div class=diffwrap>')
        for f in files:
            a = git("show", f"{BASE}:{f}").splitlines()
            b = git("show", f"model/{m}:{f}").splitlines()
            w(f"<div style='color:#888;font-family:monospace;margin:8px 0 2px'>{E(f)}</div>")
            w(hd.make_table(a, b, BASE, m, context=True, numlines=3))
        w("</div></details>")

w("</body></html>")
sys.stdout.write("\n".join(out))
