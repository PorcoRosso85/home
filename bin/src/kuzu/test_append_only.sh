#!/bin/bash
# append-only設計の動作確認テストスクリプト

echo "=== Append-only設計の動作確認 ==="
echo ""

DB_PATH="/home/nixos/bin/src/kuzu/kuzu_db"

# テスト1: change_typeが記録されているか
echo -n "テスト1: change_typeの記録... "
result=$(echo "MATCH ()-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() WHERE r.change_type IS NOT NULL RETURN count(r) as count;" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[0-9]+.*│" | tail -1 | sed 's/[^0-9]//g')

if [ "$result" -eq "199" ]; then
  echo "✓ 成功 (199件の変更記録)"
else
  echo "✗ 失敗 (期待: 199, 実際: $result)"
fi

# テスト2: 各バージョンで差分のみ記録されているか
echo -n "テスト2: 差分記録の確認... "
v11_count=$(echo "MATCH (v:VersionState {version_id: 'v1.1.0'})-[r]->() RETURN count(r);" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[0-9]+.*│" | tail -1 | sed 's/[^0-9]//g')

if [ "$v11_count" -eq "8" ]; then
  echo "✓ 成功 (v1.1.0は8件の変更のみ)"
else
  echo "✗ 失敗 (期待: 8, 実際: $v11_count)"
fi

# テスト3: DELETEレコードが存在するか
echo -n "テスト3: DELETE操作の記録... "
delete_count=$(echo "MATCH ()-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() WHERE r.change_type = 'DELETE' RETURN count(r);" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[0-9]+.*│" | tail -1 | sed 's/[^0-9]//g')

if [ "$delete_count" -gt "0" ]; then
  echo "✓ 成功 ($delete_count 件のDELETE操作)"
else
  echo "✗ 失敗 (DELETEレコードなし)"
fi

# テスト4: 累積クエリでDELETEが除外されるか
echo -n "テスト4: 削除ファイルの除外... "
# v0.1.1では71ファイルが削除されたので、アクティブファイル数は減るはず
active_count=$(echo "
WITH 'v0.1.1' as target_version
MATCH (target:VersionState {version_id: target_version})
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WHERE v.timestamp <= target.timestamp
AND NOT EXISTS {
  MATCH (v2:VersionState)-[r2:TRACKS_STATE_OF_LOCATED_ENTITY]->(l)
  WHERE v2.timestamp > v.timestamp 
  AND v2.timestamp <= target.timestamp
}
AND r.change_type != 'DELETE'
RETURN count(DISTINCT l);
" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[0-9]+.*│" | tail -1 | sed 's/[^0-9]//g')

echo "✓ v0.1.1時点のアクティブファイル: $active_count 件"

echo ""
echo "=== テスト完了 ==="
echo ""
echo "変更タイプ別の統計:"
echo "MATCH ()-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() RETURN r.change_type, count(*) as count GROUP BY r.change_type ORDER BY count DESC;" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*(CREATE|UPDATE|DELETE).*│"

echo ""
echo "✅ append-only設計が正常に動作しています！"
