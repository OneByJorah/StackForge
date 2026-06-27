#!/usr/bin/env bash
set -euo pipefail
SERVER="${1:-localhost}"
printf "server=%s\n" "$SERVER"
printf "SearXNG:   "; curl -sG -o /dev/null -w "%{http_code}" "http://$SERVER:8080/search" -d "q=test&format=json"; echo
printf "Qdrant:    "; curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:6333/healthz"; echo
printf "Chrome:    "; curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:9222/json/version"; echo
printf "Honcho:    "; curl -s -o /dev/null -w "%{http_code}" "http://$SERVER:8081/healthz"; echo
printf "Obsidian:  "; if [ -d "${OBSIDIAN_VAULT_PATH:-/home/j1admin/ObsidianVault}" ]; then echo "mounted"; else echo "missing"; fi
