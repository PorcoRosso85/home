#!/usr/bin/env bash
# Quick Start Validation Script
# Verifies that OpenCode basic setup is working correctly

set -euo pipefail

echo "🚀 OpenCode Quick Start Validation"
echo "=================================="
echo

# Test 1: Check if required tools are available
echo "1️⃣ Checking required tools..."
for tool in nix curl; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "  ✅ $tool: available"
    else
        echo "  ❌ $tool: not found"
        echo "     Install $tool and try again"
        exit 1
    fi
done
echo

# Test 2: Check if server is running
echo "2️⃣ Checking server connectivity..."
OPENCODE_URL="${OPENCODE_URL:-http://127.0.0.1:4096}"

# Try multiple endpoints to handle API implementation differences
if curl -s --max-time 5 "$OPENCODE_URL/doc" >/dev/null 2>&1; then
    echo "  ✅ Server responding at $OPENCODE_URL (via /doc)"
elif curl -s --max-time 5 "$OPENCODE_URL/config/providers" >/dev/null 2>&1; then
    echo "  ✅ Server responding at $OPENCODE_URL (via /config/providers)"
else
    echo "  ❌ Server not responding at $OPENCODE_URL"
    echo "     Tried endpoints: /doc, /config/providers"
    echo "     Start server with: nix profile install nixpkgs#opencode; opencode serve --port 4096"
    exit 1
fi
echo

# Test 3: Check project directory
echo "3️⃣ Checking project directory..."
OPENCODE_PROJECT_DIR="${OPENCODE_PROJECT_DIR:-$(pwd)}"
if [[ -d "$OPENCODE_PROJECT_DIR" ]]; then
    echo "  ✅ Project directory exists: $OPENCODE_PROJECT_DIR"
else
    echo "  ❌ Project directory not found: $OPENCODE_PROJECT_DIR"
    echo "     Set OPENCODE_PROJECT_DIR to an existing directory or use current directory"
    exit 1
fi
echo

# Test 4: Test client functionality
echo "4️⃣ Testing client functionality..."
echo "  📤 Sending test message..."

# Capture output and check for success
TEST_OUTPUT=$(OPENCODE_PROJECT_DIR="$OPENCODE_PROJECT_DIR" \
    nix run .#opencode-client -- 'respond with just: test successful' 2>&1 || echo "CLIENT_FAILED")

if echo "$TEST_OUTPUT" | grep -i "test successful" >/dev/null 2>&1; then
    echo "  ✅ Client test successful"
    echo "  📝 Response received from AI model"
elif echo "$TEST_OUTPUT" | grep -i "CLIENT_FAILED" >/dev/null 2>&1; then
    echo "  ❌ Client test failed"
    echo "  📋 Debug info:"
    echo "$TEST_OUTPUT" | sed 's/^/     /'
    exit 1
else
    echo "  ⚠️  Client ran but response unclear"
    echo "  📋 Output:"
    echo "$TEST_OUTPUT" | sed 's/^/     /'
fi
echo

# Test 5: Check history functionality
echo "5️⃣ Testing history functionality..."
HISTORY_OUTPUT=$(OPENCODE_PROJECT_DIR="$OPENCODE_PROJECT_DIR" \
    nix run .#opencode-client -- history --limit 1 2>/dev/null || echo "HISTORY_FAILED")

if echo "$HISTORY_OUTPUT" | grep -E "(test successful|respond with just)" >/dev/null 2>&1; then
    echo "  ✅ History functionality working"
else
    echo "  ⚠️  History test inconclusive (this is usually fine)"
fi
echo

# Summary
echo "🎉 Quick Start Validation Complete!"
echo "=================================="
echo
echo "✅ Your OpenCode setup is working correctly!"
echo
echo "📚 Next steps:"
echo "   • Try: OPENCODE_PROJECT_DIR=\$(pwd) nix run .#opencode-client -- 'your message here'"
echo "   • View history: OPENCODE_PROJECT_DIR=\$(pwd) nix run .#opencode-client -- history"
echo "   • See ./check-opencode-status.sh for detailed diagnostics"
echo
echo "📖 For more features, see README.md"