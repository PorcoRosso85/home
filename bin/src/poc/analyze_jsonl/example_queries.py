#!/usr/bin/env python3
"""Claude Orchestraログ分析の実用的なクエリ例"""

import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

from mod import analyze_directories

def main():
    log_dirs = ['/tmp/claude_logs/session1', '/tmp/claude_logs/session2']
    
    print("=== Claude Orchestra ログ分析例 ===\n")
    
    # 1. 処理時間の分析
    print("1. タスク処理時間の分析")
    result = analyze_directories(log_dirs, """
        SELECT 
            task_id,
            claude_id,
            MAX(duration_ms) / 1000.0 as duration_seconds,
            status
        FROM all_logs
        WHERE duration_ms IS NOT NULL
        ORDER BY duration_ms DESC
    """)
    
    if result['ok']:
        for row in result['data']['rows']:
            print(f"  Task {row[0]} by {row[1]}: {row[2]}秒 ({row[3]})")
    
    # 2. エラー詳細
    print("\n2. エラー詳細")
    result = analyze_directories(log_dirs, """
        SELECT 
            timestamp,
            claude_id,
            task_id,
            error
        FROM all_logs
        WHERE error IS NOT NULL
        ORDER BY timestamp
    """)
    
    if result['ok']:
        for row in result['data']['rows']:
            print(f"  [{row[0]}] {row[1]}/{row[2]}: {row[3]}")
    
    # 3. 並行処理の分析
    print("\n3. 並行処理の状況")
    result = analyze_directories(log_dirs, """
        WITH task_timeline AS (
            SELECT 
                task_id,
                claude_id,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time
            FROM all_logs
            WHERE task_id IS NOT NULL
            GROUP BY task_id, claude_id
        )
        SELECT 
            t1.claude_id as claude1,
            t1.task_id as task1,
            t2.claude_id as claude2,
            t2.task_id as task2
        FROM task_timeline t1, task_timeline t2
        WHERE t1.task_id < t2.task_id
          AND t1.start_time <= t2.end_time
          AND t1.end_time >= t2.start_time
    """)
    
    if result['ok']:
        if result['data']['rows']:
            print("  並行実行されたタスク:")
            for row in result['data']['rows']:
                print(f"    {row[0]}/{row[1]} と {row[2]}/{row[3]}")
        else:
            print("  並行実行されたタスクはありません")


if __name__ == '__main__':
    main()