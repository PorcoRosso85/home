#!/usr/bin/env bash
set -euo pipefail

echo "==================================="
echo "SOPS-Flake Template Testing Suite"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOPS_FLAKE_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$SOPS_FLAKE_DIR/templates"

echo "Working directory: $SOPS_FLAKE_DIR"
echo ""

# ==========================================
# 1. Directory Structure Tests
# ==========================================
echo "1. Testing Directory Structure"
echo "------------------------------"

run_test "Templates directory exists" "[[ -d '$TEMPLATES_DIR' ]]"
run_test "app-standalone template exists" "[[ -d '$TEMPLATES_DIR/app-standalone' ]]"
run_test "systemd template exists" "[[ -d '$TEMPLATES_DIR/systemd' ]]"
run_test "user template exists" "[[ -d '$TEMPLATES_DIR/user' ]]"

echo ""

# ==========================================
# 2. Template File Completeness Tests
# ==========================================
echo "2. Testing Template Completeness"
echo "--------------------------------"

# app-standalone files
run_test "app-standalone has flake.nix" "[[ -f '$TEMPLATES_DIR/app-standalone/flake.nix' ]]"
run_test "app-standalone has README.md" "[[ -f '$TEMPLATES_DIR/app-standalone/README.md' ]]"
run_test "app-standalone has .sops.yaml" "[[ -f '$TEMPLATES_DIR/app-standalone/.sops.yaml' ]]"

# systemd files
run_test "systemd has flake.nix" "[[ -f '$TEMPLATES_DIR/systemd/flake.nix' ]]"
run_test "systemd has module.nix" "[[ -f '$TEMPLATES_DIR/systemd/module.nix' ]]"
run_test "systemd has README.md" "[[ -f '$TEMPLATES_DIR/systemd/README.md' ]]"
run_test "systemd has .sops.yaml" "[[ -f '$TEMPLATES_DIR/systemd/.sops.yaml' ]]"

# user files
run_test "user has flake.nix" "[[ -f '$TEMPLATES_DIR/user/flake.nix' ]]"
run_test "user has module.nix" "[[ -f '$TEMPLATES_DIR/user/module.nix' ]]"
run_test "user has README.md" "[[ -f '$TEMPLATES_DIR/user/README.md' ]]"
run_test "user has .sops.yaml" "[[ -f '$TEMPLATES_DIR/user/.sops.yaml' ]]"

echo ""

# ==========================================
# 3. Flake Validity Tests
# ==========================================
echo "3. Testing Flake Validity"
echo "-------------------------"

# Check if nix flakes are enabled
if command -v nix &> /dev/null && nix flake --help &> /dev/null 2>&1; then
    run_test "app-standalone flake valid" "cd '$TEMPLATES_DIR/app-standalone' && nix flake metadata --json"
    run_test "systemd flake valid" "cd '$TEMPLATES_DIR/systemd' && nix flake metadata --json"
    run_test "user flake valid" "cd '$TEMPLATES_DIR/user' && nix flake metadata --json"
else
    echo -e "${YELLOW}⚠ Skipping flake validity tests (nix flakes not available)${NC}"
fi

echo ""

# ==========================================
# 4. README Content Tests
# ==========================================
echo "4. Testing README Content"
echo "-------------------------"

run_test "app-standalone README has integration steps" "grep -q 'Integration Steps' '$TEMPLATES_DIR/app-standalone/README.md'"
run_test "systemd README has integration steps" "grep -q 'Integration Steps' '$TEMPLATES_DIR/systemd/README.md'"
run_test "user README has integration steps" "grep -q 'Integration Steps' '$TEMPLATES_DIR/user/README.md'"

echo ""

# ==========================================
# 5. SOPS Configuration Tests
# ==========================================
echo "5. Testing SOPS Configuration"
echo "-----------------------------"

run_test "app-standalone .sops.yaml has creation_rules" "grep -q 'creation_rules:' '$TEMPLATES_DIR/app-standalone/.sops.yaml'"
run_test "systemd .sops.yaml has creation_rules" "grep -q 'creation_rules:' '$TEMPLATES_DIR/systemd/.sops.yaml'"
run_test "user .sops.yaml has creation_rules" "grep -q 'creation_rules:' '$TEMPLATES_DIR/user/.sops.yaml'"

echo ""

# ==========================================
# 6. Module Content Tests
# ==========================================
echo "6. Testing Module Content"
echo "-------------------------"

run_test "systemd module.nix defines service" "grep -q 'systemd.services' '$TEMPLATES_DIR/systemd/module.nix'"
run_test "systemd module.nix has sops.secrets" "grep -q 'sops.secrets' '$TEMPLATES_DIR/systemd/module.nix'"
run_test "user module.nix defines program" "grep -q 'programs.user-script' '$TEMPLATES_DIR/user/module.nix'"
run_test "user module.nix has sops.secrets" "grep -q 'sops.secrets' '$TEMPLATES_DIR/user/module.nix'"

echo ""

# ==========================================
# 7. Template Copy Test
# ==========================================
echo "7. Testing Template Copy Operation"
echo "----------------------------------"

# Create temporary test directory
TEST_TMP_DIR=$(mktemp -d)
trap "rm -rf $TEST_TMP_DIR" EXIT

run_test "Can copy app-standalone template" "cp -r '$TEMPLATES_DIR/app-standalone' '$TEST_TMP_DIR/test-app'"
run_test "Copied app-standalone has all files" "[[ -f '$TEST_TMP_DIR/test-app/flake.nix' && -f '$TEST_TMP_DIR/test-app/README.md' ]]"

echo ""

# ==========================================
# 8. Main README Tests
# ==========================================
echo "8. Testing Main README"
echo "----------------------"

run_test "Main README exists" "[[ -f '$SOPS_FLAKE_DIR/README.md' ]]"
run_test "Main README mentions templates" "grep -q 'templates/' '$SOPS_FLAKE_DIR/README.md'"
run_test "Main README has quick start guide" "grep -q 'Quick Start' '$SOPS_FLAKE_DIR/README.md'"
run_test "Main README has template comparison" "grep -q 'Template Comparison' '$SOPS_FLAKE_DIR/README.md'"

echo ""

# ==========================================
# Test Summary
# ==========================================
echo "==================================="
echo "Test Summary"
echo "==================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}✓ All tests passed successfully!${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi