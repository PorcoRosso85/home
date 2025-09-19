#!/usr/bin/env bash
# HTTP header standardization testing (RED phase)
# Tests current HTTP communication for standards compliance

set -euo pipefail

echo "=== HTTP Header Standardization Testing ==="
echo "Testing oc_session_http_* functions for standards compliance"
echo

# Source the session helper functions
source ./lib/session-helper.sh

# Test HTTP functions behavior
test_http_functions() {
    echo "📡 Testing HTTP Helper Functions"

    # Test oc_session_http_get
    echo "  Testing oc_session_http_get..."

    # Inspect the function to see current headers
    echo "    Current oc_session_http_get implementation:"
    type oc_session_http_get | grep -A 10 "curl" | sed 's/^/      /'

    # Test oc_session_http_post
    echo "  Testing oc_session_http_post..."

    echo "    Current oc_session_http_post implementation:"
    type oc_session_http_post | grep -A 15 "curl" | sed 's/^/      /'

    echo
}

# Mock server response test with header analysis
test_headers_with_mock() {
    echo "🔍 HTTP Headers Analysis"

    # Create a simple HTTP echo server for testing
    TEST_PORT="8899"
    TEST_DIR="/tmp/http_header_test_$$"
    mkdir -p "$TEST_DIR"

    # Start a simple HTTP server that echoes request headers
    cat > "$TEST_DIR/echo_server.py" << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import sys

class HeaderEchoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        headers = dict(self.headers)
        response = {
            "method": "GET",
            "path": self.path,
            "headers": headers
        }
        self.wfile.write(json.dumps(response, indent=2).encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()

        headers = dict(self.headers)
        response = {
            "method": "POST",
            "path": self.path,
            "headers": headers,
            "body": body
        }
        self.wfile.write(json.dumps(response, indent=2).encode())

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
with socketserver.TCPServer(("", PORT), HeaderEchoHandler) as httpd:
    print(f"Echo server running on port {PORT}")
    httpd.serve_forever()
EOF

    # Start echo server in background
    python3 "$TEST_DIR/echo_server.py" "$TEST_PORT" &
    ECHO_PID=$!

    # Wait for server to start
    sleep 2

    # Test current HTTP GET behavior
    echo "  🔍 Testing GET request headers:"
    if response=$(oc_session_http_get "http://127.0.0.1:$TEST_PORT/test" 2>/dev/null); then
        echo "    ✓ GET request successful"

        # Check for Accept header
        if echo "$response" | jq -e '.headers.Accept' >/dev/null 2>&1; then
            accept_header=$(echo "$response" | jq -r '.headers.Accept')
            echo "    ✅ Accept header present: $accept_header"
        else
            echo "    ❌ Accept header missing"
        fi

        # Check User-Agent and other standard headers
        if echo "$response" | jq -e '.headers["User-Agent"]' >/dev/null 2>&1; then
            user_agent=$(echo "$response" | jq -r '.headers["User-Agent"]')
            echo "    ℹ️  User-Agent: $user_agent"
        fi

    else
        echo "    ❌ GET request failed"
    fi

    # Test current HTTP POST behavior
    echo "  🔍 Testing POST request headers:"
    if response=$(oc_session_http_post "http://127.0.0.1:$TEST_PORT/test" '{"test": true}' 2>/dev/null); then
        echo "    ✓ POST request successful"

        # Check for Accept header
        if echo "$response" | jq -e '.headers.Accept' >/dev/null 2>&1; then
            accept_header=$(echo "$response" | jq -r '.headers.Accept')
            echo "    ✅ Accept header present: $accept_header"
        else
            echo "    ❌ Accept header missing"
        fi

        # Check Content-Type
        if echo "$response" | jq -e '.headers["Content-Type"]' >/dev/null 2>&1; then
            content_type=$(echo "$response" | jq -r '.headers["Content-Type"]')
            echo "    ✅ Content-Type header: $content_type"
        fi

    else
        echo "    ❌ POST request failed"
    fi

    # Cleanup
    kill $ECHO_PID 2>/dev/null || true
    rm -rf "$TEST_DIR"
    echo
}

# Standards compliance analysis
analyze_compliance() {
    echo "📋 HTTP Standards Compliance Analysis"

    echo "  🎯 Current Status:"
    echo "    - Content-Type: ✅ Set for POST requests (application/json)"
    echo "    - Accept: ❓ Need to verify presence"
    echo "    - User-Agent: ❓ Default curl behavior"
    echo

    echo "  🎯 Desired Improvements:"
    echo "    - Accept: application/json (explicit JSON preference)"
    echo "    - Better server compatibility (OpenAPI compliance)"
    echo "    - Network debugging friendliness"
    echo

    echo "  🎯 Implementation Strategy:"
    echo "    - Add Accept header to oc_session_http_get"
    echo "    - Ensure no breaking changes to existing API calls"
    echo "    - Maintain backward compatibility"
}

# Run all tests
test_http_functions
test_headers_with_mock
analyze_compliance

echo "=== Test Summary ==="
echo "This test evaluates current HTTP header usage and identifies"
echo "opportunities for standards compliance improvement."
echo ""
echo "🔄 Expected Findings:"
echo "   - POST requests likely have Content-Type: application/json"
echo "   - GET requests likely missing explicit Accept header"
echo "   - Room for improvement in API standards compliance"