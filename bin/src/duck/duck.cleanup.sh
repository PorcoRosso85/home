# DuckLakeクリーンアップスクリプト
# 使用方法: bash duck.cleanup.sh
# 説明: DuckLakeのデータディレクトリをクリーンアップ

set -e

# 設定
DATA_PATH="${DATA_FILES_PATH:-./data_files}"
if [[ "$DATA_PATH" != /* ]]; then
    DATA_PATH="$(pwd)/$DATA_PATH"
fi

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "DuckLakeクリーンアップを開始します..."
echo "データパス: $DATA_PATH"
echo ""

# 確認
echo -e "${YELLOW}警告: これによりすべてのDuckLakeデータが削除されます！${NC}"
echo -n "続行しますか？ (y/N): "
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "クリーンアップ中..."
    
    # カタログをデタッチ
    echo "カタログをデタッチ中..."
    curl -s -X POST http://localhost:8000/query \
        -H 'Content-Type: application/json' \
        -d '{"query": "DETACH lake"}' > /dev/null 2>&1 || true
    
    # データディレクトリを削除
    if [ -d "$DATA_PATH" ]; then
        rm -rf "$DATA_PATH"
        echo -e "${GREEN}データディレクトリを削除しました${NC}"
    else
        echo "データディレクトリが見つかりません"
    fi
    
    echo ""
    echo -e "${GREEN}クリーンアップが完了しました${NC}"
else
    echo ""
    echo "クリーンアップをキャンセルしました"
fi