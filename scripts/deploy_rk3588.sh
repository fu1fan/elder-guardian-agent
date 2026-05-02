#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-192.168.10.64}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/opt/elder-guardian-agent}"
PUBLIC_HOST="${PUBLIC_HOST:-192.168.10.64}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Deploying ${ROOT_DIR} to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

ssh -o StrictHostKeyChecking=accept-new "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_DIR}'"

rsync -az \
  --exclude '.git' \
  --exclude '.env' \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'data/guardian.db' \
  --exclude 'data/guardian.db-*' \
  --exclude 'data/mosquitto' \
  --exclude 'data/logs/*' \
  --exclude 'data/snapshots/*' \
  "${ROOT_DIR}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/"

ssh "${REMOTE_USER}@${REMOTE_HOST}" "chmod +x '${REMOTE_DIR}/update_latest.sh' '${REMOTE_DIR}/deploy/rk3588/update_latest.sh' 2>/dev/null || true; cd '${REMOTE_DIR}' && PUBLIC_HOST='${PUBLIC_HOST}' APP_DIR='${REMOTE_DIR}' bash deploy/rk3588/update_latest.sh"

