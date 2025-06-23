#!/usr/bin/env python3
"""
Claude Telemetry POC メインエントリーポイント

責務: claude --print --output-format stream-jsonからJSONLを取得してクエリを抽出
"""

import subprocess
import json
import sys
from typing import List, Dict, Any


def extract_queries(prompt: str) -> Dict[str, Any]:
    """Claudeを実行してクエリを抽出"""
    
    cmd = [
        "claude",
        "--dangerously-skip-permissions", 
        "--print",
        prompt,
        "--output-format", "stream-json",
        "--verbose"
    ]
    
    # 実行
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 結果を解析
    queries = []
    outputs = []
    session_id = None
    
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
            
        try:
            data = json.loads(line)
            
            # セッションID
            if data.get("type") == "system" and data.get("subtype") == "init":
                session_id = data.get("session_id")
            
            # ツール使用
            elif data.get("type") == "assistant":
                message = data.get("message", {})
                for item in message.get("content", []):
                    if item.get("type") == "tool_use":
                        queries.append({
                            "tool": item.get("name"),
                            "input": item.get("input", {})
                        })
                    elif item.get("type") == "text":
                        outputs.append(item.get("text", ""))
            
            # 最終結果
            elif data.get("type") == "result":
                if data.get("result"):
                    outputs.append(f"[RESULT] {data['result']}")
                    
        except json.JSONDecodeError:
            pass
    
    return {
        "session_id": session_id,
        "queries": queries,
        "outputs": outputs,
        "exit_code": result.returncode,
        "stderr": result.stderr
    }


def main():
    """メイン実行"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <prompt>")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    print(f"Executing: {prompt}\n")
    
    result = extract_queries(prompt)
    
    print(f"Session ID: {result['session_id']}")
    print(f"\n=== QUERIES ({len(result['queries'])}) ===")
    
    for i, query in enumerate(result['queries'], 1):
        print(f"\n#{i} {query['tool']}")
        for key, value in query['input'].items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")
    
    print(f"\n=== OUTPUTS ===")
    for output in result['outputs']:
        if len(output) > 200:
            print(f"{output[:200]}...")
        else:
            print(output)
    
    if result['stderr']:
        print(f"\n=== ERRORS ===\n{result['stderr']}")


if __name__ == "__main__":
    main()