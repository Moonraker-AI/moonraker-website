#!/usr/bin/env bash
# Publish moonraker.ai to R2 (the deploy path after the Vercel -> CF R2 migration).
#
# What it does:
#   1. astro build  -> renders the site into dist/ (the Astro generator)
#   2. build_r2.py  -> regenerates markdown siblings + the upload manifest from dist/
#   3. upload_r2.py -> pushes all dist files + .md to client-sites/moonraker-website/
#
# HTML cache TTL is 300s at the edge, so content updates show within ~5 min.
# Worker CODE changes are separate: cd worker && npx wrangler deploy
#
# Auth: CLOUDFLARE_API_TOKEN (Workers + R2 scope). Pulled from the VPS agent env
# if not already set. Account is the Moonraker CF account.
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
: "${CLOUDFLARE_API_TOKEN:=$(ssh root@87.99.133.69 'grep -iE "^CLOUDFLARE_API_TOKEN=|^CF_API_TOKEN=" /opt/moonraker-agent/.env | head -1 | cut -d= -f2-')}"
export CLOUDFLARE_API_TOKEN
export CLOUDFLARE_ACCOUNT_ID="b0d0e7ccfcabdec0507b4cac779f048a"

echo "==> building Astro site into dist/"
( cd "$DIR" && npm ci && npx astro build )

echo "==> generating markdown + manifest from dist/"
python3 "$DIR/scripts/build_r2.py"

echo "==> uploading to R2 (client-sites/moonraker-website/)"
python3 "$DIR/scripts/upload_r2.py"

echo "==> done. Edge HTML TTL is 300s; updates are live within ~5 min."
echo "    Worker code change? cd worker && npx wrangler deploy"
