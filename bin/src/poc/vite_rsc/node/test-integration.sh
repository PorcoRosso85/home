#!/bin/bash

echo "=== RSC統合テスト ==="
echo ""
echo "1. ビルドを実行..."
npm run build

echo ""
echo "2. ビルド結果の確認..."
node test-rsc-environments.js

echo ""
echo "3. プロダクションサーバー起動..."
echo "   サーバーは http://localhost:3000 で起動します"
echo "   Ctrl+C で停止できます"
echo ""
echo "テスト項目:"
echo "  - http://localhost:3000      → HTML (SSR)"
echo "  - http://localhost:3000/.rsc → RSC Stream"
echo ""

node server.js