#!/usr/bin/env bash
# Test helper functions for OpenCode tests
# Common functions to avoid duplication across test files

set -euo pipefail

# Source the main session helper functions
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$TESTS_DIR")"
source "$REPO_ROOT/lib/session-helper.sh"

# Convert absolute path to project key (same logic as main library)
# This ensures tests use the same path conversion logic
test_path_to_project_key() {
    local abs_path="$1"
    oc_session_project_key "$abs_path"
}

# Generate expected session file path for testing
# Usage: test_get_expected_session_file URL WORKDIR
test_get_expected_session_file() {
    local url="$1"
    local workdir="$2"
    
    url=$(oc_session_normalize_url "$url")
    local hostport
    hostport=$(oc_session_derive_host_port "$url")
    
    local abs_path
    abs_path=$(cd "$workdir" && pwd)
    local project_name
    project_name=$(oc_session_project_key "$abs_path")
    
    local session_base
    session_base=$(oc_session_get_base_dir)
    echo "$session_base/$hostport/$project_name.session"
}

# Create isolated test environment
test_setup_environment() {
    local test_state_dir="/tmp/opencode_test_$$"
    mkdir -p "$test_state_dir"
    export XDG_STATE_HOME="$test_state_dir"
    echo "$test_state_dir"
}

# Clean up test environment
test_cleanup_environment() {
    local test_state_dir="$1"
    rm -rf "$test_state_dir"
}

# Create test directory with specific name
test_create_directory() {
    local base_dir="$1"
    local dir_name="$2"
    local test_dir="$base_dir/$dir_name"
    mkdir -p "$test_dir"
    echo "$test_dir"
}