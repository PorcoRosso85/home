#!/usr/bin/env python3
"""
Claude Code Transport Module (Fixed Version)
pexpectを使用してPTY経由でClaude Codeを制御
"""

import os
import time
import json
import glob
from pathlib import Path
from typing import Optional, Dict, Any

# pexpectのインポート
try:
    import pexpect
except ImportError:
    print("Error: pexpect not installed")
    print("Run: nix-shell -p python3Packages.pexpect")
    exit(1)


class ClaudeSession:
    """単一のClaude Codeセッション管理（pexpect版）"""
    
    def __init__(self, session_id: int, work_dir: str):
        self.session_id = session_id
        self.work_dir = Path(work_dir).resolve()
        self.jsonl_path: Optional[Path] = None
        self.session: Optional[pexpect.spawn] = None  # subprocess.Popenではなくpexpect
        self.claude_shell = "/home/nixos/bin/src/develop/claude/ui/claude-shell.sh"
        
    def _get_project_dir_name(self) -> str:
        """プロジェクトパスをClaude形式に変換"""
        path_str = str(self.work_dir)
        return path_str.replace('/', '-')
    
    def _find_jsonl(self) -> Optional[Path]:
        """セッションのJSONLファイルを特定"""
        project_name = self._get_project_dir_name()
        pattern = f"{Path.home()}/.claude/projects/{project_name}/*.jsonl"
        
        # 起動前の既存ファイル取得
        existing_files = set(glob.glob(pattern))
        
        # 新規ファイル検出のためポーリング（最大30秒）
        for _ in range(30):
            current_files = set(glob.glob(pattern))
            new_files = current_files - existing_files
            
            if new_files:
                # 最新のファイルを返す
                newest = max(new_files, key=os.path.getctime)
                return Path(newest)
            
            time.sleep(1)
        
        return None
    
    def start(self) -> bool:
        """Claude CodeをPTY経由で起動"""
        print(f"[Session {self.session_id}] Starting in {self.work_dir}")
        
        try:
            # pexpect.spawnでPTY作成
            self.session = pexpect.spawn(
                'bash', 
                ['-c', f'{self.claude_shell} {self.work_dir}'],
                encoding='utf-8',
                timeout=30,
                dimensions=(24, 80)
            )
            
            # Claude起動を待機
            try:
                # Welcomeメッセージまたはプロンプトを待つ
                index = self.session.expect(
                    ["Welcome", r">\s*│", "Starting Claude"],
                    timeout=30
                )
                print(f"[Session {self.session_id}] Claude started (pattern {index})")
            except pexpect.TIMEOUT:
                print(f"[Session {self.session_id}] Timeout waiting for startup, continuing...")
            
            # JSONL作成待機
            print(f"[Session {self.session_id}] Waiting for JSONL...")
            self.jsonl_path = self._find_jsonl()
            
            if self.jsonl_path:
                print(f"[Session {self.session_id}] JSONL: {self.jsonl_path.name}")
            else:
                print(f"[Session {self.session_id}] Warning: JSONL not detected yet")
            
            return True
                
        except Exception as e:
            print(f"[Session {self.session_id}] Start failed: {e}")
            return False
    
    def send_command(self, command: str) -> bool:
        """コマンド送信"""
        if not self.session:
            print(f"[Session {self.session_id}] Not started")
            return False
        
        try:
            self.session.sendline(command)
            print(f"[Session {self.session_id}] Sent: {command}")
            return True
        except Exception as e:
            print(f"[Session {self.session_id}] Send failed: {e}")
            return False
    
    def is_ready(self) -> bool:
        """セッションが準備完了か確認"""
        if not self.session:
            return False
        return self.session.isalive()
    
    def get_latest_entry(self) -> Optional[Dict[str, Any]]:
        """最新のJSONLエントリ取得"""
        if not self.jsonl_path or not self.jsonl_path.exists():
            return None
        
        try:
            with open(self.jsonl_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    return json.loads(lines[-1])
        except:
            pass
        
        return None
    
    def close(self):
        """セッション終了"""
        if self.session:
            self.session.close()
            print(f"[Session {self.session_id}] Closed")


class SessionManager:
    """複数セッション管理"""
    
    def __init__(self):
        self.sessions: Dict[int, ClaudeSession] = {}
        self.base_dir = Path("/home/nixos/bin/src/poc/realtime-claudecode")
    
    def get_or_create_session(self, session_id: int) -> ClaudeSession:
        """セッション取得または作成"""
        if session_id not in self.sessions:
            work_dir = self.base_dir / f"{session_id:02d}"
            work_dir.mkdir(parents=True, exist_ok=True)
            
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
        
        # セッション準備待機
        if not session.is_ready():
            print(f"[Manager] Session {session_id} not ready, waiting...")
            time.sleep(2)
        
        return session.send_command(command)
    
    def get_status(self) -> Dict[int, str]:
        """全セッションのステータス"""
        status = {}
        for sid, session in self.sessions.items():
            if session.is_ready():
                status[sid] = "ready"
            else:
                status[sid] = "not_ready"
        return status
    
    def close_all(self):
        """全セッション終了"""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()


# CLI使用例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m transport start <session_id>")
        print("  python -m transport send <session_id> <command>")
        print("  python -m transport status")
        sys.exit(1)
    
    manager = SessionManager()
    action = sys.argv[1]
    
    if action == "start":
        sid = int(sys.argv[2])
        session = manager.get_or_create_session(sid)
        print(f"Session {sid} started")
        # 維持するため入力待機
        input("Press Enter to close...")
        session.close()
        
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