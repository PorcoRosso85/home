#!/usr/bin/env bash
# Check for plaintext secrets in the secrets/ directory
# This script ensures that all secrets files are properly encrypted by SOPS

set -euo pipefail

# Exit if secrets directory doesn't exist
[ -d secrets ] || {
    echo "No secrets directory found, skipping plaintext check"
    exit 0
}

# Check for plaintext secrets (files without ENC[AES256_GCM pattern)
if command -v rg >/dev/null 2>&1; then
    # -L means files without match, if any are found, that means plaintext exists
    if rg -L 'ENC\[AES256_GCM' secrets/ | grep -q .; then
        echo 'ERROR: Plaintext secrets detected under secrets/'
        echo 'The following files contain unencrypted data:'
        rg -L 'ENC\[AES256_GCM' secrets/
        echo 'Please encrypt these files with: sops -e -i <filename>'
        exit 1
    fi
elif command -v grep >/dev/null 2>&1; then
    # Find files without ENC pattern
    PLAINTEXT_FILES=$(find secrets/ -name "*.yaml" -o -name "*.yml" -o -name "*.json" | xargs grep -L 'ENC\[AES256_GCM' 2>/dev/null || true)
    if [ -n "$PLAINTEXT_FILES" ]; then
        echo 'ERROR: Plaintext secrets detected under secrets/'
        echo 'The following files contain unencrypted data:'
        echo "$PLAINTEXT_FILES"
        echo 'Please encrypt these files with: sops -e -i <filename>'
        exit 1
    fi
else
    echo 'WARNING: Neither rg nor grep found, cannot check for plaintext secrets'
    exit 1
fi

echo 'SUCCESS: All secrets files are properly encrypted'