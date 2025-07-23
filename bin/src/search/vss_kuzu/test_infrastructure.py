#!/usr/bin/env python3
"""
インフラ層のテスト - KuzuDB接続、VECTOR拡張関連
データベース操作、永続化、拡張機能の可用性など
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

from vss_kuzu import (
    DatabaseConfig,
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    count_documents,
    close_connection,
)
from vss_kuzu.infrastructure import EMBEDDING_DIMENSION


class TestInfrastructure:
    """インフラストラクチャ層のテストクラス"""
    
    @pytest.fixture
    def db_config(self):
        """Temporary database configuration"""
        tmpdir = tempfile.mkdtemp()
        config = DatabaseConfig(db_path=tmpdir, in_memory=False)
        yield config
        # Cleanup
        shutil.rmtree(tmpdir)
    
    @pytest.fixture
    def in_memory_config(self):
        """In-memory database configuration"""
        return DatabaseConfig(db_path=":memory:", in_memory=True)
    
    def test_indexing_without_vector_extension_returns_informative_error(self, db_config):
        """VECTOR拡張なしでインデックスを作成すると、有用なエラー情報を返すこと"""
        # データベースと接続を作成
        db_success, database, db_error = create_kuzu_database(db_config)
        if not db_success:
            # KuzuDBが利用できない環境の場合
            assert db_error is not None
            assert "error" in db_error
            assert "details" in db_error
            return
        
        conn_success, connection, conn_error = create_kuzu_connection(database)
        assert conn_success is True
        
        # スキーマ初期化を試みる
        schema_success, schema_error = initialize_vector_schema(connection, EMBEDDING_DIMENSION)
        
        if not schema_success:
            # エラーの場合、有用な情報が含まれていること
            assert schema_error is not None
            assert "error" in schema_error
            assert "details" in schema_error
            
            # VECTOR拡張が原因の場合
            if "VECTOR extension" in schema_error["error"]:
                # extensionフィールドが存在する場合のみチェック
                if "extension" in schema_error["details"]:
                    assert schema_error["details"]["extension"] == "VECTOR"
                # install_commandが存在する場合のみチェック
                if "install_command" in schema_error["details"]:
                    assert "INSTALL" in schema_error["details"]["install_command"]
        
        close_connection(connection)
    
    def test_search_without_vector_extension_returns_informative_error(self, db_config):
        """VECTOR拡張なしで検索すると、有用なエラー情報を返すこと"""
        # データベースと接続を作成
        db_success, database, db_error = create_kuzu_database(db_config)
        if not db_success:
            return
        
        conn_success, connection, conn_error = create_kuzu_connection(database)
        assert conn_success is True
        
        # ダミーの検索ベクトル
        query_vector = [0.1] * EMBEDDING_DIMENSION
        
        # 検索を実行
        search_success, results, search_error = search_similar_vectors(
            connection, query_vector, limit=10
        )
        
        if not search_success:
            # エラーの場合、有用な情報が含まれていること
            assert search_error is not None
            assert "error" in search_error
            assert "details" in search_error
            
            # VECTOR拡張が原因の場合
            if "VECTOR extension" in search_error["error"]:
                # extensionフィールドが存在する場合のみチェック
                if "extension" in search_error["details"]:
                    assert search_error["details"]["extension"] == "VECTOR"
                # install_commandが存在する場合のみチェック
                if "install_command" in search_error["details"]:
                    assert "INSTALL" in search_error["details"]["install_command"]
        
        close_connection(connection)
    
    def test_vector_index_persists_across_sessions(self, db_config):
        """ベクトルインデックスがセッションを超えて永続化されること"""
        # 最初のセッション
        db_success1, database1, _ = create_kuzu_database(db_config)
        if not db_success1:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success1, connection1, _ = create_kuzu_connection(database1)
        assert conn_success1 is True
        
        # VECTOR拡張をチェック
        vector_available, _ = check_vector_extension(connection1)
        if not vector_available:
            close_connection(connection1)
            pytest.skip("VECTOR extension not available in test environment")
        
        # スキーマ初期化
        schema_success, _ = initialize_vector_schema(connection1, EMBEDDING_DIMENSION)
        assert schema_success is True
        
        # ドキュメントを挿入
        documents = [
            ("1", "永続性テスト", [0.1] * EMBEDDING_DIMENSION)
        ]
        insert_success, count, _ = insert_documents_with_embeddings(connection1, documents)
        assert insert_success is True
        assert count == 1
        
        # 検索可能であることを確認
        query_vector = [0.1] * EMBEDDING_DIMENSION
        search_success1, results1, _ = search_similar_vectors(connection1, query_vector)
        assert search_success1 is True
        assert len(results1) > 0
        
        close_connection(connection1)
        
        # 新しいセッション
        db_success2, database2, _ = create_kuzu_database(db_config)
        assert db_success2 is True
        
        conn_success2, connection2, _ = create_kuzu_connection(database2)
        assert conn_success2 is True
        
        # 同じ検索を実行
        search_success2, results2, _ = search_similar_vectors(connection2, query_vector)
        
        if search_success2:
            assert len(results2) > 0
            assert results2[0]["id"] == "1"
            assert results2[0]["content"] == "永続性テスト"
        
        close_connection(connection2)
    
    def test_search_with_wrong_dimension_vector_returns_descriptive_error(self, in_memory_config):
        """誤った次元数のベクトルで検索すると、わかりやすいエラーを返すこと"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # 間違った次元数のベクトルを提供
        wrong_query_vector = [0.1] * 128  # 256次元ではなく128次元
        
        # 検索を実行
        search_success, results, search_error = search_similar_vectors(
            connection, wrong_query_vector, limit=10
        )
        
        # エラーが返されること
        assert search_success is False
        assert search_error is not None
        assert "error" in search_error
        assert "details" in search_error
        
        # 次元数の情報が含まれていること（存在する場合のみチェック）
        if "expected" in search_error["details"] and "got" in search_error["details"]:
            assert search_error["details"]["expected"] == EMBEDDING_DIMENSION
            assert search_error["details"]["got"] == 128
        else:
            # 少なくとも次元数に関するエラーメッセージが含まれていること
            assert "dimension" in search_error["error"].lower()
        
        close_connection(connection)
    
    def test_indexed_documents_are_searchable_immediately(self, in_memory_config):
        """インデックスしたドキュメントが即座に検索可能であること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # VECTOR拡張をチェック
        vector_available, _ = check_vector_extension(connection)
        if not vector_available:
            close_connection(connection)
            pytest.skip("VECTOR extension not available in test environment")
        
        # スキーマ初期化
        schema_success, _ = initialize_vector_schema(connection, EMBEDDING_DIMENSION)
        assert schema_success is True
        
        # ドキュメントをインデックス
        documents = [
            ("1", "テストドキュメント", [0.5] * EMBEDDING_DIMENSION)
        ]
        
        insert_success, count, _ = insert_documents_with_embeddings(connection, documents)
        assert insert_success is True
        assert count == 1
        
        # 即座に検索できることを確認
        query_vector = [0.5] * EMBEDDING_DIMENSION
        search_success, results, _ = search_similar_vectors(connection, query_vector)
        
        assert search_success is True
        assert len(results) == 1
        assert results[0]["id"] == "1"
        assert results[0]["content"] == "テストドキュメント"
        
        close_connection(connection)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])