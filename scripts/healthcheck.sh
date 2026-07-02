#!/usr/bin/env bash
# =============================================================================
# StackDeploy Health Check
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SERVER="${1:-localhost}"
TIMEOUT="${2:-5}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "  StackDeploy Health Check"
echo "  Target: $SERVER"
echo "  Timeout: ${TIMEOUT}s"
echo "=========================================="
echo ""

check_service() {
    local name="$1"
    local url="$2"
    local expected="${3:-}"
    local timeout="${4:-$TIMEOUT}"

    if [[ -n "$expected" ]]; then
        if curl -sf --max-time "$timeout" "$url" | grep -q "$expected"; then
            info "✅ $name — $url"
            return 0
        fi
    else
        if curl -sf --max-time "$timeout" -o /dev/null "$url"; then
            info "✅ $name — $url"
            return 0
        fi
    fi
    error "❌ $name — $url"
    return 1
}

FAILED=0

echo "--- Core Infrastructure ---"
check_service "SearXNG" "http://$SERVER:8080/search?q=healthcheck&format=json" "results" || FAILED=1
check_service "Camofox" "http://$SERVER:9377/health" "ok" || FAILED=1
check_service "Obsidian" "http://$SERVER:8083/" "Obsidian" || FAILED=1
check_service "Qdrant" "http://$SERVER:6333/healthz" "ok" || FAILED=1

echo ""
echo "--- Memory Layer ---"
check_service "Honcho API" "http://$SERVER:8081/healthz" "" || FAILED=1

echo ""
echo "--- Observability ---"
check_service "Prometheus" "http://$SERVER:9090/-/ready" "" || FAILED=1
check_service "Grafana" "http://$SERVER:3000/api/health" "" || FAILED=1
check_service "Loki" "http://$SERVER:3100/ready" "" || FAILED=1

echo ""
echo "--- Optional Services ---"
check_service "CloakBrowser" "http://$SERVER:9222/json/version" "Browser" || warn "⚠️  CloakBrowser not available (optional)"

echo ""
echo "=========================================="
if [[ $FAILED -eq 0 ]]; then
    info "🎉 All services healthy!"
    exit 0
else
    error "❌ Some services are down"
    echo ""
    echo "Quick diagnostics:"
    echo "  docker compose ps"
    echo "  docker compose logs --tail=50"
    echo "  bash scripts/validate-config.sh"
    exit 1
fi
