#!/usr/bin/env bash
set -euo pipefail

# Test: flake description contains essential information
echo "Testing flake description completeness..."

# Get flake description from nix flake metadata
FLAKE_METADATA=$(nix flake metadata --no-warn-dirty 2>/dev/null)

# Extract the description line
DESCRIPTION=$(echo "$FLAKE_METADATA" | grep "Description:" | sed 's/^Description: *//')

echo "Current description: $DESCRIPTION"

# Required keywords that must appear in description or early output
REQUIRED_KEYWORDS=(
    "HTTP"
    "server"
    "opencode"
    "template"
    "multi-agent"
    "pre-auth"
)

FAILED_KEYWORDS=()

for keyword in "${REQUIRED_KEYWORDS[@]}"; do
    if ! echo "$DESCRIPTION" | grep -i "$keyword" >/dev/null; then
        FAILED_KEYWORDS+=("$keyword")
    fi
done

if [ ${#FAILED_KEYWORDS[@]} -gt 0 ]; then
    echo "❌ FAIL: Missing required keywords in flake description: ${FAILED_KEYWORDS[*]}"
    echo "Expected: All keywords should be visible in 'nix flake metadata' description"
    echo "Actual: Keywords missing from flake description"
    exit 1
else
    echo "✅ PASS: All required keywords found in flake description"
fi