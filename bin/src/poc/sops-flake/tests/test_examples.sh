#!/usr/bin/env bash
# Test script for examples-based templates

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Testing $test_name... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
}

echo "================================================"
echo "         SOPS-Flake Examples Test Suite        "
echo "================================================"
echo ""

# Test 1: Check directory structure
echo "1. Directory Structure Tests"
echo "----------------------------"
run_test "examples directory exists" "[[ -d examples ]]"
run_test "systemd-web-api exists" "[[ -d examples/systemd-web-api ]]"
run_test "cli-tool exists" "[[ -d examples/cli-tool ]]"
run_test "deploy-script exists" "[[ -d examples/deploy-script ]]"
echo ""

# Test 2: Check required files in each example
echo "2. Required Files Tests"
echo "-----------------------"

# systemd-web-api
run_test "systemd-web-api/flake.nix" "[[ -f examples/systemd-web-api/flake.nix ]]"
run_test "systemd-web-api/module.nix" "[[ -f examples/systemd-web-api/module.nix ]]"
run_test "systemd-web-api/README.md" "[[ -f examples/systemd-web-api/README.md ]]"
run_test "systemd-web-api/.sops.yaml" "[[ -f examples/systemd-web-api/.sops.yaml ]]"
run_test "systemd-web-api/secrets dir" "[[ -d examples/systemd-web-api/secrets ]]"

# cli-tool
run_test "cli-tool/flake.nix" "[[ -f examples/cli-tool/flake.nix ]]"
run_test "cli-tool/default.nix" "[[ -f examples/cli-tool/default.nix ]]"
run_test "cli-tool/README.md" "[[ -f examples/cli-tool/README.md ]]"
run_test "cli-tool/.sops.yaml" "[[ -f examples/cli-tool/.sops.yaml ]]"
run_test "cli-tool/secrets dir" "[[ -d examples/cli-tool/secrets ]]"

# deploy-script
run_test "deploy-script/flake.nix" "[[ -f examples/deploy-script/flake.nix ]]"
run_test "deploy-script/deploy.sh" "[[ -f examples/deploy-script/deploy.sh ]]"
run_test "deploy-script/README.md" "[[ -f examples/deploy-script/README.md ]]"
run_test "deploy-script/.sops.yaml" "[[ -f examples/deploy-script/.sops.yaml ]]"
run_test "deploy-script/secrets dir" "[[ -d examples/deploy-script/secrets ]]"
echo ""

# Test 3: Flake validation
echo "3. Flake Validation Tests"
echo "-------------------------"
run_test "Main flake check" "nix flake check --no-build 2>/dev/null"
run_test "Main flake templates" "nix flake show --json 2>/dev/null | grep -q templates"
echo ""

# Test 4: Template initialization tests
echo "4. Template Initialization Tests"
echo "--------------------------------"

# Create temporary directory for tests
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Test systemd template
if cd "$TEMP_DIR" && mkdir test-systemd && cd test-systemd; then
    run_test "Init systemd template" "nix flake init -t $OLDPWD#systemd 2>/dev/null"
    run_test "Systemd template has flake.nix" "[[ -f flake.nix ]]"
    run_test "Systemd template has module.nix" "[[ -f module.nix ]]"
    cd "$OLDPWD" || exit 1
fi

# Test app template
if cd "$TEMP_DIR" && mkdir test-app && cd test-app; then
    run_test "Init app template" "nix flake init -t $OLDPWD#app 2>/dev/null"
    run_test "App template has flake.nix" "[[ -f flake.nix ]]"
    run_test "App template has default.nix" "[[ -f default.nix ]]"
    cd "$OLDPWD" || exit 1
fi

# Test script template
if cd "$TEMP_DIR" && mkdir test-script && cd test-script; then
    run_test "Init script template" "nix flake init -t $OLDPWD#script 2>/dev/null"
    run_test "Script template has flake.nix" "[[ -f flake.nix ]]"
    run_test "Script template has deploy.sh" "[[ -f deploy.sh ]]"
    cd "$OLDPWD" || exit 1
fi
echo ""

# Test 5: File permissions
echo "5. File Permissions Tests"
echo "------------------------"
run_test "deploy.sh is executable" "[[ -x examples/deploy-script/deploy.sh ]]"
echo ""

# Test 6: SOPS configuration validation
echo "6. SOPS Configuration Tests"
echo "--------------------------"
run_test "Main .sops.yaml valid YAML" "yq eval . .sops.yaml > /dev/null 2>&1"
run_test "systemd .sops.yaml valid" "yq eval . examples/systemd-web-api/.sops.yaml > /dev/null 2>&1"
run_test "cli-tool .sops.yaml valid" "yq eval . examples/cli-tool/.sops.yaml > /dev/null 2>&1"
run_test "deploy-script .sops.yaml valid" "yq eval . examples/deploy-script/.sops.yaml > /dev/null 2>&1"
echo ""

# Final report
echo "================================================"
echo "                 TEST RESULTS                   "
echo "================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [[ $FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}✅ All tests passed successfully!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi