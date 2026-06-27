# Honcho Setup

Honcho provides long-term memory/workspace context for Hermes Agent.

## Prerequisites

- Docker Engine + Compose v2+
- API keys from an OpenAI-compatible provider (OpenRouter recommended)

## Quick Start

1. Initialize Honcho environment:
   ```bash
   ./scripts/init-honcho.sh
   ```

2. Edit `.env.honcho` and add your LLM API keys:
   - `LLM_VLLM_API_KEY` (primary provider)
   - `LLM_VLLM_BASE_URL` (e.g., https://openrouter.ai/api/v1)
   - `LLM_EMBEDDING_API_KEY` (can be same as primary)
   - `LLM_EMBEDDING_BASE_URL`
   - `LLM_EMBEDDING_MODEL` (default: openai/text-embedding-3-small)
   - (Optional) backup provider keys

3. Ensure the Honcho submodule is initialized:
   ```bash
   git submodule update --init vendor/honcho
   ```

4. Start Honcho alongside StackDeploy:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.honcho.yml up -d
   ```

5. Verify Honcho is running:
   ```bash
   curl -s http://localhost:8000/api/v1/health  # or check /openapi.json
   ```

6. Configure Hermes to use local Honcho:
   ```yaml
   # in ~/.hermes/config.yaml (or profile config)
   honcho:
     enabled: true
     base_url: "http://localhost:8000"
     workspace: hermes-main
   ```

7. Restart Hermes:
   ```bash
   hermes restart
   ```

## Notes

- The first build will compile the Honcho image (requires pulling dependencies). This may take a few minutes.
- Honcho uses PostgreSQL with pgvector and Redis, both included in `docker-compose.honcho.yml`.
- All data persists in Docker volumes: `honcho-pgdata` and `honcho-redis-data`.
- Configuration (`config.toml`) is mounted read-only at runtime. Adjust `honcho/config.toml` if needed.
- For more details, see the upstream repo: https://github.com/plastic-labs/honcho

## Stopping Honcho

```bash
docker compose -f docker-compose.honcho.yml down
```
