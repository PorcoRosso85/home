#!/usr/bin/env bash
# テスト実行スクリプト（nix develop環境内で実行）

echo "🧪 Running Tests..."
echo "===================="

# nix develop環境チェック
if ! command -v pnpm &> /dev/null; then
    echo "❌ Not in nix develop environment"
    echo "Please run: nix develop"
    exit 1
fi

# DDL+DQLテスト実行
echo ""
echo "📋 Test: DDL+DQL Integration"
node test-ddl-dql.mjs

# 結果表示
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Tests failed"
    exit 1
fi