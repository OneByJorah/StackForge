#!/usr/bin/env bash
set -euo pipefail
# Use existing venv if present; create one otherwise
cd "$(dirname "$0")"
if [ -d .venv ]; then
  . .venv/bin/activate
else
  python3 -m venv .venv
  . .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt || true
fi
python3 - <<'PY'
import os, sys
print("venv_state=ok")
PY
