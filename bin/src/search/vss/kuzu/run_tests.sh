#!/usr/bin/env bash
# In-memory KuzuDBテストの実行スクリプト

echo "=== VSS In-Memory Tests ==="
echo ""
echo "注意: このテストは実際のKuzuDBインスタンスを使用します"
echo "NumPy依存の問題を回避するため、nix環境での実行を推奨します"
echo ""
echo "実行方法:"
echo "1. nix develop でシェルに入る"
echo "2. pytest tests/test_vss_in_memory.py -v"
echo ""
echo "または:"
echo "nix run .#test -- tests/test_vss_in_memory.py"
echo ""

# 代替: モックベースのテストを実行
echo "=== 代替: 仕様テストの実行 ==="
PYTHONPATH="/home/nixos/bin/src:$PYTHONPATH" python3 tests/test_vss_specification.py