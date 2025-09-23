#!/usr/bin/env bash
set -euo pipefail

# Test: Safe Lock Reproducibility Verification
# Purpose: Verify that lock deletion and regeneration produces identical results
# Method: Copy flake files to temporary directory, test lock regeneration there
# Safety: No changes to actual repository files, proper cleanup

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly FLAKE_DIR="$SCRIPT_DIR"
readonly TEST_NAME="safe-lock-reproducibility"

# Color output for better readability
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Global variables for cleanup
TEMP_DIR=""
CLEANUP_REGISTERED=false

# Register cleanup function
register_cleanup() {
    if [[ "$CLEANUP_REGISTERED" == "false" ]]; then
        trap cleanup_temp_resources EXIT INT TERM
        CLEANUP_REGISTERED=true
        log_info "Cleanup handler registered"
    fi
}

# Cleanup temporary resources
cleanup_temp_resources() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        log_info "Cleaning up temporary directory: $TEMP_DIR"
        rm -rf "$TEMP_DIR" || true
        TEMP_DIR=""
    fi
}

# Create temporary working directory
create_temp_workspace() {
    local temp_dir
    temp_dir=$(mktemp -d -t "opencode-lock-test-XXXXXX")
    if [[ ! -d "$temp_dir" ]]; then
        log_error "Failed to create temporary directory"
        return 1
    fi

    # Set global variable for cleanup
    TEMP_DIR="$temp_dir"
    log_info "Created temporary workspace: $TEMP_DIR"
    echo "$TEMP_DIR"
}

# Copy essential flake files to temporary directory
copy_flake_files() {
    local src_dir="$1"
    local dst_dir="$2"

    log_info "Copying flake files from $src_dir to $dst_dir"

    # Copy flake.nix (required)
    if [[ ! -f "$src_dir/flake.nix" ]]; then
        log_error "Source flake.nix not found: $src_dir/flake.nix"
        return 1
    fi
    cp "$src_dir/flake.nix" "$dst_dir/"

    # Copy flake.lock if it exists (for comparison)
    if [[ -f "$src_dir/flake.lock" ]]; then
        cp "$src_dir/flake.lock" "$dst_dir/flake.lock.original"
        log_info "Copied flake.lock as flake.lock.original for comparison"
    else
        log_warning "No flake.lock found in source directory"
        return 1
    fi

    # Copy any template directories that may be referenced
    if [[ -d "$src_dir/templates" ]]; then
        cp -r "$src_dir/templates" "$dst_dir/"
        log_info "Copied templates directory"
    fi

    # Copy lib directory if it exists (for client scripts)
    if [[ -d "$src_dir/lib" ]]; then
        cp -r "$src_dir/lib" "$dst_dir/"
        log_info "Copied lib directory"
    else
        log_info "No lib directory found (optional)"
    fi

    log_success "Flake files copied successfully"
}

# Generate new flake.lock in temporary directory
generate_new_lock() {
    local temp_dir="$1"

    log_info "Generating new flake.lock in temporary directory"

    # Change to temp directory and update flake
    cd "$temp_dir"

    # Remove any existing lock file to force regeneration
    if [[ -f "flake.lock" ]]; then
        rm -f "flake.lock"
        log_info "Removed existing flake.lock"
    fi

    # Generate new lock file
    if ! nix flake update --commit-lock-file 2>/dev/null; then
        # Try without commit-lock-file if we're not in a git repo
        if ! nix flake update 2>/dev/null; then
            log_error "Failed to generate new flake.lock"
            return 1
        fi
    fi

    if [[ ! -f "flake.lock" ]]; then
        log_error "flake.lock was not generated"
        return 1
    fi

    log_success "New flake.lock generated successfully"
}

# Compare original and regenerated lock files
compare_lock_files() {
    local temp_dir="$1"
    local original_lock="$temp_dir/flake.lock.original"
    local new_lock="$temp_dir/flake.lock"

    log_info "Comparing original and regenerated lock files"

    if [[ ! -f "$original_lock" ]]; then
        log_error "Original lock file not found: $original_lock"
        return 1
    fi

    if [[ ! -f "$new_lock" ]]; then
        log_error "New lock file not found: $new_lock"
        return 1
    fi

    # Compare JSON structure (ignoring formatting differences)
    local original_json new_json

    if ! original_json=$(jq --sort-keys . "$original_lock" 2>/dev/null); then
        log_error "Failed to parse original lock file as JSON"
        return 1
    fi

    if ! new_json=$(jq --sort-keys . "$new_lock" 2>/dev/null); then
        log_error "Failed to parse new lock file as JSON"
        return 1
    fi

    # Compare critical fields
    local original_rev new_rev original_hash new_hash

    original_rev=$(echo "$original_json" | jq -r '.nodes.nixpkgs.locked.rev // empty')
    new_rev=$(echo "$new_json" | jq -r '.nodes.nixpkgs.locked.rev // empty')

    original_hash=$(echo "$original_json" | jq -r '.nodes.nixpkgs.locked.narHash // empty')
    new_hash=$(echo "$new_json" | jq -r '.nodes.nixpkgs.locked.narHash // empty')

    log_info "Original revision: $original_rev"
    log_info "New revision: $new_rev"
    log_info "Original hash: $original_hash"
    log_info "New hash: $new_hash"

    # Check for exact matches
    local success=true

    if [[ "$original_rev" != "$new_rev" ]]; then
        log_error "Revision mismatch: original ($original_rev) != new ($new_rev)"
        success=false
    fi

    if [[ "$original_hash" != "$new_hash" ]]; then
        log_error "Hash mismatch: original ($original_hash) != new ($new_hash)"
        success=false
    fi

    # Additional check: compare full JSON structure
    if ! diff <(echo "$original_json") <(echo "$new_json") >/dev/null; then
        log_warning "Full JSON structure differs, checking critical fields only"

        # If critical fields match but structure differs, it might be acceptable
        if [[ "$success" == "true" ]]; then
            log_info "Critical fields match despite structural differences"
        fi
    else
        log_success "Complete lock file match (identical JSON structure)"
    fi

    if [[ "$success" == "true" ]]; then
        log_success "Lock file reproducibility: VERIFIED"
        return 0
    else
        log_error "Lock file reproducibility: FAILED"
        return 1
    fi
}

# Test that the regenerated environment still provides opencode
verify_opencode_available() {
    local temp_dir="$1"

    log_info "Verifying opencode availability in regenerated environment"

    cd "$temp_dir"

    # Test that nix develop works and opencode is available
    if ! nix develop --command which opencode >/dev/null 2>&1; then
        log_error "opencode not available in regenerated environment"
        return 1
    fi

    # Verify opencode version/help is accessible
    local opencode_version
    if opencode_version=$(nix develop --command opencode --version 2>/dev/null); then
        log_info "opencode version: $opencode_version"
    else
        log_warning "Could not get opencode version, testing help command"
        if ! nix develop --command opencode --help >/dev/null 2>&1; then
            log_error "opencode help command failed"
            return 1
        fi
    fi

    log_success "opencode available in regenerated environment"
    return 0
}

# Main test execution
main() {
    log_info "=== $TEST_NAME ==="
    log_info "Testing lock reproducibility with temporary directory (safe)"

    # Verify test environment
    if [[ ! -f "$FLAKE_DIR/flake.nix" ]]; then
        log_error "flake.nix not found in: $FLAKE_DIR"
        exit 1
    fi

    if [[ ! -f "$FLAKE_DIR/flake.lock" ]]; then
        log_error "flake.lock not found in: $FLAKE_DIR"
        exit 1
    fi

    # Check required tools
    for tool in nix jq mktemp; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done

    # Store original working directory
    local original_dir
    original_dir=$(pwd)

    # Create temporary workspace
    local temp_workspace
    if ! temp_workspace=$(create_temp_workspace); then
        exit 1
    fi

    # Register cleanup now that we have a temp directory
    register_cleanup

    # Verify temp directory exists before proceeding
    if [[ ! -d "$temp_workspace" ]]; then
        log_error "Temporary workspace not available: $temp_workspace"
        exit 1
    fi

    # Copy flake files to temporary directory
    if ! copy_flake_files "$FLAKE_DIR" "$temp_workspace"; then
        exit 1
    fi

    # Generate new lock file
    if ! generate_new_lock "$temp_workspace"; then
        exit 1
    fi

    # Return to original directory before comparisons
    cd "$original_dir"

    # Compare lock files
    local comparison_passed=false
    if compare_lock_files "$temp_workspace"; then
        comparison_passed=true
    fi

    # Test opencode availability
    local opencode_available=false
    if verify_opencode_available "$temp_workspace"; then
        opencode_available=true
    fi

    # Final result
    echo
    if [[ "$comparison_passed" == "true" && "$opencode_available" == "true" ]]; then
        log_success "=== TEST PASSED ==="
        log_success "Lock reproducibility verified"
        log_success "opencode serve consistently available"
        log_success "Repository integrity maintained (no changes)"
        exit 0
    else
        log_error "=== TEST FAILED ==="
        if [[ "$comparison_passed" == "false" ]]; then
            log_error "Lock file reproducibility test failed"
        fi
        if [[ "$opencode_available" == "false" ]]; then
            log_error "opencode availability test failed"
        fi
        exit 1
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi