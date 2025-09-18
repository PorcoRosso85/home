#!/usr/bin/env python3
"""
LocationURI Dataset Management CLI

LLM-firstな対話的インターフェース
"""
import json
import sys
from typing import Dict, Any, Optional


def parse_json_input(prompt: str = "Input JSON: ") -> Optional[Dict[str, Any]]:
    """JSON入力をパースする"""
    try:
        user_input = input(prompt).strip()
        if not user_input:
            return None
        return json.loads(user_input)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return None
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)


def show_help():
    """ヘルプメッセージを表示"""
    help_text = """
LocationURI Dataset Management System

This system manages LocationURI datasets with the following constraints:
- Uses requirement/graph schema definitions
- Leverages persistence/kuzu_py for database operations  
- Restricts node creation to pre-defined dataset only

Available Commands (provide as JSON):

1. Initialize Repository:
   {"action": "init", "db_path": ":memory:"}  # or provide file path

2. List Allowed Dataset:
   {"action": "list_dataset"}

3. Create LocationURI Node:
   {"action": "create_node", "uri": "req://system"}

4. List Created Nodes:
   {"action": "list_nodes"}

5. Validate URI:
   {"action": "validate", "uri": "req://custom/path"}

6. Exit:
   {"action": "exit"}

Example Usage:
  Input JSON: {"action": "init"}
  Input JSON: {"action": "create_node", "uri": "req://architecture"}
"""
    print(help_text)


def main():
    """メインエントリーポイント"""
    print("LocationURI Dataset Management CLI")
    print("Type 'help' or provide JSON commands")
    print("-" * 40)
    
    # リポジトリ状態
    repo = None
    
    while True:
        # 入力取得
        user_input = input("\nInput (JSON or 'help'): ").strip()
        
        if user_input.lower() == "help":
            show_help()
            continue
            
        if not user_input:
            continue
            
        # JSON解析
        try:
            command = json.loads(user_input)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            continue
        
        # アクション取得
        action = command.get("action")
        if not action:
            print("Error: 'action' field is required")
            continue
        
        # アクション処理
        if action == "exit":
            print("Exiting...")
            break
            
        elif action == "init":
            from mod import create_restricted_repository
            
            db_path = command.get("db_path", ":memory:")
            print(f"Initializing repository with db_path: {db_path}")
            
            result = create_restricted_repository(db_path)
            if "type" in result and "Error" in result["type"]:
                print(f"Error: {result}")
            else:
                repo = result
                print("Repository initialized successfully")
                print(f"Allowed dataset size: {len(repo['get_allowed_dataset']()['uris'])}")
        
        elif action == "list_dataset":
            if not repo:
                print("Error: Repository not initialized. Use {'action': 'init'} first")
                continue
                
            result = repo["get_allowed_dataset"]()
            print(json.dumps(result, indent=2))
        
        elif action == "create_node":
            if not repo:
                print("Error: Repository not initialized. Use {'action': 'init'} first")
                continue
                
            uri = command.get("uri")
            if not uri:
                print("Error: 'uri' field is required")
                continue
                
            result = repo["create_locationuri_node"](uri)
            print(json.dumps(result, indent=2))
        
        elif action == "list_nodes":
            if not repo:
                print("Error: Repository not initialized. Use {'action': 'init'} first")
                continue
                
            result = repo["list_locationuris"]()
            print(json.dumps(result, indent=2))
        
        elif action == "validate":
            uri = command.get("uri")
            if not uri:
                print("Error: 'uri' field is required")
                continue
            
            if repo:
                result = repo["validate_locationuri"](uri)
            else:
                from mod import validate_locationuri
                result = validate_locationuri(uri)
                
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown action: {action}")
            print("Use 'help' to see available actions")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)