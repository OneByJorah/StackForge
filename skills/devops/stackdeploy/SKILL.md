---
name: stackdeploy
description: Run StackDeploy and integrate its services (SearXNG, Camofox, Obsidian, Qdrant, CloakBrowser) with Hermes Agent.
version: "1.0.0"
metadata:
  hermes:
    tags: [stackdeploy, ops, docker, searxng, camofox, obsidian, qdrant, cloackbrowser]
---

# StackDeploy Integration

StackDeploy provides local AI-friendly infrastructure: SearXNG for search, Camofox for browser automation, Obsidian for notes, Qdrant for vector storage, and optional Honcho/llama.cpp. This skill helps you install, configure, and use StackDeploy with Hermes.

## Prerequisites
- Docker & Docker Compose
- Node.js (for browser-search)
- Git

## Quick Setup

1. Clone the StackDeploy repository:
   ```bash
   git clone https://github.com/OneByJorah/StackDeploy.git
   cd StackDeploy
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env: set SERVER_IP, HONCHO_TOKEN (optional), HONCHO_DB_PASSWORD (if using Honcho)
   ```

3. Start the stack:
   ```bash
   docker compose up -d
   ./scripts/init-honcho.sh   # if using Honcho
   ./scripts/init-obsidian.sh
   ```

4. Install browser-search dependencies (if needed):
   ```bash
   cd browser-search && npm install
   ```

5. Configure Hermes to use local services:
   ```bash
   hermes config set web.backend searxng
   hermes config set web.searxng_url http://127.0.0.1:8080
   # (Optional) Set browser engine to camofox if not auto-detected:
   # hermes config set browser.engine camofox
   ```

## Default Paths
- Repo: `~/StackDeploy` (or wherever you cloned it)
- Obsidian Vault: `~/StackDeploy/obsidian-vault` by default; configurable via `OBSIDIAN_VAULT_PATH` in `.env`.

## Verify
```bash
# Check service health
cd ~/StackDeploy
docker compose ps
bash tests/smoke.sh

# Test search
curl 'http://localhost:8080/search?format=json&q=test&language=en'
```

## Usage

Once configured, use Hermes’s web search normally. The agent will route queries through your local SearXNG instance. For browser automation, it will use Camofox. Obsidian notes can be managed via the Obsidian skill. Qdrant is available for vector storage.

## Troubleshooting
- SearXNG may appear `unhealthy` but still works; healthcheck may fail due to optional metrics.
- If Camofox shows `browserConnected: false`, it will connect on first automation task.
- Ensure `node_modules` exists in `browser-search` (run `npm install`).

For more details, see the StackDeploy documentation: `docs/` in the repository.
