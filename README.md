<div align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/SearXNG-000?style=for-the-badge&logo=googlesearch&logoColor=white">
</div>

<br>

<div align="center">
  <h1>📦 StackDeploy</h1>
  <p><strong>Production-Ready Docker Compose Stack for Hermes Agents</strong></p>
  <p>One IP, one stack, one admin panel — CPU-only, privacy-focused, self-hosted</p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-services">Services</a> •
    <a href="#-architecture">Architecture</a>
  </p>
</div>

---

## ✨ Features

- **One Command Deploy** — Single bootstrap script for full stack
- **CPU Only** — Optimized for consumer hardware
- **Privacy-Focused** — Self-hosted search with SearXNG
- **Long-Term Memory** — Qdrant vector store with PostgreSQL + pgvector
- **Browser Automation** — CloakBrowser for agent web tasks
- **Obsidian Integration** — Note-taking and markdown skills
- **Redis Caching** — High-performance caching layer
- **Tailscale Ready** — Secure networking out of the box

## 🚀 Quick Start

```bash
git clone https://github.com/OneByJorah/StackDeploy.git
cd StackDeploy
sudo ./bootstrap.sh
```

## 🏗️ Services

| Service | Description |
|---------|-------------|
| SearXNG | Private meta-search engine |
| Camofox | Privacy-focused web rendering |
| CloakBrowser | Browser automation for agents |
| Qdrant | Vector database for embeddings |
| PostgreSQL + pgvector | Relational + vector storage |
| Redis | Caching and pub/sub |
| Obsidian Skills | Note-taking and markdown |

## 🏗️ Architecture

```
Client/Hermes Agent → StackDeploy (one IP)
                           ├── SearXNG (search)
                           ├── Qdrant (memory)
                           ├── PostgreSQL (data)
                           ├── Redis (cache)
                           ├── CloakBrowser (browser)
                           └── Obsidian (notes)
```

## 📄 License

MIT © Jhonattan L. Jimenez

---

<div align="center">
  <p>📦 One stack to rule them all</p>
  <p><a href="https://github.com/OneByJorah">@OneByJorah</a></p>
</div>
