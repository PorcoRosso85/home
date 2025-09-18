#!/usr/bin/env bash
set -uo pipefail

echo '🔍 Production-Ready Integration Test'
echo '====================================='

PASS=0
FAIL=0

# Test Suite 1: Determinism
echo ''
echo '📦 Testing Determinism...'
[[ -f flake.nix ]] && grep -q 'nixos-23.11' flake.nix && ((PASS++)) || ((FAIL++))
grep -q 'sops-nix/0.7.1' flake.nix && ((PASS++)) || ((FAIL++))

# Test Suite 2: Purity
echo '🔒 Testing Purity...'
! grep -q '/etc/ssh/ssh_host' module.nix && ((PASS++)) || ((FAIL++))
grep -q 'sopsKeyPath.*mkOption' module.nix && ((PASS++)) || ((FAIL++))

# Test Suite 3: Non-destructive Operations
echo '💾 Testing Non-destructive Operations...'
grep -q 'encrypt-pure' flake.nix && ((PASS++)) || ((FAIL++))
! grep -rq 'sops -e -i' . --include="*.sh" && ((PASS++)) || ((FAIL++))

# Test Suite 4: Declarative Configuration
echo '📝 Testing Declarative Configuration...'
grep -q 'environment.etc.*sops.yaml' module.nix && ((PASS++)) || ((FAIL++))

# Summary
echo ''
echo '====================================='
echo "Results: ✅ $PASS passed, ❌ $FAIL failed"

if [[ $FAIL -eq 0 ]]; then
    echo ''
    echo '🎉 PRODUCTION READY!'
    exit 0
else
    echo ''
    echo '⚠️  Not production ready yet'
    exit 1
fi
