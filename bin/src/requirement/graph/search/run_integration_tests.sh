#!/bin/bash

# 統合テストを実行するスクリプト

echo "=== Search Modules Integration Test ==="
echo

# embeddingsディレクトリのvenv環境を使用
cd /home/nixos/bin/src/poc/search

# Pythonパスを設定
export PYTHONPATH=/home/nixos/bin/src/poc/search:$PYTHONPATH

# embeddingsのvenvを使ってテストを実行
/home/nixos/bin/src/poc/search/embeddings/.venv/bin/python -m pytest test_search_modules_integration.py -v