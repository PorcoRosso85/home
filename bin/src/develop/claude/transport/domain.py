#!/usr/bin/env python3
"""
Transport Module Domain Layer
ピュア関数によるビジネスロジック
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

def format_project_path(work_dir: Path) -> str:
    """
    プロジェクトパスをClaude形式に変換（ピュア関数）
    
    /home/nixos/bin/src/poc/realtime-claudecode/02
    → -home-nixos-bin-src-poc-realtime-claudecode-02
    """
    return str(work_dir).replace('/', '-')

def parse_jsonl_entry(line: str) -> Optional[Dict[str, Any]]:
    """JSONLエントリをパース（ピュア関数）"""
    try:
        return json.loads(line.strip())
    except (json.JSONDecodeError, AttributeError):
        return None

def validate_session_id(session_id: int) -> bool:
    """セッションIDの妥当性を検証（ピュア関数）"""
    return 0 < session_id <= 99

def format_command_result(
    session_id: int,
    command: str,
    success: bool,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """コマンド実行結果を構造化（ピュア関数）"""
    return {
        "session_id": session_id,
        "command": command,
        "success": success,
        "error": error,
        "timestamp": None  # インフラ層で設定
    }

def determine_session_state(
    has_process: bool,
    has_jsonl: bool,
    is_responsive: bool
) -> str:
    """セッション状態を判定（ピュア関数）"""
    if not has_process:
        return "not_started"
    elif not has_jsonl:
        return "starting"
    elif not is_responsive:
        return "busy"
    else:
        return "ready"

def calculate_session_work_dir(base_dir: Path, session_id: int) -> Path:
    """セッションIDから作業ディレクトリパスを計算（ピュア関数）"""
    return base_dir / f"{session_id:02d}"

def calculate_tmux_pane_id(window: str, session_id: int) -> str:
    """セッションIDからtmux pane IDを計算（ピュア関数）"""
    return f"{window}.{session_id}"

def format_timestamp(dt: datetime) -> str:
    """datetimeオブジェクトをISO形式文字列に変換（ピュア関数）"""
    return dt.isoformat()