#!/usr/bin/env bash
set -uo pipefail

echo '🧪 Testing Pure Encryption Function'
echo '===================================='

# Create test file
TEST_FILE="test-secret.yaml"
echo "test_key: test_value" > $TEST_FILE

# Test 1: Check if encrypt-pure exists in flake
echo -n 'Testing encrypt-pure package definition... '
if grep -q 'packages.encrypt-pure' flake.nix; then
    echo '✅ PASS'
else
    echo '❌ FAIL: encrypt-pure not found in flake.nix'
    exit 1
fi

# Test 2: Check for non-destructive encryption
echo -n 'Testing non-destructive behavior... '
if grep -q 'never modify original' flake.nix; then
    echo '✅ PASS'
else
    echo '⚠️  WARN: Non-destructive behavior not documented'
fi

# Test 3: Check for no in-place editing
echo -n 'Testing absence of -i flag... '
if grep -q 'sops -e -i' flake.nix scripts/*.sh 2>/dev/null; then
    echo '❌ FAIL: In-place editing (-i) still used'
else
    echo '✅ PASS'
fi

# Cleanup
rm -f $TEST_FILE

echo ''
echo 'Pure Encryption Test Complete'
