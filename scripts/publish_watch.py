#!/usr/bin/env python3
"""publish_watch.py: rebuild moonraker.ai when published content OR code changes.

Runs on the VPS host from cron (every few minutes). It watches TWO things and
rebuilds when either moves:

  1. the set of PUBLISHED content_pieces in Supabase (fingerprinted), and
  2. the tip of origin/main for this repo.

Either delta runs vps_publish.sh, which resets the clone to origin/main,
rebuilds the static site, and uploads to R2. Neither -> no build.

Watching (2) is what makes "push to main publishes" actually true. Before it,
a plain code commit (a page edit, a CSS change, a copy fix) could NEVER reach
the live site without a human running vps_publish.sh by hand, because
content_pieces is blind to git. The marker and the log both sat frozen at
2026-06-08 for that reason.

NOTE: this covers the STATIC half only. A change under worker/ (CSP, security
headers, redirects, markdown negotiation) still needs a separate
`cd worker && npx wrangler deploy`; nothing here deploys the worker.

This is the server-side "build trigger": publishing a piece in client-hq, or
pushing a commit to main, flows to the live site within one poll interval, with
no local machine.

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
REPO = os.environ.get("MR_SITE_REPO", "/opt/moonraker-website")

# vps_publish.sh exits with this when another publish already holds the lock.
# Distinct from success, so the marker is not advanced for a build that never
# ran; the next poll picks the work back up.
EX_LOCK_HELD = 75


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


def origin_main_sha():
    """SHA of origin/main after a fetch, or None if it cannot be resolved.

    The fetch failure is deliberately NOT fatal. A GitHub outage would otherwise
    write a traceback into the cron log and exit non-zero every five minutes
    forever. On a failed fetch we fall back to the cached origin/main ref, which
    is stale at worst and can never be ahead of the real remote.
    """
    fetch = subprocess.run(
        ["git", "-C", REPO, "fetch", "--quiet", "origin", "main"],
        capture_output=True,
    )
    if fetch.returncode != 0:
        print("WARNING: git fetch failed; using the cached origin/main ref")
    out = subprocess.run(
        ["git", "-C", REPO, "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        print("WARNING: cannot resolve origin/main; commit check skipped this poll")
        return None
    return out.stdout.strip()


def built_sha(fallback=""):
    """HEAD after a build. vps_publish.sh resets the clone to origin/main as its
    first step, so HEAD post-build is exactly what got built, even if another
    push landed while the build was running.

    Never fatal, for the same reason origin_main_sha is not: this runs from cron
    every five minutes, and an unresolvable HEAD (an empty or half-initialised
    clone, a detached or corrupt repo) must not turn into a recurring traceback.
    Falls back to the SHA we set out to build, which vps_publish.sh has just
    reset the tree to anyway.
    """
    out = subprocess.run(
        ["git", "-C", REPO, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        print("WARNING: cannot resolve HEAD after the build; recording the fetched SHA")
        return fallback
    return out.stdout.strip()


def read_state():
    """Return {"content": <sha256>, "commit": <sha>}.

    Tolerates the legacy marker format, a bare content sha256 with no commit,
    which is what is on the box today. That reads as commit unknown, so the
    first poll after this ships publishes once and adopts the new format.
    """
    try:
        with open(MARKER) as fh:
            raw = fh.read().strip()
    except FileNotFoundError:
        return {"content": "", "commit": ""}
    if not raw:
        return {"content": "", "commit": ""}
    try:
        state = json.loads(raw)
        if isinstance(state, dict):
            return {
                "content": state.get("content", ""),
                "commit": state.get("commit", ""),
            }
    except json.JSONDecodeError:
        pass
    return {"content": raw, "commit": ""}


def write_state(content_fp, commit):
    with open(MARKER, "w") as fh:
        json.dump({"content": content_fp, "commit": commit}, fh)


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
    head = origin_main_sha()
    prev = read_state()

    reasons = []
    if fp != prev["content"]:
        reasons.append(f"published-content change ({count} published pieces)")
    if head and head != prev["commit"]:
        short = head[:8]
        was = prev["commit"][:8] if prev["commit"] else "unknown"
        reasons.append(f"new commit on origin/main ({was} -> {short})")

    if not reasons:
        return  # nothing moved, stay quiet

    print("rebuilding: " + "; ".join(reasons))
    result = subprocess.run(["bash", PUBLISH_SH])
    if result.returncode == EX_LOCK_HELD:
        # Another publish holds the lock, so nothing was built. Leave the marker
        # where it is; the next poll retries.
        print("another publish holds the lock; marker NOT advanced, will retry")
        return
    if result.returncode != 0:
        sys.exit(f"ERROR: {PUBLISH_SH} exited {result.returncode}; marker NOT advanced")
    write_state(fp, built_sha(fallback=head or prev["commit"]))
    print("rebuild complete; marker advanced")


if __name__ == "__main__":
    main()
