#!/usr/bin/env python3
"""完全自動化されたオーケストレーター意思決定"""

import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

from mod import analyze_directories
import json

class OrchestratorDecision:
    def __init__(self, log_dirs):
        self.log_dirs = log_dirs
        
    def get_next_actions(self):
        """次のアクションを自動的に決定"""
        
        actions = []
        
        # 1. アイドル状態のClaudeを取得
        idle_claudes = self._get_idle_claudes()
        
        # 2. 実行可能なタスクを取得
        executable_tasks = self._get_executable_tasks()
        
        # 3. リトライが必要なタスクを取得
        retry_tasks = self._get_retry_tasks()
        
        # 4. アクションを生成
        for claude_id in idle_claudes:
            # リトライタスクを優先
            retry_task = next((t for t in retry_tasks if t['claude_id'] == claude_id), None)
            if retry_task:
                actions.append({
                    'claude_id': claude_id,
                    'action': 'RETRY',
                    'task_id': retry_task['task_id'],
                    'command': f"tsx claude.ts --uri ./{claude_id} --print '{retry_task['task_id']}を再実行: {retry_task['fix_suggestion']}'"
                })
            # 新規タスクを割り当て
            elif executable_tasks:
                task = executable_tasks.pop(0)  # 優先度順に取得
                actions.append({
                    'claude_id': claude_id,
                    'action': 'NEW_TASK',
                    'task_id': task['task_id'],
                    'command': f"tsx claude.ts --uri ./{claude_id} --print '{task['description']}'"
                })
        
        return actions
    
    def _get_idle_claudes(self):
        """アイドル状態のClaude一覧を取得"""
        result = analyze_directories(self.log_dirs, """
            WITH latest_status AS (
                SELECT 
                    claude_id,
                    status,
                    ROW_NUMBER() OVER (PARTITION BY claude_id ORDER BY timestamp DESC) as rn
                FROM all_logs
                WHERE claude_id IS NOT NULL AND status IS NOT NULL
            )
            SELECT DISTINCT claude_id
            FROM latest_status
            WHERE rn = 1 AND status IN ('completed', 'error')
        """)
        
        if result['ok']:
            return [row[0] for row in result['data']['rows']]
        return []
    
    def _get_retry_tasks(self):
        """リトライが必要なタスク一覧を取得"""
        result = analyze_directories(self.log_dirs, """
            SELECT DISTINCT
                task_id,
                claude_id,
                error,
                CASE 
                    WHEN error LIKE '%timeout%' THEN 'タイムアウトを延長して再試行'
                    WHEN error LIKE '%library%' THEN '代替ライブラリを使用して再試行'
                    ELSE 'エラー原因を調査して再試行'
                END as fix_suggestion
            FROM all_logs
            WHERE status = 'error' AND error IS NOT NULL
            ORDER BY timestamp DESC
        """)
        
        if result['ok']:
            return [
                {
                    'task_id': row[0],
                    'claude_id': row[1],
                    'error': row[2],
                    'fix_suggestion': row[3]
                }
                for row in result['data']['rows']
            ]
        return []
    
    def _get_executable_tasks(self):
        """実行可能な新規タスク（要件グラフから取得する想定）"""
        # 本来はKuzuDBの要件グラフから取得
        # ここではデモ用にハードコード
        return [
            {
                'task_id': 'task008',
                'description': 'task008: データアーカイブ処理を実行',
                'priority': 'low',
                'depends_on': []
            },
            {
                'task_id': 'task010',
                'description': 'task010: システム監視ダッシュボード更新',
                'priority': 'medium',
                'depends_on': []
            }
        ]
    
    def print_decision(self):
        """意思決定結果を表示"""
        actions = self.get_next_actions()
        
        print("=== 自動化されたオーケストレーター意思決定 ===\n")
        
        if not actions:
            print("現在、実行可能なアクションはありません。")
            print("全てのClaudeがビジー状態か、実行可能なタスクがありません。")
            return
        
        print(f"【実行すべきアクション数: {len(actions)}】\n")
        
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action['claude_id']} → {action['task_id']} ({action['action']})")
            print(f"   コマンド: {action['command']}")
            print()
        
        # バッチ実行スクリプトも生成
        print("\n【バッチ実行スクリプト】")
        print("```bash")
        print("#!/bin/bash")
        print("# オーケストレーター自動実行スクリプト")
        for action in actions:
            print(f"{action['command']} &")
        print("wait")
        print("echo '全タスクの割り当てが完了しました'")
        print("```")


if __name__ == '__main__':
    log_dirs = ['/tmp/claude_logs/session1', '/tmp/claude_logs/session2']
    orchestrator = OrchestratorDecision(log_dirs)
    orchestrator.print_decision()