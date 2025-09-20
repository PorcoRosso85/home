#!/usr/bin/env bash
# Test: Step 4 Enhanced SID Reverse Lookup and Process-Internal Duplicate Prevention
# Tests new oc_session_index_* functions for bidirectional lookup and statistics

set -euo pipefail

echo "=== Step 4 Enhanced Features Test ==="
echo "Testing SID reverse lookup and process-internal duplicate prevention"
echo

# Source session helper functions
source ./lib/session-helper.sh

# Test directory setup
TEST_BASE="/tmp/step4_test_$$"
mkdir -p "$TEST_BASE"
export OPENCODE_SESSION_DIR="$TEST_BASE"

echo "✅ Test environment setup: $TEST_BASE"
echo

# Setup test data
setup_test_data() {
    echo "Setting up test data..."

    # Create test directories
    mkdir -p "$TEST_BASE/project-a" "$TEST_BASE/project-b" "$TEST_BASE/project-c"

    # Add test records
    oc_session_index_append "$TEST_BASE/project-a" "http://127.0.0.1:4096" "ses_alpha123"
    oc_session_index_append "$TEST_BASE/project-b" "http://127.0.0.1:4096" "ses_beta456"
    oc_session_index_append "$TEST_BASE/project-c" "http://127.0.0.1:4097" "ses_gamma789"
    oc_session_index_append "$TEST_BASE/project-a" "http://127.0.0.1:4097" "ses_alpha999"

    echo "✅ Test data setup complete"
}

# Test 1: SID to directory lookup
test_sid_to_dir() {
    echo "🔬 Test 1: SID to Directory Lookup"

    local dir_result
    if dir_result=$(oc_session_index_sid_to_dir "ses_alpha123" 2>/dev/null); then
        if [[ "$dir_result" == "$TEST_BASE/project-a" ]]; then
            echo "✅ SID to dir lookup succeeded: ses_alpha123 → $dir_result"
        else
            echo "❌ Unexpected directory result: $dir_result"
            return 1
        fi
    else
        echo "❌ SID to dir lookup failed"
        return 1
    fi

    # Test nonexistent session
    if dir_result=$(oc_session_index_sid_to_dir "ses_nonexistent" 2>/dev/null); then
        if [[ -z "$dir_result" ]]; then
            echo "✅ Nonexistent SID correctly returns empty result"
        else
            echo "❌ Nonexistent SID should return empty, got: $dir_result"
            return 1
        fi
    else
        echo "❌ Nonexistent SID lookup should succeed with empty result"
        return 1
    fi

    echo "✅ SID to directory lookup test passed"
    return 0
}

# Test 2: List directories by host:port
test_dirs_by_hostport() {
    echo "🔬 Test 2: List Directories by Host:Port"

    local dirs_4096
    if dirs_4096=$(oc_session_index_list_dirs_by_hostport "127.0.0.1:4096" 2>/dev/null); then
        local count_4096=$(echo "$dirs_4096" | wc -l)
        if [[ $count_4096 -eq 2 ]]; then
            echo "✅ Found $count_4096 directories for 127.0.0.1:4096"
            echo "   Directories: $(echo "$dirs_4096" | tr '\\n' ' ')"
        else
            echo "❌ Expected 2 directories for 127.0.0.1:4096, got $count_4096"
            return 1
        fi
    else
        echo "❌ List directories by host:port failed"
        return 1
    fi

    local dirs_4097
    if dirs_4097=$(oc_session_index_list_dirs_by_hostport "127.0.0.1:4097" 2>/dev/null); then
        local count_4097=$(echo "$dirs_4097" | wc -l)
        if [[ $count_4097 -eq 2 ]]; then
            echo "✅ Found $count_4097 directories for 127.0.0.1:4097"
        else
            echo "❌ Expected 2 directories for 127.0.0.1:4097, got $count_4097"
            return 1
        fi
    else
        echo "❌ List directories by host:port failed"
        return 1
    fi

    echo "✅ List directories by host:port test passed"
    return 0
}

# Test 3: List session IDs by directory
test_sids_by_dir() {
    echo "🔬 Test 3: List Session IDs by Directory"

    local sids_project_a
    if sids_project_a=$(oc_session_index_list_sids_by_dir "$TEST_BASE/project-a" 2>/dev/null); then
        local count_a=$(echo "$sids_project_a" | wc -l)
        if [[ $count_a -eq 2 ]]; then
            echo "✅ Found $count_a sessions for project-a"
            echo "   Sessions: $(echo "$sids_project_a" | tr '\\n' ' ')"
        else
            echo "❌ Expected 2 sessions for project-a, got $count_a"
            return 1
        fi
    else
        echo "❌ List sessions by directory failed"
        return 1
    fi

    local sids_project_b
    if sids_project_b=$(oc_session_index_list_sids_by_dir "$TEST_BASE/project-b" 2>/dev/null); then
        local count_b=$(echo "$sids_project_b" | wc -l)
        if [[ $count_b -eq 1 ]]; then
            echo "✅ Found $count_b session for project-b"
        else
            echo "❌ Expected 1 session for project-b, got $count_b"
            return 1
        fi
    else
        echo "❌ List sessions by directory failed"
        return 1
    fi

    echo "✅ List session IDs by directory test passed"
    return 0
}

# Test 4: Duplicate statistics
test_duplicate_stats() {
    echo "🔬 Test 4: Duplicate Statistics"

    local stats
    if stats=$(oc_session_index_get_duplicate_stats 2>/dev/null); then
        local total_records=$(echo "$stats" | jq -r '.totalRecords')
        local unique_hostports=$(echo "$stats" | jq -r '.uniqueHostPorts')
        local unique_sessions=$(echo "$stats" | jq -r '.uniqueSessions')

        echo "Statistics JSON: $stats"

        if [[ $total_records -eq 4 ]] && [[ $unique_hostports -eq 2 ]] && [[ $unique_sessions -eq 4 ]]; then
            echo "✅ Statistics correct: $total_records records, $unique_hostports host:ports, $unique_sessions sessions"
        else
            echo "❌ Statistics incorrect: expected 4 records, 2 host:ports, 4 sessions"
            echo "   Got: $total_records records, $unique_hostports host:ports, $unique_sessions sessions"
            return 1
        fi
    else
        echo "❌ Duplicate statistics failed"
        return 1
    fi

    echo "✅ Duplicate statistics test passed"
    return 0
}

# Test 5: Session integration
test_session_integration() {
    echo "🔬 Test 5: Session Integration"

    # Test successful integration
    if oc_session_index_integrate_with_session "$TEST_BASE/project-new" "http://127.0.0.1:4096" "ses_new123" 2>/dev/null; then
        echo "✅ Session integration succeeded"
    else
        echo "❌ Session integration failed"
        return 1
    fi

    # Test duplicate integration (should not fail but log warning)
    if oc_session_index_integrate_with_session "$TEST_BASE/project-new" "http://127.0.0.1:4096" "ses_new123" 2>/dev/null; then
        echo "✅ Duplicate session integration handled gracefully"
    else
        echo "❌ Duplicate session integration should not fail"
        return 1
    fi

    echo "✅ Session integration test passed"
    return 0
}

# Cleanup function
cleanup() {
    rm -rf "$TEST_BASE"
}
trap cleanup EXIT

# Run all tests
echo "🔄 Running Step 4 Enhanced Features Tests"
echo

# Setup test data first
setup_test_data
echo

test_count=0
passed_count=0

echo "Test 1/5: SID to Directory Lookup"
if test_sid_to_dir; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 2/5: List Directories by Host:Port"
if test_dirs_by_hostport; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 3/5: List Session IDs by Directory"
if test_sids_by_dir; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 4/5: Duplicate Statistics"
if test_duplicate_stats; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 5/5: Session Integration"
if test_session_integration; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

# Final results
if [[ $passed_count -eq $test_count ]]; then
    echo "🟢 STEP 4 ENHANCED FEATURES: ALL TESTS PASSED (GREEN) ✅"
    echo "   Passed: $passed_count/$test_count enhanced feature tests"
    echo "   SID reverse lookup and duplicate prevention working correctly"
else
    echo "🔴 STEP 4 ENHANCED FEATURES: SOME TESTS FAILED (RED) ❌"
    echo "   Passed: $passed_count/$test_count enhanced feature tests"
fi

echo
echo "🏁 Step 4 Enhanced Features Test Completed!"
echo "   Tested: SID→dir lookup, dir→SID lists, host:port→dirs, statistics, integration"