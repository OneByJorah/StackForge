#!/usr/bin/env bash
# =============================================================================
# StackDeploy Config Validation
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

FAILED=0

check_file() {
    local file="$1"
    local desc="${2:-$file}"

    if [ -f "$file" ]; then
        info "✅ $desc exists"
        return 0
    else
        error "❌ $desc missing: $file"
        FAILED=1
        return 1
    fi
}

check_env_var() {
    local var="$1"
    local file="${2:-.env}"

    if [ ! -f "$file" ]; then
        error "❌ $file not found"
        FAILED=1
        return 1
    fi

    if grep -q "^${var}=" "$file" 2>/dev/null; then
        local val
        val=$(grep "^${var}=" "$file" | cut -d= -f2-)
        if [ -z "$val" ] || [ "$val" = "REPLACE_WITH_*" ] || [ "$val" = "CHANGEME" ]; then
            warn "⚠️  $var is empty or has placeholder value"
            return 1
        fi
        info "✅ $var is set"
        return 0
    else
        warn "⚠️  $var not found in $file"
        return 1
    fi
}

echo "=========================================="
echo "  StackDeploy Configuration Validation"
echo "=========================================="
echo ""

# Check required files
echo "--- Required Files ---"
check_file "$REPO_ROOT/docker-compose.yml" "docker-compose.yml"
check_file "$REPO_ROOT/.env.example" ".env.example"
check_file "$REPO_ROOT/searxng/settings.yml" "SearXNG settings"
check_file "$REPO_ROOT/scripts/bootstrap.sh" "bootstrap script"
check_file "$REPO_ROOT/scripts/healthcheck.sh" "healthcheck script"

echo ""
echo "--- Environment Configuration ---"
if [ -f "$REPO_ROOT/.env" ]; then
    info "✅ .env file exists"
    check_env_var "HONCHO_DB_PASSWORD" "$REPO_ROOT/.env"
    check_env_var "SERVER_IP" "$REPO_ROOT/.env"
else
    warn "⚠️  .env file not found (run: cp .env.example .env)"
fi

echo ""
echo "--- Docker Compose Validation ---"
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        if docker compose -f "$REPO_ROOT/docker-compose.yml" config -q 2>/dev/null; then
            info "✅ Docker Compose configuration is valid"
        else
            error "❌ Docker Compose configuration has errors"
            FAILED=1
        fi
    else
        warn "⚠️  Docker Compose v2 not available"
    fi
else
    warn "⚠️  Docker not available"
fi

echo ""
echo "--- Secrets Check ---"
if [ -d "$REPO_ROOT/secrets" ]; then
    info "✅ Secrets directory exists"
    for f in "$REPO_ROOT/secrets"/*.txt; do
        if [ -f "$f" ]; then
            local name
            name=$(basename "$f" .txt)
            local size
            size=$(wc -c < "$f")
            if [ "$size" -gt 0 ]; then
                info "  ✅ $name (${size}b)"
            else
                error "  ❌ $name is empty"
                FAILED=1
            fi
        fi
    done
else
    warn "⚠️  Secrets directory not found (run: scripts/manage-secrets.sh init)"
fi

echo ""
echo "--- Monitoring Configuration ---"
check_file "$REPO_ROOT/monitoring/prometheus/prometheus.yml" "Prometheus config"
check_file "$REPO_ROOT/monitoring/prometheus/rules/alerts.yml" "Alert rules"
check_file "$REPO_ROOT/monitoring/grafana/datasources/datasources.yml" "Grafana datasources"
check_file "$REPO_ROOT/monitoring/grafana/dashboards/dashboard.yml" "Grafana dashboard provisioning"
check_file "$REPO_ROOT/monitoring/loki/loki-config.yml" "Loki config"

echo ""
echo "--- Git Configuration ---"
if [ -d "$REPO_ROOT/.git" ]; then
    info "✅ Git repository initialized"

    # Check .gitignore
    if [ -f "$REPO_ROOT/.gitignore" ]; then
        if grep -q "^.env$" "$REPO_ROOT/.gitignore" 2>/dev/null; then
            info "✅ .env is gitignored"
        else
            warn "⚠️  .env not in .gitignore"
        fi
        if grep -q "^secrets/" "$REPO_ROOT/.gitignore" 2>/dev/null; then
            info "✅ secrets/ is gitignored"
        else
            warn "⚠️  secrets/ not in .gitignore"
        fi
    fi
fi

echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    info "✅ All configuration checks passed!"
    exit 0
else
    error "❌ Some configuration checks failed"
    exit 1
fi
