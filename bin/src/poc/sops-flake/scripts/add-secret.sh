#!/usr/bin/env bash
set -euo pipefail

KEY="${1:-}"
VALUE="${2:-}"

if [[ -z "$KEY" ]]; then
    read -p "Secret key name: " KEY
    read -s -p "Secret value: " VALUE
    echo ""
fi

# Validate key name
if [[ ! "$KEY" =~ ^[a-z_][a-z0-9_]*$ ]]; then
    echo "Error: Key must start with letter/underscore and contain only lowercase letters, numbers, and underscores"
    exit 1
fi

# Backup existing secrets
cp secrets/app.yaml secrets/app.yaml.bak

# Check if sops can decrypt the file
if grep -q 'ENC\[AES256_GCM' secrets/app.yaml; then
    # File is encrypted, decrypt first
    echo "Decrypting existing secrets..."
    sops -d -i secrets/app.yaml
fi

# Add new secret
echo "$KEY: \"$VALUE\"" >> secrets/app.yaml

# Re-encrypt
echo "Encrypting secrets..."
sops -e -i secrets/app.yaml

echo "✅ Secret '$KEY' added successfully"
