#!/usr/bin/env python3
"""Scan vault directory and generate index.json for the web viewer."""
import json
import sys
from pathlib import Path

VAULT = Path(sys.argv[1] if len(sys.argv) > 1 else "/usr/share/caddy/vault")

def scan():
    notes = []
    for f in sorted(VAULT.rglob("*.md")):
        rel = f.relative_to(VAULT)
        title = rel.stem.replace("-", " ").replace("_", " ").title()
        notes.append({"path": str(rel), "title": title})
    idx = {"count": len(notes), "notes": notes}
    (VAULT / "index.json").write_text(json.dumps(idx, indent=2))
    print(f"Indexed {len(notes)} notes")

if __name__ == "__main__":
    scan()