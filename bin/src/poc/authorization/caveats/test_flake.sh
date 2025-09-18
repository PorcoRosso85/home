#!/usr/bin/env bash
# Test: flake.nixが正しくSpiceDBを提供することを確認

set -euo pipefail

echo "Testing flake.nix configuration..."

# Test 1: flake.nixが存在し、有効なNix flakeであること
if ! nix flake metadata . &>/dev/null; then
    echo "❌ FAIL: flake.nix is not a valid Nix flake"
    exit 1
fi
echo "✅ PASS: Valid Nix flake"

# Test 2: SpiceDBパッケージが利用可能であること
if ! nix build .#spicedb --no-link &>/dev/null; then
    echo "❌ FAIL: SpiceDB package is not available"
    exit 1
fi
echo "✅ PASS: SpiceDB package is available"

# Test 3: 開発シェルが利用可能であること
if ! nix develop --command echo "dev shell works" &>/dev/null; then
    echo "❌ FAIL: Development shell is not available"
    exit 1
fi
echo "✅ PASS: Development shell is available"

# Test 4: SpiceDBバイナリが開発シェルで利用可能であること
if ! nix develop --command which spicedb &>/dev/null; then
    echo "❌ FAIL: SpiceDB binary is not available in dev shell"
    exit 1
fi
echo "✅ PASS: SpiceDB binary is available in dev shell"

echo "🎉 All tests passed!"