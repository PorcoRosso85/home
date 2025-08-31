#!/usr/bin/env python3
"""
Claude Code Transport Module - Attach Version
既存のClaude Codeセッションに接続する版
"""

import os
import time
import json
import glob
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List


class ClaudeSession:
    """既存のClaude Codeセッションへの接続管理"""
    
    def __init__(self, session_id: int, work_dir: str):
        self.session_id = session_id
        self.work_dir = Path(work_dir).resolve()
        self.jsonl_path: Optional[Path] = None
        self.tmux_target: Optional[str] = None  # tmux pane ID
        
    def _get_project_dir_name(self) -> str:
        """プロジェクトパスをClaude形式に変換"""
        path_str = str(self.work_dir)
        return path_str.replace('/', '-')
    
    def _find_jsonl(self) -> Optional[Path]:
        """セッションのJSONLファイルを特定"""
        project_name = self._get_project_dir_name()
        pattern = f"{Path.home()}/.claude/projects/{project_name}/*.jsonl"
        
        files = glob.glob(pattern)
        if files:
            # 最新のファイルを返す
            newest = max(files, key=os.path.getctime)
            return Path(newest)
        
        return None
    
    def _find_tmux_pane(self) -> Optional[str]:
        """このセッションのtmux paneを特定"""
        # tmux list-panesで全paneを取得
        try:
            result = subprocess.run(
                ["tmux", "list-panes", "-a", "-F", 
                 "#{session_name}:#{window_index}.#{pane_index} #{pane_current_path}"],
                capture_output=True, text=True, check=True
            )
            
            # work_dirにマッチするpaneを探す
            for line in result.stdout.strip().split('\n'):
                if str(self.work_dir) in line:
                    pane_id = line.split()[0]
                    return pane_id
                    
        except subprocess.CalledProcessError:
            pass
            
        return None
    
    def attach(self) -> bool:
        """既存のClaude Codeセッションに接続"""
        print(f"[Session {self.session_id}] Attaching to existing session in {self.work_dir}")
        
        # tmux paneを検索
        self.tmux_target = self._find_tmux_pane()
        if not self.tmux_target:
            # pane指定で検索（window 1のpane session_id）
            self.tmux_target = f"1.{self.session_id}"
            print(f"[Session {self.session_id}] Using default pane: {self.tmux_target}")
        else:
            print(f"[Session {self.session_id}] Found tmux pane: {self.tmux_target}")
        
        # JSONLファイルを検索
        self.jsonl_path = self._find_jsonl()
        if self.jsonl_path:
            print(f"[Session {self.session_id}] JSONL: {self.jsonl_path.name}")
        else:
            print(f"[Session {self.session_id}] Warning: JSONL not found")
        
        return True
    
    def send_command(self, command: str) -> bool:
        """tmux経由でコマンド送信"""
        if not self.tmux_target:
            print(f"[Session {self.session_id}] Not attached")
            return False
        
        try:
            # tmux send-keysでコマンド送信
            subprocess.run(
                ["tmux", "send-keys", "-t", self.tmux_target, command, "Enter"],
                check=True
            )
            print(f"[Session {self.session_id}] Sent via tmux: {command}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Session {self.session_id}] Send failed: {e}")
            return False
    
    def is_ready(self) -> bool:
        """セッションが準備完了か確認"""
        if not self.tmux_target:
            return False
            
        # tmux paneが存在するか確認
        try:
            subprocess.run(
                ["tmux", "list-panes", "-t", self.tmux_target],
                capture_output=True, check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_latest_entry(self) -> Optional[Dict[str, Any]]:
        """最新のJSONLエントリ取得"""
        if not self.jsonl_path or not self.jsonl_path.exists():
            # 再検索
            self.jsonl_path = self._find_jsonl()
            if not self.jsonl_path:
                return None
        
        try:
            with open(self.jsonl_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except:
            pass
        
        return None
    
    def get_output(self, lines: int = 10) -> str:
        """tmux paneの出力を取得"""
        if not self.tmux_target:
            return ""
            
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", self.tmux_target, "-p"],
                capture_output=True, text=True, check=True
            )
            lines_list = result.stdout.strip().split('\n')
            return '\n'.join(lines_list[-lines:])
        except subprocess.CalledProcessError:
            return ""


class SessionManager:
    """複数セッション管理（既存セッション接続版）"""
    
    def __init__(self):
        self.sessions: Dict[int, ClaudeSession] = {}
        self.base_dir = Path("/home/nixos/bin/src/poc/realtime-claudecode")
    
    def attach_session(self, session_id: int) -> ClaudeSession:
        """既存セッションに接続"""
        if session_id not in self.sessions:
            work_dir = self.base_dir / f"{session_id:02d}"
            
            session = ClaudeSession(session_id, str(work_dir))
            if session.attach():
                self.sessions[session_id] = session
            else:
                raise RuntimeError(f"Failed to attach session {session_id}")
        
        return self.sessions[session_id]
    
    def send_to(self, session_id: int, command: str) -> bool:
        """指定セッションにコマンド送信"""
        print(f"\n[Manager] Sending to session {session_id}")
        
        session = self.attach_session(session_id)
        
        # セッション準備確認
        if not session.is_ready():
            print(f"[Manager] Session {session_id} not ready")
            return False
        
        return session.send_command(command)
    
    def get_status(self) -> Dict[int, str]:
        """全セッションのステータス"""
        status = {}
        for sid, session in self.sessions.items():
            if session.is_ready():
                status[sid] = "attached"
            else:
                status[sid] = "not_attached"
        return status
    
    def show_outputs(self):
        """全セッションの最新出力を表示"""
        for sid, session in self.sessions.items():
            print(f"\n--- Session {sid} output ---")
            print(session.get_output(5))


# CLI使用例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m mod_attach attach <session_id>")
        print("  python -m mod_attach send <session_id> <command>")
        print("  python -m mod_attach status")
        print("  python -m mod_attach output")
        sys.exit(1)
    
    manager = SessionManager()
    action = sys.argv[1]
    
    if action == "attach":
        sid = int(sys.argv[2])
        session = manager.attach_session(sid)
        print(f"Attached to session {sid}")
        
    elif action == "send":
        sid = int(sys.argv[2])
        cmd = " ".join(sys.argv[3:])
        success = manager.send_to(sid, cmd)
        print(f"Send {'successful' if success else 'failed'}")
        
    elif action == "status":
        status = manager.get_status()
        print("Session status:")
        for sid, state in status.items():
            print(f"  Session {sid}: {state}")
            
    elif action == "output":
        manager.show_outputs()