#!/usr/bin/env bash
# Verify that secrets are properly encrypted
# 使用例: ./scripts/verify-encryption.sh

set -euo pipefail

SECRETS_DIR="${1:-secrets}"
ERRORS=0

# すべての.yaml/.jsonファイルをチェック
shopt -s nullglob
for file in "$SECRETS_DIR"/*.yaml "$SECRETS_DIR"/*.json; do
    [[ -f "$file" ]] || continue
    
    if ! grep -q "^sops:" "$file" 2>/dev/null; then
        echo "✗ Not encrypted: $file"
        ((ERRORS++))
    else
        echo "✓ Encrypted: $file"
    fi
done

if [[ $ERRORS -gt 0 ]]; then
    echo "Found $ERRORS unencrypted files"
    exit 1
fi

echo "All secrets are properly encrypted"