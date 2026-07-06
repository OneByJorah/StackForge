#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# StackDeploy Bootstrap  —  Interactive First-Run Setup
# Usage:  bash bootstrap.sh
#
# Prompts for passwords/ips on first run, then deploys everything.
# ═══════════════════════════════════════════════════════════════
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# ── Colors ────────────────────────────────────────────────────
BOLD='\033[1m'; DIM='\033[2m'; AMBER='\033[38;5;214m'; NC='\033[0m'
OK="${AMBER}✓${NC}"; INFO="${DIM}▸${NC}"; WARN="${AMBER}⚠${NC}"

echo -e "${BOLD}"
echo "═══════════════════════════════════════"
echo "  StackDeploy — Self-hosted AI Brain"
echo "═══════════════════════════════════════"
echo -e "${NC}"

# ── 1. Prerequisites ─────────────────────────────────────────
echo -e "${INFO} Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo -e "${WARN} docker not found — install Docker first"; exit 1; }
echo -e "${OK} docker found"

# Check for docker compose v2 (preferred) or docker-compose v1
DC=""
docker compose version >/dev/null 2>&1 && DC="docker compose" || true
[ -z "$DC" ] && command -v docker-compose >/dev/null 2>&1 && DC="docker-compose" || true
[ -z "$DC" ] && { echo -e "${WARN} docker compose plugin not found"; exit 1; }
echo -e "${OK} $DC"

# ── 2. Interactive .env setup ────────────────────────────────
setup_env() {
  echo ""
  echo -e "${BOLD}First-time setup — let's configure your secrets.${NC}"
  echo -e "${DIM}Press Enter to accept defaults — but please use strong passwords in production.${NC}"
  echo ""

  cp .env.example .env

  # Prompt: Tailscale IP (most important)
  default_ip=$(ip -4 addr show tailscale0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1)
  [ -z "$default_ip" ] && default_ip="$(tailscale ip -4 2>/dev/null || true)"
  [ -z "$default_ip" ] && default_ip="localhost"
  read -p "  Tailscale/LAN IP [${default_ip}]: " SERVER_IP
  SERVER_IP="${SERVER_IP:-$default_ip}"
  sed -i "s/REPLACE_WITH_YOUR_TAILSCALE_IP/${SERVER_IP}/" .env
  echo -e "${OK} SERVER_IP = ${SERVER_IP}"
  echo ""

  # Prompt each REPLACE_WITH_* in .env
  while IFS= read -r line; do
    var=$(echo "$line" | cut -d= -f1)
    placeholder=$(echo "$line" | cut -d= -f2-)
    # Only prompt lines with unset values
    [[ "$placeholder" != "REPLACE_WITH_"* ]] && continue
    [[ "$var" == "SERVER_IP" ]] && continue  # already set

    hint=""
    case "$var" in
      HONCHO_DB_PASSWORD)      hint="(e.g. honcho_db_$(openssl rand -hex 4))" ;;
      HONCHO_TOKEN)            hint="(e.g. honcho_$(openssl rand -hex 8))" ;;
      COUCHDB_ADMIN_PASSWORD)  hint="(e.g. admin_$(openssl rand -hex 4))" ;;
      COUCHDB_SYNC_PASSWORD)   hint="(e.g. sync_$(openssl rand -hex 4))" ;;
      COUCHDB_ADMIN_USER)      hint="[admin]" ;;
      COUCHDB_SYNC_USER)       hint="[obsync]" ;;
    esac

    # Generate a default
    case "$var" in
      HONCHO_DB_PASSWORD)      def="hc_$(openssl rand -hex 4)" ;;
      HONCHO_TOKEN)            def="ht_$(openssl rand -hex 8)" ;;
      COUCHDB_ADMIN_PASSWORD)  def="ad_$(openssl rand -hex 4)" ;;
      COUCHDB_SYNC_PASSWORD)   def="sy_$(openssl rand -hex 4)" ;;
      COUCHDB_ADMIN_USER)      def="admin" ;;
      COUCHDB_SYNC_USER)       def="obsync" ;;
      *)                       def="" ;;
    esac

    read -p "  ${var} ${hint} [${def}]: " val
    val="${val:-$def}"
    sed -i "s/^${var}=${placeholder}$/${var}=${val}/" .env
    echo -e "${OK} ${var} set"
    echo ""
  done < <(grep -v '^#' .env.example | grep 'REPLACE_WITH_')

  # Set SEARXNG_SECRET_KEY
  searxng_secret=$(openssl rand -hex 32)
  if grep -q "^# SEARXNG_SECRET_KEY" .env; then
    sed -i "s/^# SEARXNG_SECRET_KEY=.*/SEARXNG_SECRET_KEY=${searxng_secret}/" .env
  elif ! grep -q "^SEARXNG_SECRET_KEY=" .env; then
    echo "SEARXNG_SECRET_KEY=${searxng_secret}" >> .env
  fi
  echo -e "${OK} SEARXNG_SECRET_KEY generated"
  echo ""
  echo -e "${BOLD}All secrets configured.${NC}"
}

if [ ! -f .env ]; then
  setup_env
else
  # Check if .env still has placeholder values
  placeholders=$(grep -c 'REPLACE_WITH_' .env 2>/dev/null || true)
  if [ "$placeholders" -gt 0 ]; then
    echo -e "${WARN} Your .env still has ${placeholders} placeholder values."
    read -p "  Re-run interactive setup? [Y/n]: " rerun
    if [[ "$rerun" =~ ^[Yy]?$ ]]; then
      setup_env
    fi
  fi
fi

# Source the final .env
set -a; source .env; set +a

# ── 3. Create required directories ─────────────────────────────
echo -e "${INFO} Ensuring directory structure..."
mkdir -p obsidian/vault syncthing/config

# ── 4. Init vault with Welcome note ────────────────────────────
if [ ! -f obsidian/vault/Welcome.md ]; then
  cat > obsidian/vault/Welcome.md <<- WELCOME
---
title: "Welcome"
date: $(date +"%Y-%m-%d %H:%M:%S")
tags: [system,guide]
---

# Welcome to Your AI Brain

This shared vault is the **persistent memory layer** for your Hermes fleet.

- **Agents** write session summaries here automatically
- **Syncthing** syncs these notes to your laptop's Obsidian
- **CouchDB LiveSync** provides real-time sync (alternative)
- **Web viewer** at \`http://${SERVER_IP:-localhost}:${SVC_OBSIDIAN_PORT:-8083}\`
WELCOME
  echo -e "${OK} Welcome.md created"
fi

# ── 5. Create vault index ──────────────────────────────────────
cat > obsidian/vault/index.json <<- INDEX
{
  "count": $(ls obsidian/vault/*.md 2>/dev/null | wc -l),
  "notes": []
}
INDEX

# ── 6. Fire up the stack ───────────────────────────────────────
echo -e "${INFO} Starting all services..."
$DC down 2>/dev/null || true
$DC up -d --wait 2>&1 | sed 's/^/  /'

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "  ${OK} StackDeploy is live!"
echo -e "  ${DIM}═${NC}"
echo -e "  Web viewer    ${BOLD}http://${SERVER_IP}:${SVC_OBSIDIAN_PORT:-8083}${NC}"
echo -e "  LiveSync      ${BOLD}http://${SERVER_IP}:${SVC_COUCHDB_PORT:-5984}${NC}"
echo -e "  Syncthing UI  ${BOLD}http://${SERVER_IP}:${SVC_SYNCTHING_UI_PORT:-8384}${NC}"
echo -e "  SearXNG       ${BOLD}http://${SERVER_IP}:${SVC_SEARXNG_PORT:-8080}${NC}"
echo -e "  Qdrant        ${BOLD}http://${SERVER_IP}:${SVC_QDRANT_PORT:-6333}${NC}"
echo -e "  Honcho API    ${BOLD}http://${SERVER_IP}:${SVC_HONCHO_PORT:-8000}${NC}"
echo -e "  Web Auto      ${BOLD}http://${SERVER_IP}:${SVC_SELENIUM_PORT:-4444}${NC}"
echo -e "  Ollama        ${BOLD}http://${SERVER_IP}:11434${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"

# ── 7. Save credentials to a note for the vault ────────────────
creds_file="obsidian/vault/credentials.md"
if [ ! -f "$creds_file" ]; then
  echo -e "${INFO} Saving credentials to vault..."
  cat > "$creds_file" <<- CREDS
---
title: "Credentials"
date: $(date +"%Y-%m-%d %H:%M:%S")
tags: [system,credentials]
---

# Service Credentials

> **Store these securely.** These were generated during first-time setup.

| Service | URL | User | Password |
|---------|-----|------|----------|
| CouchDB LiveSync | http://${SERVER_IP}:${SVC_COUCHDB_PORT:-5984} | ${COUCHDB_ADMIN_USER:-admin} | ${COUCHDB_ADMIN_PASSWORD:-} |
| CouchDB Sync User | http://${SERVER_IP}:${SVC_COUCHDB_PORT:-5984} | ${COUCHDB_SYNC_USER:-obsync} | ${COUCHDB_SYNC_PASSWORD:-} |
| Syncthing UI | http://${SERVER_IP}:${SVC_SYNCTHING_UI_PORT:-8384} | (set in web UI) | (set in web UI) |
| Honcho API | http://${SERVER_IP}:${SVC_HONCHO_PORT:-8000} | (token auth) | ${HONCHO_TOKEN:-} |
CREDS
  echo -e "${OK} Credentials saved to vault"
fi

echo ""
echo -e "${DIM}Your credentials are also saved in obsidian/vault/credentials.md${NC}"
echo -e "${DIM}Delete that file after you've memorized them — or keep it behind Tailscale only.${NC}"
echo ""