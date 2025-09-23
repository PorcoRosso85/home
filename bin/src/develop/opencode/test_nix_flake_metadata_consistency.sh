#!/usr/bin/env bash
set -euo pipefail

# Test: Nix Flake Metadata Consistency Verification
# Purpose: Verify that ?rev= fixed revision approach ensures perfect reproducibility
# Method: Non-destructive comparison of flake.nix revision with resolved metadata
# Safety: No repository changes, read-only operations only

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly FLAKE_DIR="$SCRIPT_DIR"
readonly TEST_NAME="nix-flake-metadata-consistency"

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

# Extract revision from flake.nix ?rev= parameter
extract_flake_nix_revision() {
    local flake_file="$1"

    if [[ ! -f "$flake_file" ]]; then
        log_error "flake.nix not found: $flake_file"
        return 1
    fi

    # Extract revision from line like: inputs.nixpkgs.url = "github:NixOS/nixpkgs?rev=8eaee110344796db060382e15d3af0a9fc396e0e";
    local revision
    revision=$(grep -E 'inputs\.nixpkgs\.url.*\?rev=' "$flake_file" | \
               sed -E 's/.*\?rev=([a-f0-9]+).*/\1/' | \
               head -1)

    if [[ -z "$revision" ]]; then
        log_error "Could not extract revision from flake.nix"
        return 1
    fi

    echo "$revision"
}

# Extract revision from flake.lock
extract_flake_lock_revision() {
    local lock_file="$1"

    if [[ ! -f "$lock_file" ]]; then
        log_error "flake.lock not found: $lock_file"
        return 1
    fi

    # Extract nixpkgs revision from flake.lock
    local revision
    revision=$(jq -r '.nodes.nixpkgs.locked.rev // empty' "$lock_file")

    if [[ -z "$revision" ]]; then
        log_error "Could not extract nixpkgs revision from flake.lock"
        return 1
    fi

    echo "$revision"
}

# Get resolved revision from nix flake metadata
get_flake_metadata_revision() {
    local flake_dir="$1"

    log_info "Querying nix flake metadata for: $flake_dir"

    # Use nix flake metadata to get resolved revision
    local metadata_output
    if ! metadata_output=$(nix flake metadata "$flake_dir" --json 2>/dev/null); then
        log_error "Failed to get flake metadata"
        return 1
    fi

    # Extract nixpkgs revision from metadata
    local revision
    revision=$(echo "$metadata_output" | jq -r '.locks.nodes.nixpkgs.locked.rev // empty')

    if [[ -z "$revision" ]]; then
        log_error "Could not extract nixpkgs revision from metadata"
        return 1
    fi

    echo "$revision"
}

# Verify that all three sources agree on the revision
verify_revision_consistency() {
    local flake_dir="$1"
    local flake_file="$flake_dir/flake.nix"
    local lock_file="$flake_dir/flake.lock"

    log_info "Starting revision consistency verification"
    log_info "Flake directory: $flake_dir"

    # Extract revisions from all sources
    local flake_nix_rev
    local flake_lock_rev
    local metadata_rev

    log_info "Extracting revision from flake.nix..."
    if ! flake_nix_rev=$(extract_flake_nix_revision "$flake_file"); then
        return 1
    fi
    log_info "flake.nix revision: $flake_nix_rev"

    log_info "Extracting revision from flake.lock..."
    if ! flake_lock_rev=$(extract_flake_lock_revision "$lock_file"); then
        return 1
    fi
    log_info "flake.lock revision: $flake_lock_rev"

    log_info "Querying nix flake metadata..."
    if ! metadata_rev=$(get_flake_metadata_revision "$flake_dir"); then
        return 1
    fi
    log_info "metadata revision: $metadata_rev"

    # Verify all revisions match
    local success=true

    if [[ "$flake_nix_rev" != "$flake_lock_rev" ]]; then
        log_error "Revision mismatch: flake.nix ($flake_nix_rev) != flake.lock ($flake_lock_rev)"
        success=false
    fi

    if [[ "$flake_nix_rev" != "$metadata_rev" ]]; then
        log_error "Revision mismatch: flake.nix ($flake_nix_rev) != metadata ($metadata_rev)"
        success=false
    fi

    if [[ "$flake_lock_rev" != "$metadata_rev" ]]; then
        log_error "Revision mismatch: flake.lock ($flake_lock_rev) != metadata ($metadata_rev)"
        success=false
    fi

    if [[ "$success" == "true" ]]; then
        log_success "All revisions match: $flake_nix_rev"
        log_success "Fixed revision reproducibility: VERIFIED"
        return 0
    else
        log_error "Revision consistency check: FAILED"
        return 1
    fi
}

# Verify hash consistency between sources
verify_hash_consistency() {
    local flake_dir="$1"
    local lock_file="$flake_dir/flake.lock"

    log_info "Verifying hash consistency..."

    # Get hash from flake.lock
    local lock_hash
    lock_hash=$(jq -r '.nodes.nixpkgs.locked.narHash // empty' "$lock_file")

    if [[ -z "$lock_hash" ]]; then
        log_error "Could not extract narHash from flake.lock"
        return 1
    fi

    # Get hash from metadata
    local metadata_output
    if ! metadata_output=$(nix flake metadata "$flake_dir" --json 2>/dev/null); then
        log_error "Failed to get flake metadata for hash verification"
        return 1
    fi

    local metadata_hash
    metadata_hash=$(echo "$metadata_output" | jq -r '.locks.nodes.nixpkgs.locked.narHash // empty')

    if [[ -z "$metadata_hash" ]]; then
        log_error "Could not extract narHash from metadata"
        return 1
    fi

    if [[ "$lock_hash" == "$metadata_hash" ]]; then
        log_success "Hash consistency verified: $lock_hash"
        return 0
    else
        log_error "Hash mismatch: lock ($lock_hash) != metadata ($metadata_hash)"
        return 1
    fi
}

# Main test execution
main() {
    log_info "=== $TEST_NAME ==="
    log_info "Testing fixed revision reproducibility (non-destructive)"

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
    for tool in nix jq; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done

    # Run consistency checks
    local test_passed=true

    if ! verify_revision_consistency "$FLAKE_DIR"; then
        test_passed=false
    fi

    if ! verify_hash_consistency "$FLAKE_DIR"; then
        test_passed=false
    fi

    # Final result
    echo
    if [[ "$test_passed" == "true" ]]; then
        log_success "=== TEST PASSED ==="
        log_success "Fixed revision reproducibility verified"
        log_success "Repository state unchanged (non-destructive)"
        exit 0
    else
        log_error "=== TEST FAILED ==="
        log_error "Reproducibility verification failed"
        exit 1
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi