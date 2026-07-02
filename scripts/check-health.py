#!/usr/bin/env python3
"""Check Docker Compose service health status from JSON output."""
import json
import sys

lines = [l for l in sys.stdin if l.strip()]
if not lines:
    print("0/0 healthy (no data)")
    sys.exit(1)

data = [json.loads(l) for l in lines]
healthy = [d for d in data if d.get('Health') == 'healthy']
print(f'{len(healthy)}/{len(data)} healthy')

if len(healthy) == len(data) and len(data) > 0:
    sys.exit(0)
else:
    sys.exit(1)
