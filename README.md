# StackDeploy

**Version:** v3.0.0  
**Status:** Production Ready  
**Repository:** https://github.com/JorahOne-Services/StackDeploy

---

## Overview

StackDeploy is a **production-ready Docker Compose deployment** that consolidates self-hosted web search, long-term memory, browser automation, vector storage, and Obsidian note-taking under a single IP with centralized management. Designed to run on consumer hardware with Tailscale networking.

**Core philosophy:** One stack, one IP, zero secrets in git, full observability.

### Bundled Services

| Category | Services |
|----------|----------|
| **Search & Browser** | SearXNG (8080), Camofox (9377), CloakBrowser (9222) |
| **Memory & Knowledge** | Honcho Memory API (8081) + pgvector/Redis, Qdrant (6333) |
| **Notes & Docs** | Obsidian Remote (8083) |
| **Observability** | Prometheus (9090), Grafana (3000), Loki (3100) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAILSCALE NETWORK                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STACKDEPLOY                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FRONTEND NETWORK (172.20.0.0/24)                        │  │
│  │  SearXNG (8080) · Camofox (9377) · Obsidian (8083)      │  │
│  │  CloakBrowser (9222)                                     │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                          │                                       │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  BACKEND NETWORK (172.20.1.0/24) — INTERNAL ONLY          │  │
│  │  Qdrant (6333) · Honcho (8081) · PostgreSQL · Redis      │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                          │                                       │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │  MONITORING NETWORK (172.20.2.0/24) — INTERNAL ONLY       │  │
│  │  Prometheus (9090) · Grafana (3000) · Loki (3100)        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

- ✅ **Single-command bootstrap** — `bash scripts/bootstrap.sh` deploys everything
- ✅ **Zero secrets in git** — Docker secrets + `.env` (gitignored) + `secrets/` directory
- ✅ **Container hardening** — `no-new-privileges`, `cap_drop: ALL`, read-only rootfs, pinned images
- ✅ **Network isolation** — 3 internal networks (frontend, backend, monitoring)
- ✅ **Health checks on every service** — Docker healthchecks + `scripts/healthcheck.sh`
- ✅ **Full observability** — Prometheus metrics, Grafana dashboards, Loki log aggregation
- ✅ **CI/CD pipeline** — GitHub Actions: lint, security scan, build, test, deploy
- ✅ **Dependabot** — Weekly automated dependency updates
- ✅ **BATS test coverage** — Unit tests + integration tests
- ✅ **OpenAPI docs** — Complete API documentation for all services
- ✅ **Secrets management** — `scripts/manage-secrets.sh` for init, rotate, backup
- ✅ **Config validation** — `scripts/validate-config.sh` checks everything
- ✅ **Runbook** — `docs/RUNBOOK.md` with full operational documentation
- ✅ **CPU-first with GPU option** — Runs on CPU; Ollama on Tailscale host for GPU inference
- ✅ **Extensible Compose blocks** — Add services via compose fragments

---

## Quick Start

### Prerequisites
- Docker 24+ & Docker Compose v2
- Tailscale (for multi-host Ollama access)
- 8GB+ RAM, 50GB+ disk

### One-Command Deploy

```bash
git clone https://github.com/JorahOne-Services/StackDeploy.git
cd StackDeploy
bash scripts/bootstrap.sh
```

### Manual Deploy

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env: set HONCHO_DB_PASSWORD, SERVER_IP, etc.

# 2. Initialize secrets
bash scripts/manage-secrets.sh init

# 3. Validate configuration
bash scripts/validate-config.sh

# 4. Start the stack
docker compose up -d

# 5. Verify
bash scripts/healthcheck.sh localhost
```

### Access Points

| Interface | URL | Purpose |
|-----------|-----|---------|
| **SearXNG** | http://localhost:8080 | Privacy-respecting metasearch |
| **Camofox** | http://localhost:9377 | Stealth browser automation |
| **Obsidian** | http://localhost:8083 | Remote vault web UI |
| **Qdrant** | http://localhost:6333 | Vector database |
| **Honcho API** | http://localhost:8081 | Long-term memory API |
| **Prometheus** | http://localhost:9090 | Metrics & alerting |
| **Grafana** | http://localhost:3000 | Dashboards (admin/admin) |
| **Loki** | http://localhost:3100 | Log aggregation |

---

## Project Structure

```
StackDeploy/
├── docker-compose.yml          # 11 services with security hardening
├── .env.example                # Documented environment variables
├── .gitignore                  # Covers .env, secrets/, node_modules
├── secrets/                    # Docker secrets (gitignored)
│   └── *.txt                   # Auto-generated secret files
├── searxng/
│   └── settings.yml            # SearXNG configuration
├── scripts/
│   ├── bootstrap.sh            # One-command deployment
│   ├── healthcheck.sh          # Validates all services
│   ├── validate-config.sh      # Configuration validation
│   ├── manage-secrets.sh       # Secrets management (init/rotate/backup)
│   ├── check-secrets.py        # CI secrets scanner helper
│   ├── check-health.py         # CI health check helper
│   ├── init-honcho.sh          # Honcho initialization
│   ├── init-obsidian.sh        # Vault initialization
│   └── install.sh              # Venv setup
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml      # Scrape configuration
│   │   └── rules/
│   │       └── alerts.yml      # Alerting rules
│   ├── grafana/
│   │   ├── datasources/        # Auto-provisioned data sources
│   │   └── dashboards/         # Auto-provisioned dashboards
│   └── loki/
│       └── loki-config.yml     # Log aggregation config
├── tests/
│   ├── unit/
│   │   └── stackdeploy.bats    # Unit tests (shell scripts, configs)
│   └── integration/
│       └── services.bats       # Integration tests (endpoints, containers)
├── docs/
│   ├── RUNBOOK.md              # Full operational documentation
│   ├── openapi.json            # OpenAPI/Swagger specification
│   ├── SERVER_SETUP.md         # Server setup guide
│   ├── HERMES_SETUP.md         # Hermes integration guide
│   ├── HONCHO_SETUP.md         # Honcho setup guide
│   ├── HEADROOM_SETUP.md       # Headroom setup guide
│   └── MAINTENANCE.md          # Maintenance procedures
├── .github/
│   ├── dependabot.yml          # Automated dependency updates
│   └── workflows/
│       ├── ci-cd.yml           # Full CI/CD pipeline
│       └── webpack.yml         # Node.js build
├── browser-search/             # Camofox + CloakBrowser helpers
├── obsidian-skills/            # Agent skills for Obsidian
├── honcho/                     # Honcho configuration
├── headroom/                   # Headroom configuration
└── vendor/                     # Git submodules (honcho, headroom)
```

---

## Service Management

```bash
# Start all
docker compose up -d

# Stop all
docker compose down

# View logs
docker compose logs -f
docker compose logs -f honcho

# Restart single service
docker compose restart honcho

# Health check
bash scripts/healthcheck.sh localhost

# Config validation
bash scripts/validate-config.sh

# Full status
docker compose ps
```

---

## Security

- **No secrets in git** — `.env` and `secrets/` in `.gitignore`
- **Docker secrets** — Secrets mounted as files, not environment variables
- **Container hardening** — `no-new-privileges:true`, `cap_drop: ALL`, read-only rootfs
- **Network isolation** — 3 internal Docker networks; backend/monitoring are internal-only
- **Pinned images** — All images use specific versions (no `:latest`)
- **Vulnerability scanning** — Trivy scans in CI/CD pipeline
- **Secret rotation** — `scripts/manage-secrets.sh rotate <name>`
- **Tailscale** — All inter-host traffic encrypted; no public ports needed

---

## CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci-cd.yml`):

| Stage | Tools | Description |
|-------|-------|-------------|
| Lint | shellcheck, yamllint, hadolint | Code quality checks |
| Security | Trivy, detect-secrets, Dockle | Vulnerability & secret scanning |
| Build | Docker Buildx | Build all service images |
| Test | BATS | Unit + integration tests |
| Deploy | SSH action | Auto-deploy on push to master |
| Release | GitHub Releases | Auto-release on tags |

**Dependabot** (`.github/dependabot.yml`):
- Weekly checks for Docker, GitHub Actions, and npm dependencies
- Auto-creates PRs with labels and commit message prefixes

---

## Monitoring

### Prometheus
- **Access:** http://localhost:9090
- **Retention:** 30 days
- **Alert rules:** Service down, high memory/CPU, disk space, container restarts

### Grafana
- **Access:** http://localhost:3000 (admin/admin)
- **Pre-configured dashboards:** StackDeploy Overview
- **Data sources:** Prometheus (metrics), Loki (logs)

### Loki
- **Access:** http://localhost:3100
- **Retention:** 30 days
- **Structured logging:** All services log in JSON format

---

## API Documentation

Full OpenAPI/Swagger specification at `docs/openapi.json` covering:
- SearXNG search endpoints
- Camofox browser automation
- Honcho memory API
- Qdrant vector database

---

## License

MIT

---

## Author

Built by **Jhonattan L. Jimenez** (J1admin).

- GitHub: [@OneByJorah](https://github.com/OneByJorah)
- Tailscale: `ollama` (100.92.150.99)
