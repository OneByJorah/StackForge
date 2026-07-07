# StackForge Install Notes (for Hermes Integration)

## Verified endpoints (localhost)
- SearXNG: http://localhost:8080
- Camofox: http://localhost:9377
- Obsidian web: http://localhost:8083
- Qdrant: http://localhost:6333

## Default paths
- Repo: ~/StackForge
- Vault: ~/StackForge/obsidian-vault (or as set by OBSIDIAN_VAULT_PATH)

## Setup checklist
1. Clone repo and set `.env`.
2. Run `docker compose up -d`.
3. Run `./scripts/init-obsidian.sh`.
4. Install browser-search deps: `cd browser-search && npm install`.
5. Configure Hermes:
   ```bash
   hermes config set web.backend searxng
   hermes config set web.searxng_url http://127.0.0.1:8080
   ```
6. (Optional) `hermes config set browser.engine camofox` if auto-detection fails.

## Notes
- SearXNG may show as `unhealthy` in `docker compose ps` but still works.
- Camofox may show `browserConnected: false` until first use.
