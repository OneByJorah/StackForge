"""
J1-NOC Dashboard — Standalone version (no Docker required).
Mounts static files from local frontend/ dir and adds localhost fallback
for services so health checks work even without Docker network.
"""
import asyncio
import json
import os
import uuid
import subprocess
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

# DERP relay geo coordinates (relay → nearest real datacenter)
TAILSCALE_RELAY_GEO = {
    "mia": (25.7617, -80.1918, "Miami, USA"),
    "lax": (33.9425, -118.4082, "Los Angeles, USA"),
    "sfo": (37.7749, -122.4194, "San Francisco, USA"),
    "dfw": (32.7793, -96.8213, "Dallas, USA"),
    "ewr": (40.7357, -74.1724, "Newark, USA"),
    "iad": (38.9531, -77.4565, "Ashburn, USA"),
    "lhr": (51.5074, -0.1278, "London, UK"),
    "fra": (50.1109, 8.6821, "Frankfurt, DE"),
    "ams": (52.3676, 4.9041, "Amsterdam, NL"),
    "sin": (1.3521, 103.8198, "Singapore"),
    "hkg": (22.3193, 114.1694, "Hong Kong"),
    "tyo": (35.6762, 139.6503, "Tokyo, JP"),
    "syd": (-33.8688, 151.2093, "Sydney, AU"),
    "jfk": (40.6413, -73.7781, "New York, USA"),
    "sea": (47.6062, -122.3321, "Seattle, USA"),
    "den": (39.7392, -104.9903, "Denver, USA"),
    "ord": (41.9742, -87.9073, "Chicago, USA"),
    "atl": (33.6407, -84.4277, "Atlanta, USA"),
    "bog": (4.7110, -74.0721, "Bogotá, CO"),
    "gru": (-23.4356, -46.4731, "São Paulo, BR"),
}

_ts_cache = {"ts": 0, "data": []}

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
BASE_DIR = Path(__file__).parent.resolve()

# Services, with optional per-service host/port overrides:
#   SVC_<ID>_HOST / SVC_<ID>_PORT   (e.g. SVC_SEARXNG_HOST, SVC_QDRANT_PORT)
DEFAULT_SERVICES = [
    # --- Core published stack (tracked, counts toward SLO) ---
    {"id": "searxng", "name": "SearXNG", "host": "localhost", "port": 8080, "public_port": 8080,
     "kind": "http", "path": "/search?q=healthcheck&format=json", "group": "Search & Browser"},
    {"id": "obsidian", "name": "Obsidian Remote", "host": "localhost", "port": 8080, "public_port": 8083,
     "kind": "http", "path": "/", "group": "Notes & Docs"},
    {"id": "obsidian-wallpaper", "name": "Obsidian Live Wallpaper", "host": "YOUR_SERVER_IP", "port": 3000, "public_port": 3000,
     "kind": "http", "path": "/", "group": "Notes & Docs", "optional": True},
    {"id": "couchdb", "name": "CouchDB (LiveSync)", "host": "localhost", "port": 5984, "public_port": 5984,
     "kind": "tcp", "group": "Notes & Docs"},
    {"id": "qdrant", "name": "Qdrant", "host": "localhost", "port": 6333, "public_port": 6333,
     "kind": "http", "path": "/readyz", "group": "Memory & Knowledge"},
    {"id": "honcho", "name": "Honcho API", "host": "localhost", "port": 8000, "public_port": 8000,
     "kind": "http", "path": "/healthz", "group": "Memory & Knowledge"},
    {"id": "ollama", "name": "Ollama Cloud", "host": "localhost", "port": 11434, "public_port": 11434,
     "kind": "http", "path": "/api/tags", "group": "Inference"},
    {"id": "mission-control", "name": "Mission Control", "host": "localhost", "port": 51763, "public_port": 51763,
     "kind": "http", "path": "/", "group": "Dashboards"},
    {"id": "hs-bridge", "name": "Hermes Hub · Bridge", "host": "YOUR_SERVER_IP", "port": 18000, "public_port": 18000,
     "kind": "http", "path": "/health", "group": "Hermes Satellite"},
    {"id": "hs-ears", "name": "Hermes Hub · Ears (STT)", "host": "YOUR_SERVER_IP", "port": 9000, "public_port": 9000,
     "kind": "http", "path": "/health", "group": "Hermes Satellite"},
    {"id": "hs-mouth", "name": "Hermes Hub · Mouth (TTS)", "host": "YOUR_SERVER_IP", "port": 9001, "public_port": 9001,
     "kind": "http", "path": "/health", "group": "Hermes Satellite"},

    # --- Optional / standby infrastructure (excluded from SLO) ---
    {"id": "honcho-db", "name": "Honcho DB (Postgres)", "host": "localhost", "port": 5432, "public_port": None,
     "kind": "tcp", "group": "Memory & Knowledge", "optional": True},
    {"id": "honcho-redis", "name": "Honcho Redis", "host": "localhost", "port": 6379, "public_port": None,
     "kind": "tcp", "group": "Memory & Knowledge", "optional": True},
    {"id": "camofox", "name": "Camofox", "host": "localhost", "port": 9377, "public_port": 9377,
     "kind": "http", "path": "/health", "group": "Search & Browser", "optional": True},
    {"id": "cloakbrowser", "name": "CloakBrowser", "host": "localhost", "port": 9222, "public_port": 9222,
     "kind": "http", "path": "/json/version", "group": "Search & Browser", "optional": True},
]

SERVICES = []
TS_IP = os.getenv("TAILSCALE_IP", "YOUR_SERVER_IP")
for svc in DEFAULT_SERVICES:
    host_override = env_override_host(svc["id"])
    port_override = env_override_port(svc["id"])
    resolved_host = (host_override or svc["host"]).replace("YOUR_SERVER_IP", TS_IP)
    is_optional = svc.get("optional", False) or str(resolved_host).startswith("YOUR_")
    SERVICES.append({
        **svc,
        "host": resolved_host,
        "port": port_override or svc["port"],
        "optional": is_optional,
    })

if env_bool("ENABLE_HEADROOM_MONITORING", False):
    SERVICES += [
        {"id": "headroom-proxy", "name": "Headroom Proxy", "host": "localhost", "port": 8787, "public_port": 8787,
         "kind": "http", "path": "/readyz", "group": "Headroom"},
        {"id": "headroom-qdrant", "name": "Headroom Qdrant", "host": "localhost", "port": 5333, "public_port": 5333,
         "kind": "http", "path": "/healthz", "group": "Headroom"},
        {"id": "headroom-neo4j", "name": "Headroom Neo4j", "host": "localhost", "port": 7474, "public_port": 7474,
         "kind": "http", "path": "/", "group": "Headroom"},
    ]

PORTAINER_URL = os.getenv("PORTAINER_URL", "").rstrip("/")
PORTAINER_API_KEY = os.getenv("PORTAINER_API_KEY", "")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL_SECONDS", "10"))
LATENCY_WARN_MS = float(os.getenv("LATENCY_WARN_MS", "2000"))
PORT = int(os.getenv("PORT", "9500"))

state = {
    "services": {},
    "history": {s["id"]: deque(maxlen=HISTORY_LEN) for s in SERVICES},
    "incidents": deque(maxlen=300),
    "prev_up": {},
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
        return {"up": False, "latency_ms": None, "error": str(exc)[:80]}


async def check_tcp(svc: dict) -> dict:
    start = time.perf_counter()
    try:
        fut = asyncio.open_connection(svc["host"], svc["port"])
        reader, writer = await asyncio.wait_for(fut, timeout=3.0)
        writer.close()
        await writer.wait_closed()
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return {"up": True, "latency_ms": latency_ms, "code": None}
    except Exception as exc:
        return {"up": False, "latency_ms": None, "error": str(exc)[:80]}


async def check_portainer() -> list:
    if not PORTAINER_URL:
        return []
    url = f"{PORTAINER_URL}/api/endpoints/1/docker/containers/json"
    try:
        async with httpx.AsyncClient() as c:
            headers = {"X-API-Key": PORTAINER_API_KEY} if PORTAINER_API_KEY else {}
            r = await c.get(url, headers=headers, timeout=5.0)
            if r.status_code != 200:
                return [{"error": f"HTTP {r.status_code}"}]
            data = r.json()
            return [{"name": ctn.get("Names", [""])[0].lstrip("/"),
                     "state": ctn.get("State"),
                     "status": ctn.get("Status"),
                     "image": ctn.get("Image"),
                     "id": ctn.get("Id", "")[:12]} for ctn in data]
    except Exception as exc:
        return [{"error": str(exc)[:120]}]


async def poll_once():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for svc in SERVICES:
            if svc["kind"] == "http":
                tasks.append(check_http(client, svc))
            else:
                tasks.append(check_tcp(svc))
        results = await asyncio.gather(*tasks)

    for svc, res in zip(SERVICES, results):
        state["services"][svc["id"]] = {
            "id": svc["id"],
            "name": svc.get("name"),
            "host": svc.get("host"),
            "port": svc.get("port"),
            "public_port": svc.get("public_port"),
            "kind": svc.get("kind"),
            "path": svc.get("path"),
            "group": svc.get("group"),
            "optional": svc.get("optional", False),
            **res,
        }
        state["history"][svc["id"]].append({
            "time": time.time(),
            "up": res["up"],
            "latency_ms": res.get("latency_ms"),
        })

        # incident transition detection
        prev = state["prev_up"].get(svc["id"])
        if prev is not None and prev != res["up"]:
            state["incidents"].append({
                "ts": time.time(),
                "id": svc["id"],
                "name": svc.get("name"),
                "severity": "critical" if not res["up"] else "resolved",
                "kind": "down" if not res["up"] else "up",
                "msg": f'{svc.get("name")} {"went DOWN" if not res["up"] else "recovered"}',
                "latency_ms": res.get("latency_ms"),
            })
        elif res["up"] and res.get("latency_ms") and res["latency_ms"] > LATENCY_WARN_MS:
            last = state["incidents"][-1] if state["incidents"] else None
            if not (last and last["id"] == svc["id"] and last["kind"] == "latency"
                    and time.time() - last["ts"] < 120):
                state["incidents"].append({
                    "ts": time.time(),
                    "id": svc["id"],
                    "name": svc.get("name"),
                    "severity": "warn",
                    "kind": "latency",
                    "msg": f'{svc.get("name")} high latency {res["latency_ms"]}ms',
                    "latency_ms": res.get("latency_ms"),
                })
        state["prev_up"][svc["id"]] = res["up"]

    state["services"]["_portainer"] = await check_portainer()
    state["last_run"] = time.time()


async def poll_loop():
    while True:
        await poll_once()
        try:
            await broadcast_status()
        except Exception:
            pass
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()


app = FastAPI(title="J1-NOC StackForge Dashboard", lifespan=lifespan)


@app.get("/api/status")
async def api_status():
    return JSONResponse(build_status())


def build_status():
    services = {k: v for k, v in state["services"].items() if k != "_portainer"}
    history = {k: list(v) for k, v in state["history"].items()}
    services_out = {}
    for k, v in services.items():
        hist = state["history"].get(k, deque())
        samples = [h for h in hist if h.get("up") is not None]
        up_n = sum(1 for h in samples if h["up"])
        uptime = round(100.0 * up_n / len(samples), 2) if samples else None
        services_out[k] = {**v, "uptime_pct": uptime}
    core = {k: v for k, v in services_out.items() if not v.get("optional")}
    ext = {k: v for k, v in services_out.items() if v.get("optional")}
    fleet_up = sum(1 for v in core.values() if v.get("up"))
    fleet_total = len(core)
    fleet_slo = round(100.0 * fleet_up / fleet_total, 2) if fleet_total else None
    core_down = sum(1 for v in core.values() if not v.get("up"))
    ext_down = sum(1 for v in ext.values() if not v.get("up"))
    return {
        "last_run": state["last_run"],
        "poll_interval": POLL_INTERVAL,
        "services": services_out,
        "history": history,
        "portainer": {
            "configured": bool(PORTAINER_URL),
            "containers": state["services"].get("_portainer", []),
        },
        "prod": {
            "configured": True,
            "ollama_host": os.getenv("OLLAMA_HOST", "localhost"),
            "ollama_port": int(os.getenv("OLLAMA_PORT", "11434")),
            "prod_hosts": os.getenv("PROD_HOSTS", ""),
        },
        "fleet_slo": fleet_slo,
        "core_down": core_down,
        "external_down": ext_down,
        "incidents": list(state["incidents"])[-50:],
    }


@app.get("/api/tailscale")
async def tailscale_nodes():
    global _ts_cache
    now = time.time()
    if now - _ts_cache["ts"] > 15:
        try:
            r = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True, text=True, timeout=8,
            )
            data = json.loads(r.stdout)
            peers = data.get("Peer", {})
            self_node = data.get("Self", {})
            out = []
            for v in list(peers.values()) + [{"HostName": self_node.get("HostName","self"), "TailscaleIPs": self_node.get("TailscaleIPs",[]), "OS": "linux", "Online": True, "LastSeen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "Relay": "", "DNSName": self_node.get("DNSName",""), "_self": True}]:
                ips = v.get("TailscaleIPs", [])
                ipv4 = next((ip for ip in ips if "." in ip and not ip.startswith("fd")), None)
                if not ipv4:
                    continue
                octets = list(map(int, ipv4.split(".")))
                is_self = v.get("_self", False)
                # Self is in St. Lucia; peers fly into the Miami DERP hub
                if is_self:
                    lat, lon = 14.0754, -60.9442
                else:
                    lat = (octets[1] * 7 + octets[2] * 13) % 180 - 90
                    lon = (octets[2] * 17 + octets[3] * 23) % 360 - 180
                relay = (v.get("Relay") or "").lower() if not is_self else ""
                if is_self:
                    rlat, rlon, rname = lat, lon, "Beauséjour, St.Lucia"
                else:
                    rlat, rlon, rname = TAILSCALE_RELAY_GEO.get(relay, (lat, lon, relay or "DIRECT"))
                out.append({
                    "hostname": v.get("HostName", "?"),
                    "dns": v.get("DNSName", ""),
                    "ip": ipv4,
                    "os": v.get("OS", "?"),
                    "online": v.get("Online", False),
                    "lastseen": v.get("LastSeen", "")[:19],
                    "relay": relay,
                    "relay_name": rname,
                    "lat": round(rlat, 4),
                    "lon": round(rlon, 4),
                    "tx_gb": round(v.get("TxBytes", 0) / 1e9, 2),
                    "rx_gb": round(v.get("RxBytes", 0) / 1e9, 2),
                    "self": v.get("_self", False),
                })
            _ts_cache = {"ts": now, "data": out}
        except Exception as exc:
            return JSONResponse({"error": str(exc), "nodes": _ts_cache["data"]}, status_code=500)
    return JSONResponse({"ts": _ts_cache["ts"], "nodes": _ts_cache["data"]})


# ---- Tailscale client metrics scraper ----
_metrics_cache = {"ts": 0, "data": []}

def _parse_prometheus_text(text: str) -> dict:
    """Best-effort parse of Prometheus text format into metric→value mapping.
    Ignores HELP/TYPE lines and keeps only gauges/counters with numeric values.
    """
    out = {}
    current_meta = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            if line.startswith("# TYPE "):
                parts = line.split()
                if len(parts) >= 4:
                    current_meta[parts[2]] = parts[3]
            continue
        # metric_name{labels} value
        if " " not in line:
            continue
        name_part, value_part = line.rsplit(" ", 1)
        name_part = name_part.strip()
        value_part = value_part.strip()
        try:
            value = float(value_part)
        except ValueError:
            continue
        out[name_part] = {"value": value, "type": current_meta.get(name_part)}
        # also store by labels substring for matching family names
    return out


@app.get("/api/tailscale/metrics")
async def tailscale_metrics():
    """Best-effort scrape of Tailscale client metrics from reachable peers
    that have `--webclient` enabled on port 5252.

    Returns per-peer:
      - host / ip / online / relay
      - tx_by_path / rx_by_path: bytes by path label if available
      - derp_region_id: Home DERP region gauge
      - route_advertised / route_approved: subnet route counts
      - health_warnings: number of active health messages
      - relay_forwarded_bytes: peer_relay forwarded bytes
    """
    global _metrics_cache, _ts_cache
    now = time.time()
    try:
        if now - _metrics_cache["ts"] > 30:
            peers = _ts_cache.get("data", []) or []
            async with httpx.AsyncClient(timeout=3.0) as client:
                results = []
                for n in peers:
                    entry = {
                        "hostname": n.get("hostname"),
                        "ip": n.get("ip"),
                        "online": n.get("online", False),
                        "relay": n.get("relay"),
                        "relay_name": n.get("relay_name"),
                        "reachable": False,
                        "error": None,
                        "tx_by_path": {},
                        "rx_by_path": {},
                        "derp_region_id": None,
                        "route_advertised": None,
                        "route_approved": None,
                        "health_warnings": None,
                        "relay_forwarded_bytes": None,
                    }
                    if not n.get("online") or n.get("self"):
                        results.append(entry)
                        continue
                    try:
                        r = await client.get(f"http://{n['ip']}:5252/metrics")
                        if r.status_code == 200:
                            parsed = _parse_prometheus_text(r.text)

                            def pick(path_val: str, direction: str):
                                key = f"tailscaled_{direction}_bytes_total{{path=\\\"{path_val}\\\"}}"
                                hit = parsed.get(key)
                                return round(hit["value"] / 1e9, 3) if hit else None

                            entry["reachable"] = True
                            entry["tx_by_path"] = {
                                p: pick(p, "outbound") for p in [
                                    "direct_ipv4", "direct_ipv6", "derp",
                                    "peer_relay_ipv4", "peer_relay_ipv6",
                                ]
                            }
                            entry["rx_by_path"] = {
                                p: pick(p, "inbound") for p in [
                                    "direct_ipv4", "direct_ipv6", "derp",
                                    "peer_relay_ipv4", "peer_relay_ipv6",
                                ]
                            }
                            derp = parsed.get("tailscaled_home_derp_region_id")
                            entry["derp_region_id"] = int(derp["value"]) if derp else None
                            adv = parsed.get("tailscaled_advertised_routes")
                            app = parsed.get("tailscaled_approved_routes")
                            entry["route_advertised"] = int(adv["value"]) if adv else None
                            entry["route_approved"] = int(app["value"]) if app else None
                            hlt = parsed.get("tailscaled_health_messages")
                            entry["health_warnings"] = int(hlt["value"]) if hlt else None
                            relay_b = parsed.get("tailscaled_peer_relay_forwarded_bytes_total")
                            entry["relay_forwarded_bytes"] = round(relay_b["value"] / 1e9, 3) if relay_b else None
                        else:
                            entry["error"] = f"HTTP {r.status_code}"
                    except Exception as exc:
                        entry["error"] = str(exc)
                    results.append(entry)
                _metrics_cache = {"ts": now, "data": results}
    except Exception as exc:
        return JSONResponse({
            "error": str(exc),
            "peers": _metrics_cache.get("data", []),
        }, status_code=500)
    return JSONResponse({"ts": _metrics_cache["ts"], "peers": _metrics_cache["data"]})


@app.get("/api/healthz")
async def healthz():
    return {"ok": True}


# ── Self-hosted API registry ──────────────────────────────────────────────────
# Other Hermes agents on Tailscale call this to discover every local service.
TAILSCALE_IP = os.getenv("TAILSCALE_IP", "YOUR_SERVER_IP")

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
            "notes": "Supports POST /search with q=query&format=json",
        },
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
            "notes": "v1.18.2. Full REST API with Swagger at /docs.",
        },
        "agent_isolation": {
            "type": "collection-prefix",
            "orchestrator": "orchestrator_memories",
            "analyst": "analyst_memories",
            "writer": "writer_memories",
            "marketer": "marketer_memories",
            "coder": "coder_memories",
            "notes": "Use per-agent collection names. All agents share host but write to isolated collections.",
        },
    },
    "redis": {
        "name": "Redis",
        "description": "In-memory key-value store. Cache, session, and pub/sub. Managed by Honcho.",
        "tailscale_url": f"redis://{TAILSCALE_IP}:***@localhost:5432/honcho",
        "api_docs": None,
        "group": "Memory & Knowledge",
        "hermes_usage": {
            "env_var": "DATABASE_URL=postgresql://postgres@YOUR_SERVER_IP:5432/honcho",
            "config": "Honcho manages all connections. Direct access bypasses workspace isolation.",
            "notes": "Port 5432. Access only through Honcho API to maintain per-agent isolation.",
        },
        "agent_isolation": {
            "type": "honcho-managed",
            "notes": "Never connect directly. Honcho API at port 8000 provides workspace-level isolation.",
        },
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
            "notes": "OpenAI-compatible API at /v1/. Stateless — no isolation concerns.",
        },
    },
    "honcho": {
        "name": "Honcho Memory",
        "description": "Self-hosted memory backend with workspace-level multi-agent isolation.",
        "tailscale_url": f"http://{TAILSCALE_IP}:8000",
        "internal_url": "http://localhost:8000",
        "api_docs": "http://localhost:8000/openapi.json",
        "group": "Memory & Knowledge",
        "hermes_usage": {
            "env_var": "HONCHO_URL=http://YOUR_SERVER_IP:8000",
            "config": "Honcho memory provider. Uses PostgreSQL + Redis underneath. Per-agent workspaces.",
            "notes": "v3 API at /v3/. Workspace isolation per agent.",
        },
        "agent_isolation": {
            "type": "workspace",
            "orchestrator": "orc_6594283abd4456d7a",
            "analyst": "ana_44c2da12c9a654099",
            "writer": "wri_d89772f564d55757b",
            "marketer": "mar_50ce547eb4db51e7a",
            "coder": "cod_3e1e2656fd1d5e85a",
            "notes": "Each agent has a dedicated Honcho workspace. All memory/data scoped within it.",
        },
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
            "notes": "Python HTTPServer. Poll /api/snapshot for live state. Shared kanban board.",
        },
        "agent_isolation": {
            "type": "shared",
            "notes": "Single kanban board shared across all agents. No isolation — designed for coordination.",
        },
    },
    "noc_dashboard": {
        "name": "NOC Dashboard",
        "description": "StackForge health monitor showing service uptime, Tailscale map, and DERP relays.",
        "tailscale_url": f"http://{TAILSCALE_IP}:9500",
        "internal_url": "http://localhost:9500",
        "api_docs": "http://localhost:9500/api/status",
        "group": "Dashboards & Ops",
        "hermes_usage": {
            "env_var": "NOC_URL=http://YOUR_SERVER_IP:9500",
            "config": "FastAPI. Live service health at /api/status. Service registry at /api/services.json.",
            "notes": "Period 10s poll. Read-only. No isolation concerns.",
        },
    },
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
        ),
    })


@app.get("/api/services.sh")
async def api_services_sh():
    """Shell script snippet — source from any Hermes agent on Tailscale to set env vars."""
    lines = [
        "#!/bin/bash",
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
        "echo '  Search:    SearXNG     -> $SEARXNG_URL'",
        "echo '  Vectors:   Qdrant      -> $QDRANT_URL'",
        "echo '  Cache:     Redis       -> $REDIS_URL'",
        "echo '  Database:  PostgreSQL  -> $DATABASE_URL'",
        "echo '  Inference: Ollama      -> $OLLAMA_HOST'",
        "echo '  Dashboard: Mission Ctrl-> $MISSION_CONTROL_URL'",
        "echo '  Dashboard: NOC         -> $NOC_URL'",
        "echo",
        'echo "One-command agent setup: hermes config set model.base_url $OLLAMA_HOST"',
        "",
    ]
    return PlainTextResponse("\n".join(lines), media_type="text/x-shellscript")


@app.get("/metrics")
async def metrics_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/metrics.html")

@app.get("/geo")
async def geo_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/geo.html")

@app.get("/agents")
async def agents_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/agents.html")

@app.get("/mesh")
async def mesh_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/mesh.html")

# ── Live WebSocket stream ─────────────────────────────────────────────────────
WS_CLIENTS = set()


async def broadcast_status():
    if not WS_CLIENTS:
        return
    payload = json.dumps(build_status(), default=str)
    dead = set()
    for ws in list(WS_CLIENTS):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        WS_CLIENTS.discard(ws)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    WS_CLIENTS.add(ws)
    try:
        await ws.send_json(build_status())
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        WS_CLIENTS.discard(ws)


@app.get("/api/incidents")
async def api_incidents(limit: int = 50):
    return JSONResponse({
        "incidents": list(state["incidents"])[-limit:],
        "active": [i for i in state["incidents"] if i["severity"] == "critical"],
    })


@app.get("/api/check/{svc_id}")
async def api_check(svc_id: str):
    svc = next((s for s in SERVICES if s["id"] == svc_id), None)
    if not svc:
        return JSONResponse({"error": "unknown service"}, status_code=404)
    if svc["kind"] == "http":
        async with httpx.AsyncClient(follow_redirects=True) as c:
            res = await check_http(c, svc)
    else:
        res = await check_tcp(svc)
    state["services"][svc_id] = {
        "id": svc["id"], "name": svc.get("name"), "host": svc.get("host"),
        "port": svc.get("port"), "public_port": svc.get("public_port"),
        "kind": svc.get("kind"), "path": svc.get("path"), "group": svc.get("group"),
        "optional": svc.get("optional", False),
        **res,
    }
    state["history"][svc_id].append({"time": time.time(), "up": res["up"], "latency_ms": res.get("latency_ms")})
    state["prev_up"][svc_id] = res["up"]
    return JSONResponse({"id": svc_id, "result": res})


@app.post("/api/agents/onboard")
async def api_agents_onboard(request: Request):
    """Auto-onboard a Hermes agent: provision Honcho workspace+peer (memory DB)
    + API key (passcode); return connection config for the agent to self-configure.
    Backend reaches Honcho on localhost; agent receives TAILSCALE_IP endpoints."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    agent_id = body.get("agent_id") or ("agent-" + uuid.uuid4().hex[:8])
    name = body.get("name") or agent_id
    honcho = os.getenv("HONCHO_URL", "http://localhost:8000")
    ip = os.getenv("TAILSCALE_IP", "YOUR_SERVER_IP")
    ws_id = peer_id = key = None
    async with httpx.AsyncClient() as c:
        try:
            w = (await c.post(f"{honcho}/v3/workspaces", json={"name": name, "embedding_provider": "openai"})).json()
            ws_id = w.get("id")
        except Exception as e:
            return JSONResponse({"error": "honcho workspace create failed", "detail": str(e)}, status_code=502)
        try:
            p = (await c.post(f"{honcho}/v3/workspaces/{ws_id}/peers", json={"name": name})).json()
            peer_id = p.get("id")
        except Exception:
            peer_id = None
        try:
            # Honcho /v3/keys feature is disabled; mint a local passcode the agent
            # can use to identify/authenticate itself on future calls.
            key = uuid.uuid4().hex + uuid.uuid4().hex
        except Exception:
            key = None
    setup_bash = (
        f"# StackForge agent onboarding — run to self-configure (nothing manual)\\n"
        f"hermes config set model.base_url http://{ip}:11434\n"
        f"hermes config set model.provider custom:ollama\n"
        f"hermes config set memory.provider custom\n"
        f"hermes config set memory.base_url http://{ip}:8000\n"
        f"# Notes to this server CouchDB (LiveSync): agent writes via CouchDB REST API at http://{ip}:5984\n"
    )
    AGENTS_REGISTRY[agent_id] = {
        "agent_id": agent_id, "name": name, "workspace_id": ws_id,
        "peer_id": peer_id, "passcode": key, "memory_api": f"http://{ip}:8000",
        "notes_api": f"http://{ip}:5984", "ollama": f"http://{ip}:11434",
        "created_at": time.time(),
    }
    _save_agents(AGENTS_REGISTRY)
    return JSONResponse({
        "agent_id": agent_id,
        "workspace_id": ws_id,
        "peer_id": peer_id,
        "passcode": key,
        "memory_api": f"http://{ip}:8000",
        "notes_api": f"http://{ip}:5984",
        "ollama": f"http://{ip}:11434",
        "setup": {"bash": setup_bash},
        "status": "onboarded",
    })


# Agent onboarding registry (persisted across restarts)
AGENTS_FILE = "/tmp/noc-agents.json"
def _load_agents():
    try:
        import json
        with open(AGENTS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}
def _save_agents(d):
    try:
        import json
        with open(AGENTS_FILE, "w") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass
AGENTS_REGISTRY = _load_agents()

@app.get("/api/agents")
async def api_agents_list():
    out = []
    for a in AGENTS_REGISTRY.values():
        c = a.get("passcode") or ""
        item = {k: v for k, v in a.items() if k != "passcode"}
        item["passcode_masked"] = ("****" + c[-4:]) if c else ""
        out.append(item)
    return JSONResponse({"agents": out, "count": len(out)})

# CORS so the Mission Control dashboard (:51763) can fetch this API
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# Serve static frontend from local directory (runtime placeholder fill)
FRONTEND_SRC = str(BASE_DIR.parent / "frontend")
DIST_DIR = "/tmp/noc-dist"

def build_dist():
    """Copy frontend to DIST_DIR, substituting infra placeholders with env values.
    Repo ships placeholders (YOUR_SERVER_IP); live server injects TAILSCALE_IP."""
    import shutil
    ip = os.getenv("TAILSCALE_IP", "YOUR_SERVER_IP")
    host = os.getenv("TAILSCALE_HOST", "YOUR_SERVER_HOST")
    tailnet = os.getenv("TAILNET_NAME", "YOUR_TAILNET_NAME")
    repl = (("YOUR_SERVER_IP", ip), ("YOUR_SERVER_HOST", host), ("YOUR_TAILNET_NAME", tailnet))
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)
    for root, _, files in os.walk(FRONTEND_SRC):
        for fn in files:
            sp = os.path.join(root, fn)
            dp = os.path.join(DIST_DIR, os.path.relpath(sp, FRONTEND_SRC))
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            if fn.endswith(".html"):
                t = open(sp, encoding="utf-8").read()
                for a, b in repl:
                    t = t.replace(a, b)
                open(dp, "w", encoding="utf-8").write(t)
            else:
                shutil.copy2(sp, dp)

build_dist()
if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
else:
    @app.get("/")
    async def root():
        return {"message": "NOC Dashboard backend running (no frontend built)", "port": PORT}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
