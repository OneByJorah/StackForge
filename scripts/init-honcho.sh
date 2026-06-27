#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Initialize .env.honcho if not exists
if [ ! -f "$REPO_ROOT/.env.honcho" ]; then
  cp "$REPO_ROOT/honcho/.env.honcho.example" "$REPO_ROOT/.env.honcho"
  echo "Created .env.honcho from example. Please edit it with your LLM API keys."
else
  echo ".env.honcho already exists, skipping"
fi

# Create ~/.honcho directory and copy config
mkdir -p "$HOME/.honcho"
cp "$REPO_ROOT/honcho/honcho-config.json" "$HOME/.honcho/config.json"
echo "Honcho config installed to ~/.honcho/config.json"
echo "Remember to restart Hermes after configuration."
