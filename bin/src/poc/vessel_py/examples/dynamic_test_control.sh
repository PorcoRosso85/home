#!/bin/bash
# pytest vesselを使った動的テスト制御の例

echo "=== pytest vessel による動的テスト制御 ==="
echo ""

# 1. 全てのskipを解除
echo "1. 全てのskipマーカーを解除:"
echo 'for item in items: remove_skip(item)' | python -m pytest --conftest-file=../pytest_vessel.py examples/pytest_marker_crud.py -v

echo ""

# 2. 特定のテストだけskip
echo "2. normalテストだけskip追加:"
cat << 'EOF' | python -m pytest --conftest-file=../pytest_vessel.py examples/pytest_marker_crud.py -v
for item in items:
    if "normal" in item.name:
        add_skip(item, "動的にスキップ追加")
EOF

echo ""

# 3. 条件付きマーカー操作
echo "3. 条件付きでマーカー操作:"
cat << 'EOF' | python -m pytest --conftest-file=../pytest_vessel.py examples/pytest_marker_crud.py -v
import os
for item in items:
    # 環境変数で制御
    if os.environ.get("TEST_MODE") == "fast":
        # slowマーカーのテストをスキップ
        if item.get_closest_marker("slow"):
            add_skip(item, "fast mode enabled")
EOF