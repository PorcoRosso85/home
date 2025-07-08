#!/usr/bin/env bash
# Gmail CLI実行スクリプト

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Denoを使って実行
exec deno run \
  --allow-net \
  --allow-read \
  --allow-write \
  --allow-env \
  --allow-run \
  "$SCRIPT_DIR/mail/cli_full_auto.ts" "$@"