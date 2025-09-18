#!/usr/bin/env bash
# Setup SSH key as SOPS recipient
# Usage: ./scripts/setup-ssh-recipient.sh [SSH_KEY_PATH]

set -euo pipefail

SSH_KEY="${1:-$HOME/.ssh/id_ed25519.pub}"

# Check SSH key exists
if [[ ! -f "$SSH_KEY" ]]; then
    echo "✗ SSH public key not found: $SSH_KEY"
    echo "  Please specify a valid SSH public key path"
    exit 1
fi

# Convert SSH to age format
echo "Converting SSH key to age format..."
AGE_KEY=$(ssh-to-age -i "$SSH_KEY")

if [[ -z "$AGE_KEY" ]]; then
    echo "✗ Failed to convert SSH key"
    exit 1
fi

echo "✓ SSH key converted to age format:"
echo "  $AGE_KEY"
echo ""
echo "To use this key, update .sops.yaml:"
echo "  1. Replace REPLACE_ME_SSH with: $AGE_KEY"
echo "  2. Run: sops updatekeys secrets/app.yaml"
echo ""
echo "For decryption, use the converted age key:"
echo "  nix develop  # Includes ssh-to-age conversion tools"