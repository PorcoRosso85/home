#!/usr/bin/env bash
# Initialize sops-flake template with proper configuration

set -euo pipefail

# Help function
show_help() {
    cat <<EOF
Usage: $0 [OPTIONS]

Initialize sops-flake template with age key setup and configuration.

OPTIONS:
    -h, --help      Show this help message and exit
    -v, --verbose   Enable verbose output
    -f, --force     Force re-initialization even if already configured

EXAMPLES:
    $0              # Normal initialization
    $0 --verbose    # Initialize with detailed output
    $0 --force      # Re-initialize from scratch

EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -f|--force)
            FORCE=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

echo "=== sops-flake Template Initialization ==="

# 1. Age鍵セットアップ
echo "Step 1: Setting up age key..."
./scripts/setup-age-key.sh

# 2. .sops.yaml更新
echo "Step 2: Updating .sops.yaml..."
if [[ -f .sops.yaml ]] && grep -q "REPLACE_ME" .sops.yaml; then
    PUBLIC_KEY=$(age-keygen -y "${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}")
    sed -i "s/REPLACE_ME/$PUBLIC_KEY/g" .sops.yaml
    echo "✓ .sops.yaml updated with your public key"
else
    echo "✓ .sops.yaml already configured or not found"
fi

# 3. 暗号化検証
echo "Step 3: Verifying encryption..."
if [[ -d secrets ]]; then
    ./scripts/verify-encryption.sh
fi

# 4. Git hooks設定
echo "Step 4: Setting up git hooks..."
if [[ -d .git ]]; then
    cp scripts/check-no-plaintext-secrets.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✓ Git pre-commit hook installed"
fi

echo "=== Initialization complete ==="