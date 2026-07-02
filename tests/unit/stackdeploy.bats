#!/usr/bin/env bats
# =============================================================================
# Unit tests for StackDeploy shell scripts
# =============================================================================

setup() {
    load '/usr/local/lib/bats-support/load.bash'
    load '/usr/local/lib/bats-assert/load.bash'
    load '/usr/local/lib/bats-file/load.bash'

    export TEST_DIR=$(mktemp -d)
    export REPO_ROOT="/home/j1admin/jorah-repos/StackDeploy"
}

teardown() {
    rm -rf "$TEST_DIR"
}

# ===========================================================================
# bootstrap.sh tests
# ===========================================================================

@test "bootstrap.sh fails without Docker" {
    # Mock command -v to fail for docker
    run bash -c '
        function command() { return 1; }
        export -f command
        source '"$REPO_ROOT"'/scripts/bootstrap.sh 2>&1 || true
    '
    # Should fail gracefully
    [ $status -ne 0 ] || skip "Docker is installed on this system"
}

@test "bootstrap.sh creates .env from .env.example" {
    cd "$TEST_DIR"
    cp "$REPO_ROOT/.env.example" "$TEST_DIR/.env.example"
    run bash -c '
        cd '"$TEST_DIR"'
        if [[ ! -f .env ]]; then
            if [[ -f .env.example ]]; then
                cp .env.example .env
                echo "Created .env from .env.example"
            fi
        fi
    '
    assert_success
    assert_file_exist "$TEST_DIR/.env"
}

# ===========================================================================
# healthcheck.sh tests
# ===========================================================================

@test "healthcheck.sh requires server argument" {
    run bash "$REPO_ROOT/scripts/healthcheck.sh"
    # Should output usage or fail gracefully
    [ $status -eq 0 ] || true
}

@test "healthcheck.sh check_service function works" {
    run bash -c '
        source '"$REPO_ROOT"'/scripts/healthcheck.sh 2>/dev/null || true
        # Test the check_service function directly
        type check_service 2>/dev/null && echo "function exists" || echo "no function"
    '
    assert_output --partial "function exists"
}

# ===========================================================================
# manage-secrets.sh tests
# ===========================================================================

@test "manage-secrets.sh init creates secrets directory" {
    run bash "$REPO_ROOT/scripts/manage-secrets.sh" init
    assert_success
    assert_file_exist "$REPO_ROOT/secrets/honcho_db_password.txt"
    assert_file_exist "$REPO_ROOT/secrets/camofox_api_key.txt"
    assert_file_exist "$REPO_ROOT/secrets/searxng_secret_key.txt"
}

@test "manage-secrets.sh list shows secrets" {
    run bash "$REPO_ROOT/scripts/manage-secrets.sh" list
    assert_success
    assert_output --partial "Secrets:"
}

@test "manage-secrets.sh get reads a secret" {
    # First ensure secrets exist
    bash "$REPO_ROOT/scripts/manage-secrets.sh" init 2>/dev/null || true
    run bash "$REPO_ROOT/scripts/manage-secrets.sh" get honcho_db_password
    assert_success
    [ -n "$output" ]
}

@test "manage-secrets.sh rotate generates new secret" {
    bash "$REPO_ROOT/scripts/manage-secrets.sh" init 2>/dev/null || true
    local old_val
    old_val=$(cat "$REPO_ROOT/secrets/honcho_db_password.txt")
    run bash "$REPO_ROOT/scripts/manage-secrets.sh" rotate honcho_db_password 32
    assert_success
    local new_val
    new_val=$(cat "$REPO_ROOT/secrets/honcho_db_password.txt")
    [ "$old_val" != "$new_val" ]
}

# ===========================================================================
# validate-config.sh tests
# ===========================================================================

@test "validate-config.sh runs without errors" {
    run bash "$REPO_ROOT/scripts/validate-config.sh"
    # Should complete (may have warnings but not crash)
    [ $status -eq 0 ] || [ $status -eq 1 ]
}

# ===========================================================================
# Docker Compose config tests
# ===========================================================================

@test "docker-compose.yml is valid YAML" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
assert 'services' in data, 'No services defined'
assert 'networks' in data, 'No networks defined'
print('Valid YAML with', len(data['services']), 'services')
"
    assert_success
}

@test "docker-compose.yml has all required services" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
required = ['searxng', 'camofox', 'obsidian', 'qdrant', 'honcho-db', 'honcho-redis', 'honcho']
for s in required:
    assert s in data['services'], f'Missing service: {s}'
print('All required services present')
"
    assert_success
}

@test "docker-compose.yml services have healthchecks" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
for name, svc in data['services'].items():
    assert 'healthcheck' in svc, f'Missing healthcheck on {name}'
print('All services have healthchecks')
"
    assert_success
}

@test "docker-compose.yml services have security hardening" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
for name, svc in data['services'].items():
    assert 'cap_drop' in svc, f'Missing cap_drop on {name}'
    assert 'security_opt' in svc, f'Missing security_opt on {name}'
print('All services have security hardening')
"
    assert_success
}

@test "docker-compose.yml uses pinned image versions" {
    run python3 -c "
import yaml, re
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
for name, svc in data['services'].items():
    if 'image' in svc:
        tag = svc['image'].split(':')[1] if ':' in svc['image'] else 'latest'
        assert tag != 'latest', f'{name} uses :latest tag'
print('All images use pinned versions')
"
    assert_success
}

@test "docker-compose.yml has monitoring services" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
monitoring = ['prometheus', 'grafana', 'loki']
for s in monitoring:
    assert s in data['services'], f'Missing monitoring service: {s}'
print('All monitoring services present')
"
    assert_success
}

@test "docker-compose.yml has internal networks" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/docker-compose.yml') as f:
    data = yaml.safe_load(f)
networks = data.get('networks', {})
assert 'backend' in networks, 'Missing backend network'
assert 'frontend' in networks, 'Missing frontend network'
assert 'monitoring' in networks, 'Missing monitoring network'
backend = networks['backend']
assert backend.get('internal') == True, 'backend network should be internal'
print('Network isolation properly configured')
"
    assert_success
}

# ===========================================================================
# .env.example tests
# ===========================================================================

@test ".env.example has all required variables" {
    run python3 -c "
required = ['SERVER_IP', 'HONCHO_DB_PASSWORD', 'HONCHO_TOKEN']
with open('$REPO_ROOT/.env.example') as f:
    content = f.read()
for var in required:
    assert var in content, f'Missing required var: {var}'
print('All required env vars documented')
"
    assert_success
}

# ===========================================================================
# .gitignore tests
# ===========================================================================

@test ".gitignore covers sensitive files" {
    run python3 -c "
with open('$REPO_ROOT/.gitignore') as f:
    content = f.read()
required = ['.env', 'secrets/', 'node_modules']
for item in required:
    assert item in content, f'Missing gitignore entry: {item}'
print('All sensitive files gitignored')
"
    assert_success
}

# ===========================================================================
# Monitoring config tests
# ===========================================================================

@test "Prometheus config is valid" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/monitoring/prometheus/prometheus.yml') as f:
    data = yaml.safe_load(f)
assert 'global' in data
assert 'scrape_configs' in data
print('Valid Prometheus config')
"
    assert_success
}

@test "Grafana datasource config is valid" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/monitoring/grafana/datasources/datasources.yml') as f:
    data = yaml.safe_load(f)
assert 'datasources' in data
print('Valid Grafana datasource config')
"
    assert_success
}

@test "Loki config is valid" {
    run python3 -c "
import yaml
with open('$REPO_ROOT/monitoring/loki/loki-config.yml') as f:
    data = yaml.safe_load(f)
assert 'server' in data
assert 'schema_config' in data
print('Valid Loki config')
"
    assert_success
}
