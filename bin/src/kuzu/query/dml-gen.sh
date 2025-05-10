#!/bin/bash
# KuzuDB DML生成ツールラッパー

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# デフォルト値
ENTITY_FILE=""
ALL_FLAG=0
OUTPUT_DIR="${SCRIPT_DIR}/dml"
DDL_FILE="${SCRIPT_DIR}/ddl/schema.cypher"

# 使用方法を表示
show_usage() {
  echo "使用方法: $0 [オプション]"
  echo ""
  echo "オプション:"
  echo "  -e, --entity FILE     処理する単一エンティティ定義ファイル"
  echo "  -a, --all             すべてのエンティティ定義を処理"
  echo "  -o, --output-dir DIR  出力ディレクトリ（デフォルト: ./dml）"
  echo "  -d, --ddl FILE        DDLスキーマファイル（デフォルト: ./ddl/schema.cypher）"
  echo "  -h, --help            このヘルプを表示"
  echo ""
  echo "例:"
  echo "  $0 --entity dml/location_uri.json"
  echo "  $0 --all"
}

# コマンドライン引数の解析
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--entity)
      ENTITY_FILE="$2"
      shift 2
      ;;
    -a|--all)
      ALL_FLAG=1
      shift
      ;;
    -o|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -d|--ddl)
      DDL_FILE="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    *)
      echo "エラー: 不明なオプション $1"
      show_usage
      exit 1
      ;;
  esac
done

# 入力チェック
if [[ -z "$ENTITY_FILE" && $ALL_FLAG -eq 0 ]]; then
  echo "エラー: --entity または --all オプションを指定してください"
  show_usage
  exit 1
fi

# Python DML生成ツールを実行
cd "$SCRIPT_DIR"

if [[ $ALL_FLAG -eq 1 ]]; then
  python3 ./dml_generator.py --all --output-dir "$OUTPUT_DIR" --ddl "$DDL_FILE"
else
  python3 ./dml_generator.py --entity "$ENTITY_FILE" --output-dir "$OUTPUT_DIR" --ddl "$DDL_FILE"
fi
