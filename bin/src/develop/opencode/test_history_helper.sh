#!/usr/bin/env bash
set -euo pipefail

# Test: 履歴ライブラリの仕様
# - oc_history_get_messages(SESSION_ID, LIMIT)
# - oc_history_format_text(JSON_ARRAY)
# - oc_history_format_json(JSON_ARRAY)

echo "🧪 Testing History Helper Library"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# Source session helper first (dependency)
if [ -f "$REPO_ROOT/lib/session-helper.sh" ]; then
    source "$REPO_ROOT/lib/session-helper.sh"
else
    echo "❌ FAIL: lib/session-helper.sh not found (dependency)"
    exit 1
fi

# Source the history helper (to be created)
if [ -f "$REPO_ROOT/lib/history-helper.sh" ]; then
    source "$REPO_ROOT/lib/history-helper.sh"
else
    echo "❌ FAIL: lib/history-helper.sh not found"
    exit 1
fi

# Test 1: oc_history_get_messages 関数の存在確認
echo "Testing oc_history_get_messages function exists..."
if declare -f oc_history_get_messages > /dev/null; then
    echo "✅ PASS: oc_history_get_messages function exists"
else
    echo "❌ FAIL: oc_history_get_messages function not found"
    exit 1
fi

# Test 2: oc_history_format_text 関数の存在確認
echo "Testing oc_history_format_text function exists..."
if declare -f oc_history_format_text > /dev/null; then
    echo "✅ PASS: oc_history_format_text function exists"
else
    echo "❌ FAIL: oc_history_format_text function not found"
    exit 1
fi

# Test 3: oc_history_format_json 関数の存在確認
echo "Testing oc_history_format_json function exists..."
if declare -f oc_history_format_json > /dev/null; then
    echo "✅ PASS: oc_history_format_json function exists"
else
    echo "❌ FAIL: oc_history_format_json function not found"
    exit 1
fi

# Test 4: 基本的なJSON処理テスト（サンプルデータ）
echo "Testing basic JSON formatting..."
sample_json='[{"info":{"type":"user"},"parts":[{"type":"text","text":"Hello"}]}, {"info":{"type":"assistant"},"parts":[{"type":"text","text":"Hi there!"}]}]'

if echo "$sample_json" | oc_history_format_text | grep -q "Hello"; then
    echo "✅ PASS: Text formatting works with sample data"
else
    echo "❌ FAIL: Text formatting should process sample data"
    exit 1
fi

if echo "$sample_json" | oc_history_format_json | jq -e '.[0].info.type' >/dev/null 2>&1; then
    echo "✅ PASS: JSON formatting preserves structure"
else
    echo "❌ FAIL: JSON formatting should preserve structure"
    exit 1
fi

echo "🟢 All history helper library tests PASSED"