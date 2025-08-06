#!/usr/bin/env bash
# Qwen-Code runner with automatic Nix build management

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# OpenRouter configuration
# You can override these by setting environment variables before running this script
: ${OPENAI_API_KEY:="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"}
: ${OPENAI_BASE_URL:="https://openrouter.ai/api/v1"}
: ${OPENAI_MODEL:="qwen/qwen3-coder"}

# Export the environment variables
export OPENAI_API_KEY
export OPENAI_BASE_URL
export OPENAI_MODEL

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