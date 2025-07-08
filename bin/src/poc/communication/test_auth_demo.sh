#!/usr/bin/env bash

# デモ用認証テスト（実際のクレデンシャルは使用しない）

echo "=== Gmail認証デモ ==="
echo
echo "実際の使用方法:"
echo
echo "1. Google Cloud Consoleでアプリケーションを作成"
echo "   https://console.cloud.google.com/"
echo
echo "2. OAuth 2.0 クライアントIDを作成"
echo "   - リダイレクトURI: http://localhost:8080/callback"
echo
echo "3. 環境変数を設定:"
echo "   export GOOGLE_CLIENT_ID='your-client-id.apps.googleusercontent.com'"
echo "   export GOOGLE_CLIENT_SECRET='GOCSPX-your-secret'"
echo
echo "4. 実行:"
echo "   nix develop -c deno run --allow-all ./mail/cli_full_auto.ts"
echo
echo "動作の流れ:"
echo "- 初回実行時、ブラウザが自動で開きます"
echo "- Googleアカウントでログイン"
echo "- 権限を許可"
echo "- 自動でコードを取得してメール一覧を表示"
echo "- 2回目以降は自動認証"
echo
echo "=== 現在の実装状況 ==="
echo "✅ 完全自動認証フロー"
echo "✅ ブラウザ自動起動"
echo "✅ コード自動取得"
echo "✅ トークン自動更新"
echo "⚠️  日付フィルタリング（未実装）"