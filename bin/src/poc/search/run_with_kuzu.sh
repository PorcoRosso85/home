#!/bin/bash
# KuzuDB実行用の汎用ラッパースクリプト

# キャッシュファイル
CACHE_FILE="$HOME/.cache/kuzu_libpath"

# キャッシュが存在しない場合のみ検索
if [ ! -f "$CACHE_FILE" ]; then
    LIBPATH=$(find /nix/store -name 'libstdc++.so.6' 2>/dev/null | head -1 | xargs dirname)
    if [ -n "$LIBPATH" ]; then
        mkdir -p "$(dirname "$CACHE_FILE")"
        echo "$LIBPATH" > "$CACHE_FILE"
    fi
else
    LIBPATH=$(cat "$CACHE_FILE")
fi

# ライブラリパスを設定して実行
if [ -n "$LIBPATH" ]; then
    export LD_LIBRARY_PATH="$LIBPATH:$LD_LIBRARY_PATH"
fi

# 引数として渡されたコマンドを実行
exec "$@"