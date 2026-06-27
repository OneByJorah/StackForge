# StackDeploy (StackDeploy)

**Version:** v1.3  
**Status:** Production Ready  
**Repository:** https://github.com/OneByJorah/StackDeploy

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Features](#features)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Service Management](#service-management)
- [CI/CD & Deployment](#cicd--deployment)
- [Security](#security)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [Hermes Integration](#hermes-integration)
- [License](#license)
- [Author](#author)

---

## Overview

StackDeploy is a Docker Compose-based self-hosted stack for Hermes Agents. It consolidates local web search, long-term memory, browser automation, vector storage, and Obsidian note-taking into a reproducible, one-command deployment. The stack is designed to run on CPU-only hosts with no local GPU, while keeping the LLM layer intentionally external so you can plug in free cloud providers.

Bundled integrations:
- **browser-search**: SearXNG + Camofox + CloakBrowser for search and protected-site browsing
- **obsidian-skills**: Agent skills for Obsidian Markdown, Bases, JSON Canvas, CLI, and Defuddle extraction

Secrets and environment configuration are managed via `docker-compose.yml` and `.env`, never committed to version control.

---

## Architecture

Client → Hermes Agent → Local services (SearXNG, Camofox, Qdrant, Obsidian, PostgreSQL + Redis) → optional upstream LLM provider via Hermes config.

---

## Technology Stack

| Layer | Stack |
|---|---|
| Runtime | Linux (Ubuntu 22.04+) |
| Primary Stack | Docker Compose / Bash |
| VCS | Git + GitHub (`github.com/OneByJorah/StackDeploy`) |
| Memory / Context | Honcho |
| Notifications | Telegram (J1-bot) |
| Release path | `git push origin main` (documentation/build on branch) |

---

## Features

- **SearXNG**: privacy-respecting self-hosted web search.
- **Camofox**: browser navigation via REST API for standard sites.
- **CloakBrowser**: stealth browser fallback for anti-bot protected sites.
- **Honcho API**: long-term memory and workspace context for Hermes.
- **Qdrant**: vector storage for semantic retrieval.
- **Obsidian vault**: markdown-backed note-taking exposed via web UI.
- **Obsidian Skills**: agent-ready skills for Markdown, Bases, Canvas, CLI, and Defuddle extraction.
- **PostgreSQL + pgvector + Redis**: durable memory backend with vector support.
- **One-command bootstrap**: clone, env, stack, init, healthcheck.
- **Extensible service-based design**: add modules via Compose blocks.
- **CPU-first design**: no local GPU required for base stack.

---

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/OneByJorah/StackDeploy.git
cd StackDeploy

# 2. Environment
cp .env.example .env
# Edit .env: set SERVER_IP, HONCHO_TOKEN, HONCHO_DB_PASSWORD

# 3. Start the stack
docker compose up -d
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

## Browser-search

Self-hosted search and browsing via SearXNG, Camofox, and CloakBrowser.

**Endpoints**

| Service | Port | Notes |
|---|---|---|
| SearXNG | `8080` | JSON API: `/search?format=json&q=<query>` |
| Camofox | `9377` | REST API: `/docs` for Swagger UI |

**Setup**

```bash
cd browser-search
npm install
```

Optional: run Camofox with auth keys in `.env`:
```bash
camofox_api_key=... camofox_admin_key=... docker compose up -d
```

CloakBrowser is included as npm scripts:
```bash
node scripts/cloak/cloak-fetch.mjs "https://example.com"
```

## Obsidian Skills

Agent-readable skills for working with Obsidian vaults.

| Skill | Purpose |
|---|---|
| `obsidian-markdown` | Create/edit Obsidian Flavored Markdown |
| `obsidian-bases` | Create/edit `.base` views and filters |
| `json-canvas` | Create/edit `.canvas` mind maps |
| `obsidian-cli` | Interact with vault via `obsidian` CLI |
| `defuddle` | Extract clean markdown from URLs |

These skills are available at `obsidian-skills/skills/`. If your agent loads skills from a directory, point it there. For Obsidian CLI, ensure the desktop app is installed and accessible on the host.

## CI/CD & Deployment

- Branch model: `main` for stable, feature branches for work-in-progress.
- Use `git push origin <branch>` to publish changes and trigger downstream automation.
- Keep Cheatsheet/docs in sync before merging: docs, README, and any changed service ports/endpoints.

---

## Security

- Secrets are handled through `.env` files with restrictive permissions; never store raw API tokens in README or source.
- Frontend artifacts and dashboard access paths are not credential-based in this repository.
- Services expose ports on localhost / trusted interfaces by default; bind only to trusted networks in production.

---

## Project Structure

```text
StackDeploy/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── browser-search/         # browser-search skill + scripts (CloakBrowser, Camofox helper)
│   ├── SKILL.md
│   ├── scripts/
│   └── docker/
├── obsidian-skills/        # kepano/obsidian-skills agent skills
│   └── skills/
│       ├── defuddle/
│       ├── json-canvas/
│       ├── obsidian-bases/
│       ├── obsidian-cli/
│       └── obsidian-markdown/
├── scripts/
│   ├── bootstrap.sh
│   ├── healthcheck.sh
│   ├── init-honcho.sh
│   └── init-obsidian.sh
├── docs/
│   ├── SERVER_SETUP.md
│   └── HERMES_SETUP.md
└── README.md
```

---

## Screenshots

All screenshots are live captures from the local dev instance.

_(Screenshots will be added after build/run capture.)_

---

## Contributing

1. Create a feature branch off `main`.
2. Follow the existing code style and README section order.
3. Submit a PR with description and screenshots for UI changes.
4. Do not commit real secrets or `.env` files.

## Hermes Integration

StackDeploy ships a first-class Hermes Agent skill.

Local install path for Hermes:
```bash
~/.hermes/profiles/agent-20260614-212330/skills/autonomous-ai-agents/selfhosted-stack-deploy/SKILL.md
```

Inline Hermes commands:
```bash
cd /home/j1admin/StackDeploy && bash tests/smoke.sh
docker compose ps
curl -s 'http://localhost:8080/search?format=json&q=<query>&language=en'
cd /home/j1admin/StackDeploy/browser-search && bash scripts/install-browser-search.sh
node scripts/cloak/cloak-fetch.mjs "https://example.com"
```

Hermes config:
```yaml
web:
  backend: searxng
  searxng_url: "http://127.0.0.1:8080"
```

Docs:
```bash
cat docs/hermes.md
```

---

## License

MIT

---

## Author

Built by **Jhonattan L. Jimenez**.
