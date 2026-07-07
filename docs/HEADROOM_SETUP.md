# Headroom / Aphrodite Setup

Headroom is integrated into StackForge as an optional service under `vendor/headroom`, using the upstream `headroomlabs-ai/headroom` codebase. It exposes a local proxy on port `8787` plus Qdrant/Neo4j backends for vector + graph memory. Aphrodite-specific config is handled through Headroom’s proxy and `headroom.toml` conventions.

## Prerequisites

- Docker Compose
- Build exports only on localhost-facing ports by default via `docker-compose.headroom.yml`

## Quick start

```bash
cp .env.headroom.example .env.headroom
# Edit .env.headroom: set NEO4J_AUTH, then:

docker compose -f docker-compose.yml -f docker-compose.headroom.yml up -d
bash scripts/init-headroom.sh
```

## Endpoints

| Service | Port | Notes |
|---------|------|-------|
| Headroom proxy | `8787` | OpenAI-compatible proxy + readz `/readyz` |
| Qdrant | `6333` / `6334` | Vector REST/gRPC |
| Neo4j | `7474` / `7687` | Browser + Bolt |

## Hermes config hints

- Set web/memory proxy base to `http://127.0.0.1:8787`
- Enable Aphrodite tool relay via the proxy’s upstream/tool_relay config fields
- Target upstream model via `OPENAI_TARGET_API_URL`

## Updating

```bash
cd vendor/headroom
git fetch headroomlabs
git merge headroomlabs/main
cd ../..
git add vendor/headroom
git commit -m "chore(headroom): update upstream"
```
