# Server Setup

## Prerequisites

- Docker + Docker Compose v2+
- Tailscale installed

## Install

```bash
# 1. Clone the repository
git clone https://github.com/OneByJorah/StackForge.git
cd StackForge

# 2. Environment
cp .env.example .env
# Edit .env: set SERVER_IP, HONCHO_TOKEN, HONCHO_DB_PASSWORD

# 3. Bring up the stack
docker compose up -d

# 4. Initialize services
./scripts/init-honcho.sh
./scripts/init-obsidian.sh
```

---

## Environment Variables

| Variable | Purpose | Notes |
|---|---|---|
| `SERVER_IP` | Tailscale or local IP used in docs/examples | Required |
| `HONCHO_TOKEN` | Auth token for Honcho API | Optional |
| `HONCHO_DB_PASSWORD` | Postgres password for Honcho backend | Required |
| `OBSIDIAN_VAULT_PATH` | Host path for the Obsidian vault | Optional |

Keep `.env` out of VCS. Prefer `.env.example` placeholders in docs.

---

## Services

| Service | Port |
|---|---|
| SearXNG | `8080` |
| Honcho API | `8000` |
| Selenium Chrome | `4444` |
| Qdrant | `6333` |
| Obsidian Web | `8083` |

---

## Service Management

```bash
# Start the stack
docker compose up -d

# Stop
docker compose down

# Tail logs
docker compose logs -f

# Healthcheck
./scripts/healthcheck.sh <server-ip>
```

---

## Security

- Bind services to trusted interfaces in production.
- Obsidian vault data persists in the `obsidian-vault` Docker volume; back it up regularly.
- All secrets remain in `.env`, excluded from VCS.

---

## Troubleshooting

- If services fail to start, inspect `docker compose up -d && docker compose logs -f`.
- Ensure `SERVER_IP` matches the host address used by other clients (Tailscale recommended).

---

## License

MIT

---
