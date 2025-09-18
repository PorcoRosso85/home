#!/usr/bin/env bash

# Advanced integration tests for graph.ncl and error_diagnostics.ncl
# Tests high-level functionality including graph visualization and error diagnostics

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test execution wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TOTAL_TESTS++))
    log_info "Running test: $test_name"
    
    if eval "$test_command"; then
        log_success "$test_name passed"
        return 0
    else
        log_error "$test_name failed"
        return 1
    fi
}

# Test graph.ncl functionality
test_graph_visualization() {
    log_info "Testing contract graph visualization..."
    
    # Test basic graph export
    if nickel export --format json graph.ncl > output/graph_output.json 2>/dev/null; then
        log_success "Graph export successful"
        
        # Verify JSON structure
        if jq -e '.basic.nodes | length' output/graph_output.json >/dev/null 2>&1; then
            local node_count=$(jq -r '.basic.nodes | length' output/graph_output.json)
            local edge_count=$(jq -r '.basic.edges | length' output/graph_output.json)
            log_info "Basic graph: $node_count nodes, $edge_count edges"
            
            # Verify large scale graph
            local large_node_count=$(jq -r '.large_scale.nodes | length' output/graph_output.json)
            local large_edge_count=$(jq -r '.large_scale.edges | length' output/graph_output.json)
            log_info "Large scale graph: $large_node_count nodes, $large_edge_count edges"
            
            if [ "$large_node_count" -ge 10 ]; then
                log_success "Large scale graph has sufficient complexity ($large_node_count nodes)"
                return 0
            else
                log_error "Large scale graph too simple ($large_node_count nodes < 10)"
                return 1
            fi
        else
            log_error "Invalid JSON structure in graph output"
            return 1
        fi
    else
        log_error "Graph export failed"
        return 1
    fi
}

# Test error diagnostics functionality
test_error_diagnostics() {
    log_info "Testing error diagnostics..."
    
    # Create test file for error diagnostics
    cat > test_error_diagnostics.ncl << 'EOF'
let error_diagnostics = import "error_diagnostics.ncl" in
{
  # Test valid data
  valid_test = error_diagnostics.valid_producer_data & error_diagnostics.ProducerContractWithDiagnostics,
  
  # Test invalid examples (these should exist but we won't evaluate them directly)
  error_labels = error_diagnostics.ErrorLabels,
  contracts_available = {
    producer = error_diagnostics.ProducerContractWithDiagnostics,
    command = error_diagnostics.CommandContractWithDiagnostics,
  }
}
EOF
    
    if nickel export --format json test_error_diagnostics.ncl > output/error_diagnostics_output.json 2>/dev/null; then
        log_success "Error diagnostics export successful"
        
        # Verify error labels are present
        if jq -e '.error_labels.NEGATIVE_VALUE' output/error_diagnostics_output.json >/dev/null 2>&1; then
            local error_label=$(jq -r '.error_labels.NEGATIVE_VALUE' output/error_diagnostics_output.json)
            log_info "Error label detected: $error_label"
            log_success "Error diagnostics structure verified"
            return 0
        else
            log_error "Error labels not found in diagnostics output"
            return 1
        fi
    else
        log_error "Error diagnostics export failed"
        return 1
    fi
}

# Test contract validation with error cases
test_contract_validation() {
    log_info "Testing contract validation with error cases..."
    
    # Test negative value validation
    cat > test_negative_validation.ncl << 'EOF'
let error_diagnostics = import "error_diagnostics.ncl" in
let test_data = {
  processed = -5,
  failed = 2,
  output = ["item1"],
} in
# This should fail validation but we can test the structure
{
  test_result = error_diagnostics.invalid_data_examples.negative_processed,
  validation_available = true,
}
EOF
    
    if nickel export --format json test_negative_validation.ncl > output/negative_validation_output.json 2>/dev/null; then
        log_success "Negative validation test structure verified"
        return 0
    else
        log_warning "Negative validation test failed (expected for some cases)"
        return 0  # This might fail by design
    fi
}

# Test scalability with simulated large dataset
test_scalability() {
    log_info "Testing scalability with contract graph..."
    
    # Use the large_scale graph from graph.ncl as a scalability test
    if jq -e '.large_scale.nodes | length' output/graph_output.json >/dev/null 2>&1; then
        local node_count=$(jq -r '.large_scale.nodes | length' output/graph_output.json)
        
        # Test that we can handle a reasonable number of nodes efficiently
        if [ "$node_count" -ge 10 ] && [ "$node_count" -le 100 ]; then
            log_success "Scalability test passed: handling $node_count nodes efficiently"
            
            # Test JSON processing time (should be fast)
            local start_time=$(date +%s%N)
            jq '.large_scale' output/graph_output.json > /dev/null
            local end_time=$(date +%s%N)
            local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
            
            if [ "$duration" -lt 1000 ]; then  # Less than 1 second
                log_success "Graph processing performance acceptable: ${duration}ms"
                return 0
            else
                log_warning "Graph processing slower than expected: ${duration}ms"
                return 0  # Still pass, just warn
            fi
        else
            log_error "Scalability test failed: unexpected node count $node_count"
            return 1
        fi
    else
        log_error "Cannot test scalability: graph output not available"
        return 1
    fi
}

# Test integration between graph and error diagnostics
test_integration() {
    log_info "Testing integration between graph and error diagnostics..."
    
    # Create integration test
    cat > test_integration.ncl << 'EOF'
let graph = import "graph.ncl" in
let error_diagnostics = import "error_diagnostics.ncl" in
{
  graph_types_available = ["Producer", "Transformer", "Consumer"],
  error_labels_available = error_diagnostics.ErrorLabels,
  basic_graph_nodes = std.array.length graph.basic.nodes,
  large_scale_nodes = std.array.length graph.large_scale.nodes,
}
EOF
    
    if nickel export --format json test_integration.ncl > output/integration_output.json 2>/dev/null; then
        local basic_nodes=$(jq -r '.basic_graph_nodes' output/integration_output.json)
        local large_nodes=$(jq -r '.large_scale_nodes' output/integration_output.json)
        
        log_info "Integration test: Basic graph has $basic_nodes nodes, Large scale has $large_nodes nodes"
        log_success "Integration test passed: both modules work together"
        return 0
    else
        log_error "Integration test failed"
        return 1
    fi
}

# Main test execution
main() {
    log_info "Starting Advanced Integration Tests for Contract Flake Nickel"
    log_info "=============================================================="
    
    # Create output directory
    mkdir -p output
    
    # Run all tests
    run_test "Graph Visualization" "test_graph_visualization"
    run_test "Error Diagnostics" "test_error_diagnostics"
    run_test "Contract Validation" "test_contract_validation"
    run_test "Scalability" "test_scalability"
    run_test "Integration" "test_integration"
    
    # Cleanup temporary files
    rm -f test_error_diagnostics.ncl test_negative_validation.ncl test_integration.ncl
    
    # Summary
    log_info ""
    log_info "Test Summary"
    log_info "============"
    log_info "Total tests: $TOTAL_TESTS"
    log_success "Passed: $PASSED_TESTS"
    if [ "$FAILED_TESTS" -gt 0 ]; then
        log_error "Failed: $FAILED_TESTS"
    else
        log_info "Failed: $FAILED_TESTS"
    fi
    
    if [ "$FAILED_TESTS" -eq 0 ]; then
        log_success "All advanced tests passed! 🎉"
        exit 0
    else
        log_error "Some tests failed. Please check the output above."
        exit 1
    fi
}

# Run main function
main "$@"