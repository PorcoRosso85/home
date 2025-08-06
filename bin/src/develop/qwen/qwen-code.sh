#!/usr/bin/env bash
# Qwen-Code runner with automatic Nix build management

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to get the store path for the built package
get_store_path() {
    # Build and get the store path
    nix build --no-link --print-out-paths "${SCRIPT_DIR}#qwen-code" 2>/dev/null || {
        echo "Building qwen-code for the first time..." >&2
        nix build --no-link --print-out-paths "${SCRIPT_DIR}#qwen-code"
    }
}

# Get or build the package
STORE_PATH=$(get_store_path)

# Execute qwen-code from the store path
exec "${STORE_PATH}/bin/qwen-code" "$@"