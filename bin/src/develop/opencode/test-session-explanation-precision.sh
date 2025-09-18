#!/usr/bin/env bash
set -euo pipefail

# Test: Session Explanation Technical Precision
# Verifies that session management is described with technical accuracy:
# - Server manages state, client holds only ID
# - Clear API flow patterns
# - Precise terminology (avoid "client holds session info")

# Test configuration
readonly TEST_NAME="Session Explanation Technical Precision"
readonly EXIT_SUCCESS=0
readonly EXIT_FAILURE=1

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Test functions
log_info() {
    echo -e "${YELLOW}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $*"
}

# Test 1: README.md should contain precise session explanation
test_readme_session_precision() {
    log_info "Testing README.md for precise session explanation..."
    
    local readme_file="README.md"
    local issues=()
    
    # Check for required precise descriptions
    if ! grep -q "server.*manage.*state" "$readme_file" && ! grep -q "server.*manage.*conversation" "$readme_file"; then
        issues+=("Missing explanation that server manages session state")
    fi
    
    if ! grep -q "client.*holds.*only.*ID\|client.*references.*via.*ID" "$readme_file"; then
        issues+=("Missing explanation that client holds only session ID for reference")
    fi
    
    # Check for correct API flow pattern
    if ! grep -q "POST /session" "$readme_file"; then
        issues+=("Missing POST /session → receive ID pattern")
    fi
    
    if ! grep -q "POST /session/.*id.*/message\|POST /session/\$SID/message" "$readme_file"; then
        issues+=("Missing POST /session/:id/message pattern")
    fi
    
    # Check for problematic ambiguous language (should not exist)
    if grep -q "client.*session.*info\|client.*manages.*session" "$readme_file"; then
        issues+=("Found ambiguous language: 'client holds session info' or 'client manages sessions'")
    fi
    
    # Report results
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "README.md contains precise session explanations"
        return $EXIT_SUCCESS
    else
        log_failure "README.md session explanation issues:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return $EXIT_FAILURE
    fi
}

# Test 2: Documentation should use correct terminology
test_session_terminology() {
    log_info "Testing for correct session terminology across documentation..."
    
    local issues=()
    local files=("README.md" "templates/multi-agent/README.md")
    
    # Words/phrases that should NOT appear (ambiguous)
    local forbidden_phrases=(
        "client.*holds.*session.*info"
        "client.*manages.*session"
        "client.*session.*data"
        "session.*stored.*client"
    )
    
    # Words/phrases that SHOULD appear (precise)
    local required_phrases=(
        "server.*state\|server.*manage"
        "session.*ID\|session.*identifier"
        "client.*reference\|client.*ID"
    )
    
    for file in "${files[@]}"; do
        if [[ ! -f "$file" ]]; then
            continue
        fi
        
        # Check for forbidden ambiguous phrases
        for phrase in "${forbidden_phrases[@]}"; do
            if grep -q "$phrase" "$file"; then
                issues+=("$file contains ambiguous phrase matching: $phrase")
            fi
        done
        
        # Check for at least some required precise phrases
        local found_required=false
        for phrase in "${required_phrases[@]}"; do
            if grep -q "$phrase" "$file"; then
                found_required=true
                break
            fi
        done
        
        if [[ "$found_required" == "false" ]]; then
            issues+=("$file lacks precise session terminology")
        fi
    done
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "Documentation uses correct session terminology"
        return $EXIT_SUCCESS
    else
        log_failure "Session terminology issues:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return $EXIT_FAILURE
    fi
}

# Test 3: Session-manager should have precise technical comments
test_session_manager_precision() {
    log_info "Testing session-manager.sh for precise technical explanations..."
    
    local session_manager="templates/multi-agent/session-manager.sh"
    local issues=()
    
    if [[ ! -f "$session_manager" ]]; then
        log_failure "Session manager file not found: $session_manager"
        return $EXIT_FAILURE
    fi
    
    # Check for comments that should clarify technical precision
    if ! grep -q "Server manages.*state\|Sessions are.*server.*managed" "$session_manager"; then
        issues+=("Missing comment clarifying server manages session state")
    fi
    
    if ! grep -q "Client.*holds.*only.*ID\|Client.*ID.*reference" "$session_manager"; then
        issues+=("Missing comment clarifying client holds only ID for reference")
    fi
    
    # Check for problematic comments (if any)
    if grep -q "# Client.*session.*info\|# Client.*manages.*session" "$session_manager"; then
        issues+=("Found ambiguous comments about client session management")
    fi
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "Session manager contains precise technical explanations"
        return $EXIT_SUCCESS
    else
        log_failure "Session manager precision issues:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return $EXIT_FAILURE
    fi
}

# Test 4: API pattern examples should be technically accurate
test_api_pattern_accuracy() {
    log_info "Testing API pattern examples for technical accuracy..."
    
    local readme_file="README.md"
    local issues=()
    
    # Should show clear pattern: POST /session → get ID → POST /session/:id/message
    local has_session_creation=false
    local has_message_sending=false
    local has_correct_flow=false
    
    if grep -q "POST.*session.*-d.*{}" "$readme_file" || grep -q "POST.*session" "$readme_file"; then
        has_session_creation=true
    fi
    
    if grep -q "POST.*session.*\$SID.*message\|POST.*session.*:id.*message" "$readme_file"; then
        has_message_sending=true
    fi
    
    # Check if the flow shows: create session, extract ID, use ID
    if grep -A5 -B5 "POST.*session" "$readme_file" | grep -q "jq.*-r.*id\|\$SID\|session.*id"; then
        has_correct_flow=true
    fi
    
    if [[ "$has_session_creation" == "false" ]]; then
        issues+=("Missing session creation API example")
    fi
    
    if [[ "$has_message_sending" == "false" ]]; then
        issues+=("Missing message sending with session ID example")
    fi
    
    if [[ "$has_correct_flow" == "false" ]]; then
        issues+=("Missing clear flow showing ID extraction and usage")
    fi
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        log_success "API pattern examples are technically accurate"
        return $EXIT_SUCCESS
    else
        log_failure "API pattern accuracy issues:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return $EXIT_FAILURE
    fi
}

# Main test runner
main() {
    echo "========================================"
    echo "Running: $TEST_NAME"
    echo "========================================"
    
    local failed_tests=0
    local total_tests=4
    
    # Run all tests
    test_readme_session_precision || ((failed_tests++))
    echo
    
    test_session_terminology || ((failed_tests++))
    echo
    
    test_session_manager_precision || ((failed_tests++))
    echo
    
    test_api_pattern_accuracy || ((failed_tests++))
    echo
    
    # Summary
    echo "========================================"
    local passed_tests=$((total_tests - failed_tests))
    
    if [[ $failed_tests -eq 0 ]]; then
        log_success "All tests passed ($passed_tests/$total_tests)"
        echo "Session explanations are technically precise!"
        return $EXIT_SUCCESS
    else
        log_failure "$failed_tests/$total_tests tests failed"
        echo "Session explanations need technical precision improvements."
        echo ""
        echo "Required improvements:"
        echo "1. Server manages session state, client holds only ID"
        echo "2. Clear API flow: POST /session → ID → POST /session/:id/message"
        echo "3. Avoid: 'client holds session info', 'client manages sessions'"
        echo "4. Use: 'server-side state', 'client references via ID'"
        return $EXIT_FAILURE
    fi
}

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi