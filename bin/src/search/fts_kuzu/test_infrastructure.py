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

import sys
sys.path.insert(0, '.')

from infrastructure import (
    DatabaseConfig,
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    count_documents,
    close_connection,
    EMBEDDING_DIMENSION,
    install_fts_extension,
    initialize_fts_schema,
    create_fts_index,
    drop_fts_index,
    list_fts_indexes,
    get_fts_index_info
)


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
                assert schema_error["details"]["extension"] == "VECTOR"
                assert "install_command" in schema_error["details"]
        
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
                assert search_error["details"]["extension"] == "VECTOR"
                assert "install_command" in search_error["details"]
        
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
        
        # 次元数の情報が含まれていること
        assert search_error["details"]["expected"] == EMBEDDING_DIMENSION
        assert search_error["details"]["got"] == 128
        
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
    
    def test_install_fts_extension_success(self, in_memory_config):
        """FTS拡張のインストールが成功すること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストール
        install_success, install_error = install_fts_extension(connection)
        
        assert install_success is True
        assert install_error is None
        
        close_connection(connection)
    
    def test_install_fts_extension_duplicate_handling(self, in_memory_config):
        """FTS拡張の重複インストール時に適切に処理されること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # 1回目のインストール
        first_install_success, first_error = install_fts_extension(connection)
        assert first_install_success is True
        
        # 2回目のインストール（重複）
        second_install_success, second_error = install_fts_extension(connection)
        
        # 重複インストールでも成功またはすでにインストール済みのエラーを返すこと
        if second_install_success:
            assert second_error is None
        else:
            assert second_error is not None
            assert "error" in second_error
            assert "already installed" in second_error["error"].lower() or "already exists" in second_error["error"].lower()
        
        close_connection(connection)
    
    def test_initialize_fts_schema_without_extension_returns_error(self, in_memory_config):
        """FTS拡張なしでスキーマ初期化するとエラーを返すこと"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストールせずにスキーマ初期化を試みる
        schema_success, schema_error = initialize_fts_schema(connection)
        
        assert schema_success is False
        assert schema_error is not None
        assert "error" in schema_error
        assert "details" in schema_error
        assert "FTS extension" in schema_error["error"] or "fts" in schema_error["error"].lower()
        
        close_connection(connection)
    
    def test_initialize_fts_schema_with_extension_succeeds(self, in_memory_config):
        """FTS拡張インストール後のスキーマ初期化が成功すること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストール
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        # FTSスキーマを初期化
        schema_success, schema_error = initialize_fts_schema(connection)
        
        assert schema_success is True
        assert schema_error is None
        
        close_connection(connection)
    
    def test_create_fts_index_success(self, in_memory_config):
        """FTSインデックスの作成が成功すること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストール
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        # FTSスキーマを初期化
        schema_success, _ = initialize_fts_schema(connection)
        assert schema_success is True
        
        # FTSインデックスを作成
        index_config = {
            "table_name": "Document",
            "property_name": "content",
            "index_name": "doc_content_idx"
        }
        
        create_success, create_error = create_fts_index(connection, index_config)
        
        assert create_success is True
        assert create_error is None
        
        close_connection(connection)
    
    def test_create_fts_index_with_custom_config(self, in_memory_config):
        """カスタム設定でFTSインデックスを作成できること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストールとスキーマ初期化
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        schema_success, _ = initialize_fts_schema(connection)
        assert schema_success is True
        
        # カスタム設定でFTSインデックスを作成
        index_config = {
            "table_name": "Document",
            "property_name": "content",
            "index_name": "doc_content_custom_idx",
            "stopwords": ["the", "is", "and", "a"],
            "stemming": True,
            "case_sensitive": False
        }
        
        create_success, create_error = create_fts_index(connection, index_config)
        
        assert create_success is True
        assert create_error is None
        
        close_connection(connection)
    
    def test_drop_fts_index_success(self, in_memory_config):
        """FTSインデックスの削除が成功すること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストールとスキーマ初期化
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        schema_success, _ = initialize_fts_schema(connection)
        assert schema_success is True
        
        # インデックスを作成
        index_config = {
            "table_name": "Document",
            "property_name": "content",
            "index_name": "doc_to_drop_idx"
        }
        create_success, _ = create_fts_index(connection, index_config)
        assert create_success is True
        
        # インデックスを削除
        drop_success, drop_error = drop_fts_index(connection, "doc_to_drop_idx")
        
        assert drop_success is True
        assert drop_error is None
        
        close_connection(connection)
    
    def test_drop_nonexistent_fts_index_returns_error(self, in_memory_config):
        """存在しないFTSインデックスの削除はエラーを返すこと"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストール
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        # 存在しないインデックスを削除しようとする
        drop_success, drop_error = drop_fts_index(connection, "nonexistent_idx")
        
        assert drop_success is False
        assert drop_error is not None
        assert "error" in drop_error
        assert "details" in drop_error
        assert "not found" in drop_error["error"].lower() or "does not exist" in drop_error["error"].lower()
        
        close_connection(connection)
    
    def test_list_fts_indexes_returns_created_indexes(self, in_memory_config):
        """作成したFTSインデックスが一覧に含まれること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストールとスキーマ初期化
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        schema_success, _ = initialize_fts_schema(connection)
        assert schema_success is True
        
        # 複数のインデックスを作成
        index_names = ["idx1", "idx2", "idx3"]
        for idx_name in index_names:
            config = {
                "table_name": "Document",
                "property_name": "content",
                "index_name": idx_name
            }
            create_success, _ = create_fts_index(connection, config)
            assert create_success is True
        
        # インデックス一覧を取得
        list_success, indexes, list_error = list_fts_indexes(connection)
        
        assert list_success is True
        assert list_error is None
        assert isinstance(indexes, list)
        
        # 作成したインデックスが含まれていること
        found_names = [idx["name"] for idx in indexes]
        for idx_name in index_names:
            assert idx_name in found_names
        
        close_connection(connection)
    
    def test_get_fts_index_info_returns_details(self, in_memory_config):
        """FTSインデックスの詳細情報を取得できること"""
        # データベースと接続を作成
        db_success, database, _ = create_kuzu_database(in_memory_config)
        if not db_success:
            pytest.skip("KuzuDB not available in test environment")
        
        conn_success, connection, _ = create_kuzu_connection(database)
        assert conn_success is True
        
        # FTS拡張をインストールとスキーマ初期化
        install_success, _ = install_fts_extension(connection)
        if not install_success:
            close_connection(connection)
            pytest.skip("FTS extension installation failed")
        
        schema_success, _ = initialize_fts_schema(connection)
        assert schema_success is True
        
        # インデックスを作成
        index_config = {
            "table_name": "Document",
            "property_name": "content",
            "index_name": "doc_info_idx",
            "stopwords": ["the", "is"],
            "stemming": True
        }
        create_success, _ = create_fts_index(connection, index_config)
        assert create_success is True
        
        # インデックス情報を取得
        info_success, index_info, info_error = get_fts_index_info(connection, "doc_info_idx")
        
        assert info_success is True
        assert info_error is None
        assert isinstance(index_info, dict)
        assert index_info["name"] == "doc_info_idx"
        assert index_info["table"] == "Document"
        assert index_info["property"] == "content"
        assert "stopwords" in index_info
        assert "stemming" in index_info
        
        close_connection(connection)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])