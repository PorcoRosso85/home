#!/usr/bin/env python3
"""
Transport Module CLI - LLM-first JSON Interface
"""

import json
import sys
try:
    from .application import SingleSessionController, MultiSessionOrchestrator
except ImportError:
    from application import SingleSessionController, MultiSessionOrchestrator

def process_attach_action(params: dict) -> dict:
    """接続アクション処理"""
    session_id = params.get("session_id", 1)
    controller = SingleSessionController(session_id)
    return controller.attach_existing()

def process_send_action(params: dict) -> dict:
    """送信アクション処理"""
    session_id = params.get("session_id", 1)
    command = params.get("command", "pwd")
    controller = SingleSessionController(session_id)
    return controller.send_command(command)

def process_discover_action(params: dict) -> dict:
    """発見アクション処理"""
    orchestrator = MultiSessionOrchestrator()
    return orchestrator.discover_active_sessions()

def process_broadcast_action(params: dict) -> dict:
    """ブロードキャストアクション処理"""
    command = params.get("command", "pwd")
    orchestrator = MultiSessionOrchestrator()
    orchestrator.discover_active_sessions()
    return orchestrator.broadcast_to_all(command)

def main():
    """メインエントリーポイント"""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        output = {"success": False, "error": f"Invalid JSON: {e}"}
        print(json.dumps(output))
        sys.exit(1)
    
    action = input_data.get("action", "discover")
    
    action_handlers = {
        "attach": process_attach_action,
        "send": process_send_action,
        "discover": process_discover_action,
        "broadcast": process_broadcast_action
    }
    
    handler = action_handlers.get(action)
    if not handler:
        result = {"success": False, "error": f"Unknown action: {action}"}
    else:
        try:
            result = handler(input_data)
            result["success"] = result.get("error") is None
        except Exception as e:
            result = {"success": False, "error": str(e)}
    
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("success", False) else 1)

if __name__ == "__main__":
    main()