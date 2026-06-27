#!/usr/bin/env bash
set -euo pipefail
# StackDeploy one-shot deploy for Hermes
# Fixes stale searxng container automatically
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"
chmod +x scripts/*.sh || true
bash scripts/init-honcho.sh
bash scripts/init-obsidian.sh
docker compose down >/dev/null 2>&1 || true
docker compose up -d
if docker ps -a --format '{{.Names}}' | grep -x searxng >/dev/null 2>&1; then
  docker rm -f searxng >/dev/null 2>&1 || true
fi
cd "$REPO_DIR/browser-search" && [ -d node_modules ] || npm install
bash "$REPO_DIR/tests/smoke.sh"
echo "StackDeploy ready at $REPO_DIR"
