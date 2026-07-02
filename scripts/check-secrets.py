#!/usr/bin/env python3
"""Check detect-secrets report for potential secrets."""
import json
import sys

try:
    with open('/tmp/secrets-report.json') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("No secrets report found or invalid JSON")
    sys.exit(0)

results = data.get('results', {})
total = sum(len(v) for v in results.values())
print(f'Secrets scan complete: {total} potential issues found')
if total > 0:
    for filename, secrets in results.items():
        for s in secrets:
            print(f'  - {filename}:{s.get("line_number", "?")} ({s.get("type", "unknown")})')
