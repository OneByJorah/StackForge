#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load env if present
set -a
[ -f "$REPO_ROOT/.env" ] && source "$REPO_ROOT/.env"
set +a

VAULT="${OBSIDIAN_VAULT_PATH:-$REPO_ROOT/obsidian-vault}"
mkdir -p "$VAULT"
mkdir -p "$VAULT/.obsidian/plugins"
cat > "$VAULT/.obsidian/app.json" <<'EOF'
{"baseFontSize":16,"theme":"obsidian","translucency":false}
EOF
echo "init-obsidian: vault ready at $VAULT"
