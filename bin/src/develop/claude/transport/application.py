#!/usr/bin/env python3
"""
Transport Module Application Layer
ユースケースの実装（ドメインとインフラの統合）
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from .variables import PATHS, TIMEOUTS
except ImportError:
    from variables import PATHS, TIMEOUTS

try:
    from .domain import (
        format_project_path,
        parse_jsonl_entry,
        validate_session_id,
        format_command_result,
        determine_session_state,
        calculate_session_work_dir,
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
        format_timestamp
    )

try:
    from .infrastructure import (
        list_sessions,
        create_session,
        get_session,
        send_command,
        find_jsonl_files,
        read_jsonl_last_entry,
        get_session_jsonl_path,
        ensure_directory,
        get_current_datetime,
    )
except ImportError:
    from infrastructure import (
        list_sessions,
        create_session,
        get_session,
        send_command,
        find_jsonl_files,
        read_jsonl_last_entry,
        get_session_jsonl_path,
        ensure_directory,
        get_current_datetime,
    )

class SingleSessionController:
    """単一セッションの管理"""
    
    def __init__(self, session_id: int):
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session_id: {session_id}")
        
        self.session_id = session_id
        self.work_dir = calculate_session_work_dir(PATHS["base_dir"], session_id)
    
    def start_new_session(self) -> Dict[str, Any]:
        """新規セッション開始"""
        # ディレクトリ確保
        if not ensure_directory(self.work_dir):
            return {
                "session_id": self.session_id,
                "success": False,
                "error": "Failed to create directory",
                "timestamp": format_timestamp(get_current_datetime())
            }
        
        # セッション作成（既存があればそれを返す）
        session = create_session(self.work_dir)
        
        if session:
            return {
                "session_id": self.session_id,
                "work_dir": str(self.work_dir),
                "success": True,
                "error": None,
                "timestamp": format_timestamp(get_current_datetime())
            }
        else:
            return {
                "session_id": self.session_id,
                "success": False,
                "error": "Failed to create session",
                "timestamp": format_timestamp(get_current_datetime())
            }
    
    def attach_existing(self) -> Dict[str, Any]:
        """既存セッションへのアタッチ"""
        # セッション取得または作成
        session = get_session(self.work_dir)
        if not session:
            # なければ作成
            session = create_session(self.work_dir)
        
        if session:
            return {
                "session_id": self.session_id,
                "work_dir": str(self.work_dir),
                "success": True,
                "attached": True,
                "timestamp": format_timestamp(get_current_datetime())
            }
        else:
            return {
                "session_id": self.session_id,
                "success": False,
                "error": "Failed to attach to session",
                "timestamp": format_timestamp(get_current_datetime())
            }
    
    def send_command(self, command: str) -> Dict[str, Any]:
        """コマンド送信"""
        success = send_command(self.work_dir, command)
        
        return format_command_result(
            self.session_id,
            command,
            success,
            None if success else "Failed to send command"
        ) | {"timestamp": format_timestamp(get_current_datetime())}
    
    def get_status(self) -> Dict[str, Any]:
        """セッション状態取得"""
        session = get_session(self.work_dir)
        has_session = session is not None
        
        jsonl_path = get_session_jsonl_path(self.work_dir)
        has_jsonl = jsonl_path is not None
        
        state = determine_session_state(
            has_process=has_session,
            has_jsonl=has_jsonl,
            is_responsive=has_session  # セッションがあれば応答可能とみなす
        )
        
        return {
            "session_id": self.session_id,
            "work_dir": str(self.work_dir),
            "state": state,
            "has_session": has_session,
            "has_jsonl": has_jsonl,
            "timestamp": format_timestamp(get_current_datetime())
        }

class MultiSessionOrchestrator:
    """複数セッションの管理"""
    
    def __init__(self):
        self.base_dir = PATHS["base_dir"]
    
    def discover_active_sessions(self) -> Dict[str, Any]:
        """アクティブセッション発見"""
        sessions = list_sessions()
        
        # session_idにマッピング
        result = {}
        for dir_path, is_alive in sessions.items():
            # ディレクトリ名からsession_id抽出を試みる
            try:
                dir_name = Path(dir_path).name
                if dir_name.isdigit():
                    session_id = int(dir_name)
                    result[session_id] = {
                        "work_dir": dir_path,
                        "alive": is_alive,
                        "state": "ready" if is_alive else "dead"
                    }
            except (ValueError, AttributeError):
                # 数値でないディレクトリはスキップ
                pass
        
        return {
            "sessions": result,
            "count": len(result),
            "timestamp": format_timestamp(get_current_datetime())
        }
    
    def start_multiple_sessions(self, session_ids: List[int]) -> Dict[str, Any]:
        """複数セッション起動"""
        results = {}
        
        for session_id in session_ids:
            if validate_session_id(session_id):
                controller = SingleSessionController(session_id)
                results[session_id] = controller.start_new_session()
        
        return {
            "results": results,
            "success": all(r["success"] for r in results.values()),
            "timestamp": format_timestamp(get_current_datetime())
        }
    
    def broadcast_to_all(self, command: str) -> Dict[str, Any]:
        """全セッションへブロードキャスト"""
        sessions = list_sessions()
        results = {}
        
        for dir_path in sessions.keys():
            try:
                dir_name = Path(dir_path).name
                if dir_name.isdigit():
                    session_id = int(dir_name)
                    controller = SingleSessionController(session_id)
                    results[session_id] = controller.send_command(command)
            except (ValueError, AttributeError):
                pass
        
        return results | {
            "success": True,
            "timestamp": format_timestamp(get_current_datetime())
        }