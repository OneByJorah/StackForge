#!/usr/bin/env bash
# =============================================================================
# StackDeploy Bootstrap — One-command deployment
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "  StackDeploy Bootstrap v3.0.0"
echo "=========================================="
echo ""

# --- Prerequisites ---
info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    error "Docker not found. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose v2 not found. Please install Docker Compose v2."
    exit 1
fi

info "✅ Docker $(docker --version)"
info "✅ Docker Compose $(docker compose version --short)"

# --- Environment ---
echo ""
info "Checking environment configuration..."

if [[ ! -f "$REPO_ROOT/.env" ]]; then
    if [[ -f "$REPO_ROOT/.env.example" ]]; then
        cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
        info "Created .env from .env.example"
        warn "⚠️  Please edit .env with your configuration before continuing!"
        echo ""
        echo "   Required variables:"
        echo "     - HONCHO_DB_PASSWORD"
        echo "     - SERVER_IP"
        echo ""
        echo "   Optional variables:"
        echo "     - CAMOFOX_API_KEY, CAMOFOX_ADMIN_KEY"
        echo "     - OBSIDIAN_VAULT_PATH"
        echo "     - QDRANT_API_KEY, REDIS_PASSWORD"
        echo "     - GRAFANA_ADMIN_PASSWORD"
        echo ""
        exit 1
    else
        error ".env.example not found"
        exit 1
    fi
fi

# Check for placeholder values
if grep -q "REPLACE_WITH" "$REPO_ROOT/.env" 2>/dev/null; then
    warn "⚠️  .env still contains placeholder values. Please update them."
    grep "REPLACE_WITH" "$REPO_ROOT/.env" || true
fi

info "✅ .env file found"

# --- Secrets ---
echo ""
info "Checking secrets..."

if [[ ! -d "$REPO_ROOT/secrets" ]] || [[ -z "$(ls -A "$REPO_ROOT/secrets"/*.txt 2>/dev/null)" ]]; then
    warn "⚠️  Secrets not initialized. Running secrets init..."
    bash "$REPO_ROOT/scripts/manage-secrets.sh" init
else
    info "✅ Secrets directory found"
fi

# --- Configuration Validation ---
echo ""
info "Validating configuration..."
if bash "$REPO_ROOT/scripts/validate-config.sh"; then
    info "✅ Configuration valid"
else
    warn "⚠️  Configuration has warnings (continuing anyway)"
fi

# --- Pull Images ---
echo ""
info "Pulling Docker images..."
docker compose pull
info "✅ Images pulled"

# --- Start Services ---
echo ""
info "Starting services..."
docker compose up -d
info "✅ Services started"

# --- Wait for Health ---
echo ""
info "Waiting for services to become healthy..."
for i in $(seq 1 30); do
    STATUS=$(docker compose ps --format json 2>/dev/null || echo "")
    if [ -n "$STATUS" ]; then
        echo "$STATUS" | python3 "$REPO_ROOT/scripts/check-health.py" && break || true
    fi
    sleep 5
done

# --- Health Check ---
echo ""
info "Running health check..."
if bash "$REPO_ROOT/scripts/healthcheck.sh" localhost; then
    echo ""
    echo "=========================================="
    info "✅ StackDeploy is ready!"
    echo "=========================================="
    echo ""
    echo "Access points:"
    echo "  SearXNG:            http://localhost:8080"
    echo "  Camofox:            http://localhost:9377"
    echo "  Obsidian:           http://localhost:8083"
    echo "  Qdrant:             http://localhost:6333"
    echo "  Honcho API:         http://localhost:8081"
    echo "  Prometheus:         http://localhost:9090"
    echo "  Grafana:            http://localhost:3000"
    echo "  Loki:               http://localhost:3100"
    echo ""
    echo "Management:"
    echo "  Health check:       bash scripts/healthcheck.sh localhost"
    echo "  Config validate:    bash scripts/validate-config.sh"
    echo "  Secrets manage:     bash scripts/manage-secrets.sh"
    echo "  View logs:          docker compose logs -f"
    echo ""
else
    error "❌ Some services failed health check"
    echo ""
    echo "Check service status: docker compose ps"
    echo "View logs:            docker compose logs --tail=50"
    exit 1
fi
