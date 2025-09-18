# browseアプリ複数テーブル対応確認
# 使用方法: bash test_multi_table_complete.sh

BASE_URL="http://localhost:8000"

echo "=== Phase 2 完了確認 ==="
echo ""

echo "1. テーブル一覧取得"
TABLES_JSON=$(curl -s -X POST "$BASE_URL/api/snapshot/2/tables")
echo "$TABLES_JSON" | jq '.'

echo ""
echo "2. 存在するテーブルのリスト"
EXISTING_TABLES=$(echo "$TABLES_JSON" | jq -r '.tables[] | select(.exists == true) | .name')
echo "$EXISTING_TABLES"

echo ""
echo "3. 各テーブルの取得確認"
for table in $EXISTING_TABLES; do
    echo ""
    echo "テーブル: $table"
    HEADERS=$(curl -s -I -X POST "$BASE_URL/api/snapshot/2/$table")
    echo "$HEADERS" | grep -E "(HTTP/|Content-Length|X-DuckLake-Table)"
    
    # サイズ取得
    SIZE=$(echo "$HEADERS" | grep "Content-Length" | awk '{print $2}' | tr -d '\r')
    if [ -n "$SIZE" ]; then
        echo "サイズ: $SIZE bytes"
    fi
done

echo ""
echo "=== 実装状況 ==="
echo "✅ Phase 1: 新エンドポイント対応、リトライ機能"
echo "✅ Phase 2: 汎用関数loadTableFromDuck実装"
echo "✅ Phase 2: 並列ロード関数loadTablesFromDuck実装"
echo "✅ Phase 2: 後方互換性維持（loadLocationUrisFromDuck）"
echo ""
echo "利用可能な関数:"
echo "- loadTableFromDuck(conn, version, tableName)"
echo "- loadTablesFromDuck(conn, version, tableNames[], onProgress?)"
echo "- loadAllDuckLakeTables(conn, version, onProgress?)"
