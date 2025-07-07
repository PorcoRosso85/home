#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Claude Graph POC テスト実行"
echo "=============================="
echo ""

# 各テストを実行
echo "📋 taskExplorer.test.ts を実行中..."
deno test taskExplorer.test.ts --allow-read --no-check
echo ""

echo "📋 taskPlanner.test.ts を実行中..."
deno test taskPlanner.test.ts --allow-read --no-check
echo ""

echo "📋 versionBasedExplorer.test.ts を実行中..."
deno test versionBasedExplorer.test.ts --allow-read --no-check
echo ""

# claudeIntegration.test.tsがあれば実行（現在は未実装のためスキップ）
# if [ -f "claudeIntegration.test.ts" ]; then
#   echo "📋 claudeIntegration.test.ts を実行中..."
#   deno test claudeIntegration.test.ts --allow-read --no-check
#   echo ""
# fi

echo ""
echo "✅ テスト実行完了"