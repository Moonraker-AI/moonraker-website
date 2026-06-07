#!/usr/bin/env bash
# vps_publish.sh: build + publish moonraker.ai to R2 entirely ON THE VPS.
#
# This is the server-resident twin of publish_r2.sh (which builds on a local
# machine then ships dist/). Here the build runs on the VPS host, so a publish
# can be triggered with no local machine in the loop: a content piece is
# published in client-hq -> publish_watch.py notices -> this runs.
#
# Prereqs on the host (one-time, see scripts/vps_setup_publish.sh):
#   - Node 20 + npm
#   - /opt/moonraker-website is a clone of this repo
#   - /opt/moonraker-agent/.env holds SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
#     CF_API_TOKEN, CF_ACCOUNT_ID
#
# Env mapping:
#   - The Astro build (src/lib/content.js) reads SUPABASE_URL + SUPABASE_ANON_KEY
#     at BUILD time to fetch published content_pieces. The host .env carries the
#     service-role key, not an anon key; we map it in. That key only ever reads
#     published rows here and the output is public HTML, so this is safe. It never
#     ships to the static output (getStaticPaths runs at build only).
#   - upload_r2.py wants CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID.
#
# After upload: the worker edge-caches HTML at s-maxage=300, so a publish appears
# within ~5 min without a purge. The CF token lacks cache_purge, so a one-time
# dashboard Purge is only needed for pages cached before the s-maxage fix.
set -euo pipefail

REPO="${MR_SITE_REPO:-/opt/moonraker-website}"
AGENT_ENV="${MR_AGENT_ENV:-/opt/moonraker-agent/.env}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] vps_publish: $*"; }

[ -d "$REPO/.git" ] || { echo "ERROR: $REPO is not a git clone" >&2; exit 1; }
[ -f "$AGENT_ENV" ] || { echo "ERROR: $AGENT_ENV not found" >&2; exit 1; }

# Serialize: never let two builds (cron + manual) overlap.
exec 9>/tmp/mr_site_publish.lock
flock -n 9 || { log "another publish is running; exiting"; exit 0; }

log "syncing repo to origin/main"
git -C "$REPO" fetch --quiet origin main
git -C "$REPO" reset --quiet --hard origin/main

# Pull the host secrets into this shell.
set -a; . "$AGENT_ENV"; set +a
export SUPABASE_URL
export SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-${SUPABASE_SERVICE_ROLE_KEY:-}}"
export CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-${CF_API_TOKEN:-}}"
export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-${CF_ACCOUNT_ID:-}}"
[ -n "${SUPABASE_URL:-}" ] && [ -n "${SUPABASE_ANON_KEY:-}" ] || { echo "ERROR: SUPABASE_URL / key missing" >&2; exit 1; }
[ -n "${CLOUDFLARE_API_TOKEN:-}" ] && [ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] || { echo "ERROR: CF token / account missing" >&2; exit 1; }

cd "$REPO"
log "npm ci"
npm ci --no-audit --no-fund --silent
log "astro build"
npx astro build
log "build_r2.py (manifest)"
python3 scripts/build_r2.py
log "upload_r2.py (R2)"
python3 scripts/upload_r2.py
log "done"
