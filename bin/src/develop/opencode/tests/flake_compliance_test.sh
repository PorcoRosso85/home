#!/usr/bin/env bash
set -euo pipefail

# flake.nix compliance test - RED phase
# These tests SHOULD FAIL until flake.nix becomes compliant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Test that flake.nix does NOT contain shell script implementations
test_no_shell_functions_in_flake() {
    echo "Testing: flake.nix should not contain shell script function implementations"
    
    # Check for session function definitions (prohibited per conventions/prohibited_items.md)
    if grep -q "session_get_base_dir()" "$REPO_ROOT/flake.nix"; then
        echo "❌ FAIL: Found shell function session_get_base_dir() in flake.nix (prohibited)"
        return 1
    fi
    
    if grep -q "session_normalize_url()" "$REPO_ROOT/flake.nix"; then
        echo "❌ FAIL: Found shell function session_normalize_url() in flake.nix (prohibited)"
        return 1
    fi
    
    if grep -q "session_derive_host_port()" "$REPO_ROOT/flake.nix"; then
        echo "❌ FAIL: Found shell function session_derive_host_port() in flake.nix (prohibited)"
        return 1
    fi
    
    echo "✅ PASS: No prohibited shell functions found in flake.nix"
    return 0
}

# Test that lib/session-helper.sh exists and contains required functions
test_session_helper_exists() {
    echo "Testing: lib/session-helper.sh should exist with oc_session_* functions"
    
    if [[ ! -f "$REPO_ROOT/lib/session-helper.sh" ]]; then
        echo "❌ FAIL: lib/session-helper.sh does not exist"
        return 1
    fi
    
    # Check for proper function naming (oc_session_* prefix)
    if ! grep -q "oc_session_get_base_dir()" "$REPO_ROOT/lib/session-helper.sh"; then
        echo "❌ FAIL: oc_session_get_base_dir() not found in lib/session-helper.sh"
        return 1
    fi
    
    if ! grep -q "oc_session_get_or_create()" "$REPO_ROOT/lib/session-helper.sh"; then
        echo "❌ FAIL: oc_session_get_or_create() not found in lib/session-helper.sh"
        return 1
    fi
    
    echo "✅ PASS: lib/session-helper.sh exists with required oc_session_* functions"
    return 0
}

# Test that flake.nix sources lib/session-helper.sh instead of inline implementation
test_flake_sources_session_helper() {
    echo "Testing: flake.nix should source lib/session-helper.sh"
    
    if ! grep -q "source.*lib/session-helper.sh" "$REPO_ROOT/flake.nix"; then
        echo "❌ FAIL: flake.nix does not source lib/session-helper.sh"
        return 1
    fi
    
    echo "✅ PASS: flake.nix sources lib/session-helper.sh"
    return 0
}

# Test unified package naming  
test_unified_package_naming() {
    echo "Testing: Packages should have clear, purpose-driven names"
    
    # opencode-client should exist (renamed from client-hello)
    if ! grep -q '"opencode-client"' "$REPO_ROOT/flake.nix"; then
        echo "❌ FAIL: opencode-client package not found (should be renamed from client-hello)"
        return 1
    fi
    
    # Backward compatibility: client-hello should still work as alias in apps
    if ! grep -q "client-hello" "$REPO_ROOT/flake.nix"; then
        echo "❌ FAIL: client-hello alias not found (backward compatibility)"
        return 1
    fi
    
    echo "✅ PASS: Package naming follows conventions with backward compatibility"
    return 0
}

# Test that examples directory exists for deprecated flakes
test_examples_directory() {
    echo "Testing: examples/ directory should exist for flake-core.nix and flake-enhanced.nix"
    
    if [[ ! -d "$REPO_ROOT/examples" ]]; then
        echo "❌ FAIL: examples/ directory does not exist"
        return 1
    fi
    
    if [[ ! -f "$REPO_ROOT/examples/flake-core.nix" ]] && [[ -f "$REPO_ROOT/flake-core.nix" ]]; then
        echo "❌ FAIL: flake-core.nix should be moved to examples/"
        return 1
    fi
    
    if [[ ! -f "$REPO_ROOT/examples/flake-enhanced.nix" ]] && [[ -f "$REPO_ROOT/flake-enhanced.nix" ]]; then
        echo "❌ FAIL: flake-enhanced.nix should be moved to examples/"
        return 1
    fi
    
    echo "✅ PASS: Alternative flakes properly organized in examples/"
    return 0
}

# Run all compliance tests
main() {
    echo "🔴 RED Phase: flake.nix Compliance Tests (Expected to FAIL initially)"
    echo "=============================================="
    
    local failed=0
    
    test_no_shell_functions_in_flake || failed=$((failed + 1))
    test_session_helper_exists || failed=$((failed + 1))
    test_flake_sources_session_helper || failed=$((failed + 1))
    test_unified_package_naming || failed=$((failed + 1))
    test_examples_directory || failed=$((failed + 1))
    
    echo ""
    if [[ $failed -eq 0 ]]; then
        echo "🟢 All compliance tests PASSED - Ready for GREEN phase"
        exit 0
    else
        echo "🔴 $failed compliance test(s) FAILED - This is EXPECTED in RED phase"
        echo "Implementation needed to make tests pass"
        exit 1
    fi
}

main "$@"