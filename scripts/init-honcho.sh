#!/usr/bin/env bash
set -euo pipefail
mkdir -p /home/j1admin/docker/j1-stack-deploy
cat > /home/j1admin/docker/j1-stack-deploy/.env <<EOF
SERVER_IP=REPLACE_WITH_YOUR_TAILSCALE_IP
HONCHO_TOKEN=<REPLACE_WITH_YOUR_HONCHO_TOKEN>
HONCHO_DB_PASSWORD=REPLACE_WITH_SECURE_PASSWORD
EOF
echo "init-honcho: wrote /home/j1admin/docker/j1-stack-deploy/.env"
