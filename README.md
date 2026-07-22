# StackForge

Production-ready Docker Compose stack for AI agents — CPU-only, privacy-focused, self-hosted with one command.

![status](https://img.shields.io/badge/status-active-FFB300?style=flat-square)
![language](https://img.shields.io/badge/python+docker-0d0d0c?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-FFB300?style=flat-square)

## Overview

StackForge is a production-ready, CPU-optimized Docker Compose stack for self-hosted AI agents. One bootstrap script deploys SearXNG, Qdrant, Honcho (PostgreSQL + pgvector + Redis), Obsidian, Syncthing, Selenium, and Ollama on consumer hardware. Privacy-focused — no third-party APIs required.

## Features

- One-command deploy — single bootstrap script for full stack
- CPU only — optimized for consumer hardware (GPU optional for Ollama)
- Privacy-focused — self-hosted SearXNG, no third-party APIs
- Long-term memory — Honcho API with PostgreSQL + pgvector + Redis
- Vector database — Qdrant for RAG and semantic search
- Obsidian integration — CouchDB LiveSync vault with web viewer
- P2P file sync — Syncthing between server and laptop
- Browser automation — Selenium standalone Chrome for agent web tasks
- Local LLM — Ollama for offline inference
- Mesh networking ready — all services on single host IP

## Services

| Service | Port | Purpose |
|---------|------|---------|
| SearXNG | 8080 | Privacy-respecting metasearch |
| Qdrant | 6333 | Vector database for embeddings |
| Honcho API | 8000 | Long-term memory for agents |
| Honcho DB | 5432 | PostgreSQL + pgvector |
| Honcho Redis | 6379 | Session cache |
| Obsidian | 5984 | CouchDB LiveSync vault |
| Syncthing | 8384 | P2P file sync |
| Selenium | 4444 | Browser automation |
| Ollama | 11434 | Local LLM inference |

## Installation

```bash
git clone https://github.com/OneByJorah/StackForge.git
cd StackForge

sudo ./bootstrap.sh --auto
```

## Configuration

See `.env.example` for all available options.

## License

MIT — see [LICENSE](LICENSE).

---
Part of the JorahOne / J1 ecosystem — self-hosted AI infrastructure on consumer hardware.
