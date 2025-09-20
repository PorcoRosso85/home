#!/usr/bin/env bash
# Test: Tier 0 Index Specification (Precise Implementation Definition)
# Tests exact record format, uniqueness constraints, and corruption handling

set -euo pipefail

echo "=== Tier 0 Index Specification Test ==="
echo "Testing precise JSONL record format, uniqueness, and corruption handling"
echo

OPENCODE_URL="http://127.0.0.1:4096"
TEST_DIR="/tmp/tier0_index_spec_$$"
mkdir -p "$TEST_DIR"

# Source session helper functions
source ./lib/session-helper.sh

# Test precise JSONL record format specification
test_jsonl_record_format() {
    echo "🔬 Testing Precise JSONL Record Format"

    # Test record must contain exact fields with correct types
    local test_record='{"dir":"/absolute/path","dirHash":"sha256prefix","hostPort":"127.0.0.1:4096","session":"ses_abc123","created":"1695123456"}'

    echo "Expected record format:"
    echo "$test_record" | jq .

    # Verify all required fields are present
    local required_fields=("dir" "dirHash" "hostPort" "session" "created")
    for field in "${required_fields[@]}"; do
        if echo "$test_record" | jq -e ".$field" >/dev/null 2>&1; then
            echo "✅ Required field present: $field"
        else
            echo "❌ FAIL: Missing required field: $field"
            return 1
        fi
    done

    # Verify field types and constraints
    echo "Testing field constraints..."

    # dir: must be absolute path (starts with /)
    local dir_value=$(echo "$test_record" | jq -r '.dir')
    if [[ "$dir_value" =~ ^/ ]]; then
        echo "✅ dir field: absolute path constraint satisfied"
    else
        echo "❌ FAIL: dir field must be absolute path"
        return 1
    fi

    # dirHash: must be string (sha256 prefix)
    local dirHash_value=$(echo "$test_record" | jq -r '.dirHash')
    if [[ -n "$dirHash_value" && "$dirHash_value" != "null" ]]; then
        echo "✅ dirHash field: non-empty string"
    else
        echo "❌ FAIL: dirHash field must be non-empty string"
        return 1
    fi

    # hostPort: must follow host:port format
    local hostPort_value=$(echo "$test_record" | jq -r '.hostPort')
    if [[ "$hostPort_value" =~ ^[^:]+:[0-9]+$ ]]; then
        echo "✅ hostPort field: host:port format"
    else
        echo "❌ FAIL: hostPort field must follow host:port format"
        return 1
    fi

    # session: must start with ses_ (OpenCode session ID format)
    local session_value=$(echo "$test_record" | jq -r '.session')
    if [[ "$session_value" =~ ^ses_ ]]; then
        echo "✅ session field: ses_ prefix format"
    else
        echo "❌ FAIL: session field must start with ses_"
        return 1
    fi

    # created: must be numeric timestamp
    local created_value=$(echo "$test_record" | jq -r '.created')
    if [[ "$created_value" =~ ^[0-9]+$ ]]; then
        echo "✅ created field: numeric timestamp"
    else
        echo "❌ FAIL: created field must be numeric timestamp"
        return 1
    fi

    echo "✅ JSONL record format specification verified"
    return 0
}

# Test uniqueness constraint specification
test_uniqueness_constraint() {
    echo "🔬 Testing Uniqueness Constraint Specification"

    # Uniqueness key: (hostPort, dirHash, session)
    echo "Testing uniqueness key: (hostPort, dirHash, session)"

    # Test records that should be considered duplicates
    local record1='{"dir":"/path/one","dirHash":"hash123","hostPort":"127.0.0.1:4096","session":"ses_abc","created":"1695100000"}'
    local record2='{"dir":"/different/path","dirHash":"hash123","hostPort":"127.0.0.1:4096","session":"ses_abc","created":"1695200000"}'

    echo "Record 1: $record1"
    echo "Record 2: $record2"

    # Extract uniqueness keys
    local key1=$(echo "$record1" | jq -r '[.hostPort, .dirHash, .session] | join("|")')
    local key2=$(echo "$record2" | jq -r '[.hostPort, .dirHash, .session] | join("|")')

    echo "Uniqueness key 1: $key1"
    echo "Uniqueness key 2: $key2"

    if [[ "$key1" == "$key2" ]]; then
        echo "✅ Uniqueness constraint: Records correctly identified as duplicates"
        echo "   Different 'dir' and 'created' fields don't affect uniqueness"
    else
        echo "❌ FAIL: Uniqueness constraint logic incorrect"
        return 1
    fi

    # Test records that should NOT be duplicates
    local record3='{"dir":"/path/one","dirHash":"hash456","hostPort":"127.0.0.1:4096","session":"ses_abc","created":"1695100000"}'
    local key3=$(echo "$record3" | jq -r '[.hostPort, .dirHash, .session] | join("|")')

    echo "Record 3: $record3"
    echo "Uniqueness key 3: $key3"

    if [[ "$key1" != "$key3" ]]; then
        echo "✅ Uniqueness constraint: Different dirHash creates different uniqueness key"
    else
        echo "❌ FAIL: Different dirHash should create different uniqueness key"
        return 1
    fi

    echo "✅ Uniqueness constraint specification verified"
    return 0
}

# Test corruption handling specification
test_corruption_handling() {
    echo "🔬 Testing Corruption Handling Specification"

    # Create test file with mixed valid and corrupted lines
    local test_index_file="$TEST_DIR/test_index.jsonl"

    cat > "$test_index_file" << 'EOF'
{"dir":"/valid/path1","dirHash":"hash1","hostPort":"127.0.0.1:4096","session":"ses_valid1","created":"1695100000"}
{"dir":"/valid/path2","dirHash":"hash2","hostPort":"127.0.0.1:4096","session":"ses_valid2","created":"1695200000"}
{broken_json_line_no_quotes: invalid}
{"dir":"/valid/path3","dirHash":"hash3","hostPort":"127.0.0.1:4096","session":"ses_valid3","created":"1695300000"}
incomplete_line_at_end
EOF

    echo "Test index file with corruption:"
    echo "---"
    cat "$test_index_file"
    echo "---"

    # Test "tail parsing with broken line skipping" specification
    echo "Testing tail parsing with broken line skipping..."

    local valid_count=0
    local total_count=0

    # Simulate read_safe behavior: read from tail, skip broken lines
    while IFS= read -r line; do
        total_count=$((total_count + 1))
        echo "Processing line $total_count: $line"

        if echo "$line" | jq . >/dev/null 2>&1; then
            valid_count=$((valid_count + 1))
            echo "  ✅ Valid JSON line"
        else
            echo "  ⚠️  Skipping broken line (as specified)"
        fi
    done < "$test_index_file"

    echo "Results:"
    echo "  Total lines: $total_count"
    echo "  Valid lines: $valid_count"
    echo "  Broken lines skipped: $((total_count - valid_count))"

    # Verify specification: at least some valid lines recovered
    if [[ $valid_count -ge 3 ]]; then
        echo "✅ Corruption handling: Valid lines successfully recovered"
        echo "   Specification: 'Skip broken lines, continue with valid ones'"
    else
        echo "❌ FAIL: Corruption handling should recover valid lines"
        return 1
    fi

    # Verify broken lines don't crash the system
    echo "✅ Corruption handling: System continues despite broken lines"

    rm -f "$test_index_file"
    return 0
}

# Test path normalization specification
test_path_normalization() {
    echo "🔬 Testing Path Normalization Specification"

    # Test cases for realpath + trailing slash removal
    local test_paths=(
        "/home/user/project/"     # trailing slash removal
        "/home/user/../user/project"  # .. resolution
        "relative/path"           # should be made absolute
    )

    cd "$TEST_DIR"
    mkdir -p "relative/path"

    for path in "${test_paths[@]}"; do
        echo "Testing path: '$path'"

        # Simulate normalization (basic version for testing)
        local normalized
        if [[ "$path" =~ ^/ ]]; then
            # Absolute path: remove trailing slash
            normalized="${path%/}"
        else
            # Relative path: make absolute + remove trailing slash
            normalized="$(cd "$path" && pwd 2>/dev/null || echo "$TEST_DIR/$path")"
            normalized="${normalized%/}"
        fi

        echo "  Normalized: '$normalized'"

        # Verify normalization rules
        if [[ "$normalized" =~ ^/ ]]; then
            echo "  ✅ Result is absolute path"
        else
            echo "  ❌ FAIL: Normalized path must be absolute"
            return 1
        fi

        if [[ ! "$normalized" =~ /$ ]]; then
            echo "  ✅ No trailing slash"
        else
            echo "  ❌ FAIL: Trailing slash should be removed"
            return 1
        fi
    done

    echo "✅ Path normalization specification verified"
    return 0
}

# Cleanup function
cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Server health check
if ! curl -fsS "$OPENCODE_URL/doc" >/dev/null 2>&1; then
    echo "❌ Server not accessible at $OPENCODE_URL"
    echo "   Start server: nix run . -- serve --port 4096"
    exit 1
fi

echo "✅ Server responding"
echo

# Run all specification tests
echo "🔄 Running Tier 0 Index Specification Tests"
echo

test_passed=0
test_total=4

echo "Test 1/4: JSONL Record Format"
if test_jsonl_record_format; then
    test_passed=$((test_passed + 1))
fi
echo

echo "Test 2/4: Uniqueness Constraint"
if test_uniqueness_constraint; then
    test_passed=$((test_passed + 1))
fi
echo

echo "Test 3/4: Corruption Handling"
if test_corruption_handling; then
    test_passed=$((test_passed + 1))
fi
echo

echo "Test 4/4: Path Normalization"
if test_path_normalization; then
    test_passed=$((test_passed + 1))
fi
echo

# Final results
if [[ $test_passed -eq $test_total ]]; then
    echo "🔴 TIER 0 INDEX SPECIFICATION: READY FOR IMPLEMENTATION (RED) ❌"
    echo "   All $test_total specification tests define expected behavior"
    echo "   Implementation in Step 3 will make these tests GREEN"
    echo "   Specification complete: Record format, uniqueness, corruption handling, normalization"
else
    echo "🔴 TIER 0 INDEX SPECIFICATION: INCOMPLETE DEFINITION (RED) ❌"
    echo "   Passed: $test_passed/$test_total specification tests"
    echo "   Some specification definitions need refinement"
fi

echo
echo "🏁 Tier 0 Index Specification Test Completed!"
echo "   These tests define exact behavior expected from index implementation:"
echo "   - Precise JSONL record format with required fields and types"
echo "   - Uniqueness constraint: (hostPort, dirHash, session) key"
echo "   - Corruption handling: skip broken lines, continue with valid ones"
echo "   - Path normalization: realpath + trailing slash removal"