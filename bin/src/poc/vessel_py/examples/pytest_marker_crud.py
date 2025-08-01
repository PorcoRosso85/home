#!/usr/bin/env python3
"""
pytest マーカーCRUD操作の実証例
知見を「動くドキュメント」として記録
"""
import pytest

# テスト対象のダミーテスト
@pytest.mark.skip(reason="デフォルトでスキップ")
def test_example_skip():
    """スキップマーカーのデモ用テスト"""
    assert True

@pytest.mark.slow
def test_example_slow():
    """slowマーカーのデモ用テスト"""
    assert True

def test_example_normal():
    """マーカーなしのテスト"""
    assert True

# conftest.py として使用する場合のマーカー操作
def pytest_collection_modifyitems(items):
    """
    実証された pytestマーカーCRUD操作
    
    結論：
    - item.keywords での削除は不可能（読み取り専用）
    - own_markers の直接操作で完全なCRUD実現
    """
    import os
    
    for item in items:
        # CREATE（追加）
        if "normal" in item.name:
            item.add_marker(pytest.mark.custom("動的に追加"))
        
        # READ（読み取り）
        markers = list(item.iter_markers())
        skip_marker = item.get_closest_marker("skip")
        
        # DELETE（削除） - FORCE_RUN環境変数で制御
        if os.environ.get("FORCE_RUN") == "1":
            item.own_markers = [
                m for m in item.own_markers
                if not (hasattr(m, 'mark') and m.mark.name == "skip")
            ]
        
        # UPDATE（更新） - slowをvery_slowに変更
        if any(m.mark.name == "slow" for m in item.own_markers if hasattr(m, 'mark')):
            # 1. 既存マーカーを削除
            item.own_markers = [
                m for m in item.own_markers 
                if not (hasattr(m, 'mark') and m.mark.name == "slow")
            ]
            # 2. 新しいマーカーを追加
            item.add_marker(pytest.mark.very_slow)

if __name__ == "__main__":
    # 実行例を表示
    print("""
=== pytestマーカーCRUD操作の実行例 ===

1. 通常実行（skipマーカーが有効）:
   pytest examples/pytest_marker_crud.py -v

2. FORCE_RUN実行（skipマーカーを削除）:
   FORCE_RUN=1 pytest examples/pytest_marker_crud.py -v

3. マーカー確認:
   pytest examples/pytest_marker_crud.py --collect-only

実証結果:
- 通常実行: test_example_skip SKIPPED
- FORCE_RUN=1: test_example_skip PASSED
- test_example_slow → very_slow マーカーに変更
- test_example_normal → custom マーカーが追加
""")