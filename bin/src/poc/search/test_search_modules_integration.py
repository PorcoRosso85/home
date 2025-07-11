#!/usr/bin/env python3
"""
search/vssの統合テスト
embeddingsから移行後も全機能が正しく動作することを確認
"""

import pytest
import sys
import os
from pathlib import Path

# モジュールパスを追加
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "vss"))
sys.path.insert(0, str(current_dir))


class TestVSSIntegration:
    """VSS統合テスト"""
    
    def test_vss_module_imports(self):
        """VSSモジュールが正しくインポートできること"""
        # VSSモジュールのインポート
        from vss import VectorSearchSystem, create_embedding_model
        from vss.domain import EmbeddingRequest, EmbeddingType
        
        # システムの作成
        system = VectorSearchSystem(db_path=":memory:")
        assert system is not None
    
    def test_embedding_model_functionality(self):
        """埋め込みモデルの機能が維持されていること"""
        # VSSモジュールからのインポート
        from vss.infrastructure import create_embedding_model
        from vss.domain import EmbeddingRequest, EmbeddingType
        
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
    
    def test_vector_search_functionality(self):
        """ベクトル検索機能が維持されていること"""
        from vss import VectorSearchSystem
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # システムの初期化
            system = VectorSearchSystem(db_path=tmpdir)
            
            # 文書のインデックス
            docs = ["テスト文書1", "テスト文書2"]
            result = system.index_documents(docs)
            assert result.ok is True
            assert result.indexed_count == 2
            
            # 検索
            search_result = system.search("テスト", k=1)
            assert search_result.ok is True
    
    def test_kuzu_vector_repository(self):
        """KuzuDBベクトルリポジトリが動作すること"""
        from vss.infrastructure.kuzu import KuzuVectorRepository
        import kuzu
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # KuzuDB接続
            db = kuzu.Database(tmpdir)
            conn = kuzu.Connection(db)
            
            # リポジトリの作成
            repo = KuzuVectorRepository(conn)
            assert repo is not None
    
    @pytest.mark.parametrize("query_text", [
        "要件管理システム",
        "AIによる検索",
        "ベクトル類似度",
        "日本語の意味検索",
    ])
    def test_japanese_text_processing(self, query_text):
        """日本語テキストが正しく処理できること"""
        from vss.infrastructure import create_embedding_model
        from vss.domain import EmbeddingRequest, EmbeddingType
        
        # VSSモジュール（Ruri実装）
        model = create_embedding_model("ruri-v3-30m")
        request = EmbeddingRequest(text=query_text, embedding_type=EmbeddingType.QUERY)
        result = model.encode(request)
        assert len(result.embeddings) == 256
        assert all(isinstance(v, float) for v in result.embeddings)


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