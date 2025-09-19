#!/usr/bin/env bash
# Output separation testing for client stdout/stderr policy (RED phase)
# Tests current vs. desired output behavior for machine readability

set -euo pipefail

echo "=== Output Separation Testing ==="
echo "Testing client output policy for machine readability"
echo

# Create test session directory
TEST_DIR="/tmp/test_output_separation_$$"
mkdir -p "$TEST_DIR"

# Mock successful server response for testing
mock_test() {
    local test_name="$1"
    echo "Testing: $test_name"

    # Capture stdout and stderr separately
    local stdout_file="$TEST_DIR/stdout.txt"
    local stderr_file="$TEST_DIR/stderr.txt"

    # Run client and capture outputs
    cd "$TEST_DIR"
    if OPENCODE_PROJECT_DIR="$TEST_DIR" timeout 10 \
       nix run /home/nixos/bin/src/develop/opencode#opencode-client -- 'test output format' \
       >"$stdout_file" 2>"$stderr_file"; then

        echo "  ✓ Client executed successfully"

        # Analyze current stdout content
        echo "  📄 Current stdout content:"
        if [[ -s "$stdout_file" ]]; then
            local stdout_lines=$(wc -l < "$stdout_file")
            local has_reply_label=$(grep -c '\[client\] reply:' "$stdout_file" || true)
            local has_json=$(grep -c '^{' "$stdout_file" || true)

            echo "    Lines: $stdout_lines"
            echo "    Contains [client] reply:: $has_reply_label"
            echo "    Contains JSON: $has_json"

            # Show first few lines
            echo "    Preview:"
            head -3 "$stdout_file" | sed 's/^/      /'
        else
            echo "    (empty)"
        fi

        # Analyze current stderr content
        echo "  📄 Current stderr content:"
        if [[ -s "$stderr_file" ]]; then
            local stderr_lines=$(wc -l < "$stderr_file")
            local has_client_logs=$(grep -c '\[client\]' "$stderr_file" || true)

            echo "    Lines: $stderr_lines"
            echo "    Contains [client] logs: $has_client_logs"

            # Show client logs only
            echo "    Client logs:"
            grep '\[client\]' "$stderr_file" | sed 's/^/      /' || echo "      (none)"
        else
            echo "    (empty)"
        fi

        # Evaluate against ideal output policy
        echo "  🎯 Output Policy Evaluation:"

        # Check if stdout contains only response content
        if grep -q '\[client\]' "$stdout_file"; then
            echo "    ❌ STDOUT contaminated with client logs"
            echo "       Ideal: stdout should contain only AI response"
        else
            echo "    ✅ STDOUT clean (no client logs)"
        fi

        # Check if stderr contains client metadata
        if grep -q '\[client\]' "$stderr_file"; then
            echo "    ✅ STDERR contains client logs (good)"
        else
            echo "    ⚠️  STDERR missing client logs"
        fi

        # Machine readability test
        echo "  🤖 Machine Readability Test:"
        if jq . "$stdout_file" >/dev/null 2>&1; then
            echo "    ✅ STDOUT is valid JSON"
        elif [[ $(wc -l < "$stdout_file") -eq 1 ]] && ! grep -q '\[client\]' "$stdout_file"; then
            echo "    ✅ STDOUT is clean single response"
        else
            echo "    ❌ STDOUT is not machine-friendly"
            echo "       Contains mixed content that requires parsing"
        fi

    else
        echo "  ❌ Client execution failed"
        echo "  This may be due to server not running or network issues"
        echo "  To run this test:"
        echo "    1. Start server: nix run nixpkgs#opencode -- serve --port 4096"
        echo "    2. Re-run this test"
        return 1
    fi

    echo
}

# Test current behavior
mock_test "Current Output Format"

# Cleanup
rm -rf "$TEST_DIR"

echo "=== Test Summary ==="
echo "This test demonstrates the current output mixing behavior."
echo ""
echo "💡 Desired Improvement:"
echo "   STDOUT: Pure AI response text only"
echo "   STDERR: All [client] logs and metadata"
echo ""
echo "📈 Benefits:"
echo "   - Clean machine processing: response = \$(opencode-client 'query')"
echo "   - Unix pipeline friendly: opencode-client 'query' | jq ."
echo "   - Clear separation of data vs. logs"
echo ""
echo "🔄 Implementation needed:"
echo "   - Move '[client] reply:' label to stderr"
echo "   - Keep pure response content in stdout"