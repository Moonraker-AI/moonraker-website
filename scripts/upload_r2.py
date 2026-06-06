#!/usr/bin/env python3
"""Upload the manifest to R2 (client-sites bucket) concurrently via wrangler.
Env: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID. Manifest: /tmp/mr_r2_manifest.tsv
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

MANIFEST = "/tmp/mr_r2_manifest.tsv"
BUCKET = "client-sites"
rows = [l.rstrip("\n").split("\t") for l in open(MANIFEST) if l.strip()]
env = dict(os.environ)

def put(row):
    localpath, key, ct = row
    target = f"{BUCKET}/{key}"
    cmd = ["npx", "wrangler", "r2", "object", "put", target,
           "--file", localpath, "--content-type", ct, "--remote"]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    ok = p.returncode == 0
    return (key, ok, "" if ok else (p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "fail"))

fails = []
done = 0
with ThreadPoolExecutor(max_workers=6) as ex:
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
