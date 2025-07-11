#!/usr/bin/env python3
"""ベクトル検索層のテスト - RED段階"""

import pytest
from typing import List
from embeddings.infrastructure.kuzu import KuzuVectorRepository


class TestKuzuVectorRepository:
    """KuzuDBベクトルリポジトリのテスト"""
    
    def test_ベクトルインデックスの作成(self, mock_connection):
        """KuzuDBにベクトルインデックスが作成されること"""
        repo = KuzuVectorRepository(mock_connection)
        result = repo.create_index(
            table_name="Document",
            index_name="doc_embedding_index",
            column_name="embedding",
            dimension=256
        )
        assert result.ok is True
        assert "created" in result.message
    
    def test_類似ベクトル検索(self, mock_connection):
        """上位k件の類似ドキュメントが距離順で返されること"""
        from embeddings.infrastructure.kuzu.vector_subprocess_wrapper import KuzuVectorSubprocess, is_pytest_running
        
        repo = KuzuVectorRepository(mock_connection)
        
        # テストデータを挿入
        test_docs = [
            {"id": 1, "content": "瑠璃色の説明", "embedding": [0.1] * 256},
            {"id": 2, "content": "別の文書", "embedding": [0.2] * 256},
            {"id": 3, "content": "さらに別の文書", "embedding": [0.3] * 256},
        ]
        
        if is_pytest_running() and hasattr(mock_connection, '_database'):
            # pytest環境ではサブプロセスでデータを挿入
            wrapper = KuzuVectorSubprocess(mock_connection._database._database_path)
            result = wrapper.execute_vector_operation("insert_documents", {"documents": test_docs})
            if not result["ok"]:
                raise RuntimeError(f"Failed to insert documents: {result.get('error')}")
        else:
            # 通常環境では直接挿入
            for doc in test_docs:
                mock_connection.execute("""
                    CREATE (d:Document {
                        id: $id,
                        content: $content,
                        embedding: $embedding
                    })
                """, doc)
        
        # インデックスを作成
        repo.create_index("Document", "doc_embedding_index", "embedding", 256)
        
        # 検索を実行
        query_embedding = [0.15] * 256  # 256次元
        result = repo.query_index(
            index_name="doc_embedding_index",
            query_vector=query_embedding,
            k=2
        )
        
        assert result.ok is True
        assert len(result.results) == 2
        # 距離順にソートされていること
        if result.results:
            distances = [r['distance'] for r in result.results]
            assert distances == sorted(distances)
    
    def test_ベクトルインデックスの削除(self, mock_connection):
        """ベクトルインデックスが削除できること"""
        repo = KuzuVectorRepository(mock_connection)
        
        # まずインデックスを作成
        create_result = repo.create_index(
            table_name="Document",
            index_name="doc_embedding_index",
            column_name="embedding",
            dimension=256
        )
        assert create_result.ok is True
        
        # 次にインデックスを削除
        result = repo.drop_index(
            table_name="Document",
            index_name="doc_embedding_index"
        )
        assert result.ok is True
        assert "dropped" in result.message
    
    def test_存在しないインデックスへのクエリ(self, mock_connection):
        """存在しないインデックスへのクエリがエラーを返すこと"""
        repo = KuzuVectorRepository(mock_connection)
        query_embedding = [0.1] * 256
        result = repo.query_index(
            index_name="non_existent_index",
            query_vector=query_embedding,
            k=5
        )
        assert result.ok is False
        assert "not found" in result.error.lower()


@pytest.fixture
def mock_connection():
    """実際のKuzuDB接続（サブプロセスラッパー対応）"""
    import kuzu
    import tempfile
    import shutil
    from embeddings.infrastructure.kuzu.vector_subprocess_wrapper import KuzuVectorSubprocess, is_pytest_running
    
    # 一時ディレクトリでKuzuDBを作成
    tmpdir = tempfile.mkdtemp()
    
    # pytest環境の場合はサブプロセスでスキーマを作成
    if is_pytest_running():
        # サブプロセスで初期化
        wrapper = KuzuVectorSubprocess(tmpdir)
        # スキーマ作成
        result = wrapper.execute_vector_operation("create_schema", {})
        if not result["ok"]:
            raise RuntimeError(f"Failed to create schema: {result.get('error')}")
        
        # ダミーのconnectionオブジェクトを作成（db_pathだけ設定）
        class MockConnection:
            def __init__(self, db_path):
                self._database = type('obj', (object,), {'_database_path': db_path})()
                
            def close(self):
                pass
        
        conn = MockConnection(tmpdir)
    else:
        # 通常環境では直接実行
        db = kuzu.Database(tmpdir)
        conn = kuzu.Connection(db)
        
        # VECTOR拡張をインストール
        try:
            conn.execute("INSTALL VECTOR;")
        except:
            pass
        conn.execute("LOAD EXTENSION VECTOR;")
        
        # テスト用のスキーマを作成
        conn.execute("""
            CREATE NODE TABLE Document (
                id INT64,
                content STRING,
                embedding FLOAT[256],
                PRIMARY KEY (id)
            )
        """)
        
        # connectionオブジェクトにdb_pathを設定
        conn._database = db
        conn._database._database_path = tmpdir
    
    yield conn
    
    # クリーンアップ
    conn.close()
    shutil.rmtree(tmpdir)