#!/bin/bash
# Helper script to decrypt and source env.sh securely
set -euo pipefail

# Create secure temp file with restricted permissions
TEMP_ENV=$(mktemp -t env.XXXXXX)
chmod 600 "$TEMP_ENV"

# Cleanup function
cleanup() {
    if [[ -f "$TEMP_ENV" ]]; then
        shred -u "$TEMP_ENV" 2>/dev/null || rm -f "$TEMP_ENV"
    fi
}
trap cleanup EXIT

if [[ -f env.sh.enc ]]; then
    # Decrypt to temp file and source it (no eval!)
    if sops -d env.sh.enc > "$TEMP_ENV" 2>/dev/null; then
        source "$TEMP_ENV"
        echo "✓ Environment variables loaded from env.sh.enc" >&2
    else
        echo "❌ Error: Failed to decrypt env.sh.enc" >&2
        echo "   Check: SOPS_AGE_KEY_FILE=${SOPS_AGE_KEY_FILE:-~/.config/sops/age/keys.txt}" >&2
        exit 1
    fi
elif [[ -f env.sh ]]; then
    # Fallback to plain env.sh with warning
    echo "⚠️  Warning: Using unencrypted env.sh (please encrypt it)" >&2
    source env.sh
else
    echo "❌ Error: Neither env.sh.enc nor env.sh found" >&2
    exit 1
fi
