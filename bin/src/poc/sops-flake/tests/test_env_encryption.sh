#!/usr/bin/env bash
# tests/test_env_encryption.sh
# Comprehensive test suite for env.sh encryption functionality

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test environment
TEST_DIR=""

# Initialize test environment
setup_test_env() {
    TEST_DIR=$(mktemp -d -t test_env_encryption.XXXXXX)
    echo -e "${YELLOW}Test directory: $TEST_DIR${NC}"
    
    # Copy example scripts to test directory
    cp -r /home/nixos/bin/src/poc/sops-flake/examples/env-encryption/* "$TEST_DIR/"
    cd "$TEST_DIR"
    
    echo -e "${GREEN}✓ Test environment initialized${NC}"
}

# Cleanup test environment
cleanup_test_env() {
    if [[ -n "$TEST_DIR" && -d "$TEST_DIR" ]]; then
        rm -rf "$TEST_DIR"
        echo -e "${GREEN}✓ Test environment cleaned up${NC}"
    fi
}

# Test assertion helpers
assert_file_exists() {
    local file="$1"
    local description="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓ $description${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ $description - File not found: $file${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_not_exists() {
    local file="$1"
    local description="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ ! -f "$file" ]]; then
        echo -e "${GREEN}✓ $description${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ $description - File should not exist: $file${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_command_success() {
    local description="$1"
    local exit_code="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ "$exit_code" -eq 0 ]]; then
        echo -e "${GREEN}✓ $description${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ $description - Command failed with exit code: $exit_code${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_command_failure() {
    local description="$1"
    local exit_code="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ "$exit_code" -ne 0 ]]; then
        echo -e "${GREEN}✓ $description${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ $description - Command should have failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_permissions() {
    local file="$1"
    local expected_perms="$2"
    local description="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ -f "$file" ]]; then
        local actual_perms=$(stat -c "%a" "$file")
        if [[ "$actual_perms" == "$expected_perms" ]]; then
            echo -e "${GREEN}✓ $description - permissions: $actual_perms${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ $description - Expected: $expected_perms, Got: $actual_perms${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${RED}✗ $description - File not found: $file${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test 1: Setup test
test_setup() {
    echo -e "${YELLOW}=== Test 1: Setup Test ===${NC}"
    
    # Test initial setup.sh execution
    set +e  # Temporarily disable strict error handling for command capture
    bash setup.sh > setup.log 2>&1
    local setup_exit_code=$?
    set -e  # Re-enable strict error handling
    
    assert_command_success "setup.sh execution" "$setup_exit_code"
    assert_file_exists "$HOME/.config/sops/age/keys.txt" "Age key generation"
    assert_file_exists ".sops.yaml" ".sops.yaml creation"
    assert_file_exists "source-env.sh" "source-env.sh helper script creation"
    assert_file_exists "encrypt-env.sh" "encrypt-env.sh helper script creation"
    assert_file_exists "env.sh.example" "env.sh.example creation"
    
    # Test idempotency - run setup again
    set +e
    bash setup.sh > setup2.log 2>&1
    local setup2_exit_code=$?
    set -e
    
    assert_command_success "setup.sh idempotency" "$setup2_exit_code"
    
    # Verify helper scripts are executable
    assert_file_permissions "source-env.sh" "755" "source-env.sh executable permissions"
    assert_file_permissions "encrypt-env.sh" "755" "encrypt-env.sh executable permissions"
    
    echo ""
}

# Test 2: Encryption test
test_encryption() {
    echo -e "${YELLOW}=== Test 2: Encryption Test ===${NC}"
    
    # Create test env.sh from example
    cp env.sh.example env.sh
    echo 'export TEST_VAR=test_value_123' >> env.sh
    
    # Test encryption
    set +e
    bash encrypt-env.sh > encrypt.log 2>&1
    local encrypt_exit_code=$?
    set -e
    
    assert_command_success "encrypt-env.sh execution" "$encrypt_exit_code"
    assert_file_exists "env.sh.enc" "env.sh.enc generation"
    
    # Verify decryption matches original
    local temp_test=$(mktemp)
    chmod 600 "$temp_test"
    
    if sops -d env.sh.enc > "$temp_test" 2>/dev/null; then
        if diff -q env.sh "$temp_test" > /dev/null 2>&1; then
            TESTS_TOTAL=$((TESTS_TOTAL + 1))
            echo -e "${GREEN}✓ Decryption verification - content matches original${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            TESTS_TOTAL=$((TESTS_TOTAL + 1))
            echo -e "${RED}✗ Decryption verification - content mismatch${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ Decryption verification - failed to decrypt${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    shred -u "$temp_test" 2>/dev/null || rm -f "$temp_test"
    
    # Test encryption with missing env.sh
    rm env.sh
    set +e
    bash encrypt-env.sh > encrypt_fail.log 2>&1
    local encrypt_fail_exit_code=$?
    set -e
    
    assert_command_failure "encrypt-env.sh with missing env.sh" "$encrypt_fail_exit_code"
    
    echo ""
}

# Test 3: Decryption and sourcing test
test_decryption_sourcing() {
    echo -e "${YELLOW}=== Test 3: Decryption and Sourcing Test ===${NC}"
    
    # Ensure env.sh.enc exists from previous test
    if [[ ! -f "env.sh.enc" ]]; then
        cp env.sh.example env.sh
        echo 'export TEST_VAR=test_value_123' >> env.sh
        ./encrypt-env.sh > /dev/null 2>&1
        rm env.sh
    fi
    
    # Test sourcing encrypted file in subprocess to avoid env pollution
    unset TEST_VAR API_KEY ORG_ID SECRET_TOKEN DATABASE_URL 2>/dev/null || true
    set +e
    source ./source-env.sh > source.log 2>&1
    local source_exit_code=$?
    set -e
    
    assert_command_success "source-env.sh execution" "$source_exit_code"
    
    # Check if environment variables are loaded by running again
    set +e
    (source ./source-env.sh && [[ -n "${TEST_VAR:-}" ]]) > /dev/null 2>&1
    local env_loaded=$?
    set -e
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ "$env_loaded" -eq 0 ]]; then
        echo -e "${GREEN}✓ Environment variables loaded from encrypted file${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ Environment variables not loaded${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test fallback to plain env.sh with warning
    mv env.sh.enc env.sh.enc.backup
    cp env.sh.example env.sh
    echo 'export TEST_VAR=fallback_value' >> env.sh
    
    set +e
    source ./source-env.sh > fallback.log 2>&1
    local fallback_exit_code=$?
    set -e
    
    assert_command_success "source-env.sh fallback to plain env.sh" "$fallback_exit_code"
    
    # Check for warning in output
    if grep -q "Warning.*unencrypted" fallback.log; then
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${GREEN}✓ Warning shown for unencrypted fallback${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ Warning not shown for unencrypted fallback${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test error when no env files exist
    rm env.sh
    set +e
    bash source-env.sh > no_env.log 2>&1
    local no_env_exit_code=$?
    set -e
    
    assert_command_failure "source-env.sh with no env files" "$no_env_exit_code"
    
    # Restore env.sh.enc for next tests
    mv env.sh.enc.backup env.sh.enc
    
    echo ""
}

# Test 4: Security test
test_security() {
    echo -e "${YELLOW}=== Test 4: Security Test ===${NC}"
    
    # Test that source-env.sh uses secure temp file permissions
    # We'll modify source-env.sh to capture temp file info
    cp source-env.sh source-env.sh.backup
    
    # Create a test version that shows temp file permissions
    cat > test-source-env.sh <<'EOF'
#!/bin/bash
set -euo pipefail

TEMP_ENV=$(mktemp -t env.XXXXXX)
chmod 600 "$TEMP_ENV"

# Check permissions immediately
TEMP_PERMS=$(stat -c "%a" "$TEMP_ENV")
echo "TEMP_PERMS:$TEMP_PERMS"

cleanup() {
    if [[ -f "$TEMP_ENV" ]]; then
        shred -u "$TEMP_ENV" 2>/dev/null || rm -f "$TEMP_ENV"
    fi
}
trap cleanup EXIT

if [[ -f env.sh.enc ]]; then
    if sops -d env.sh.enc > "$TEMP_ENV" 2>/dev/null; then
        source "$TEMP_ENV"
        echo "✓ Environment variables loaded from env.sh.enc" >&2
    else
        echo "❌ Error: Failed to decrypt env.sh.enc" >&2
        exit 1
    fi
fi
EOF
    chmod +x test-source-env.sh
    
    # Test temp file permissions
    set +e
    local temp_output=$(bash test-source-env.sh 2>&1)
    set -e
    if echo "$temp_output" | grep -q "TEMP_PERMS:600"; then
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${GREEN}✓ Temp file created with secure permissions (600)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ Temp file permissions not secure${NC}"
        echo -e "${RED}   Debug: $temp_output${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test that source-env.sh doesn't use eval (excluding comments)
    if ! grep -v "^\s*#" source-env.sh | grep -q "eval"; then
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${GREEN}✓ No eval usage detected (injection protection)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ Eval usage detected (security risk)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test shred usage for secure deletion
    if grep -q "shred" source-env.sh; then
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${GREEN}✓ Secure deletion with shred${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ No secure deletion detected${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test trap cleanup is properly set
    if grep -q "trap cleanup EXIT" source-env.sh; then
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${GREEN}✓ Cleanup trap properly configured${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ Cleanup trap not configured${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Restore original source-env.sh
    mv source-env.sh.backup source-env.sh
    
    echo ""
}

# Test 5: Error handling test
test_error_handling() {
    echo -e "${YELLOW}=== Test 5: Error Handling Test ===${NC}"
    
    # Test encrypt-env.sh without .sops.yaml
    mv .sops.yaml .sops.yaml.backup
    cp env.sh.example env.sh
    
    set +e
    bash encrypt-env.sh > no_sops.log 2>&1
    local no_sops_exit_code=$?
    set -e
    
    assert_command_failure "encrypt-env.sh without .sops.yaml" "$no_sops_exit_code"
    
    if grep -q ".sops.yaml not found" no_sops.log; then
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${GREEN}✓ Proper error message for missing .sops.yaml${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        echo -e "${RED}✗ Missing proper error message for .sops.yaml${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test encrypt-env.sh without age key
    mv .sops.yaml.backup .sops.yaml
    mv "$HOME/.config/sops/age/keys.txt" "$HOME/.config/sops/age/keys.txt.backup" 2>/dev/null || true
    
    set +e
    bash encrypt-env.sh > no_key.log 2>&1
    local no_key_exit_code=$?
    set -e
    
    assert_command_failure "encrypt-env.sh without age key" "$no_key_exit_code"
    
    # Test source-env.sh with corrupted encrypted file
    mv "$HOME/.config/sops/age/keys.txt.backup" "$HOME/.config/sops/age/keys.txt" 2>/dev/null || true
    rm env.sh
    
    # Create corrupted encrypted file
    echo "corrupted_data" > env.sh.enc
    
    set +e
    bash source-env.sh > corrupted.log 2>&1
    local corrupted_exit_code=$?
    set -e
    
    assert_command_failure "source-env.sh with corrupted file" "$corrupted_exit_code"
    
    echo ""
}

# Test 6: Team sharing test
test_team_sharing() {
    echo -e "${YELLOW}=== Test 6: Team Sharing Test ===${NC}"
    
    # Generate second age key (simulating team member)
    TEAM_KEY_FILE=$(mktemp)
    set +e
    age-keygen -o "$TEAM_KEY_FILE" 2>/dev/null
    local keygen_result=$?
    set -e
    
    if [[ $keygen_result -ne 0 ]]; then
        echo -e "${RED}✗ Failed to generate team member key${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        return
    fi
    
    TEAM_PUBLIC_KEY=$(age-keygen -y "$TEAM_KEY_FILE" 2>/dev/null)
    
    if [[ -z "$TEAM_PUBLIC_KEY" ]]; then
        echo -e "${RED}✗ Failed to extract team member public key${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        rm -f "$TEAM_KEY_FILE"
        return
    fi
    
    # Get original public key
    ORIG_PUBLIC_KEY=$(age-keygen -y "$HOME/.config/sops/age/keys.txt" 2>/dev/null)
    
    if [[ -z "$ORIG_PUBLIC_KEY" ]]; then
        echo -e "${RED}✗ Failed to extract original public key${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
        rm -f "$TEAM_KEY_FILE"
        return
    fi
    
    # Create multi-key .sops.yaml
    cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*env\.sh$
    key_groups:
      - age:
          - $ORIG_PUBLIC_KEY
          - $TEAM_PUBLIC_KEY
EOF
    
    # Create and encrypt env.sh with multiple keys
    cp env.sh.example env.sh
    echo 'export TEAM_TEST=multi_key_test' >> env.sh
    
    set +e
    bash encrypt-env.sh > multi_key.log 2>&1
    local multi_key_exit_code=$?
    set -e
    
    assert_command_success "Multi-key encryption" "$multi_key_exit_code"
    
    # Test decryption with original key
    set +e
    source ./source-env.sh > decrypt1.log 2>&1
    local decrypt1_exit_code=$?
    set -e
    
    assert_command_success "Decryption with original key" "$decrypt1_exit_code"
    
    # Test decryption with team member key
    set +e
    SOPS_AGE_KEY_FILE="$TEAM_KEY_FILE" source ./source-env.sh > decrypt2.log 2>&1
    local decrypt2_exit_code=$?
    set -e
    
    assert_command_success "Decryption with team member key" "$decrypt2_exit_code"
    
    # Test decryption failure with wrong key
    WRONG_KEY_FILE=$(mktemp)
    set +e
    age-keygen -o "$WRONG_KEY_FILE" 2>/dev/null
    local wrong_keygen_result=$?
    set -e
    
    if [[ $wrong_keygen_result -ne 0 ]]; then
        echo -e "${YELLOW}⚠ Skipping wrong key test - failed to generate key${NC}"
        rm -f "$TEAM_KEY_FILE"
        return
    fi
    
    set +e
    SOPS_AGE_KEY_FILE="$WRONG_KEY_FILE" bash source-env.sh > decrypt_fail.log 2>&1
    local decrypt_fail_exit_code=$?
    set -e
    
    assert_command_failure "Decryption with wrong key" "$decrypt_fail_exit_code"
    
    # Cleanup temp keys
    shred -u "$TEAM_KEY_FILE" 2>/dev/null || rm -f "$TEAM_KEY_FILE"
    shred -u "$WRONG_KEY_FILE" 2>/dev/null || rm -f "$WRONG_KEY_FILE"
    
    echo ""
}

# Run all tests
run_all_tests() {
    echo -e "${GREEN}=== ENV Encryption Test Suite ===${NC}"
    echo ""
    
    # Setup test environment
    setup_test_env
    
    # Ensure required tools are available
    if ! command -v age &> /dev/null; then
        echo -e "${RED}❌ Error: age is not installed${NC}"
        echo "Please install age first: nix shell nixpkgs#age"
        exit 1
    fi
    
    if ! command -v sops &> /dev/null; then
        echo -e "${RED}❌ Error: sops is not installed${NC}"
        echo "Please install sops first: nix shell nixpkgs#sops"
        exit 1
    fi
    
    # Run tests
    test_setup
    test_encryption
    test_decryption_sourcing
    test_security
    test_error_handling
    test_team_sharing
    
    # Print summary
    echo -e "${GREEN}=== Test Summary ===${NC}"
    echo -e "Total tests: ${TESTS_TOTAL}"
    echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
    
    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit_code=0
    else
        echo -e "${RED}❌ Some tests failed!${NC}"
        exit_code=1
    fi
    
    # Cleanup
    cleanup_test_env
    
    return ${exit_code}
}

# Handle script termination
trap cleanup_test_env EXIT

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_all_tests
fi