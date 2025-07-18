#!/usr/bin/env python3
"""
VSS (Vector Similarity Search) LLM-first Entry Point
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from search.vss.kuzu.vss_service import VSSService


def show_readme():
    """Display README and usage guide"""
    readme = """
# VSS (Vector Similarity Search) Service

## 概要
要件テキストをベクトル化し、意味的に類似した要件を検索するサービスです。
JSON Schema契約に基づいて動作します。

## 主な機能
1. **要件のインデックス作成**: テキストを256次元ベクトルに変換してKuzuDBに保存
2. **類似検索**: クエリテキストに意味的に類似した要件を検索
3. **バッチ処理**: 複数の要件を一括でインデックス

## 使用例

### 要件のインデックス作成
```json
{
  "operation": "index",
  "documents": [
    {"id": "REQ001", "content": "ユーザー認証機能を実装する"},
    {"id": "REQ002", "content": "ログインシステムを構築する"},
    {"id": "REQ003", "content": "データベースを設計する"}
  ]
}
```

### 類似検索
```json
{
  "operation": "search",
  "query": "認証システム",
  "limit": 5,
  "threshold": 0.7
}
```

### バッチ検索
```json
{
  "operation": "batch_search",
  "queries": [
    {"query": "認証", "limit": 3},
    {"query": "データベース", "limit": 3}
  ]
}
```

## インタラクティブモード
引数なしで実行すると対話モードが開始されます。
自然言語で要求を入力してください。

例:
- "認証に関する要件を検索して"
- "REQ001からREQ003までの要件をインデックスに追加"
- "ログインに似た要件を5件表示"
"""
    print(readme)


def process_operation(operation: Dict[str, Any], service: VSSService) -> Dict[str, Any]:
    """Process a single operation"""
    op_type = operation.get("operation")
    
    if op_type == "index":
        documents = operation.get("documents", [])
        return service.index_documents(documents)
    
    elif op_type == "search":
        search_params = {
            "query": operation.get("query"),
            "limit": operation.get("limit", 10),
            "threshold": operation.get("threshold")
        }
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        return service.search(search_params)
    
    elif op_type == "batch_search":
        queries = operation.get("queries", [])
        results = []
        for query in queries:
            result = service.search(query)
            results.append(result)
        return {"status": "success", "results": results}
    
    else:
        return {"status": "error", "message": f"Unknown operation: {op_type}"}


def interactive_mode(service: VSSService):
    """Interactive mode for natural language queries"""
    print("\n対話モードを開始します。終了するには 'exit' と入力してください。\n")
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("終了します。")
                break
            
            # Natural language processing (simplified)
            if "検索" in user_input or "探" in user_input or "類似" in user_input:
                # Extract query terms
                query_terms = user_input.replace("検索", "").replace("して", "").strip()
                print(f"'{query_terms}' を検索します...")
                
                result = service.search({"query": query_terms, "limit": 5})
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
            elif "インデックス" in user_input or "追加" in user_input:
                print("追加する要件をJSON形式で入力してください:")
                json_input = input()
                try:
                    documents = json.loads(json_input)
                    if not isinstance(documents, list):
                        documents = [documents]
                    result = service.index_documents(documents)
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print("エラー: 無効なJSON形式です")
            
            else:
                print("理解できませんでした。'検索' または 'インデックス' を含む文で指示してください。")
                
        except KeyboardInterrupt:
            print("\n終了します。")
            break
        except Exception as e:
            print(f"エラーが発生しました: {e}")


def main():
    """Main entry point"""
    # Initialize service
    db_path = os.environ.get("VSS_DB_PATH", "./vss_kuzu_db")
    in_memory = os.environ.get("VSS_IN_MEMORY", "false").lower() == "true"
    
    try:
        service = VSSService(db_path=db_path, in_memory=in_memory)
    except Exception as e:
        print(f"サービスの初期化に失敗しました: {e}")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "run":
            # Process JSON from stdin
            try:
                data = json.load(sys.stdin)
                
                # Handle single operation or list of operations
                if isinstance(data, list):
                    results = []
                    for op in data:
                        result = process_operation(op, service)
                        results.append(result)
                    output = {"status": "success", "results": results}
                else:
                    output = process_operation(data, service)
                
                print(json.dumps(output, ensure_ascii=False, indent=2))
                
            except json.JSONDecodeError as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Invalid JSON: {e}"
                }, ensure_ascii=False))
                sys.exit(1)
                
        elif command == "test":
            # Run test scenarios
            print("テストモードは未実装です")
            sys.exit(1)
            
        else:
            print(f"不明なコマンド: {command}")
            print("使用方法: entry.py [run|test]")
            sys.exit(1)
    else:
        # Default: show README and enter interactive mode
        show_readme()
        interactive_mode(service)


if __name__ == "__main__":
    main()