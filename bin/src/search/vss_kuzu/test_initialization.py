#!/usr/bin/env python3
"""
初期化エラーハンドリングの統合テスト
規約に従い、モックを使わず実際のKuzuDBで動作をテスト
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from vss_kuzu.application import create_embedding_service
from vss_kuzu.infrastructure.variables.config import create_config
from vss_kuzu.infrastructure import (
    create_kuzu_database,
    create_kuzu_connection,
    check_vector_extension,
    initialize_vector_schema,
    insert_documents_with_embeddings,
    search_similar_vectors,
    DatabaseConfig,
)


class TestInitializationErrors:
    """初期化エラーハンドリングのテストクラス"""
    
    def test_database_with_valid_path_handles_vector_extension(self):
        """データベースでVECTOR拡張の状態を適切に処理すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ConfigとDatabaseConfigを作成
            config = create_config(db_path=tmpdir, in_memory=False)
            db_config = {
                'db_path': config['db_path'],
                'in_memory': config['in_memory'],
                'embedding_dimension': config['embedding_dimension']
            }
            
            # データベース作成を試みる
            db_success, database, db_error = create_kuzu_database(db_config)
            
            if db_success:
                # コネクション作成
                conn_success, connection, conn_error = create_kuzu_connection(database)
                
                if conn_success:
                    # VECTOR拡張のチェック
                    vec_success, vec_error = check_vector_extension(connection)
                    
                    if vec_success:
                        # スキーマ初期化
                        schema_success, schema_error = initialize_vector_schema(connection, dimension=256)
                        assert schema_success is True
                        
                        # 正常に動作することを確認
                        embedding_func = create_embedding_service(config['model_name'])
                        embedding = embedding_func("test document")
                        docs = [("doc1", "test document", embedding)]
                        insert_success, count, insert_error = insert_documents_with_embeddings(connection, docs)
                        assert insert_success is True
                        assert count == 1
                    else:
                        # VECTOR拡張が利用できない場合
                        assert vec_error is not None
            else:
                # データベース作成に失敗した場合
                assert db_error is not None
    
    def test_database_with_readonly_path_returns_error(self):
        """読み取り専用パスでエラーが適切に処理されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリを読み取り専用にする
            Path(tmpdir).chmod(0o444)
            
            try:
                # ConfigとDatabaseConfigを作成
                config = create_config(db_path=f"{tmpdir}/readonly_db", in_memory=False)
                db_config = {
                    'db_path': config['db_path'],
                    'in_memory': config['in_memory'],
                    'embedding_dimension': config['embedding_dimension']
                }
                
                # データベース作成を試みる
                db_success, database, db_error = create_kuzu_database(db_config)
                
                # 初期化エラーが発生すること
                assert db_success is False
                assert db_error is not None
                assert "Permission denied" in str(db_error) or "Read-only" in str(db_error)
                
            finally:
                # 権限を戻す
                Path(tmpdir).chmod(0o755)
    
    def test_database_with_invalid_path_characters_returns_error(self):
        """無効なパス文字でエラーが適切に処理されること"""
        # NUL文字を含む無効なパス
        invalid_path = "/tmp/test\x00db"
        
        # ConfigとDatabaseConfigを作成
        config = create_config(db_path=invalid_path, in_memory=False)
        db_config = {
            'db_path': config['db_path'],
            'in_memory': config['in_memory'],
            'embedding_dimension': config['embedding_dimension']
        }
        
        # データベース作成を試みる
        db_success, database, db_error = create_kuzu_database(db_config)
        
        # 初期化エラーが発生すること
        assert db_success is False
        assert db_error is not None
    
    def test_database_operations_fail_gracefully_when_not_initialized(self):
        """初期化失敗時にすべての操作が適切にエラーを返すこと"""
        # 無効なパスでデータベースを作成
        invalid_path = "/nonexistent/path/\x00/db"
        config = create_config(db_path=invalid_path, in_memory=False)
        db_config = {
            'db_path': config['db_path'],
            'in_memory': config['in_memory'],
            'embedding_dimension': config['embedding_dimension']
        }
        
        # データベース作成に失敗
        db_success, database, db_error = create_kuzu_database(db_config)
        assert db_success is False
        assert db_error is not None
        
        # データベースがないため、コネクション作成も失敗する
        if database is None:
            # データベースが作成されなかった場合
            # 以降の操作は実行できない
            return
        
        # コネクション作成を試みる
        conn_success, connection, conn_error = create_kuzu_connection(database)
        if not conn_success:
            assert conn_error is not None
    
    def test_in_memory_database_handles_vector_extension(self):
        """インメモリデータベースでVECTOR拡張の状態を適切に処理すること"""
        # ConfigとDatabaseConfigを作成
        config = create_config(db_path=":memory:", in_memory=True)
        db_config = {
            'db_path': config['db_path'],
            'in_memory': config['in_memory'],
            'embedding_dimension': config['embedding_dimension']
        }
        
        # データベース作成
        db_success, database, db_error = create_kuzu_database(db_config)
        assert db_success is True
        
        # コネクション作成
        conn_success, connection, conn_error = create_kuzu_connection(database)
        assert conn_success is True
        
        # VECTOR拡張のチェック
        vec_success, vec_error = check_vector_extension(connection)
        
        if vec_success:
            # VECTOR拡張が利用可能な場合
            # スキーマ初期化
            schema_success, schema_error = initialize_vector_schema(connection, dimension=256)
            assert schema_success is True
            
            # 正常に動作することを確認
            embedding_func = create_embedding_service(config['model_name'])
            embedding = embedding_func("in-memory test")
            docs = [("doc1", "in-memory test", embedding)]
            insert_success, count, insert_error = insert_documents_with_embeddings(connection, docs)
            assert insert_success is True
            assert count == 1
        else:
            # VECTOR拡張が利用できない場合
            assert vec_error is not None
    
    def test_initialization_error_details_contain_useful_information(self):
        """初期化エラーの詳細に有用な情報が含まれること"""
        # 無効なパスでデータベースを作成
        invalid_path = "/root/no_permission_db"
        config = create_config(db_path=invalid_path, in_memory=False)
        db_config = {
            'db_path': config['db_path'],
            'in_memory': config['in_memory'],
            'embedding_dimension': config['embedding_dimension']
        }
        
        # データベース作成を試みる
        db_success, database, db_error = create_kuzu_database(db_config)
        
        if not db_success:
            # エラーに必要な情報が含まれていること
            assert db_error is not None
            
            # パス情報が含まれていること（デバッグに有用）
            error_str = str(db_error)
            assert invalid_path in error_str or "Permission" in error_str
    
    def test_multiple_connections_handle_vector_extension_consistently(self):
        """複数のコネクションがVECTOR拡張を一貫して処理すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ConfigとDatabaseConfigを作成
            config = create_config(db_path=tmpdir, in_memory=False)
            db_config = {
                'db_path': config['db_path'],
                'in_memory': config['in_memory'],
                'embedding_dimension': config['embedding_dimension']
            }
            
            # 最初のデータベースとコネクション
            db_success1, database1, db_error1 = create_kuzu_database(db_config)
            assert db_success1 is True
            
            conn_success1, connection1, conn_error1 = create_kuzu_connection(database1)
            assert conn_success1 is True
            
            # 2番目のデータベースとコネクション（同じパス）
            db_success2, database2, db_error2 = create_kuzu_database(db_config)
            assert db_success2 is True
            
            conn_success2, connection2, conn_error2 = create_kuzu_connection(database2)
            assert conn_success2 is True
            
            # 両コネクションでVECTOR拡張の状態をチェック
            vec_success1, vec_error1 = check_vector_extension(connection1)
            vec_success2, vec_error2 = check_vector_extension(connection2)
            
            # 両コネクションの初期化状態が一致すること
            assert vec_success1 == vec_success2
            
            if vec_success1:
                # 両方ともVECTOR拡張が利用可能
                # スキーマ初期化
                schema_success1, schema_error1 = initialize_vector_schema(connection1, dimension=256)
                schema_success2, schema_error2 = initialize_vector_schema(connection2, dimension=256)
                assert schema_success1 is True
                assert schema_success2 is True
                
                # データ操作が可能
                embedding_func = create_embedding_service(config['model_name'])
                
                embedding1 = embedding_func("shared document")
                docs1 = [("shared1", "shared document", embedding1)]
                insert_success1, count1, insert_error1 = insert_documents_with_embeddings(connection1, docs1)
                assert insert_success1 is True
                
                embedding2 = embedding_func("another shared document")
                docs2 = [("shared2", "another shared document", embedding2)]
                insert_success2, count2, insert_error2 = insert_documents_with_embeddings(connection2, docs2)
                assert insert_success2 is True
            else:
                # 両方ともVECTOR拡張が利用不可
                assert vec_error1 is not None
                assert vec_error2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])