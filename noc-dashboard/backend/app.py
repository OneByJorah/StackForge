"""
J1-NOC Dashboard — StackDeploy monitoring backend.

Polls every service in StackDeploy over the internal Docker network using
the SAME health endpoints defined in docker-compose.yml / scripts/healthcheck.sh,
plus optional Portainer container stats if PORTAINER_URL is set.

This dashboard is READ-ONLY monitoring. It does not proxy traffic — every
service still exposes its own port/API directly, exactly as before.
"""
import asyncio
import os
import socket
import time
from collections import deque
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.static import StaticFiles


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_override_host(svc_id: str) -> str | None:
    val = os.getenv(f"SVC_{svc_id.upper().replace('-', '_')}_HOST")
    return val.strip() if val else None


def env_override_port(svc_id: str) -> int | None:
    val = os.getenv(f"SVC_{svc_id.upper().replace('-', '_')}_PORT")
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


HISTORY_LEN = 20

# Same services as docker-compose, with optional per-service host/port overrides:
#   SVC_<ID>_HOST / SVC_<ID>_PORT   (e.g. SVC_SEARXNG_HOST, SVC_QDRANT_PORT)
SERVICES = [
    {"id": "searxng", "name": "SearXNG", "host": "localhost", "port": 8080, "public_port": 8080,
     "kind": "http", "path": "/search?q=healthcheck&format=json", "group": "Search & Browser"},
    {"id": "camofox", "name": "Camofox", "host": "localhost", "port": 9377, "public_port": 9377,
     "kind": "http", "path": "/health", "group": "Search & Browser"},
    {"id": "cloakbrowser", "name": "CloakBrowser", "host": "localhost", "port": 9222, "public_port": 9222,
     "kind": "http", "path": "/json/version", "group": "Search & Browser"},
    {"id": "obsidian", "name": "Obsidian Remote", "host": "localhost", "port": 8080, "public_port": 8083,
     "kind": "http", "path": "/", "group": "Notes & Docs"},
    {"id": "qdrant", "name": "Qdrant", "host": "localhost", "port": 6333, "public_port": 6333,
     "kind": "http", "path": "/readyz", "group": "Memory & Knowledge"},
    {"id": "honcho", "name": "Honcho API", "host": "localhost", "port": 8081, "public_port": 8081,
     "kind": "http", "path": "/healthz", "group": "Memory & Knowledge"},
    {"id": "honcho-db", "name": "Honcho DB (Postgres)", "host": "localhost", "port": 5432, "public_port": None,
     "kind": "tcp", "group": "Memory & Knowledge"},
    {"id": "honcho-redis", "name": "Honcho Redis", "host": "localhost", "port": 6379, "public_port": None,
     "kind": "tcp", "group": "Memory & Knowledge"},
    {"id": "ollama", "name": "Ollama Cloud", "host": "localhost", "port": 11434, "public_port": 11434,
     "kind": "http", "path": "/api/tags", "group": "Inference"},
]

if env_bool("ENABLE_HEADROOM_MONITORING", True):
    SERVICES += [
        {"id": "headroom-proxy", "name": "Headroom Proxy", "host": "localhost", "port": 8787, "public_port": 8787,
         "kind": "http", "path": "/readyz", "group": "Headroom"},
        {"id": "headroom-qdrant", "name": "Headroom Qdrant", "host": "localhost", "port": 5333, "public_port": 5333,
         "kind": "http", "path": "/healthz", "group": "Headroom"},
        {"id": "headroom-neo4j", "name": "Headroom Neo4j", "host": "localhost", "port": 7474, "public_port": 7474,
         "kind": "http", "path": "/", "group": "Headroom"},
    ]


for svc in SERVICES:
    host_override = env_override_host(svc["id"])
    port_override = env_override_port(svc["id"])
    if host_override:
        svc["host"] = host_override
    if port_override:
        svc["port"] = port_override

PORTAINER_URL = os.getenv("PORTAINER_URL", "").rstrip("/")
PORTAINER_API_KEY = os.getenv("PORTAINER_API_KEY", "")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL_SECONDS", "10"))

state = {
    "services": {},
    "history": {s["id"]: deque(maxlen=HISTORY_LEN) for s in SERVICES},
    "last_run": None,
}


async def check_http(client: httpx.AsyncClient, svc: dict) -> dict:
    url = f"http://{svc['host']}:{svc['port']}{svc.get('path', '/')}"
    start = time.perf_counter()
    try:
        r = await client.get(url, timeout=5.0)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        up = r.status_code < 500
        return {"up": up, "latency_ms": latency_ms, "code": r.status_code}
    except Exception as exc:
        return {"up": False, "latency_ms": None, "error": str(exc)[:120]}


async def check_tcp(svc: dict) -> dict:
    start = time.perf_counter()
    try:
        fut = asyncio.open_connection(svc["host"], svc["port"])
        reader, writer = await asyncio.wait_for(fut, timeout=5.0)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return {"up": True, "latency_ms": latency_ms}
    except Exception as exc:
        return {"up": False, "latency_ms": None, "error": str(exc)[:120]}


async def check_portainer() -> list:
    if not PORTAINER_URL:
        return []
    headers = {"X-API-Key": PORTAINER_API_KEY} if PORTAINER_API_KEY else {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{PORTAINER_URL}/api/endpoints/1/docker/containers/json",
                                 headers=headers, params={"all": "true"})
            r.raise_for_status()
            data = r.json()
            return [
                {
                    "name": c.get("Names", ["?"])[0].lstrip("/"),
                    "state": c.get("State"),
                    "status": c.get("Status"),
                    "image": c.get("Image"),
                }
                for c in data
            ]
    except Exception as exc:
        return [{"error": str(exc)[:200]}]


async def poll_once():
    async with httpx.AsyncClient() as client:
        results = {}
        tasks = []
        for svc in SERVICES:
            if svc["kind"] == "http":
                tasks.append(check_http(client, svc))
            else:
                tasks.append(check_tcp(svc))
        outcomes = await asyncio.gather(*tasks, return_exceptions=False)

    now = time.time()
    for svc, outcome in zip(SERVICES, outcomes):
        results[svc["id"]] = {
            **svc,
            **outcome,
            "checked_at": now,
        }
        state["history"][svc["id"]].append({
            "t": now,
            "up": outcome["up"],
            "latency_ms": outcome.get("latency_ms"),
        })

    results["_portainer"] = await check_portainer()
    state["services"] = results
    state["last_run"] = now


async def poll_loop():
    while True:
        try:
            await poll_once()
        except Exception:
            pass
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()


TAILSCALE_IP = os.getenv("TAILSCALE_IP", "YOUR_SERVER_IP")

app = FastAPI(title="J1-NOC StackDeploy Dashboard", lifespan=lifespan)

# ── Self-hosted API registry ──────────────────────────────────────────────────
# This is the catalog that other Hermes agents on Tailscale query to discover
# every local service with one curl command.
SERVICE_REGISTRY = {
    "searxng": {
        "name": "SearXNG",
        "description": "Privacy-respecting metasearch engine. Use as web_search provider.",
        "tailscale_url": f"http://{TAILSCALE_IP}:8080",
        "internal_url": "http://localhost:8080",
        "api_docs": "http://localhost:8080/search?format=json",
        "group": "Search & Browser",
        "hermes_usage": {
            "env_var": "SEARXNG_URL=http://YOUR_SERVER_IP:8080",
            "config": "Hermes can use SearXNG as an internal tool when configured.",
            "notes": "Supports POST /search with q=query&format=json"
        }
    },
    "qdrant": {
        "name": "Qdrant",
        "description": "Vector search engine for semantic memory and RAG.",
        "tailscale_url": f"http://{TAILSCALE_IP}:6333",
        "internal_url": "http://localhost:6333",
        "api_docs": "http://localhost:6333/docs",
        "group": "Memory & Knowledge",
        "hermes_usage": {
            "env_var": "QDRANT_URL=http://YOUR_SERVER_IP:6333",
            "config": "Set QDRANT_HOST and QDRANT_PORT. Qdrant's REST API is at /collections.",
            "notes": "v1.18.2. Full REST API with Swagger at /docs."
        }
    },
    "redis": {
        "name": "Redis",
        "description": "In-memory key-value store. Cache, session, and pub/sub.",
        "tailscale_url": f"redis://{TAILSCALE_IP}:6379",
        "internal_url": "redis://localhost:6379",
        "api_docs": None,
        "group": "Memory & Knowledge",
        "hermes_usage": {
            "env_var": "REDIS_URL=redis://YOUR_SERVER_IP:6379",
            "config": "Standard REDIS_URL env var. No auth configured.",
            "notes": "TCP protocol. Use redis-py or redis-cli."
        }
    },
    "postgresql": {
        "name": "PostgreSQL",
        "description": "Relational database. Agent memory store, session storage, app backends.",
        "tailscale_url": f"postgresql://postgres@YOUR_SERVER_IP:5432/postgres",
        "internal_url": "postgresql://postgres@localhost:5432/postgres",
        "api_docs": None,
        "group": "Memory & Knowledge",
        "hermes_usage": {
            "env_var": "DATABASE_URL=postgresql://postgres@YOUR_SERVER_IP:5432/postgres",
            "config": "Set PGUSER/PGPASSWORD in .env. Honcho uses this as its memory backend.",
            "notes": "Port 5432. TCP protocol. Also serves Honcho."
        }
    },
    "ollama": {
        "name": "Ollama",
        "description": "Local LLM inference. Run models without cloud APIs.",
        "tailscale_url": f"http://{TAILSCALE_IP}:11434",
        "internal_url": "http://localhost:11434",
        "api_docs": "http://localhost:11434",
        "group": "Inference",
        "hermes_usage": {
            "env_var": "OLLAMA_HOST=http://YOUR_SERVER_IP:11434",
            "config": "Set model.base_url=http://YOUR_SERVER_IP:11434 and provider=custom:ollama with model ollama/<name>.",
            "notes": "OpenAI-compatible API at /v1/. Models: currently none loaded. Use 'ollama pull <model>'."
        }
    },
    "mission_control": {
        "name": "Mission Control Dashboard",
        "description": "Hermes agent dashboard with kanban board, agent status, 3D office, and cron management.",
        "tailscale_url": f"http://{TAILSCALE_IP}:51763",
        "internal_url": "http://localhost:51763",
        "api_docs": "http://localhost:51763/api/snapshot",
        "group": "Dashboards & Ops",
        "hermes_usage": {
            "env_var": "MISSION_CONTROL_URL=http://YOUR_SERVER_IP:51763",
            "config": "SSE streaming at /api/snapshot. Board API at /api/board. Content at /api/content.",
            "notes": "Python HTTPServer. Poll /api/snapshot for live state."
        }
    },
    "noc_dashboard": {
        "name": "NOC Dashboard",
        "description": "StackDeploy health monitor showing service uptime, Tailscale map, and DERP relays.",
        "tailscale_url": f"http://{TAILSCALE_IP}:9500",
        "internal_url": "http://localhost:9500",
        "api_docs": "http://localhost:9500/api/status",
        "group": "Dashboards & Ops",
        "hermes_usage": {
            "env_var": "NOC_URL=http://YOUR_SERVER_IP:9500",
            "config": "FastAPI. Live service health at /api/status.",
            "notes": "Period 10s poll. Service history available at /api/status."
        }
    }
}


@app.get("/api/services.json")
async def api_services():
    """Agent-facing registry of every self-hosted service on this Tailscale node.
    
    Other Hermes agents call http://YOUR_SERVER_IP:9500/api/services.json to discover
    all available local APIs with one curl command.
    """
    return JSONResponse({
        "node": TAILSCALE_IP,
        "node_name": "YOUR_SERVER_HOST",
        "tailnet": "YOUR_TAILNET_NAME",
        "generated_at": time.time(),
        "services": SERVICE_REGISTRY,
        "hermes_setup_command": (
            f"source <(curl -s http://{TAILSCALE_IP}:9500/api/services.sh)"
        )
    })


@app.get("/api/services.sh")
async def api_services_sh():
    """Shell script snippet — source from any Hermes agent on Tailscale to set env vars."""
    lines = ["#!/bin/bash",
             f"# J1-NOC self-hosted API registry — sourced from http://{TAILSCALE_IP}:9500/api/services.sh",
             "# Run:  source <(curl -s http://YOUR_SERVER_IP:9500/api/services.sh)",
             "",
             f"export TAILSCALE_MSCONTROL={TAILSCALE_IP}",
             "",
             "# ── Search & Browser ──",
             "export SEARXNG_URL=http://YOUR_SERVER_IP:8080",
             "",
             "# ── Memory & Knowledge ──",
             "export QDRANT_URL=http://YOUR_SERVER_IP:6333",
             "export REDIS_URL=redis://YOUR_SERVER_IP:6379",
             "export DATABASE_URL=postgresql://postgres@YOUR_SERVER_IP:5432/postgres",
             "",
             "# ── Inference ──",
             "export OLLAMA_HOST=http://YOUR_SERVER_IP:11434",
             "export OLLAMA_BASE_URL=http://YOUR_SERVER_IP:11434",
             "",
             "# ── Dashboards ──",
             "export MISSION_CONTROL_URL=http://YOUR_SERVER_IP:51763",
             "export NOC_URL=http://YOUR_SERVER_IP:9500",
             "",
             "# ── Ansible-style inventory (machine-readable) ──",
             "export J1_NOC_HOST=YOUR_SERVER_IP",
             "export J1_NOC_NODE=YOUR_SERVER_HOST",
             "export J1_NOC_TAILNET=YOUR_TAILNET_NAME",
             "",
             "echo '[J1-NOC Registry] Services loaded:'",
             "echo '  Search:    SearXNG     → $SEARXNG_URL'",
             "echo '  Vectors:   Qdrant      → $QDRANT_URL'",
             "echo '  Cache:     Redis       → $REDIS_URL'",
             "echo '  Database:  PostgreSQL  → $DATABASE_URL'",
             "echo '  Inference: Ollama      → $OLLAMA_HOST'",
             "echo '  Dashboard: Mission Ctrl→ $MISSION_CONTROL_URL'",
             "echo '  Dashboard: NOC         → $NOC_URL'",
             "echo",
             'echo "One-command agent setup: hermes config set model.base_url $OLLAMA_HOST"',
             ""]
    return PlainTextResponse("\n".join(lines), media_type="text/x-shellscript")


@app.get("/api/status")
async def api_status():
    services = {k: v for k, v in state["services"].items() if k != "_portainer"}
    history = {k: list(v) for k, v in state["history"].items()}
    return JSONResponse({
        "last_run": state["last_run"],
        "poll_interval": POLL_INTERVAL,
        "services": services,
        "history": history,
        "portainer": {
            "configured": bool(PORTAINER_URL),
            "containers": state["services"].get("_portainer", []),
        },
        "prod": {
            "configured": True,
            "ollama_host": os.getenv("OLLAMA_HOST", "ollama"),
            "ollama_port": int(os.getenv("OLLAMA_PORT", "11434")),
            "prod_hosts": os.getenv("PROD_HOSTS", ""),
        }
    })


@app.get("/api/healthz")
async def healthz():
    return {"ok": True}


app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")
