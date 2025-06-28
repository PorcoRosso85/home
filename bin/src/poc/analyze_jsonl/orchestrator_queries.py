#!/usr/bin/env python3
"""オーケストレーター（claude0）用の意思決定支援クエリ"""

import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

from mod import analyze_directories
from datetime import datetime

def analyze_for_orchestrator(log_dirs):
    """オーケストレーターが次のアクションを決定するための分析"""
    
    print("=== オーケストレーター向け分析 ===\n")
    
    # 1. 各Claudeの現在の状態
    print("1. 【現在の状態】 各Claudeは何をしているか？")
    result = analyze_directories(log_dirs, """
        WITH latest_status AS (
            SELECT 
                claude_id,
                task_id,
                status,
                timestamp,
                ROW_NUMBER() OVER (PARTITION BY claude_id ORDER BY timestamp DESC) as rn
            FROM all_logs
            WHERE claude_id IS NOT NULL AND status IS NOT NULL
        )
        SELECT 
            claude_id,
            task_id,
            status,
            timestamp,
            CASE 
                WHEN status IN ('in_progress', 'started') THEN 'BUSY'
                WHEN status IN ('completed', 'error') THEN 'IDLE'
                ELSE 'UNKNOWN'
            END as current_state
        FROM latest_status
        WHERE rn = 1
        ORDER BY claude_id
    """)
    
    idle_claudes = []
    if result['ok']:
        print("  Claude ID | 最後のタスク | 状態      | 最終更新時刻         | 現在")
        print("  " + "-" * 70)
        for row in result['data']['rows']:
            print(f"  {row[0]:9} | {row[1]:12} | {row[2]:9} | {row[3]} | {row[4]}")
        
        # アイドル状態のClaude IDを抽出
        idle_claudes = [row[0] for row in result['data']['rows'] if row[4] == 'IDLE']
        print(f"\n  → アイドル状態のClaude: {idle_claudes}")
    else:
        print(f"  エラー: {result.get('error', 'Unknown error')}")
    
    # 2. 失敗タスクの分析
    print("\n2. 【要対応】 失敗したタスクとリトライ可能性")
    result = analyze_directories(log_dirs, """
        SELECT 
            task_id,
            claude_id,
            error,
            timestamp,
            CASE 
                WHEN error LIKE '%timeout%' THEN 'RETRY_POSSIBLE'
                WHEN error LIKE '%library%' THEN 'RETRY_WITH_FIX'
                ELSE 'MANUAL_CHECK'
            END as action_recommendation
        FROM all_logs
        WHERE status = 'error' OR level = 'error'
        ORDER BY timestamp DESC
    """)
    
    if result['ok']:
        print("  タスクID  | Claude | エラー内容                            | 推奨アクション")
        print("  " + "-" * 80)
        for row in result['data']['rows']:
            print(f"  {row[0]:9} | {row[1]:6} | {row[2][:35]:35} | {row[4]}")
    
    # 3. パフォーマンス統計
    print("\n3. 【効率性】 Claudeごとのパフォーマンス統計")
    result = analyze_directories(log_dirs, """
        WITH task_stats AS (
            SELECT 
                claude_id,
                COUNT(DISTINCT task_id) as completed_tasks,
                AVG(duration_ms) / 1000.0 as avg_duration_sec,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM all_logs
            WHERE claude_id IS NOT NULL
            GROUP BY claude_id
        )
        SELECT 
            claude_id,
            completed_tasks,
            ROUND(avg_duration_sec, 1) as avg_duration_sec,
            error_count,
            CASE 
                WHEN error_count = 0 AND avg_duration_sec < 20 THEN 'HIGH_PERFORMER'
                WHEN error_count > 0 THEN 'NEEDS_ATTENTION'
                ELSE 'NORMAL'
            END as performance_rating
        FROM task_stats
        ORDER BY completed_tasks DESC
    """)
    
    if result['ok']:
        print("  Claude | タスク数 | 平均時間(秒) | エラー数 | 評価")
        print("  " + "-" * 60)
        for row in result['data']['rows']:
            print(f"  {row[0]:6} | {row[1]:8} | {row[2]:12} | {row[3]:8} | {row[4]}")
    
    # 4. 次のアクション提案
    print("\n4. 【次のアクション】 推奨される割り当て")
    
    # 現在の状態から動的に提案を生成
    result_status = analyze_directories(log_dirs, """
        WITH latest_status AS (
            SELECT 
                claude_id,
                status,
                ROW_NUMBER() OVER (PARTITION BY claude_id ORDER BY timestamp DESC) as rn
            FROM all_logs
            WHERE claude_id IS NOT NULL AND status IS NOT NULL
        )
        SELECT claude_id, status
        FROM latest_status
        WHERE rn = 1
    """)
    
    if result_status['ok']:
        print("\n  提案:")
        for row in result_status['data']['rows']:
            claude_id, status = row
            if status in ['completed', 'error']:
                print(f"  - {claude_id}: IDLE状態 → 新しいタスクを割り当て可能")
            elif status in ['in_progress', 'started']:
                print(f"  - {claude_id}: BUSY状態 → 現在のタスク完了を待機")
    
    if len(idle_claudes) >= 2:
        print(f"  - 並行処理の余地: {len(idle_claudes)}個のClaudeがアイドル状態")
    
    return idle_claudes


def generate_next_commands(idle_claudes):
    """アイドル状態のClaudeへの次のコマンドを生成"""
    print("\n5. 【実行コマンド例】")
    
    for claude_id in idle_claudes:
        print(f"\n  # {claude_id}への指示")
        if claude_id == 'claude1':
            print(f"  tsx claude.ts --uri ./{claude_id} --print 'タスク006: ユーザーレポートの生成を実行してください'")
        elif claude_id == 'claude2':
            print(f"  tsx claude.ts --uri ./{claude_id} --print 'タスク005を再実行: データベース接続のタイムアウトを回避する方法で再試行してください'")


if __name__ == '__main__':
    log_dirs = ['/tmp/claude_logs/session1', '/tmp/claude_logs/session2']
    idle_claudes = analyze_for_orchestrator(log_dirs)
    generate_next_commands(idle_claudes)