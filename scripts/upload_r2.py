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
import os, sys, time, subprocess
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
if fails:
    print("FAILURES:")
    for k, e in fails[:20]:
        print(f"  {k}: {e}")
    sys.exit(1)
