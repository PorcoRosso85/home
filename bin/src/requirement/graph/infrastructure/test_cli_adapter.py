"""
Tests for CLI Adapter
"""
import tempfile
import os
import io
import sys
from .cli_adapter import create_cli
from .jsonl_repository import create_jsonl_repository
from ..application.decision_service import create_decision_service


def test_cli_add_command_valid_args_prints_success_message():
    """cli_add_正常引数_成功メッセージを出力する"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        cli = create_cli(temp_path, use_kuzu=False)
        
        # 標準出力をキャプチャ
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        # add コマンド実行
        cli(["add", "Test Decision", "This is a test"])
        
        output = buffer.getvalue()
        sys.stdout = old_stdout
        
        assert "Added decision:" in output
        assert "Title: Test Decision" in output
        assert "Status:" in output
        
    finally:
        os.unlink(temp_path)


def test_cli_search_command_matching_query_returns_results():
    """cli_search_マッチするクエリ_結果を返す"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name
    
    try:
        # リポジトリとサービスを直接セットアップ
        repo = create_jsonl_repository(temp_path)
        service = create_decision_service(repo)
        
        # テストデータを追加
        service["add_decision"]("Database Migration", "Move to KuzuDB")
        service["add_decision"]("API Design", "Create REST API")
        
        # CLIでsearch実行
        cli = create_cli(temp_path, use_kuzu=False)
        
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        cli(["search", "database"])
        
        output = buffer.getvalue()
        sys.stdout = old_stdout
        
        assert "Database Migration" in output
        assert "Move to KuzuDB" in output
        
    finally:
        os.unlink(temp_path)