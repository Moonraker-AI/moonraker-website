#!/usr/bin/env bash
# vps_setup_publish.sh: one-time (idempotent) setup of the moonraker.ai
# server-side publish on the VPS host. Safe to re-run.
#
#   1. Node 20 (NodeSource) if the host has no node
#   2. /opt/moonraker-website clone (or fetch if it already exists)
#   3. a cron entry that runs publish_watch.py every 5 minutes
#
# After this, publishing a content piece in client-hq propagates to the live
# site within ~5 min (poll) + the build time, with no local machine.
set -euo pipefail

REPO_DIR="/opt/moonraker-website"
REPO_URL="https://github.com/Moonraker-AI/moonraker-website.git"
LOG="/var/log/moonraker-site-publish.log"
CRON_LINE="*/5 * * * * flock -n /tmp/mr_watch.lock /usr/bin/python3 ${REPO_DIR}/scripts/publish_watch.py >> ${LOG} 2>&1"

echo "==> 1. node"
if command -v node >/dev/null 2>&1; then
  echo "    node already present: $(node -v)"
else
  echo "    installing Node 20 (NodeSource)"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
  echo "    installed: $(node -v)"
fi

echo "==> 2. repo"
if [ -d "${REPO_DIR}/.git" ]; then
  echo "    ${REPO_DIR} exists; fetching"
  git -C "${REPO_DIR}" fetch --quiet origin main
  git -C "${REPO_DIR}" reset --quiet --hard origin/main
else
  echo "    cloning into ${REPO_DIR}"
  git clone --quiet "${REPO_URL}" "${REPO_DIR}"
fi
chmod +x "${REPO_DIR}/scripts/vps_publish.sh"

echo "==> 3. cron"
touch "${LOG}"
current="$(crontab -l 2>/dev/null || true)"
if echo "${current}" | grep -Fq "publish_watch.py"; then
  echo "    cron entry already installed"
else
  printf '%s\n%s\n' "${current}" "${CRON_LINE}" | grep -v '^$' | crontab -
  echo "    cron entry installed: ${CRON_LINE}"
fi

echo "==> setup complete. Manual publish: bash ${REPO_DIR}/scripts/vps_publish.sh"
