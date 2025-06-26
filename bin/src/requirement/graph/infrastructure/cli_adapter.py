"""
CLI Adapter - コマンドラインインターフェース
依存: domain, application
外部依存: argparse
"""
import argparse
import json
import os
from typing import Dict, List
from ..application.decision_service import create_decision_service
from .jsonl_repository import create_jsonl_repository


def create_cli(repository_path: str = None, use_kuzu: bool = True):
    """
    CLIを作成
    
    Args:
        repository_path: データベースパス
        use_kuzu: KuzuDBを使用するか（デフォルト: True）
    
    Returns:
        CLI実行関数
    """
    if use_kuzu:
        from .kuzu_repository import create_kuzu_repository
        if repository_path is None:
            repository_path = os.path.expanduser("~/.rgl/graph.db")
        repository = create_kuzu_repository(repository_path)
    else:
        if repository_path is None:
            repository_path = os.path.expanduser("~/.rgl/decisions.jsonl")
        repository = create_jsonl_repository(repository_path)
    
    service = create_decision_service(repository)
    
    def run_cli(args: List[str] = None):
        """CLI実行"""
        parser = argparse.ArgumentParser(
            description="RGL - Requirement Graph Logic",
            prog="rgl"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Commands")
        
        # add command
        add_parser = subparsers.add_parser("add", help="Add new decision")
        add_parser.add_argument("title", help="Decision title")
        add_parser.add_argument("description", help="Decision description")
        add_parser.add_argument("--tags", nargs="*", default=[], help="Tags")
        
        # find command
        find_parser = subparsers.add_parser("find", help="Find decision by ID")
        find_parser.add_argument("id", help="Decision ID")
        
        # search command
        search_parser = subparsers.add_parser("search", help="Search similar decisions")
        search_parser.add_argument("query", help="Search query")
        search_parser.add_argument("--threshold", type=float, default=0.5, help="Similarity threshold")
        search_parser.add_argument("--limit", type=int, default=10, help="Max results")
        
        # list command
        list_parser = subparsers.add_parser("list", help="List decisions")
        list_parser.add_argument("--tag", help="Filter by tag")
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        # Execute command
        if parsed_args.command == "add":
            result = service["add_decision"](
                title=parsed_args.title,
                description=parsed_args.description,
                tags=parsed_args.tags
            )
            
            if "type" in result:
                print(f"Error: {result['message']}")
                if "details" in result:
                    for detail in result["details"]:
                        print(f"  - {detail}")
            else:
                print(f"Added decision: {result['id']}")
                print(f"Title: {result['title']}")
                print(f"Status: {result['status']}")
                if result["tags"]:
                    print(f"Tags: {', '.join(result['tags'])}")
        
        elif parsed_args.command == "find":
            result = service["find_decision"](parsed_args.id)
            
            if "type" in result:
                print(f"Error: {result['message']}")
            else:
                print(f"ID: {result['id']}")
                print(f"Title: {result['title']}")
                print(f"Description: {result['description']}")
                print(f"Status: {result['status']}")
                if result["tags"]:
                    print(f"Tags: {', '.join(result['tags'])}")
        
        elif parsed_args.command == "search":
            results = service["search_similar"](
                query=parsed_args.query,
                threshold=parsed_args.threshold,
                limit=parsed_args.limit
            )
            
            if not results:
                print("No matching decisions found")
            else:
                print(f"Found {len(results)} matching decisions:")
                for i, decision in enumerate(results, 1):
                    print(f"\n{i}. {decision['id']}: {decision['title']}")
                    print(f"   {decision['description']}")
                    if decision["tags"]:
                        print(f"   Tags: {', '.join(decision['tags'])}")
        
        elif parsed_args.command == "list":
            if parsed_args.tag:
                results = service["list_by_tag"](parsed_args.tag)
                print(f"Decisions with tag '{parsed_args.tag}':")
            else:
                results = repository["find_all"]()
                print("All decisions:")
            
            if not results:
                print("No decisions found")
            else:
                for decision in results:
                    print(f"\n- {decision['id']}: {decision['title']}")
                    print(f"  Status: {decision['status']}")
                    if decision["tags"]:
                        print(f"  Tags: {', '.join(decision['tags'])}")
    
    return run_cli


# Test cases
def test_cli_add_command_valid_args_prints_success_message():
    """cli_add_正常引数_成功メッセージを出力する"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        cli = create_cli(temp_path)
        
        # 標準出力をキャプチャ
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        # add コマンド実行
        cli(["add", "Test Decision", "This is a test", "--tags", "test", "cli"])
        
        output = buffer.getvalue()
        sys.stdout = old_stdout
        
        assert "Added decision:" in output
        assert "Title: Test Decision" in output
        assert "Tags: test, cli" in output
        
    finally:
        os.unlink(temp_path)


def test_cli_search_command_matching_query_returns_results():
    """cli_search_マッチするクエリ_結果を返す"""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        # リポジトリとサービスを直接セットアップ
        repo = create_jsonl_repository(temp_path)
        service = create_decision_service(repo)
        
        # テストデータを追加
        service["add_decision"]("Database Migration", "Move to KuzuDB", ["db"])
        service["add_decision"]("API Design", "Create REST API", ["api"])
        
        # CLIでsearch実行
        cli = create_cli(temp_path)
        
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        cli(["search", "database"])
        
        output = buffer.getvalue()
        sys.stdout = old_stdout
        
        assert "Database Migration" in output
        assert "Move to KuzuDB" in output
        
    finally:
        os.unlink(temp_path)
