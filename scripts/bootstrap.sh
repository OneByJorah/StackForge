#!/usr/bin/env bash
set -euo pipefail

echo "=== StackDeploy Bootstrap ==="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose v2 not found. Please install Docker Compose v2."
    exit 1
fi

# Check .env
if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
        cp .env.example .env
        echo "📋 Created .env from .env.example"
        echo "⚠️  Please edit .env with your passwords before continuing!"
        echo "   Required: HONCHO_DB_PASSWORD, SERVER_IP, COUCHDB_ADMIN_PASSWORD"
        echo "   Optional: COUCHDB_SYNC_PASSWORD, OBSIDIAN_VAULT_PATH"
        exit 1
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

echo "🔧 Pulling images..."
docker compose pull

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🏥 Running health check..."
./scripts/healthcheck.sh localhost

echo ""
echo "✅ StackDeploy is ready!"
echo ""
echo "Access points:"
echo "  SearXNG:            http://localhost:8080"
echo "  Qdrant:             http://localhost:6333"
echo "  Honcho API:         http://localhost:8000"
echo "  CouchDB:            http://localhost:5984"
echo "  Obsidian:           http://localhost:8083"
echo "  Syncthing:          http://localhost:8384"
echo "  Selenium:           http://localhost:4444"
echo "  Ollama:             http://localhost:11434"