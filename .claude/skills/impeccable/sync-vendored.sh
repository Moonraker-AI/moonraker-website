#!/usr/bin/env bash
# Propagate the canonical impeccable skill (this directory, in client-hq)
# into the repos that carry a vendored duplicate. Run after any edit here,
# then commit each target repo (vendored third-party prose is exempt from
# the em-dash hook: commit with --no-verify if the hook trips on it).
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_ROOT="$(cd "$SRC/../../../.." && pwd)"

TARGETS=(
  "$DEV_ROOT/moonraker-site-template/.claude/skills/impeccable"
  "$DEV_ROOT/moonraker-website/.claude/skills/impeccable"
)

for dst in "${TARGETS[@]}"; do
  mkdir -p "$dst"
  rsync -a --delete "$SRC/" "$dst/"
  echo "synced -> $dst"
done

echo "done. diff check:"
for dst in "${TARGETS[@]}"; do
  diff -rq "$SRC" "$dst" >/dev/null && echo "  in sync: $dst"
done
