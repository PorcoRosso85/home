#!/usr/bin/env bash

# コマンドライン引数を取得
ARGS="$@"

# 引数がない場合はデフォルトでヘルプを表示
if [ -z "$ARGS" ]; then
  ARGS="--help"
fi

#
AICHAT_FUNCTIONS_DIR="/home/nixos/bin/src/aichat_extension" nix run nixpkgs#aichat -- $ARGS
