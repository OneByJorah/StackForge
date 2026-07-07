# INTENT.md — J1-PIPELINE Phase -1 (ORACLE)

**Repository:** `OneByJorah/StackForge`
**Analysis Date:** 2026-07-05
**Analyst:** J1-PIPELINE ORACLE (read-only)
**Status:** Intent Reconstructed

---

## What This System Does

### Technical Role

StackForge is a **production-ready Docker Compose stack** that provides self-hosted AI-agent infrastructure in a single deployable unit. It bundles 10+ services across five capability domains, all wired together with health checks, network isolation, and Tailscale integration.

| Category | Services | Ports |
|----------|----------|-------|
| **Search** | SearXNG (privacy metasearch) | 8080 |
| **Vector Storage** | Qdrant (RAG / semantic search) | 6333 |
| **Memory Layer** | Honcho API + PostgreSQL+pgvector + Redis | 8000, 5432, 6379 |
| **Notes & Sync** | CouchDB (LiveSync backend), Obsidian Web Viewer (Caddy), Syncthing (P2P file sync) | 5984, 8083, 8384 |
| **Automation** | Selenium standalone Chrome (browser automation) | 4444 |
| **Local LLM** | Ollama (offline inference, optional) | 11434 |
| **Optional Overlays** | Portainer (container admin), Headroom/Aphrodite (LLM proxy + Neo4j), NOC Dashboard (monitoring) | 9000, 8787, 9500 |

**Network topology:**
- Two Docker networks: `stackdeploy-tailnet` (exposed services, bridge) and `stackdeploy-backend` (internal DB/cache, bridge, `internal: true`)
- All services on `tailnet` are reachable via a single Tailscale IP
- DB and cache services (`honcho-db`, `honcho-redis`) are on the internal network only, with host ports bound to `127.0.0.1` for admin access

### Operational Role

StackForge is the **companion infrastructure layer for Hermes Agent** (by Nous Research). A Hermes agent running on a server with StackForge can:

- **Search the web privately** via self-hosted SearXNG (no third-party search API)
- **Store and retrieve long-term memory** via Honcho (LLM-powered memory with PostgreSQL+pgvector)
- **Perform RAG / semantic search** via Qdrant vector database
- **Automate browser tasks** via Selenium Chrome (or the optional Camofox/CloakBrowser from `browser-search/`)
- **Read and write notes** to an Obsidian vault, synced to the user's laptop via Syncthing or CouchDB LiveSync
- **Run local LLM inference** via Ollama (CPU-only by default, GPU optional)
- **Monitor all services** via the optional NOC Dashboard

The stack is designed to be deployed on a single machine (e.g., a home server, VPS, or Tailscale node) and consumed by one or more Hermes agents over the local network or Tailscale mesh.

---

## Why This Was Built

### Real Problem

AI agents like Hermes need a suite of local infrastructure to function autonomously: web search, persistent memory, vector storage, browser automation, and note-taking. Setting up each of these services individually — configuring Docker networks, health checks, environment variables, volume mounts, and security — is tedious, error-prone, and hard to maintain. The problem is compounded when multiple agents share the same infrastructure.

### Why Existing Tools Were Insufficient

Each individual service (SearXNG, Qdrant, Honcho, CouchDB, Syncthing, Selenium, Ollama) already existed as a standalone Docker image. What was missing was:

1. **No unified deployment** — No single `docker compose up` that wires all services together with correct dependency ordering, health checks, and network isolation.
2. **No Tailscale-native design** — Existing stacks assumed public IPs or reverse proxies. StackForge is designed from the ground up for a single Tailscale IP, with no public ports required.
3. **No Hermes-specific integration** — The services needed to be pre-configured with the exact endpoints, auth schemes, and data formats that Hermes Agent expects (e.g., Honcho's memory API, SearXNG's JSON search format, Qdrant's REST API).
4. **No health-check standardization** — Each image ships different tools (wget, curl, python3, bash). StackForge standardizes health checks per-image so `docker compose ps` actually works.
5. **No optional overlay pattern** — Services like Portainer, Headroom, and the NOC Dashboard are useful but not essential. StackForge's `-f docker-compose.*.yml` overlay pattern lets users opt in without modifying the core compose file.

### What Triggered Development

The initial commit message is `"chore: bootstrap Free Auto Project repo"`, suggesting the repo started as a general "free auto" infrastructure project. The trigger for the current form was the **development of Hermes Agent by Nous Research**, which created an immediate need for a self-hosted, privacy-focused, CPU-friendly infrastructure stack that could be deployed alongside the agent. The repo evolved through several phases:

1. **Initial bootstrap** — Basic Docker Compose with SearXNG + Qdrant
2. **Honcho integration** — Added long-term memory (submodule from plastic-labs/honcho)
3. **Obsidian + Syncthing** — Added note-taking and P2P file sync
4. **Browser automation** — Added Selenium Chrome (and later Camofox/CloakBrowser from `browser-search/`)
5. **Ollama** — Added local LLM inference
6. **NOC Dashboard + Portainer + Headroom** — Added monitoring and optional overlays
7. **Interactive bootstrap** — Unified `bootstrap.sh` with interactive password generation
8. **Security overhaul** — CodeQL, dependabot, CI/CD, health check standardization

### Ecosystem Fit

StackForge is the **infrastructure layer** in the JorahOne / OneByJorah ecosystem, sitting between Hermes Agent and the raw Docker host.

```
JorahOne Ecosystem
├── Hermes Agent (Nous Research)     ← primary consumer
│   ├── SearXNG (web search)
│   ├── Honcho (long-term memory)
│   ├── Qdrant (vector storage)
│   ├── Selenium / Camofox (browser automation)
│   ├── Obsidian (note-taking)
│   └── Ollama (local LLM)
├── StackForge                      ← THIS REPO: unified infrastructure
│   ├── docker-compose.yml           (core services)
│   ├── docker-compose.headroom.yml  (optional: LLM proxy + Neo4j)
│   ├── docker-compose.portainer.yml (optional: container admin)
│   └── noc-dashboard/               (optional: monitoring)
├── headroom-j1 (submodule)          ← optional LLM proxy layer
└── browser-search/                  ← optional browser automation toolkit
```

---

## Operational Classification

**Classification: PRODUCTION**

Evidence:
- **CI/CD pipeline** — GitHub Actions with lint (hadolint, shellcheck, yamllint), build, test (smoke test), and deploy stages
- **Security scanning** — CodeQL analysis (Python, JavaScript, TypeScript) on push and weekly schedule
- **Dependency management** — Dependabot configured for pip, npm, Docker, and GitHub Actions (weekly)
- **Health checks** — Every service has a Docker health check using the tool available in its image
- **Security policy** — `SECURITY.md` with 90-day disclosure timeline, dedicated email (j1admin@onebyjorah.com)
- **Community readiness** — `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, issue templates (bug report, feature request), PR template
- **License** — MIT (explicit, standard)
- **Documentation** — Comprehensive README, 6 docs files (server setup, Honcho setup, Hermes setup, Headroom setup, maintenance, Hermes integration)
- **Secrets management** — `.env` in `.gitignore`, `.env.example` with placeholders, no secrets in git history
- **Network isolation** — Internal Docker network for DB/cache, explicit port mapping, read-only config mounts
- **Test evidence** — `tests/smoke.sh` and `test_results.txt` showing historical test runs
- **Version pinning** — Specific image tags (e.g., `couchdb:3.4`, `redis:8.2`, `pgvector/pgvector:pg15`)

---

## Key Architectural Decisions

1. **Single Tailscale IP as the sole network endpoint** — All services are exposed on a single Tailscale IP with direct port mapping. No reverse proxy, no public DNS, no port forwarding. This eliminates attack surface and simplifies configuration: one IP to remember, one firewall rule.

2. **Two-tier Docker network isolation** — `stackdeploy-tailnet` (bridge, attachable) for services that need host access; `stackdeploy-backend` (internal, no host access) for DB and cache. DB credentials are never exposed to the host network.

3. **Per-image health check strategy** — Instead of requiring `curl` everywhere, each service uses whatever tool its image ships: `wget` for SearXNG, `bash /dev/tcp` for Qdrant/Ollama, `python3 urllib` for Honcho/Syncthing, `curl` for CouchDB/Caddy/Selenium. This avoids adding unnecessary packages to images.

4. **Optional overlay compose files** — Portainer, Headroom, and NOC Dashboard are separate `docker-compose.*.yml` files that users opt into with `-f` flags. The core `docker-compose.yml` stays clean and minimal.

5. **Honcho as a git submodule** — The Honcho API is pulled from `plastic-labs/honcho` as a submodule under `vendor/honcho`, allowing local builds and custom config without forking the upstream.

6. **Interactive bootstrap with auto-generated secrets** — `bootstrap.sh` detects the Tailscale IP, prompts for passwords with auto-generated defaults, and writes `.env` — no manual editing of secrets files required.

7. **Obsidian vault as the shared memory surface** — The `obsidian/vault/` directory is simultaneously served by Caddy (web viewer), synced by Syncthing (P2P), and replicated by CouchDB (LiveSync). This gives three access paths to the same notes.

8. **CPU-first design with optional GPU** — All services are configured for CPU-only operation by default. Ollama's GPU acceleration is commented out, and Selenium's `shm_size` is set to 2g for headless Chrome stability.

---

## Repository Structure

```
StackForge/
├── docker-compose.yml                  # Core compose — all 10 services
├── docker-compose.headroom.yml         # Optional: Headroom/Aphrodite LLM proxy
├── docker-compose.portainer.yml         # Optional: Portainer container admin
├── .env.example                         # Environment variable template
├── .env.honcho.example                 # Honcho LLM provider config template
├── .env.headroom.example               # Headroom Neo4j config template
├── .gitignore
├── .dockerignore
├── .gitmodules                         # Submodules: vendor/honcho, vendor/headroom
├── bootstrap.sh                        # Interactive first-run setup script
├── README.md                           # Primary documentation
├── LICENSE                             # MIT
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── test_results.txt                    # Historical test output
│
├── scripts/
│   ├── bootstrap.sh                    # Legacy bootstrap (docker compose up + healthcheck)
│   ├── healthcheck.sh                  # External health check (curl-based)
│   ├── install.sh                      # Python venv setup
│   ├── init-honcho.sh                  # Honcho env + config init
│   ├── init-obsidian.sh                # Obsidian vault directory init
│   ├── init-headroom.sh                # Headroom env init
│   └── install-browser-search.sh       # npm install for browser-search
│
├── tests/
│   └── smoke.sh                        # Smoke test script
│
├── docs/
│   ├── SERVER_SETUP.md                 # Server installation guide
│   ├── HERMES_SETUP.md                 # Hermes Agent configuration
│   ├── HONCHO_SETUP.md                 # Honcho memory setup
│   ├── HEADROOM_SETUP.md               # Headroom/Aphrodite setup
│   ├── MAINTENANCE.md                  # Maintenance procedures
│   ├── hermes.md                       # Hermes integration reference
│   └── screenshots/                    # UI screenshots
│
├── searxng/
│   └── settings.yml                    # SearXNG config (JSON format, public_instance: false)
│
├── honcho/
│   ├── config.toml                     # Honcho API config (LLM providers, model tiers)
│   ├── honcho-config.json              # Hermes Honcho plugin config
│   └── .env.honcho.example             # Honcho env template (duplicate)
│
├── obsidian/
│   ├── Caddyfile                       # Caddy reverse proxy config
│   ├── index.html                      # Vault viewer HTML
│   ├── couchdb-init.sh                 # CouchDB user + CORS init script
│   ├── scan.py                         # Vault index scanner
│   ├── vault-write.sh                  # Vault write helper
│   └── vault/                          # Markdown note vault
│       ├── Welcome.md
│       └── .stfolder/                  # Syncthing marker
│
├── syncthing/
│   └── config/                         # Syncthing device config (empty)
│
├── headroom/
│   └── headroom-config.example         # Headroom config example
│
├── vendor/
│   ├── honcho/                         # Git submodule (plastic-labs/honcho)
│   └── headroom/                       # Git submodule (OneByJorah/headroom-j1)
│
├── browser-search/                     # Browser automation toolkit (standalone project)
│   ├── README.md, SKILL.md, LICENSE
│   ├── scripts/cloak/                  # Cloak browser automation scripts
│   ├── scripts/camofox/                # Camofox integration
│   └── package.json
│
├── obsidian-skills/                    # Hermes Obsidian skills (standalone project)
│   ├── obsidian-cli/SKILL.md
│   ├── obsidian-bases/SKILL.md
│   ├── obsidian-markdown/SKILL.md
│   ├── json-canvas/SKILL.md
│   └── defuddle/SKILL.md
│
├── noc-dashboard/                      # Optional monitoring dashboard
│   ├── README.md
│   ├── Dockerfile
│   ├── docker-compose.dashboard.yml
│   ├── backend/app.py, standalone.py
│   ├── frontend/ (index.html, agents.html, metrics.html, etc.)
│   └── healthcheck.sh.patched
│
├── skills/
│   └── devops/stackforge/SKILL.md     # Hermes skill for StackForge ops
│
└── .github/
    ├── workflows/
    │   ├── ci-cd.yml                   # Lint → Build → Test → Deploy
    │   ├── codeql.yml                  # CodeQL security analysis
    │   └── webpack.yml                 # Webpack build (legacy)
    ├── dependabot.yml                  # Weekly dependency updates
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Notes

- **Naming discrepancy — healthcheck.sh references services not in main compose:** `scripts/healthcheck.sh` checks for Camofox (port 9377) and CloakBrowser (port 9222), but the main `docker-compose.yml` uses Selenium standalone Chrome (port 4444) for browser automation. Camofox and CloakBrowser live in the `browser-search/` subdirectory and are not wired into the main compose file. The healthcheck script appears to be from an earlier version of the stack.
- **`docker-compose.headroom.yml` was previously empty but now has content** — The file at the repo root now contains 75 lines with a full Headroom proxy + Qdrant + Neo4j service definition. The historical artifact at `noc-dashboard/docker-compose.headroom.yml.patched` still exists but the root file is the canonical version.
- **`vendor/` submodules may not be initialized** — `vendor/honcho` and `vendor/headroom` are declared in `.gitmodules` but the `test_results.txt` shows a build failure (`failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory`) because the submodule wasn't checked out.
- **`.gitignore` has a merged pattern bug** — Line 24 reads `*.swoCostForge/` which merged the `*.swo` pattern with the `CostForge/` entry. A recent commit (`c85d84d`) attempted to fix this.
- **Initial commit message** — `"chore: bootstrap Free Auto Project repo"` — suggests the repo began as a general-purpose automation project before becoming Hermes-specific.
- **SearXNG health check may report `unhealthy`** — The `test_results.txt` shows SearXNG as `(unhealthy)` even though the service is running. This is a known issue with SearXNG's optional metrics endpoint.
- **Honcho API port discrepancy** — The main compose maps Honcho to port 8000, but `scripts/healthcheck.sh` and `scripts/bootstrap.sh` reference port 8081. The README and `.env.example` use 8000. The 8081 references appear to be from an earlier version.
- **Dependabot ecosystem mismatch** — Dependabot is configured for `pip` and `npm` ecosystems, but there is no `requirements.txt` or `package.json` at the repo root. The only `requirements.txt` is inside `noc-dashboard/backend/` and the only `package.json` is inside `browser-search/`. The `pip` and `npm` Dependabot entries are template vestiges that won't find anything to update at the root directory.
- **`webpack.yml` workflow is a legacy artifact** — The `.github/workflows/webpack.yml` runs `npx webpack` on push to `master`, but there is no `webpack.config.js` or `package.json` at the repo root. This workflow will fail on every run. It appears to be a template leftover from an earlier project phase.
- **`scripts/bootstrap.sh` (legacy) references services not in the main compose** — The legacy `scripts/bootstrap.sh` references Portainer (port 9000), Camofox (port 9377), CloakBrowser (port 9222), and Honcho API (port 8081), none of which match the current `docker-compose.yml`. The root `bootstrap.sh` (interactive) is the canonical version and correctly references the current service ports.
- **`docs/MAINTENANCE.md` is a stub** — The maintenance doc contains only 3 commands (restart stack, update model, backup Honcho memory) and references a `llama-server` service that does not exist in any compose file. It is not a substantive maintenance guide.
- **`obsidian-skills/` and `browser-search/` are embedded standalone projects** — These directories have their own READMEs, licenses, `.gitignore` files, and `package.json`. They are not git submodules but were likely copied in from other repos. `obsidian-skills/` contains 5 Hermes skills (obsidian-cli, obsidian-bases, obsidian-markdown, json-canvas, defuddle) that are not referenced by any compose file or script.
