#!/usr/bin/env bash
# Age key setup helper for sops-flake templates
# 使用例: ./scripts/setup-age-key.sh

set -euo pipefail

KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"

# 既存鍵チェック
if [[ -f "$KEY_FILE" ]]; then
    echo "✓ Age key already exists at: $KEY_FILE"
    age-keygen -y "$KEY_FILE" 2>/dev/null || echo "Public key: (unable to display)"
    exit 0
fi

# 新規鍵生成
mkdir -p "$(dirname "$KEY_FILE")"
age-keygen -o "$KEY_FILE"
chmod 600 "$KEY_FILE"

echo "✓ Age key generated at: $KEY_FILE"
echo "Add this public key to .sops.yaml:"
age-keygen -y "$KEY_FILE"