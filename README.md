# StackDeploy — Self-hosted AI Stack for Hermes Agents

**Version:** v1.0  
**Status:** Active Development  
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
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

StackDeploy is a one-command self-hosted AI stack for Hermes Agents. It brings together llama.cpp for local LLM inference, SearXNG for privacy-respecting search, Honcho memory for long-term context, Chrome CDP for browser automation, vector memory for semantic retrieval, TTS for speech synthesis, and observability tooling in a single Docker Compose deployment.

Designed for operators who want full control: run the stack on your own hardware, keep data on-prem, and wire it into Hermes via environment configuration.

---

## Architecture

Client → Nginx / Docker compose → Services (llama.cpp, SearXNG, Honcho, Redis, Postgres/pgvector) → Hermes Agent integration.

Flow:
- SearXNG provides web search.
- llama.cpp serves a local quantized model.
- Honcho + Redis + pgvector hold memory/context.
- Chrome CDP exposes browser automation.
- Observability exports metrics/logs.

---

## Technology Stack

|| Layer | Stack |
|---|---|
| Runtime | Linux (Ubuntu 22.04+) |
| Orchestration | Docker Compose |
| LLM Runtime | llama.cpp (Q4 quant, flash-attn) |
| Search | SearXNG |
| Memory | Honcho API + Redis + pgvector |
| Database | PostgreSQL 15 + pgvector |
| Browser Automation | Chrome CDP |
| Scripts | Bash / curl |
| VCS | Git + GitHub (`github.com/OneByJorah/StackDeploy`) |

---

## Features

- **Local LLM**: llama.cpp with configurable model path, context size, threading, and batching.
- **Privacy search**: self-hosted SearXNG instance.
- **Long-term memory**: Honcho memory API backed by Postgres/pgvector and Redis.
- **Browser control**: Chrome CDP integration.
- **Observability**: metrics and health-check scripts included.
- **One-command bootstrap**: compose + init + bootstrap + healthcheck.

---

## Getting Started

```bash
# 1. Clone
git clone https://github.com/OneByJorah/StackDeploy.git
cd StackDeploy

# 2. Environment
cp .env.example .env
# Edit .env: set model path, passwords, and ports.

# 3. Bring up the stack
docker compose up -d

# 4. Initialize services
./scripts/init-honcho.sh
./scripts/bootstrap.sh

# 5. Verify
./scripts/healthcheck.sh
```

---

## Environment Variables

Key variables from `.env.example`:

| Variable | Purpose |
|---|---|
| `MODEL_PATH` | Path to GGUF model inside the host or mounted volume |
| `CTX_SIZE` | Context window size for llama.cpp |
| `HONCHO_DB_PASSWORD` | Postgres password for Honcho |
| Ports | `8080` (SearXNG), `8082` (llama.cpp), and others |

Keep `.env` out of VCS.

---

## Service Management

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f

# Healthcheck
./scripts/healthcheck.sh
```

Services expose ports on the host; bind only to trusted interfaces in production.

---

## Project Structure

```
StackDeploy/
├── docker-compose.yml
├── .env.example
├── scripts/
│   ├── bootstrap.sh
│   ├── healthcheck.sh
│   └── init-honcho.sh
├── docs/
│   ├── SERVER_SETUP.md
│   ├── HERMES_SETUP.md
│   └── MAINTENANCE.md
└── README.md
```

---

## Screenshots

All screenshots are live captures from the local deployment.

_(Screenshots will be added after build/run capture.)_

---

## Contributing

1. Create a feature branch off `main`.
2. Test changes with `docker compose up -d` and `./scripts/healthcheck.sh`.
3. Submit a PR with description and screenshots for service/UI changes.

---

## License

MIT

---

## Author

Built by **Jhonattan L. Jimenez**.
