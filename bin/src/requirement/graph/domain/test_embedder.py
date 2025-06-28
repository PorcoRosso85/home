"""
Tests for Embedder
"""
from .embedder import create_embedding


def test_create_embedding_valid_text_returns_normalized_vector():
    """create_embedding_正常テキスト_正規化ベクトルを返す"""
    result = create_embedding("Hello World")
    
    assert isinstance(result, list)
    assert len(result) == 50
    
    # 正規化されていることを確認
    norm = sum(x*x for x in result) ** 0.5
    assert abs(norm - 1.0) < 0.01


def test_create_embedding_same_input_returns_same_output():
    """create_embedding_同一入力_同一出力を返す"""
    text = "KuzuDB migration for relationship queries"
    embed1 = create_embedding(text)
    embed2 = create_embedding(text)
    
    assert isinstance(embed1, list)
    assert isinstance(embed2, list)
    assert embed1 == embed2


def test_create_embedding_empty_text_returns_error():
    """create_embedding_空テキスト_エラーを返す"""
    result = create_embedding("")
    
    assert isinstance(result, dict)
    assert result["type"] == "EmbeddingError"
    
    result2 = create_embedding("   ")
    assert isinstance(result2, dict)
    assert result2["type"] == "EmbeddingError"


def test_create_embedding_similar_texts_returns_higher_similarity():
    """create_embedding_類似テキスト_高い類似度を返す"""
    embed1 = create_embedding("database migration")
    embed2 = create_embedding("database movement")
    embed3 = create_embedding("completely different topic")
    
    # コサイン類似度計算
    def cosine_sim(a, b):
        return sum(x*y for x, y in zip(a, b))
    
    if isinstance(embed1, list) and isinstance(embed2, list) and isinstance(embed3, list):
        sim12 = cosine_sim(embed1, embed2)
        sim13 = cosine_sim(embed1, embed3)
        
        # 類似テキストの方が高い類似度
        assert sim12 > sim13