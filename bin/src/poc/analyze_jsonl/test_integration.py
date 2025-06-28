#!/usr/bin/env python3
"""統合テスト: claude_sdkのログをanalyze_jsonlで分析"""

import os
import sys

# 環境変数設定
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

# パスを追加
sys.path.insert(0, '.')

from core import create_analyzer
from mod import analyze_directories

def main():
    print("=== Claude SDK ログ分析テスト ===\n")
    
    # テストディレクトリ
    log_dirs = ['/tmp/claude_logs/session1', '/tmp/claude_logs/session2']
    
    # アナライザー作成
    print("1. アナライザー作成")
    analyzer = create_analyzer(log_dirs)
    
    # 各セッションのログを登録
    print("\n2. ログファイル登録")
    for i, log_dir in enumerate(log_dirs):
        result = analyzer.register_jsonl_files(log_dir, 'stream.jsonl', f'session{i+1}')
        if result['ok']:
            print(f"✓ {log_dir}: {result['registered_count']} ファイル登録")
        else:
            print(f"✗ {log_dir}: {result['error']}")
    
    # 統合ビュー作成
    print("\n3. 統合ビュー作成")
    result = analyzer.create_unified_view('all_claude_logs')
    if result['ok']:
        print(f"✓ 統合ビュー 'all_claude_logs' 作成（{result['source_count']} ソース）")
    
    # クエリ実行
    print("\n4. 分析クエリ実行")
    
    # クエリ1: タスク別の統計
    print("\n[タスク別統計]")
    result = analyzer.query("""
        SELECT 
            task_id,
            MIN(timestamp) as started_at,
            MAX(timestamp) as completed_at,
            COUNT(*) as log_entries,
            MAX(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as has_error
        FROM all_claude_logs
        WHERE task_id IS NOT NULL
        GROUP BY task_id
        ORDER BY started_at
    """)
    
    if result['ok']:
        print(f"Columns: {result['data']['columns']}")
        for row in result['data']['rows']:
            print(f"  {row}")
    
    # クエリ2: Claude別のエラー率
    print("\n[Claude別エラー統計]")
    result = analyzer.query("""
        SELECT 
            claude_id,
            COUNT(*) as total_logs,
            SUM(CASE WHEN level = 'error' OR status = 'error' THEN 1 ELSE 0 END) as error_count,
            ROUND(100.0 * SUM(CASE WHEN level = 'error' OR status = 'error' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
        FROM all_claude_logs
        WHERE claude_id IS NOT NULL
        GROUP BY claude_id
    """)
    
    if result['ok']:
        print(f"Columns: {result['data']['columns']}")
        for row in result['data']['rows']:
            print(f"  {row}")
    
    # クエリ3: 時系列ログ分布
    print("\n[時系列ログ分布]")
    result = analyzer.query("""
        SELECT 
            strftime('%H:%M', timestamp) as time_bucket,
            source,
            COUNT(*) as log_count
        FROM all_claude_logs
        GROUP BY time_bucket, source
        ORDER BY time_bucket, source
    """)
    
    if result['ok']:
        print(f"Columns: {result['data']['columns']}")
        for row in result['data']['rows'][:10]:  # 最初の10行のみ表示
            print(f"  {row}")
        if result['data']['row_count'] > 10:
            print(f"  ... and {result['data']['row_count'] - 10} more rows")
    
    # 高レベルAPI使用例
    print("\n5. 高レベルAPI使用例")
    result = analyze_directories(
        log_dirs,
        "SELECT COUNT(DISTINCT task_id) as unique_tasks, COUNT(DISTINCT claude_id) as unique_claudes FROM all_logs"
    )
    
    if result['ok']:
        print(f"✓ 分析結果: {result['data']['rows'][0]}")
    else:
        print(f"✗ エラー: {result['error']}")


if __name__ == '__main__':
    main()