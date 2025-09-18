#!/usr/bin/env bash
# R2 バケット作成・削除デモ

set -e

echo "=== R2 バケット操作デモ ==="
echo ""

# 環境変数読み込み
source .env.local

# バケット名
BUCKET_NAME="test-bucket-demo-$(date +%s)"

echo "1. Cloudflare API（wrangler）でバケット作成"
echo "   ※ wranglerはAPIトークンを使用"
echo ""

# wranglerが利用可能な場合
if command -v wrangler &> /dev/null; then
    echo "wrangler r2 bucket create $BUCKET_NAME"
    wrangler r2 bucket create "$BUCKET_NAME" || echo "エラー: wrangler認証失敗"
else
    echo "wranglerが見つかりません"
fi

echo ""
echo "2. S3 API（MinIO Client）でバケット操作"
echo "   ※ S3 APIはAccess Key/Secret Keyを使用"
echo ""

# MinIO Client設定
echo "mc alias set r2 $R2_ENDPOINT $R2_ACCESS_KEY_ID $R2_SECRET_ACCESS_KEY"
mc alias set r2 "$R2_ENDPOINT" "$R2_ACCESS_KEY_ID" "$R2_SECRET_ACCESS_KEY" --api S3v4

# バケット作成
echo "mc mb r2/$BUCKET_NAME"
mc mb "r2/$BUCKET_NAME" || echo "エラー: S3 API認証失敗"

# バケット一覧
echo ""
echo "3. バケット一覧表示"
mc ls r2/

# バケット削除
echo ""
echo "4. バケット削除"
echo "mc rb r2/$BUCKET_NAME"
mc rb "r2/$BUCKET_NAME"

echo ""
echo "=== デモ完了 ==="