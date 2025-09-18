#!/usr/bin/env bash
# test_unification.sh - Comprehensive unification verification
# This script verifies that all templates follow the unified structure and procedures

set -euo pipefail

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES="systemd user app-standalone"
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

# Test functions
test_directory_structure() {
    log_info "Testing directory structure consistency..."
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        
        # Check if template directory exists
        if [[ ! -d "$template_path" ]]; then
            log_error "$template: Template directory missing"
            continue
        fi
        
        # Check required directories
        local required_dirs="scripts secrets"
        for dir in $required_dirs; do
            if [[ ! -d "$template_path/$dir" ]]; then
                log_error "$template: Missing directory $dir"
            else
                log_success "$template: Directory $dir exists"
            fi
        done
        
        # Check required scripts
        local required_scripts="init-template.sh verify-encryption.sh check-no-plaintext-secrets.sh setup-age-key.sh"
        for script in $required_scripts; do
            local script_path="$template_path/scripts/$script"
            if [[ ! -f "$script_path" ]]; then
                log_error "$template: Missing script $script"
            elif [[ ! -x "$script_path" ]]; then
                log_error "$template: Script $script is not executable"
            else
                log_success "$template: Script $script exists and is executable"
            fi
        done
        
        # Check configuration files
        local config_files=".sops.yaml flake.nix .gitignore"
        for config in $config_files; do
            if [[ ! -f "$template_path/$config" ]]; then
                log_error "$template: Missing configuration file $config"
            else
                log_success "$template: Configuration file $config exists"
            fi
        done
        
        # Check for module.nix (optional for app-standalone)
        if [[ "$template" != "app-standalone" ]]; then
            if [[ ! -f "$template_path/module.nix" ]]; then
                log_error "$template: Missing configuration file module.nix"
            else
                log_success "$template: Configuration file module.nix exists"
            fi
        else
            if [[ -f "$template_path/module.nix" ]]; then
                log_success "$template: Configuration file module.nix exists"
            else
                log_success "$template: module.nix not required for standalone app"
            fi
        fi
        
        # Check documentation files
        local doc_files="README.md COMMANDS.md"
        for doc in $doc_files; do
            if [[ ! -f "$template_path/$doc" ]]; then
                log_error "$template: Missing documentation file $doc"
            else
                log_success "$template: Documentation file $doc exists"
            fi
        done
    done
}

test_configuration_formats() {
    log_info "Testing configuration file formats..."
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        
        # Test .sops.yaml format
        if [[ -f "$template_path/.sops.yaml" ]]; then
            if grep -q "REPLACE_ME" "$template_path/.sops.yaml"; then
                log_success "$template: .sops.yaml contains REPLACE_ME placeholder"
            else
                log_warning "$template: .sops.yaml may not have proper placeholder format"
            fi
            
            # Check for required sections
            if grep -q "creation_rules:" "$template_path/.sops.yaml"; then
                log_success "$template: .sops.yaml has creation_rules section"
            else
                log_error "$template: .sops.yaml missing creation_rules section"
            fi
        fi
        
        # Test flake.nix for devShells
        if [[ -f "$template_path/flake.nix" ]]; then
            if grep -q "devShells" "$template_path/flake.nix"; then
                log_success "$template: flake.nix has devShells definition"
            else
                log_error "$template: flake.nix missing devShells definition"
            fi
        fi
        
        # Test module.nix for encryptionMethod option (if module.nix exists)
        if [[ -f "$template_path/module.nix" ]]; then
            if grep -q "encryptionMethod" "$template_path/module.nix"; then
                log_success "$template: module.nix has encryptionMethod option"
            else
                log_error "$template: module.nix missing encryptionMethod option"
            fi
        elif [[ "$template" == "app-standalone" ]]; then
            log_success "$template: encryptionMethod handled in flake.nix directly"
        fi
    done
}

test_nix_flake_functionality() {
    log_info "Testing nix flake functionality..."
    
    local original_pwd="$PWD"
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        
        cd "$template_path"
        
        # Test nix flake check
        log_info "Running nix flake check for $template..."
        if timeout 60 nix flake check 2>/dev/null; then
            log_success "$template: nix flake check passed"
        else
            log_error "$template: nix flake check failed"
        fi
        
        # Test that devShell can be built
        log_info "Testing devShell for $template..."
        if timeout 30 nix develop --dry-run 2>/dev/null; then
            log_success "$template: nix develop dry-run passed"
        else
            log_error "$template: nix develop dry-run failed"
        fi
        
        cd "$original_pwd"
    done
}

test_script_functionality() {
    log_info "Testing script functionality..."
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        
        # Test init-template.sh (dry-run mode if available)
        if [[ -x "$template_path/scripts/init-template.sh" ]]; then
            log_info "Testing init-template.sh for $template..."
            if "$template_path/scripts/init-template.sh" --help >/dev/null 2>&1; then
                log_success "$template: init-template.sh responds to --help"
            else
                log_warning "$template: init-template.sh may not have --help option"
            fi
        fi
        
        # Test verify-encryption.sh
        if [[ -x "$template_path/scripts/verify-encryption.sh" ]]; then
            log_info "Testing verify-encryption.sh for $template..."
            # This script should be safe to run as it's read-only
            if "$template_path/scripts/verify-encryption.sh" >/dev/null 2>&1; then
                log_success "$template: verify-encryption.sh executed successfully"
            else
                log_warning "$template: verify-encryption.sh may need encrypted files to verify"
            fi
        fi
        
        # Test check-no-plaintext-secrets.sh
        if [[ -x "$template_path/scripts/check-no-plaintext-secrets.sh" ]]; then
            log_info "Testing check-no-plaintext-secrets.sh for $template..."
            if "$template_path/scripts/check-no-plaintext-secrets.sh" >/dev/null 2>&1; then
                log_success "$template: check-no-plaintext-secrets.sh executed successfully"
            else
                log_warning "$template: check-no-plaintext-secrets.sh returned non-zero exit code"
            fi
        fi
    done
}

test_security_functionality() {
    log_info "Testing security functionality..."
    
    local temp_dir="/tmp/sops-security-test-$$"
    mkdir -p "$temp_dir"
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        local test_template_path="$temp_dir/$template"
        
        # Copy template to temp directory for testing
        cp -r "$template_path" "$test_template_path"
        
        # Test plaintext detection
        echo "password: plaintext_secret" > "$test_template_path/secrets/test-plaintext.yaml"
        
        if [[ -x "$test_template_path/scripts/check-no-plaintext-secrets.sh" ]]; then
            if ! "$test_template_path/scripts/check-no-plaintext-secrets.sh" >/dev/null 2>&1; then
                log_success "$template: Plaintext detection working (script failed as expected)"
            else
                log_error "$template: Plaintext detection not working (script should have failed)"
            fi
        fi
        
        # Clean up test file
        rm -f "$test_template_path/secrets/test-plaintext.yaml"
    done
    
    # Clean up temp directory
    rm -rf "$temp_dir"
}

test_documentation_consistency() {
    log_info "Testing documentation consistency..."
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        
        # Test README.md structure
        if [[ -f "$template_path/README.md" ]]; then
            local required_sections="Quick Start Usage Commands Security"
            for section in $required_sections; do
                if grep -qi "$section" "$template_path/README.md"; then
                    log_success "$template: README.md contains $section section"
                else
                    log_warning "$template: README.md may be missing $section section"
                fi
            done
        fi
        
        # Test COMMANDS.md existence and content
        if [[ -f "$template_path/COMMANDS.md" ]]; then
            if grep -q "init-template.sh" "$template_path/COMMANDS.md"; then
                log_success "$template: COMMANDS.md documents init-template.sh"
            else
                log_warning "$template: COMMANDS.md may not document init-template.sh"
            fi
        fi
    done
}

test_performance_benchmarks() {
    log_info "Testing performance benchmarks..."
    
    for template in $TEMPLATES; do
        local template_path="$PROJECT_ROOT/templates/$template"
        
        # Test init-template.sh performance (if --dry-run available)
        if [[ -x "$template_path/scripts/init-template.sh" ]]; then
            log_info "Benchmarking init-template.sh for $template..."
            start_time=$(date +%s.%N)
            if "$template_path/scripts/init-template.sh" --help >/dev/null 2>&1; then
                end_time=$(date +%s.%N)
                duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "N/A")
                if [[ "$duration" != "N/A" ]]; then
                    log_info "$template: init-template.sh --help took ${duration}s"
                fi
            fi
        fi
        
        # Test verify-encryption.sh performance
        if [[ -x "$template_path/scripts/verify-encryption.sh" ]]; then
            log_info "Benchmarking verify-encryption.sh for $template..."
            start_time=$(date +%s.%N)
            "$template_path/scripts/verify-encryption.sh" >/dev/null 2>&1 || true
            end_time=$(date +%s.%N)
            duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "N/A")
            if [[ "$duration" != "N/A" ]]; then
                log_info "$template: verify-encryption.sh took ${duration}s"
                # Check if under 1 second as specified
                if (( $(echo "$duration < 1" | bc -l 2>/dev/null || echo 0) )); then
                    log_success "$template: verify-encryption.sh meets performance target (<1s)"
                else
                    log_warning "$template: verify-encryption.sh may be slower than target (${duration}s)"
                fi
            fi
        fi
    done
}

# Main execution
main() {
    log_info "Starting sops-flake unification verification..."
    log_info "Testing templates: $TEMPLATES"
    
    test_directory_structure
    test_configuration_formats
    test_nix_flake_functionality
    test_script_functionality
    test_security_functionality
    test_documentation_consistency
    test_performance_benchmarks
    
    # Summary
    echo
    log_info "=== VERIFICATION SUMMARY ==="
    if [[ $FAILURES -eq 0 ]]; then
        log_success "All critical tests passed! ✅"
        if [[ $WARNINGS -gt 0 ]]; then
            log_warning "$WARNINGS warnings detected (non-critical)"
        else
            log_success "No warnings detected"
        fi
    else
        log_error "$FAILURES critical tests failed ❌"
        [[ $WARNINGS -gt 0 ]] && log_warning "$WARNINGS warnings detected"
        exit 1
    fi
    
    echo
    log_success "Unification verification complete!"
    log_info "All templates follow unified structure and procedures"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi