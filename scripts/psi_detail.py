#!/usr/bin/env python3
"""Pull actionable element-level detail for the top fixable audits (homepage focus)."""
import json, os

RAW = os.path.join(os.path.dirname(__file__), "..", "_audit", "psi_raw.json")
raw = json.load(open(RAW))

def page(key):
    return raw.get(key, {}).get("lighthouseResult", {}).get("audits", {})

def items_of(audits, aid, fields):
    a = audits.get(aid, {})
    det = a.get("details", {}) or {}
    out = []
    for it in det.get("items", [])[:12]:
        row = {}
        for f in fields:
            v = it.get(f)
            if isinstance(v, dict):
                v = v.get("snippet") or v.get("value") or v.get("url") or str(v)[:80]
            row[f] = v
        out.append(row)
    return out

# Homepage mobile = worst perf; use for element detail
hp = page("/|mobile")

print("### REDIRECTS (homepage mobile)")
a = hp.get("redirects", {})
for it in (a.get("details", {}) or {}).get("items", [])[:8]:
    print(f"   {it.get('url','')}  +{int(it.get('wastedMs',0))}ms")

print("\n### IMAGE-ALT culprits (homepage)")
for r in items_of(hp, "image-alt", ["node"]):
    print("   ", r)

print("\n### FRAME-TITLE culprits (homepage)")
for r in items_of(hp, "frame-title", ["node"]):
    print("   ", r)

print("\n### HEADING-ORDER culprits (homepage)")
for r in items_of(hp, "heading-order", ["node"]):
    print("   ", r)

print("\n### LIST culprits (homepage)")
for r in items_of(hp, "list", ["node"]):
    print("   ", r)

print("\n### COLOR-CONTRAST culprits (homepage)")
for r in items_of(hp, "color-contrast", ["node"]):
    print("   ", r)

print("\n### ERRORS-IN-CONSOLE (homepage)")
for r in items_of(hp, "errors-in-console", ["source", "description"]):
    print("   ", r)

print("\n### THIRD-PARTY-COOKIES (homepage)")
for r in items_of(hp, "third-party-cookies", ["name", "url"]):
    print("   ", r)

print("\n### TOTAL-BYTE-WEIGHT (homepage, top resources)")
for r in items_of(hp, "total-byte-weight", ["url", "totalBytes"]):
    print("   ", r)
