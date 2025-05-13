# 色付きの出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 環境変数の設定
export LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/":$LD_LIBRARY_PATH

# 基本コマンド
DENO_CMD="nix run nixpkgs#deno -- run --allow-read --allow-write --allow-env --allow-net --allow-ffi"
CLI_PATH="/home/nixos/bin/src/log/interfaces/cli.ts"

# データベースファイルを削除
rm -f ./logs.db

# テーブルを初期化
echo -e "${YELLOW}テーブルを初期化します...${NC}"
$DENO_CMD $CLI_PATH init --verbose

# 正常なデータを挿入
echo -e "${YELLOW}正常なデータを挿入します...${NC}"
$DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (1, '123', json '{\"message\":\"テストエラー\"}')"

# 挿入結果を確認
echo -e "${YELLOW}挿入したデータを確認します...${NC}"
$DENO_CMD $CLI_PATH exec "SELECT * FROM logs"

# 無効なデータテスト
echo -e "${YELLOW}2桁コードのテスト（エラーになるはず）...${NC}"
ERROR_OUTPUT=$($DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (2, '12', json '{\"message\":\"テストエラー\"}')")
echo "$ERROR_OUTPUT"

# エラーメッセージをチェック
echo -e "${YELLOW}エラーメッセージをチェックします...${NC}"
if [[ "$ERROR_OUTPUT" == *"Constraint Error"* ]]; then
  echo -e "${GREEN}テスト成功: 期待通りのバリデーションエラーが発生しました!${NC}"
else
  echo -e "${RED}テスト失敗: 期待されたバリデーションエラーが発生しませんでした!${NC}"
  exit 1
fi

# エラータイプごとのテスト
# 文字を含むコード
echo -e "${YELLOW}文字を含むコードのテスト...${NC}"
ERROR_OUTPUT=$($DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (3, 'ABC', json '{\"message\":\"テストエラー\"}')")
echo "$ERROR_OUTPUT"
if [[ "$ERROR_OUTPUT" == *"Constraint Error"* && "$ERROR_OUTPUT" == *"regexp_matches"* ]]; then
  echo -e "${GREEN}文字を含むコードテスト成功!${NC}"
else
  echo -e "${RED}文字を含むコードテスト失敗!${NC}"
  exit 1
fi

# 3桁より多いコード
echo -e "${YELLOW}3桁より多いコードのテスト...${NC}"
ERROR_OUTPUT=$($DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (4, '1234', json '{\"message\":\"テストエラー\"}')")
echo "$ERROR_OUTPUT"
if [[ "$ERROR_OUTPUT" == *"Constraint Error"* && "$ERROR_OUTPUT" == *"regexp_matches"* ]]; then
  echo -e "${GREEN}3桁より多いコードテスト成功!${NC}"
else
  echo -e "${RED}3桁より多いコードテスト失敗!${NC}"
  exit 1
fi

# 文字列型のエラー
echo -e "${YELLOW}文字列型エラーのテスト...${NC}"
ERROR_OUTPUT=$($DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (5, '123', json '\"テストエラー\"')")
echo "$ERROR_OUTPUT"
if [[ "$ERROR_OUTPUT" == *"Constraint Error"* && "$ERROR_OUTPUT" == *"json_type"* ]]; then
  echo -e "${GREEN}文字列型エラーテスト成功!${NC}"
else
  echo -e "${RED}文字列型エラーテスト失敗!${NC}"
  exit 1
fi

# NULL値のテスト
echo -e "${YELLOW}NULLコードのテスト...${NC}"
ERROR_OUTPUT=$($DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (6, NULL, json '{\"message\":\"テストエラー\"}')")
echo "$ERROR_OUTPUT"
if [[ "$ERROR_OUTPUT" == *"Constraint Error"* && "$ERROR_OUTPUT" == *"NOT NULL"* ]]; then
  echo -e "${GREEN}NULLコードテスト成功!${NC}"
else
  echo -e "${RED}NULLコードテスト失敗!${NC}"
  exit 1
fi

echo -e "${GREEN}すべてのテストが成功しました!${NC}"
