#!/usr/bin/env bash
# =============================================================================
# StackDeploy Secrets Management
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SECRETS_DIR="$REPO_ROOT/secrets"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Ensure secrets directory exists with proper permissions
init_secrets() {
    mkdir -p "$SECRETS_DIR"
    chmod 750 "$SECRETS_DIR"

    # Create .gitkeep to track directory
    touch "$SECRETS_DIR/.gitkeep"

    # Add to .gitignore if not already there
    if [ -f "$REPO_ROOT/.gitignore" ]; then
        if ! grep -q "^secrets/" "$REPO_ROOT/.gitignore" 2>/dev/null; then
            echo "secrets/" >> "$REPO_ROOT/.gitignore"
            info "Added secrets/ to .gitignore"
        fi
    fi
}

# Generate a random password
generate_password() {
    local length="${1:-32}"
    openssl rand -base64 48 | tr -dc 'a-zA-Z0-9!@#$%^&*()_+-=' | head -c "$length"
}

# Create or update a secret file
set_secret() {
    local name="$1"
    local value="$2"
    local file="$SECRETS_DIR/${name}.txt"

    if [ -f "$file" ]; then
        warn "Secret $name already exists, overwriting..."
    fi

    echo -n "$value" > "$file"
    chmod 600 "$file"
    info "Secret $name written to $file"
}

# Read a secret from file
get_secret() {
    local name="$1"
    local file="$SECRETS_DIR/${name}.txt"

    if [ ! -f "$file" ]; then
        error "Secret $name not found at $file"
        return 1
    fi

    cat "$file"
}

# List all secrets
list_secrets() {
    if [ ! -d "$SECRETS_DIR" ]; then
        info "No secrets directory found"
        return 0
    fi

    echo "Secrets:"
    for f in "$SECRETS_DIR"/*.txt; do
        if [ -f "$f" ]; then
            local name
            name=$(basename "$f" .txt)
            local size
            size=$(wc -c < "$f")
            echo "  - $name (${size}b)"
        fi
    done
}

# Rotate a secret (generate new one)
rotate_secret() {
    local name="$1"
    local length="${2:-32}"
    local new_value
    new_value=$(generate_password "$length")
    set_secret "$name" "$new_value"
    info "Secret $name rotated"
}

# Initialize all required secrets with random values
init_all_secrets() {
    init_secrets

    info "Initializing all required secrets..."

    if [ ! -f "$SECRETS_DIR/honcho_db_password.txt" ]; then
        set_secret "honcho_db_password" "$(generate_password 32)"
    fi

    if [ ! -f "$SECRETS_DIR/camofox_api_key.txt" ]; then
        set_secret "camofox_api_key" "$(generate_password 48)"
    fi

    if [ ! -f "$SECRETS_DIR/camofox_admin_key.txt" ]; then
        set_secret "camofox_admin_key" "$(generate_password 48)"
    fi

    if [ ! -f "$SECRETS_DIR/searxng_secret_key.txt" ]; then
        set_secret "searxng_secret_key" "$(generate_password 64)"
    fi

    if [ ! -f "$SECRETS_DIR/postgres_password.txt" ]; then
        set_secret "postgres_password" "$(generate_password 32)"
    fi

    info "All secrets initialized in $SECRETS_DIR"
    info "IMPORTANT: Back up this directory securely!"
    info "Run: tar czf stackdeploy-secrets-backup.tar.gz -C $SECRETS_DIR ."
}

# Export secrets as environment variables
export_secrets() {
    if [ ! -d "$SECRETS_DIR" ]; then
        error "Secrets directory not found. Run 'init' first."
        return 1
    fi

    for f in "$SECRETS_DIR"/*.txt; do
        if [ -f "$f" ]; then
            local name
            name=$(basename "$f" .txt)
            # Convert to env var name (e.g., honcho_db_password -> HONCHO_DB_PASSWORD)
            local env_name
            env_name=$(echo "$name" | tr '[:lower:]' '[:upper:]')
            export "$env_name"=$(cat "$f")
        fi
    done

    info "Secrets exported as environment variables"
}

# Main
case "${1:-help}" in
    init)
        init_all_secrets
        ;;
    list)
        list_secrets
        ;;
    get)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 get <secret-name>"
            exit 1
        fi
        get_secret "$2"
        ;;
    set)
        if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
            error "Usage: $0 set <secret-name> <value>"
            exit 1
        fi
        set_secret "$2" "$3"
        ;;
    rotate)
        if [ -z "${2:-}" ]; then
            error "Usage: $0 rotate <secret-name> [length]"
            exit 1
        fi
        rotate_secret "$2" "${3:-32}"
        ;;
    export)
        export_secrets
        ;;
    *)
        echo "StackDeploy Secrets Manager"
        echo ""
        echo "Usage:"
        echo "  $0 init              Initialize all secrets with random values"
        echo "  $0 list              List all secrets"
        echo "  $0 get <name>        Read a secret value"
        echo "  $0 set <name> <val>  Set a secret value"
        echo "  $0 rotate <name>     Rotate a secret (generate new random)"
        echo "  $0 export            Export secrets as env vars"
        echo ""
        echo "Secrets directory: $SECRETS_DIR"
        ;;
esac
