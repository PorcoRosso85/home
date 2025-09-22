#!/usr/bin/env bash

# Test to verify clear usage separation documentation exists
# This test should FAIL initially (RED state) until proper documentation is created

set -euo pipefail

echo "=== Testing Usage Documentation Clarity ==="

# Test 1: Check if README.md exists
if [[ ! -f "README.md" ]]; then
    echo "❌ FAIL: README.md does not exist"
    exit 1
fi

# Test 2: Check for "Basic Usage" section that doesn't require nix develop
if ! grep -q "Basic Usage" README.md; then
    echo "❌ FAIL: 'Basic Usage' section not found in README.md"
    exit 1
fi

# Test 3: Check for "Development Usage" section
if ! grep -q "Development Usage" README.md; then
    echo "❌ FAIL: 'Development Usage' section not found in README.md"
    exit 1
fi

# Test 4: Help section should mention profile install approach
if ! grep -A 30 "Help" README.md | grep -q "nix profile install nixpkgs#opencode"; then
    echo "❌ FAIL: Help section doesn't mention profile install approach"
    exit 1
fi

# Test 5: Basic Usage should include direct HTTP API examples with curl
if ! grep -A 50 "Basic Usage" README.md | grep -q "curl.*session"; then
    echo "❌ FAIL: Basic Usage section doesn't include curl session examples"
    exit 1
fi

# Test 6: Development Usage should mention 'nix develop'
if ! grep -A 10 "Development Usage" README.md | grep -q "nix develop"; then
    echo "❌ FAIL: Development Usage section doesn't mention 'nix develop'"
    exit 1
fi

# Test 7: Should clarify when nix develop is NOT needed  
if ! grep -q "No.*nix develop.*needed\|without.*nix develop\|nix develop.*not.*required" README.md; then
    echo "❌ FAIL: Documentation doesn't clarify when 'nix develop' is not needed"
    exit 1
fi

# Test 8: Should have clear distinction between the two approaches
if ! grep -q "Choose.*Usage.*Approach\|Which.*Approach.*Should\|Two.*ways" README.md; then
    echo "❌ FAIL: Documentation doesn't provide clear guidance on choosing between approaches"
    exit 1
fi

echo "✅ All documentation clarity tests passed!"
echo "Usage separation is clearly documented."