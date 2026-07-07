#!/usr/bin/env bash
set -euo pipefail
cd /path/to/StackForge

echo '=== Core services ==='
curl -s -o /dev/null -w 'searxng=%{http_code}\n' 'http://localhost:8080/search?format=json&q=test'
curl -s -o /dev/null -w 'obsidian=%{http_code}\n' http://localhost:8083/
curl -s -o /dev/null -w 'qdrant=%{http_code}\n' http://localhost:6333/
curl -s -o /dev/null -w 'couchdb=%{http_code}\n' http://localhost:5984/
curl -s -o /dev/null -w 'selenium=%{http_code}\n' http://localhost:4444/status

echo '=== SearXNG JSON ==='
curl -s 'http://localhost:8080/search?format=json&q=python&language=en' > /tmp/sd_searxng.json
python3 -c 'import json,sys; d=json.load(open("/tmp/sd_searxng.json")); print("results=", len(d.get("results", [])))'

echo '=== Honcho health ==='
curl -s http://localhost:8000/health

echo '=== Obsidian page ==='
curl -s http://localhost:8083/ | grep -q 'Obsidian' || echo '⚠️  Obsidian page content check failed'

echo '=== All done ==='