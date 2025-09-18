#!/bin/bash
# Helper script to encrypt env.sh securely
set -euo pipefail

if [[ ! -f env.sh ]]; then
    echo "❌ Error: env.sh not found"
    echo "Create it from env.sh.example:"
    echo "  cp env.sh.example env.sh"
    echo "  vim env.sh"
    exit 1
fi

# Check for .sops.yaml
if [[ ! -f .sops.yaml ]]; then
    echo "❌ Error: .sops.yaml not found"
    echo "Run ./setup.sh first"
    exit 1
fi

# Check for age key
KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
if [[ ! -f "$KEY_FILE" ]]; then
    echo "❌ Error: Age key not found at $KEY_FILE"
    echo "Generate one with: age-keygen -o $KEY_FILE"
    exit 1
fi

echo "🔐 Encrypting env.sh..."

# Encrypt with SOPS
if sops -e env.sh > env.sh.enc; then
    echo "✅ Created env.sh.enc"
    
    # Verify decryption works
    echo "🔍 Verifying encryption..."
    TEMP_TEST=$(mktemp)
    chmod 600 "$TEMP_TEST"
    if sops -d env.sh.enc > "$TEMP_TEST" 2>/dev/null; then
        if diff -q env.sh "$TEMP_TEST" > /dev/null; then
            echo "✅ Encryption verified successfully"
            shred -u "$TEMP_TEST" 2>/dev/null || rm -f "$TEMP_TEST"
        else
            echo "❌ Error: Decrypted content doesn't match original"
            shred -u "$TEMP_TEST" 2>/dev/null || rm -f "$TEMP_TEST"
            rm -f env.sh.enc
            exit 1
        fi
    else
        echo "❌ Error: Failed to decrypt for verification"
        shred -u "$TEMP_TEST" 2>/dev/null || rm -f "$TEMP_TEST"
        rm -f env.sh.enc
        exit 1
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. IMPORTANT: Delete the plain file"
    echo "   shred -u env.sh || rm -f env.sh"
    echo ""
    echo "2. Commit the encrypted file:"
    echo "   git add env.sh.enc"
    echo "   git commit -m 'chore: add encrypted environment variables'"
    echo ""
    echo "3. To use the variables:"
    echo "   source ./source-env.sh"
else
    echo "❌ Error: Encryption failed"
    exit 1
fi
