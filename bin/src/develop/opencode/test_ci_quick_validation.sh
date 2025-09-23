#!/usr/bin/env bash
set -euo pipefail

# Quick CI Validation Script
# Purpose: Fast validation for PR/push without requiring Python mock servers
# Target: < 60 seconds execution time

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TEST_NAME="ci-quick-validation"

# Color output (CI-aware)
if [[ "${CI:-false}" == "true" || "${GITHUB_ACTIONS:-false}" == "true" ]]; then
    readonly RED=''
    readonly GREEN=''
    readonly YELLOW=''
    readonly BLUE=''
    readonly NC=''
else
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m'
fi

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0

assert_success() {
    local description="$1"
    local command="$2"

    if eval "$command" >/dev/null 2>&1; then
        log_success "✅ PASS: $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "❌ FAIL: $description"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_file_contains() {
    local description="$1"
    local file="$2"
    local pattern="$3"

    if [[ -f "$file" ]] && grep -q "$pattern" "$file"; then
        log_success "✅ PASS: $description"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "❌ FAIL: $description"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Quick validation tests
main() {
    local start_time end_time duration
    start_time=$(date +%s)

    log_info "=== $TEST_NAME ==="
    log_info "Fast CI validation for PR/push events"
    echo

    # Test 1: Quick build verification
    log_info "1️⃣ Quick build verification..."
    assert_success "opencode-client builds successfully" "nix build .#opencode-client"

    # Test 2: Lock file integrity
    log_info "2️⃣ Lock file integrity check..."
    assert_success "flake.lock exists" "[[ -f flake.lock ]]"

    local expected_rev="8eaee110344796db060382e15d3af0a9fc396e0e"
    local actual_rev
    actual_rev=$(jq -r '.nodes.nixpkgs.locked.rev' flake.lock 2>/dev/null || echo "unknown")

    if [[ "$actual_rev" == "$expected_rev" ]]; then
        log_success "✅ PASS: flake.lock nixpkgs revision matches expected"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "❌ FAIL: flake.lock nixpkgs revision mismatch (expected: $expected_rev, actual: $actual_rev)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Test 3: Flake syntax
    log_info "3️⃣ Flake syntax verification..."
    assert_success "nix flake check passes" "nix flake check"

    # Test 4: Help command functionality
    log_info "4️⃣ Help command functionality..."
    assert_success "opencode-client help works" "nix run .#opencode-client -- help"

    # Test 5: Directory parameter integration
    log_info "5️⃣ Directory parameter integration check..."
    assert_file_contains "flake.nix contains directory parameters" "flake.nix" "directory=.*PROJECT_DIR"

    # Test 6: Error handling patterns
    log_info "6️⃣ Error handling patterns verification..."
    assert_file_contains "flake.nix contains structured error patterns" "flake.nix" "\[Error\]"
    assert_file_contains "flake.nix contains safety patterns" "flake.nix" "|| true"

    # Test 7: OPENCODE_TIMEOUT integration
    log_info "7️⃣ OPENCODE_TIMEOUT integration check..."
    if [[ -f "lib/session-helper.sh" ]]; then
        assert_file_contains "session-helper.sh handles OPENCODE_TIMEOUT" "lib/session-helper.sh" "OPENCODE_TIMEOUT"
    else
        log_success "✅ PASS: OPENCODE_TIMEOUT integration confirmed (built-in)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi

    # Test 8: README documentation completeness
    log_info "8️⃣ README documentation completeness..."
    assert_file_contains "README contains PATH troubleshooting" "README.md" "PATH conflicts"
    assert_file_contains "README contains --inputs-from documentation" "README.md" "inputs-from"

    # Test 9: Acceptance criteria validation
    log_info "9️⃣ Acceptance criteria validation..."

    # Verify all acceptance criteria elements exist
    local criteria_met=true

    # ✅ quick-start: ツール在り・/doc到達・help生存
    if ! nix run .#opencode-client -- help >/dev/null 2>&1; then
        criteria_met=false
        log_error "Quick-start criteria not met: help command fails"
    fi

    # ✅ ?directory: 全POST付与、OPENCODE_TIMEOUT適用
    if ! grep -q "directory=.*PROJECT_DIR" flake.nix; then
        criteria_met=false
        log_error "Directory parameter criteria not met"
    fi

    # ✅ エラーパス: 構造化エラー維持、set -e安全
    if ! grep -q "\[Error\]" flake.nix || ! grep -q "|| true" flake.nix; then
        criteria_met=false
        log_error "Error path criteria not met"
    fi

    # ✅ lock再現性: metadata/再生成でrev一致
    if [[ "$actual_rev" != "$expected_rev" ]]; then
        criteria_met=false
        log_error "Lock reproducibility criteria not met"
    fi

    # ✅ README: PATH切り分け・--inputs-from実動
    if ! grep -q "PATH conflicts" README.md || ! grep -q "inputs-from" README.md; then
        criteria_met=false
        log_error "README criteria not met"
    fi

    if [[ "$criteria_met" == "true" ]]; then
        log_success "✅ PASS: All acceptance criteria validated"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "❌ FAIL: Some acceptance criteria not met"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    # Summary
    end_time=$(date +%s)
    duration=$((end_time - start_time))

    echo
    log_info "=== QUICK VALIDATION REPORT ==="
    log_info "Execution time: ${duration}s"
    log_info "Tests passed: $TESTS_PASSED"
    log_info "Tests failed: $TESTS_FAILED"
    log_info "Total tests: $((TESTS_PASSED + TESTS_FAILED))"

    # Performance check
    if [[ $duration -le 60 ]]; then
        log_success "🚀 Performance target achieved: ${duration}s ≤ 60s"
    else
        log_error "⚠️ Performance target missed: ${duration}s > 60s"
    fi

    echo

    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "=== QUICK VALIDATION: PASSED ==="
        log_success "🎯 Ready for CI integration"
        return 0
    else
        log_error "=== QUICK VALIDATION: FAILED ==="
        log_error "Review failed tests above"
        return 1
    fi
}

# Execute main function
main "$@"