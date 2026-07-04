# StackDeploy

**Unify web search, long-term memory, browser automation, vector storage, and admin management under one IP with Docker Compose.**

![License](https://img.shields.io/badge/License-MIT-FFB300.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production_Ready-FFB300.svg?style=for-the-badge)
![Language](https://img.shields.io/badge/Language-Docker_Compose-FFB300.svg?style=for-the-badge)
![Stack](https://img.shields.io/badge/Stack-Docker_Portainer_Tailscale-FFB300.svg?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Linux-FFB300.svg?style=for-the-badge)

StackDeploy consolidates self-hosted web search, long-term memory, browser automation, vector storage, and Obsidian note-taking into a single Docker Compose stack exposed through one IP. It targets SMB and public-sector operators who need ops-grade visibility without SaaS dependencies. Every service runs with zero secrets in git and is managed through Portainer or the CLI. Built for Tailscale networks, it supports multi-host inference via optional upstream LLM.

- One-command bootstrap and validation.
- Zero secrets in git; `.env.example` documents required placeholders.
- Health checks on all services.
- Full admin panel via Portainer for container lifecycle, logs, and persistence.
- Tailscale-native networking across Linux hosts.

- Deploy the full stack with `./scripts/bootstrap.sh`.
- Validate service health with `./scripts/healthcheck.sh localhost`.
- Isolate secrets in `.env` outside version control.
- Manage containers, volumes, logs, and RBAC via Portainer CE.
- Route multi-host traffic through Tailscale for encrypted inter-host communication.
- Extend the stack by dropping in validated Docker Compose fragments.
- Trigger CI/CD pipelines on push for lint, build, test, and deploy.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAILSCALE NETWORK                            │
│  100.92.150.99 (ollama host)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STACKDEPLOY                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  SEARCH & BROWSER              MEMORY & KNOWLEDGE          │  │
│  │  SearXNG (8080)                Honcho API (8081)           │  │
│  │  Camofox (9377)                Qdrant (6333)               │  │
│  │  CloakBrowser (9222)           PostgreSQL + Redis          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│        ┌─────────────────────┼─────────────────────┐             │
│        ▼                     ▼                     ▼             │
│  ┌───────────┐         ┌───────────┐         ┌───────────┐     │
│  │  NOTES    │         │  ADMIN    │         │  OPTIONAL │     │
│  │ Obsidian  │         │ Portainer │         │ Ollama    │     │
│  │ (8083)    │         │ (9000)    │         │ (11434)   │     │
│  └───────────┘         └───────────┘         └───────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Runtime**: Linux (Ubuntu 22.04+), Docker Compose v2
- **Orchestration**: Docker Compose v2, Bash bootstrap scripts
- **VCS**: Git + GitHub
- **Memory / Context**: Honcho (pgvector + Redis), Qdrant
- **Search / Browser**: SearXNG, Camofox, CloakBrowser
- **Notes**: Obsidian Remote (web UI)
- **Admin**: Portainer CE (container lifecycle, RBAC, backups)
- **Notifications**: Telegram (J1-bot)
- **CI/CD**: GitHub Actions (build, test, deploy)

### Quickstart

1. Clone the repository.
   ```bash
   git clone https://github.com/OneByJorah/StackDeploy.git
   cd StackDeploy
   ```
2. Configure the environment.
   ```bash
   cp .env.example .env
   # Edit .env: set HONCHO_DB_PASSWORD, CAMOFOX_API_KEY, and other required values.
   ```
3. Deploy the stack.
   ```bash
   ./scripts/bootstrap.sh
   ```
4. Validate that all services are healthy.
   ```bash
   ./scripts/healthcheck.sh localhost
   ```

### Configuration

All secrets live in `.env` (never committed). See `.env.example` for documented placeholders.

| Variable | Purpose | Default |
|---|---|---|
| `HONCHO_DB_PASSWORD` | PostgreSQL password for Honcho | *(none)* |
| `CAMOFOX_API_KEY` | Camofox authentication key | *(empty)* |
| `CAMOFOX_ADMIN_KEY` | Camofox admin key | *(empty)* |
| `OBSIDIAN_VAULT_PATH` | Host path for Obsidian vault | *(empty)* |
| `SERVER_IP` | Tailscale / local IP for docs | *(empty)* |
| `NEO4J_AUTH` | Neo4j authentication string | *(empty)* |

### Roadmap

- [ ] Add unified backup / restore playbook
- [ ] Integrate Loki / Prometheus metrics export
- [ ] Publish pinned image digests for production
- [ ] Add ARM64 build matrix to CI/CD

### License

MIT © JorahOne, LLC

---

*Built by [JorahOne, LLC](https://github.com/JorahOne-Services) — network security, AD/M365, and infrastructure automation for SMBs and public sector.*
