#!/usr/bin/env python3
"""
Claude Code Transport Module
複数のClaude Codeインスタンス間の通信を管理
JSONL基軸でセッション識別
"""

import os
import subprocess
import time
import json
import glob
from pathlib import Path
from typing import Optional, Dict, Any


class ClaudeSession:
    """単一のClaude Codeセッション管理"""
    
    def __init__(self, session_id: int, work_dir: str):
        self.session_id = session_id
        self.work_dir = Path(work_dir).resolve()
        self.jsonl_path: Optional[Path] = None
        self.process: Optional[subprocess.Popen] = None
        self.claude_shell = Path("/home/nixos/bin/src/develop/claude/ui/claude-shell.sh")
        
    def _get_project_dir_name(self) -> str:
        """プロジェクトパスをClaude形式に変換
        /home/nixos/bin/src/poc/realtime-claudecode/02
        → -home-nixos-bin-src-poc-realtime-claudecode-02
        """
        path_str = str(self.work_dir)
        return path_str.replace('/', '-')
    
    def _find_jsonl(self) -> Optional[Path]:
        """セッションのJSONLファイルを特定"""
        project_name = self._get_project_dir_name()
        pattern = f"{Path.home()}/.claude/projects/{project_name}/*.jsonl"
        
        # 起動前の既存ファイル取得
        existing_files = set(glob.glob(pattern))
        
        # 新規ファイル検出のためポーリング（最大10秒）
        for _ in range(20):
            current_files = set(glob.glob(pattern))
            new_files = current_files - existing_files
            
            if new_files:
                # 最新のファイルを返す
                newest = max(new_files, key=os.path.getctime)
                return Path(newest)
            
            time.sleep(0.5)
        
        return None
    
    def start(self) -> bool:
        """Claude Codeを起動"""
        if not self.claude_shell.exists():
            print(f"[Session {self.session_id}] Error: claude-shell.sh not found")
            return False
        
        print(f"[Session {self.session_id}] Starting in {self.work_dir}")
        
        # 起動前のJSONLファイル記録
        existing_jsonls = self._find_existing_jsonls()
        
        # claude-shell.sh経由で起動
        try:
            self.process = subprocess.Popen(
                [str(self.claude_shell), str(self.work_dir)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # JSONL作成待機
            print(f"[Session {self.session_id}] Waiting for JSONL...")
            self.jsonl_path = self._find_jsonl()
            
            if self.jsonl_path:
                print(f"[Session {self.session_id}] JSONL: {self.jsonl_path.name}")
                return True
            else:
                print(f"[Session {self.session_id}] Warning: JSONL not detected")
                return True  # JSONLなくても継続
                
        except Exception as e:
            print(f"[Session {self.session_id}] Start failed: {e}")
            return False
    
    def _find_existing_jsonls(self) -> set:
        """既存のJSONLファイルを取得"""
        project_name = self._get_project_dir_name()
        pattern = f"{Path.home()}/.claude/projects/{project_name}/*.jsonl"
        return set(glob.glob(pattern))
    
    def send_command(self, command: str) -> bool:
        """コマンド送信"""
        if not self.process:
            print(f"[Session {self.session_id}] Not started")
            return False
        
        try:
            # stdin経由で送信
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()
            print(f"[Session {self.session_id}] Sent: {command}")
            return True
        except Exception as e:
            print(f"[Session {self.session_id}] Send failed: {e}")
            return False
    
    def get_latest_entry(self) -> Optional[Dict[str, Any]]:
        """最新のJSONLエントリを取得"""
        if not self.jsonl_path or not self.jsonl_path.exists():
            return None
        
        try:
            with open(self.jsonl_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except Exception as e:
            print(f"[Session {self.session_id}] JSONL read error: {e}")
        
        return None
    
    def is_ready(self) -> bool:
        """入力待機状態か確認"""
        entry = self.get_latest_entry()
        if not entry:
            return False
        
        # メッセージタイプから状態を推定
        # 実際のJSONL構造に応じて調整必要
        msg_type = entry.get('type', '')
        return 'user' in msg_type or 'prompt' in msg_type
    
    def close(self):
        """セッション終了"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            print(f"[Session {self.session_id}] Closed")


class SessionManager:
    """複数のClaude Codeセッション管理"""
    
    def __init__(self):
        self.sessions: Dict[int, ClaudeSession] = {}
        self.base_dir = Path("/home/nixos/bin/src/poc/realtime-claudecode")
        
    def get_or_create_session(self, session_id: int) -> ClaudeSession:
        """セッション取得または作成"""
        if session_id not in self.sessions:
            # ディレクトリパス決定（01, 02, 03...）
            work_dir = self.base_dir / f"{session_id:02d}"
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # セッション作成
            session = ClaudeSession(session_id, str(work_dir))
            if session.start():
                self.sessions[session_id] = session
            else:
                raise RuntimeError(f"Failed to start session {session_id}")
        
        return self.sessions[session_id]
    
    def send_to(self, session_id: int, command: str) -> bool:
        """指定セッションにコマンド送信"""
        print(f"\n[Manager] Sending to session {session_id}")
        session = self.get_or_create_session(session_id)
        
        # 待機状態確認
        if not session.is_ready():
            print(f"[Manager] Session {session_id} not ready, waiting...")
            time.sleep(2)
        
        return session.send_command(command)
    
    def get_status(self) -> Dict[int, str]:
        """全セッションの状態取得"""
        status = {}
        for sid, session in self.sessions.items():
            if session.is_ready():
                status[sid] = "ready"
            else:
                status[sid] = "busy"
        return status
    
    def close_all(self):
        """全セッション終了"""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()


def main():
    """コマンドライン使用例"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Code Transport')
    parser.add_argument('action', choices=['send', 'status', 'start'])
    parser.add_argument('session_id', type=int, nargs='?', help='Session ID (1, 2, 3...)')
    parser.add_argument('command', nargs='?', help='Command to send')
    
    args = parser.parse_args()
    
    manager = SessionManager()
    
    try:
        if args.action == 'send' and args.session_id and args.command:
            success = manager.send_to(args.session_id, args.command)
            print(f"Send result: {'Success' if success else 'Failed'}")
            
        elif args.action == 'status':
            status = manager.get_status()
            print("Session status:")
            for sid, state in status.items():
                print(f"  Session {sid}: {state}")
                
        elif args.action == 'start' and args.session_id:
            session = manager.get_or_create_session(args.session_id)
            print(f"Session {args.session_id} started")
            
        else:
            parser.print_help()
            
    finally:
        # クリーンアップ
        manager.close_all()


if __name__ == "__main__":
    main()