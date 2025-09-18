#!/usr/bin/env bash
# Test runner script for KuzuDB Migration Framework

set -e

echo "🧪 KuzuDB Migration Test Runner"
echo "=============================="
echo ""

# Check if we're in a nix develop shell
if [ -z "$IN_NIX_SHELL" ]; then
    echo "⚠️  Not in nix shell. Running 'nix develop' first..."
    exec nix develop -c "$0" "$@"
fi

# Ensure dependencies are installed
echo "📦 Checking dependencies..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

echo "Installing/updating dependencies..."
uv sync

echo ""
echo "🧪 Running tests..."
echo ""

# Run pytest with verbose output
uv run pytest -v "$@"

echo ""
echo "✅ Test run complete!"