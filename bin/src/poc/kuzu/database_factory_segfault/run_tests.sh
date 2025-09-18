#!/usr/bin/env bash
# テスト実行スクリプト（LD_LIBRARY_PATHを設定）

# gcc libのパスを見つける
GCC_LIB_PATH=$(find /nix/store -name "libstdc++.so.6" 2>/dev/null | head -1 | xargs dirname)

if [ -z "$GCC_LIB_PATH" ]; then
    echo "Error: Could not find libstdc++.so.6 in /nix/store"
    exit 1
fi

export LD_LIBRARY_PATH="$GCC_LIB_PATH:$LD_LIBRARY_PATH"
echo "LD_LIBRARY_PATH set to: $LD_LIBRARY_PATH"

# venv pytestを使用
if [ -f ".venv/bin/pytest" ]; then
    exec .venv/bin/pytest "$@"
else
    echo "Error: .venv/bin/pytest not found. Run 'uv sync' first."
    exit 1
fi