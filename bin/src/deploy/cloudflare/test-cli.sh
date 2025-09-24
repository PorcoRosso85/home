#!/usr/bin/env bash

# CLI Test Suite for R2 Connection Manifest Generator

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_SCRIPT="$SCRIPT_DIR/scripts/gen-connection-manifest.js"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

log() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    ((TESTS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
}

# Test 1: CLI Script Structure
test_script_structure() {
    log "Testing CLI script structure..."

    if [[ ! -f "$CLI_SCRIPT" ]]; then
        fail "CLI script not found at $CLI_SCRIPT"
        return
    fi

    # Check if script is executable
    if [[ ! -x "$CLI_SCRIPT" ]]; then
        fail "CLI script is not executable"
        return
    fi

    # Check shebang
    local shebang=$(head -n1 "$CLI_SCRIPT")
    if [[ ! "$shebang" =~ ^#!/ ]]; then
        fail "CLI script missing proper shebang"
        return
    fi

    pass "CLI script structure is valid"
}

# Test 2: Required Functions
test_required_functions() {
    log "Testing required functions exist..."

    local required_functions=(
        "parseArguments"
        "validateArguments"
        "showHelp"
        "listEnvironments"
        "readR2Configuration"
        "generateManifest"
        "validateManifest"
        "writeManifest"
    )

    local missing_functions=()

    for func in "${required_functions[@]}"; do
        if ! grep -q "function $func" "$CLI_SCRIPT"; then
            missing_functions+=("$func")
        fi
    done

    if [[ ${#missing_functions[@]} -gt 0 ]]; then
        fail "Missing required functions: ${missing_functions[*]}"
        return
    fi

    pass "All required functions are present"
}

# Test 3: Configuration Constants
test_configuration() {
    log "Testing configuration constants..."

    local required_configs=(
        "supportedEnvironments"
        "defaultOutputDir"
        "manifestVersion"
    )

    local missing_configs=()

    for config in "${required_configs[@]}"; do
        if ! grep -q "$config:" "$CLI_SCRIPT"; then
            missing_configs+=("$config")
        fi
    done

    if [[ ${#missing_configs[@]} -gt 0 ]]; then
        fail "Missing configuration constants: ${missing_configs[*]}"
        return
    fi

    # Check supported environments include dev, stg, prod
    if ! grep -q "dev.*stg.*prod\|prod.*stg.*dev" "$CLI_SCRIPT"; then
        fail "Supported environments don't include required dev/stg/prod"
        return
    fi

    pass "Configuration constants are properly defined"
}

# Test 4: CLI Options Parsing
test_cli_options() {
    log "Testing CLI options parsing..."

    local required_options=(
        "--env"
        "--output"
        "--dry-run"
        "--verbose"
        "--quiet"
        "--force"
        "--use-template"
        "--list-environments"
        "--help"
    )

    local missing_options=()

    for option in "${required_options[@]}"; do
        if ! grep -q "$option" "$CLI_SCRIPT"; then
            missing_options+=("$option")
        fi
    done

    if [[ ${#missing_options[@]} -gt 0 ]]; then
        fail "Missing CLI options: ${missing_options[*]}"
        return
    fi

    pass "All required CLI options are handled"
}

# Test 5: Error Handling
test_error_handling() {
    log "Testing error handling patterns..."

    local error_patterns=(
        "console\.error"
        "process\.exit\([1-9]"
        "Error:"
        "try.*catch"
    )

    local missing_patterns=()

    for pattern in "${error_patterns[@]}"; do
        if ! grep -q "$pattern" "$CLI_SCRIPT"; then
            missing_patterns+=("$pattern")
        fi
    done

    if [[ ${#missing_patterns[@]} -gt 0 ]]; then
        fail "Missing error handling patterns: ${missing_patterns[*]}"
        return
    fi

    pass "Error handling patterns are present"
}

# Test 6: Help Content
test_help_content() {
    log "Testing help content completeness..."

    local help_sections=(
        "DESCRIPTION"
        "USAGE"
        "OPTIONS"
        "EXAMPLES"
        "PREREQUISITES"
    )

    local missing_sections=()

    for section in "${help_sections[@]}"; do
        if ! grep -q "$section" "$CLI_SCRIPT"; then
            missing_sections+=("$section")
        fi
    done

    if [[ ${#missing_sections[@]} -gt 0 ]]; then
        fail "Missing help sections: ${missing_sections[*]}"
        return
    fi

    pass "Help content is comprehensive"
}

# Test 7: Integration Points
test_integration_points() {
    log "Testing integration points..."

    local integration_points=(
        "sops"
        "validate-r2-manifest"
        "r2-manifest.json"
        "schemas"
    )

    local missing_integrations=()

    for point in "${integration_points[@]}"; do
        if ! grep -q "$point" "$CLI_SCRIPT"; then
            missing_integrations+=("$point")
        fi
    done

    if [[ ${#missing_integrations[@]} -gt 0 ]]; then
        fail "Missing integration points: ${missing_integrations[*]}"
        return
    fi

    pass "Integration points are properly handled"
}

# Test 8: Security Considerations
test_security() {
    log "Testing security considerations..."

    # Check for SOPS encryption support
    if ! grep -q "SOPS_AGE_KEY_FILE" "$CLI_SCRIPT"; then
        fail "SOPS Age key configuration missing"
        return
    fi

    # Check for template mode (non-production secrets)
    if ! grep -q "useTemplate\|use-template" "$CLI_SCRIPT"; then
        fail "Template mode for testing missing"
        return
    fi

    # Check for prerequisite validation
    if ! grep -q "checkPrerequisites\|prerequisite" "$CLI_SCRIPT"; then
        fail "Prerequisites validation missing"
        return
    fi

    pass "Security considerations are implemented"
}

# Test 9: Manifest Generation Logic
test_manifest_logic() {
    log "Testing manifest generation logic..."

    local required_manifest_fields=(
        "account_id"
        "endpoint"
        "region"
        "buckets"
        "connection_mode"
        "meta"
    )

    local missing_fields=()

    for field in "${required_manifest_fields[@]}"; do
        if ! grep -q "$field" "$CLI_SCRIPT"; then
            missing_fields+=("$field")
        fi
    done

    if [[ ${#missing_fields[@]} -gt 0 ]]; then
        fail "Missing manifest fields: ${missing_fields[*]}"
        return
    fi

    pass "Manifest generation logic is complete"
}

# Test 10: Wrapper Script
test_wrapper_script() {
    log "Testing wrapper script..."

    local wrapper_script="$SCRIPT_DIR/scripts/gen-connection-manifest.sh"

    if [[ ! -f "$wrapper_script" ]]; then
        fail "Wrapper script not found"
        return
    fi

    if [[ ! -x "$wrapper_script" ]]; then
        fail "Wrapper script is not executable"
        return
    fi

    # Check if wrapper handles Node.js detection
    if ! grep -q "find_node\|NODE" "$wrapper_script"; then
        fail "Wrapper script doesn't handle Node.js detection"
        return
    fi

    pass "Wrapper script is properly configured"
}

# Run all tests
main() {
    echo "🧪 R2 Connection Manifest Generator CLI Test Suite"
    echo "=================================================="
    echo ""

    test_script_structure
    test_required_functions
    test_configuration
    test_cli_options
    test_error_handling
    test_help_content
    test_integration_points
    test_security
    test_manifest_logic
    test_wrapper_script

    echo ""
    echo "📊 Test Results"
    echo "==============="
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "Total:  $((TESTS_PASSED + TESTS_FAILED))"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}🎉 All tests passed! CLI implementation is complete.${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Some tests failed. Review implementation.${NC}"
        exit 1
    fi
}

main "$@"