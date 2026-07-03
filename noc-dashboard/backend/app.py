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
from fastapi.responses import FileResponse, JSONResponse
from fastapi.static import StaticFiles


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


HISTORY_LEN = 20

SERVICES = [
    {"id": "searxng", "name": "SearXNG", "host": "searxng", "port": 8080, "public_port": 8080,
     "kind": "http", "path": "/search?q=healthcheck&format=json", "group": "Search & Browser"},
    {"id": "camofox", "name": "Camofox", "host": "camofox-browser", "port": 9377, "public_port": 9377,
     "kind": "http", "path": "/health", "group": "Search & Browser"},
    {"id": "cloakbrowser", "name": "CloakBrowser", "host": "cloak-browser", "port": 9222, "public_port": 9222,
     "kind": "http", "path": "/json/version", "group": "Search & Browser"},
    {"id": "obsidian", "name": "Obsidian Remote", "host": "obsidian", "port": 8080, "public_port": 8083,
     "kind": "http", "path": "/", "group": "Notes & Docs"},
    {"id": "qdrant", "name": "Qdrant", "host": "qdrant", "port": 6333, "public_port": 6333,
     "kind": "http", "path": "/readyz", "group": "Memory & Knowledge"},
    {"id": "honcho", "name": "Honcho API", "host": "honcho", "port": 8081, "public_port": 8081,
     "kind": "http", "path": "/healthz", "group": "Memory & Knowledge"},
    {"id": "honcho-db", "name": "Honcho DB (Postgres)", "host": "honcho-db", "port": 5432, "public_port": None,
     "kind": "tcp", "group": "Memory & Knowledge"},
    {"id": "honcho-redis", "name": "Honcho Redis", "host": "honcho-redis", "port": 6379, "public_port": None,
     "kind": "tcp", "group": "Memory & Knowledge"},
    {"id": "ollama", "name": "Ollama Cloud", "host": "ollama", "port": 11434, "public_port": 11434,
     "kind": "http", "path": "/api/tags", "group": "Inference"},
]

if env_bool("ENABLE_HEADROOM_MONITORING", True):
    SERVICES += [
        {"id": "headroom-proxy", "name": "Headroom Proxy", "host": "headroom-proxy", "port": 8787, "public_port": 8787,
         "kind": "http", "path": "/readyz", "group": "Headroom"},
        {"id": "headroom-qdrant", "name": "Headroom Qdrant", "host": "headroom-qdrant", "port": 5333, "public_port": 5333,
         "kind": "http", "path": "/healthz", "group": "Headroom"},
        {"id": "headroom-neo4j", "name": "Headroom Neo4j", "host": "headroom-neo4j", "port": 7474, "public_port": 7474,
         "kind": "http", "path": "/", "group": "Headroom"},
    ]

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


app = FastAPI(title="J1-NOC StackDeploy Dashboard", lifespan=lifespan)


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
