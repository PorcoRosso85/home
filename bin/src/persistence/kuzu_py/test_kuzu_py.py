"""
kuzu_py インフラ層のテスト

規約に従い、インフラ層の統合テストのみを実装
"""
import pytest
from kuzu_py import create_database, create_connection


def test_create_in_memory_database():
    """In-memoryデータベース作成の動作確認"""
    # Act
    result = create_database(":memory:")
    
    # Assert - Result型でエラーがないことを確認
    # エラーの場合は辞書型でtypeフィールドを持つ、成功時はDatabaseオブジェクト
    assert not isinstance(result, dict) or "type" not in result
    assert result is not None


def test_create_connection():
    """データベース接続作成の動作確認"""
    # Arrange
    db_result = create_database(":memory:")
    assert not isinstance(db_result, dict) or "type" not in db_result
    
    # Act
    conn_result = create_connection(db_result)
    
    # Assert
    assert not isinstance(conn_result, dict) or "type" not in conn_result
    assert conn_result is not None


def test_basic_kuzu_operations():
    """KuzuDBの基本操作が可能であることを確認"""
    # Arrange
    db_result = create_database(":memory:")
    assert not isinstance(db_result, dict) or "type" not in db_result
    
    conn_result = create_connection(db_result)
    assert not isinstance(conn_result, dict) or "type" not in conn_result
    
    # Act & Assert - 基本的なCypher操作
    conn = conn_result
    
    # テーブル作成
    conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))")
    
    # データ挿入
    conn.execute("CREATE (:Person {name: 'Alice', age: 30})")
    
    # クエリ実行
    result = conn.execute("MATCH (p:Person) RETURN p.name, p.age")
    assert result.has_next()
    
    row = result.get_next()
    assert row[0] == "Alice"
    assert row[1] == 30


def test_error_handling_invalid_path():
    """無効なパスでのデータベース作成時のエラーハンドリング"""
    # 存在しないディレクトリへのパス
    result = create_database("/invalid/path/to/database")
    
    # FileOperationErrorが返されることを確認
    assert isinstance(result, dict)
    assert result["type"] == "FileOperationError"
    assert "message" in result
    assert result["operation"] == "create"
    assert result["file_path"] == "/invalid/path/to/database"
    assert result["permission_issue"] is True


def test_error_handling_none_database():
    """Noneデータベースでの接続作成時のエラーハンドリング"""
    result = create_connection(None)
    
    # ValidationErrorが返されることを確認
    assert isinstance(result, dict)
    assert result["type"] == "ValidationError"
    assert result["message"] == "Database instance is required"
    assert result["field"] == "database"
    assert result["value"] == "None"
    assert result["constraint"] == "Must be a valid kuzu.Database instance"


def test_kuzu_api_exposed():
    """KuzuDBのAPIが直接公開されていることを確認"""
    # kuzu_pyからKuzuDBのクラスが直接インポートできることを確認
    try:
        from kuzu_py import Database, Connection
        assert Database is not None
        assert Connection is not None
    except ImportError:
        # Nix環境外では失敗する可能性があるため、スキップ
        pytest.skip("KuzuDB not available in this environment")