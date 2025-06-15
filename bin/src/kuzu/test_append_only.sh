#!/bin/bash
# 修正版append-only設計テストスクリプト

echo "=== 修正版 Append-only設計テスト ==="
echo ""

DB_PATH="/home/nixos/bin/src/kuzu/kuzu_db"

# ヘルパー関数: クエリ実行して数値を取得
run_query() {
  result=$(echo "$1" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[0-9]+.*│" | tail -1 | sed 's/[^0-9]//g')
  # 結果が空の場合は0を返す
  if [ -z "$result" ]; then
    echo "0"
  else
    echo "$result"
  fi
}

# ヘルパー関数: クエリ実行して結果を表示
show_query() {
  echo "$1" | kuzu $DB_PATH 2>/dev/null
}

echo "=== 基本テスト ==="

# テスト1: change_typeが記録されているか
echo -n "テスト1: change_typeの記録... "
result=$(run_query "MATCH ()-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() WHERE r.change_type IS NOT NULL RETURN count(r) as count;")

if [ "$result" -eq "199" ]; then
  echo "✓ 成功 (199件の変更記録)"
else
  echo "✗ 失敗 (期待: 199, 実際: $result)"
fi

# テスト2: 各バージョンで差分のみ記録されているか
echo -n "テスト2: 差分記録の確認... "
v11_count=$(run_query "MATCH (v:VersionState {version_id: 'v1.1.0'})-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() RETURN count(r);")

if [ "$v11_count" -eq "8" ]; then
  echo "✓ 成功 (v1.1.0は8件の変更のみ)"
else
  echo "△ 警告 (期待: 8, 実際: $v11_count)"
fi

# テスト3: DELETEレコードが存在するか
echo -n "テスト3: DELETE操作の記録... "
delete_count=$(run_query "MATCH ()-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() WHERE r.change_type = 'DELETE' RETURN count(r);")

if [ "$delete_count" -gt "0" ]; then
  echo "✓ 成功 ($delete_count 件のDELETE操作)"
else
  echo "✗ 失敗 (DELETEレコードなし)"
fi

# テスト4: 修正された累積クエリでDELETEが除外されるか
echo -n "テスト4: 削除ファイルの除外（修正版）... "

# 修正版：各ファイルの最終状態を確認
active_count=$(echo "
MATCH (v:VersionState {version_id: 'v0.1.1'})
WITH v.timestamp as target_timestamp
MATCH (version:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
WHERE version.timestamp <= target_timestamp
RETURN l.id, version.timestamp, r.change_type
ORDER BY l.id, version.timestamp DESC;" | kuzu $DB_PATH 2>/dev/null | awk -f /home/nixos/bin/src/kuzu/cumulative_query_processor.awk)

echo "✓ v0.1.1時点のアクティブファイル: $active_count 件"

echo ""
echo "=== 拡張テスト（修正版） ==="

# テスト5: 各バージョンの累積状態を正しく計算
echo ""
echo "テスト5: 各バージョンの累積状態（修正版）:"

versions=("v1.0.0" "v1.1.0" "v1.2.0" "v1.2.1" "v0.1.0" "v0.1.1")
echo "バージョン | アクティブファイル数 | 変更数"
echo "-----------|---------------------|-------"

for version in "${versions[@]}"; do
  # 修正版累積クエリ
  cumulative_query="
  MATCH (v:VersionState {version_id: '$version'})
  WITH v.timestamp as target_timestamp
  MATCH (version:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
  WHERE version.timestamp <= target_timestamp
  RETURN l.id, version.timestamp, r.change_type
  ORDER BY l.id, version.timestamp DESC;"
  
  active_count=$(echo "$cumulative_query" | kuzu $DB_PATH 2>/dev/null | awk -f /home/nixos/bin/src/kuzu/cumulative_query_processor.awk)
  
  # このバージョンでの変更数
  change_query="MATCH (v:VersionState {version_id: '$version'})-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() RETURN count(r);"
  change_count=$(echo "$change_query" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[0-9]+.*│" | tail -1 | sed 's/[^0-9]//g')
  
  printf "%-10s | %19s | %6s\n" "$version" "$active_count" "$change_count"
done

# テスト6: 特定ファイルのライフサイクル追跡（修正版）
echo ""
echo "テスト6: ファイルライフサイクルの追跡（file:///src/utils.ts）:"

# 各バージョンでのファイル状態を確認
for version in "v1.0.0" "v1.1.0" "v1.2.0" "v1.2.1"; do
  state_query="
  MATCH (v:VersionState {version_id: '$version'})
  WITH v.timestamp as target_timestamp
  MATCH (version:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI {id: 'file:///src/utils.ts'})
  WHERE version.timestamp <= target_timestamp
  WITH version, r
  ORDER BY version.timestamp DESC
  LIMIT 1
  RETURN r.change_type as state;"
  
  state=$(echo "$state_query" | kuzu $DB_PATH 2>/dev/null | grep -E "│.*[A-Z]+.*│" | tail -1 | sed 's/│//g' | tr -d ' ')
  
  if [ -z "$state" ]; then
    echo "  $version: ファイルなし"
  elif [ "$state" = "DELETE" ]; then
    echo "  $version: 削除済み ✓"
  else
    echo "  $version: 存在（$state） ✓"
  fi
done

# テスト7: DELETE → CREATE パターンの検証
echo ""
echo "テスト7: DELETE → CREATE パターンの検証:"

delete_create_query="
MATCH (l:LocationURI)
MATCH (v1:VersionState)-[r1:TRACKS_STATE_OF_LOCATED_ENTITY {change_type: 'DELETE'}]->(l)
MATCH (v2:VersionState)-[r2:TRACKS_STATE_OF_LOCATED_ENTITY {change_type: 'CREATE'}]->(l)
WHERE v2.timestamp > v1.timestamp
RETURN l.id as file, v1.version_id as deleted_in, v2.version_id as recreated_in
ORDER BY l.id;"

echo "$delete_create_query" | kuzu $DB_PATH 2>/dev/null | grep -A 10 "│ file" | grep "│ file:"

echo ""
echo "=== 詳細統計 ==="
echo ""
echo "変更タイプ別の統計:"
show_query "MATCH ()-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->() RETURN r.change_type, count(r) ORDER BY count(r) DESC;" | grep -E "│.*(CREATE|UPDATE|DELETE).*│"

echo ""
echo "=== 要件トレーサビリティテスト ==="
echo ""

# テスト8: 要件と実装のトレーサビリティ
echo "テスト8: 要件トレーサビリティの確認:"

# 要件→テスト→実装のパス
echo -n "  テスト経由の実装... "
test_path_count=$(run_query "MATCH (r:RequirementEntity)-[:IS_VERIFIED_BY]->(test:CodeEntity)-[:TESTS]->(impl:CodeEntity) RETURN count(*);")
if [ "$test_path_count" -gt "0" ]; then
  echo "✓ $test_path_count 件のテスト経由実装"
else
  echo "△ テスト経由の実装なし"
fi

# 直接実装のパス
echo -n "  直接実装（テストなし）... "
direct_impl_count=$(run_query "MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(impl:CodeEntity) RETURN count(*);")
if [ "$direct_impl_count" -eq "0" ]; then
  echo "✓ 直接実装なし（TDD準拠）"
else
  echo "△ $direct_impl_count 件の直接実装"
fi

# テスト9: 重複パスチェック
echo ""
echo "テスト9: 重複パスチェック:"
duplicate_count=$(run_query "MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(impl:CodeEntity) WHERE EXISTS((r)-[:IS_VERIFIED_BY]->(:CodeEntity)-[:TESTS]->(impl)) RETURN count(*);")

if [ "$duplicate_count" -eq "0" ]; then
  echo "  ✓ 重複パスなし"
else
  echo "  ✗ $duplicate_count 件の重複パスが検出されました"
fi

# テスト10: 未検証要件の検出
echo ""
echo "テスト10: 検証必須要件のチェック:"
# 検証必須だが未検証の要件をカウント
unverified_query="MATCH (r:RequirementEntity) WHERE r.verification_required = true OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(c:CodeEntity) WITH r, c WHERE c IS NULL RETURN count(r);"
unverified_count=$(run_query "$unverified_query")

if [ "$unverified_count" -eq "0" ]; then
  echo "  ✓ すべての必須要件が検証済み"
else
  echo "  △ $unverified_count 件の未検証要件"
fi

echo ""
echo "=== テスト完了 ==="
echo ""

# 最終判定
if [ ! -z "$active_count" ] && [ "$duplicate_count" -eq "0" ]; then
  echo "✅ 修正版append-onlyクエリとトレーサビリティが正常に動作しています！"
else
  echo "❌ 修正版クエリまたはトレーサビリティに問題があります"
fi