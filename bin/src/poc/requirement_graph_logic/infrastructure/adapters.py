"""インフラストラクチャ層のアダプター（外部依存の実装）"""

from typing import List, Dict
import math
import random
from datetime import datetime
from ..domain.types import (
    RequirementDict, ErrorDict, EmbeddingDict, 
    RequirementRepositoryPort, EmbedderPort,
    validate_embedding
)


class InMemoryRequirementRepository:
    """インメモリ要件リポジトリ（テスト用実装）"""
    
    def __init__(self):
        self.requirements: Dict[str, RequirementDict] = {}
    
    def save(self, requirement: RequirementDict) -> str | ErrorDict:
        """要件を保存"""
        try:
            req_id = requirement["id"]
            self.requirements[req_id] = requirement
            return req_id
        except Exception as e:
            return {"error": str(e), "code": "SAVE_ERROR", "details": None}
    
    def find_by_id(self, requirement_id: str) -> RequirementDict | ErrorDict:
        """IDで要件を検索"""
        if requirement_id in self.requirements:
            return self.requirements[requirement_id]
        return {"error": f"Requirement {requirement_id} not found", "code": "NOT_FOUND", "details": None}
    
    def find_similar(self, embedding: EmbeddingDict, limit: int) -> List[RequirementDict] | ErrorDict:
        """類似要件を検索（簡易版：全件からコサイン類似度計算）"""
        try:
            if not self.requirements:
                return []
            
            # 全要件との類似度を計算
            similarities = []
            for req_id, req in self.requirements.items():
                similarity = _cosine_similarity(embedding["vector"], req["embedding"]["vector"])
                similarities.append((req, similarity))
            
            # 類似度でソートして上位を返す
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [req for req, _ in similarities[:limit]]
            
        except Exception as e:
            return {"error": str(e), "code": "SEARCH_ERROR", "details": None}


class SimpleEmbedder:
    """シンプルな埋め込み生成器（テスト用実装）"""
    
    def __init__(self, dimension: int = 3):
        self.dimension = dimension
        self.model_name = "simple-embedder"
    
    def embed(self, text: str) -> EmbeddingDict | ErrorDict:
        """テキストから埋め込みを生成（簡易版：文字列ハッシュベース）"""
        try:
            # 簡易実装：文字列のハッシュ値から決定的なベクトルを生成
            hash_val = hash(text)
            random.seed(abs(hash_val) % 2**32)
            vector = [random.gauss(0, 1) for _ in range(self.dimension)]
            # 正規化
            norm = math.sqrt(sum(v * v for v in vector))
            if norm > 0:
                vector = [v / norm for v in vector]
            
            embedding: EmbeddingDict = {
                "vector": vector,
                "model_name": self.model_name,
                "dimension": self.dimension
            }
            
            # バリデーション
            error = validate_embedding(embedding)
            if error:
                return {"error": error, "code": "VALIDATION_ERROR", "details": None}
            
            return embedding
            
        except Exception as e:
            return {"error": str(e), "code": "EMBED_ERROR", "details": None}


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """コサイン類似度を計算"""
    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    norm1 = math.sqrt(sum(v * v for v in vec1))
    norm2 = math.sqrt(sum(v * v for v in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def create_in_memory_repository() -> RequirementRepositoryPort:
    """インメモリリポジトリを作成（高階関数パターン）"""
    return InMemoryRequirementRepository()


def create_simple_embedder(dimension: int = 3) -> EmbedderPort:
    """シンプル埋め込み器を作成（高階関数パターン）"""
    return SimpleEmbedder(dimension)


# ===== テストコード（規約: in-sourceテスト） =====

def test_in_memory_repository_save_and_find_returns_requirement():
    """リポジトリ_保存と検索_要件を返す"""
    from ..domain.types import create_requirement, create_embedding
    
    repo = create_in_memory_repository()
    req = create_requirement("テスト要件", create_embedding([1.0, 0.0, 0.0]))
    
    # 保存
    result = repo.save(req)
    assert isinstance(result, str)
    assert result == req["id"]
    
    # 検索
    found = repo.find_by_id(req["id"])
    assert "error" not in found
    assert found["text"] == "テスト要件"


def test_in_memory_repository_find_nonexistent_returns_error():
    """リポジトリ_存在しないID検索_エラー"""
    repo = create_in_memory_repository()
    result = repo.find_by_id("NONEXISTENT")
    assert "error" in result
    assert result["code"] == "NOT_FOUND"


def test_in_memory_repository_find_similar_empty_returns_empty_list():
    """リポジトリ_類似検索（空）_空リスト"""
    from ..domain.types import create_embedding
    
    repo = create_in_memory_repository()
    embedding = create_embedding([1.0, 0.0, 0.0])
    result = repo.find_similar(embedding, limit=10)
    assert isinstance(result, list)
    assert len(result) == 0


def test_in_memory_repository_find_similar_returns_sorted_by_similarity():
    """リポジトリ_類似検索_類似度順"""
    from ..domain.types import create_requirement, create_embedding
    
    repo = create_in_memory_repository()
    
    # 3つの要件を追加（類似度が異なる）
    req1 = create_requirement("要件1", create_embedding([1.0, 0.0, 0.0]))
    req2 = create_requirement("要件2", create_embedding([0.9, 0.1, 0.0]))  # req1に近い
    req3 = create_requirement("要件3", create_embedding([0.0, 1.0, 0.0]))  # req1と直交
    
    repo.save(req1)
    repo.save(req2)
    repo.save(req3)
    
    # req1の埋め込みで検索
    result = repo.find_similar(req1["embedding"], limit=3)
    assert len(result) == 3
    assert result[0]["text"] == "要件1"  # 自分自身が最も類似
    assert result[1]["text"] == "要件2"  # 次に類似
    assert result[2]["text"] == "要件3"  # 最も非類似


def test_simple_embedder_generates_deterministic_embedding():
    """埋め込み生成_同じテキスト_同じベクトル"""
    embedder = create_simple_embedder()
    
    result1 = embedder.embed("テスト文書")
    result2 = embedder.embed("テスト文書")
    
    assert "error" not in result1
    assert "error" not in result2
    assert result1["vector"] == result2["vector"]


def test_simple_embedder_different_text_different_embedding():
    """埋め込み生成_異なるテキスト_異なるベクトル"""
    embedder = create_simple_embedder()
    
    result1 = embedder.embed("テスト文書1")
    result2 = embedder.embed("テスト文書2")
    
    assert "error" not in result1
    assert "error" not in result2
    assert result1["vector"] != result2["vector"]


def test_simple_embedder_normalized_vectors():
    """埋め込み生成_正規化_単位ベクトル"""
    embedder = create_simple_embedder()
    
    result = embedder.embed("テスト")
    assert "error" not in result
    
    norm = math.sqrt(sum(v * v for v in result["vector"]))
    assert abs(norm - 1.0) < 1e-6  # 単位ベクトル