#!/usr/bin/env python3
"""
Transport Module Infrastructure Layer
外部システムとの接続（副作用を含む）
"""

import subprocess
import glob
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from .variables import PATHS, TIMEOUTS, PTY_CONFIG, PROMPT_PATTERNS
except ImportError:
    from variables import PATHS, TIMEOUTS, PTY_CONFIG, PROMPT_PATTERNS

# pexpectインポート（オプショナル）
try:
    import pexpect
    PEXPECT_AVAILABLE = True
except ImportError:
    PEXPECT_AVAILABLE = False

# === tmux操作 ===

def send_to_tmux(target: str, command: str) -> Optional[str]:
    """tmux paneにコマンド送信（副作用）"""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", target, command, "C-m"],
            check=True,
            capture_output=True,
            text=True
        )
        return None
    except subprocess.CalledProcessError as e:
        return str(e)

def check_tmux_pane(target: str) -> bool:
    """tmux paneの存在確認（副作用）"""
    try:
        subprocess.run(
            ["tmux", "list-panes", "-t", target],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def capture_tmux_output(target: str, lines: int = 10) -> Optional[str]:
    """tmux paneの出力取得（副作用）"""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", target, "-p"],
            capture_output=True,
            text=True,
            check=True
        )
        output_lines = result.stdout.strip().split('\n')
        return '\n'.join(output_lines[-lines:])
    except subprocess.CalledProcessError:
        return None

# === pexpect操作 ===

def spawn_claude_session(
    claude_shell: Path,
    work_dir: Path
) -> Optional['pexpect.spawn']:
    """Claude Codeセッションを起動（副作用）"""
    if not PEXPECT_AVAILABLE:
        return None
    
    try:
        session = pexpect.spawn(
            'bash',
            ['-c', f'{claude_shell} {work_dir}'],
            encoding=PTY_CONFIG["encoding"],
            timeout=TIMEOUTS["startup"],
            dimensions=PTY_CONFIG["dimensions"]
        )
        
        # 起動待機
        session.expect(PROMPT_PATTERNS, timeout=TIMEOUTS["startup"])
        return session
    except (pexpect.TIMEOUT, pexpect.EOF):
        return None

def send_to_pexpect(session: 'pexpect.spawn', command: str) -> bool:
    """pexpectセッションにコマンド送信（副作用）"""
    if not PEXPECT_AVAILABLE or not session:
        return False
    
    try:
        session.sendline(command)
        return True
    except:
        return False

# === ファイルシステム操作 ===

def find_jsonl_files(project_dir: str) -> List[Path]:
    """JSONLファイルを検索（副作用）"""
    pattern = str(PATHS["claude_projects"] / project_dir / "*.jsonl")
    files = glob.glob(pattern)
    return [Path(f) for f in files]

def read_jsonl_last_entry(jsonl_path: Path) -> Optional[str]:
    """JSONLファイルの最終エントリ読み込み（副作用）"""
    if not jsonl_path.exists():
        return None
    
    try:
        with open(jsonl_path, 'r') as f:
            lines = f.readlines()
            if lines:
                return lines[-1]
    except IOError:
        return None

def ensure_directory(path: Path) -> bool:
    """ディレクトリ作成（副作用）"""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False

# === プロセス管理 ===

def find_claude_processes(work_dir: Path) -> List[int]:
    """Claude Codeプロセスを検索（副作用）"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )
        
        pids = []
        for line in result.stdout.split('\n'):
            if "claude" in line and str(work_dir) in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pids.append(int(parts[1]))
                    except ValueError:
                        pass
        return pids
    except subprocess.CalledProcessError:
        return []

def get_current_datetime() -> datetime:
    """現在時刻取得（副作用）"""
    return datetime.now()