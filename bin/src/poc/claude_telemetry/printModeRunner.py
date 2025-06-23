"""
Print Mode Runner

責務: --printオプションを使った堅牢なクエリ実行
- stream-json出力の確実な取得
- エラーハンドリング
- クエリ情報の抽出
"""

import subprocess
import json
import time
from typing import Dict, Any, List, Union, Optional
import sys


def run_with_print_mode(
    prompt: str,
    verbose: bool = True,
    timeout: int = 60
) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    --printモードでクエリを実行
    
    Args:
        prompt: 実行するプロンプト
        verbose: 詳細出力
        timeout: タイムアウト（秒）
        
    Returns:
        成功: {"session_id": str, "events": List, "result": Any}
        失敗: {"error": str}
    """
    cmd = [
        "claude",
        "--dangerously-skip-permissions",
        "--print",
        prompt,
        "--output-format", "stream-json"
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    events = []
    session_id = None
    result = None
    errors = []
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # stream-json出力を1行ずつ読む
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                process.kill()
                return {"error": f"Timeout after {timeout} seconds"}
            
            line = process.stdout.readline()
            if not line:
                # 出力が終了したかチェック
                if process.poll() is not None:
                    break
                continue
            
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                events.append(data)
                
                # セッションID抽出
                if data.get("type") == "system" and data.get("subtype") == "init":
                    session_id = data.get("session_id")
                
                # 結果抽出
                if data.get("type") == "result":
                    result = data
                    
            except json.JSONDecodeError as e:
                errors.append(f"JSON parse error: {str(e)} - line: {line}")
        
        # プロセス終了待機
        exit_code = process.wait()
        
        # エラー出力確認
        stderr = process.stderr.read()
        if stderr:
            errors.append(f"stderr: {stderr}")
        
        if exit_code != 0:
            return {"error": f"Process exited with code {exit_code}", "stderr": stderr}
        
        return {
            "session_id": session_id,
            "events": events,
            "result": result,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        return {"error": f"Failed to run command: {str(e)}"}


def extract_tool_usage(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    イベントからツール使用を抽出
    
    Args:
        events: stream-jsonイベントリスト
        
    Returns:
        ツール使用情報のリスト
    """
    tools = []
    
    for event in events:
        if event.get("type") == "assistant":
            message = event.get("message", {})
            content = message.get("content", [])
            
            for item in content:
                if item.get("type") == "tool_use":
                    tools.append({
                        "tool": item.get("name"),
                        "id": item.get("id"),
                        "input": item.get("input", {}),
                        "timestamp": time.time()
                    })
    
    return tools


def extract_file_operations(tools: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    ツール使用からファイル操作を抽出
    
    Args:
        tools: ツール使用情報リスト
        
    Returns:
        ファイル操作の分類
    """
    operations = {
        "created": [],
        "read": [],
        "edited": [],
        "bash_commands": []
    }
    
    for tool in tools:
        tool_name = tool.get("tool", "").lower()
        tool_input = tool.get("input", {})
        
        if tool_name == "write":
            file_path = tool_input.get("file_path")
            if file_path:
                operations["created"].append(file_path)
                
        elif tool_name == "read":
            file_path = tool_input.get("file_path")
            if file_path:
                operations["read"].append(file_path)
                
        elif tool_name in ["edit", "multiedit"]:
            file_path = tool_input.get("file_path")
            if file_path:
                operations["edited"].append(file_path)
                
        elif tool_name == "bash":
            command = tool_input.get("command")
            if command:
                operations["bash_commands"].append(command)
    
    return operations


# 堅牢性テスト関数
def test_file_creation():
    """ファイル作成タスクのテスト"""
    prompt = """Create a directory called poc_test_output, then create two Python files:
    1. poc_test_output/calculator.py with add(a, b) and multiply(a, b) functions
    2. poc_test_output/formatter.py with format_currency(amount) function that formats numbers as currency"""
    
    print("=== Testing file creation task ===")
    result = run_with_print_mode(prompt)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return False
    
    print(f"Session ID: {result['session_id']}")
    
    # ツール使用を抽出
    tools = extract_tool_usage(result["events"])
    print(f"\nTools used: {len(tools)}")
    
    # ファイル操作を抽出
    file_ops = extract_file_operations(tools)
    
    print("\nFile operations:")
    for op_type, files in file_ops.items():
        if files:
            print(f"  {op_type}:")
            for f in files:
                print(f"    - {f}")
    
    # 結果確認
    if result.get("result"):
        print(f"\nResult: {result['result'].get('subtype', 'unknown')}")
        
    return True


def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== Testing error handling ===")
    
    # 無効なプロンプト（非常に長い）でタイムアウトテスト
    result = run_with_print_mode("x" * 10000, timeout=5)
    
    if "error" in result:
        print(f"Expected error caught: {result['error'][:50]}...")
        return True
    
    return False


def test_bash_commands():
    """Bashコマンド実行のテスト"""
    prompt = "List files in current directory and show current date using bash commands"
    
    print("\n=== Testing bash command execution ===")
    result = run_with_print_mode(prompt)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return False
    
    tools = extract_tool_usage(result["events"])
    file_ops = extract_file_operations(tools)
    
    print("Bash commands executed:")
    for cmd in file_ops["bash_commands"]:
        print(f"  - {cmd}")
    
    return len(file_ops["bash_commands"]) > 0


if __name__ == "__main__":
    print("Starting robust print mode tests...\n")
    
    # テスト1: ファイル作成
    test1 = test_file_creation()
    print(f"\n✓ File creation test: {'PASSED' if test1 else 'FAILED'}")
    
    # テスト2: エラーハンドリング
    test2 = test_error_handling()
    print(f"✓ Error handling test: {'PASSED' if test2 else 'FAILED'}")
    
    # テスト3: Bashコマンド
    test3 = test_bash_commands()
    print(f"✓ Bash command test: {'PASSED' if test3 else 'FAILED'}")
    
    print(f"\nAll tests {'PASSED' if all([test1, test2, test3]) else 'FAILED'}!")