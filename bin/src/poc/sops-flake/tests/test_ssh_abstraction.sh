#!/usr/bin/env bash
set -uo pipefail

echo '🧪 Testing SSH Key Abstraction'
echo '================================'

# Test 1: Check if module.nix has sopsKeyPath option
echo -n 'Testing sopsKeyPath option existence... '
if grep -q 'sopsKeyPath.*mkOption' module.nix 2>/dev/null; then
    echo '✅ PASS'
else
    echo '❌ FAIL: sopsKeyPath option not found in module.nix'
    exit 1
fi

# Test 2: Check if hardcoded path is removed
echo -n 'Testing removal of hardcoded SSH path... '
if grep -q '/etc/ssh/ssh_host_ed25519_key' module.nix 2>/dev/null; then
    echo '❌ FAIL: Hardcoded SSH path still exists'
    exit 1
else
    echo '✅ PASS'
fi

# Test 3: Check if init script uses abstraction
echo -n 'Testing init script abstraction... '
if grep -q 'cat /etc/ssh/' scripts/init-project.sh 2>/dev/null; then
    echo '⚠️  WARN: Init script still has direct SSH path access'
else
    echo '✅ PASS'
fi

echo ''
echo 'SSH Abstraction Test Complete'
