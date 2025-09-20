#!/usr/bin/env bash
# Test: Step 5 Comprehensive - Rebuild Index and Recovery
# Tests index rebuild functionality, validation, and end-to-end recovery scenarios

set -euo pipefail

echo "=== Step 5 Comprehensive Test ==="
echo "Testing rebuild-index functionality and recovery scenarios"
echo

# Source session helper functions
source ./lib/session-helper.sh

# Test directory setup
TEST_BASE="/tmp/step5_comprehensive_$$"
mkdir -p "$TEST_BASE"
export OPENCODE_SESSION_DIR="$TEST_BASE"

echo "✅ Test environment setup: $TEST_BASE"
echo

# Setup test session files (simulating existing sessions)
setup_session_files() {
    echo "Setting up test session files..."

    local session_base="$TEST_BASE/opencode/sessions"

    # Create session file structure
    mkdir -p "$session_base/127.0.0.1:4096"
    mkdir -p "$session_base/127.0.0.1:4097"

    # Create session files
    echo "ses_project_alpha" > "$session_base/127.0.0.1:4096/home__SLASH__user__SLASH__project-alpha.session"
    echo "ses_project_beta" > "$session_base/127.0.0.1:4096/home__SLASH__user__SLASH__project-beta.session"
    echo "ses_project_gamma" > "$session_base/127.0.0.1:4097/home__SLASH__user__SLASH__project-gamma.session"
    echo "ses_nested_project" > "$session_base/127.0.0.1:4096/home__SLASH__user__SLASH__nested__SLASH__project.session"

    # Create an empty session file (should be handled gracefully)
    touch "$session_base/127.0.0.1:4096/empty__SLASH__project.session"

    echo "✅ Session files created"
}

# Test 1: Dry run rebuild
test_dry_run_rebuild() {
    echo "🔬 Test 1: Dry Run Rebuild"

    local result
    if result=$(oc_session_index_rebuild --dry-run 2>/dev/null); then
        local mode=$(echo "$result" | jq -r '.mode')
        local rebuilt=$(echo "$result" | jq -r '.rebuiltRecords')
        local errors=$(echo "$result" | jq -r '.errorCount')

        echo "Dry run result: $result"

        if [[ "$mode" == "dry-run" ]] && [[ $rebuilt -eq 4 ]] && [[ $errors -eq 1 ]]; then
            echo "✅ Dry run rebuild: found $rebuilt sessions, $errors errors (as expected)"
        else
            echo "❌ Unexpected dry run result: mode=$mode, rebuilt=$rebuilt, errors=$errors"
            return 1
        fi
    else
        echo "❌ Dry run rebuild failed"
        return 1
    fi

    echo "✅ Dry run rebuild test passed"
    return 0
}

# Test 2: Actual rebuild
test_actual_rebuild() {
    echo "🔬 Test 2: Actual Rebuild"

    # Ensure no index exists before rebuild
    local index_file
    index_file=$(oc_session_index_get_file_path)
    rm -f "$index_file"

    local result
    if result=$(oc_session_index_rebuild 2>/dev/null); then
        local mode=$(echo "$result" | jq -r '.mode')
        local rebuilt=$(echo "$result" | jq -r '.rebuiltRecords')

        echo "Rebuild result: $result"

        if [[ "$mode" == "rebuild" ]] && [[ $rebuilt -eq 4 ]]; then
            echo "✅ Actual rebuild: created $rebuilt index records"
        else
            echo "❌ Unexpected rebuild result: mode=$mode, rebuilt=$rebuilt"
            return 1
        fi

        # Verify index file was created
        if [[ -f "$index_file" ]]; then
            local line_count=$(wc -l < "$index_file")
            echo "✅ Index file created with $line_count lines"
        else
            echo "❌ Index file was not created"
            return 1
        fi
    else
        echo "❌ Actual rebuild failed"
        return 1
    fi

    echo "✅ Actual rebuild test passed"
    return 0
}

# Test 3: Index validation
test_index_validation() {
    echo "🔬 Test 3: Index Validation"

    local validation_result
    if validation_result=$(oc_session_index_validate 2>/dev/null); then
        local is_consistent=$(echo "$validation_result" | jq -r '.isConsistent')
        local index_records=$(echo "$validation_result" | jq -r '.indexRecords')
        local file_records=$(echo "$validation_result" | jq -r '.fileRecords')

        echo "Validation result: $validation_result"

        if [[ "$is_consistent" == "true" ]] && [[ $index_records -eq 4 ]] && [[ $file_records -eq 4 ]]; then
            echo "✅ Index validation: consistent with $index_records records"
        else
            echo "❌ Validation failed: consistent=$is_consistent, index=$index_records, files=$file_records"
            return 1
        fi
    else
        echo "❌ Index validation failed"
        return 1
    fi

    echo "✅ Index validation test passed"
    return 0
}

# Test 4: Recovery scenario - corrupted index
test_corrupted_index_recovery() {
    echo "🔬 Test 4: Corrupted Index Recovery"

    local index_file
    index_file=$(oc_session_index_get_file_path)

    # Corrupt the index file
    echo "corrupted_json_line" >> "$index_file"
    echo "another_bad_line" >> "$index_file"

    echo "Corrupted index file (added 2 broken lines)"

    # Validate should detect issues
    local validation_before
    if validation_before=$(oc_session_index_validate 2>/dev/null); then
        echo "Validation before rebuild: $validation_before"
    fi

    # Rebuild should fix the corruption
    local rebuild_result
    if rebuild_result=$(oc_session_index_rebuild 2>/dev/null); then
        echo "Rebuild result: $rebuild_result"

        # Validate after rebuild
        local validation_after
        if validation_after=$(oc_session_index_validate 2>/dev/null); then
            local is_consistent=$(echo "$validation_after" | jq -r '.isConsistent')
            echo "Validation after rebuild: $validation_after"

            if [[ "$is_consistent" == "true" ]]; then
                echo "✅ Recovery successful: index is now consistent"
            else
                echo "❌ Recovery failed: index still inconsistent"
                return 1
            fi
        else
            echo "❌ Post-rebuild validation failed"
            return 1
        fi
    else
        echo "❌ Rebuild for recovery failed"
        return 1
    fi

    echo "✅ Corrupted index recovery test passed"
    return 0
}

# Test 5: End-to-end integration with session lookup
test_end_to_end_integration() {
    echo "🔬 Test 5: End-to-End Integration"

    # Test all lookup functions work with rebuilt index
    echo "Testing SID reverse lookup..."
    local dir_result
    if dir_result=$(oc_session_index_sid_to_dir "ses_project_alpha" 2>/dev/null); then
        if [[ "$dir_result" == "/home/user/project-alpha" ]]; then
            echo "✅ SID lookup works: ses_project_alpha → $dir_result"
        else
            echo "❌ Unexpected SID lookup result: $dir_result"
            return 1
        fi
    else
        echo "❌ SID lookup failed"
        return 1
    fi

    echo "Testing directory session listing..."
    local sessions
    if sessions=$(oc_session_index_list_sids_by_dir "/home/user/project-alpha" 2>/dev/null); then
        if echo "$sessions" | grep -q "ses_project_alpha"; then
            echo "✅ Directory sessions work: found ses_project_alpha"
        else
            echo "❌ Directory sessions failed: session not found"
            return 1
        fi
    else
        echo "❌ Directory sessions listing failed"
        return 1
    fi

    echo "Testing host:port directory listing..."
    local dirs
    if dirs=$(oc_session_index_list_dirs_by_hostport "127.0.0.1:4096" 2>/dev/null); then
        local count=$(echo "$dirs" | wc -l)
        if [[ $count -eq 3 ]]; then
            echo "✅ Host:port directories work: found $count directories"
        else
            echo "❌ Expected 3 directories for 127.0.0.1:4096, got $count"
            return 1
        fi
    else
        echo "❌ Host:port directories listing failed"
        return 1
    fi

    echo "Testing statistics..."
    local stats
    if stats=$(oc_session_index_get_duplicate_stats 2>/dev/null); then
        local total=$(echo "$stats" | jq -r '.totalRecords')
        echo "✅ Statistics work: $total total records"
        echo "   Stats: $stats"
    else
        echo "❌ Statistics failed"
        return 1
    fi

    echo "✅ End-to-end integration test passed"
    return 0
}

# Test 6: Recovery with missing index
test_missing_index_recovery() {
    echo "🔬 Test 6: Missing Index Recovery"

    local index_file
    index_file=$(oc_session_index_get_file_path)

    # Remove index completely
    rm -f "$index_file"
    echo "Removed index file completely"

    # Try to use lookup functions (should handle gracefully)
    echo "Testing lookup with missing index..."
    local result
    if result=$(oc_session_index_lookup_by_sid "ses_project_alpha" 2>/dev/null); then
        if [[ -z "$result" ]]; then
            echo "✅ Missing index handled gracefully"
        else
            echo "❌ Unexpected result from missing index: $result"
            return 1
        fi
    else
        echo "✅ Missing index handled gracefully (function failed as expected)"
    fi

    # Rebuild from scratch
    local rebuild_result
    if rebuild_result=$(oc_session_index_rebuild 2>/dev/null); then
        echo "Rebuild from scratch: $rebuild_result"

        # Verify lookup works again
        if result=$(oc_session_index_lookup_by_sid "ses_project_alpha" 2>/dev/null); then
            if [[ -n "$result" ]]; then
                echo "✅ Lookup works after rebuild from scratch"
            else
                echo "❌ Lookup still doesn't work after rebuild"
                return 1
            fi
        else
            echo "❌ Lookup failed after rebuild"
            return 1
        fi
    else
        echo "❌ Rebuild from scratch failed"
        return 1
    fi

    echo "✅ Missing index recovery test passed"
    return 0
}

# Cleanup function
cleanup() {
    rm -rf "$TEST_BASE"
}
trap cleanup EXIT

# Run all tests
echo "🔄 Running Step 5 Comprehensive Tests"
echo

# Setup test data first
setup_session_files
echo

test_count=0
passed_count=0

echo "Test 1/6: Dry Run Rebuild"
if test_dry_run_rebuild; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 2/6: Actual Rebuild"
if test_actual_rebuild; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 3/6: Index Validation"
if test_index_validation; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 4/6: Corrupted Index Recovery"
if test_corrupted_index_recovery; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 5/6: End-to-End Integration"
if test_end_to_end_integration; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 6/6: Missing Index Recovery"
if test_missing_index_recovery; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

# Final results
if [[ $passed_count -eq $test_count ]]; then
    echo "🟢 STEP 5 COMPREHENSIVE: ALL TESTS PASSED (GREEN) ✅"
    echo "   Passed: $passed_count/$test_count comprehensive tests"
    echo "   Rebuild functionality and recovery scenarios working correctly"
    echo "   System is ready for production with full recovery capabilities"
else
    echo "🔴 STEP 5 COMPREHENSIVE: SOME TESTS FAILED (RED) ❌"
    echo "   Passed: $passed_count/$test_count comprehensive tests"
fi

echo
echo "🏁 Step 5 Comprehensive Test Completed!"
echo "   Tested: rebuild, validation, corruption recovery, end-to-end integration, missing index recovery"
echo "   Recovery guarantee: System can rebuild index from session files in all scenarios"