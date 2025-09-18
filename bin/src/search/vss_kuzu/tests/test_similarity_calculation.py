#!/usr/bin/env python3
"""
類似度計算の検証テスト

VSS_KUZUの類似度計算が正しく動作することを検証する。
特に日本語テキストでの類似度計算に焦点を当てる。
"""

import pytest
import tempfile
import os
from typing import Dict, Any, List
from log_py import log


class TestSimilarityCalculation:
    """類似度計算のテストクラス"""
    
    @pytest.fixture
    def vss_instance(self):
        """VSSインスタンスを作成するフィクスチャ"""
        from vss_kuzu import create_vss
        
        with tempfile.TemporaryDirectory() as db_dir:
            os.environ['RGL_DATABASE_PATH'] = db_dir
            vss = create_vss(db_path=db_dir, in_memory=False)
            if isinstance(vss, dict) and vss.get('type'):
                pytest.skip(f"VECTOR extension not available: {vss.get('message')}")
            yield vss
    
    def test_similarity_score_not_zero_for_similar_texts(self, vss_instance):
        """類似テキストの類似度スコアが0.0にならないことを確認"""
        # 日本語テキストでのテスト必須
        log("info", {
            "message": "Testing similarity score for similar Japanese texts",
            "test": "test_similarity_score_not_zero_for_similar_texts"
        })
        
        # ドキュメントをインデックスに追加
        doc = {
            "id": "auth_001",
            "content": "ユーザー認証機能 安全なログイン機能を提供"
        }
        index_result = vss_instance.index([doc])
        
        assert index_result.get('ok'), f"Failed to index document: {index_result}"
        
        # 類似したテキストで検索
        search_query = "ユーザー認証システム セキュアなログイン実装"
        search_result = vss_instance.search(search_query, limit=5)
        
        assert search_result.get('ok'), f"Search failed: {search_result}"
        assert search_result.get('results'), "No results found"
        
        # スコアが0.0でないことを確認
        for result in search_result['results']:
            score = result.get('score', 0.0)
            log("info", {
                "message": "Found similar document",
                "id": result.get('id'),
                "score": score,
                "content": result.get('content')
            })
            assert score > 0.0, f"Similarity score should not be 0.0, got {score}"
    
    def test_exact_match_returns_high_similarity(self, vss_instance):
        """完全一致テキストが高い類似度を返すことを確認"""
        log("info", {
            "message": "Testing exact match similarity",
            "test": "test_exact_match_returns_high_similarity"
        })
        
        # ドキュメントをインデックスに追加
        content = "完全に一致するテキストのテスト"
        doc = {
            "id": "exact_001",
            "content": content
        }
        index_result = vss_instance.index([doc])
        
        assert index_result.get('ok'), f"Failed to index document: {index_result}"
        
        # 完全に同じテキストで検索
        search_result = vss_instance.search(content, limit=1)
        
        assert search_result.get('ok'), f"Search failed: {search_result}"
        assert search_result.get('results'), "No results found"
        
        # 最高スコアを確認（通常1.0に近い値）
        top_result = search_result['results'][0]
        score = top_result.get('score', 0.0)
        log("info", {
            "message": "Exact match result",
            "score": score,
            "expected": "close to 1.0"
        })
        
        # 完全一致は非常に高いスコアを返すべき
        assert score > 0.95, f"Exact match should return very high score, got {score}"
    
    def test_semantic_similarity_works_correctly(self, vss_instance):
        """意味的に類似したテキストが適切にランク付けされることを確認"""
        log("info", {
            "message": "Testing semantic similarity ranking",
            "test": "test_semantic_similarity_works_correctly"
        })
        
        # 複数の関連ドキュメントをインデックスに追加
        docs = [
            {
                "id": "auth_001",
                "content": "ユーザー認証とログイン機能"
            },
            {
                "id": "auth_002", 
                "content": "セキュアな認証システムの実装"
            },
            {
                "id": "unrelated_001",
                "content": "天気予報と気象情報の提供"
            },
            {
                "id": "auth_003",
                "content": "パスワード管理と認証フロー"
            }
        ]
        
        for doc in docs:
            index_result = vss_instance.index([doc])
            assert index_result.get('ok'), f"Failed to index document {doc['id']}: {index_result}"
        
        # 認証関連のクエリで検索
        search_query = "認証機能とセキュリティ"
        search_result = vss_instance.search(search_query, limit=10)
        
        assert search_result.get('ok'), f"Search failed: {search_result}"
        assert search_result.get('results'), "No results found"
        
        # 結果を分析
        auth_scores = []
        unrelated_scores = []
        
        for result in search_result['results']:
            doc_id = result.get('id')
            score = result.get('score', 0.0)
            
            log("info", {
                "message": "Search result",
                "id": doc_id,
                "score": score,
                "content": result.get('content')
            })
            
            if 'auth' in doc_id:
                auth_scores.append(score)
            elif 'unrelated' in doc_id:
                unrelated_scores.append(score)
        
        # 認証関連のドキュメントが高いスコアを持つことを確認
        if auth_scores and unrelated_scores:
            avg_auth_score = sum(auth_scores) / len(auth_scores)
            avg_unrelated_score = sum(unrelated_scores) / len(unrelated_scores)
            
            log("info", {
                "message": "Average scores comparison",
                "auth_related_avg": avg_auth_score,
                "unrelated_avg": avg_unrelated_score
            })
            
            assert avg_auth_score > avg_unrelated_score, \
                f"Auth-related docs should have higher scores. Auth: {avg_auth_score}, Unrelated: {avg_unrelated_score}"