#!/usr/bin/env python3
"""Tier-1 a11y/SEO discovery across all page HTML files (no full-file dumps)."""
import os, re, glob

ROOT = os.path.join(os.path.dirname(__file__), "..")
pages = sorted(glob.glob(os.path.join(ROOT, "index.html")) +
               glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True))
# de-dup
pages = sorted(set(os.path.relpath(p, ROOT) for p in pages))

def first(pat, html, flags=re.I|re.S):
    m = re.search(pat, html, flags)
    return (m.group(1).strip()[:120] if m else None)

for rel in pages:
    if "node_modules" in rel:
        continue
    html = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
    title = first(r"<title[^>]*>(.*?)</title>", html)
    has_desc = bool(re.search(r'<meta\s+name=["\']description["\']', html, re.I))
    og_desc = first(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html)
    # imgs: total vs missing alt attribute entirely
    imgs = re.findall(r"<img\b[^>]*>", html, re.I)
    img_no_alt = [t for t in imgs if not re.search(r'\balt\s*=', t, re.I)]
    # iframes: total vs missing title
    iframes = re.findall(r"<iframe\b[^>]*>", html, re.I)
    if_no_title = [t for t in iframes if not re.search(r'\btitle\s*=', t, re.I)]
    # headings present (for heading-order context)
    hs = re.findall(r"<h([1-6])\b", html, re.I)
    hcount = {f"h{n}": hs.count(str(n)) for n in range(1,7) if hs.count(str(n))}
    print(f"\n## {rel}")
    print(f"   title: {title}")
    print(f"   meta-desc present: {has_desc} | og:desc: {og_desc!r}")
    print(f"   imgs: {len(imgs)} total, {len(img_no_alt)} missing alt")
    print(f"   iframes: {len(iframes)} total, {len(if_no_title)} missing title")
    print(f"   headings: {hcount}")
