#!/usr/bin/env python3
"""publish_watch.py: rebuild moonraker.ai when published content changes.

Runs on the VPS host from cron (every few minutes). It asks Supabase for the
set of PUBLISHED content_pieces, fingerprints it, and compares that fingerprint
to a stored marker. When the fingerprint changes (a piece published, an existing
published piece edited, or one unpublished/deleted) it runs vps_publish.sh,
which rebuilds the static site and uploads to R2. No change -> no build.

This is the server-side "build trigger": publishing a piece in client-hq now
flows to the live site within one poll interval, with no local machine.

Secrets come from the agent .env (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY).
The fingerprint covers id + updated_at + status + slug, so any publish-relevant
mutation is caught. The published set is small, so this is a cheap request.

Exit codes: 0 = no change or a build that succeeded; non-zero = an error worth
surfacing in the cron log.
"""
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

AGENT_ENV = os.environ.get("MR_AGENT_ENV", "/opt/moonraker-agent/.env")
MARKER = os.environ.get("MR_SITE_MARKER", "/opt/moonraker-agent/.mr_site_publish_marker")
PUBLISH_SH = os.environ.get("MR_PUBLISH_SH", "/opt/moonraker-website/scripts/vps_publish.sh")


def load_env(path):
    """Minimal .env reader (KEY=VALUE lines); does not touch os.environ globally."""
    env = {}
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        sys.exit(f"ERROR: {path} not found")
    return env


def fingerprint(supabase_url, key):
    url = (
        supabase_url.rstrip("/")
        + "/rest/v1/content_pieces"
        + "?status=eq.published&select=id,updated_at,status,slug&order=id.asc"
    )
    req = urllib.request.Request(
        url, headers={"apikey": key, "Authorization": f"Bearer {key}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = json.loads(resp.read().decode())
    # Stable serialization -> stable hash regardless of key order.
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest(), len(rows)


def read_marker():
    try:
        with open(MARKER) as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return ""


def write_marker(value):
    with open(MARKER, "w") as fh:
        fh.write(value)


def main():
    env = load_env(AGENT_ENV)
    supabase_url = os.environ.get("SUPABASE_URL") or env.get("SUPABASE_URL")
    # Prefer the anon key (the poll only reads non-sensitive content_pieces
    # columns); service-role is a last resort and never reaches the build.
    key = (
        os.environ.get("SUPABASE_ANON_KEY")
        or env.get("SUPABASE_ANON_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or env.get("SUPABASE_SERVICE_ROLE_KEY")
    )
    if not supabase_url or not key:
        sys.exit("ERROR: SUPABASE_URL / key missing from env and agent .env")

    fp, count = fingerprint(supabase_url, key)
    prev = read_marker()
    if fp == prev:
        return  # no change, stay quiet

    print(f"published-content change detected ({count} published pieces); rebuilding")
    result = subprocess.run(["bash", PUBLISH_SH])
    if result.returncode != 0:
        sys.exit(f"ERROR: {PUBLISH_SH} exited {result.returncode}; marker NOT advanced")
    write_marker(fp)
    print("rebuild complete; marker advanced")


if __name__ == "__main__":
    main()
