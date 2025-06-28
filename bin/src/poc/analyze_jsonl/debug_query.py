#!/usr/bin/env python3
"""クエリのデバッグ"""

import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

from core import create_analyzer

def debug():
    log_dirs = ['/tmp/claude_logs/session1', '/tmp/claude_logs/session2']
    analyzer = create_analyzer(log_dirs)
    
    # 各ログファイルを個別に登録
    analyzer.register_jsonl_files('/tmp/claude_logs/session1', 'stream.jsonl', 'session1')
    analyzer.register_jsonl_files('/tmp/claude_logs/session2', 'stream.jsonl', 'session2')
    
    # 各ビューの構造を確認
    print("=== ビュー構造の確認 ===")
    for view in ['session1', 'session2']:
        result = analyzer.query(f"SELECT * FROM {view} LIMIT 1")
        if result['ok'] and result['data']['rows']:
            print(f"\n{view} columns: {result['data']['columns']}")
        else:
            print(f"\n{view}: Empty or error")
    
    # 統合ビューを作成
    print("\n=== 統合ビュー作成 ===")
    result = analyzer.create_unified_view('all_logs')
    print(f"Result: {result}")
    
    # 統合ビューの確認
    print("\n=== 統合ビューの確認 ===")
    result = analyzer.query("SELECT * FROM all_logs LIMIT 5")
    if result['ok']:
        print(f"Columns: {result['data']['columns']}")
        print(f"Rows: {result['data']['row_count']}")
        for row in result['data']['rows']:
            print(f"  {row}")
    else:
        print(f"Error: {result['error']}")

if __name__ == '__main__':
    debug()