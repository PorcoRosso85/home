#!/usr/bin/env bash
# Edge case testing for session key robustness (RED phase)
# Tests current implementation against complex real-world scenarios

set -euo pipefail

# Source the session helper functions
source ./lib/session-helper.sh

echo "=== Session Key Edge Case Testing ==="
echo "Testing oc_session_project_key against complex scenarios"
echo

# Test cases covering production edge cases
declare -a edge_cases=(
    # Delimiter collision tests
    "/path/with__SLASH__in/name"
    "/another__SLASH__path/subdir"

    # Unicode and international paths
    "/home/ユーザー/プロジェクト"
    "/项目/中文目录"
    "/домой/проект"

    # Special characters and spaces
    "/path with spaces/project"
    "/path/with'quotes/and\"double"
    "/path/with[brackets]/and(parens)"
    "/path/with@symbols#and\$dollars"

    # Edge formatting cases
    "/path/ending/with/slash/"
    "/path///multiple///slashes"
    "/single"
    "/"

    # Real-world project patterns
    "/Users/dev/my-awesome-project_v2.1"
    "/tmp/.hidden-project/sub/.config"
    "/var/log/app-name_2024-12-20_backup"
    "/mnt/external/Project (Copy)/work"
)

echo "Edge case results:"
echo "==================="

declare -A session_keys
collision_detected=false
error_detected=false

for path in "${edge_cases[@]}"; do
    echo "Testing path: '$path'"

    # Test with error handling
    if key=$(oc_session_project_key "$path" 2>/dev/null); then
        echo "   Key: '$key'"

        # Check for collisions (use hash approach for complex keys)
        key_hash=$(echo "$key" | sha256sum | cut -d' ' -f1)
        if [[ -n "${session_keys[$key_hash]:-}" ]]; then
            echo "   🔴 COLLISION DETECTED!"
            echo "      Conflicts with: '${session_keys[$key_hash]}'"
            collision_detected=true
        else
            session_keys[$key_hash]="$path"
        fi

        # Check for problematic characters in key
        if [[ "$key" =~ [[:space:]] ]]; then
            echo "   ⚠️  WARNING: Key contains spaces"
        fi

        if [[ "$key" =~ [^a-zA-Z0-9_] ]]; then
            echo "   ⚠️  WARNING: Key contains special characters"
        fi

    else
        echo "   ❌ ERROR: Function failed for this path"
        error_detected=true
    fi
    echo
done

echo "=== Test Summary ==="
total_paths=${#edge_cases[@]}
unique_keys=${#session_keys[@]}

echo "Total paths tested: $total_paths"
echo "Unique keys generated: $unique_keys"

if [[ "$error_detected" == "true" ]]; then
    echo "❌ ERRORS: Some paths caused function failures"
    exit 1
elif [[ "$collision_detected" == "true" ]]; then
    echo "❌ COLLISIONS: Multiple paths mapped to same keys"
    exit 1
elif [[ "$unique_keys" -ne "$total_paths" ]]; then
    echo "❌ MISMATCH: Not all paths generated unique keys"
    exit 1
else
    echo "✅ SUCCESS: All edge cases handled safely"
    echo "Current implementation demonstrates robustness across:"
    echo "  - Delimiter conflicts (__SLASH__ in paths)"
    echo "  - Unicode characters (Japanese, Chinese, Cyrillic)"
    echo "  - Special characters and spaces"
    echo "  - Edge formatting (trailing slashes, multiples)"
    echo "  - Real-world project naming patterns"
    exit 0
fi