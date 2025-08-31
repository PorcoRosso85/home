#!/usr/bin/env python3
"""
Transport Module Infrastructure Layer
pexpectのみでのセッション管理（1 dir : 1 session）
"""

import json
import glob
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from .variables import PATHS, TIMEOUTS, PTY_CONFIG, PROMPT_PATTERNS
except ImportError:
    from variables import PATHS, TIMEOUTS, PTY_CONFIG, PROMPT_PATTERNS

try:
    import pexpect
except ImportError:
    raise ImportError("pexpect is required for this module")

# === グローバルセッション管理 ===
# ディレクトリパス -> pexpectセッションのマッピング
_sessions: Dict[str, pexpect.spawn] = {}

# === プロセス検出 ===

def find_existing_claude_process(work_dir: Path) -> Optional[int]:
    """指定ディレクトリで動作中のClaude Codeプロセスを検出
    Returns:
        PID if found, None otherwise
    """
    try:
        # ps auxでプロセス一覧を取得
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )
        
        dir_str = str(work_dir.absolute())
        
        # Claude Codeプロセスを検索
        for line in result.stdout.split('\n'):
            # claude-shell.shまたはclaude関連プロセスを検索
            if 'claude' in line.lower() and dir_str in line:
                # コマンドライン引数にディレクトリが含まれているか確認
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                        # プロセスが生きているか確認
                        subprocess.run(["kill", "-0", str(pid)], 
                                     capture_output=True, check=True)
                        return pid
                    except (ValueError, subprocess.CalledProcessError):
                        continue
        return None
    except subprocess.CalledProcessError:
        return None

# === セッション操作 (list/create only) ===

def list_sessions() -> Dict[str, bool]:
    """アクティブなセッション一覧
    Returns:
        Dict[dir_path, is_alive]
    """
    global _sessions
    result = {}
    dead_keys = []
    
    for dir_path, session in _sessions.items():
        if session.isalive():
            result[dir_path] = True
        else:
            result[dir_path] = False
            dead_keys.append(dir_path)
    
    # 死んだセッションを削除
    for key in dead_keys:
        del _sessions[key]
    
    return result

def create_session(work_dir: Path) -> Optional[pexpect.spawn]:
    """新規セッション作成（1 dir : 1 session）"""
    global _sessions
    
    dir_str = str(work_dir.absolute())
    
    # 既存セッションがあれば返す
    if dir_str in _sessions and _sessions[dir_str].isalive():
        return _sessions[dir_str]
    
    # システムレベルで既存プロセスを検出
    existing_pid = find_existing_claude_process(work_dir)
    if existing_pid:
        # 既存プロセスが見つかった場合は新規作成しない
        print(f"Warning: Claude Code already running in {work_dir} (PID: {existing_pid})")
        return None
    
    claude_shell = PATHS["claude_shell"]
    
    try:
        session = pexpect.spawn(
            'bash',
            ['-c', f'{claude_shell} {work_dir}'],
            encoding=PTY_CONFIG["encoding"],
            timeout=TIMEOUTS["startup"],
            dimensions=PTY_CONFIG["dimensions"]
        )
        
        # 起動待機 - プロセスが生きているかの確認のみ
        import time
        time.sleep(2)  # 短い待機でプロセス起動を待つ
        if session.isalive():
            _sessions[dir_str] = session
            return session
        else:
            return None
    except (pexpect.TIMEOUT, pexpect.EOF, Exception):
        return None

def get_session(work_dir: Path) -> Optional[pexpect.spawn]:
    """既存セッション取得"""
    dir_str = str(work_dir.absolute())
    session = _sessions.get(dir_str)
    
    if session and session.isalive():
        return session
    return None

def send_command(work_dir: Path, command: str) -> bool:
    """セッションにコマンド送信"""
    session = get_session(work_dir)
    if not session:
        return False
    
    try:
        session.sendline(command)
        return True
    except:
        return False

# === ファイルシステム操作 ===

def find_jsonl_files(project_dir: str) -> List[Path]:
    """JSONLファイルを検索"""
    pattern = str(PATHS["claude_projects"] / project_dir / "*.jsonl")
    files = glob.glob(pattern)
    return [Path(f) for f in files]

def read_jsonl_last_entry(jsonl_path: Path) -> Optional[Dict[str, Any]]:
    """JSONLファイルの最終エントリ読み込み"""
    if not jsonl_path.exists():
        return None
    
    try:
        with open(jsonl_path, 'r') as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1].strip())
    except (IOError, json.JSONDecodeError):
        return None

def get_session_jsonl_path(work_dir: Path) -> Optional[Path]:
    """作業ディレクトリからJSONLパスを取得"""
    project_name = str(work_dir).replace('/', '-')
    project_path = PATHS["claude_projects"] / project_name
    
    if not project_path.exists():
        return None
    
    jsonl_files = list(project_path.glob("*.jsonl"))
    if jsonl_files:
        # 最新のJSONLファイルを返す
        return max(jsonl_files, key=lambda p: p.stat().st_mtime)
    return None

def ensure_directory(path: Path) -> bool:
    """ディレクトリ作成"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False

def get_current_datetime() -> datetime:
    """現在時刻取得"""
    return datetime.now()