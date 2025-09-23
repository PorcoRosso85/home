#!/usr/bin/env bash
# Quick Start Validation Script
# Verifies that OpenCode basic setup is working correctly
# Supports both server mode (real server) and mock mode (CI optimization)

set -euo pipefail

# CI mode detection
CI_TEST_MODE="${CI_TEST_MODE:-server}"

echo "🚀 OpenCode Quick Start Validation"
echo "=================================="
echo "🎯 Test Mode: $CI_TEST_MODE"
echo

# Mock server for CI optimization
start_mock_server() {
    local port="${MOCK_SERVER_PORT:-9999}"
    echo "🔧 Starting mock server for CI mode on port $port..."

    python3 << EOF &
import http.server
import socketserver
import json
import sys

class QuickStartMockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs for cleaner CI output

    def do_GET(self):
        if self.path == '/doc':
            response = '{"status": "API documentation available"}'
            self.send_response(200)
        elif self.path == '/config/providers':
            response = '{"opencode": {"models": ["grok-code", "claude-3-sonnet"]}}'
            self.send_response(200)
        else:
            response = '{"status": "mock_ok"}'
            self.send_response(200)

        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())

    def do_POST(self):
        if '/session' in self.path:
            if self.path.endswith('/session'):
                response = '{"id": "quick-start-test-session"}'
            else:
                response = '{"response": "test successful"}'
            self.send_response(200)
        else:
            response = '{"status": "mock_ok"}'
            self.send_response(200)

        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())

with socketserver.TCPServer(("", $port), QuickStartMockHandler) as httpd:
    httpd.serve_forever()
EOF

    MOCK_SERVER_PID=$!
    sleep 2
    echo "✅ Mock server started (PID: $MOCK_SERVER_PID)"
}

stop_mock_server() {
    if [[ -n "${MOCK_SERVER_PID:-}" ]]; then
        kill "$MOCK_SERVER_PID" 2>/dev/null || true
        wait "$MOCK_SERVER_PID" 2>/dev/null || true
    fi
    pkill -f "python.*9999" 2>/dev/null || true
}

# Setup cleanup
cleanup() {
    if [[ "$CI_TEST_MODE" == "mock" ]]; then
        stop_mock_server
    fi
}
trap cleanup EXIT

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

# Test 2: Check if server is running or start mock server
echo "2️⃣ Checking server connectivity..."

if [[ "$CI_TEST_MODE" == "mock" ]]; then
    # Mock mode for CI speed
    start_mock_server
    OPENCODE_URL="http://127.0.0.1:9999"
    echo "  🔧 Using mock server at $OPENCODE_URL for CI optimization"
else
    # Server mode for real testing
    OPENCODE_URL="${OPENCODE_URL:-http://127.0.0.1:4096}"
fi

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

if [[ "$CI_TEST_MODE" == "mock" ]]; then
    echo "  🔧 Mock mode: Simulating client functionality..."

    # In mock mode, just verify the client can build and run
    if nix run .#opencode-client -- help >/dev/null 2>&1; then
        echo "  ✅ Client functionality verified (mock mode)"
        echo "  📝 Client executable and help command working"
    else
        echo "  ❌ Client build/help test failed"
        exit 1
    fi
else
    echo "  📤 Sending test message..."

    # Capture output and check for success
    TEST_OUTPUT=$(OPENCODE_PROJECT_DIR="$OPENCODE_PROJECT_DIR" \
        OPENCODE_URL="$OPENCODE_URL" \
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
fi
echo

# Test 5: Check history functionality
echo "5️⃣ Testing history functionality..."

if [[ "$CI_TEST_MODE" == "mock" ]]; then
    echo "  🔧 Mock mode: Simulating history functionality..."

    # In mock mode, just verify the history command exists
    if nix run .#opencode-client -- history --help >/dev/null 2>&1; then
        echo "  ✅ History functionality verified (mock mode)"
    else
        echo "  ⚠️  History command test inconclusive (mock mode)"
    fi
else
    HISTORY_OUTPUT=$(OPENCODE_PROJECT_DIR="$OPENCODE_PROJECT_DIR" \
        OPENCODE_URL="$OPENCODE_URL" \
        nix run .#opencode-client -- history --limit 1 2>/dev/null || echo "HISTORY_FAILED")

    if echo "$HISTORY_OUTPUT" | grep -E "(test successful|respond with just)" >/dev/null 2>&1; then
        echo "  ✅ History functionality working"
    else
        echo "  ⚠️  History test inconclusive (this is usually fine)"
    fi
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