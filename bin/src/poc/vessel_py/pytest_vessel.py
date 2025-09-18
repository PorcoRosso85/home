#!/usr/bin/env python3
"""
pytest Vessel - pytest動的制御コンテナ
標準入力から受け取ったマーカー操作スクリプトを実行する器
"""
import sys
import pytest

def pytest_collection_modifyitems(items):
    """テスト収集時にマーカーを動的に操作"""
    # 標準入力からスクリプトを読み込む
    if hasattr(sys.stdin, 'isatty') and not sys.stdin.isatty():
        script = sys.stdin.read()
    else:
        script = ""
    
    # 実行コンテキストを準備
    context = {
        'items': items,
        'pytest': pytest,
        '__name__': '__main__',
        'vessel': True
    }
    
    # マーカー操作のヘルパー関数を追加
    context['remove_skip'] = lambda item: setattr(item, 'own_markers', [
        m for m in item.own_markers 
        if not (hasattr(m, 'mark') and m.mark.name == "skip")
    ])
    
    context['add_skip'] = lambda item, reason="": item.add_marker(
        pytest.mark.skip(reason=reason)
    )
    
    # スクリプトを実行
    if script:
        try:
            exec(script, context)
        except Exception as e:
            print(f"Error in pytest vessel: {e}", file=sys.stderr)