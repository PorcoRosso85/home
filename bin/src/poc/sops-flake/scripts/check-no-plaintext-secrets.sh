#!/bin/bash
# check-no-plaintext-secrets.sh - Secret-First plaintext detection script
# Prevents plaintext secrets from being committed to Git
set -euo pipefail

# Version and constants
SCRIPT_VERSION="1.0.0"
SECRETS_DIR="secrets"
ALLOWLIST_FILE=".secrets-allowlist"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default file extensions to check
DEFAULT_EXTENSIONS=(yaml yml json toml ini txt conf)

# Files to exclude by pattern
EXCLUDE_PATTERNS=(
    "*.bak"
    "*.dec"
    "*.tmp"
    "*.example"
    "README.*"
    "readme.*"
)

# Environment variable support
SKIP_CHECK="${SKIP_SECRETS_CHECK:-}"
EXTRA_EXCLUDES="${SECRETS_CHECK_EXCLUDE:-}"

# Usage information
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Secret-First plaintext detection script v$SCRIPT_VERSION

Detects plaintext secrets in the secrets/ directory to prevent
accidental commits. Part of the Secret-First security framework.

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    -d, --dir DIR       Secrets directory (default: $SECRETS_DIR)
    --skip-empty        Skip empty files (default behavior)
    --version           Show version information

ENVIRONMENT VARIABLES:
    SKIP_SECRETS_CHECK=1        Skip all checks (local development only)
    SECRETS_CHECK_EXCLUDE       Space-separated list of additional files to exclude

EXIT CODES:
    0    No plaintext secrets found
    1    Plaintext secrets detected
    2    Script error or invalid usage

EXAMPLES:
    # Basic usage
    $(basename "$0")

    # Check custom directory
    $(basename "$0") -d /path/to/secrets

    # Skip checks temporarily (local only)
    SKIP_SECRETS_CHECK=1 $(basename "$0")

MORE INFO:
    - Encrypted files must contain 'ENC[AES256_GCM' OR 'sops:' + 'mac:' fields
    - Create .secrets-allowlist file to exclude specific files
    - Use 'sops -e -i <file>' to encrypt plaintext files
EOF
}

version_info() {
    echo "check-no-plaintext-secrets.sh version $SCRIPT_VERSION"
    echo "Part of the Secret-First SOPS framework"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Check if file should be excluded
is_excluded() {
    local file="$1"
    local basename_file
    basename_file=$(basename "$file")

    # Check built-in exclude patterns
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        if [[ "$basename_file" == $pattern ]]; then
            return 0  # Excluded
        fi
    done

    # Check environment variable excludes
    if [[ -n "$EXTRA_EXCLUDES" ]]; then
        for exclude in $EXTRA_EXCLUDES; do
            if [[ "$basename_file" == "$exclude" ]] || [[ "$file" == *"$exclude"* ]]; then
                return 0  # Excluded
            fi
        done
    fi

    # Check .secrets-allowlist
    if [[ -f "$ALLOWLIST_FILE" ]]; then
        while IFS= read -r pattern; do
            # Skip empty lines and comments
            [[ -z "$pattern" || "$pattern" =~ ^[[:space:]]*# ]] && continue

            # Simple glob pattern matching
            if [[ "$file" == $pattern ]] || [[ "$file" == *"$pattern"* ]]; then
                return 0  # Excluded by allowlist
            fi
        done < "$ALLOWLIST_FILE"
    fi

    return 1  # Not excluded
}

# Check if file contains encrypted content
is_encrypted() {
    local file="$1"
    local content

    # Read file content
    if ! content=$(cat "$file" 2>/dev/null); then
        log_warning "Could not read file: $file"
        return 1  # Treat unreadable as plaintext for safety
    fi

    # Empty files or comment-only files are considered safe
    if [[ -z "$content" ]] || ! grep -q '[^[:space:]#]' <<< "$content"; then
        return 0  # Empty/comment-only files are safe
    fi

    # Method 1: Check for ENC[AES256_GCM markers (direct SOPS encryption)
    if grep -q 'ENC\[AES256_GCM,' "$file"; then
        return 0  # Encrypted with SOPS
    fi

    # Method 2: Check for SOPS structure with MAC field
    if grep -q '^sops:' "$file" && grep -q '^\s*mac:' "$file"; then
        return 0  # SOPS file with MAC (fully encrypted)
    fi

    return 1  # Appears to be plaintext
}

# Main checking logic
check_secrets() {
    local secrets_dir="$1"
    local verbose="${2:-false}"
    local found_plaintext=()
    local checked_files=0
    local total_files=0

    log_info "Checking for plaintext secrets in: $secrets_dir"

    # Check if secrets directory exists
    if [[ ! -d "$secrets_dir" ]]; then
        log_success "No secrets directory found - nothing to check"
        return 0
    fi

    # Find files to check
    local find_args=()
    for ext in "${DEFAULT_EXTENSIONS[@]}"; do
        find_args+=(-name "*.$ext" -o)
    done
    # Remove the trailing -o
    unset 'find_args[-1]'

    # Find all target files
    while IFS= read -r -d '' file; do
        ((total_files++))

        if is_excluded "$file"; then
            [[ "$verbose" == "true" ]] && log_info "Skipping excluded file: $file"
            continue
        fi

        ((checked_files++))
        [[ "$verbose" == "true" ]] && log_info "Checking: $file"

        if ! is_encrypted "$file"; then
            found_plaintext+=("$file")
            log_error "PLAINTEXT DETECTED: $file"
        fi
    done < <(find "$secrets_dir" -type f \( "${find_args[@]}" \) -print0 2>/dev/null || true)

    # Report results
    if [[ ${#found_plaintext[@]} -eq 0 ]]; then
        log_success "No plaintext secrets found"
        log_info "Checked $checked_files files (excluded $(( total_files - checked_files )) files)"
        return 0
    else
        echo
        log_error "Found ${#found_plaintext[@]} file(s) with plaintext secrets:"
        for file in "${found_plaintext[@]}"; do
            echo -e "${RED}  ❌ $file${NC}" >&2
        done

        echo >&2
        echo -e "${YELLOW}TO FIX THESE ISSUES:${NC}" >&2
        echo "  1. Encrypt files with SOPS:" >&2
        for file in "${found_plaintext[@]}"; do
            echo -e "     ${BLUE}sops -e -i $file${NC}" >&2
        done
        echo >&2
        echo "  2. Or add to .secrets-allowlist if they're test data:" >&2
        for file in "${found_plaintext[@]}"; do
            echo -e "     ${BLUE}echo '$file' >> .secrets-allowlist${NC}" >&2
        done
        echo >&2
        echo -e "${RED}COMMIT BLOCKED - Plaintext secrets detected${NC}" >&2

        return 1
    fi
}

# Parse command line arguments
parse_args() {
    local secrets_dir="$SECRETS_DIR"
    local verbose=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -d|--dir)
                secrets_dir="$2"
                shift 2
                ;;
            --skip-empty)
                # Default behavior, kept for compatibility
                shift
                ;;
            --version)
                version_info
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                usage >&2
                exit 2
                ;;
            *)
                log_error "Unexpected argument: $1"
                usage >&2
                exit 2
                ;;
        esac
    done

    echo "$secrets_dir" "$verbose"
}

# Main function
main() {
    # Handle skip check
    if [[ "$SKIP_CHECK" == "1" ]]; then
        log_warning "SKIPPED: SKIP_SECRETS_CHECK=1 (local development mode)"
        echo -e "${YELLOW}WARNING: Secret checking is disabled${NC}" >&2
        return 0
    fi

    # Parse arguments directly
    local secrets_dir="$SECRETS_DIR"
    local verbose=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -d|--dir)
                secrets_dir="$2"
                shift 2
                ;;
            --skip-empty)
                # Default behavior, kept for compatibility
                shift
                ;;
            --version)
                version_info
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                usage >&2
                exit 2
                ;;
            *)
                log_error "Unexpected argument: $1"
                usage >&2
                exit 2
                ;;
        esac
    done

    # Perform the check
    if check_secrets "$secrets_dir" "$verbose"; then
        log_success "All secrets are properly encrypted ✅"
        return 0
    else
        log_error "Plaintext secrets detected ❌"
        return 1
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

