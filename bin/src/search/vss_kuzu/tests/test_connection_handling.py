#!/usr/bin/env python3
"""
接続管理の検証テスト

VSS_KUZUのデータベース接続が適切に管理されることを検証する。
永続的データベース、複数接続、リソース管理に焦点を当てる。
"""

import pytest
import tempfile
import os
import gc
from typing import List, Any
from log_py import log
from pathlib import Path


class TestConnectionHandling:
    """接続管理のテストクラス"""
    
    def test_persistent_database_connection(self):
        """永続的データベースでの接続が正常に管理されることを確認"""
        log("info", {
            "message": "Testing persistent database connection",
            "test": "test_persistent_database_connection"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            db_path = Path(db_dir)
            
            # 永続的データベースでVSSを作成
            vss1 = create_vss(db_path=str(db_path), in_memory=False)
            if isinstance(vss1, dict) and vss1.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss1.get('message')}")
                
                # データをインデックスに追加
                doc = {
                    "id": "persist_001",
                    "content": "永続化テストデータ"
                }
                index_result = vss1.index([doc])
                assert index_result.get('ok'), f"Failed to index: {index_result}"
                
                # 接続を閉じる（closeメソッドがある場合）
                if hasattr(vss1, 'close'):
                    vss1.close()
                
                # 同じデータベースパスで新しい接続を作成
                vss2 = create_vss(db_path=str(db_path), in_memory=False)
                if isinstance(vss2, dict) and vss2.get('type'):
                    pytest.skip(f"VECTOR extension not available: {vss2.get('message')}")
                
                # データが永続化されていることを確認
                search_result = vss2.search("永続化テスト", limit=5)
                assert search_result.get('ok'), f"Search failed: {search_result}"
                assert search_result.get('results'), "No results found in persistent database"
                
                # 結果を検証
                found = False
                for result in search_result['results']:
                    if result.get('id') == 'persist_001':
                        found = True
                        log("info", {
                            "message": "Found persisted document",
                            "id": result.get('id'),
                            "content": result.get('content')
                        })
                        break
                
                assert found, "Persisted document not found after reconnection"
                
                # クリーンアップ
                if hasattr(vss2, 'close'):
                    vss2.close()
    
    def test_multiple_connections_work_independently(self):
        """複数の接続が独立して動作することを確認"""
        log("info", {
            "message": "Testing multiple independent connections",
            "test": "test_multiple_connections_work_independently"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir1, \
             tempfile.TemporaryDirectory() as db_dir2:
            
            # 2つの独立したVSSインスタンスを作成
            os.environ['RGL_DATABASE_PATH'] = db_dir1
            vss1 = create_vss(db_path=db_dir1, in_memory=False)
            if isinstance(vss1, dict) and vss1.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss1.get('message')}")
            
            os.environ['RGL_DATABASE_PATH'] = db_dir2
            vss2 = create_vss(db_path=db_dir2, in_memory=False)
            if isinstance(vss2, dict) and vss2.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss2.get('message')}")
                
                # それぞれに異なるデータを追加
                doc1 = {
                    "id": "conn1_001",
                    "content": "接続1のデータ"
                }
                doc2 = {
                    "id": "conn2_001",
                    "content": "接続2のデータ"
                }
                
                result1 = vss1.index([doc1])
                assert result1.get('ok'), f"Failed to index in vss1: {result1}"
                
                result2 = vss2.index([doc2])
                assert result2.get('ok'), f"Failed to index in vss2: {result2}"
                
                # それぞれの接続で独立したデータが管理されていることを確認
                search1 = vss1.search("接続1", limit=5)
                search2 = vss2.search("接続2", limit=5)
                
                assert search1.get('ok') and search2.get('ok'), "Search failed"
                
                # vss1には接続1のデータのみが存在
                found_in_vss1 = any(r.get('id') == 'conn1_001' for r in search1.get('results', []))
                not_found_in_vss1 = not any(r.get('id') == 'conn2_001' for r in search1.get('results', []))
                
                # vss2には接続2のデータのみが存在
                found_in_vss2 = any(r.get('id') == 'conn2_001' for r in search2.get('results', []))
                not_found_in_vss2 = not any(r.get('id') == 'conn1_001' for r in search2.get('results', []))
                
                log("info", {
                    "message": "Connection independence test results",
                    "vss1_has_conn1": found_in_vss1,
                    "vss1_not_has_conn2": not_found_in_vss1,
                    "vss2_has_conn2": found_in_vss2,
                    "vss2_not_has_conn1": not_found_in_vss2
                })
                
                assert found_in_vss1 and not_found_in_vss1, "VSS1 should only have its own data"
                assert found_in_vss2 and not_found_in_vss2, "VSS2 should only have its own data"
                
                # クリーンアップ
                if hasattr(vss1, 'close'):
                    vss1.close()
                if hasattr(vss2, 'close'):
                    vss2.close()
    
    def test_connection_cleanup_on_close(self):
        """close()メソッドでリソースが適切に解放されることを確認"""
        log("info", {
            "message": "Testing connection cleanup on close",
            "test": "test_connection_cleanup_on_close"
        })
        
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            
            connections: List[Any] = []
            
            # 複数の接続を作成
            for i in range(3):
                vss = create_vss(db_path=db_dir, in_memory=False)
                if isinstance(vss, dict) and vss.get('type'):
                    pytest.skip(f"VECTOR extension not available: {vss.get('message')}")
                connections.append(vss)
                
                # データを追加してアクティブに使用
                doc = {
                    "id": f"cleanup_{i:03d}",
                    "content": f"クリーンアップテスト {i}"
                }
                vss.index([doc])
                
                log("info", {
                    "message": "Created multiple connections",
                    "count": len(connections)
                })
                
                # すべての接続を閉じる
                for i, vss in enumerate(connections):
                    if hasattr(vss, 'close'):
                        vss.close()
                        log("info", {
                            "message": "Closed connection",
                            "index": i
                        })
                
                # ガベージコレクションを強制実行
                gc.collect()
                
                # 新しい接続が作成できることを確認（リソースが解放されている）
                new_vss = create_vss(db_path=db_dir, in_memory=False)
                if isinstance(new_vss, dict) and new_vss.get('type'):
                    pytest.skip(f"VECTOR extension not available: {new_vss.get('message')}")
                
                # 新しい接続でデータを確認
                search_result = new_vss.search("クリーンアップテスト", limit=10)
                assert search_result.get('ok'), "New connection should work after cleanup"
                
                # 以前のデータが存在することを確認
                results = search_result.get('results', [])
                log("info", {
                    "message": "Found documents after cleanup",
                    "count": len(results)
                })
                
                # 少なくとも作成したドキュメントの一部が見つかることを確認
                assert len(results) > 0, "Should find previously indexed documents"
                
                # クリーンアップ
                if hasattr(new_vss, 'close'):
                    new_vss.close()