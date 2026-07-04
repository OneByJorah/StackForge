#!/bin/bash
# vault-write.sh — write a note to the shared Obsidian vault
# Usage: vault-write.sh "My Title" "content here" [tags]
# Called by Hermes agents after each task.
#
# Portable: reads OBSIDIAN_VAULT_PATH from env or uses the default.
# Works inside Docker, bare metal, or via cron.

set -euo pipefail

VAULT="${OBSIDIAN_VAULT_PATH:-/path/to/StackDeploy/obsidian/vault}"
TITLE="${1:-Untitled}"
BODY="${2:-}"
TAGS="${3:-agent}"

DATE=$(date +"%Y-%m-%d")
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' '-' | tr -cd '[:alnum:]-')
FILE="${DATE}-${SLUG}.md"

mkdir -p "$VAULT"

cat > "$VAULT/$FILE" <<EOF
---
title: "$TITLE"
date: $TIMESTAMP
tags: [$TAGS]
agent: ${HERMES_AGENT:-unknown}
---

# $TITLE

$BODY

---
*Automated entry from Hermes Agent (${HERMES_AGENT:-unknown}) • $TIMESTAMP*
EOF

echo "$FILE"
