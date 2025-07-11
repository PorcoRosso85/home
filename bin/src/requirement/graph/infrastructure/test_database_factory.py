"""
データベースファクトリーのテスト（TDD Red）

KuzuDBインスタンス生成を1箇所に集約
- in memory/persistenceの切り替え
- 環境に応じた設定
"""


class TestDatabaseFactory:
    """データベースファクトリーのテスト"""

    def setup_method(self):
        """各テストの前にキャッシュをクリア"""
        from .database_factory import clear_database_cache
        clear_database_cache()

    def test_create_persistent_database(self):
        """永続化データベースの作成（インメモリDBでテスト）"""
        from .database_factory import create_database

        # テストではインメモリDBを使用
        db = create_database(in_memory=True, use_cache=False, test_unique=True)

        assert db is not None

    def test_create_in_memory_database(self):
        """インメモリデータベースの作成"""
        from .database_factory import create_database

        db = create_database(in_memory=True)

        assert db is not None
        # インメモリデータベースはファイルを作成しない

    def test_create_connection(self):
        """コネクションの作成"""
        from .database_factory import create_database, create_connection

        # テストではインメモリDBを使用
        db = create_database(in_memory=True, use_cache=False, test_unique=True)
        conn = create_connection(db)

        assert conn is not None
        # 基本的なクエリが実行できることを確認
        result = conn.execute("RETURN 1 as value")
        assert result.has_next()
        assert result.get_next()[0] == 1


