#!/usr/bin/env bash
set -euo pipefail

# Test Suite: CI-Safe Reproducibility Verification
# Purpose: Orchestrate all reproducibility tests with proper cleanup and CI integration
# Method: Run all tests in sequence with comprehensive error handling and reporting
# Safety: No repository changes, CI-compatible execution

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly FLAKE_DIR="$SCRIPT_DIR"
readonly TEST_SUITE_NAME="reproducibility-verification-suite"

# Color output for better readability (with CI detection)
if [[ "${CI:-false}" == "true" || "${GITHUB_ACTIONS:-false}" == "true" ]]; then
    # Disable colors in CI environments
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly NC=''
else
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m' # No Color
fi

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Test configuration
declare -a TEST_SCRIPTS=(
    "test_nix_flake_metadata_consistency.sh"
    "test_lock_reproducibility_safe.sh"
    "test_serve_availability_pinned.sh"
)

declare -a TEST_DESCRIPTIONS=(
    "Nix Flake Metadata Consistency"
    "Safe Lock Reproducibility"
    "Serve Availability (Pinned Revision)"
)

# Global test results tracking
declare -A TEST_RESULTS=()
declare -A TEST_DURATIONS=()

# CI environment detection
detect_ci_environment() {
    local ci_detected=false
    local ci_system="none"

    if [[ "${CI:-false}" == "true" ]]; then
        ci_detected=true
        ci_system="generic"
    fi

    if [[ "${GITHUB_ACTIONS:-false}" == "true" ]]; then
        ci_detected=true
        ci_system="github-actions"
    fi

    if [[ "${GITLAB_CI:-false}" == "true" ]]; then
        ci_detected=true
        ci_system="gitlab-ci"
    fi

    if [[ -n "${BUILD_NUMBER:-}" ]]; then
        ci_detected=true
        ci_system="jenkins"
    fi

    echo "$ci_detected,$ci_system"
}

# Verify test environment and prerequisites
verify_test_environment() {
    log_info "Verifying test environment prerequisites"

    # Check required files
    if [[ ! -f "$FLAKE_DIR/flake.nix" ]]; then
        log_error "flake.nix not found: $FLAKE_DIR/flake.nix"
        return 1
    fi

    if [[ ! -f "$FLAKE_DIR/flake.lock" ]]; then
        log_error "flake.lock not found: $FLAKE_DIR/flake.lock"
        return 1
    fi

    # Check test scripts exist
    for script in "${TEST_SCRIPTS[@]}"; do
        local script_path="$FLAKE_DIR/$script"
        if [[ ! -f "$script_path" ]]; then
            log_error "Test script not found: $script_path"
            return 1
        fi

        if [[ ! -x "$script_path" ]]; then
            log_error "Test script not executable: $script_path"
            return 1
        fi
    done

    # Check required tools
    local required_tools=("nix" "jq" "grep" "sed")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found: $tool"
            return 1
        fi
    done

    log_success "Test environment verification complete"
    return 0
}

# Run a single test with timing and error handling
run_single_test() {
    local script_name="$1"
    local description="$2"
    local script_path="$FLAKE_DIR/$script_name"

    log_info "Running test: $description"
    log_info "Script: $script_name"

    local start_time
    start_time=$(date +%s)

    # Run test and capture output
    local test_output
    local test_exit_code

    if test_output=$("$script_path" 2>&1); then
        test_exit_code=0
    else
        test_exit_code=$?
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Store results
    TEST_RESULTS["$script_name"]="$test_exit_code"
    TEST_DURATIONS["$script_name"]="$duration"

    # Report results
    if [[ $test_exit_code -eq 0 ]]; then
        log_success "Test passed: $description (${duration}s)"
        return 0
    else
        log_error "Test failed: $description (${duration}s)"
        log_error "Exit code: $test_exit_code"

        # Show error output (limited in CI)
        if [[ "${CI:-false}" == "true" ]]; then
            echo "--- Test Output (last 20 lines) ---"
            echo "$test_output" | tail -20
            echo "--- End Test Output ---"
        else
            echo "--- Full Test Output ---"
            echo "$test_output"
            echo "--- End Test Output ---"
        fi

        return 1
    fi
}

# Generate test report
generate_test_report() {
    local total_tests="${#TEST_SCRIPTS[@]}"
    local passed_tests=0
    local failed_tests=0
    local total_duration=0

    echo
    log_info "=== REPRODUCIBILITY TEST SUITE REPORT ==="
    echo

    # Count results and calculate totals
    for script in "${TEST_SCRIPTS[@]}"; do
        local exit_code="${TEST_RESULTS[$script]}"
        local duration="${TEST_DURATIONS[$script]}"

        total_duration=$((total_duration + duration))

        if [[ $exit_code -eq 0 ]]; then
            passed_tests=$((passed_tests + 1))
        else
            failed_tests=$((failed_tests + 1))
        fi
    done

    # Summary
    log_info "Total Tests: $total_tests"
    log_info "Passed: $passed_tests"
    log_info "Failed: $failed_tests"
    log_info "Total Duration: ${total_duration}s"
    echo

    # Detailed results
    log_info "Detailed Results:"
    for i in "${!TEST_SCRIPTS[@]}"; do
        local script="${TEST_SCRIPTS[$i]}"
        local description="${TEST_DESCRIPTIONS[$i]}"
        local exit_code="${TEST_RESULTS[$script]}"
        local duration="${TEST_DURATIONS[$script]}"

        if [[ $exit_code -eq 0 ]]; then
            log_success "✓ $description (${duration}s)"
        else
            log_error "✗ $description (${duration}s) - Exit code: $exit_code"
        fi
    done

    echo

    # Final verdict
    if [[ $failed_tests -eq 0 ]]; then
        log_success "=== ALL TESTS PASSED ==="
        log_success "Fixed revision reproducibility verification: SUCCESS"
        log_success "Repository integrity maintained throughout testing"
        return 0
    else
        log_error "=== SOME TESTS FAILED ==="
        log_error "Reproducibility issues detected: $failed_tests/$total_tests tests failed"
        log_error "Review failed tests above for details"
        return 1
    fi
}

# CI-specific output formatting
format_ci_output() {
    local passed_tests="$1"
    local failed_tests="$2"
    local total_tests="$3"
    local total_duration="$4"

    local ci_info
    IFS=',' read -r ci_detected ci_system <<< "$(detect_ci_environment)"

    if [[ "$ci_detected" == "true" ]]; then
        log_info "CI Environment Detected: $ci_system"

        # GitHub Actions specific formatting
        if [[ "$ci_system" == "github-actions" ]]; then
            echo "::group::Reproducibility Test Suite"
        fi

        # Export test results for CI systems
        export REPRODUCIBILITY_TESTS_PASSED="$passed_tests"
        export REPRODUCIBILITY_TESTS_FAILED="$failed_tests"
        export REPRODUCIBILITY_TESTS_TOTAL="$total_tests"
        export REPRODUCIBILITY_TESTS_DURATION="$total_duration"
    fi
}

# Cleanup function for CI safety
cleanup_test_environment() {
    log_info "Performing test environment cleanup"

    # Check for any temporary files that might have been left behind
    local temp_files
    temp_files=$(find /tmp -name "opencode-lock-test-*" -type d 2>/dev/null || true)

    if [[ -n "$temp_files" ]]; then
        log_warning "Found temporary test directories, cleaning up:"
        echo "$temp_files" | while read -r dir; do
            log_info "Removing: $dir"
            rm -rf "$dir" || true
        done
    fi

    log_info "Cleanup complete"
}

# Main test suite execution
main() {
    local start_time
    start_time=$(date +%s)

    log_info "=== $TEST_SUITE_NAME ==="
    log_info "Testing Fixed Revision Reproducibility (CI-Safe)"

    # Detect CI environment
    local ci_info
    IFS=',' read -r ci_detected ci_system <<< "$(detect_ci_environment)"

    if [[ "$ci_detected" == "true" ]]; then
        log_info "Running in CI environment: $ci_system"
    else
        log_info "Running in local development environment"
    fi

    echo

    # Verify test environment
    if ! verify_test_environment; then
        log_error "Test environment verification failed"
        exit 1
    fi

    echo

    # Run all tests
    log_info "Executing reproducibility test suite..."
    echo

    local suite_passed=true

    for i in "${!TEST_SCRIPTS[@]}"; do
        local script="${TEST_SCRIPTS[$i]}"
        local description="${TEST_DESCRIPTIONS[$i]}"

        if ! run_single_test "$script" "$description"; then
            suite_passed=false
        fi

        echo
    done

    # Generate comprehensive report
    if ! generate_test_report; then
        suite_passed=false
    fi

    # CI-specific formatting
    if [[ "$ci_detected" == "true" ]]; then
        local total_tests="${#TEST_SCRIPTS[@]}"
        local passed_tests=0
        local failed_tests=0
        local total_duration=0

        # Calculate totals for CI output
        for script in "${TEST_SCRIPTS[@]}"; do
            local exit_code="${TEST_RESULTS[$script]}"
            local duration="${TEST_DURATIONS[$script]}"

            total_duration=$((total_duration + duration))

            if [[ $exit_code -eq 0 ]]; then
                passed_tests=$((passed_tests + 1))
            else
                failed_tests=$((failed_tests + 1))
            fi
        done

        format_ci_output "$passed_tests" "$failed_tests" "$total_tests" "$total_duration"

        if [[ "$ci_system" == "github-actions" ]]; then
            echo "::endgroup::"
        fi
    fi

    # Cleanup
    cleanup_test_environment

    # Final timing
    local end_time
    end_time=$(date +%s)
    local total_suite_duration=$((end_time - start_time))

    echo
    log_info "Suite completed in ${total_suite_duration}s"

    # Exit with appropriate code
    if [[ "$suite_passed" == "true" ]]; then
        log_success "Reproducibility verification suite: PASSED"
        exit 0
    else
        log_error "Reproducibility verification suite: FAILED"
        exit 1
    fi
}

# Ensure cleanup on script exit
trap cleanup_test_environment EXIT

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi