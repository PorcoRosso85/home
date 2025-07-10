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


