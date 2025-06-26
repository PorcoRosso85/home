"""
Embedder - 軽量な埋め込み生成ロジック
外部依存: なし（純粋Python実装）
"""
from typing import List, Union
from .types import EmbeddingError


def create_embedding(text: str) -> Union[List[float], EmbeddingError]:
    """
    テキストから50次元の埋め込みベクトルを生成
    
    Simple deterministic embedder:
    - 文字頻度ベース
    - 単語長統計
    - n-gram特徴
    
    Args:
        text: 埋め込みを生成するテキスト
        
    Returns:
        50次元のベクトル または EmbeddingError
    """
    if not text or len(text.strip()) == 0:
        return {
            "type": "EmbeddingError",
            "message": "Empty text cannot be embedded",
            "text": text
        }
    
    # 前処理
    text_lower = text.lower()
    words = text_lower.split()
    
    # 50次元の特徴ベクトル初期化
    embedding = [0.0] * 50
    
    # 1. 文字頻度特徴 (0-25: a-z頻度)
    for char in text_lower:
        if 'a' <= char <= 'z':
            idx = ord(char) - ord('a')
            embedding[idx] += 1
    
    # 正規化
    char_total = sum(embedding[:26])
    if char_total > 0:
        for i in range(26):
            embedding[i] /= char_total
    
    # 2. 単語統計特徴 (26-35)
    if words:
        embedding[26] = len(words) / 100.0  # 単語数
        embedding[27] = sum(len(w) for w in words) / len(words) / 20.0  # 平均単語長
        embedding[28] = len(set(words)) / len(words)  # ユニーク単語率
    
    # 3. 2-gram特徴 (36-49)
    bigrams = []
    for i in range(len(text_lower) - 1):
        if text_lower[i].isalpha() and text_lower[i+1].isalpha():
            bigrams.append(text_lower[i:i+2])
    
    # 頻出2-gramをハッシュして配置
    for bigram in set(bigrams):
        idx = 36 + (hash(bigram) % 14)
        embedding[idx] += bigrams.count(bigram) / max(len(bigrams), 1)
    
    # 最終正規化
    norm = sum(x*x for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]
    
    return embedding


# Test cases
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
