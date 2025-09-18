#!/usr/bin/env bash
set -euo pipefail

# Test template selection functionality for sops-flake
PASS_COUNT=0
FAIL_COUNT=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
    return 0
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
    return 0
}

cd "$(dirname "$0")/.."  # Go to sops-flake root

echo '🧪 Testing Template Selection Functionality'
echo '=========================================='

# Test 1: Template directory structure validation
echo ''
echo '📁 Testing template directory structure...'
[[ -d templates ]] && test_pass 'templates/ directory exists' || test_fail 'templates/ directory missing'
[[ -d templates/systemd ]] && test_pass 'templates/systemd/ exists' || test_fail 'templates/systemd/ missing'  
[[ -d templates/app ]] && test_pass 'templates/app/ exists' || test_fail 'templates/app/ missing'

# Check template files
[[ -f templates/systemd/flake.nix.tmpl ]] && test_pass 'systemd template has flake.nix.tmpl' || test_fail 'systemd template missing flake.nix.tmpl'
[[ -f templates/systemd/module.nix.tmpl ]] && test_pass 'systemd template has module.nix.tmpl' || test_fail 'systemd template missing module.nix.tmpl'
[[ -f templates/app/flake.nix.tmpl ]] && test_pass 'app template has flake.nix.tmpl' || test_fail 'app template missing flake.nix.tmpl'
[[ -f templates/app/default.nix.tmpl ]] && test_pass 'app template has default.nix.tmpl' || test_fail 'app template missing default.nix.tmpl'

# Test 2: Template variables
echo ''
echo '🔧 Testing template variables...'
grep -q "{{PROJECT_NAME}}" templates/systemd/flake.nix.tmpl && test_pass 'systemd template contains PROJECT_NAME' || test_fail 'systemd template missing PROJECT_NAME'
grep -q "{{PROJECT_NAME}}" templates/app/flake.nix.tmpl && test_pass 'app template contains PROJECT_NAME' || test_fail 'app template missing PROJECT_NAME'

# Test 3: Script validation
echo ''
echo '⚙️ Testing script functionality...'
./scripts/init-project.sh --help > /dev/null 2>&1 && test_pass 'help option works' || test_fail 'help option failed'

# Test 4: Invalid type handling
echo ''
echo '❌ Testing invalid type handling...'
! ./scripts/init-project.sh test-invalid --type=invalid >/dev/null 2>&1 && test_pass 'invalid type rejected' || test_fail 'invalid type should be rejected'

# Test 5: Project name validation
echo ''
echo '✅ Testing project name validation...'
! ./scripts/init-project.sh "Invalid-Name" --type=systemd >/dev/null 2>&1 && test_pass 'invalid name rejected' || test_fail 'invalid name should be rejected'

# Summary
echo ''
echo '=========================================='
echo "Test Results: ${GREEN}$PASS_COUNT passed${NC}, ${RED}$FAIL_COUNT failed${NC}"

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✅ All template selection tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some template selection tests failed.${NC}"
    exit 1
fi