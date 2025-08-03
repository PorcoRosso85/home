#!/usr/bin/env python3
"""
SearchAdapter互換機能の実装テスト

requirement/graphのSearchAdapterが依存する機能をVSS_KUZUが
正しく提供することを検証する。
"""

import pytest
import tempfile
import os
from typing import Dict, Any, List
from log_py import log


class TestSearchAdapterCompatibility:
    """SearchAdapter互換機能のテストクラス"""
    
    @pytest.fixture
    def vss_instance(self):
        """VSSインスタンスを作成するフィクスチャ"""
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            try:
                vss = create_vss(db_path=db_dir, in_memory=False)
                yield vss
            except RuntimeError as e:
                log("warning", {
                    "message": "Failed to create VSS instance",
                    "error": str(e),
                    "reason": "VECTOR extension might not be available"
                })
                pytest.skip(f"VECTOR extension not available: {e}")
    
    def test_add_to_index_functionality(self, vss_instance):
        """add_to_indexに相当する機能が正常動作"""
        log("info", {
            "message": "Testing add_to_index functionality",
            "test": "test_add_to_index_functionality"
        })
        
        # requirement形式のドキュメント追加
        requirement_doc = {
            "id": "auth_001",
            "title": "ユーザー認証機能",
            "description": "安全なログイン機能を提供"
        }
        
        # VSS_KUZUではcontentフィールドを使用するため変換
        vss_doc = {
            "id": requirement_doc["id"],
            "content": f"{requirement_doc['title']} {requirement_doc['description']}"
        }
        
        # インデックスに追加
        result = vss_instance.index([vss_doc])
        
        log("info", {
            "message": "Index result",
            "ok": result.get('ok'),
            "error": result.get('error')
        })
        
        assert result.get('ok'), f"Failed to add to index: {result}"
        
        # 追加されたドキュメントが検索可能であることを確認
        search_result = vss_instance.search("ユーザー認証", limit=5)
        assert search_result.get('ok'), f"Search failed: {search_result}"
        
        # 結果にドキュメントが含まれることを確認
        found = False
        for res in search_result.get('results', []):
            if res.get('id') == requirement_doc['id']:
                found = True
                log("info", {
                    "message": "Document found in index",
                    "id": res.get('id'),
                    "content": res.get('content'),
                    "score": res.get('score')
                })
                break
        
        assert found, f"Document {requirement_doc['id']} not found in index"
        
        # 複数のドキュメントを一度に追加
        multiple_docs = [
            {
                "id": "auth_002",
                "title": "パスワードリセット機能",
                "description": "ユーザーがパスワードをリセットできる機能"
            },
            {
                "id": "auth_003",
                "title": "二要素認証",
                "description": "セキュリティ強化のための二要素認証機能"
            }
        ]
        
        vss_docs = []
        for doc in multiple_docs:
            vss_docs.append({
                "id": doc["id"],
                "content": f"{doc['title']} {doc['description']}"
            })
        
        multi_result = vss_instance.index(vss_docs)
        assert multi_result.get('ok'), f"Failed to add multiple documents: {multi_result}"
        
        log("info", {
            "message": "Multiple documents added successfully",
            "count": len(vss_docs)
        })
    
    def test_search_similar_functionality(self, vss_instance):
        """search_similarに相当する機能の完全テスト"""
        log("info", {
            "message": "Testing search_similar functionality",
            "test": "test_search_similar_functionality"
        })
        
        # テスト用のドキュメントを準備
        test_docs = [
            {
                "id": "req_001",
                "content": "ユーザー認証機能 セキュアなログイン実装"
            },
            {
                "id": "req_002",
                "content": "商品検索機能 キーワードによる商品検索"
            },
            {
                "id": "req_003",
                "content": "認証システム パスワード管理機能"
            },
            {
                "id": "req_004",
                "content": "在庫管理システム 商品の在庫確認"
            },
            {
                "id": "req_005",
                "content": "ログイン履歴 認証ログの記録"
            }
        ]
        
        # すべてのドキュメントをインデックスに追加
        for doc in test_docs:
            result = vss_instance.index([doc])
            assert result.get('ok'), f"Failed to index document {doc['id']}: {result}"
        
        # k件の類似文書取得テスト
        search_query = "ユーザー認証とセキュリティ"
        k_values = [1, 3, 5, 10]
        
        for k in k_values:
            search_result = vss_instance.search(search_query, limit=k)
            
            assert search_result.get('ok'), f"Search failed for k={k}: {search_result}"
            results = search_result.get('results', [])
            
            # 返される結果の数がk以下であることを確認
            assert len(results) <= k, f"Expected at most {k} results, got {len(results)}"
            
            log("info", {
                "message": f"Search results for k={k}",
                "query": search_query,
                "num_results": len(results),
                "results": [{"id": r.get('id'), "score": r.get('score')} for r in results]
            })
        
        # スコアの妥当性確認
        search_result = vss_instance.search(search_query, limit=5)
        results = search_result.get('results', [])
        
        if len(results) >= 2:
            # スコアが降順にソートされていることを確認
            scores = [r.get('score', 0.0) for r in results]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], \
                    f"Scores should be in descending order: {scores}"
            
            # 認証関連のドキュメントが上位に来ることを確認
            top_ids = [r.get('id') for r in results[:3]]
            auth_related_ids = ['req_001', 'req_003', 'req_005']
            auth_in_top = sum(1 for id in top_ids if id in auth_related_ids)
            
            log("info", {
                "message": "Relevance check",
                "top_3_ids": top_ids,
                "auth_related_in_top_3": auth_in_top
            })
            
            # 少なくとも1つの認証関連ドキュメントが上位3件に含まれることを期待
            assert auth_in_top >= 1, \
                f"Expected auth-related documents in top results, got {top_ids}"
    
    def test_empty_index_search(self, vss_instance):
        """空のインデックスでの検索が適切に処理される"""
        log("info", {
            "message": "Testing search on empty index",
            "test": "test_empty_index_search"
        })
        
        # 空のインデックスで検索を実行
        search_result = vss_instance.search("存在しないコンテンツ", limit=5)
        
        # 検索がエラーなく完了することを確認
        assert search_result.get('ok') is not False, \
            f"Search should complete without error: {search_result}"
        
        # 結果が空であることを確認
        results = search_result.get('results', [])
        assert isinstance(results, list), "Results should be a list"
        assert len(results) == 0, f"Expected empty results, got {len(results)} items"
        
        log("info", {
            "message": "Empty index search completed",
            "ok": search_result.get('ok'),
            "num_results": len(results)
        })
        
        # 検索後にドキュメントを追加して、正常に動作することを確認
        doc = {
            "id": "after_empty_001",
            "content": "空のインデックス後に追加されたドキュメント"
        }
        
        index_result = vss_instance.index([doc])
        assert index_result.get('ok'), f"Failed to index after empty search: {index_result}"
        
        # 追加後の検索が正常に動作することを確認
        new_search_result = vss_instance.search("追加されたドキュメント", limit=5)
        assert new_search_result.get('ok'), f"Search failed after indexing: {new_search_result}"
        
        new_results = new_search_result.get('results', [])
        assert len(new_results) > 0, "Should find the newly added document"
        
        found = any(r.get('id') == 'after_empty_001' for r in new_results)
        assert found, "Newly added document should be searchable"
        
        log("info", {
            "message": "Document searchable after empty index",
            "doc_id": doc['id'],
            "found": found
        })