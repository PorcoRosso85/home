#!/bin/bash
# Test suite for the enhanced plaintext detection script
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Setup test environment
setup() {
    mkdir -p test_secrets
    rm -f test_secrets/* .secrets-allowlist 2>/dev/null || true
}

cleanup() {
    rm -rf test_secrets .secrets-allowlist 2>/dev/null || true
}

# Test assertion helpers
assert_exit_code() {
    local expected=$1
    local actual=$2
    local test_name="$3"

    if [[ $actual -eq $expected ]]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name (expected: $expected, got: $actual)"
        ((FAILED++))
    fi
}

assert_contains() {
    local output="$1"
    local expected="$2"
    local test_name="$3"

    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name (output missing: '$expected')"
        echo "Actual output: $output"
        ((FAILED++))
    fi
}

# Test 1: Detects plaintext secrets
test_detects_plaintext() {
    setup
    echo "api_key: plain_secret_value" > test_secrets/test.yaml

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) || exit_code=$?

    assert_exit_code 1 ${exit_code:-0} "detects plaintext in secrets"
    assert_contains "$output" "test_secrets/test.yaml" "lists plaintext file"
    assert_contains "$output" "sops -e -i" "shows fix command"
    cleanup
}

# Test 2: Allows ENC encrypted content
test_allows_enc_encrypted() {
    setup
    cat > test_secrets/encrypted.yaml <<EOF
api_key: ENC[AES256_GCM,data:xxxx,iv:yyyy,tag:zzzz,type:str]
database_url: ENC[AES256_GCM,data:aaaa,iv:bbbb,tag:cccc,type:str]
EOF

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "allows ENC[] encrypted content"
    assert_contains "$output" "SUCCESS" "shows success message"
    cleanup
}

# Test 3: Allows SOPS with MAC
test_allows_sops_with_mac() {
    setup
    cat > test_secrets/sops.yaml <<EOF
sops:
    kms: []
    gcp_kms: []
    azure_kv: []
    hc_vault: []
    age:
        - recipient: age1xxx
          enc: xxx
    lastmodified: "2023-01-01T00:00:00Z"
    mac: ENC[AES256_GCM,data:xxxx]
    version: 3.7.3
api_key: ENC[AES256_GCM,data:yyyy]
EOF

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "allows sops+mac structure"
    assert_contains "$output" "SUCCESS" "shows success message"
    cleanup
}

# Test 4: Rejects sops without MAC
test_rejects_sops_without_mac() {
    setup
    cat > test_secrets/incomplete.yaml <<EOF
sops:
    version: 3.7.3
api_key: some_value
EOF

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) || exit_code=$?

    assert_exit_code 1 ${exit_code:-0} "rejects sops without mac"
    assert_contains "$output" "incomplete.yaml" "lists incomplete file"
    cleanup
}

# Test 5: Excludes example files
test_excludes_examples() {
    setup
    echo "api_key: example_value" > test_secrets/app.yaml.example
    echo "secret: another_example" > test_secrets/config.json.example

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "excludes .example files"
    assert_contains "$output" "SUCCESS" "shows success for excluded files"
    cleanup
}

# Test 6: Respects allowlist
test_respects_allowlist() {
    setup
    echo "test_secrets/test-data.yaml" > .secrets-allowlist
    echo "# Comment pattern" >> .secrets-allowlist
    echo "test_secrets/*.tmp" >> .secrets-allowlist

    echo "test: plain_value" > test_secrets/test-data.yaml
    echo "temp: plain_temp" > test_secrets/temp.tmp

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "respects allowlist exclusions"
    assert_contains "$output" "SUCCESS" "shows success for allowlisted files"
    cleanup
}

# Test 7: Handles empty files
test_handles_empty_files() {
    setup
    touch test_secrets/empty.yaml
    echo "# Just a comment" > test_secrets/comment-only.yaml

    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "handles empty/comment-only files"
    assert_contains "$output" "SUCCESS" "shows success for empty files"
    cleanup
}

# Test 8: Skip environment variable
test_skip_env_variable() {
    setup
    echo "api_key: plain_secret" > test_secrets/test.yaml

    local output exit_code
    SKIP_SECRETS_CHECK=1 output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "respects SKIP_SECRETS_CHECK=1"
    assert_contains "$output" "SKIPPED" "shows skip message"
    cleanup
}

# Test 9: Exclude environment variable
test_exclude_env_variable() {
    setup
    echo "secret1: plain" > test_secrets/exclude1.yaml
    echo "secret2: plain" > test_secrets/exclude2.yaml
    echo "secret3: plain" > test_secrets/include.yaml

    local output exit_code
    SECRETS_CHECK_EXCLUDE="exclude1.yaml exclude2.yaml" output=$(bash scripts/check-no-plaintext-secrets.sh -d test_secrets 2>&1) || exit_code=$?

    assert_exit_code 1 ${exit_code:-0} "processes SECRETS_CHECK_EXCLUDE"
    assert_contains "$output" "include.yaml" "detects non-excluded file"
    cleanup
}

# Test 10: No secrets directory
test_no_secrets_dir() {
    local output exit_code
    output=$(bash scripts/check-no-plaintext-secrets.sh -d nonexistent_dir 2>&1) && exit_code=$?

    assert_exit_code 0 ${exit_code:-1} "handles missing secrets directory"
    assert_contains "$output" "No secrets directory found" "shows appropriate message"
}

# Test 11: Help and version
test_help_and_version() {
    local output exit_code

    # Test help
    output=$(bash scripts/check-no-plaintext-secrets.sh --help 2>&1) && exit_code=$?
    assert_exit_code 0 ${exit_code:-1} "help option works"
    assert_contains "$output" "Secret-First" "help shows description"

    # Test version
    output=$(bash scripts/check-no-plaintext-secrets.sh --version 2>&1) && exit_code=$?
    assert_exit_code 0 ${exit_code:-1} "version option works"
    assert_contains "$output" "version" "version shows version info"
}

# Main test runner
main() {
    echo "Testing Secret-First plaintext detection script"
    echo "==============================================="

    if [[ ! -f scripts/check-no-plaintext-secrets.sh ]]; then
        echo -e "${RED}ERROR: scripts/check-no-plaintext-secrets.sh not found${NC}"
        echo "This script should be run from the project root"
        exit 1
    fi

    # Run all tests
    test_detects_plaintext
    test_allows_enc_encrypted
    test_allows_sops_with_mac
    test_rejects_sops_without_mac
    test_excludes_examples
    test_respects_allowlist
    test_handles_empty_files
    test_skip_env_variable
    test_exclude_env_variable
    test_no_secrets_dir
    test_help_and_version

    echo
    echo "==============================================="
    echo -e "Test Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"

    if [[ $FAILED -gt 0 ]]; then
        echo -e "${RED}❌ Some tests failed${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ All tests passed${NC}"
        exit 0
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi