#!/usr/bin/env bash
# Test script for deps structure validation - Schema v2

set -euo pipefail

echo "Testing deps structure (Schema v2)..."

# Build the index
nix build .#index-json

# Test 1: Check schema version
echo "Test 1: Checking schema version..."
SCHEMA_VERSION=$(cat result | jq -r '.schemaVersion')
if [ "$SCHEMA_VERSION" = "2" ]; then
    echo "✓ Schema version is 2"
else
    echo "✗ Expected schema version 2, got $SCHEMA_VERSION"
    exit 1
fi

# Test 2: Check if deps[0] has required fields for v2
echo "Test 2: Checking deps[0] structure..."
if [ "$(cat result | jq '.deps | length')" -gt 0 ]; then
    if cat result | jq -e '.deps[0] | has("name") and has("node") and has("isFlake") and has("locked") and has("original")' > /dev/null; then
        echo "✓ deps[0] has required v2 fields (name, node, isFlake, locked, original)"
    else
        echo "✗ deps[0] missing required v2 fields"
        exit 1
    fi
else
    echo "✓ deps is empty (no dependencies)"
fi

# Test 3: Check that deps is sorted by name
echo "Test 3: Checking deps sorting..."
if cat result | jq -e '.deps | sort_by(.name) == .' > /dev/null; then
    echo "✓ deps is sorted by name"
else
    echo "✗ deps is not sorted by name"
    exit 1
fi

# Test 4: Check generatedAt field exists and is ISO 8601
echo "Test 4: Checking generatedAt timestamp..."
if cat result | jq -e '.generatedAt' > /dev/null; then
    TIMESTAMP=$(cat result | jq -r '.generatedAt')
    # Basic check for ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
    if [[ "$TIMESTAMP" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]]; then
        echo "✓ generatedAt is in ISO 8601 format: $TIMESTAMP"
    else
        echo "✗ generatedAt is not in ISO 8601 format: $TIMESTAMP"
        exit 1
    fi
else
    echo "✗ generatedAt field missing"
    exit 1
fi

# Test 5: Check docs field exists
echo "Test 5: Checking docs field..."
if cat result | jq -e '.docs' > /dev/null; then
    echo "✓ docs field exists"
else
    echo "✗ docs field missing"
    exit 1
fi

echo ""
echo "All tests passed! ✅"
echo ""
echo "Sample output:"
cat result | jq '{schemaVersion, generatedAt, depsCount: .deps | length, firstDep: .deps[0]}' | head -30