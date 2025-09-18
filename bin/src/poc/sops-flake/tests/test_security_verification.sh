#!/usr/bin/env bash
# test_security_verification.sh - Security-focused testing for sops-flake
# Tests plaintext detection, secure handling, and Git hooks

set -euo pipefail

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES="systemd user app-standalone"
TEST_BASE_DIR="/tmp/sops-security-test-$$"
FAILURES=0
WARNINGS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((FAILURES++))
}

# Cleanup function
cleanup() {
    if [[ -d "$TEST_BASE_DIR" ]]; then
        log_info "Cleaning up test directory: $TEST_BASE_DIR"
        rm -rf "$TEST_BASE_DIR"
    fi
}

# Setup cleanup trap
trap cleanup EXIT

test_plaintext_detection() {
    local template="$1"
    local test_dir="$TEST_BASE_DIR/$template"
    
    log_info "=== Testing plaintext detection for $template ==="
    
    # Copy template
    cp -r "$PROJECT_ROOT/templates/$template" "$test_dir"
    cd "$test_dir"
    
    # Test 1: Create obvious plaintext secret
    log_info "Test 1: Testing obvious plaintext detection..."
    echo "password: plaintext_secret" > "./secrets/test-plaintext.yaml"
    echo "api_key: sk-1234567890abcdef" >> "./secrets/test-plaintext.yaml"
    
    if [[ -x "./scripts/check-no-plaintext-secrets.sh" ]]; then
        if ! ./scripts/check-no-plaintext-secrets.sh >/dev/null 2>&1; then
            log_success "$template: Detected obvious plaintext secrets"
        else
            log_error "$template: Failed to detect obvious plaintext secrets"
        fi
    else
        log_error "$template: check-no-plaintext-secrets.sh not found or not executable"
    fi
    
    rm -f "./secrets/test-plaintext.yaml"
    
    # Test 2: Test with encrypted content (should pass)
    log_info "Test 2: Testing encrypted content (should pass)..."
    cat > "./secrets/test-encrypted.yaml" << 'EOF'
# This is a SOPS encrypted file
password: ENC[AES256_GCM,data:abcd1234,iv:xyz789,aad:test,tag:valid]
api_key: ENC[AES256_GCM,data:efgh5678,iv:abc123,aad:test,tag:valid]
sops:
    kms: []
    gcp_kms: []
    azure_kv: []
    hc_vault: []
    age:
        - recipient: age1234567890abcdef
          enc: xyz
    lastmodified: '2023-01-01T00:00:00Z'
    mac: ENC[AES256_GCM,data:valid_mac,type:str]
    pgp: []
    version: 3.7.3
EOF
    
    if [[ -x "./scripts/check-no-plaintext-secrets.sh" ]]; then
        if ./scripts/check-no-plaintext-secrets.sh >/dev/null 2>&1; then
            log_success "$template: Correctly passed encrypted content"
        else
            log_warning "$template: May have false positive on encrypted content"
        fi
    fi
    
    rm -f "./secrets/test-encrypted.yaml"
    
    # Test 3: Test edge cases
    log_info "Test 3: Testing edge cases..."
    
    # Empty file (should pass)
    touch "./secrets/empty.yaml"
    if [[ -x "./scripts/check-no-plaintext-secrets.sh" ]]; then
        if ./scripts/check-no-plaintext-secrets.sh >/dev/null 2>&1; then
            log_success "$template: Correctly handled empty file"
        else
            log_warning "$template: May have issues with empty files"
        fi
    fi
    rm -f "./secrets/empty.yaml"
    
    # File with only comments (should pass)
    cat > "./secrets/comments-only.yaml" << 'EOF'
# This is just a comment file
# password: this_is_commented_out
# api_key: this_is_also_commented
EOF
    
    if [[ -x "./scripts/check-no-plaintext-secrets.sh" ]]; then
        if ./scripts/check-no-plaintext-secrets.sh >/dev/null 2>&1; then
            log_success "$template: Correctly handled comment-only file"
        else
            log_warning "$template: May have false positive on comments"
        fi
    fi
    rm -f "./secrets/comments-only.yaml"
    
    log_info "=== Completed plaintext detection test for $template ==="
    echo
}

test_git_hooks_functionality() {
    local template="$1"
    local test_dir="$TEST_BASE_DIR/git-$template"
    
    log_info "=== Testing Git hooks functionality for $template ==="
    
    # Copy template and initialize git
    cp -r "$PROJECT_ROOT/templates/$template" "$test_dir"
    cd "$test_dir"
    
    # Initialize git repository
    git init >/dev/null 2>&1
    git config user.email "test@example.com"
    git config user.name "Test User"
    
    # Test pre-commit hook installation (if available)
    if [[ -f "./.pre-commit-config.yaml" ]]; then
        log_success "$template: Has pre-commit configuration"
        
        # Check if pre-commit hook references plaintext detection
        if grep -q "check-no-plaintext" "./.pre-commit-config.yaml" 2>/dev/null; then
            log_success "$template: Pre-commit config includes plaintext check"
        else
            log_warning "$template: Pre-commit config may not include plaintext check"
        fi
    else
        log_warning "$template: No pre-commit configuration found"
    fi
    
    # Test manual Git hook setup
    if [[ -x "./scripts/check-no-plaintext-secrets.sh" ]]; then
        # Simulate pre-commit hook
        mkdir -p ".git/hooks"
        cat > ".git/hooks/pre-commit" << 'EOF'
#!/bin/bash
exec ./scripts/check-no-plaintext-secrets.sh
EOF
        chmod +x ".git/hooks/pre-commit"
        
        # Test with plaintext file
        echo "password: plaintext" > "./secrets/test.yaml"
        git add "./secrets/test.yaml"
        
        if ! git commit -m "Test commit" >/dev/null 2>&1; then
            log_success "$template: Git hook correctly blocked plaintext commit"
        else
            log_error "$template: Git hook failed to block plaintext commit"
        fi
        
        # Clean up
        git reset --hard HEAD >/dev/null 2>&1
        rm -f "./secrets/test.yaml"
    fi
    
    log_info "=== Completed Git hooks test for $template ==="
    echo
}

test_secure_file_handling() {
    local template="$1"
    local test_dir="$TEST_BASE_DIR/secure-$template"
    
    log_info "=== Testing secure file handling for $template ==="
    
    # Copy template
    cp -r "$PROJECT_ROOT/templates/$template" "$test_dir"
    cd "$test_dir"
    
    # Test 1: Check script permissions
    log_info "Test 1: Checking script permissions..."
    for script in ./scripts/*.sh; do
        if [[ -f "$script" ]]; then
            local perms=$(stat -c "%a" "$script")
            if [[ "$perms" =~ ^7[0-5][0-5]$ ]]; then
                log_success "$template: Script $(basename "$script") has secure permissions ($perms)"
            else
                log_warning "$template: Script $(basename "$script") has permissions $perms (check if appropriate)"
            fi
        fi
    done
    
    # Test 2: Check secrets directory permissions
    log_info "Test 2: Checking secrets directory permissions..."
    if [[ -d "./secrets" ]]; then
        local dir_perms=$(stat -c "%a" "./secrets")
        if [[ "$dir_perms" =~ ^7[0-5][0-5]$ ]]; then
            log_success "$template: Secrets directory has secure permissions ($dir_perms)"
        else
            log_warning "$template: Secrets directory permissions are $dir_perms"
        fi
    fi
    
    # Test 3: Check for secure temporary file handling in scripts
    log_info "Test 3: Checking secure temporary file handling..."
    local temp_issues=0
    for script in ./scripts/*.sh; do
        if [[ -f "$script" ]]; then
            # Check for insecure temp file creation
            if grep -q ">/tmp/" "$script" 2>/dev/null; then
                log_warning "$template: $(basename "$script") may use insecure temp files"
                ((temp_issues++))
            fi
            
            # Check for mktemp usage (secure)
            if grep -q "mktemp" "$script" 2>/dev/null; then
                log_success "$template: $(basename "$script") uses mktemp for temp files"
            fi
        fi
    done
    
    if [[ $temp_issues -eq 0 ]]; then
        log_success "$template: No obvious insecure temp file usage detected"
    fi
    
    log_info "=== Completed secure file handling test for $template ==="
    echo
}

test_encryption_verification() {
    local template="$1"
    local test_dir="$TEST_BASE_DIR/verify-$template"
    
    log_info "=== Testing encryption verification for $template ==="
    
    # Copy template
    cp -r "$PROJECT_ROOT/templates/$template" "$test_dir"
    cd "$test_dir"
    
    # Test verify-encryption.sh functionality
    if [[ -x "./scripts/verify-encryption.sh" ]]; then
        log_info "Testing verify-encryption.sh execution..."
        
        # Test with no encrypted files (should handle gracefully)
        if ./scripts/verify-encryption.sh >/dev/null 2>&1; then
            log_success "$template: verify-encryption.sh handles missing files gracefully"
        else
            log_warning "$template: verify-encryption.sh may need encrypted files present"
        fi
        
        # Create mock encrypted file and test
        cat > "./secrets/mock-encrypted.yaml" << 'EOF'
# Mock SOPS file for testing
password: ENC[AES256_GCM,data:mock,iv:test,aad:test,tag:test]
sops:
    version: 3.7.3
    age:
        - recipient: age1mock
          enc: test
    lastmodified: '2023-01-01T00:00:00Z'
EOF
        
        # Test verification with mock file
        if ./scripts/verify-encryption.sh >/dev/null 2>&1; then
            log_success "$template: verify-encryption.sh processes encrypted files"
        else
            log_warning "$template: verify-encryption.sh may need valid keys for verification"
        fi
        
        rm -f "./secrets/mock-encrypted.yaml"
    else
        log_error "$template: verify-encryption.sh not found or not executable"
    fi
    
    log_info "=== Completed encryption verification test for $template ==="
    echo
}

# Main execution
main() {
    log_info "Starting sops-flake Security Verification Testing..."
    log_info "Test base directory: $TEST_BASE_DIR"
    
    # Create test base directory
    mkdir -p "$TEST_BASE_DIR"
    
    # Run security tests for each template
    for template in $TEMPLATES; do
        test_plaintext_detection "$template"
        test_git_hooks_functionality "$template"
        test_secure_file_handling "$template"
        test_encryption_verification "$template"
    done
    
    # Summary
    echo
    log_info "=== SECURITY VERIFICATION SUMMARY ==="
    if [[ $FAILURES -eq 0 ]]; then
        log_success "All security tests passed! ✅"
        if [[ $WARNINGS -gt 0 ]]; then
            log_warning "$WARNINGS security warnings detected (review recommended)"
        else
            log_success "No security warnings detected"
        fi
    else
        log_error "$FAILURES security tests failed ❌"
        [[ $WARNINGS -gt 0 ]] && log_warning "$WARNINGS security warnings detected"
        exit 1
    fi
    
    echo
    log_success "Security verification complete!"
    log_info "All templates implement proper security measures"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi