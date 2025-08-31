#!/usr/bin/env python3
"""
Transport Module Application Layer
ユースケースの実装（ドメインとインフラの統合）
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from .variables import PATHS, TIMEOUTS, TMUX_CONFIG
except ImportError:
    from variables import PATHS, TIMEOUTS, TMUX_CONFIG

try:
    from .domain import (
        format_project_path,
        parse_jsonl_entry,
        validate_session_id,
        format_command_result,
        determine_session_state,
        calculate_session_work_dir,
        calculate_tmux_pane_id,
        format_timestamp
    )
except ImportError:
    from domain import (
        format_project_path,
        parse_jsonl_entry,
        validate_session_id,
        format_command_result,
        determine_session_state,
        calculate_session_work_dir,
        calculate_tmux_pane_id,
        format_timestamp
    )

try:
    from .infrastructure import (
        send_to_tmux,
        check_tmux_pane,
        capture_tmux_output,
        spawn_claude_session,
        send_to_pexpect,
        find_jsonl_files,
        read_jsonl_last_entry,
        ensure_directory,
        find_claude_processes,
        get_current_datetime,
        PEXPECT_AVAILABLE
    )
except ImportError:
    from infrastructure import (
        send_to_tmux,
        check_tmux_pane,
        capture_tmux_output,
        spawn_claude_session,
        send_to_pexpect,
        find_jsonl_files,
        read_jsonl_last_entry,
        ensure_directory,
        find_claude_processes,
        get_current_datetime,
        PEXPECT_AVAILABLE
    )


class SingleSessionController:
    """単一セッションの制御"""
    
    def __init__(self, session_id: int):
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session ID: {session_id}")
        
        self.session_id = session_id
        self.work_dir = calculate_session_work_dir(PATHS["base_dir"], session_id)
        self.tmux_target = calculate_tmux_pane_id(TMUX_CONFIG["default_window"], session_id)
        self.project_dir = format_project_path(self.work_dir)
        self.pexpect_session = None
        self.jsonl_path = None
    
    def attach_existing(self) -> Dict[str, Any]:
        """既存セッションに接続"""
        # tmux pane確認
        has_tmux = check_tmux_pane(self.tmux_target)
        
        # JSONLファイル検索
        jsonl_files = find_jsonl_files(self.project_dir)
        if jsonl_files:
            self.jsonl_path = max(jsonl_files, key=lambda p: p.stat().st_ctime)
        
        # プロセス確認
        pids = find_claude_processes(self.work_dir)
        
        # 状態判定
        state = determine_session_state(
            has_process=bool(pids),
            has_jsonl=bool(self.jsonl_path),
            is_responsive=has_tmux
        )
        
        return {
            "session_id": self.session_id,
            "state": state,
            "tmux_target": self.tmux_target if has_tmux else None,
            "jsonl_path": str(self.jsonl_path) if self.jsonl_path else None,
            "process_count": len(pids)
        }
    
    def start_new(self) -> Dict[str, Any]:
        """新規セッション起動"""
        if not PEXPECT_AVAILABLE:
            return {
                "session_id": self.session_id,
                "success": False,
                "error": "pexpect not available"
            }
        
        # ディレクトリ作成
        ensure_directory(self.work_dir)
        
        # Claude起動
        self.pexpect_session = spawn_claude_session(
            PATHS["claude_shell"],
            self.work_dir
        )
        
        if not self.pexpect_session:
            return {
                "session_id": self.session_id,
                "success": False,
                "error": "Failed to spawn session"
            }
        
        # JSONL待機
        for _ in range(TIMEOUTS["jsonl_wait"]):
            jsonl_files = find_jsonl_files(self.project_dir)
            if jsonl_files:
                self.jsonl_path = max(jsonl_files, key=lambda p: p.stat().st_ctime)
                break
            time.sleep(1)
        
        return {
            "session_id": self.session_id,
            "success": True,
            "jsonl_path": str(self.jsonl_path) if self.jsonl_path else None
        }
    
    def send_command(self, command: str) -> Dict[str, Any]:
        """コマンド送信"""
        # tmux経由を優先
        if check_tmux_pane(self.tmux_target):
            error = send_to_tmux(self.tmux_target, command)
            success = error is None
        # pexpect経由
        elif self.pexpect_session:
            success = send_to_pexpect(self.pexpect_session, command)
            error = None if success else "pexpect send failed"
        else:
            success = False
            error = "No active session"
        
        result = format_command_result(
            self.session_id,
            command,
            success,
            error
        )
        result["timestamp"] = format_timestamp(get_current_datetime())
        return result
    
    def get_output(self, lines: int = 10) -> Optional[str]:
        """出力取得"""
        return capture_tmux_output(self.tmux_target, lines)
    
    def get_latest_jsonl_entry(self) -> Optional[Dict[str, Any]]:
        """最新JSONLエントリ取得"""
        if not self.jsonl_path:
            # 再検索
            jsonl_files = find_jsonl_files(self.project_dir)
            if jsonl_files:
                self.jsonl_path = max(jsonl_files, key=lambda p: p.stat().st_ctime)
        
        if self.jsonl_path:
            last_line = read_jsonl_last_entry(self.jsonl_path)
            if last_line:
                return parse_jsonl_entry(last_line)
        
        return None


class MultiSessionOrchestrator:
    """複数セッションの統合管理"""
    
    def __init__(self):
        self.controllers: Dict[int, SingleSessionController] = {}
    
    def get_controller(self, session_id: int) -> SingleSessionController:
        """コントローラー取得または作成"""
        if session_id not in self.controllers:
            self.controllers[session_id] = SingleSessionController(session_id)
        return self.controllers[session_id]
    
    def discover_active_sessions(self) -> Dict[int, Dict[str, Any]]:
        """アクティブなセッションを発見"""
        results = {}
        for i in range(1, 10):  # セッション1-9をチェック
            controller = self.get_controller(i)
            attach_result = controller.attach_existing()
            if attach_result["state"] != "not_started":
                results[i] = attach_result
        return results
    
    def broadcast_to_all(self, command: str) -> Dict[int, Dict[str, Any]]:
        """全コントローラーにコマンドをブロードキャスト"""
        results = {}
        for sid, controller in self.controllers.items():
            results[sid] = controller.send_command(command)
        return results