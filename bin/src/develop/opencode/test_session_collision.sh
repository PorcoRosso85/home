#!/usr/bin/env bash
# Session collision detection test (RED phase)
# Tests current implementation to demonstrate the bug

set -euo pipefail

# Source the session helper functions
source ./lib/session-helper.sh

echo "=== Session Collision Detection Test ==="
echo "Testing current oc_session_project_key implementation"
echo

# Test cases that should generate DIFFERENT session keys but currently don't
declare -a test_cases=(
    "/home/nixos/bin/src/sops_flake"
    "/home/nixos/bin/src/sops/flake"
    "/home/user/my_project"
    "/home/user/my/project"
    "/var/log/app_data"
    "/var/log/app/data"
    "/tmp/test_dir"
    "/tmp/test/dir"
)

echo "Current implementation results:"
echo "-------------------------------"

declare -A session_keys
collision_detected=false

for path in "${test_cases[@]}"; do
    key=$(oc_session_project_key "$path")
    echo "Path: $path"
    echo "Key:  $key"

    # Check for collisions
    if [[ -n "${session_keys[$key]:-}" ]]; then
        echo "🔴 COLLISION DETECTED!"
        echo "   '$path' conflicts with '${session_keys[$key]}'"
        echo "   Both map to: '$key'"
        collision_detected=true
    else
        session_keys[$key]="$path"
    fi
    echo
done

echo "=== Test Results ==="
if [[ "$collision_detected" == "true" ]]; then
    echo "❌ FAIL: Naming collisions detected in current implementation"
    echo "This demonstrates the critical bug that needs fixing."
    exit 1
else
    echo "✅ PASS: No collisions detected"
    echo "Current implementation appears safe for these test cases."
    exit 0
fi