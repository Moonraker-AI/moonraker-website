#!/usr/bin/env bash
# Publish moonraker.ai to R2 (the deploy path after the Vercel -> CF R2 migration).
#
# What it does:
#   1. astro build  -> renders the site into dist/ (the Astro generator)
#   2. ship dist/ + the R2 scripts to the VPS
#   3. on the VPS: build_r2.py (markdown siblings + upload manifest from dist/)
#      then upload_r2.py (Cloudflare REST object API PUT via curl, one call/file)
#
# Why the upload runs ON THE VPS:
#   - The R2-write Cloudflare token (CF_API_TOKEN) lives in the VPS agent .env and
#     works from that host. A local shell often has a DEAD CLOUDFLARE_API_TOKEN that
#     shadows any pull (401), and Cloudflare's edge WAF 1010-bans local automated
#     clients. Running on the VPS sidesteps both and keeps the secret on the box.
#   - The moonraker-r2-worker INGEST endpoint cannot be used here: it only accepts
#     client-site key shapes (sites/<slug>/preview|prod/vN/...), not the flat
#     `moonraker-website/` prefix this site serves from (it 400s "Invalid key shape").
#   - `wrangler r2 object put` makes several REST calls per file; in bulk that trips
#     the REST rate limit (HTTP 429 / code 10429). upload_r2.py uses ONE curl PUT
#     per file at low concurrency.
#
# After publish: the worker edge-caches HTML. The CF_API_TOKEN lacks cache_purge,
# so either purge the moonraker.ai cache in the Cloudflare dashboard or wait for
# the edge TTL for updates to appear.
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
VPS="root@87.99.133.69"

echo "==> building Astro site into dist/"
( cd "$DIR" && npm ci && npx astro build )

echo "==> shipping dist/ + scripts to the VPS"
tar czf /tmp/mrpub.tgz -C "$DIR" dist scripts/build_r2.py scripts/upload_r2.py
scp -q /tmp/mrpub.tgz "$VPS:/tmp/mrpub.tgz"
rm -f /tmp/mrpub.tgz

echo "==> generating manifest + uploading to R2 (client-sites/moonraker-website/) on the VPS"
ssh "$VPS" 'set -e; rm -rf /tmp/mrpub && mkdir -p /tmp/mrpub && tar xzf /tmp/mrpub.tgz -C /tmp/mrpub && cd /tmp/mrpub && python3 scripts/build_r2.py && set -a; . /opt/moonraker-agent/.env; set +a; export CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-$CF_API_TOKEN}" CLOUDFLARE_ACCOUNT_ID="$CF_ACCOUNT_ID"; python3 scripts/upload_r2.py; rm -rf /tmp/mrpub /tmp/mrpub.tgz'

echo "==> done. Purge the moonraker.ai cache in the Cloudflare dashboard (token lacks cache_purge), or wait for the edge TTL."
echo "    Worker code change? cd worker && npx wrangler deploy"
