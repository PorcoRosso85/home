#!/usr/bin/env bash
set -euo pipefail

# ShellCheck Quality Gate Test
# Validates all shell scripts in lib/ directory for ShellCheck compliance
# This supplements the main flake compliance testing with focused shell quality checking

echo "🔍 ShellCheck Quality Gate Test"
echo "================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
LIB_DIR="$REPO_ROOT/lib"

# Check if lib directory exists
if [ ! -d "$LIB_DIR" ]; then
    echo "❌ FAIL: lib/ directory not found at $LIB_DIR"
    exit 1
fi

# Find all .sh files in lib directory
SHELL_FILES=$(find "$LIB_DIR" -name "*.sh" -type f)

if [ -z "$SHELL_FILES" ]; then
    echo "⚠️  WARNING: No .sh files found in lib/ directory"
    echo "✅ Quality gate passed (no files to check)"
    exit 0
fi

echo "📂 Checking shell scripts in lib/ directory:"
echo "$SHELL_FILES" | while IFS= read -r file; do
    echo "  - $(basename "$file")"
done
echo

# Check if shellcheck is available
if ! command -v shellcheck >/dev/null 2>&1; then
    echo "❌ FAIL: shellcheck not found in PATH"
    echo "💡 HINT: Install shellcheck or run in nix develop environment"
    exit 1
fi

# Track overall result
OVERALL_RESULT=0

# Run shellcheck on each file
echo "$SHELL_FILES" | while IFS= read -r file; do
    echo "🔍 Checking $(basename "$file")..."

    # Run shellcheck with standard options
    # SC1091: Not following sourced files (common in this context)
    # SC2034: Unused variables (may be used by sourcing scripts)
    if shellcheck -e SC1091,SC2034 "$file"; then
        echo "✅ PASS: $(basename "$file")"
    else
        echo "❌ FAIL: $(basename "$file") has ShellCheck violations"
        OVERALL_RESULT=1
    fi
    echo
done

# Final result (note: subshell limitation requires re-checking)
FINAL_CHECK=0
echo "🔍 Final verification pass..."
echo "$SHELL_FILES" | while IFS= read -r file; do
    if ! shellcheck -e SC1091,SC2034 "$file" >/dev/null 2>&1; then
        FINAL_CHECK=1
        echo "❌ Final check failed for $(basename "$file")"
    fi
done

# Check final result by re-running the test
echo "📊 Quality Gate Summary:"
echo "$SHELL_FILES" | while IFS= read -r file; do
    if shellcheck -e SC1091,SC2034 "$file" >/dev/null 2>&1; then
        echo "  ✅ $(basename "$file"): PASS"
    else
        echo "  ❌ $(basename "$file"): FAIL"
        exit 1
    fi
done

echo
echo "🎉 All shell scripts in lib/ passed ShellCheck quality gate!"
echo "🔧 Checked files: $(echo "$SHELL_FILES" | wc -l)"
echo "🛡️  Quality gate: PASSED"