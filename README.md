<!-- j1-brand:v2 -->
<div align="center">

# StackDeploy

A production-ready, self-hosted Docker Compose stack for Hermes Agents — memory, search, browser automation, and file sync, all optimized for CPU-based hardware.

[![GitHub](https://img.shields.io/badge/github-OneByJorah%2FStackDeploy-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://github.com/OneByJorah/StackDeploy)
[![License](https://img.shields.io/badge/license-MIT-FFB300?style=for-the-badge&labelColor=0d0d0c)](LICENSE)
[![Language](https://img.shields.io/badge/JavaScript-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://javascript.com)
[![Built by](https://img.shields.io/badge/built%20by-JorahOne%20LLC-FFB300?style=for-the-badge&labelColor=0d0d0c)](https://github.com/OneByJorah)

</div>

---

## Why This Exists

Standing up the full Hermes agent infrastructure means wiring together a dozen services — database, vector store, search, browser automation, file sync — each with its own config. StackDeploy bundles them into a single `docker-compose` stack tuned for consumer CPU hardware, with optional GPU support for Ollama. One config, one `up` command, and your Hermes agents have everything they need.

## Services

| Service | Port | Purpose |
|---|---|---|
| **SearXNG** | — | Private meta-search engine |
| **Qdrant** | — | Vector database for RAG and memory |
| **Ollama** | — | Local LLM inference (GPU optional) |
| **Honcho API** | 8000 | Agent memory and state management |
| **PostgreSQL** | 5432 | Relational data with pgvector |
| **Redis** | 6379 | Caching and message broker |
| **CouchDB** | 5984 | Obsidian LiveSync database |
| **Obsidian Web** | 8083 | In-browser Obsidian access |
| **Syncthing** | 8384 | Peer-to-peer file synchronization |
| **Selenium Chrome** | 4444 | Headless browser for web agents |

## Quick Start

```bash
git clone https://github.com/OneByJorah/StackDeploy.git
cd StackDeploy
cp .env.example .env   # set server IP, database passwords, etc.
docker compose up -d
```

Prerequisites: Docker, Docker Compose, Tailscale, 8GB+ RAM, 50GB+ disk.

## Architecture

```
┌──────────────────────────────────────────┐
│              Tailscale Mesh              │
│   (all services on a single Tailscale IP)│
└──────┬──────┬──────┬──────┬──────┬──────┘
       │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼    ▼
    ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
    │LLM │ │Vec │ │Mem │ │Sync│ │Web │ │Srch│
    │Oll │ │Qdr │ │Hon │ │Syn │ │Obs │ │SxNG│
    └────┘ └────┘ └────┘ └────┘ └────┘ └────┘
```

## Documentation

| Doc | Description |
|---|---|
| [Getting Started](docs/start.md) | Prerequisites and first deployment |
| [Service Configuration](docs/services.md) | Tuning each service for your hardware |
| [Tailscale Setup](docs/tailscale.md) | Networking all services on your mesh VPN |

---

## License

MIT © JorahOne, LLC — see [LICENSE](LICENSE)

<sub>Part of the JorahOne infrastructure ecosystem.</sub>
