#!/usr/bin/env python3
"""
ドメイン層のテスト - ビジネスロジック関連
埋め込み生成、距離計算、類似度スコアリングなど
"""

import pytest
from typing import List, Tuple

from vss_kuzu.domain import (
    calculate_cosine_similarity,
    cosine_distance_to_similarity,
    sort_results_by_similarity,
    select_top_k_results,
    find_semantically_similar_documents,
    validate_embedding_dimension,
    group_documents_by_topic_similarity,
    SearchResult
)


class TestDomain:
    """ドメインロジックのテストクラス"""
    
    def test_vector_search_returns_semantically_similar_documents(self):
        """ベクトル検索が意味的に類似したドキュメントを返すこと"""
        # 類似性の異なるドキュメントを準備（ダミー埋め込み）
        # 実際の環境では埋め込みモデルが生成するが、テストでは手動で設定
        doc_embeddings = [
            ("REQ001", "ユーザー認証機能を実装する", [0.8, 0.2, 0.1]),
            ("REQ002", "ログインシステムを構築する", [0.7, 0.3, 0.1]),  # REQ001と類似
            ("REQ003", "データベースを設計する", [0.1, 0.1, 0.9]),      # 無関係
        ]
        
        # クエリの埋め込み（認証システムに関連）
        query_embedding = [0.75, 0.25, 0.1]
        
        # 検索実行
        results = find_semantically_similar_documents(
            query_embedding,
            doc_embeddings,
            limit=3
        )
        
        # 検証
        assert len(results) == 3
        
        # 認証系のドキュメントが上位2件に含まれること
        top_2_ids = [r.id for r in results[:2]]
        assert set(top_2_ids) == {"REQ001", "REQ002"}
        
        # データベース系が最下位であること
        assert results[-1].id == "REQ003"
        
        # スコアが降順であること
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_search_converts_distance_to_score_correctly(self):
        """検索が距離をスコアに正しく変換すること（score = 1 - distance）"""
        # 様々な距離値でテスト
        test_cases = [
            (0.0, 1.0),    # 距離0 → スコア1.0
            (0.5, 0.5),    # 距離0.5 → スコア0.5
            (1.0, 0.0),    # 距離1.0 → スコア0.0
            (1.5, -0.5),   # 距離1.5 → スコア-0.5
            (2.0, -1.0),   # 距離2.0 → スコア-1.0
        ]
        
        for distance, expected_score in test_cases:
            score = cosine_distance_to_similarity(distance)
            assert abs(score - expected_score) < 0.0001
    
    def test_search_orders_results_by_similarity(self):
        """検索結果が類似度順で並ぶこと"""
        # 異なるスコアを持つ検索結果を作成
        results = [
            SearchResult("1", "機械学習の基礎", 0.6, 0.4, []),
            SearchResult("2", "機械学習とディープラーニング", 0.9, 0.1, []),
            SearchResult("3", "Python プログラミング", 0.3, 0.7, []),
            SearchResult("4", "機械学習の応用", 0.8, 0.2, []),
            SearchResult("5", "データベース設計", 0.1, 0.9, [])
        ]
        
        # ソート実行
        sorted_results = sort_results_by_similarity(results)
        
        # 検証
        assert len(sorted_results) == 5
        
        # スコアが降順であること
        scores = [r.score for r in sorted_results]
        assert scores == sorted(scores, reverse=True)
        
        # 期待される順序
        expected_order = ["2", "4", "1", "3", "5"]
        actual_order = [r.id for r in sorted_results]
        assert actual_order == expected_order
    
    def test_search_returns_top_k_similar_documents(self):
        """検索が上位k件の類似ドキュメントを返すこと"""
        # テスト用の検索結果（既にソート済み）
        results = [
            SearchResult("1", "最も類似", 0.9, 0.1, []),
            SearchResult("2", "2番目に類似", 0.7, 0.3, []),
            SearchResult("3", "3番目に類似", 0.5, 0.5, []),
            SearchResult("4", "4番目に類似", 0.3, 0.7, []),
            SearchResult("5", "最も類似度が低い", 0.1, 0.9, [])
        ]
        
        # k=2で上位2件を取得
        top_2 = select_top_k_results(results, 2)
        
        # 検証
        assert len(top_2) == 2
        assert top_2[0].id == "1"
        assert top_2[1].id == "2"
        
        # k=0の場合は空リスト
        assert select_top_k_results(results, 0) == []
        
        # k > len(results)の場合は全件
        assert len(select_top_k_results(results, 10)) == 5
    
    def test_indexing_multiple_documents_with_different_topics_succeeds(self):
        """異なるトピックの複数ドキュメントをグループ化できること"""
        # 異なるトピックのドキュメント（ダミー埋め込み）
        documents = [
            ("1", "Pythonプログラミング", [0.9, 0.1, 0.0, 0.0]),
            ("2", "機械学習とディープラーニング", [0.0, 0.9, 0.1, 0.0]),
            ("3", "データベース設計", [0.0, 0.0, 0.9, 0.1]),
            ("4", "Python開発環境", [0.8, 0.2, 0.0, 0.0]),  # 1と類似
            ("5", "深層学習フレームワーク", [0.0, 0.8, 0.2, 0.0])  # 2と類似
        ]
        
        # グループ化実行（閾値0.7）
        groups = group_documents_by_topic_similarity(documents, 0.7)
        
        # 検証
        assert len(groups) == 3  # 3つのトピックグループ
        
        # 各グループのサイズを確認
        group_sizes = sorted([len(g) for g in groups], reverse=True)
        assert group_sizes == [2, 2, 1]  # 2つの2要素グループと1つの1要素グループ
        
        # グループ内のドキュメントが類似していることを確認
        for group in groups:
            if len(group) > 1:
                # グループ内の最初のドキュメントと他のドキュメントの類似度を確認
                base_embedding = group[0][2]
                for _, _, embedding in group[1:]:
                    similarity = calculate_cosine_similarity(base_embedding, embedding)
                    assert similarity >= 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])