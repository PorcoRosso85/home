#!/usr/bin/env bash

# 認証テストスクリプト
# 環境変数が設定されているか確認し、認証フローをテスト

set -e

echo "=== Gmail認証テスト ==="
echo

# 環境変数チェック
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ エラー: 環境変数が設定されていません"
    echo
    echo "以下を実行してください:"
    echo "export GOOGLE_CLIENT_ID='your-client-id'"
    echo "export GOOGLE_CLIENT_SECRET='your-client-secret'"
    echo
    echo "詳細は SIMPLE_AUTH_SETUP.md を参照"
    exit 1
fi

echo "✅ 環境変数確認OK"
echo "  GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:0:20}..."
echo "  GOOGLE_CLIENT_SECRET: ***"
echo

# 既存のトークンファイルをチェック
if [ -f ".gmail_tokens.json" ]; then
    echo "📄 既存のトークンファイルが見つかりました"
    echo -n "削除して新規認証をテストしますか？ (y/N): "
    read answer
    if [ "$answer" = "y" ]; then
        rm .gmail_tokens.json
        echo "✅ トークンファイルを削除しました"
    fi
    echo
fi

# 認証テスト実行
echo "🚀 認証テストを開始します..."
echo "  （初回はブラウザが開きます）"
echo
nix run .#gmail -- --limit 1

echo
echo "=== テスト完了 ==="