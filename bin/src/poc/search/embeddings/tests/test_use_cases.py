#!/usr/bin/env python3
"""ユースケース層のテスト - RED段階"""

import pytest
from embeddings.application import (
    SearchSimilarDocumentsUseCase,
    IndexDocumentsUseCase,
    DocumentSearchResult,
    Document
)


class TestSearchSimilarDocumentsUseCase:
    """類似文書検索ユースケースのテスト"""
    
    def test_日本語テキスト検索ユースケース(self, mock_dependencies):
        """日本語クエリで意味的に類似した文書が検索されること"""
        use_case = SearchSimilarDocumentsUseCase(
            embedding_model=mock_dependencies["model"],
            vector_repository=mock_dependencies["repo"]
        )
        
        result = use_case.execute(
            query="瑠璃色はどんな色？",
            k=3
        )
        
        assert result.ok is True
        assert len(result.documents) == 3
        # 最も類似度が高い文書に「瑠璃」が含まれること
        assert "瑠璃" in result.documents[0].content
        # スコア順にソートされていること
        scores = [doc.similarity_score for doc in result.documents]
        assert scores == sorted(scores, reverse=True)
    
    def test_空のクエリでのエラーハンドリング(self, mock_dependencies):
        """空のクエリが適切にエラーとして扱われること"""
        use_case = SearchSimilarDocumentsUseCase(
            embedding_model=mock_dependencies["model"],
            vector_repository=mock_dependencies["repo"]
        )
        
        result = use_case.execute(query="", k=3)
        
        assert result.ok is False
        assert "empty query" in result.error.lower()


class TestIndexDocumentsUseCase:
    """文書インデックス作成ユースケースのテスト"""
    
    def test_複数文書の一括インデックス作成(self, mock_dependencies):
        """複数の文書が一括でインデックスに追加されること"""
        use_case = IndexDocumentsUseCase(
            embedding_model=mock_dependencies["model"],
            vector_repository=mock_dependencies["repo"]
        )
        
        documents = [
            Document(id=1, content="瑠璃色は紫みを帯びた濃い青"),
            Document(id=2, content="サーファーが海辺にいる"),
            Document(id=3, content="今日は良い天気です"),
        ]
        
        result = use_case.execute(documents)
        
        assert result.ok is True
        assert result.indexed_count == 3
        assert result.failed_count == 0
    
    def test_空の文書リストでのエラーハンドリング(self, mock_dependencies):
        """空の文書リストが適切にエラーとして扱われること"""
        use_case = IndexDocumentsUseCase(
            embedding_model=mock_dependencies["model"],
            vector_repository=mock_dependencies["repo"]
        )
        
        result = use_case.execute([])
        
        assert result.ok is False
        assert "no documents" in result.error.lower()


@pytest.fixture
def mock_dependencies():
    """モックの依存関係"""
    class MockEmbeddingModel:
        def encode(self, request):
            return type('', (), {'embeddings': [0.1] * 256, 'dimension': 256})()
        
        def encode_batch(self, requests):
            return [self.encode(r) for r in requests]
    
    class MockVectorRepository:
        def query_index(self, index_name, query_vector, k):
            return type('', (), {
                'ok': True,
                'results': [
                    {'id': 1, 'content': '瑠璃色の説明', 'distance': 0.1},
                    {'id': 2, 'content': '別の文書', 'distance': 0.5},
                    {'id': 3, 'content': 'さらに別の文書', 'distance': 0.8},
                ][:k]
            })()
        
        def insert_documents(self, documents):
            return type('', (), {'ok': True, 'inserted_count': len(documents)})()
    
    return {
        "model": MockEmbeddingModel(),
        "repo": MockVectorRepository()
    }