#!/usr/bin/env bash
#
# Basic .gitignore verification (lightweight version)
#

set -euo pipefail

echo "🔍 Basic .gitignore Verification"
echo

# Test 1: readme.nix protection
echo "📋 Testing readme.nix protection..."
PROTECTED=0
TOTAL=0

for readme_file in $(find . -name "readme.nix" -type f | sort); do
    ((TOTAL++))
    if git check-ignore -q -- "$readme_file" 2>/dev/null; then
        echo "❌ IGNORED: $readme_file"
    else
        echo "✅ OK: $readme_file"
        ((PROTECTED++))
    fi
done

echo "   Result: $PROTECTED/$TOTAL protected"
echo

# Test 2: artifact exclusion
echo "🗑️  Testing artifact patterns..."
IGNORED=0
TESTED=0

for artifact in "result" "logs/test.log" "temp.tmp" "backup.bak"; do
    ((TESTED++))
    if git check-ignore -q -- "$artifact" 2>/dev/null; then
        echo "✅ IGNORED: $artifact"
        ((IGNORED++))
    else
        echo "❌ NOT IGNORED: $artifact"
    fi
done

echo "   Result: $IGNORED/$TESTED patterns working"
echo

# Summary
if [[ $PROTECTED -eq $TOTAL ]] && [[ $IGNORED -gt 0 ]]; then
    echo "🎉 Basic verification PASSED"
    exit 0
else
    echo "💥 Basic verification FAILED"
    exit 1
fi