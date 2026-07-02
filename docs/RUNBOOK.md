# =============================================================================
# StackDeploy Runbook — Operational Documentation
# =============================================================================

**Version:** 3.0.0
**Last Updated:** 2025-07-02
**Repository:** https://github.com/JorahOne-Services/StackDeploy

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Service Reference](#2-service-reference)
3. [Deployment](#3-deployment)
4. [Operations](#4-operations)
5. [Monitoring & Alerting](#5-monitoring--alerting)
6. [Backup & Recovery](#6-backup--recovery)
7. [Security Procedures](#7-security-procedures)
8. [Troubleshooting](#8-troubleshooting)
9. [Maintenance](#9-maintenance)
10. [Runbook Automation](#10-runbook-automation)

---

## 1. Architecture Overview

StackDeploy is a Docker Compose-based deployment for AI agent infrastructure. It provides:

- **Search & Browser**: SearXNG (metasearch), Camofox (stealth browser), CloakBrowser (protected sites)
- **Memory & Knowledge**: Honcho (long-term memory API), Qdrant (vector database)
- **Notes & Docs**: Obsidian Remote (web-based vault)
- **Observability**: Prometheus, Grafana, Loki
- **Data Layer**: PostgreSQL (pgvector), Redis

### Network Topology

```
┌─────────────────────────────────────────────────────────┐
│                    stackdeploy-frontend                  │
│  (172.20.0.0/24) — External-facing services              │
│  searxng, camofox, obsidian, cloakbrowser               │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    stackdeploy-backend                   │
│  (172.20.1.0/24) — INTERNAL ONLY                        │
│  qdrant, honcho-db, honcho-redis, honcho, prometheus    │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    stackdeploy-monitoring                │
│  (172.20.2.0/24) — INTERNAL ONLY                        │
│  prometheus, grafana, loki                               │
└─────────────────────────────────────────────────────────┘
```

### Port Mapping

| Service | Port | Bind | Protocol | Purpose |
|---------|------|------|----------|---------|
| SearXNG | 8080 | 127.0.0.1 | HTTP | Metasearch engine |
| Camofox | 9377 | 127.0.0.1 | HTTP | Browser automation API |
| Obsidian | 8083 | 127.0.0.1 | HTTP | Web vault UI |
| Qdrant | 6333 | 127.0.0.1 | HTTP/gRPC | Vector database |
| Honcho | 8081 | 127.0.0.1 | HTTP | Memory API |
| Prometheus | 9090 | 127.0.0.1 | HTTP | Metrics |
| Grafana | 3000 | 127.0.0.1 | HTTP | Dashboards |
| Loki | 3100 | 127.0.0.1 | HTTP | Log aggregation |
| CloakBrowser | 9222 | 127.0.0.1 | HTTP | CDP debugger |

---

## 2. Service Reference

### 2.1 SearXNG

**Purpose:** Privacy-respecting metasearch engine
**Image:** `searxng/searxng:2025.04.1-3e1e2f0e`
**Port:** 8080
**Health Endpoint:** `GET /search?q=healthcheck&format=json`
**Config:** `./searxng/settings.yml`
**Data:** `stackdeploy_searxng_data` volume

**API Usage:**
```bash
# Search
curl 'http://localhost:8080/search?format=json&q=<query>&language=en'

# Health check
curl 'http://localhost:8080/search?q=healthcheck&format=json'
```

**Troubleshooting:**
- Check logs: `docker compose logs searxng`
- Verify settings.yml syntax
- Ensure `searxng-data` volume has correct permissions

### 2.2 Camofox

**Purpose:** Stealth browser automation API for AI agents
**Image:** `ghcr.io/jo-inc/camofox-browser:1.2.0`
**Port:** 9377
**Health Endpoint:** `GET /health`
**Secrets:** `camofox_api_key`, `camofox_admin_key`

**API Usage:**
```bash
# Create a browsing tab
curl -X POST http://localhost:9377/tabs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $(cat secrets/camofox_api_key.txt)" \
  -d '{"userId":"hermes","sessionKey":"default","url":"https://example.com"}'

# Get page snapshot
curl http://localhost:9377/tabs/{tabId}/snapshot?userId=hermes \
  -H "X-API-Key: $(cat secrets/camofox_api_key.txt)"
```

**Troubleshooting:**
- Requires 2GB shared memory (`shm_size: 2g`)
- Check seccomp profile if browser crashes
- Verify API keys match between secrets and service config

### 2.3 Obsidian Remote

**Purpose:** Web-based Obsidian vault access
**Image:** `sytone/obsidian-remote:0.4.2`
**Port:** 8083
**Health Endpoint:** `GET /`
**Data:** Host-mounted vault path (`OBSIDIAN_VAULT_PATH`)

**Usage:**
- Open `http://localhost:8083` in browser
- Vault path configured via `OBSIDIAN_VAULT_PATH` env var

**Troubleshooting:**
- Ensure vault path exists and has correct permissions
- Check `NODE_ENV=production` is set
- Verify `FM_HOME` matches mounted path

### 2.4 Qdrant

**Purpose:** Vector database for similarity search
**Image:** `qdrant/qdrant:v1.13.6`
**Port:** 6333 (REST), 6334 (gRPC)
**Health Endpoint:** `GET /healthz`
**Data:** `stackdeploy_qdrant_data` volume

**API Usage:**
```bash
# List collections
curl http://localhost:6333/collections

# Health check
curl http://localhost:6333/healthz
```

**Troubleshooting:**
- gRPC port 6334 is optional but enabled
- API key can be set via `QDRANT_API_KEY` env var
- Storage path: `/qdrant/storage`

### 2.5 Honcho

**Purpose:** Long-term memory API for AI agents
**Image:** `honcho-repo-api:latest` (build from vendor/honcho)
**Port:** 8081
**Health Endpoint:** `GET /healthz`
**Dependencies:** PostgreSQL (honcho-db), Redis (honcho-redis)

**API Usage:**
```bash
# Health check
curl http://localhost:8081/healthz

# Create memory
curl -X POST http://localhost:8081/api/v1/memory \
  -H "Authorization: Bearer ${HONCHO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"text": "Remember this information"}'
```

**Troubleshooting:**
- Ensure PostgreSQL and Redis are healthy first
- Check `DB_CONNECTION_URI` and `REDIS_URL` env vars
- Log level: `LOG_LEVEL=INFO`, format: `LOG_FORMAT=json`

### 2.6 PostgreSQL (honcho-db)

**Purpose:** Primary database with pgvector extension
**Image:** `pgvector/pgvector:pg17`
**Port:** 5432 (internal only)
**Health:** `pg_isready -U honcho -d honcho`
**Data:** `stackdeploy_honcho_postgres` volume

**Connection:**
```bash
docker compose exec honcho-db psql -U honcho -d honcho
```

### 2.7 Redis (honcho-redis)

**Purpose:** Cache and session store
**Image:** `redis:7.4.2-alpine`
**Port:** 6379 (internal only)
**Health:** `redis-cli ping`
**Data:** `stackdeploy_honcho_redis` volume

**Configuration:**
- Password: `REDIS_PASSWORD` env var
- Max memory: 256MB
- Eviction policy: allkeys-lru
- AOF persistence enabled

### 2.8 Prometheus

**Purpose:** Metrics collection and alerting
**Image:** `prom/prometheus:v2.55.1`
**Port:** 9090
**Health:** `GET /-/ready`
**Data:** `stackdeploy_prometheus_data` volume (30-day retention)
**Config:** `./monitoring/prometheus/prometheus.yml`
**Rules:** `./monitoring/prometheus/rules/alerts.yml`

**Access:** `http://localhost:9090`

### 2.9 Grafana

**Purpose:** Metrics visualization and dashboards
**Image:** `grafana/grafana:11.5.2`
**Port:** 3000
**Health:** `GET /api/health`
**Data:** `stackdeploy_grafana_data` volume
**Default credentials:** admin / admin (change via `GF_SECURITY_ADMIN_PASSWORD`)

**Access:** `http://localhost:3000`

### 2.10 Loki

**Purpose:** Log aggregation
**Image:** `grafana/loki:3.4.2`
**Port:** 3100
**Health:** `GET /ready`
**Data:** `stackdeploy_loki_data` volume (30-day retention)
**Config:** `./monitoring/loki/loki-config.yml`

---

## 3. Deployment

### 3.1 First-Time Deployment

```bash
# 1. Clone and enter
git clone https://github.com/JorahOne-Services/StackDeploy.git
cd StackDeploy

# 2. Initialize secrets
bash scripts/manage-secrets.sh init

# 3. Configure environment
cp .env.example .env
# Edit .env with your specific values

# 4. Validate configuration
bash scripts/validate-config.sh

# 5. Deploy
bash scripts/bootstrap.sh
```

### 3.2 Quick Deploy (bootstrap.sh)

```bash
bash scripts/bootstrap.sh
```

This will:
1. Check Docker and Docker Compose are installed
2. Create `.env` from `.env.example` if missing
3. Pull all Docker images
4. Start all services
5. Run health check

### 3.3 Manual Deploy

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# Run health check
bash scripts/healthcheck.sh localhost
```

### 3.4 CI/CD Deployment

The GitHub Actions pipeline (`.github/workflows/ci-cd.yml`) automatically:
1. Lints code (shellcheck, yamllint, hadolint)
2. Scans for vulnerabilities (Trivy) and secrets
3. Builds all Docker images
4. Runs unit and integration tests
5. Deploys to production on push to master

---

## 4. Operations

### 4.1 Service Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart a single service
docker compose restart <service-name>

# View logs (all services)
docker compose logs -f

# View logs (single service)
docker compose logs -f <service-name>

# View recent logs (last 100 lines)
docker compose logs --tail=100 <service-name>

# Check service status
docker compose ps

# Execute command in running container
docker compose exec <service-name> <command>
```

### 4.2 Health Checks

```bash
# Quick health check
bash scripts/healthcheck.sh localhost

# Detailed health check with Docker
docker compose ps

# Check individual service health
curl http://localhost:8080/search?q=healthcheck&format=json  # SearXNG
curl http://localhost:9377/health                              # Camofox
curl http://localhost:8083/                                    # Obsidian
curl http://localhost:6333/healthz                             # Qdrant
curl http://localhost:8081/healthz                             # Honcho
curl http://localhost:9090/-/ready                              # Prometheus
curl http://localhost:3000/api/health                          # Grafana
curl http://localhost:3100/ready                                # Loki
```

### 4.3 Configuration Validation

```bash
# Validate all configuration
bash scripts/validate-config.sh

# Validate Docker Compose
docker compose config -q

# Check .env variables
bash -c 'source .env && echo "HONCHO_DB_PASSWORD is set: ${HONCHO_DB_PASSWORD:+yes}"'
```

### 4.4 Secrets Management

```bash
# Initialize all secrets
bash scripts/manage-secrets.sh init

# List secrets
bash scripts/manage-secrets.sh list

# Get a secret value
bash scripts/manage-secrets.sh get honcho_db_password

# Rotate a secret
bash scripts/manage-secrets.sh rotate honcho_db_password

# Export secrets as environment variables
bash scripts/manage-secrets.sh export
```

---

## 5. Monitoring & Alerting

### 5.1 Prometheus

**Access:** `http://localhost:9090`

**Pre-built queries:**
```
# Service up status
up

# Container memory usage (MB)
container_memory_usage_bytes{container!=""} / 1048576

# Container CPU usage (%)
rate(container_cpu_usage_seconds_total{container!=""}[5m]) * 100

# Container restarts
rate(container_restarts_seconds_total{container!=""}[15m])
```

**Alert rules** (in `monitoring/prometheus/rules/alerts.yml`):
- `ServiceDown`: Service unreachable for >1 minute
- `HighMemoryUsage`: Memory >85% for >5 minutes
- `HighCPUUsage`: CPU >80% for >5 minutes
- `DiskSpaceLow`: Disk >85% for >10 minutes
- `ContainerRestarts`: Container restarting
- `HealthCheckFailing`: Health check failing for >2 minutes

### 5.2 Grafana

**Access:** `http://localhost:3000` (default: admin/admin)

**Pre-configured dashboards:**
- **StackDeploy Overview**: Service health, memory, CPU, restarts, log volume

**Data sources:**
- Prometheus (default)
- Loki

### 5.3 Loki

**Access:** `http://localhost:3100`

**Log queries:**
```logql
# All logs
{job=~".+"}

# Specific service logs
{container="stackdeploy-searxng"}

# Error logs
{job=~".+"} |= "error"

# Logs in time range
{container="stackdeploy-honcho"} |= "ERROR" != "health"
```

### 5.4 Logging Configuration

All services use structured JSON logging with:
- `json-file` driver
- Max 10MB per file
- 3 rotated files
- Container name, image, and ID tags

---

## 6. Backup & Recovery

### 6.1 Secrets Backup

```bash
# Backup all secrets
tar czf stackdeploy-secrets-$(date +%Y%m%d).tar.gz -C secrets/ .

# Restore secrets
tar xzf stackdeploy-secrets-*.tar.gz -C secrets/
```

### 6.2 Volume Backups

```bash
# Backup all volumes
docker run --rm -v stackdeploy_qdrant_data:/source -v $(pwd)/backups:/backup alpine \
  tar czf /backup/qdrant-$(date +%Y%m%d).tar.gz -C /source .

docker run --rm -v stackdeploy_honcho_postgres:/source -v $(pwd)/backups:/backup alpine \
  tar czf /backup/honcho-postgres-$(date +%Y%m%d).tar.gz -C /source .

docker run --rm -v stackdeploy_honcho_redis:/source -v $(pwd)/backups:/backup alpine \
  tar czf /backup/honcho-redis-$(date +%Y%m%d).tar.gz -C /source .

docker run --rm -v stackdeploy_prometheus_data:/source -v $(pwd)/backups:/backup alpine \
  tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz -C /source .

docker run --rm -v stackdeploy_grafana_data:/source -v $(pwd)/backups:/backup alpine \
  tar czf /backup/grafana-$(date +%Y%m%d).tar.gz -C /source .
```

### 6.3 Database Dump

```bash
# Dump Honcho database
docker compose exec honcho-db pg_dump -U honcho honcho > honcho-db-$(date +%Y%m%d).sql

# Restore Honcho database
cat honcho-db-*.sql | docker compose exec -T honcho-db psql -U honcho honcho
```

### 6.4 Full Stack Recovery

```bash
# 1. Stop all services
docker compose down

# 2. Restore volumes (see section 6.2)

# 3. Restore secrets (see section 6.1)

# 4. Restart
docker compose up -d

# 5. Verify
bash scripts/healthcheck.sh localhost
```

---

## 7. Security Procedures

### 7.1 Container Hardening

All containers implement:
- `no-new-privileges:true` — prevents privilege escalation
- `cap_drop: ALL` — drops all Linux capabilities
- `read_only: true` — read-only root filesystem (where possible)
- `tmpfs: /tmp` — ephemeral temp storage
- Pinned image versions (no `:latest` tags)
- Internal network isolation for backend services

### 7.2 Secrets Management

- All secrets stored in `./secrets/` directory (gitignored)
- Secrets mounted as Docker secrets (not env vars)
- File permissions: 600 (owner read/write only)
- Directory permissions: 750
- Secret rotation via `scripts/manage-secrets.sh rotate`
- Backup secrets directory securely

### 7.3 Network Security

- **Frontend network** (172.20.0.0/24): External-facing services
- **Backend network** (172.20.1.0/24): INTERNAL — databases, caches
- **Monitoring network** (172.20.2.0/24): INTERNAL — observability stack
- All ports bound to `127.0.0.1` (localhost only)
- No public port exposure

### 7.4 Vulnerability Scanning

- Trivy scans in CI/CD pipeline
- Weekly scheduled security scans (Monday 6 AM)
- SARIF results uploaded to GitHub Security tab
- `detect-secrets` checks for accidental secret commits

### 7.5 Incident Response

1. **Service Down**: Check Prometheus alerts → inspect logs → restart service
2. **Security Breach**: Rotate all secrets → audit access → rebuild from clean images
3. **Data Loss**: Restore from backup (see Section 6)
4. **Resource Exhaustion**: Scale resources → check monitoring → optimize config

---

## 8. Troubleshooting

### 8.1 Common Issues

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| Container won't start | Port conflict | Check `netstat -tlnp \| grep <port>` |
| Health check failing | Service not ready | Wait, check logs: `docker compose logs <service>` |
| Camofox crashes | Insufficient SHM | Check `shm_size: 2g` in compose |
| Database connection refused | DB not healthy | Check `docker compose ps`, wait for health |
| Secrets not found | Secrets not initialized | Run `bash scripts/manage-secrets.sh init` |
| Permission denied | Read-only filesystem | Check `read_only: true` and tmpfs mounts |
| Out of disk space | Logs or volumes full | `docker system prune`, check volume sizes |

### 8.2 Diagnostic Commands

```bash
# Full status
docker compose ps

# All logs
docker compose logs --tail=50

# Specific service logs
docker compose logs --tail=100 searxng

# Resource usage
docker stats --no-stream

# Disk usage
docker system df

# Network inspection
docker network inspect stackdeploy_frontend
docker network inspect stackdeploy_backend

# Volume inspection
docker volume inspect stackdeploy_qdrant_data

# Container details
docker inspect stackdeploy-searxng
```

### 8.3 Debug Mode

```bash
# Start with debug logging
docker compose up -d
docker compose logs -f

# Execute shell in container
docker compose exec searxng sh

# Check environment variables
docker compose exec honcho env | grep -E '^(DB_|REDIS_|LOG_)'

# Test network connectivity
docker compose exec honcho ping -c 2 honcho-db
```

---

## 9. Maintenance

### 9.1 Regular Tasks

| Frequency | Task | Command |
|-----------|------|---------|
| Daily | Check health | `bash scripts/healthcheck.sh localhost` |
| Weekly | Review logs | `docker compose logs --tail=200` |
| Weekly | Check disk usage | `docker system df` |
| Monthly | Prune unused resources | `docker system prune -af` |
| Monthly | Update images | `docker compose pull` |
| Monthly | Rotate secrets | `bash scripts/manage-secrets.sh rotate <name>` |
| Quarterly | Full backup | See Section 6 |
| Quarterly | Security audit | Run CI/CD security scan locally |

### 9.2 Updating Services

```bash
# 1. Pull latest images
docker compose pull

# 2. Recreate containers
docker compose up -d --remove-orphans

# 3. Verify
bash scripts/healthcheck.sh localhost
```

### 9.3 Updating Configuration

```bash
# 1. Edit config files
vim searxng/settings.yml
vim monitoring/prometheus/prometheus.yml

# 2. Reload (for services that support it)
docker compose exec prometheus kill -HUP 1

# 3. Or recreate container
docker compose up -d --force-recreate <service>
```

### 9.4 Cleanup

```bash
# Remove unused containers, networks, images
docker system prune -af

# Remove unused volumes (WARNING: destroys data)
docker volume prune -f

# Remove specific old backups
rm -rf backups/*.tar.gz
```

---

## 10. Runbook Automation

### 10.1 Quick Reference

```bash
# Deploy
bash scripts/bootstrap.sh

# Health check
bash scripts/healthcheck.sh localhost

# Validate config
bash scripts/validate-config.sh

# Manage secrets
bash scripts/manage-secrets.sh <command>

# View logs
docker compose logs -f

# Restart all
docker compose restart

# Full stop and cleanup
docker compose down -v
```

### 10.2 Emergency Restart

```bash
# If the stack is unresponsive:
docker compose down --timeout 30
docker compose up -d
sleep 15
bash scripts/healthcheck.sh localhost
```

### 10.3 Rollback

```bash
# Rollback to previous git commit
git log --oneline -5
git reset --hard <previous-commit>
docker compose up -d --force-recreate
bash scripts/healthcheck.sh localhost
```

---

## Appendix A: Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SERVER_IP` | Yes | — | Tailscale/local IP for service URLs |
| `HONCHO_DB_PASSWORD` | Yes | — | PostgreSQL password for Honcho |
| `HONCHO_TOKEN` | No | — | Auth token for Honcho API |
| `CAMOFOX_API_KEY` | No | — | Camofox API authentication key |
| `CAMOFOX_ADMIN_KEY` | No | — | Camofox admin authentication key |
| `OBSIDIAN_VAULT_PATH` | No | `./obsidian-vault` | Host path for Obsidian vault |
| `QDRANT_API_KEY` | No | — | Qdrant API key |
| `REDIS_PASSWORD` | No | — | Redis password |
| `GRAFANA_ADMIN_PASSWORD` | No | `admin` | Grafana admin password |
| `GRAFANA_ADMIN_USER` | No | `admin` | Grafana admin username |

## Appendix B: File Paths

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main service definition |
| `.env.example` | Environment variable template |
| `secrets/*.txt` | Secret files (gitignored) |
| `searxng/settings.yml` | SearXNG configuration |
| `monitoring/prometheus/prometheus.yml` | Prometheus scrape config |
| `monitoring/prometheus/rules/alerts.yml` | Alerting rules |
| `monitoring/grafana/datasources/datasources.yml` | Grafana data sources |
| `monitoring/grafana/dashboards/dashboard.yml` | Dashboard provisioning |
| `monitoring/loki/loki-config.yml` | Loki configuration |
| `scripts/bootstrap.sh` | Deployment script |
| `scripts/healthcheck.sh` | Health check script |
| `scripts/validate-config.sh` | Config validation |
| `scripts/manage-secrets.sh` | Secrets management |
| `tests/unit/*.bats` | Unit tests |
| `tests/integration/*.bats` | Integration tests |

## Appendix C: Docker Compose Overrides

```bash
# With Honcho (build from source)
docker compose -f docker-compose.yml -f docker-compose.honcho.yml up -d

# With Headroom/Aphrodite
docker compose -f docker-compose.yml -f docker-compose.headroom.yml up -d

# All optional services
docker compose -f docker-compose.yml \
  -f docker-compose.honcho.yml \
  -f docker-compose.headroom.yml up -d
```
