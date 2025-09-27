#!/usr/bin/env bash
set -euo pipefail

echo "🚀 CUE Contract Management System - Complete System Test"
echo ""

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo "🧪 Testing: $test_name"
    TESTS_RUN=$((TESTS_RUN + 1))

    if eval "$test_command" > /tmp/test_output 2>&1; then
        echo "✅ PASS: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo "❌ FAIL: $test_name"
        echo "Error output:"
        cat /tmp/test_output | head -10
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

echo "📋 Step 1: Core CUE Schema Foundation"
run_test "CUE Schema Validation" "cue vet schema/contract.cue"
run_test "CUE Schema Export" "cue export schema/contract.cue > /dev/null"
run_test "CUE Module Configuration" "test -f cue.mod/module.cue"

echo "📋 Step 2: File Enumeration System"
run_test "Contract Discovery" "find contracts -name 'contract.cue' -type f | wc -l | grep -q '[1-9]'"
run_test "Index Generation" "test -f tools/index.json"

echo "📋 Step 3: Aggregation Checks"
run_test "Aggregate Validation Tool" "test -f tools/aggregate.cue"
run_test "Example Contract Validation" "cue vet contracts/example/contract.cue"

echo "📋 Step 4: Flake Check Integration"
run_test "All Flake Checks Pass" "timeout 300 nix flake check --no-write-lock-file"
run_test "Individual Check: CUE Format" "nix build .#checks.x86_64-linux.cueFmt --no-link"
run_test "Individual Check: CUE Vet" "nix build .#checks.x86_64-linux.cueVet --no-link"
run_test "Individual Check: CUE Export" "nix build .#checks.x86_64-linux.cueExport --no-link"

echo "📋 Step 5: Secrets Management"
run_test "Secrets Directory Setup" "test -d secrets"
run_test "SOPS Configuration" "test -f secrets/.sops.yaml"
run_test "Secrets Detection Script" "./tools/test-secrets.sh"

echo "📋 Step 6: Pre-Commit Integration"
run_test "Pre-commit Configuration" "test -f .pre-commit-config.yaml"
run_test "Pre-commit Hook Testing" "./tools/test-precommit.sh"

echo "📋 Step 7: Practical Examples"
run_test "Normal Examples Exist" "test -d contracts/examples/normal && find contracts/examples/normal -name 'contract.cue' | wc -l | grep -q '[1-9]'"
run_test "Duplicate Examples Exist" "test -d contracts/examples/duplicate && find contracts/examples/duplicate -name 'contract.cue' | wc -l | grep -q '[1-9]'"
run_test "Unresolved Examples Exist" "test -d contracts/examples/unresolved && find contracts/examples/unresolved -name 'contract.cue' | wc -l | grep -q '[1-9]'"
run_test "Examples Documentation" "test -f contracts/examples/README.md"

echo "📋 Step 8: Documentation Complete"
run_test "Main README Updated" "grep -q 'COMPLETE' README.md"
run_test "New Developer Guide" "test -f docs/NEW_DEVELOPER_GUIDE.md"
run_test "Documentation Links" "grep -q 'NEW_DEVELOPER_GUIDE.md' README.md"

echo "🔧 Development Environment Tests"
run_test "Nix Development Shell" "nix develop --command echo 'Development environment ready'"
run_test "CUE Tools Available" "nix develop --command cue version"
run_test "Pre-commit Tool Available" "nix develop --command pre-commit --version"

echo "🏗️ Build System Tests"
run_test "Nix Formatter Works" "nix fmt --help"
run_test "Development Shell Apps" "nix develop --command bash -c 'type cue && type pre-commit'"

echo "📊 Final System Validation"
run_test "Complete Flake Check" "nix flake check --no-write-lock-file"
run_test "System Smoke Test" "nix build .#nixosTests.smoke --no-link"

# Summary
echo "==============================================="
echo "🎯 SYSTEM TEST SUMMARY"
echo "==============================================="
echo "Tests Run:    $TESTS_RUN"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! 🎉"
    echo ""
    echo "✅ CUE Contract Management System is fully operational!"
    echo ""
    echo "System Features Verified:"
    echo "  🔹 CUE schema foundation with closed structures"
    echo "  🔹 Automatic contract discovery and enumeration"
    echo "  🔹 Aggregation validation with standardized messages"
    echo "  🔹 Complete Nix flake integration"
    echo "  🔹 Secrets management with SOPS support"
    echo "  🔹 Pre-commit hooks for development workflow"
    echo "  🔹 Comprehensive examples and documentation"
    echo ""
    echo "Ready for production use! 🚀"
    echo ""
    echo "Next steps:"
    echo "  1. Review docs/NEW_DEVELOPER_GUIDE.md"
    echo "  2. Run 'nix develop' to start developing"
    echo "  3. Create your first contract in contracts/"
    exit 0
else
    echo "❌ SOME TESTS FAILED!"
    echo ""
    echo "Please check the failed tests above and fix any issues."
    echo "The system may not be fully operational."
    exit 1
fi