#!/usr/bin/env bash
set -euo pipefail

# Complete Integration Test
# Run all individual step tests to verify the complete implementation

echo "🧪 Complete Integration Test - All Baby Steps"
echo "============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# Test 1: Subcommand infrastructure
echo
echo "1. Testing subcommand infrastructure..."
if bash "$REPO_ROOT/test_subcommand_infrastructure.sh"; then
    echo "✅ Step 1: Subcommand infrastructure - PASSED"
else
    echo "❌ Step 1: Subcommand infrastructure - FAILED"
    exit 1
fi

# Test 2: History library
echo
echo "2. Testing history library..."
if bash "$REPO_ROOT/test_history_helper.sh"; then
    echo "✅ Step 2: History library - PASSED"
else
    echo "❌ Step 2: History library - FAILED"
    exit 1
fi

# Test 3: History subcommand
echo
echo "3. Testing history subcommand..."
if bash "$REPO_ROOT/test_history_subcommand.sh"; then
    echo "✅ Step 3: History subcommand - PASSED"
else
    echo "❌ Step 3: History subcommand - FAILED"
    exit 1
fi

# Test 4: Sessions subcommand
echo
echo "4. Testing sessions subcommand..."
if bash "$REPO_ROOT/test_sessions_subcommand.sh"; then
    echo "✅ Step 4: Sessions subcommand - PASSED"
else
    echo "❌ Step 4: Sessions subcommand - FAILED"
    exit 1
fi

# Test 5: Documentation and integration
echo
echo "5. Testing documentation and integration..."
if bash "$REPO_ROOT/test_documentation_integration.sh"; then
    echo "✅ Step 5: Documentation integration - PASSED"
else
    echo "❌ Step 5: Documentation integration - FAILED"
    exit 1
fi

# Test 6: ShellCheck quality gate
echo
echo "6. Testing ShellCheck quality gate..."
if nix develop --command bash -c "./test_shellcheck_quality.sh" 2>&1 | grep -q "Quality gate: PASSED"; then
    echo "✅ Step 6: ShellCheck quality gate - PASSED"
else
    echo "❌ Step 6: ShellCheck quality gate - FAILED"
    exit 1
fi

# Test 7: Final compliance check
echo
echo "7. Final flake compliance verification..."
if bash "$REPO_ROOT/tests/flake_compliance_test.sh" 2>&1 | grep -q "All compliance tests PASSED"; then
    echo "✅ Final: Flake compliance - PASSED"
else
    echo "❌ Final: Flake compliance - FAILED"
    exit 1
fi

echo
echo "🎉 ALL BABY STEPS COMPLETED SUCCESSFULLY!"
echo "============================================="
echo "✅ Step 1: Subcommand infrastructure with help"
echo "✅ Step 2: History library (lib/history-helper.sh)"
echo "✅ Step 3: History subcommand with auto-session selection"
echo "✅ Step 4: Sessions subcommand with listing functionality"
echo "✅ Step 5: Documentation and test integration"
echo "✅ Step 6: ShellCheck quality gate (lib/*.sh validation)"
echo "✅ Final: Architecture compliance maintained"
echo
echo "🎯 OpenCode client now supports:"
echo "   - send [MESSAGE]     (default behavior)"
echo "   - history [OPTIONS]  (view conversation history)"
echo "   - sessions [OPTIONS] (list available sessions)"
echo "   - help               (usage information)"
echo
echo "📚 Documentation updated in README.md"
echo "🏗️  Architecture: unified CLI + library separation"
echo "🔄 Backward compatibility: 100% maintained"