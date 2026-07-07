<div align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/SearXNG-000?style=for-the-badge&logo=googlesearch&logoColor=white">
</div>

<br>

<div align="center">
  <h1>📦 StackForge</h1>
  <p><strong>Production-Ready Docker Compose Stack for Hermes Agents</strong></p>
  <p>One IP, one stack — CPU-only, privacy-focused, self-hosted</p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-services">Services</a> •
    <a href="#-healthcheck-notes">Healthcheck Notes</a>
  </p>
</div>

---

## ✨ Features

- **One Command Deploy** — Single bootstrap script for full stack
- **CPU Only** — Optimized for consumer hardware (GPU optional for Ollama)
- **Privacy-Focused** — Self-hosted search with SearXNG, no third-party APIs
- **Long-Term Memory** — Honcho API with PostgreSQL + pgvector + Redis
- **Vector Database** — Qdrant for RAG and semantic search
- **Obsidian Integration** — CouchDB LiveSync vault with web viewer
- **P2P File Sync** — Syncthing between server and laptop
- **Browser Automation** — Selenium standalone Chrome for agent web tasks
- **Local LLM** — Ollama for offline inference
- **Tailscale Ready** — All services exposed on a single Tailscale IP

---

## 📋 Services

| Service | Port | Health Check | Purpose |
|---------|------|--------------|---------|
| **SearXNG** | 8080 | `wget --spider http://localhost:8080/` | Privacy-respecting metasearch |
| **Qdrant** | 6333 | `bash /dev/tcp` port probe | Vector database for embeddings |
| **Honcho API** | 8000 | `python3 urllib GET /health` | Long-term memory for agents |
| **Honcho DB** | 5432 | `pg_isready` | PostgreSQL + pgvector |
| **Honcho Redis** | 6379 | `redis-cli ping` | Cache layer |
| **CouchDB** | 5984 | `curl GET /` (allows 401) | Obsidian LiveSync backend |
| **Obsidian Viewer** | 8083 | `curl -f http://localhost:80/` | Web vault UI via Caddy |
| **Syncthing** | 8384 | `python3 urllib GET /` | P2P file sync (laptop ↔ server) |
| **Selenium Chrome** | 4444 | `curl -f /status` | Browser automation |
| **Ollama** | 11434 | `bash /dev/tcp` port probe | Local LLM inference |

---

## 🚀 Quick Start

### Prerequisites

- Docker & docker-compose (v1 or v2)
- Tailscale (recommended, for multi-machine access)
- 8GB+ RAM, 50GB+ disk

### Setup

```bash
git clone https://github.com/OneByJorah/StackForge.git
cd StackForge

# 1. Configure environment
cp .env.example .env
# Edit .env — set SERVER_IP, HONCHO_DB_PASSWORD, COUCHDB passwords

# 2. Optional: configure Honcho LLM provider
cp .env.honcho.example .env.honcho
# Edit .env.honcho — set your OpenAI-compatible API keys

# 3. Start the stack
docker-compose up -d
```

### First-time Honcho Setup

Honcho requires database schema migrations on first run:

```bash
docker run --rm \
  --network stackdeploy-backend \
  -e DB_CONNECTION_URI=postgresql+psycopg://honcho:YOUR_PASSWORD@honcho-db:5432/honcho \
  --entrypoint alembic \
  ghcr.io/plastic-labs/honcho:latest upgrade head
```

Then restart the Honcho API container:

```bash
docker-compose stop honcho-api
docker-compose rm -f honcho-api
docker-compose up -d honcho-api
```

### Health Check

```bash
# Check all services
docker-compose ps

# Verify Honcho specifically
curl -s http://localhost:8000/health
# → {"status":"ok"}
```

---

## ⚙️ Healthcheck Notes

Many container images don't ship `curl`. The stack uses the tool each image actually has:

| Image | Available Tool | Healthcheck Method |
|-------|---------------|--------------------|
| searxng/searxng | `wget` | `wget --spider -q http://localhost:8080/` |
| qdrant/qdrant | `bash` + `timeout` | `bash -c 'cat < /dev/null > /dev/tcp/localhost/6333'` |
| ghcr.io/plastic-labs/honcho | `python3` | `python3 -c "urllib.request.urlopen(...)"` |
| couchdb:3.4 | `curl` | `curl -s -o /dev/null http://127.0.0.1:5984/` (no `-f` — allows 401) |
| caddy:2-alpine | `curl` | `curl -f http://localhost:80/` |
| syncthing/syncthing | `python3` | `python3 -c "urllib.request.urlopen(...)"` |
| selenium/standalone-chrome | `curl` | `curl -f http://localhost:4444/status` |
| ollama/ollama | `bash` + `timeout` | `bash -c 'cat < /dev/null > /dev/tcp/localhost/11434'` |

If you see `(unhealthy)` in `docker ps`, check the healthcheck method matches your image. The `bash /dev/tcp` pattern works on any image with bash and `timeout` — no extra packages needed.

---

## 🔧 Service Management

```bash
# Start all
docker-compose up -d

# Stop all
docker-compose down

# View logs (all or specific)
docker-compose logs -f
docker-compose logs -f honcho-api

# Restart single service
docker-compose restart honcho-api

# Health check
docker-compose ps
```

---

## 🔐 Environment Variables

All secrets in `.env` (never committed — it's in `.gitignore`). See `.env.example` for the full list.

| Variable | Purpose | Required |
|----------|---------|----------|
| `SERVER_IP` | Your Tailscale/local IP for service URLs | Yes |
| `HONCHO_DB_PASSWORD` | PostgreSQL password for Honcho | Yes |
| `HONCHO_TOKEN` | Honcho API auth token | Yes |
| `COUCHDB_ADMIN_USER` | CouchDB admin username | Yes |
| `COUCHDB_ADMIN_PASSWORD` | CouchDB admin password | Yes |
| `COUCHDB_SYNC_USER` | CouchDB sync user for Obsidian | Yes |
| `COUCHDB_SYNC_PASSWORD` | CouchDB sync password | Yes |
| `OBSIDIAN_VAULT_PATH` | Host path for Hermes agent notes | Optional |

### Honcho LLM Provider (`.env.honcho`)

Honcho needs an OpenAI-compatible LLM provider for its embedding/LLM features. Copy `.env.honcho.example` to `.env.honcho` and configure:

| Variable | Purpose | Example |
|----------|---------|---------|
| `LLM_VLLM_API_KEY` | Primary LLM API key | `sk-or-v1-...` |
| `LLM_VLLM_BASE_URL` | Primary LLM base URL | `https://openrouter.ai/api/v1` |
| `LLM_EMBEDDING_API_KEY` | Embeddings API key | `sk-or-v1-...` |
| `LLM_EMBEDDING_BASE_URL` | Embeddings base URL | `https://openrouter.ai/api/v1` |
| `LLM_EMBEDDING_MODEL` | Embedding model | `openai/text-embedding-3-small` |

---

## 🌐 Hermes Agent Integration

The entire stack is designed to be consumed by Hermes agents. Configure your agent's provider settings to point at the Tailscale IP where StackForge runs.

### Agent configuration

| Service | URL Pattern | Hermes Provider |
|---------|-------------|-----------------|
| Honcho | `http://YOUR_IP:8000` | `custom` memory provider |
| SearXNG | `http://YOUR_IP:8080` | `custom` search provider |
| Qdrant | `http://YOUR_IP:6333` | `custom` vector store |
| Ollama | `http://YOUR_IP:11434` | `ollama` provider |
| Obsidian | `http://YOUR_IP:8083` | Web vault viewer |
| CouchDB | `http://YOUR_IP:5984` | LiveSync sync backend |
| Syncthing | `http://YOUR_IP:8384` | File sync UI |
| Selenium | `http://YOUR_IP:4444` | Browser automation |

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│               TAILSCALE NETWORK                      │
│           Single IP exposes all ports                 │
└────────────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────┐
│                   STACKDEPLOY                        │
│                                                      │
│  SEARCH       MEMORY          STORAGE                │
│  SearXNG      Honcho + PG     Qdrant                 │
│  (8080)       + Redis (8000)  (6333)                │
│                                                      │
│  NOTES        FILE SYNC       BROWSER     LOCAL LLM  │
│  CouchDB      Syncthing       Selenium    Ollama     │
│  (5984/8083)  (8384)          (4444)      (11434)   │
└────────────────────────────────────────────────────┘
```

**Data Flow:**
- Hermes Agent → Local services (search, memory, browser) → Optional upstream LLM via Hermes config
- All services communicate over Docker internal network
- Single Tailscale IP exposes everything via direct ports

---

## Project Structure

```
StackForge/
├── docker-compose.yml         # Main compose file — all services
├── .env.example               # Environment variable template
├── .env.honcho.example        # Honcho LLM provider config template
├── bootstrap.sh               # One-command deploy script
├── searxng/                   # SearXNG configuration
│   └── settings.yml
├── honcho/
│   ├── config.toml            # Honcho API config
│   └── couchdb-init.sh        # CouchDB user initialization
├── obsidian/
│   ├── Caddyfile              # Caddy reverse proxy config
│   ├── index.html             # Vault viewer HTML
│   └── vault/                 # Markdown note vault
│       └── Welcome.md
└── syncthing/
    └── config/                # Syncthing device configuration
```

---

## 📄 License

MIT

---

## Security

- **No secrets in git** — `.env`, `.env.honcho` in `.gitignore`; `.env.example` has placeholders
- **Network isolation** — Internal Docker network (`stackdeploy-backend`) for DB/cache; ports explicitly mapped
- **Tailscale** — All inter-host traffic encrypted; no public ports needed
- **Read-only mounts** — Config files mounted `:ro` where possible
- **Health checks** — Every service auto-reports status to Docker