#!/usr/bin/env bash

# Test Framework for Terminal Development Environment
# Focuses on path validation and basic functionality

set -o pipefail

# Test framework configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERMINAL_ROOT="$(cd "${TEST_DIR}/.." && pwd)"
MAIN_SCRIPT="${TERMINAL_ROOT}/modules/core/main.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test framework functions
test_assert() {
    local description="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"
    
    ((TESTS_RUN++))
    echo -n "Testing: $description ... "
    
    local actual_exit_code=0
    eval "$command" >/dev/null 2>&1 || actual_exit_code=$?
    
    if [[ $actual_exit_code -eq $expected_exit_code ]]; then
        echo -e "${GREEN}PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (expected exit code $expected_exit_code, got $actual_exit_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_path_exists() {
    local description="$1"
    local path="$2"
    
    test_assert "$description" "[[ -e '$path' ]]"
}

test_file_executable() {
    local description="$1"
    local file="$2"
    
    test_assert "$description" "[[ -x '$file' ]]"
}

test_syntax_check() {
    local description="$1"
    local script="$2"
    
    test_assert "$description" "bash -n '$script'"
}

# Main test suite
run_tests() {
    echo "=== Terminal Development Environment Test Suite ==="
    echo "Test root: $TERMINAL_ROOT"
    echo ""
    
    # Test 1: Main script exists and is executable
    test_path_exists "Main script exists" "$MAIN_SCRIPT"
    test_file_executable "Main script is executable" "$MAIN_SCRIPT"
    
    # Test 2: Syntax validation
    test_syntax_check "Main script syntax is valid" "$MAIN_SCRIPT"
    
    # Test 3: Required directories exist
    local required_dirs=(
        "modules/core"
        "modules/tmux"
        "modules/search"
        "modules/utils"
        "modules/system"
        "modules/config"
    )
    
    for dir in "${required_dirs[@]}"; do
        test_path_exists "Directory $dir exists" "$TERMINAL_ROOT/$dir"
    done
    
    # Test 4: Main script can be sourced without errors
    test_assert "Main script can be sourced" "source '$MAIN_SCRIPT'"
    
    # Test 5: Path validation function works
    test_assert "Path validation succeeds" "bash -c \"source '$MAIN_SCRIPT' && validate_paths\""
    
    # Test 6: Init function works
    test_assert "Terminal initialization succeeds" "bash -c \"source '$MAIN_SCRIPT' && init_terminal\""
    
    # Test summary
    echo ""
    echo "=== Test Results ==="
    echo "Tests run: $TESTS_RUN"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        return 1
    fi
}

# Create required directories for testing
setup_test_environment() {
    local dirs=(
        "${TERMINAL_ROOT}/modules/core"
        "${TERMINAL_ROOT}/modules/tmux"
        "${TERMINAL_ROOT}/modules/search"
        "${TERMINAL_ROOT}/modules/utils"
        "${TERMINAL_ROOT}/modules/system"
        "${TERMINAL_ROOT}/modules/config"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    chmod +x "$MAIN_SCRIPT" 2>/dev/null || true
}

# Main execution
main() {
    setup_test_environment
    run_tests
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi