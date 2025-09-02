#!/usr/bin/env bash
# KISS: Simple test of firejail directory restrictions

echo "=== Test 1: Without firejail ==="
echo "test" > test-dirs/child1/test.txt 2>&1 && echo "✓ Write succeeded" || echo "✗ Write failed"

echo -e "\n=== Test 2: With firejail blacklist ==="
firejail --noprofile --quiet --blacklist=$PWD/test-dirs/child1 \
    bash -c 'echo "test" > test-dirs/child1/test.txt 2>&1' && echo "✓ Write succeeded" || echo "✗ Write blocked"

echo -e "\n=== Test 3: Verify restriction ==="
firejail --noprofile --quiet --blacklist=$PWD/test-dirs/child1 \
    ls test-dirs/child1 2>&1 | grep -q "Permission denied" && echo "✓ Access denied as expected" || echo "✗ Unexpected result"