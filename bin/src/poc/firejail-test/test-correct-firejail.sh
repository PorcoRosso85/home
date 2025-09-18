#!/usr/bin/env bash
# Test correct firejail usage with nix develop

echo "=== Setting up test environment ==="
echo "original content" > restricted-child/secret.txt
echo "Test file reset to: $(cat restricted-child/secret.txt)"

echo -e "\n=== Test 1: WITHOUT firejail (should succeed) ==="
cd /home/nixos/bin/src/poc/firejail-test
python3 -c "
try:
    with open('restricted-child/secret.txt', 'w') as f:
        f.write('modified without firejail')
    print('✓ Write succeeded')
except Exception as e:
    print(f'✗ Write failed: {e}')
"
echo "File content: $(cat restricted-child/secret.txt)"

echo -e "\n=== Test 2: WITH firejail using correct method ==="
echo "original content" > restricted-child/secret.txt  # Reset
cd /home/nixos/bin/src/develop/org
nix develop -c firejail --noprofile --quiet \
    --blacklist=/home/nixos/bin/src/poc/firejail-test/restricted-child \
    --read-only=/nix/store \
    -- python3 -c "
import os
os.chdir('/home/nixos/bin/src/poc/firejail-test')
try:
    with open('restricted-child/secret.txt', 'w') as f:
        f.write('modified with firejail')
    print('✓ Write succeeded (BAD - firejail failed!)')
except Exception as e:
    print(f'✗ Write blocked: {e} (GOOD - firejail works!)')
"
echo "File content: $(cat restricted-child/secret.txt)"

echo -e "\n=== Results ==="
if [ "$(cat restricted-child/secret.txt)" = "original content" ]; then
    echo "✅ SUCCESS: Firejail correctly blocked the modification!"
else
    echo "❌ FAILURE: Firejail did not block the modification"
fi