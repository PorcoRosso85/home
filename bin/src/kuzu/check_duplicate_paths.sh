#!/bin/bash
# 重複パスチェックスクリプト
# テスト経由と直接実装の両方のパスが存在しないことを確認

DB_PATH="/home/nixos/bin/src/kuzu/kuzu_db"

echo "=== 重複パスチェック ==="
echo ""

# 重複パスを検出するクエリ
DUPLICATE_CHECK_QUERY="
MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(impl:CodeEntity)
WHERE EXISTS {
  (r)-[:IS_VERIFIED_BY]->(:CodeEntity)-[:TESTS]->(impl)
}
RETURN r.id as requirement, impl.name as duplicate_implementation;"

# クエリ実行して結果を変数に格納
RESULT=$(echo "$DUPLICATE_CHECK_QUERY" | kuzu "$DB_PATH" 2>/dev/null)

# ヘッダー行を除いて結果をカウント
VIOLATION_COUNT=$(echo "$RESULT" | grep -E "│.*req_.*│" | wc -l)

if [ "$VIOLATION_COUNT" -gt 0 ]; then
  echo "❌ エラー: $VIOLATION_COUNT 件の重複パスが検出されました"
  echo ""
  echo "詳細:"
  echo "$RESULT" | grep -E "(requirement|│.*req_)"
  echo ""
  echo "以下のいずれかの対応が必要です："
  echo "1. IS_IMPLEMENTED_BY関係を削除する"
  echo "2. IS_VERIFIED_BY → TESTS関係を削除する"
  exit 1
else
  echo "✅ 重複パスなし: すべての要件は単一のパスで実装と接続されています"
fi

echo ""
echo "=== テスト中心設計の検証 ==="

# テスト経由の実装を確認
echo ""
echo "テスト経由の実装:"
echo "MATCH (r:RequirementEntity)-[:IS_VERIFIED_BY]->(test:CodeEntity)-[:TESTS]->(impl:CodeEntity)
RETURN r.id, test.name, impl.name;" | kuzu "$DB_PATH" 2>/dev/null | grep -E "(│|id|name)"

# 直接実装（テストなし）を確認
echo ""
echo "直接実装（テストなし）:"
echo "MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(impl:CodeEntity)
WHERE NOT EXISTS {
  (r)-[:IS_VERIFIED_BY]->(:CodeEntity)-[:TESTS]->(impl)
}
RETURN r.id, impl.name;" | kuzu "$DB_PATH" 2>/dev/null | grep -E "(│|id|name)"

echo ""
echo "=== チェック完了 ==="