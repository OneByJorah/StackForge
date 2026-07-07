# StackForge + Hermes Agent

This doc describes how the Hermes Agent uses the local StackForge services.

## Cluster Health
```bash
curl -s -o /dev/null -w 'searxng=%{http_code}\n' 'http://localhost:8080/search?format=json&q=test'
curl -s -o /dev/null -w 'camofox=%{http_code}\n' http://localhost:9377/health
curl -s -o /dev/null -w 'obsidian=%{http_code}\n' http://localhost:8083/
curl -s -o /dev/null -w 'qdrant=%{http_code}\n' http://localhost:6333/
```

## Services Hermes touches directly
- SearXNG at `http://localhost:8080`
  - JSON: `GET /search?format=json&q=<query>&language=en`
- Camofox at `http://localhost:9377`
  - OpenAPI: `GET /docs`
  - Create tab: `POST /tabs {"userId":"hermes","sessionKey":"default","url":"https://example.com"}`
  - Snapshot: `GET /tabs/{tabId}/snapshot?userId=hermes`
  - Close tab: `DELETE /tabs/{tabId}?userId=hermes`
- Qdrant at `http://localhost:6333`
  - Web UI / REST API root
- Obsidian
  - Web UI: `http://localhost:8083`
  - Vault path: `/path/to/your/vault`

## BrowserSearch CLI
```bash
cd /path/to/StackForge/browser-search
node scripts/cloak/cloak-fetch.mjs "https://example.com" --format markdown
```

## Smoke test
```bash
cd /path/to/StackForge
bash tests/smoke.sh
```
