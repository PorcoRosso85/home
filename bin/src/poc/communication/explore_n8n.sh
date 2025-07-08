#!/bin/bash
# n8nのメール実装を効率的に探索するスクリプト

N8N_DIR="/home/nixos/bin/src/poc/communication/source/n8n"
cd "$N8N_DIR"

echo "=== Gmail OAuth2認証の実装 ==="
cat packages/nodes-base/credentials/GmailOAuth2Api.credentials.ts | head -50

echo -e "\n=== Gmail ノードの実装概要 ==="
grep -n "class Gmail" packages/nodes-base/nodes/Google/Gmail/Gmail.node.ts -A 10

echo -e "\n=== IMAP メール読み取り実装 ==="
grep -n "connect" packages/nodes-base/nodes/EmailReadImap/EmailReadImap.node.ts -A 20

echo -e "\n=== 共通の認証パターン ==="
grep -rn "requestWithAuthentication" packages/nodes-base/nodes/Google/Gmail/ | head -10

echo -e "\n=== メールパース処理 ==="
grep -n "parseRawEmail" packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts -A 10