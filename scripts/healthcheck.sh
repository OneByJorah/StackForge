#!/usr/bin/env bash
set -euo pipefail

SERVER="${1:-localhost}"
printf "StackForge Healthcheck\nTarget: %s\n\n" "$SERVER"

check_service() {
    local name="$1"
    local url="$2"
    local expected="${3:-}"

    if [[ -n "$expected" ]]; then
        if curl -sf "$url" | grep -q "$expected"; then
            printf "  ✅ %s\n" "$name"
            return 0
        fi
    else
        if curl -sf "$url" >/dev/null; then
            printf "  ✅ %s\n" "$name"
            return 0
        fi
    fi
    printf "  ❌ %s\n" "$name"
    return 1
}

FAILED=0

echo "Core Infrastructure:"
check_service "SearXNG" "http://$SERVER:8080/search?q=healthcheck&format=json" "results" || FAILED=1
check_service "Obsidian Viewer" "http://$SERVER:8083/" "Obsidian" || FAILED=1
check_service "Qdrant" "http://$SERVER:6333/readyz" "ready" || FAILED=1
check_service "Selenium Web Automation" "http://$SERVER:4444/status" "" || FAILED=1

echo ""
echo "Memory Layer:"
check_service "Honcho API" "http://$SERVER:8000/health" "" || FAILED=1

echo ""
echo "Database & Cache:"
check_service "CouchDB" "http://$SERVER:5984/" "" || FAILED=1

echo ""
if [[ $FAILED -eq 0 ]]; then
    echo "🎉 All services healthy!"
    exit 0
else
    echo "⚠️  Some services are down"
    exit 1
fi