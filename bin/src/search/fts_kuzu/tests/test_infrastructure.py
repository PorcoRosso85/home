#!/usr/bin/env python3
"""
インフラ層のテスト - KuzuDB接続、VECTOR拡張関連
データベース操作、永続化、拡張機能の可用性など
"""

import shutil
import sys
import tempfile

import pytest

from fts_kuzu import (
    DatabaseConfig,
    close_connection,
    create_fts_index,
    create_kuzu_connection,
    create_kuzu_database,
    drop_fts_index,
    get_fts_index_info,
    initialize_fts_schema,
    install_fts_extension,
    list_fts_indexes,
)


class TestInfrastructure:
    """インフラストラクチャ層のテストクラス"""

    @pytest.fixture
    def db_config(self):
        """Temporary database configuration"""
        tmpdir = tempfile.mkdtemp()
        config: DatabaseConfig = {'db_path': tmpdir, 'in_memory': False}
        yield config
        # Cleanup
        shutil.rmtree(tmpdir)

    @pytest.fixture
    def in_memory_config(self):
        """In-memory database configuration"""
        return {'db_path': ":memory:", 'in_memory': True}

    # VSS-related tests removed





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
            assert (
                "already installed" in second_error["error"].lower()
                or "already exists" in second_error["error"].lower()
            )

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
            "index_name": "doc_content_idx",
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
            "case_sensitive": False,
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
            "index_name": "doc_to_drop_idx",
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
        assert (
            "not found" in drop_error["error"].lower()
            or "does not exist" in drop_error["error"].lower()
        )

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
            config = {"table_name": "Document", "property_name": "content", "index_name": idx_name}
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
            "stemming": True,
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
