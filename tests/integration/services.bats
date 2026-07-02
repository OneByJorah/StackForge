#!/usr/bin/env bats
# =============================================================================
# Integration tests for StackDeploy
# =============================================================================

setup() {
    load '/usr/local/lib/bats-support/load.bash'
    load '/usr/local/lib/bats-assert/load.bash'
    export REPO_ROOT="/home/j1admin/jorah-repos/StackDeploy"
}

# ===========================================================================
# Service endpoint tests
# ===========================================================================

@test "SearXNG responds on port 8080" {
    run curl -sf -o /dev/null -w '%{http_code}' 'http://localhost:8080/search?format=json&q=test'
    assert_success
    [ "$output" = "200" ]
}

@test "SearXNG returns JSON results" {
    run curl -sf 'http://localhost:8080/search?format=json&q=python&language=en'
    assert_success
    echo "$output" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert 'results' in data, 'No results in response'
print(f'Got {len(data[\"results\"])} results')
"
}

@test "Camofox health endpoint responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:9377/health
    assert_success
    [ "$output" = "200" ]
}

@test "Obsidian web UI responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:8083/
    assert_success
    [ "$output" = "200" ]
}

@test "Qdrant health endpoint responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:6333/healthz
    assert_success
    [ "$output" = "200" ]
}

@test "Honcho API health endpoint responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:8081/healthz
    assert_success
    [ "$output" = "200" ]
}

@test "Prometheus metrics endpoint responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:9090/-/ready
    assert_success
    [ "$output" = "200" ]
}

@test "Grafana health endpoint responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:3000/api/health
    assert_success
    [ "$output" = "200" ]
}

@test "Loki ready endpoint responds" {
    run curl -sf -o /dev/null -w '%{http_code}' http://localhost:3100/ready
    assert_success
    [ "$output" = "200" ]
}

# ===========================================================================
# Docker container tests
# ===========================================================================

@test "All containers are running" {
    run docker compose ps --format json
    assert_success
    echo "$output" | python3 -c "
import json, sys
containers = [json.loads(l) for l in sys.stdin if l.strip()]
running = [c for c in containers if c.get('State') == 'running']
print(f'{len(running)}/{len(containers)} containers running')
assert len(running) == len(containers), 'Not all containers are running'
"
}

@test "No containers restarting" {
    run docker compose ps --format json
    assert_success
    echo "$output" | python3 -c "
import json, sys
containers = [json.loads(l) for l in sys.stdin if l.strip()]
restarting = [c for c in containers if c.get('Status', '').startswith('restarting')]
assert len(restarting) == 0, f'{len(restarting)} containers restarting'
print('No containers restarting')
"
}

# ===========================================================================
# Network tests
# ===========================================================================

@test "Services are on correct networks" {
    run docker compose ps --format json
    assert_success
    echo "$output" | python3 -c "
import json, sys
containers = [json.loads(l) for l in sys.stdin if l.strip()]
for c in containers:
    name = c.get('Name', '')
    networks = c.get('Networks', '')
    print(f'{name}: {networks}')
"
}

# ===========================================================================
# Volume tests
# ===========================================================================

@test "Required volumes exist" {
    run docker volume ls --format '{{.Name}}'
    assert_success
    for vol in stackdeploy_searxng_data stackdeploy_qdrant_data stackdeploy_honcho_postgres stackdeploy_honcho_redis; do
        echo "$output" | grep -q "$vol" && echo "✅ $vol exists" || echo "⚠️  $vol not found"
    done
}

# ===========================================================================
# End-to-end workflow tests
# ===========================================================================

@test "Healthcheck script passes" {
    run bash "$REPO_ROOT/scripts/healthcheck.sh" localhost
    assert_success
    assert_output --partial "All services healthy"
}

@test "Config validation passes" {
    run bash "$REPO_ROOT/scripts/validate-config.sh"
    assert_success
    assert_output --partial "All configuration checks passed"
}
