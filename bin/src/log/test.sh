#!/bin/bash
# 色付きの出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 環境変数の設定
export LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/":$LD_LIBRARY_PATH
export LOG_LEVEL=4  # すべてのログを表示するため、DEBUGレベルを設定

# 基本コマンド
DENO_CMD="nix run nixpkgs#deno -- run --allow-read --allow-write --allow-env --allow-net --allow-ffi"
CLI_PATH="/home/nixos/bin/src/log/interfaces/cli.ts"

echo -e "${YELLOW}ロガーテスト開始${NC}"

# データベースファイルを削除
rm -f ./logs.db

# テーブルを初期化
echo -e "${YELLOW}テーブルを初期化します...${NC}"
$DENO_CMD $CLI_PATH init --verbose || {
  echo -e "${RED}テーブル初期化に失敗しました${NC}"
  exit 1
}

# 正常なデータを挿入
echo -e "${YELLOW}正常なデータを挿入します...${NC}"
$DENO_CMD $CLI_PATH exec "INSERT INTO logs (id, code, error) VALUES (1, '123', json '{\"message\":\"テストエラー\"}')" || {
  echo -e "${RED}正常なデータの挿入に失敗しました${NC}"
  exit 1
}

# 挿入結果を確認
echo -e "${YELLOW}挿入したデータを確認します...${NC}"
$DENO_CMD $CLI_PATH exec "SELECT * FROM logs" || {
  echo -e "${RED}データ確認に失敗しました${NC}"
  exit 1
}

# 新しいロガー機能をテスト
echo -e "${YELLOW}新しいロガー機能をテストします...${NC}"
echo "import { debug, info, warn, error, createLogger, consolePlugin, duckdbPlugin } from '/home/nixos/bin/src/log/mod.ts';

// 基本的なログ出力テスト
debug('デバッグメッセージ');
info('情報メッセージ', { test: true });
warn('警告メッセージ');
error('エラーメッセージ', new Error('テストエラー'));

// カスタムロガーのテスト
const logger = createLogger([
  consolePlugin({ format: 'json', useColors: true })
]);

logger.info('カスタムロガーからの情報', { custom: true });
" > /tmp/logger_test.ts

$DENO_CMD /tmp/logger_test.ts || {
  echo -e "${RED}ロガー機能のテストに失敗しました${NC}"
  exit 1
}

echo -e "${GREEN}すべてのテストが成功しました!${NC}"
