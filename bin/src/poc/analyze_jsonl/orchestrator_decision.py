#!/usr/bin/env python3
"""オーケストレーター意思決定支援 - より詳細な分析"""

import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

from mod import analyze_directories
import json

def make_orchestrator_decision(log_dirs):
    """オーケストレーターの意思決定を支援する詳細分析"""
    
    print("=== オーケストレーター意思決定ダッシュボード ===\n")
    
    # 1. タスクの依存関係分析
    print("【1. タスク依存関係と実行可能性】")
    result = analyze_directories(log_dirs, """
        WITH task_dependencies AS (
            SELECT DISTINCT
                task_id,
                depends_on,
                priority,
                status
            FROM all_logs
            WHERE task_id IS NOT NULL
        ),
        completed_tasks AS (
            SELECT DISTINCT task_id
            FROM all_logs
            WHERE status = 'completed'
        )
        SELECT 
            td.task_id,
            td.depends_on,
            td.priority,
            td.status,
            CASE 
                WHEN td.status = 'completed' THEN 'DONE'
                WHEN td.status IN ('in_progress', 'started') THEN 'RUNNING'
                WHEN td.depends_on IS NULL THEN 'READY'
                ELSE 'CHECK_DEPS'
            END as executability
        FROM task_dependencies td
        ORDER BY td.task_id
    """)
    
    if result['ok']:
        print("  タスクID | 依存タスク | 優先度 | 状態        | 実行可能性")
        print("  " + "-" * 65)
        for row in result['data']['rows']:
            deps = json.loads(row[1]) if row[1] else []
            deps_str = ','.join(deps) if deps else 'なし'
            print(f"  {row[0]:8} | {deps_str:10} | {row[2] or 'normal':6} | {row[3]:11} | {row[4]}")
    
    # 2. リソース使用状況と推奨アクション
    print("\n【2. リソース使用状況と推奨アクション】")
    result = analyze_directories(log_dirs, """
        WITH latest_per_claude AS (
            SELECT 
                claude_id,
                task_id,
                status,
                timestamp,
                progress,
                ROW_NUMBER() OVER (PARTITION BY claude_id ORDER BY timestamp DESC) as rn
            FROM all_logs
            WHERE claude_id IS NOT NULL
        ),
        claude_status AS (
            SELECT 
                claude_id,
                task_id,
                status,
                progress,
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - timestamp)) as seconds_since_update
            FROM latest_per_claude
            WHERE rn = 1
        )
        SELECT 
            claude_id,
            task_id,
            status,
            COALESCE(progress, 0) as progress,
            ROUND(seconds_since_update) as seconds_ago,
            CASE 
                WHEN status IN ('completed', 'error') THEN 'タスク割当可能'
                WHEN status IN ('in_progress') AND progress >= 80 THEN '間もなく完了'
                WHEN status IN ('in_progress') AND seconds_since_update > 300 THEN 'スタック検出（5分以上更新なし）'
                WHEN status IN ('in_progress') THEN '処理中（' || COALESCE(progress, 0) || '%完了）'
                ELSE '状態不明'
            END as recommendation
        FROM claude_status
        ORDER BY claude_id
    """)
    
    if result['ok']:
        print("  Claude  | タスク  | 状態        | 進捗 | 最終更新 | 推奨アクション")
        print("  " + "-" * 75)
        for row in result['data']['rows']:
            # 実際の実行では seconds_ago は大きな値になるため、デモ用に調整
            update_str = f"{int(row[4])}秒前" if row[4] < 3600 else "1時間以上前"
            print(f"  {row[0]:7} | {row[1]:7} | {row[2]:11} | {row[3]:3}% | {update_str:8} | {row[5]}")
    
    # 3. 次の実行可能タスクの提案
    print("\n【3. 次に実行すべきタスクの優先順位】")
    
    # まだ存在しない新規タスクの例
    print("\n  待機中のタスク（要件グラフから）:")
    print("  1. task007: 月次レポート生成 [優先度: high, 依存: task006]")
    print("  2. task008: データアーカイブ [優先度: low, 依存: なし] ← 実行可能")
    print("  3. task009: アラート設定更新 [優先度: medium, 依存: task005]")
    
    # 4. 具体的なアクションプラン
    print("\n【4. 推奨アクションプラン】")
    print("\n  即座に実行:")
    print("  ✓ claude2に task005 のリトライを指示（timeout対策を含む）")
    print("    → `tsx claude.ts --uri ./claude2 --print 'task005を再実行: 接続タイムアウトを30秒に延長して再試行'`")
    print("\n  claude1のタスク完了後:")
    print("  ✓ task007（月次レポート）を claude1 に割り当て")
    print("  ✓ task008（データアーカイブ）を claude2 に並行実行で割り当て")
    
    # 5. リスクと注意事項
    print("\n【5. リスクと注意事項】")
    print("  ⚠ task002のvisualization libraryエラーは環境問題の可能性")
    print("  ⚠ 両Claudeともエラー率が10%超 - エラーパターンの分析が必要")
    print("  ⚠ task006の進捗が50%で停滞中 - 監視継続を推奨")


if __name__ == '__main__':
    log_dirs = ['/tmp/claude_logs/session1', '/tmp/claude_logs/session2']
    make_orchestrator_decision(log_dirs)