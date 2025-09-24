#!/usr/bin/env bash

set -euo pipefail

# R2 Connection Manifest Generator Wrapper
# Handles Node.js environment setup and executes the main CLI script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Function to find Node.js executable
find_node() {
    # Check if we're in a Nix development environment
    if [[ -n "${NODE:-}" ]]; then
        echo "$NODE"
        return 0
    fi

    # Try standard locations
    for cmd in node nodejs; do
        if command -v "$cmd" > /dev/null 2>&1; then
            echo "$cmd"
            return 0
        fi
    done

    # Try to use Nix flake
    if [[ -f "$PROJECT_ROOT/flake.nix" ]] && command -v nix > /dev/null 2>&1; then
        log "Node.js not found in PATH, trying Nix development environment..."
        if NODE_PATH=$(nix develop "$PROJECT_ROOT" --command which node 2>/dev/null); then
            echo "$NODE_PATH"
            return 0
        fi
    fi

    return 1
}

# Check if help is requested (quick path)
for arg in "$@"; do
    if [[ "$arg" == "--help" ]] || [[ "$arg" == "-h" ]]; then
        cat << 'EOF'
R2 Connection Manifest Generator

USAGE:
    gen-connection-manifest [OPTIONS]

DESCRIPTION:
    Generate environment-specific R2 connection manifests for Cloudflare R2 buckets.
    Supports encrypted secrets via SOPS and comprehensive validation.

QUICK HELP:
    --help              Show full help message
    --env <ENV>         Environment (dev|stg|prod) - REQUIRED
    --dry-run           Preview without writing files
    --verbose           Enable verbose logging
    --list-environments List supported environments

EXAMPLES:
    gen-connection-manifest --env dev
    gen-connection-manifest --env prod --dry-run --verbose

For full help, run with Node.js available or use the Nix development environment:
    nix develop -c gen-connection-manifest --help

PREREQUISITES:
    - Node.js (available via Nix development environment)
    - SOPS and Age for encrypted secrets
    - Environment-specific secrets in secrets/r2.<env>.yaml

EOF
        exit 0
    fi
done

# Find Node.js executable
if ! NODE_EXEC=$(find_node); then
    error "Node.js not found!"
    echo ""
    echo "Solutions:"
    echo "  1. Enter Nix development environment: nix develop"
    echo "  2. Install Node.js in your system"
    echo "  3. Set NODE environment variable to Node.js path"
    echo ""
    echo "For Nix users (recommended):"
    echo "  nix develop -c gen-connection-manifest --env dev"
    exit 1
fi

# Verify the main script exists
MAIN_SCRIPT="$SCRIPT_DIR/gen-connection-manifest.js"
if [[ ! -f "$MAIN_SCRIPT" ]]; then
    error "Main CLI script not found: $MAIN_SCRIPT"
    exit 1
fi

# Execute the main script
log "Using Node.js: $NODE_EXEC"
exec "$NODE_EXEC" "$MAIN_SCRIPT" "$@"