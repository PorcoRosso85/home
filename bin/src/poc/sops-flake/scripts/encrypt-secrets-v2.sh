#!/usr/bin/env bash
set -euo pipefail

echo '🔒 Encrypting secrets with sops (v2)...'

# Check prerequisites
if [[ ! -f /etc/ssh/ssh_host_ed25519_key.pub ]]; then
    echo '❌ Error: SSH host key not found'
    echo 'Please ensure SSH is configured: sudo ssh-keygen -A'
    exit 1
fi

# Safely get SSH key
SSH_KEY=$(cat /etc/ssh/ssh_host_ed25519_key.pub 2>/dev/null | cut -d' ' -f1-2)
if [[ -z "$SSH_KEY" ]]; then
    echo '❌ Error: Failed to read SSH host key'
    exit 1
fi

echo "✓ Using SSH host key: $SSH_KEY"

# Rest of the script continues...
