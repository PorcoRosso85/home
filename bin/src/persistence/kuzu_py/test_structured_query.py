"""構造化クエリサポートのテスト"""
import tempfile
from pathlib import Path
import pytest
from query_loader import load_structured_query


class TestStructuredQuery:
    """構造化されたクエリディレクトリ（dml/dql）からのクエリ読み込みテスト"""

    def test_load_dml_query_from_structured_directory(self):
        """DMLディレクトリからクエリを読み込めること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリ構造作成
            base_dir = Path(tmpdir)
            dml_dir = base_dir / "dml"
            dml_dir.mkdir()
            
            # テストクエリファイル作成
            query_file = dml_dir / "create_user.cypher"
            query_file.write_text("CREATE (u:User {name: $name})")
            
            # 実行
            result = load_structured_query(
                query_name="create_user",
                query_type="dml",
                base_dir=str(base_dir)
            )
            
            # 検証
            assert result == "CREATE (u:User {name: $name})"

    def test_load_dql_query_from_structured_directory(self):
        """DQLディレクトリからクエリを読み込めること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリ構造作成
            base_dir = Path(tmpdir)
            dql_dir = base_dir / "dql"
            dql_dir.mkdir()
            
            # テストクエリファイル作成
            query_file = dql_dir / "find_user.cypher"
            query_file.write_text("MATCH (u:User {name: $name}) RETURN u")
            
            # 実行
            result = load_structured_query(
                query_name="find_user",
                query_type="dql",
                base_dir=str(base_dir)
            )
            
            # 検証
            assert result == "MATCH (u:User {name: $name}) RETURN u"

    def test_auto_detect_query_type(self):
        """query_type='auto'で自動的にクエリファイルを検出できること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリ構造作成
            base_dir = Path(tmpdir)
            dml_dir = base_dir / "dml"
            dql_dir = base_dir / "dql"
            dml_dir.mkdir()
            dql_dir.mkdir()
            
            # DMLに配置
            query_file = dml_dir / "update_user.cypher"
            query_file.write_text("MATCH (u:User {id: $id}) SET u.name = $name")
            
            # 実行（autoで検出）
            result = load_structured_query(
                query_name="update_user",
                query_type="auto",
                base_dir=str(base_dir)
            )
            
            # 検証
            assert result == "MATCH (u:User {id: $id}) SET u.name = $name"

    def test_query_not_found_error(self):
        """存在しないクエリでエラーを返すこと"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # dmlディレクトリを作成して、ファイルが見つからないケースをテスト
            base_dir = Path(tmpdir)
            dml_dir = base_dir / "dml"
            dml_dir.mkdir()
            
            result = load_structured_query(
                query_name="nonexistent",
                query_type="dml",
                base_dir=str(base_dir)
            )
            
            assert isinstance(result, dict)
            assert result.get("ok") is False
            assert "Query file not found" in result["error"]
            assert "nonexistent" in str(result["details"])

    def test_directory_not_found_error(self):
        """ディレクトリが存在しない場合のエラー"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_structured_query(
                query_name="test",
                query_type="dml",
                base_dir=str(tmpdir)
            )
            
            assert isinstance(result, dict)
            assert result.get("ok") is False
            assert "directory not found" in result["error"]

    def test_invalid_query_type_error(self):
        """無効なquery_typeでエラーを返すこと"""
        result = load_structured_query(
            query_name="test",
            query_type="invalid",
            base_dir="."
        )
        
        assert isinstance(result, dict)
        assert result.get("ok") is False
        assert "Invalid query_type" in result["error"]

    def test_comment_removal_in_structured_query(self):
        """構造化クエリでもコメントが適切に除去されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリ構造作成
            base_dir = Path(tmpdir)
            dql_dir = base_dir / "dql"
            dql_dir.mkdir()
            
            # コメント付きクエリ
            query_file = dql_dir / "complex_query.cypher"
            query_file.write_text("""// ユーザー検索クエリ
MATCH (u:User)
// WHERE句でフィルタ
WHERE u.active = true
RETURN u
-- このコメントも除去される""")
            
            # 実行
            result = load_structured_query(
                query_name="complex_query",
                query_type="dql",
                base_dir=str(base_dir)
            )
            
            # 検証（コメントが除去されていること）
            expected = """MATCH (u:User)
WHERE u.active = true
RETURN u"""
            assert result == expected

    def test_auto_search_priority(self):
        """autoモードではdml→dqlの順で検索されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリ構造作成
            base_dir = Path(tmpdir)
            dml_dir = base_dir / "dml"
            dql_dir = base_dir / "dql"
            dml_dir.mkdir()
            dql_dir.mkdir()
            
            # 同じ名前のクエリを両方に配置
            (dml_dir / "same_name.cypher").write_text("DML QUERY")
            (dql_dir / "same_name.cypher").write_text("DQL QUERY")
            
            # 実行
            result = load_structured_query(
                query_name="same_name",
                query_type="auto",
                base_dir=str(base_dir)
            )
            
            # 検証（DMLが優先される）
            assert result == "DML QUERY"