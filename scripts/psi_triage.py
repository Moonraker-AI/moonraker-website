#!/usr/bin/env python3
"""Root-cause triage over psi_raw.json: which audits fail, how often, total savings."""
import json, os, collections

RAW = os.environ.get("PSI_RAW") or os.path.join(os.path.dirname(__file__), "..", "_audit", "psi_raw.json")
raw = json.load(open(RAW))

# category -> audit_id -> {count, pages:set, sample_title}
fails = {c: collections.defaultdict(lambda: {"count": 0, "pages": set(), "title": "", "savings": 0})
         for c in ["accessibility", "best-practices", "seo", "performance"]}

for key, data in raw.items():
    lr = data.get("lighthouseResult", {})
    if not lr:
        continue
    cats = lr.get("categories", {})
    audits = lr.get("audits", {})
    # map each category to its member audit refs
    for catkey, cat in cats.items():
        if catkey not in fails:
            continue
        for ref in cat.get("auditRefs", []):
            aid = ref["id"]
            a = audits.get(aid, {})
            s = a.get("score")
            mode = a.get("scoreDisplayMode")
            if mode in ("notApplicable", "informative", "manual"):
                continue
            if s is not None and s < 1:
                rec = fails[catkey][aid]
                rec["count"] += 1
                rec["pages"].add(key)
                rec["title"] = a.get("title", aid)
                sv = (a.get("details", {}) or {}).get("overallSavingsMs") or 0
                rec["savings"] += sv

for cat in ["accessibility", "best-practices", "seo", "performance"]:
    print(f"\n========== {cat.upper()} ==========")
    items = sorted(fails[cat].items(), key=lambda kv: (-kv[1]["count"], -kv[1]["savings"]))
    for aid, rec in items:
        sv = f" totSav~{int(rec['savings'])}ms" if rec["savings"] else ""
        print(f"  [{rec['count']:2}/34] {aid}: {rec['title']}{sv}")
