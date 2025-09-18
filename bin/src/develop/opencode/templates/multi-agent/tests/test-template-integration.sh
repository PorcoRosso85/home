#!/usr/bin/env bash
set -euo pipefail

# Test suite for template integration
# Add parent directory to PATH so tests can find scripts
export PATH="$(dirname "$PWD"):$PATH"

# Test configuration
readonly TEST_DIR="/tmp/opencode-template-test-$$"
readonly SESSION_BASE="/tmp/opencode-sessions"

# Helper functions
setup_test() {
    mkdir -p "$TEST_DIR"
    mkdir -p "$SESSION_BASE"
    cd "$TEST_DIR"
    export OPENCODE_SESSION_DIR="$SESSION_BASE"
}

cleanup_test() {
    cd /
    rm -rf "$TEST_DIR" 2>/dev/null || true
    rm -rf "$SESSION_BASE" 2>/dev/null || true
}

fail_test() {
    local test_name="$1"
    local message="$2"
    echo "❌ FAIL: $test_name - $message"
}

pass_test() {
    local test_name="$1"
    echo "✅ PASS: $test_name"
}

# Test: Multi-agent workflow template creation
test_workflow_template() {
    setup_test
    local test_name="test_workflow_template"
    
    # This should fail because multi-agent-workflow doesn't exist yet (RED)
    if command -v multi-agent-workflow >/dev/null 2>&1; then
        # Test workflow template generation
        local result
        if result=$(multi-agent-workflow --action="create_template" --name="research-and-code" --output="$TEST_DIR" 2>&1); then
            # Check if template files were created
            if [[ -f "$TEST_DIR/research-and-code.json" ]] && [[ -f "$TEST_DIR/agents.json" ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Template files not created. Got: $result"
            fi
        else
            fail_test "$test_name" "Template creation should succeed"
        fi
    else
        fail_test "$test_name" "multi-agent-workflow command not found"
    fi
    
    cleanup_test
}

# Test: OpenCode client integration
test_opencode_client_integration() {
    setup_test
    local test_name="test_opencode_client_integration"
    
    # This should fail because opencode-multi-client doesn't exist yet (RED)
    if command -v opencode-multi-client >/dev/null 2>&1; then
        # Test client with multi-agent configuration
        local config_file="$TEST_DIR/multi-client-config.json"
        cat > "$config_file" <<EOF
{
  "servers": [
    {"url": "http://127.0.0.1:4096", "role": "primary"},
    {"url": "http://127.0.0.1:4097", "role": "backup"}
  ],
  "agents": {
    "researcher": {"server": "primary", "capabilities": ["search"]},
    "coder": {"server": "backup", "capabilities": ["coding"]}
  }
}
EOF
        
        local result
        if result=$(opencode-multi-client --config="$config_file" --action="validate" 2>&1); then
            if [[ "$result" == *"VALID"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Client integration should validate. Got: $result"
            fi
        else
            fail_test "$test_name" "Client integration validation should succeed"
        fi
    else
        fail_test "$test_name" "opencode-multi-client command not found"
    fi
    
    cleanup_test
}

# Test: End-to-end workflow execution
test_end_to_end_workflow() {
    setup_test
    local test_name="test_end_to_end_workflow"
    
    # This should fail because the integrated system doesn't exist yet (RED)
    if command -v opencode-multi-agent >/dev/null 2>&1; then
        # Create comprehensive workflow
        local workflow_config="$TEST_DIR/e2e-workflow.json"
        cat > "$workflow_config" <<EOF
{
  "workflow": {
    "id": "full-development-cycle",
    "agents": [
      {"id": "researcher", "role": "research", "server": "http://127.0.0.1:4096"},
      {"id": "developer", "role": "coding", "server": "http://127.0.0.1:4097"}
    ],
    "steps": [
      {
        "id": "research_phase",
        "agent": "researcher",
        "task": "Research best practices for API design",
        "timeout": 60
      },
      {
        "id": "development_phase", 
        "agent": "developer",
        "task": "Implement API based on research",
        "depends_on": ["research_phase"],
        "timeout": 120
      }
    ]
  }
}
EOF
        
        local result
        if result=$(opencode-multi-agent --workflow="$workflow_config" --action="execute" --timeout=180 2>&1); then
            if [[ "$result" == *"COMPLETED"* ]] || [[ "$result" == *"PROGRESS"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "E2E workflow should execute. Got: $result"
            fi
        else
            fail_test "$test_name" "E2E workflow execution should start"
        fi
    else
        fail_test "$test_name" "opencode-multi-agent command not found"
    fi
    
    cleanup_test
}

# Test: Template validation and schema checking
test_template_validation() {
    setup_test
    local test_name="test_template_validation"
    
    # This should fail because template-validator doesn't exist yet (RED)
    if command -v template-validator >/dev/null 2>&1; then
        # Create test template
        local template_file="$TEST_DIR/test-template.json"
        cat > "$template_file" <<EOF
{
  "template": {
    "name": "simple-research",
    "version": "1.0",
    "agents": [
      {"role": "researcher", "capabilities": ["search", "analysis"]}
    ],
    "workflow": {
      "steps": [
        {"agent": "researcher", "task": "search documentation"}
      ]
    }
  }
}
EOF
        
        local result
        if result=$(template-validator --template="$template_file" --action="validate" 2>&1); then
            if [[ "$result" == *"VALID"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Template validation should pass. Got: $result"
            fi
        else
            fail_test "$test_name" "Template validation should succeed"
        fi
    else
        fail_test "$test_name" "template-validator command not found"
    fi
    
    cleanup_test
}

# Test: System health check and integration status
test_system_health_check() {
    setup_test
    local test_name="test_system_health_check"
    
    # This should fail because system-health-check doesn't exist yet (RED)
    if command -v system-health-check >/dev/null 2>&1; then
        # Test comprehensive system check
        local result
        if result=$(system-health-check full_check 2>&1); then
            # Should check all components: session-manager, multi-server-manager, orchestrator
            if [[ "$result" == *"session-manager"* ]] && [[ "$result" == *"multi-server-manager"* ]] && [[ "$result" == *"orchestrator"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Health check should validate all components. Got: $result"
            fi
        else
            fail_test "$test_name" "System health check should succeed"
        fi
    else
        fail_test "$test_name" "system-health-check command not found"
    fi
    
    cleanup_test
}

# Test: Documentation and example generation
test_documentation_generation() {
    setup_test
    local test_name="test_documentation_generation"
    
    # This should fail because doc-generator doesn't exist yet (RED)
    if command -v doc-generator >/dev/null 2>&1; then
        # Test documentation generation
        local result
        if result=$(doc-generator --action="generate_examples" --output="$TEST_DIR/docs" 2>&1); then
            # Check if documentation was created
            if [[ -d "$TEST_DIR/docs" ]] && [[ -f "$TEST_DIR/docs/README.md" ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Documentation files should be created. Got: $result"
            fi
        else
            fail_test "$test_name" "Documentation generation should succeed"
        fi
    else
        fail_test "$test_name" "doc-generator command not found"
    fi
    
    cleanup_test
}

# Test: Performance and scalability validation
test_performance_validation() {
    setup_test
    local test_name="test_performance_validation"
    
    # This should fail because performance-tester doesn't exist yet (RED)
    if command -v performance-tester >/dev/null 2>&1; then
        # Test system performance under load
        local result
        if result=$(performance-tester --agents=3 --tasks=10 --duration=30 --action="load_test" 2>&1); then
            if [[ "$result" == *"COMPLETED"* ]] && [[ "$result" == *"success_rate"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Performance test should complete with metrics. Got: $result"
            fi
        else
            fail_test "$test_name" "Performance test should run successfully"
        fi
    else
        fail_test "$test_name" "performance-tester command not found"
    fi
    
    cleanup_test
}

echo "🔴 Running RED tests for template integration..."
echo "These tests should FAIL because integration components are not implemented yet"
echo

# Run all tests
test_workflow_template
test_opencode_client_integration
test_end_to_end_workflow
test_template_validation
test_system_health_check
test_documentation_generation
test_performance_validation

echo
echo "RED phase complete. All tests should have failed."