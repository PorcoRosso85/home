# Duck DBクリーンアップスクリプト
# 使用方法: bash duck.cleanup.sh
# 説明: テーブルとデータを削除

set -e  # エラー時に停止

# 設定
BASE_URL="http://localhost:8000/query"
CONTENT_TYPE="Content-Type: application/json"

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# クエリ実行関数（jqを使用してJSONを生成）
execute_query() {
    local query="$1"
    local description="$2"
    
    echo -n "実行中: $description... "
    
    # jqを使って適切にエスケープされたJSONを生成
    json_data=$(jq -n --arg q "$query" '{query: $q}')
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
        -H "$CONTENT_TYPE" \
        -d "$json_data")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" != "200" ]; then
        echo -e "${RED}失敗${NC}"
        echo "HTTPステータス: $http_code"
        echo "レスポンス: $body"
        return 1
    fi
    
    # エラーチェック（DROP文は成功してもsuccessフラグがない場合がある）
    if echo "$body" | grep -q '"success":false'; then
        echo -e "${RED}失敗${NC}"
        echo "レスポンス: $body"
        return 1
    fi
    
    echo -e "${GREEN}成功${NC}"
}

# jqの存在確認
if ! command -v jq &> /dev/null; then
    echo -e "${RED}エラー: jqがインストールされていません${NC}"
    echo "以下のコマンドでインストールしてください："
    echo "  nix-shell -p jq"
    exit 1
fi

# メイン処理
echo "Duck DBクリーンアップを開始します..."
echo -e "${YELLOW}警告: すべてのテーブルとデータが削除されます！${NC}"
echo ""

# 確認プロンプト
read -p "続行しますか？ (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "クリーンアップをキャンセルしました。"
    exit 0
fi

echo ""

# 現在のテーブル確認
echo "現在のテーブルを確認中..."
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_name IN ('VersionState', 'LocationURI', 'TRACKS_STATE_OF_LOCATED_ENTITY')" '{query: $q}')" | jq -r '.data[]?.table_name' 2>/dev/null || echo "テーブルなし"

echo ""

# トランザクション開始
execute_query "BEGIN TRANSACTION" "トランザクション開始"

# テーブル削除（依存関係の逆順）
echo ""
echo "テーブルを削除中..."

# 1. リレーションテーブルから削除
execute_query "DROP TABLE IF EXISTS TRACKS_STATE_OF_LOCATED_ENTITY" "リレーションテーブル削除"

# 2. 子テーブル削除
execute_query "DROP TABLE IF EXISTS LocationURI" "LocationURIテーブル削除"

# 3. 親テーブル削除
execute_query "DROP TABLE IF EXISTS VersionState" "VersionStateテーブル削除"

# その他の関連テーブルがある場合も削除
execute_query "DROP TABLE IF EXISTS HAS_CHILD" "HAS_CHILDテーブル削除（存在する場合）"
execute_query "DROP TABLE IF EXISTS FOLLOWS" "FOLLOWSテーブル削除（存在する場合）"

# トランザクションコミット
echo ""
execute_query "COMMIT" "トランザクションコミット"

echo ""
echo -e "${GREEN}クリーンアップが完了しました！${NC}"
echo ""

# 最終確認
echo "=== クリーンアップ後の状態 ==="
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'main' AND table_name IN ('VersionState', 'LocationURI', 'TRACKS_STATE_OF_LOCATED_ENTITY')" '{query: $q}')" | jq '.'

echo ""
echo "すべてのテーブルが削除されました。"