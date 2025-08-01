#!/usr/bin/env bash
# テスト実行スクリプト

echo "=== Running vessel pipeline tests ==="

# Nix環境でPython3を使用
PYTHON=$(which python3 || which python)

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found"
    exit 1
fi

echo "Using Python: $PYTHON"

# テストを実行
$PYTHON test_simple.py && \
$PYTHON test_pipeline.py && \
echo "✅ All tests passed!"