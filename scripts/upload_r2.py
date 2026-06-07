#!/usr/bin/env python3
"""Upload the manifest to R2 via the Cloudflare REST object API, using curl.

PUT https://api.cloudflare.com/client/v4/accounts/<acct>/r2/buckets/<bucket>/objects/<key>
with Authorization: Bearer <CLOUDFLARE_API_TOKEN> and Content-Type from the
manifest; body = file bytes.

Why curl + this endpoint (not `wrangler r2 object put`, not the ingest worker):
  - The moonraker-r2-worker ingest endpoint only accepts client-site key shapes
    (sites/<slug>/preview|prod/vN/..., migration/...), NOT moonraker.ai's flat
    `moonraker-website/` prefix, so it 400s "Invalid key shape".
  - `wrangler r2 object put` spawns a node process AND makes several API calls per
    file (token verify, metrics, the put). In bulk that blows past the REST rate
    limit (HTTP 429 / code 10429). curl makes exactly ONE call per file.
  - Low concurrency + bounded backoff keeps total calls under the ~1200/5min API
    budget.

Env: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID. Manifest: /tmp/mr_r2_manifest.tsv
"""
import os, sys, time, json, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

MANIFEST = "/tmp/mr_r2_manifest.tsv"
BUCKET = "client-sites"
ACCOUNT = os.getenv("CLOUDFLARE_ACCOUNT_ID") or ""
TOKEN = os.getenv("CLOUDFLARE_API_TOKEN") or ""
if not ACCOUNT or not TOKEN:
    sys.exit("ERROR: CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN not set (publish_r2.sh pulls them from the VPS).")

API = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/r2/buckets/{BUCKET}/objects"
rows = [l.rstrip("\n").split("\t") for l in open(MANIFEST) if l.strip()]

def enc(key):
    return "/".join(quote(seg, safe="") for seg in key.split("/"))

def _curl_json(url):
    cmd = ["curl", "-sS", url, "-H", f"Authorization: Bearer {TOKEN}", "--max-time", "60"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=80)
        return json.loads(p.stdout or "{}")
    except Exception:
        return {}

def list_keys(prefix):
    """Every object key under prefix, following the R2 list cursor."""
    keys, cursor = [], ""
    for _ in range(500):  # hard page cap (500k objects) so a bad cursor can't loop forever
        url = f"{API}?prefix={quote(prefix, safe='')}&per_page=1000"
        if cursor:
            url += f"&cursor={quote(cursor, safe='')}"
        d = _curl_json(url)
        if not d.get("success"):
            raise RuntimeError(f"list failed: {d.get('errors')}")
        keys.extend(o["key"] for o in d.get("result", []))
        info = d.get("result_info") or {}
        cursor = info.get("cursor") or ""
        if not info.get("is_truncated"):
            break
    return keys

def delete_key(key):
    cmd = ["curl", "-sS", "-X", "DELETE", f"{API}/{enc(key)}",
           "-H", f"Authorization: Bearer {TOKEN}",
           "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "60"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=80)
    except subprocess.TimeoutExpired:
        return False
    return (p.stdout or "").strip().startswith("2")

def put(row):
    localpath, key, ct = row
    url = f"{API}/{enc(key)}"
    cmd = [
        "curl", "-sS", "-X", "PUT", url,
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", f"Content-Type: {ct}",
        "--data-binary", f"@{localpath}",
        "-o", "/dev/null", "-w", "%{http_code}",
        "--max-time", "120",
    ]
    last = "fail"
    for attempt in range(5):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        except subprocess.TimeoutExpired:
            last = "timeout"; time.sleep(min(2 ** attempt, 30)); continue
        code = (p.stdout or "").strip()
        if code.startswith("2"):
            return (key, True, "")
        last = f"HTTP {code or 'curl-err'}"
        if code in ("429", "500", "502", "503", "504", "000", ""):
            # gentle backoff to stay under the REST rate limit
            time.sleep(min(3 * (2 ** attempt), 45) + attempt)
            continue
        return (key, False, last)
    return (key, False, last)

fails = []
done = 0
# concurrency 2: one call per file, paced to avoid the REST rate limit.
with ThreadPoolExecutor(max_workers=2) as ex:
    futs = {ex.submit(put, r): r for r in rows}
    for f in as_completed(futs):
        key, ok, err = f.result()
        done += 1
        if not ok:
            fails.append((key, err))
        if done % 20 == 0 or not ok:
            sys.stderr.write(f"[{done}/{len(rows)}] {'OK ' if ok else 'FAIL'} {key} {err}\n")
            sys.stderr.flush()

print(f"uploaded {len(rows)-len(fails)}/{len(rows)}")

# ---- prune: delete bucket objects no longer in the manifest ----
# Catches stale slugs / renamed-or-removed pages (the upload only PUTs the current
# set, it never deletes). Fail-safe: skip if the upload was not clean (we must not
# delete a key that just failed to re-upload), and never delete more than half the
# prefix in one run (guards against a truncated manifest wiping the live site).
PREFIX = (rows[0][1].split("/")[0] + "/") if rows else ""
if fails:
    print("skip prune: upload had failures (won't delete while the live set is uncertain)")
elif PREFIX:
    live = {r[1] for r in rows}
    try:
        existing = list_keys(PREFIX)
    except Exception as e:
        existing = None
        print(f"skip prune: list failed: {e}")
    if existing is not None:
        orphans = [k for k in existing if k not in live]
        if orphans and len(orphans) > max(20, len(existing) // 2):
            print(f"skip prune: {len(orphans)} orphans exceeds safety threshold "
                  f"(half of {len(existing)} live objects); delete manually if intended")
        elif orphans:
            pdone = 0
            for k in orphans:
                if delete_key(k):
                    pdone += 1
                    sys.stderr.write(f"pruned {k}\n")
                else:
                    sys.stderr.write(f"prune FAIL {k}\n")
            print(f"pruned {pdone}/{len(orphans)} stale objects")
        else:
            print("prune: no stale objects")

if fails:
    print("FAILURES:")
    for k, e in fails[:20]:
        print(f"  {k}: {e}")
    sys.exit(1)
