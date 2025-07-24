#!/usr/bin/env python3
"""
existing_connection機能の統合テスト
実際のKuzuDBとVECTOR拡張を使用した動作確認
"""

import pytest
import tempfile
from vss_kuzu import create_vss
from vss_kuzu.infrastructure import create_kuzu_database, create_kuzu_connection, DatabaseConfig


class TestExistingConnection:
    """existing_connection機能の統合テスト"""
    
    def test_既存接続を使用したVSSの作成と動作(self):
        """既存のKuzuDB接続を使用してVSSが正常に動作すること"""
        # 実際のデータベースと接続を作成
        with tempfile.TemporaryDirectory() as tmpdir:
            db_config = DatabaseConfig(
                db_path=tmpdir,
                in_memory=False,
                embedding_dimension=256
            )
            
            # データベースと接続を作成
            db_success, database, db_error = create_kuzu_database(db_config)
            assert db_success, f"Database creation failed: {db_error}"
            
            conn_success, connection, conn_error = create_kuzu_connection(database)
            assert conn_success, f"Connection creation failed: {conn_error}"
            
            # 既存接続でVSSを作成
            vss = create_vss(existing_connection=connection)
            
            # 実際にインデックスと検索が動作することを確認
            documents = [{"id": "1", "content": "テストドキュメント"}]
            result = vss.index(documents)
            if not result["ok"]:
                print(f"Index failed: {result}")
            assert result["ok"], f"Index failed: {result}"
            
            search_result = vss.search("テスト")
            assert search_result["ok"]
    
    def test_新規接続と既存接続の動作の違い(self):
        """新規接続作成時と既存接続使用時で適切に処理が分岐すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ケース1: 新規接続作成（existing_connection=None）
            vss1 = create_vss(db_path=tmpdir + "/db1", in_memory=False)
            docs1 = [{"id": "1", "content": "新規接続でのドキュメント"}]
            result1 = vss1.index(docs1)
            assert result1["ok"]
            
            # ケース2: 既存接続を使用
            db_config = DatabaseConfig(
                db_path=tmpdir + "/db2",
                in_memory=False,
                embedding_dimension=256
            )
            db_success, database, _ = create_kuzu_database(db_config)
            assert db_success
            conn_success, connection, _ = create_kuzu_connection(database)
            assert conn_success
            
            vss2 = create_vss(existing_connection=connection)
            docs2 = [{"id": "2", "content": "既存接続でのドキュメント"}]
            result2 = vss2.index(docs2)
            assert result2["ok"]
            
            # 両方で検索が動作することを確認
            search1 = vss1.search("新規")
            search2 = vss2.search("既存")
            assert search1["ok"] and search2["ok"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])