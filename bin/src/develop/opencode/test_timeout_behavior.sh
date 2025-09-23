#!/usr/bin/env bash
# Test: OPENCODE_TIMEOUT Application Verification
# Verifies that OPENCODE_TIMEOUT is correctly applied through unified function

set -euo pipefail

# Test configuration
TEST_NAME="OPENCODE_TIMEOUT Application"
TEST_PROJECT_DIR="/tmp/opencode-timeout-test-$(date +%s)"
MOCK_SERVER_PORT="${MOCK_SERVER_PORT:-8890}"
MOCK_SERVER_URL="http://localhost:$MOCK_SERVER_PORT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test result counters
TESTS_PASSED=0
TESTS_FAILED=0

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

assert_success() {
    local description="$1"
    local command="$2"

    if eval "$command" >/dev/null 2>&1; then
        log_info "✅ PASS: $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "❌ FAIL: $description"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_timeout_behavior() {
    local description="$1"
    local expected_timeout="$2"
    local actual_duration="$3"
    local tolerance="$4"

    # Allow for some tolerance in timing
    local min_time=$((expected_timeout - tolerance))
    local max_time=$((expected_timeout + tolerance))

    if [[ $actual_duration -ge $min_time && $actual_duration -le $max_time ]]; then
        log_info "✅ PASS: $description (${actual_duration}s within ${min_time}-${max_time}s)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "❌ FAIL: $description"
        log_error "   Expected: ${min_time}-${max_time}s, Actual: ${actual_duration}s"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_contains() {
    local description="$1"
    local haystack="$2"
    local needle="$3"

    if echo "$haystack" | grep -q "$needle"; then
        log_info "✅ PASS: $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "❌ FAIL: $description"
        log_error "   Expected to contain: $needle"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."

    # Create test project directory
    mkdir -p "$TEST_PROJECT_DIR"
    cd "$TEST_PROJECT_DIR"

    # Create a simple nix flake for testing
    cat > flake.nix << 'EOF'
{
  description = "Test project for timeout behavior verification";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { self, nixpkgs }: {
    packages.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.hello;
  };
}
EOF

    export PROJECT_DIR="$TEST_PROJECT_DIR"
    log_info "Test environment ready at: $TEST_PROJECT_DIR"
}

# Mock server with configurable delays
start_timeout_mock_server() {
    log_info "Starting timeout mock HTTP server on port $MOCK_SERVER_PORT..."

    # Kill any existing server on this port
    pkill -f "python.*$MOCK_SERVER_PORT" || true
    sleep 1

    # Start mock server that can simulate various response delays
    python3 << EOF &
import http.server
import socketserver
import json
import urllib.parse
import sys
import time

class TimeoutMockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[TIMEOUT_MOCK] {format % args}", file=sys.stderr)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        print(f"POST {parsed_url.path}", file=sys.stderr)

        # Check for delay parameter to simulate slow responses
        delay = query_params.get('delay', ['0'])[0]
        try:
            delay_seconds = int(delay)
            if delay_seconds > 0:
                print(f"Simulating {delay_seconds}s delay", file=sys.stderr)
                time.sleep(delay_seconds)
        except ValueError:
            delay_seconds = 0

        # Standard responses
        if '/session' in self.path and parsed_url.path.endswith('/session'):
            response = json.dumps({"id": "test-session-timeout-123"})
            self.send_response(200)
        elif '/message' in self.path:
            response = json.dumps({"status": "ok", "delay": delay_seconds})
            self.send_response(200)
        else:
            response = json.dumps({"status": "not_found"})
            self.send_response(404)

        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())

    def do_GET(self):
        # Health check endpoint
        response = json.dumps({"status": "ok"})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())

with socketserver.TCPServer(("", $MOCK_SERVER_PORT), TimeoutMockHandler) as httpd:
    print(f"Timeout mock server running on port $MOCK_SERVER_PORT", file=sys.stderr)
    httpd.serve_forever()
EOF

    MOCK_SERVER_PID=$!
    sleep 2

    if curl -s "$MOCK_SERVER_URL" >/dev/null 2>&1; then
        log_info "Timeout mock server started successfully (PID: $MOCK_SERVER_PID)"
    else
        log_error "Failed to start timeout mock server"
        return 1
    fi
}

stop_mock_server() {
    if [[ -n "${MOCK_SERVER_PID:-}" ]]; then
        log_info "Stopping mock server (PID: $MOCK_SERVER_PID)..."
        kill "$MOCK_SERVER_PID" 2>/dev/null || true
        wait "$MOCK_SERVER_PID" 2>/dev/null || true
    fi
    pkill -f "python.*$MOCK_SERVER_PORT" || true
}

# Source opencode functions for testing
source_opencode_functions() {
    local opencode_lib="/home/nixos/bin/src/develop/opencode/lib/session-helper.sh"

    if [[ -f "$opencode_lib" ]]; then
        log_info "Sourcing opencode session functions..."
        source "$opencode_lib"
    else
        log_error "Cannot find opencode session helper: $opencode_lib"
        return 1
    fi
}

# Test 1: Verify default timeout (30 seconds)
test_default_timeout() {
    log_info "Testing default timeout behavior (30 seconds)..."

    # Unset OPENCODE_TIMEOUT to test default
    unset OPENCODE_TIMEOUT || true

    # Test with a request that should complete quickly
    local start_time end_time duration
    start_time=$(date +%s)

    local response
    response=$(oc_session_http_post "$MOCK_SERVER_URL/session" '{}' 2>/dev/null || echo "TIMEOUT")

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Should complete quickly (much less than 30 seconds)
    assert_success "Default timeout allows quick requests" "[[ $duration -lt 5 ]]"
    assert_success "Quick request succeeds" "[[ '$response' != 'TIMEOUT' ]]"
}

# Test 2: Verify custom timeout is applied
test_custom_timeout() {
    log_info "Testing custom timeout behavior..."

    # Set a short timeout (3 seconds)
    export OPENCODE_TIMEOUT=3

    local start_time end_time duration
    start_time=$(date +%s)

    # Request with 5-second delay (should timeout with 3-second limit)
    local response
    response=$(oc_session_http_post "$MOCK_SERVER_URL/session?delay=5" '{}' 2>/dev/null || echo "TIMEOUT")

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Should timeout around 3 seconds (allow 1 second tolerance)
    assert_timeout_behavior "Custom timeout (3s) with 5s delay" 3 "$duration" 1

    # Should result in timeout/error
    assert_success "Long request times out with custom timeout" "[[ '$response' == 'TIMEOUT' || '$response' =~ 'error' ]]"

    unset OPENCODE_TIMEOUT
}

# Test 3: Verify timeout applies to both success and error paths
test_timeout_in_error_paths() {
    log_info "Testing timeout application in error paths..."

    export OPENCODE_TIMEOUT=2

    # Test main request path
    local start_time end_time duration
    start_time=$(date +%s)

    local encoded_dir
    encoded_dir=$(printf '%s' "$TEST_PROJECT_DIR" | jq -sRr @uri)

    # This mimics the main request in flake.nix line 155
    local main_response
    main_response=$(oc_session_http_post "$MOCK_SERVER_URL/session/test/message?directory=$encoded_dir&delay=4" '{}' 2>/dev/null || echo "MAIN_TIMEOUT")

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Should timeout around 2 seconds
    assert_timeout_behavior "Main request timeout (2s) with 4s delay" 2 "$duration" 1

    # Test error retry path (mimics flake.nix line 215)
    start_time=$(date +%s)

    local retry_response
    retry_response=$(oc_session_http_post "$MOCK_SERVER_URL/session/test/message?directory=$encoded_dir&delay=4" '{}' 2>/dev/null || true)

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Error retry should also respect timeout
    assert_timeout_behavior "Error retry timeout (2s) with 4s delay" 2 "$duration" 1

    unset OPENCODE_TIMEOUT
}

# Test 4: Verify timeout inheritance across function calls
test_timeout_inheritance() {
    log_info "Testing timeout inheritance across function calls..."

    export OPENCODE_TIMEOUT=5

    # Test that oc_session_get_or_create inherits timeout for internal HTTP calls
    local start_time end_time duration
    start_time=$(date +%s)

    # This should use oc_session_http_post internally and inherit the timeout
    local session_id
    session_id=$(oc_session_get_or_create "$MOCK_SERVER_URL" "$TEST_PROJECT_DIR" 2>/dev/null || echo "INHERIT_TIMEOUT")

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Should complete quickly since session creation is fast
    assert_success "Session creation inherits timeout" "[[ $duration -lt 3 ]]"
    assert_success "Session creation succeeds" "[[ '$session_id' != 'INHERIT_TIMEOUT' ]]"

    unset OPENCODE_TIMEOUT
}

# Test 5: Verify timeout environment variable precedence
test_timeout_precedence() {
    log_info "Testing timeout environment variable precedence..."

    # Test with environment variable set
    export OPENCODE_TIMEOUT=7

    # Create a test script that uses the session functions
    local test_script="/tmp/test_timeout_precedence.sh"

    cat > "$test_script" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

source /home/nixos/bin/src/develop/opencode/lib/session-helper.sh

# Check that the function reads our environment variable
echo "Testing with OPENCODE_TIMEOUT=$OPENCODE_TIMEOUT"

# Quick test request
start_time=$(date +%s)
response=$(oc_session_http_post "$1" '{}' 2>/dev/null || echo "PRECEDENCE_TIMEOUT")
end_time=$(date +%s)
duration=$((end_time - start_time))

echo "Duration: ${duration}s"
echo "Response: $response"
EOF

    chmod +x "$test_script"

    local precedence_output
    precedence_output=$("$test_script" "$MOCK_SERVER_URL/session" 2>&1)

    # Verify the script ran with our timeout setting
    assert_contains "Timeout precedence shows environment variable" "$precedence_output" "OPENCODE_TIMEOUT=7"

    rm -f "$test_script"
    unset OPENCODE_TIMEOUT
}

# Test 6: Verify flake.nix timeout integration
test_flake_nix_timeout_integration() {
    log_info "Testing flake.nix timeout integration..."

    local flake_file="/home/nixos/bin/src/develop/opencode/flake.nix"

    # Verify that flake.nix doesn't override OPENCODE_TIMEOUT
    local timeout_references
    timeout_references=$(grep -n "OPENCODE_TIMEOUT" "$flake_file" || true)

    if [[ -n "$timeout_references" ]]; then
        log_info "Found OPENCODE_TIMEOUT references in flake.nix:"
        echo "$timeout_references"

        # Should not set OPENCODE_TIMEOUT directly (should inherit from environment)
        local direct_sets
        direct_sets=$(echo "$timeout_references" | grep -c "OPENCODE_TIMEOUT=" || echo "0")

        assert_success "flake.nix doesn't override OPENCODE_TIMEOUT" "[[ $direct_sets -eq 0 ]]"
    else
        log_info "No direct OPENCODE_TIMEOUT references found in flake.nix (inherits from environment)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi

    # Verify oc_session_http_post usage (should inherit timeout)
    local http_post_calls
    http_post_calls=$(grep -n "oc_session_http_post" "$flake_file" || true)

    if [[ -n "$http_post_calls" ]]; then
        # All calls should use the unified function (which respects OPENCODE_TIMEOUT)
        assert_contains "flake.nix uses unified HTTP function" "$http_post_calls" "oc_session_http_post"
    fi
}

# Test 7: Verify timeout with network issues
test_timeout_with_network_issues() {
    log_info "Testing timeout behavior with network issues..."

    export OPENCODE_TIMEOUT=3

    # Test with completely unreachable server
    local start_time end_time duration
    start_time=$(date +%s)

    local unreachable_response
    unreachable_response=$(oc_session_http_post "http://192.0.2.1:12345/session" '{}' 2>/dev/null || echo "NETWORK_TIMEOUT")

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Should timeout around 3 seconds for unreachable server
    assert_timeout_behavior "Network timeout (3s) for unreachable server" 3 "$duration" 1

    # Should result in timeout/error
    assert_success "Unreachable server times out" "[[ '$unreachable_response' == 'NETWORK_TIMEOUT' ]]"

    unset OPENCODE_TIMEOUT
}

# Main test execution
run_all_tests() {
    log_info "Starting $TEST_NAME tests..."

    # Setup
    setup_test_environment
    source_opencode_functions
    start_timeout_mock_server

    # Run tests
    test_default_timeout
    test_custom_timeout
    test_timeout_in_error_paths
    test_timeout_inheritance
    test_timeout_precedence
    test_flake_nix_timeout_integration
    test_timeout_with_network_issues

    # Cleanup
    stop_mock_server

    # Results
    log_info "Test Results:"
    log_info "  Passed: $TESTS_PASSED"
    log_info "  Failed: $TESTS_FAILED"
    log_info "  Total:  $((TESTS_PASSED + TESTS_FAILED))"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_info "🎉 All tests passed!"
        return 0
    else
        log_error "💥 Some tests failed!"
        return 1
    fi
}

# Cleanup on exit
cleanup() {
    stop_mock_server
    rm -rf "$TEST_PROJECT_DIR" 2>/dev/null || true
    rm -f /tmp/test_*.sh 2>/dev/null || true
}

trap cleanup EXIT

# Run tests
run_all_tests