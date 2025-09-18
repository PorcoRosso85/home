#!/usr/bin/env bash

# nixd LSP Verification Script
# This script performs automated verification of nixd LSP integration
# Run within nix develop shell for best results

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Log file for detailed output
LOG_FILE="nixd_verification_$(date +%Y%m%d_%H%M%S).log"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$LOG_FILE"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1" | tee -a "$LOG_FILE"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    ((TOTAL_TESTS++))
    log_info "Running test: $test_name"
    
    if output=$(eval "$test_command" 2>&1); then
        if echo "$output" | grep -q "$expected_pattern"; then
            log_success "$test_name"
            echo "$output" >> "$LOG_FILE"
            return 0
        else
            log_error "$test_name - Expected pattern '$expected_pattern' not found"
            echo "Output: $output" >> "$LOG_FILE"
            return 1
        fi
    else
        log_error "$test_name - Command failed"
        echo "Error output: $output" >> "$LOG_FILE"
        return 1
    fi
}

run_test_no_pattern() {
    local test_name="$1"
    local test_command="$2"
    
    ((TOTAL_TESTS++))
    log_info "Running test: $test_name"
    
    if output=$(eval "$test_command" 2>&1); then
        log_success "$test_name"
        echo "$output" >> "$LOG_FILE"
        return 0
    else
        log_error "$test_name - Command failed"
        echo "Error output: $output" >> "$LOG_FILE"
        return 1
    fi
}

# Main verification function
main() {
    log_info "Starting nixd LSP verification"
    log_info "Log file: $LOG_FILE"
    log_info "Timestamp: $(date)"
    
    # Test 1: Check if we're in nix develop environment
    if [[ -n "${IN_NIX_SHELL:-}" ]]; then
        log_success "Running in nix develop environment"
    else
        log_warning "Not in nix develop environment - some tests may fail"
    fi
    
    # Test 2: Check nixd binary availability
    run_test "nixd binary availability" "which nixd" "/nix/store"
    
    # Test 3: Check nixd version
    run_test "nixd version check" "nixd --version" "nixd"
    
    # Test 4: Check nixd executable permissions
    if command -v nixd &> /dev/null; then
        nixd_path=$(which nixd)
        if [[ -x "$nixd_path" ]]; then
            log_success "nixd executable permissions"
        else
            log_error "nixd executable permissions - nixd is not executable"
        fi
    else
        log_error "nixd executable permissions - nixd not found"
    fi
    
    # Test 5: Check environment variables
    if [[ -n "${NIXD_PATH:-}" ]]; then
        log_success "NIXD_PATH environment variable set: $NIXD_PATH"
    else
        log_warning "NIXD_PATH environment variable not set"
    fi
    
    if [[ -n "${RUST_ANALYZER_PATH:-}" ]]; then
        log_success "RUST_ANALYZER_PATH environment variable set: $RUST_ANALYZER_PATH"
    else
        log_warning "RUST_ANALYZER_PATH environment variable not set"
    fi
    
    # Test 6: Project build test
    log_info "Testing project build..."
    if cargo check --quiet; then
        log_success "Project build check"
    else
        log_error "Project build check - cargo check failed"
    fi
    
    # Test 7: Create a simple test Nix file for LSP testing
    log_info "Creating test Nix file..."
    cat > test_nixd_verification.nix << 'EOF'
{
  description = "Test flake for nixd verification";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  
  outputs = { self, nixpkgs }: {
    testFunction = arg: "Hello ${arg}";
    testVariable = 42;
    testList = [ 1 2 3 ];
  };
}
EOF
    
    if [[ -f "test_nixd_verification.nix" ]]; then
        log_success "Test Nix file created"
    else
        log_error "Test Nix file creation failed"
    fi
    
    # Test 8: LSP integration test (nix-only mode)
    log_info "Testing LSP integration with nix-only mode..."
    export LSIF_ENABLED_LANGUAGES=nix
    export RUST_LOG=info
    
    # Build the project first if not already built
    if [[ ! -f "target/debug/lsif" ]]; then
        log_info "Building project for LSP test..."
        if ! cargo build --bin lsif; then
            log_error "Project build failed - cannot test LSP integration"
            return 1
        fi
    fi
    
    # Run LSP test with timeout
    log_info "Running LSP integration test (timeout: 30s)..."
    if timeout 30s ./target/debug/lsif index --force > lsp_test_output.log 2>&1; then
        # Check for success patterns in the output
        if grep -q "Successfully warmed up LSP client for nix" lsp_test_output.log; then
            log_success "LSP client warmup successful"
        else
            log_warning "LSP client warmup - success message not found in output"
        fi
        
        if grep -q "nixd LSP startup validated" lsp_test_output.log; then
            log_success "nixd LSP startup validation"
        else
            log_warning "nixd LSP startup validation - validation message not found"
        fi
        
        # Check for fallback usage (should not happen in successful case)
        if grep -q "Using Fallback Indexer" lsp_test_output.log; then
            log_warning "LSP integration - Fallback indexer was used"
        else
            log_success "No fallback indexer usage detected"
        fi
        
    else
        log_error "LSP integration test - command timed out or failed"
        if [[ -f "lsp_test_output.log" ]]; then
            log_info "LSP test output (last 20 lines):"
            tail -20 lsp_test_output.log | tee -a "$LOG_FILE"
        fi
    fi
    
    # Test 9: Symbol extraction verification
    if [[ -f "export.json" ]]; then
        log_info "Checking symbol extraction..."
        symbol_count=$(jq '[.[] | select(.type == "definition")] | length' export.json 2>/dev/null || echo "0")
        if [[ "$symbol_count" -gt 0 ]]; then
            log_success "Symbol extraction - Found $symbol_count definitions"
        else
            log_warning "Symbol extraction - No definitions found in export.json"
        fi
    else
        log_warning "Symbol extraction - export.json not found"
    fi
    
    # Test 10: Resource usage check
    log_info "Checking for resource usage patterns..."
    if [[ -f "lsp_test_output.log" ]]; then
        if grep -q "error\|panic\|fatal" lsp_test_output.log; then
            log_warning "Resource usage - Error patterns found in output"
        else
            log_success "Resource usage - No critical errors detected"
        fi
    fi
    
    # Cleanup
    log_info "Cleaning up test files..."
    rm -f test_nixd_verification.nix lsp_test_output.log
    
    # Summary
    echo ""
    log_info "=== VERIFICATION SUMMARY ==="
    log_info "Total tests: $TOTAL_TESTS"
    log_info "Passed: $PASSED_TESTS"
    log_info "Failed: $FAILED_TESTS"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "All tests passed! nixd verification successful."
        log_info "Detailed log saved to: $LOG_FILE"
        return 0
    else
        log_error "Some tests failed. Check the log for details: $LOG_FILE"
        return 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi