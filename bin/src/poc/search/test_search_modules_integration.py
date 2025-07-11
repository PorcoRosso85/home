#!/usr/bin/env python3
"""
search/vssとsearch/embeddingsの統合テスト
両モジュールが独立して正しく動作することを確認
"""

import pytest
import sys
import os
from pathlib import Path

# モジュールパスを追加
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "vss"))
sys.path.insert(0, str(current_dir / "embeddings"))
sys.path.insert(0, str(current_dir))


class TestSearchModulesIntegration:
    """検索モジュールの統合テスト"""
    
    def test_vss_module_imports(self):
        """VSSモジュールが正しくインポートできること"""
        # VSSモジュールのインポート
        from requirement_embedder import generate_requirement_embedding
        from similarity_search import search_similar_requirements
        
        # 基本的な動作確認
        embedding = generate_requirement_embedding({
            "title": "テスト要件",
            "description": "これはテストです"
        })
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # VSSは384次元
    
    def test_embeddings_module_imports(self):
        """Embeddingsモジュールが正しくインポートできること"""
        # Embeddingsモジュールのインポート
        from infrastructure import create_embedding_model
        from domain import EmbeddingRequest, EmbeddingType
        
        # モデルの作成
        model = create_embedding_model("ruri-v3-30m")
        
        # 基本的な動作確認
        request = EmbeddingRequest(
            text="テストテキスト",
            embedding_type=EmbeddingType.DOCUMENT
        )
        result = model.encode(request)
        
        assert result.embeddings is not None
        assert len(result.embeddings) == 256  # Ruriは256次元
    
    def test_dimension_compatibility(self):
        """両モジュールのベクトル次元の違いを確認"""
        from requirement_embedder import generate_requirement_embedding
        from infrastructure import create_embedding_model
        from domain import EmbeddingRequest, EmbeddingType
        
        # VSSの埋め込み（384次元）
        vss_embedding = generate_requirement_embedding({"title": "test"})
        
        # Embeddingsの埋め込み（256次元）
        model = create_embedding_model("ruri-v3-30m")
        request = EmbeddingRequest(text="test", embedding_type=EmbeddingType.DOCUMENT)
        embeddings_result = model.encode(request)
        
        # 次元数の確認
        assert len(vss_embedding) == 384
        assert len(embeddings_result.embeddings) == 256
        
        # 両者は異なる次元数を持つことを確認
        assert len(vss_embedding) != len(embeddings_result.embeddings)
    
    def test_mock_vs_real_implementation(self):
        """モック実装と実装の違いを確認"""
        from requirement_embedder import generate_requirement_embedding
        
        # 同じ入力に対して同じ出力を返すか確認（モック）
        text = {"title": "同じテキスト"}
        embedding1 = generate_requirement_embedding(text)
        embedding2 = generate_requirement_embedding(text)
        
        # モック実装は決定的（同じ入力→同じ出力）
        assert embedding1 == embedding2
        
        # 実際のモデルは少し異なる可能性がある（ここではテストしない）
    
    @pytest.mark.parametrize("query_text", [
        "要件管理システム",
        "AIによる検索",
        "ベクトル類似度",
        "日本語の意味検索",
    ])
    def test_both_modules_handle_japanese(self, query_text):
        """両モジュールが日本語を処理できること"""
        from requirement_embedder import generate_requirement_embedding
        from infrastructure import create_embedding_model
        from domain import EmbeddingRequest, EmbeddingType
        
        # VSSモジュール
        vss_embedding = generate_requirement_embedding({"title": query_text})
        assert len(vss_embedding) == 384
        
        # Embeddingsモジュール
        model = create_embedding_model("ruri-v3-30m")
        request = EmbeddingRequest(text=query_text, embedding_type=EmbeddingType.QUERY)
        result = model.encode(request)
        assert len(result.embeddings) == 256


class TestHybridSearchConcept:
    """ハイブリッド検索のコンセプトテスト"""
    
    def test_search_result_structure(self):
        """統合検索結果の構造を定義"""
        # 将来的な統合検索結果の構造
        expected_result = {
            "id": "req_001",
            "content": "要件の内容",
            "keyword_score": 0.8,  # BM25スコア
            "vector_score": 0.9,   # コサイン類似度
            "combined_score": 0.87,  # 重み付け統合
            "source": "hybrid",  # 検索ソース
        }
        
        # 構造の検証（将来の実装のためのプレースホルダー）
        assert "keyword_score" in expected_result
        assert "vector_score" in expected_result
        assert "combined_score" in expected_result
    
    def test_score_fusion_concept(self):
        """スコア統合のコンセプト"""
        # 仮想的なスコア統合
        keyword_score = 0.6
        vector_score = 0.9
        keyword_weight = 0.3
        vector_weight = 0.7
        
        # 重み付け平均
        combined_score = (
            keyword_score * keyword_weight + 
            vector_score * vector_weight
        )
        
        assert combined_score == pytest.approx(0.81, rel=1e-2)
    
    def test_result_deduplication_concept(self):
        """重複除去のコンセプト"""
        # 同じドキュメントが両方の検索で見つかった場合
        keyword_results = [
            {"id": "doc1", "score": 0.8},
            {"id": "doc2", "score": 0.7},
        ]
        
        vector_results = [
            {"id": "doc1", "score": 0.9},  # doc1は重複
            {"id": "doc3", "score": 0.85},
        ]
        
        # 重複除去と統合（概念的な実装）
        merged = {}
        for result in keyword_results:
            merged[result["id"]] = {"keyword": result["score"]}
        
        for result in vector_results:
            if result["id"] in merged:
                merged[result["id"]]["vector"] = result["score"]
            else:
                merged[result["id"]] = {"vector": result["score"]}
        
        # doc1は両方のスコアを持つ
        assert "keyword" in merged["doc1"]
        assert "vector" in merged["doc1"]
        
        # doc2はキーワードのみ、doc3はベクトルのみ
        assert "keyword" in merged["doc2"]
        assert "vector" not in merged["doc2"]
        assert "vector" in merged["doc3"]
        assert "keyword" not in merged["doc3"]


if __name__ == "__main__":
    # 直接実行時のテスト
    pytest.main([__file__, "-v"])