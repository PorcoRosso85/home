#!/usr/bin/env bash
set -euo pipefail

# Test: packages.client-hello has meta.description accessible and visible in nix search
echo "Testing packages meta.description accessibility..."

# Expected description content
EXPECTED_DESC="Dynamic HTTP client for opencode (pre-auth; POST /session/:id/message; env overrides)"

echo "Testing meta.description via nix eval..."

# Test 1: Check that meta.description is accessible via nix eval
ACTUAL_DESC=$(nix eval .#packages.x86_64-linux.client-hello.meta.description --no-warn-dirty --raw 2>/dev/null)

if [ "$ACTUAL_DESC" = "$EXPECTED_DESC" ]; then
    echo "✅ PASS: meta.description accessible via nix eval"
else
    echo "❌ FAIL: meta.description mismatch via nix eval"
    echo "Expected: '$EXPECTED_DESC'"
    echo "Actual: '$ACTUAL_DESC'"
    exit 1
fi

echo "Testing meta.description via nix search..."

# Test 2: Check that description is visible in nix search (the standard way to see package descriptions)
SEARCH_OUTPUT=$(nix search . "client-hello" --no-warn-dirty 2>/dev/null)

if echo "$SEARCH_OUTPUT" | grep -q "$EXPECTED_DESC"; then
    echo "✅ PASS: meta.description visible in nix search"
    echo "Search shows: $(echo "$SEARCH_OUTPUT" | grep "$EXPECTED_DESC" | xargs)"
else
    echo "❌ FAIL: meta.description not found in nix search"
    echo "Expected: '$EXPECTED_DESC'"
    echo "Search output: $SEARCH_OUTPUT"
    exit 1
fi

echo "✅ All tests passed: meta.description is properly implemented and visible"