#!/usr/bin/env python3
"""Build the R2 upload set for moonraker.ai:
- enumerate the static files we serve (html, assets, styles, AI files)
- generate a markdown sibling (.md) for each HTML page from its <main> content
- emit a manifest.tsv: localpath \t r2key \t content-type   (r2key prefixed)
Markdown stays out of the repo; written to a staging dir.
"""
import os, re, glob, html as htmllib
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGE = "/tmp/mr_r2_md"
PREFIX = "moonraker-website"
MANIFEST = "/tmp/mr_r2_manifest.tsv"

CT = {
    ".html": "text/html; charset=utf-8", ".md": "text/markdown; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".avif": "image/avif", ".svg": "image/svg+xml",
    ".ico": "image/x-icon", ".gif": "image/gif",
    ".txt": "text/plain; charset=utf-8", ".xml": "application/xml; charset=utf-8",
    ".json": "application/json; charset=utf-8", ".webmanifest": "application/manifest+json",
    ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf",
    ".mp4": "video/mp4", ".webm": "video/webm", ".pdf": "application/pdf",
}
def ct_for(p):
    return CT.get(os.path.splitext(p)[1].lower(), "application/octet-stream")

# ---- static file set (served from R2) ----
def static_files():
    files = []
    # all page HTML
    files += glob.glob(os.path.join(ROOT, "index.html"))
    files += glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True)
    # asset + style trees
    for d in ("assets", "styles"):
        files += glob.glob(os.path.join(ROOT, d, "**", "*"), recursive=True)
    # AI / discovery files at root
    for f in ("llms.txt", "robots.txt", "sitemap.xml", "llms-full.txt"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            files.append(p)
    out = []
    seen = set()
    for f in files:
        if os.path.isdir(f):
            continue
        rp = os.path.relpath(f, ROOT)
        if rp.startswith(("node_modules", "_audit", "scripts", ".git", ".vercel")):
            continue
        if rp in seen:
            continue
        seen.add(rp)
        out.append((f, rp))
    return out

# ---- minimal HTML -> Markdown for the <main> content ----
SKIP = {"script", "style", "svg", "nav", "footer", "select", "button", "form", "iframe", "noscript", "head"}
BLOCK = {"p", "div", "section", "article", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr"}

class MD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.tagstack = []
        self.href = None
        self.cur = []  # current inline buffer
    def flush(self, prefix=""):
        text = re.sub(r"[ \t]+", " ", "".join(self.cur)).strip()
        self.cur = []
        if text:
            self.out.append(prefix + text)
    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        a = dict(attrs)
        if tag in ("h1","h2","h3","h4","h5","h6"):
            self.flush(); self.tagstack.append(tag)
        elif tag == "p":
            self.flush()
        elif tag == "li":
            self.flush()
        elif tag == "a":
            self.href = a.get("href")
            self.cur.append("[")
        elif tag in ("strong","b"):
            self.cur.append("**")
        elif tag in ("em","i"):
            self.cur.append("*")
        elif tag == "br":
            self.flush()
    def handle_endtag(self, tag):
        if tag in SKIP:
            if self.skip_depth: self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in ("h1","h2","h3","h4","h5","h6"):
            level = int(tag[1])
            self.flush("#"*level + " ")
            if self.tagstack and self.tagstack[-1]==tag: self.tagstack.pop()
        elif tag == "p":
            self.flush()
        elif tag == "li":
            self.flush("- ")
        elif tag == "a":
            href = self.href or ""
            self.cur.append(f"]({href})" if href else "]")
            self.href = None
        elif tag in ("strong","b"):
            self.cur.append("**")
        elif tag in ("em","i"):
            self.cur.append("*")
    def handle_data(self, data):
        if self.skip_depth: return
        self.cur.append(data)
    def result(self):
        self.flush()
        lines = [l for l in self.out if l.strip()]
        return "\n\n".join(lines) + "\n"

def extract_main(html):
    m = re.search(r"<main\b[^>]*>(.*?)</main>", html, re.S|re.I)
    if m: return m.group(1)
    m = re.search(r"</nav>(.*?)<footer\b", html, re.S|re.I)
    if m: return m.group(1)
    m = re.search(r"<body\b[^>]*>(.*?)</body>", html, re.S|re.I)
    return m.group(1) if m else html

def title_of(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S|re.I)
    return htmllib.unescape(m.group(1).strip()) if m else "Moonraker"

def page_md(html):
    title = title_of(html)
    p = MD(); p.feed(extract_main(html))
    body = p.result()
    return f"# {title}\n\n{body}"

def main():
    os.makedirs(STAGE, exist_ok=True)
    rows = []
    statics = static_files()
    for localpath, rp in statics:
        rows.append((localpath, f"{PREFIX}/{rp}", ct_for(rp)))
    # markdown siblings for each index.html
    md_count = 0
    for localpath, rp in statics:
        if not rp.endswith("index.html"):
            continue
        html = open(localpath, encoding="utf-8", errors="replace").read()
        md = page_md(html)
        mdrel = rp[:-len("index.html")] + "index.md"
        stagepath = os.path.join(STAGE, mdrel)
        os.makedirs(os.path.dirname(stagepath), exist_ok=True)
        with open(stagepath, "w", encoding="utf-8") as f:
            f.write(md)
        rows.append((stagepath, f"{PREFIX}/{mdrel}", CT[".md"]))
        md_count += 1
    with open(MANIFEST, "w") as f:
        for lp, key, ct in rows:
            f.write(f"{lp}\t{key}\t{ct}\n")
    print(f"static files: {len(statics)} | markdown generated: {md_count} | manifest rows: {len(rows)}")
    print(f"manifest: {MANIFEST}")
    print("sample md (/process):")
    sp = os.path.join(STAGE, "process/index.md")
    if os.path.exists(sp):
        print("\n".join(open(sp).read().splitlines()[:8]))

if __name__ == "__main__":
    main()
