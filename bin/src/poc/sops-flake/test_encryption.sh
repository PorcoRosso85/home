#!/usr/bin/env bash
# Test: Secrets should be encrypted, not plaintext

echo '=== TEST 1: app.yaml should be encrypted ==='

# Check if secrets file exists
if [[ ! -f secrets/app.yaml ]]; then
    echo 'FAIL: secrets/app.yaml does not exist'
    exit 1
fi

# Check if file is encrypted (contains ENC[AES256_GCM])
if grep -q 'ENC\[AES256_GCM' secrets/app.yaml; then
    echo 'PASS: secrets/app.yaml is encrypted'
else
    echo 'FAIL: secrets/app.yaml is not encrypted (contains plaintext)'
    # Show current content for debugging
    echo 'Current content:'
    head -n 5 secrets/app.yaml
    exit 1
fi

echo '=== TEST 2: .sops.yaml configuration is valid ==='
if [[ -f .sops.yaml ]]; then
    echo 'PASS: .sops.yaml exists'
else
    echo 'FAIL: .sops.yaml is missing'
    exit 1
fi

echo '=== TEST 3: Module exports NixOS module ==='
if grep -q 'nixosModules.default' flake.nix; then
    echo 'PASS: flake.nix exports nixosModules.default'
else
    echo 'FAIL: flake.nix does not export nixosModules.default'
    exit 1
fi

echo ''
echo 'All tests completed!'
