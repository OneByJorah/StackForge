# StackDeploy — Self-hosted AI Stack for Hermes Agents

One-command self-hosted stack: llama.cpp, SearXNG, Honcho memory, Chrome CDP, vector memory, TTS, and observability.

## 1-click setup
```bash
cp .env.example .env
docker compose up -d
./scripts/init-honcho.sh
./scripts/bootstrap.sh
./scripts/healthcheck.sh
```
Docs:
- `docs/SERVER_SETUP.md`
- `docs/HERMES_SETUP.md`
- `docs/MAINTENANCE.md`

## Status
✅ Repo references and docs verified.
