#!/usr/bin/env python3
"""Full-site PageSpeed Insights audit for moonraker.ai.

Loops every page x {mobile, desktop}, all 4 Lighthouse categories.
Writes a markdown report + raw JSON; prints only a compact score table.
PSI_API_KEY read from env (never printed).
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone

KEY = os.environ.get("PSI_API_KEY", "").strip()
BASE = os.environ.get("MR_BASE", "https://moonraker.ai").rstrip("/")
SLUG = "".join(c if c.isalnum() else "_" for c in BASE.split("//")[-1])
PATHS = [
    "/", "/core-marketing-system/", "/core-marketing-system/credibility/",
    "/core-marketing-system/engagement/", "/core-marketing-system/optimization/",
    "/core-marketing-system/reputation/", "/process/", "/results/", "/scope/",
    "/team/", "/knowledge-hub/", "/book-a-call/", "/free-strategy-call/",
    "/reschedule/", "/cancel/", "/privacy/", "/terms/",
]
CATS = ["PERFORMANCE", "ACCESSIBILITY", "BEST_PRACTICES", "SEO"]
STRATS = ["mobile", "desktop"]
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "_audit")
os.makedirs(OUT_DIR, exist_ok=True)
RAW_PATH = os.path.join(OUT_DIR, f"psi_raw_{SLUG}.json")
MD_PATH = os.path.join(OUT_DIR, f"PSI_REPORT_{SLUG}.md")
ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

def fetch(url, strategy):
    q = [("url", url), ("strategy", strategy)]
    q += [("category", c) for c in CATS]
    if KEY:
        q.append(("key", KEY))
    full = ENDPOINT + "?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(full, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            return {"error": f"HTTP {e.code}: {e.read()[:200].decode('utf-8','replace')}"}
        except Exception as e:
            if attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            return {"error": str(e)}
    return {"error": "exhausted retries"}

def score(lr, cat):
    c = lr.get("categories", {}).get(cat.lower().replace("_", "-"))
    if c and c.get("score") is not None:
        return round(c["score"] * 100)
    return None

def metric(lr, audit_id):
    a = lr.get("audits", {}).get(audit_id, {})
    return a.get("displayValue", "")

def opportunities(lr, limit=6):
    out = []
    for aid, a in lr.get("audits", {}).items():
        s = a.get("score")
        det = a.get("details", {})
        savings = det.get("overallSavingsMs") or 0
        if s is not None and s < 0.9 and a.get("scoreDisplayMode") in ("metricSavings", "numeric", "binary"):
            if savings or a.get("scoreDisplayMode") in ("numeric", "binary"):
                out.append((savings, aid, a.get("title", ""), round((s or 0) * 100)))
    out.sort(key=lambda x: (-x[0], x[3]))
    return out[:limit]

results = {}
table = []
raw = {}
total = len(PATHS) * len(STRATS)
i = 0
for p in PATHS:
    url = BASE + p
    for strat in STRATS:
        i += 1
        sys.stderr.write(f"[{i}/{total}] {strat:7} {p}\n"); sys.stderr.flush()
        data = fetch(url, strat)
        raw[f"{p}|{strat}"] = data
        if "error" in data and "lighthouseResult" not in data:
            table.append((p, strat, None, None, None, None, "ERR:" + data["error"][:40]))
            continue
        lr = data.get("lighthouseResult", {})
        perf = score(lr, "PERFORMANCE")
        a11y = score(lr, "ACCESSIBILITY")
        bp = score(lr, "BEST_PRACTICES")
        seo = score(lr, "SEO")
        lcp = metric(lr, "largest-contentful-paint")
        cls = metric(lr, "cumulative-layout-shift")
        tbt = metric(lr, "total-blocking-time")
        results[f"{p}|{strat}"] = {
            "scores": {"perf": perf, "a11y": a11y, "bp": bp, "seo": seo},
            "cwv": {"lcp": lcp, "cls": cls, "tbt": tbt,
                    "fcp": metric(lr, "first-contentful-paint"),
                    "si": metric(lr, "speed-index")},
            "opps": opportunities(lr),
        }
        table.append((p, strat, perf, a11y, bp, seo, f"LCP {lcp} / CLS {cls} / TBT {tbt}"))
        time.sleep(0.5)

with open(RAW_PATH, "w") as f:
    json.dump(raw, f)

# markdown report
lines = [f"# moonraker.ai PageSpeed Audit", "",
         f"Generated: {datetime.now(timezone.utc).isoformat()}",
         f"Pages: {len(PATHS)} x {len(STRATS)} strategies, categories: {', '.join(CATS)}", "",
         "## Score matrix (Perf / A11y / BestPractices / SEO)", "",
         "| Page | Strat | Perf | A11y | BP | SEO | CWV |",
         "|---|---|---|---|---|---|---|"]
def fmt(v): return "-" if v is None else str(v)
for row in table:
    p, strat, perf, a11y, bp, seo, note = row
    lines.append(f"| {p} | {strat} | {fmt(perf)} | {fmt(a11y)} | {fmt(bp)} | {fmt(seo)} | {note} |")

lines += ["", "## Per-page opportunities (score < 90)", ""]
for k, v in results.items():
    if not v["opps"]:
        continue
    lines.append(f"### {k}")
    for savings, aid, title, s in v["opps"]:
        sv = f" (~{int(savings)}ms)" if savings else ""
        lines.append(f"- [{s}] {aid}: {title}{sv}")
    lines.append("")

with open(MD_PATH, "w") as f:
    f.write("\n".join(lines))

# compact stdout
print("PAGE,STRAT,PERF,A11Y,BP,SEO")
for row in table:
    p, strat, perf, a11y, bp, seo, note = row
    print(f"{p},{strat},{fmt(perf)},{fmt(a11y)},{fmt(bp)},{fmt(seo)}")
print(f"\nRaw: {os.path.relpath(RAW_PATH)}\nReport: {os.path.relpath(MD_PATH)}")
