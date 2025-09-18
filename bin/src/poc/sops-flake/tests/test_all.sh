#!/usr/bin/env bash
set -uo pipefail

PASS_COUNT=0
FAIL_COUNT=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

echo '🧪 Running sops-flake POC Test Suite'
echo '===================================='

# Run template selection tests first
echo ''
echo '🎯 Running template selection tests...'
if ./tests/test_template_selection.sh; then
    test_pass 'Template selection tests passed'
else
    test_fail 'Template selection tests failed'
fi

# Test 1: File structure
echo ''
echo '📁 Testing file structure...'
[[ -f flake.nix ]] && test_pass 'flake.nix exists' || test_fail 'flake.nix missing'
[[ -f module.nix ]] && test_pass 'module.nix exists' || test_fail 'module.nix missing'
[[ -f .sops.yaml ]] && test_pass '.sops.yaml exists' || test_fail '.sops.yaml missing'
[[ -d secrets ]] && test_pass 'secrets/ directory exists' || test_fail 'secrets/ directory missing'
[[ -f README.md ]] && test_pass 'README.md exists' || test_fail 'README.md missing'

# Test 2: Encryption status
echo ''
echo '🔐 Testing encryption...'
if [[ -f secrets/app.yaml ]]; then
    if grep -q 'ENC\[AES256_GCM' secrets/app.yaml; then
        test_pass 'secrets/app.yaml is encrypted'
    else
        test_fail 'secrets/app.yaml is NOT encrypted'
    fi
else
    test_fail 'secrets/app.yaml does not exist'
fi

# Test 3: Module structure
echo ''
echo '📦 Testing NixOS module structure...'
grep -q 'nixosModules.default' flake.nix && test_pass 'NixOS module exported' || test_fail 'NixOS module not exported'
grep -q 'services.sops-app' module.nix && test_pass 'Service option defined' || test_fail 'Service option missing'
grep -q 'sops.secrets' module.nix && test_pass 'Secrets configuration present' || test_fail 'Secrets configuration missing'

# Test 4: Documentation quality
echo ''
echo '📚 Testing documentation...'
if [[ -f README.md ]]; then
    grep -q 'OS側での使用方法' README.md && test_pass 'Usage instructions present' || test_fail 'Usage instructions missing'
    grep -q '責務分離' README.md && test_pass 'Architecture explained' || test_fail 'Architecture not explained'
else
    test_fail 'README.md missing'
fi

# Summary
echo ''
echo '===================================='
echo "Test Results: ${GREEN}$PASS_COUNT passed${NC}, ${RED}$FAIL_COUNT failed${NC}"

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed.${NC}"
    exit 1
fi
