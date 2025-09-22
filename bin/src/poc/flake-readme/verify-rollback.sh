#!/bin/bash
# Rollback Verification Script for Flake-README Ignore-Only Policy

set -euo pipefail

echo "=== Rollback Verification ==="
echo "Starting verification at $(date)"
echo

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verification functions
check_git_state() {
    echo -e "${YELLOW}Checking Git State...${NC}"

    # Check if we're on a safe branch/tag
    current_ref=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_ref" == "pre-ignore-only-backup" ]] || [[ "$current_ref" == backup-pre-ignore-only-* ]]; then
        echo -e "${GREEN}✓ On safe reference: $current_ref${NC}"
    else
        echo -e "${RED}⚠ Current reference may not be safe: $current_ref${NC}"
        echo "Expected: pre-ignore-only-backup or backup-pre-ignore-only-*"
        return 1
    fi

    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        echo -e "${GREEN}✓ No uncommitted changes${NC}"
    else
        echo -e "${YELLOW}⚠ Uncommitted changes detected${NC}"
        git status --porcelain
    fi
    echo
}

check_flake_health() {
    echo -e "${YELLOW}Checking Flake Health...${NC}"

    # Test flake check
    if nix flake check --no-build 2>/dev/null; then
        echo -e "${GREEN}✓ Flake check passed${NC}"
    else
        echo -e "${RED}✗ Flake check failed${NC}"
        echo "Running detailed check:"
        nix flake check 2>&1 | head -20
        return 1
    fi

    # Test basic build
    if nix build .#readme-config --no-link 2>/dev/null; then
        echo -e "${GREEN}✓ Basic build successful${NC}"
    else
        echo -e "${RED}✗ Basic build failed${NC}"
        return 1
    fi
    echo
}

check_core_functionality() {
    echo -e "${YELLOW}Checking Core Functionality...${NC}"

    # Check core files exist
    core_files=(
        "lib/core-docs.nix"
        "lib/flake-module.nix"
        "flake.nix"
        "README.md"
    )

    for file in "${core_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo -e "${GREEN}✓ $file exists${NC}"
        else
            echo -e "${RED}✗ $file missing${NC}"
            return 1
        fi
    done

    # Test module evaluation
    if nix eval .#flakeModule.options --json >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Module options evaluate correctly${NC}"
    else
        echo -e "${RED}✗ Module evaluation failed${NC}"
        return 1
    fi
    echo
}

check_test_suite() {
    echo -e "${YELLOW}Running Test Suite...${NC}"

    # Find and run test files
    test_files=($(find . -name "test-*.nix" -type f))

    if [[ ${#test_files[@]} -eq 0 ]]; then
        echo -e "${YELLOW}⚠ No test files found${NC}"
        return 0
    fi

    local test_passed=0
    local test_total=${#test_files[@]}

    for test_file in "${test_files[@]}"; do
        echo "Testing: $test_file"
        if nix build ".#$(basename "$test_file" .nix)" --no-link 2>/dev/null; then
            echo -e "${GREEN}✓ $test_file passed${NC}"
            ((test_passed++))
        else
            echo -e "${RED}✗ $test_file failed${NC}"
        fi
    done

    echo "Tests passed: $test_passed/$test_total"
    if [[ $test_passed -eq $test_total ]]; then
        echo -e "${GREEN}✓ All tests passed${NC}"
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        return 1
    fi
    echo
}

check_documentation() {
    echo -e "${YELLOW}Checking Documentation...${NC}"

    # Check README readability
    if [[ -f "README.md" ]] && [[ -s "README.md" ]]; then
        echo -e "${GREEN}✓ README.md exists and not empty${NC}"
    else
        echo -e "${RED}✗ README.md missing or empty${NC}"
        return 1
    fi

    # Check if rollback procedures are accessible
    if [[ -f "ROLLBACK_PROCEDURES.md" ]]; then
        echo -e "${GREEN}✓ Rollback procedures documented${NC}"
    else
        echo -e "${YELLOW}⚠ Rollback procedures not found${NC}"
    fi
    echo
}

verify_backup_integrity() {
    echo -e "${YELLOW}Verifying Backup Integrity...${NC}"

    # Check backup references exist
    if git show-ref --verify --quiet refs/heads/backup-pre-ignore-only-$(date +%Y%m%d) 2>/dev/null; then
        echo -e "${GREEN}✓ Backup branch exists${NC}"
    else
        backup_branches=($(git branch --list | grep "backup-pre-ignore-only" | head -1))
        if [[ ${#backup_branches[@]} -gt 0 ]]; then
            echo -e "${GREEN}✓ Backup branch found: ${backup_branches[0]}${NC}"
        else
            echo -e "${RED}✗ No backup branch found${NC}"
            return 1
        fi
    fi

    if git show-ref --verify --quiet refs/tags/pre-ignore-only-backup 2>/dev/null; then
        echo -e "${GREEN}✓ Backup tag exists${NC}"
    else
        echo -e "${RED}✗ Backup tag missing${NC}"
        return 1
    fi
    echo
}

# Main verification workflow
main() {
    echo "Verifying rollback state for flake-readme..."
    echo "Working directory: $(pwd)"
    echo "Current time: $(date)"
    echo

    local checks_passed=0
    local total_checks=6

    # Run all checks
    if check_git_state; then ((checks_passed++)); fi
    if check_flake_health; then ((checks_passed++)); fi
    if check_core_functionality; then ((checks_passed++)); fi
    if check_test_suite; then ((checks_passed++)); fi
    if check_documentation; then ((checks_passed++)); fi
    if verify_backup_integrity; then ((checks_passed++)); fi

    # Final report
    echo "=== Verification Summary ==="
    echo "Checks passed: $checks_passed/$total_checks"

    if [[ $checks_passed -eq $total_checks ]]; then
        echo -e "${GREEN}✓ All verifications passed - Rollback successful${NC}"
        echo -e "${GREEN}System is in a safe, functional state${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some verifications failed - Rollback may be incomplete${NC}"
        echo -e "${RED}Manual intervention may be required${NC}"
        exit 1
    fi
}

# Check if we're in the right directory
if [[ ! -f "flake.nix" ]] || [[ ! -d "lib" ]]; then
    echo -e "${RED}Error: Not in flake-readme directory${NC}"
    echo "Please run this script from /home/nixos/bin/src/poc/flake-readme"
    exit 1
fi

main "$@"