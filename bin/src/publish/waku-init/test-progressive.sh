#!/bin/bash

echo "=== Progressive Enhancement Test ==="

# 1. 通常モード（use client有効）
echo "1. Normal mode (with client JS):"
ENABLE_CLIENT=true npm run build
curl -H "User-Agent: Mozilla/5.0" http://localhost:3000

# 2. NoJSモード（use client無効）
echo "2. NoJS mode (server only):"
ENABLE_CLIENT=false PROGRESSIVE_MODE=true npm run build
curl -H "User-Agent: Mozilla/5.0" http://localhost:3000

# 3. Botモード（自動的にサーバー版）
echo "3. Bot mode (auto server fallback):"
ENABLE_CLIENT=true npm run build
curl -H "User-Agent: Googlebot" http://localhost:3000

# 4. データセーブモード
echo "4. Data save mode:"
curl -H "Save-Data: on" http://localhost:3000

# 5. JavaScriptを無効にしたブラウザシミュレーション
echo "5. Simulating disabled JavaScript:"
curl -H "Accept: text/html" -H "Accept: */*;q=0.1" http://localhost:3000