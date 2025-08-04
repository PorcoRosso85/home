#!/usr/bin/env bash
# Test script to verify the external flake can be evaluated
# This works around git tracking issues during development

set -euo pipefail

echo "Testing external flake evaluation..."
echo "===================================="
echo ""

# Create a temporary directory for testing
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📁 Creating temporary test directory: $TEMP_DIR"
cd "$TEMP_DIR"

# Copy the flake.nix
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/flake.nix" .

# Create a minimal git repo to satisfy flake requirements
git init
git add flake.nix
git commit -m "Initial commit"

echo ""
echo "🔍 Evaluating flake outputs..."

# Test that we can evaluate the flake
echo "Running: nix eval .#apps.x86_64-linux --apply builtins.attrNames"
if nix eval .#apps.x86_64-linux --apply builtins.attrNames; then
    echo "✅ Flake evaluation successful!"
    echo ""
    echo "Available apps:"
    nix eval .#apps.x86_64-linux --apply builtins.attrNames --json | jq -r '.[]' | sed 's/^/  - /'
else
    echo "❌ Flake evaluation failed"
    echo "Trying to get more error details..."
    nix flake check || true
    exit 1
fi

echo ""
echo "🧪 Testing flake metadata..."
nix flake metadata

echo ""
echo "✅ All tests passed! The external flake is valid and can be used as a dependency."