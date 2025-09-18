#!/usr/bin/env bash
set -euo pipefail

# System Health Check for OpenCode Multi-Agent System
# Validates all components and their integration

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_COMPONENT_MISSING=1
readonly EXIT_COMPONENT_FAILED=2

# Color output for better readability
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Component status tracking
declare -A component_status
declare -A component_details

# Print colored output
print_status() {
    local status="$1"
    local component="$2"
    local details="${3:-}"
    
    case "$status" in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $component"
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $component"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC}: $component"
            ;;
    esac
    
    if [[ -n "$details" ]]; then
        echo "   $details"
    fi
}

# Check if command exists and is executable
check_command() {
    local cmd="$1"
    local description="$2"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        component_status["$cmd"]="PASS"
        component_details["$cmd"]="Command available at $(which "$cmd")"
        print_status "PASS" "$description" "$(which "$cmd")"
        return 0
    else
        component_status["$cmd"]="FAIL"
        component_details["$cmd"]="Command not found"
        print_status "FAIL" "$description" "Command not found in PATH"
        return 1
    fi
}

# Test component functionality
test_component() {
    local cmd="$1"
    local test_args="$2"
    local description="$3"
    local expected_pattern="$4"
    
    if [[ "${component_status[$cmd]:-}" != "PASS" ]]; then
        print_status "FAIL" "$description" "Component not available"
        return 1
    fi
    
    local result
    local exit_code
    
    if result=$(eval "$cmd $test_args" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi
    
    if [[ $exit_code -eq 0 ]] && [[ "$result" =~ $expected_pattern ]]; then
        component_status["${cmd}_test"]="PASS"
        component_details["${cmd}_test"]="Test passed: $result"
        print_status "PASS" "$description test" "Output: $result"
        return 0
    else
        component_status["${cmd}_test"]="FAIL"
        component_details["${cmd}_test"]="Test failed (exit: $exit_code): $result"
        print_status "FAIL" "$description test" "Exit code: $exit_code, Output: $result"
        return 1
    fi
}

# Check core system dependencies
check_system_dependencies() {
    echo "=== System Dependencies ==="
    
    local deps=("jq:JSON processor" "curl:HTTP client" "bash:Shell interpreter")
    local failed=0
    
    for dep in "${deps[@]}"; do
        local cmd="${dep%:*}"
        local desc="${dep#*:}"
        
        if ! check_command "$cmd" "$desc"; then
            ((failed++))
        fi
    done
    
    echo
    return $failed
}

# Check multi-agent system components
check_multi_agent_components() {
    echo "=== Multi-Agent System Components ==="
    
    local components=(
        "session-manager:Session Management"
        "unified-error-handler:Error Handling"
        "multi-server-manager:Server Management"
        "orchestrator:Agent Orchestration"
    )
    
    local failed=0
    
    for comp in "${components[@]}"; do
        local cmd="${comp%:*}"
        local desc="${comp#*:}"
        
        if ! check_command "$cmd" "$desc"; then
            ((failed++))
        fi
    done
    
    echo
    return $failed
}

# Test component functionality
test_component_functionality() {
    echo "=== Component Functionality Tests ==="
    
    local failed=0
    
    # Test session manager
    if ! test_component "session-manager" "--strategy=auto --host-port=127.0.0.1:4096" "Session Manager" "/.*sessions.*"; then
        ((failed++))
    fi
    
    # Test unified error handler
    if ! test_component "unified-error-handler" "--url=http://httpbin.org/get --method=GET --timeout=10" "Unified Error Handler" "httpbin"; then
        ((failed++))
    fi
    
    # Test multi-server manager
    if ! test_component "multi-server-manager" "--server-pool=http://127.0.0.1:4096,http://127.0.0.1:4097 --health-check=false --action=get_server_count" "Multi-Server Manager" "2"; then
        ((failed++))
    fi
    
    # Test orchestrator
    local temp_config="/tmp/health-check-config.json"
    cat > "$temp_config" <<EOF
{
  "agents": [
    {"id": "test-agent", "role": "test", "capabilities": ["test"]}
  ]
}
EOF
    
    if ! test_component "orchestrator" "--config=$temp_config --action=validate_config" "Orchestrator" "VALID"; then
        ((failed++))
    fi
    
    rm -f "$temp_config"
    
    echo
    return $failed
}

# Check integration between components
check_integration() {
    echo "=== Integration Tests ==="
    
    local failed=0
    
    # Test session manager with multi-server manager integration
    echo -n "Testing session-manager + multi-server-manager integration... "
    local session_result
    if session_result=$(session-manager --strategy=new --host-port=127.0.0.1:4096 2>/dev/null); then
        if [[ -n "$session_result" ]] && [[ -d "$session_result" ]]; then
            print_status "PASS" "Session-MultiServer Integration" "Session created: $session_result"
        else
            print_status "FAIL" "Session-MultiServer Integration" "Invalid session path: $session_result"
            ((failed++))
        fi
    else
        print_status "FAIL" "Session-MultiServer Integration" "Session creation failed"
        ((failed++))
    fi
    
    # Test orchestrator with session manager integration
    echo -n "Testing orchestrator + session-manager integration... "
    local agent_result
    if agent_result=$(orchestrator --action=start_agent --agent-id=test-integration-agent --server-pool=http://127.0.0.1:4096 2>/dev/null); then
        if [[ "$agent_result" == *"STARTED"* ]]; then
            print_status "PASS" "Orchestrator-Session Integration" "$agent_result"
            
            # Clean up
            orchestrator --action=stop_agent --agent-id=test-integration-agent >/dev/null 2>&1 || true
        else
            print_status "FAIL" "Orchestrator-Session Integration" "$agent_result"
            ((failed++))
        fi
    else
        print_status "FAIL" "Orchestrator-Session Integration" "Agent start failed"
        ((failed++))
    fi
    
    echo
    return $failed
}

# Check system resources and performance
check_system_resources() {
    echo "=== System Resources ==="
    
    # Check available memory
    if command -v free >/dev/null 2>&1; then
        local mem_info
        mem_info=$(free -h | awk '/^Mem:/ {print "Total: " $2 ", Available: " $7}')
        print_status "PASS" "Memory" "$mem_info"
    else
        print_status "WARN" "Memory" "free command not available"
    fi
    
    # Check disk space in temp directories
    local temp_usage
    temp_usage=$(df -h /tmp 2>/dev/null | awk 'NR==2 {print "Used: " $3 "/" $2 " (" $5 ")"}' || echo "unknown")
    print_status "PASS" "Disk Space (/tmp)" "$temp_usage"
    
    # Check orchestrator resource usage
    local resource_usage
    if resource_usage=$(orchestrator --action=get_resource_usage 2>/dev/null); then
        print_status "PASS" "Orchestrator Resources" "$resource_usage"
    else
        print_status "WARN" "Orchestrator Resources" "Could not get resource usage"
    fi
    
    echo
    return 0
}

# Generate summary report
generate_summary() {
    echo "=== Health Check Summary ==="
    
    local total_checks=0
    local passed_checks=0
    local failed_checks=0
    local warned_checks=0
    
    for status in "${component_status[@]}"; do
        ((total_checks++))
        case "$status" in
            "PASS") ((passed_checks++)) ;;
            "FAIL") ((failed_checks++)) ;;
            "WARN") ((warned_checks++)) ;;
        esac
    done
    
    echo "Total checks: $total_checks"
    echo -e "Passed: ${GREEN}$passed_checks${NC}"
    if [[ $failed_checks -gt 0 ]]; then
        echo -e "Failed: ${RED}$failed_checks${NC}"
    fi
    if [[ $warned_checks -gt 0 ]]; then
        echo -e "Warnings: ${YELLOW}$warned_checks${NC}"
    fi
    
    echo
    
    if [[ $failed_checks -eq 0 ]]; then
        echo -e "${GREEN}✅ System Health: GOOD${NC}"
        echo "All critical components are operational."
        return 0
    elif [[ $failed_checks -lt 3 ]]; then
        echo -e "${YELLOW}⚠️  System Health: DEGRADED${NC}"
        echo "Some components have issues but system may still function."
        return 1
    else
        echo -e "${RED}❌ System Health: CRITICAL${NC}"
        echo "Multiple critical failures detected."
        return 2
    fi
}

# Main execution
main() {
    local action="${1:-full_check}"
    
    case "$action" in
        "full_check")
            echo "OpenCode Multi-Agent System Health Check"
            echo "========================================"
            echo
            
            local total_failures=0
            
            check_system_dependencies || ((total_failures += $?))
            check_multi_agent_components || ((total_failures += $?))
            test_component_functionality || ((total_failures += $?))
            check_integration || ((total_failures += $?))
            check_system_resources || ((total_failures += $?))
            
            generate_summary
            ;;
        "quick_check")
            echo "Quick Component Check"
            echo "===================="
            check_multi_agent_components
            ;;
        *)
            echo "Usage: $0 [full_check|quick_check]"
            return $EXIT_COMPONENT_MISSING
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi