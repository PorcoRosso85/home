"""Test connection.py with Result type error handling."""

import pytest
from pathlib import Path
import tempfile
import shutil
from architecture.db.connection import KuzuConnectionManager
from infrastructure.types.result import is_ok, is_err


def test_execute_ddl_file_returns_result():
    """execute_ddl_fileがResult型を返すこと"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        manager = KuzuConnectionManager(db_path)
        
        # ファイルが存在しない場合
        result = manager.execute_ddl_file(Path("nonexistent.cypher"))
        assert is_err(result)
        assert "not found" in result["error"]


def test_execute_ddl_file_success():
    """DDL実行が成功した場合、実行されたステートメント数を返すこと"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        manager = KuzuConnectionManager(db_path)
        
        # DDLファイルを作成
        ddl_file = Path(tmpdir) / "test.cypher"
        ddl_content = """
        CREATE NODE TABLE Person (name STRING, age INT64, PRIMARY KEY(name));
        CREATE NODE TABLE Project (id STRING, name STRING, PRIMARY KEY(id));
        """
        ddl_file.write_text(ddl_content)
        
        result = manager.execute_ddl_file(ddl_file)
        assert is_ok(result)
        assert result["value"] == 2  # 2つのステートメントが実行された


def test_execute_ddl_file_ignores_already_exists():
    """already existsエラーは無視されること"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        manager = KuzuConnectionManager(db_path)
        
        # DDLファイルを作成
        ddl_file = Path(tmpdir) / "test.cypher"
        ddl_content = "CREATE NODE TABLE Person (name STRING, PRIMARY KEY(name));"
        ddl_file.write_text(ddl_content)
        
        # 1回目の実行
        result1 = manager.execute_ddl_file(ddl_file)
        assert is_ok(result1)
        assert result1["value"] == 1
        
        # 2回目の実行（already existsエラーが発生するはず）
        result2 = manager.execute_ddl_file(ddl_file)
        assert is_ok(result2)
        assert result2["value"] == 1  # エラーが無視されて成功扱い


def test_execute_ddl_file_reports_other_errors():
    """already exists以外のエラーはErrとして返されること"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        manager = KuzuConnectionManager(db_path)
        
        # 不正なDDLファイルを作成
        ddl_file = Path(tmpdir) / "invalid.cypher"
        ddl_content = "INVALID SQL SYNTAX HERE;"
        ddl_file.write_text(ddl_content)
        
        result = manager.execute_ddl_file(ddl_file)
        assert is_err(result)
        assert "DDL execution failed" in result["error"]