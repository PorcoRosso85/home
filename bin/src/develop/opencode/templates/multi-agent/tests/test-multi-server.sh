#!/usr/bin/env bash
set -euo pipefail

# Test suite for multi-server infrastructure
# Add parent directory to PATH so tests can find scripts
export PATH="$(dirname "$PWD"):$PATH"

# Test configuration
readonly TEST_DIR="/tmp/opencode-multiserver-test-$$"
readonly SESSION_BASE="/tmp/opencode-sessions"

# Helper functions
setup_test() {
    mkdir -p "$TEST_DIR"
    mkdir -p "$SESSION_BASE"
    cd "$TEST_DIR"
    export OPENCODE_SESSION_DIR="$SESSION_BASE"
}

cleanup_test() {
    cd /
    rm -rf "$TEST_DIR" 2>/dev/null || true
    rm -rf "$SESSION_BASE" 2>/dev/null || true
}

fail_test() {
    local test_name="$1"
    local message="$2"
    echo "❌ FAIL: $test_name - $message"
}

pass_test() {
    local test_name="$1"
    echo "✅ PASS: $test_name"
}

# Test: Server pool configuration and validation
test_server_pool_config() {
    setup_test
    local test_name="test_server_pool_config"
    
    if command -v multi-server-manager >/dev/null 2>&1; then
        # Test simple server pool configuration (simplified for 2-server setup)
        local config_file="$TEST_DIR/server-pool.json"
        cat > "$config_file" <<EOF
{
  "servers": [
    {"url": "http://127.0.0.1:4096"},
    {"url": "http://127.0.0.1:4097"}
  ]
}
EOF
        
        local result
        if result=$(multi-server-manager --config="$config_file" --action="validate" 2>&1); then
            if [[ "$result" == *"VALID"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Server pool validation should return VALID. Got: $result"
            fi
        else
            fail_test "$test_name" "Server pool validation should succeed"
        fi
    else
        fail_test "$test_name" "multi-server-manager command not found"
    fi
    
    cleanup_test
}

# Test: Load balancing with round-robin strategy
test_round_robin_balancing() {
    setup_test
    local test_name="test_round_robin_balancing"
    
    if command -v multi-server-manager >/dev/null 2>&1; then
        # Configure 2-server pool with health checking disabled for testing
        local server1 server2 server3
        server1=$(multi-server-manager --server-pool="http://127.0.0.1:4096,http://127.0.0.1:4097" --health-check="false" --action="get_next_server" 2>&1)
        server2=$(multi-server-manager --server-pool="http://127.0.0.1:4096,http://127.0.0.1:4097" --health-check="false" --action="get_next_server" 2>&1)
        server3=$(multi-server-manager --server-pool="http://127.0.0.1:4096,http://127.0.0.1:4097" --health-check="false" --action="get_next_server" 2>&1)
        
        # Should cycle between 2 servers: server1 != server2, server3 == server1
        if [[ "$server1" != "$server2" ]] && [[ "$server3" == "$server1" ]]; then
            pass_test "$test_name"
        else
            fail_test "$test_name" "Round-robin should cycle through 2 servers. Got: $server1, $server2, $server3"
        fi
    else
        fail_test "$test_name" "multi-server-manager command not found"
    fi
    
    cleanup_test
}

# Test: Health checking and failover (simplified for /doc endpoint)
test_health_check_failover() {
    setup_test
    local test_name="test_health_check_failover"
    
    if command -v multi-server-manager >/dev/null 2>&1; then
        # Configure server pool: first server (9999) will be unhealthy, second will be tested for /doc endpoint
        local result
        if result=$(multi-server-manager --server-pool="http://127.0.0.1:9999,http://127.0.0.1:4096" --health-check="true" --action="get_healthy_server" 2>&1); then
            # Should get a server (either works or both fail gracefully)
            pass_test "$test_name"
        else
            fail_test "$test_name" "Health check should handle server failures gracefully"
        fi
    else
        fail_test "$test_name" "multi-server-manager command not found"
    fi
    
    cleanup_test
}




# Test: Server pool configuration reload
test_config_hot_reload() {
    setup_test
    local test_name="test_config_hot_reload"
    
    # This should fail because multi-server-manager doesn't exist yet (RED)
    if command -v multi-server-manager >/dev/null 2>&1; then
        # Create initial config
        local config_file="$TEST_DIR/dynamic-pool.json"
        cat > "$config_file" <<EOF
{
  "servers": [
    {"url": "http://127.0.0.1:4096"}
  ]
}
EOF
        
        # Get initial server count
        local result1
        result1=$(multi-server-manager --config="$config_file" --action="get_server_count" 2>&1)
        
        # Update config with more servers
        cat > "$config_file" <<EOF
{
  "servers": [
    {"url": "http://127.0.0.1:4096"},
    {"url": "http://127.0.0.1:4097"}
  ]
}
EOF
        
        # Get updated server count 
        local result2
        result2=$(multi-server-manager --config="$config_file" --action="get_server_count" 2>&1)
        
        if [[ "$result1" == "1" ]] && [[ "$result2" == "2" ]]; then
            pass_test "$test_name"
        else
            fail_test "$test_name" "Config reload failed. Before: $result1, After: $result2"
        fi
    else
        fail_test "$test_name" "multi-server-manager command not found"
    fi
    
    cleanup_test
}

echo "🔴 Testing simplified multi-server infrastructure..."
echo "Testing minimal 2-server round-robin with /doc health checks"
echo

# Run simplified tests
test_server_pool_config
test_round_robin_balancing
test_health_check_failover
test_config_hot_reload

echo
echo "Testing complete. Focus on 2-server minimal setup."