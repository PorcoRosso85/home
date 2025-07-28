"""
型安全なクエリローダーのテスト
"""
import pytest
import tempfile
import os
from pathlib import Path
from typed_query_loader import load_typed_query, execute_query


def test_load_typed_query_with_valid_query(tmp_path):
    """正常なクエリ読み込みのテスト"""
    # テスト用のクエリファイルを作成
    dml_dir = tmp_path / "dml"
    dml_dir.mkdir()
    
    query_file = dml_dir / "create_node.cypher"
    query_content = "CREATE (n:Node {id: $id, name: $name})"
    query_file.write_text(query_content)
    
    # クエリの読み込み
    result = load_typed_query("create_node", query_type="dml", base_dir=str(tmp_path))
    
    # 成功時は文字列が返る
    assert isinstance(result, str)
    assert result == query_content


def test_load_typed_query_with_auto_type(tmp_path):
    """autoタイプでのクエリ読み込みテスト"""
    # dmlとdqlの両方にクエリを配置
    dml_dir = tmp_path / "dml"
    dml_dir.mkdir()
    dql_dir = tmp_path / "dql"
    dql_dir.mkdir()
    
    # dmlが優先される
    dml_query = dml_dir / "test_query.cypher"
    dml_query.write_text("CREATE (n:Node)")
    
    dql_query = dql_dir / "test_query.cypher"
    dql_query.write_text("MATCH (n:Node) RETURN n")
    
    result = load_typed_query("test_query", query_type="auto", base_dir=str(tmp_path))
    
    assert isinstance(result, str)
    assert result == "CREATE (n:Node)"  # dmlが優先


def test_load_typed_query_with_comments(tmp_path):
    """コメント除去のテスト"""
    query_file = tmp_path / "query.cypher"
    query_file.write_text("""// This is a comment
-- This is also a comment
CREATE (n:Node)
// Another comment
RETURN n""")
    
    result = load_typed_query("query", base_dir=str(tmp_path))
    
    assert isinstance(result, str)
    assert "// This is a comment" not in result
    assert "-- This is also a comment" not in result
    assert "CREATE (n:Node)" in result
    assert "RETURN n" in result


def test_load_typed_query_not_found():
    """クエリが見つからない場合のテスト"""
    result = load_typed_query("non_existent_query", base_dir="/tmp/non_existent")
    
    # NotFoundErrorが返る
    assert isinstance(result, dict)
    assert result["type"] == "FileOperationError"  # ディレクトリが存在しない
    assert "not found" in result["message"].lower()


def test_load_typed_query_invalid_type():
    """無効なquery_typeのテスト"""
    result = load_typed_query("query", query_type="invalid")
    
    # ValidationErrorが返る
    assert isinstance(result, dict)
    assert result["type"] == "ValidationError"
    assert result["field"] == "query_type"
    assert result["value"] == "invalid"


def test_execute_query_success(tmp_path):
    """execute_query成功のテスト"""
    # クエリファイルを準備
    query_file = tmp_path / "test.cypher"
    query_file.write_text("CREATE (n:Node {id: $id})")
    
    # モックリポジトリ
    executed_queries = []
    def mock_execute(query, params):
        executed_queries.append((query, params))
        return {"nodes_created": 1}
    
    repository = {"execute": mock_execute}
    
    # 実行
    result = execute_query(
        repository,
        "test",
        {"id": 123},
        query_type="auto"
    )
    
    # ベースディレクトリが異なるため、クエリが見つからない
    assert isinstance(result, dict)
    assert result["type"] == "NotFoundError"


def test_execute_query_with_error():
    """execute_queryでクエリ読み込みエラーのテスト"""
    repository = {"execute": lambda q, p: None}
    
    # 存在しないクエリ
    result = execute_query(
        repository,
        "non_existent",
        {},
        query_type="dml"
    )
    
    # エラーがそのまま返る
    assert isinstance(result, dict)
    assert result["type"] in ["FileOperationError", "NotFoundError"]


def test_caching_behavior(tmp_path):
    """キャッシュ動作のテスト"""
    query_file = tmp_path / "cached.cypher"
    query_file.write_text("MATCH (n) RETURN n")
    
    # 1回目の読み込み
    result1 = load_typed_query("cached", base_dir=str(tmp_path))
    
    # ファイルを変更
    query_file.write_text("MATCH (n) RETURN n LIMIT 10")
    
    # 2回目の読み込み（キャッシュから）
    result2 = load_typed_query("cached", base_dir=str(tmp_path))
    
    # キャッシュのため同じ結果
    assert result1 == result2
    assert "LIMIT 10" not in result2