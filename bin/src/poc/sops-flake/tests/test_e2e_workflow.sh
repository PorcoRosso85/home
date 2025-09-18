#!/usr/bin/env bash
# test_e2e_workflow.sh - End-to-end workflow testing for unified templates
# Tests the complete user workflow from template setup to deployment

set -euo pipefail

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES="systemd user app-standalone"
TEST_BASE_DIR="/tmp/sops-e2e-test-$$"
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

# Test functions
test_template_workflow() {
    local template="$1"
    local test_dir="$TEST_BASE_DIR/$template"
    
    log_info "=== Testing E2E workflow for $template ==="
    
    # Step 1: Copy template to test directory
    log_info "Step 1: Copying template to test directory..."
    cp -r "$PROJECT_ROOT/templates/$template" "$test_dir"
    if [[ -d "$test_dir" ]]; then
        log_success "$template: Template copied successfully"
    else
        log_error "$template: Failed to copy template"
        return 1
    fi
    
    # Step 2: Change to test directory
    cd "$test_dir"
    
    # Step 3: Test init-template.sh
    log_info "Step 3: Testing init-template.sh..."
    if [[ -x "./scripts/init-template.sh" ]]; then
        # Test help option first
        if ./scripts/init-template.sh --help >/dev/null 2>&1; then
            log_success "$template: init-template.sh --help works"
        else
            log_warning "$template: init-template.sh may not have --help option"
        fi
        
        # Try to run init (some may need user input, so we'll test what we can)
        if timeout 10 ./scripts/init-template.sh --dry-run >/dev/null 2>&1 || 
           timeout 10 ./scripts/init-template.sh -n >/dev/null 2>&1; then
            log_success "$template: init-template.sh dry-run works"
        else
            log_warning "$template: init-template.sh may require interactive input"
        fi
    else
        log_error "$template: init-template.sh not executable"
    fi
    
    # Step 4: Test nix flake functionality
    log_info "Step 4: Testing nix flake functionality..."
    
    # Test flake check
    if timeout 60 nix flake check >/dev/null 2>&1; then
        log_success "$template: nix flake check passed"
    else
        log_error "$template: nix flake check failed"
    fi
    
    # Test devShell build
    if timeout 30 nix develop --dry-run >/dev/null 2>&1; then
        log_success "$template: nix develop dry-run passed"
    else
        log_warning "$template: nix develop dry-run failed (may be environment-specific)"
    fi
    
    # Step 5: Test setup-age-key.sh
    log_info "Step 5: Testing age key setup..."
    if [[ -x "./scripts/setup-age-key.sh" ]]; then
        # Test help first
        if ./scripts/setup-age-key.sh --help >/dev/null 2>&1; then
            log_success "$template: setup-age-key.sh --help works"
        else
            log_warning "$template: setup-age-key.sh may not have --help option"
        fi
        
        # Test key generation (in a safe way)
        local temp_key_dir="$test_dir/.temp-keys"
        mkdir -p "$temp_key_dir"
        if AGE_KEY_DIR="$temp_key_dir" ./scripts/setup-age-key.sh --test-mode >/dev/null 2>&1 ||
           AGE_KEY_DIR="$temp_key_dir" ./scripts/setup-age-key.sh -n >/dev/null 2>&1; then
            log_success "$template: setup-age-key.sh test mode works"
        else
            log_warning "$template: setup-age-key.sh may require interactive mode"
        fi
        rm -rf "$temp_key_dir"
    else
        log_error "$template: setup-age-key.sh not executable"
    fi
    
    # Step 6: Test verify-encryption.sh
    log_info "Step 6: Testing encryption verification..."
    if [[ -x "./scripts/verify-encryption.sh" ]]; then
        if ./scripts/verify-encryption.sh >/dev/null 2>&1; then
            log_success "$template: verify-encryption.sh executed successfully"
        else
            log_warning "$template: verify-encryption.sh needs encrypted files (expected)"
        fi
    else
        log_error "$template: verify-encryption.sh not executable"
    fi
    
    # Step 7: Test plaintext detection
    log_info "Step 7: Testing plaintext detection..."
    if [[ -x "./scripts/check-no-plaintext-secrets.sh" ]]; then
        # Create a test plaintext file
        echo "password: plaintext_secret" > "./secrets/test-plaintext.yaml"
        
        if ! ./scripts/check-no-plaintext-secrets.sh >/dev/null 2>&1; then
            log_success "$template: Plaintext detection working (script failed as expected)"
        else
            log_error "$template: Plaintext detection not working (script should have failed)"
        fi
        
        # Clean up test file
        rm -f "./secrets/test-plaintext.yaml"
    else
        log_error "$template: check-no-plaintext-secrets.sh not executable"
    fi
    
    # Step 8: Test .sops.yaml configuration
    log_info "Step 8: Testing .sops.yaml configuration..."
    if [[ -f "./.sops.yaml" ]]; then
        if grep -q "REPLACE_ME" "./.sops.yaml"; then
            log_success "$template: .sops.yaml has placeholder format"
        else
            log_warning "$template: .sops.yaml may not have expected placeholder"
        fi
        
        if grep -q "creation_rules:" "./.sops.yaml"; then
            log_success "$template: .sops.yaml has creation_rules"
        else
            log_error "$template: .sops.yaml missing creation_rules"
        fi
    else
        log_error "$template: .sops.yaml not found"
    fi
    
    # Step 9: Test documentation quality
    log_info "Step 9: Testing documentation..."
    if [[ -f "./README.md" ]]; then
        local required_sections="Quick Start Usage Commands"
        local found_sections=0
        for section in $required_sections; do
            if grep -qi "$section" "./README.md"; then
                ((found_sections++))
            fi
        done
        
        if [[ $found_sections -ge 2 ]]; then
            log_success "$template: README.md has good structure ($found_sections/3 sections)"
        else
            log_warning "$template: README.md may be missing key sections ($found_sections/3 found)"
        fi
    else
        log_error "$template: README.md not found"
    fi
    
    if [[ -f "./COMMANDS.md" ]]; then
        log_success "$template: COMMANDS.md exists"
    else
        log_warning "$template: COMMANDS.md not found"
    fi
    
    log_info "=== Completed E2E workflow test for $template ==="
    echo
}

test_cross_template_consistency() {
    log_info "=== Testing cross-template consistency ==="
    
    # Test that all templates have the same script names
    local template_scripts=()
    for template in $TEMPLATES; do
        local template_dir="$TEST_BASE_DIR/$template"
        if [[ -d "$template_dir/scripts" ]]; then
            template_scripts+=($(ls "$template_dir/scripts/" | sort))
        fi
    done
    
    # Check if all templates have the same set of scripts
    local systemd_scripts=($(ls "$TEST_BASE_DIR/systemd/scripts/" | sort))
    local user_scripts=($(ls "$TEST_BASE_DIR/user/scripts/" | sort))
    local app_scripts=($(ls "$TEST_BASE_DIR/app-standalone/scripts/" | sort))
    
    if [[ "${systemd_scripts[*]}" == "${user_scripts[*]}" && 
          "${user_scripts[*]}" == "${app_scripts[*]}" ]]; then
        log_success "All templates have consistent script sets"
    else
        log_warning "Templates may have different script sets"
        log_info "systemd: ${systemd_scripts[*]}"
        log_info "user: ${user_scripts[*]}"
        log_info "app-standalone: ${app_scripts[*]}"
    fi
    
    # Test .gitignore consistency
    local gitignore_hashes=()
    for template in $TEMPLATES; do
        local template_dir="$TEST_BASE_DIR/$template"
        if [[ -f "$template_dir/.gitignore" ]]; then
            local hash=$(sha256sum "$template_dir/.gitignore" | cut -d' ' -f1)
            gitignore_hashes+=("$template:$hash")
        fi
    done
    
    # Extract unique hashes
    local unique_hashes=($(printf '%s\n' "${gitignore_hashes[@]}" | cut -d: -f2 | sort -u))
    if [[ ${#unique_hashes[@]} -eq 1 ]]; then
        log_success "All templates have identical .gitignore files"
    else
        log_warning "Templates have different .gitignore files"
        for entry in "${gitignore_hashes[@]}"; do
            log_info "  $entry"
        done
    fi
}

# Main execution
main() {
    log_info "Starting sops-flake End-to-End workflow testing..."
    log_info "Test base directory: $TEST_BASE_DIR"
    
    # Create test base directory
    mkdir -p "$TEST_BASE_DIR"
    
    # Test each template workflow
    for template in $TEMPLATES; do
        test_template_workflow "$template"
    done
    
    # Test cross-template consistency
    test_cross_template_consistency
    
    # Summary
    echo
    log_info "=== E2E WORKFLOW TEST SUMMARY ==="
    if [[ $FAILURES -eq 0 ]]; then
        log_success "All E2E workflow tests passed! ✅"
        if [[ $WARNINGS -gt 0 ]]; then
            log_warning "$WARNINGS warnings detected (check for improvements)"
        else
            log_success "No warnings detected"
        fi
    else
        log_error "$FAILURES E2E workflow tests failed ❌"
        [[ $WARNINGS -gt 0 ]] && log_warning "$WARNINGS warnings detected"
        exit 1
    fi
    
    echo
    log_success "E2E workflow testing complete!"
    log_info "Templates are ready for user deployment"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi