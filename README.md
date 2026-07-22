<div align="center">
  <img src="https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge">
</div>

<br>

<div align="center">
  <h1>StackForge</h1>
  <p><strong>Production-Ready Docker Stack for AI Agents</strong></p>
  <p>CPU-only, privacy-focused, one command deploy.</p>
  <p>
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#stack">Stack</a> •
    <a href="#contributing">Contributing</a>
  </p>
</div>

---

## Screenshot

![StackForge Dashboard](docs/screenshot.png)
*Self-hosted AI agent stack with Ollama, Qdrant, and Honcho.*

## Features

- **One Command Deploy** — `docker compose up -d` and you're ready.
- **CPU-Only** — No GPU required, runs on any machine.
- **Privacy-Focused** — All data stays on your infrastructure.
- **Ollama LLMs** — Local language model hosting.
- **Qdrant Vector DB** — Vector storage for embeddings.
- **Honcho Memory** — Long-term agent memory.
- **SearXNG Search** — Private web search.
- **Production Ready** — Health checks, restarts, and monitoring.

## Quick Start

```bash
git clone https://github.com/OneByJorah/StackForge.git
cd StackForge

# Configure your models
cp .env.example .env

# Deploy the stack
docker compose up -d
```

### Access Services

| Service | URL |
|---------|-----|
| Ollama | http://localhost:11434 |
| Qdrant | http://localhost:6333 |
| Honcho | http://localhost:4000 |
| SearXNG | http://localhost:8080 |

## Stack Components

| Component | Purpose |
|-----------|---------|
| **Ollama** | Local LLM hosting (Llama2, Mistral, etc.) |
| **Qdrant** | Vector database for embeddings |
| **Honcho** | Long-term agent memory |
| **SearXNG** | Privacy-respecting web search |
| **PostgreSQL** | Relational database |
| **Redis** | Caching and queues |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODELS` | `llama2,mistral` | Models to download |
| `QDRANT_PORT` | `6333` | Qdrant API port |
| `HONCHO_PORT` | `4000` | Honcho API port |
| `POSTGRES_DB` | `stackforge` | PostgreSQL database |
| `POSTGRES_USER` | `stackforge` | PostgreSQL user |
| `POSTGRES_PASSWORD` | *(generated)* | PostgreSQL password |

## Architecture

```
AI Agent ──API──▶ Services
    │
    ├──▶ Ollama (LLM)
    ├──▶ Qdrant (Vectors)
    ├──▶ Honcho (Memory)
    ├──▶ SearXNG (Search)
    ├──▶ PostgreSQL (Data)
    └──▶ Redis (Cache)
```

## Project Structure

```
StackForge/
├── docker-compose.yml     # Main compose file
├── .env.example           # Environment template
├── ollama/
│   └── Modelfile          # Custom model configs
├── qdrant/
│   └── config.yaml        # Qdrant configuration
├── scripts/
│   ├── setup.sh           # Initial setup
│   ├── health-check.sh    # Health monitoring
│   └── backup.sh          # Data backup
└── README.md
```

## Hardware Requirements

| Scale | CPU | RAM | Storage |
|-------|-----|-----|---------|
| **Basic** | 4 cores | 8GB | 50GB |
| **Standard** | 8 cores | 16GB | 100GB |
| **Performance** | 16 cores | 32GB | 200GB+ |

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

## Security

For security concerns, see [SECURITY.md](SECURITY.md). Please report vulnerabilities to **info@jorahone.com** — do not use public issues.

## License

MIT © Jhonattan L. Jimenez

---

<div align="center">
  <p>Production-ready AI agent stack.</p>
  <p><a href="https://github.com/OneByJorah">@OneByJorah</a></p>
</div>
