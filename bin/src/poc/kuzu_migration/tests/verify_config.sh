#!/usr/bin/env bash
# Script to verify pytest configuration

set -e

echo "🔍 Verifying pytest configuration for kuzu-migrate"
echo "================================================="
echo ""

# Function to run pytest commands
run_pytest() {
    local cmd="$1"
    local description="$2"
    
    echo "📋 $description"
    echo "   Command: $cmd"
    echo ""
    
    if command -v pytest &> /dev/null; then
        eval "$cmd" || true
    else
        echo "   ⚠️  pytest not found in PATH. Run this script inside nix develop shell."
    fi
    echo ""
    echo "---"
    echo ""
}

# Check if we're in the tests directory
if [[ ! -f "pytest.ini" ]]; then
    echo "⚠️  Please run this script from the tests/ directory"
    exit 1
fi

# Run various pytest commands to verify configuration
run_pytest "pytest --version" "Checking pytest version"

run_pytest "pytest --collect-only" "Collecting all tests"

run_pytest "pytest --collect-only e2e/internal/" "Collecting internal tests only"

run_pytest "pytest --collect-only e2e/external/" "Collecting external tests only"

run_pytest "pytest --collect-only -m internal" "Collecting tests marked as 'internal'"

run_pytest "pytest --collect-only -m external" "Collecting tests marked as 'external'"

run_pytest "pytest --markers" "Listing available markers"

echo "✅ Configuration verification complete!"
echo ""
echo "📝 Notes:"
echo "   - pytest.ini is located in: $(pwd)/pytest.ini"
echo "   - Alternative config in: $(dirname $(pwd))/pyproject.toml"
echo "   - Run actual tests with: pytest"
echo "   - Run with coverage: pytest --cov=kuzu_migration --cov-report=html"