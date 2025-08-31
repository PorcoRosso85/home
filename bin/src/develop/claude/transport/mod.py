#!/usr/bin/env python3
"""
Transport Module Public API
"""

try:
    from .application import SingleSessionController, MultiSessionOrchestrator
except ImportError:
    from application import SingleSessionController, MultiSessionOrchestrator

__all__ = [
    "SingleSessionController",
    "MultiSessionOrchestrator",
    "connect_to_session",
    "send_command",
    "discover_sessions"
]

# 便利関数

def connect_to_session(session_id: int) -> dict:
    """単一セッションに接続"""
    controller = SingleSessionController(session_id)
    return controller.attach_existing()

def send_command(session_id: int, command: str) -> dict:
    """単一セッションにコマンド送信"""
    controller = SingleSessionController(session_id)
    return controller.send_command(command)

def discover_sessions() -> dict:
    """アクティブなセッションを発見"""
    orchestrator = MultiSessionOrchestrator()
    return orchestrator.discover_active_sessions()