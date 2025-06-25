"""ドメインエンティティとデータ型の定義"""

from typing import TypedDict, List, Optional, Protocol
from datetime import datetime


# TypedDictでエンティティ定義
class EmbeddingDict(TypedDict):
    """埋め込みベクトル"""
    vector: List[float]
    model_name: str
    dimension: int


class RequirementDict(TypedDict):
    """要件エンティティ"""
    id: str
    text: str
    embedding: EmbeddingDict
    created_at: datetime
    updated_at: datetime
    metadata: dict


class RelationDict(TypedDict):
    """要件間の関係"""
    from_id: str
    to_id: str
    relation_type: str
    confidence: float
    inferred_at: datetime
    reasoning: str


# 関係タイプ定数
RELATION_DEPENDS_ON = "depends_on"
RELATION_RELATED_TO = "related_to"
RELATION_DUPLICATES = "duplicates"
RELATION_CONFLICTS = "conflicts"


# エラー型
class ErrorDict(TypedDict):
    """エラー情報"""
    error: str
    code: Optional[str]
    details: Optional[dict]


# 操作結果型
class OperationResultDict(TypedDict):
    """操作結果（スコア付き）"""
    success: bool
    operation: str
    scores: dict
    suggestions: List[str]
    warnings: List[str]
    metadata: dict


class AddRequirementResultDict(TypedDict):
    """要件追加結果"""
    requirement_id: str
    scores: dict
    similar_requirements: List[dict]
    suggestions: List[str]


# ポート定義（Protocolを使用）
class RequirementRepositoryPort(Protocol):
    """要件リポジトリのポート"""
    def save(self, requirement: RequirementDict) -> str | ErrorDict:
        ...
    
    def find_by_id(self, requirement_id: str) -> RequirementDict | ErrorDict:
        ...
    
    def find_similar(self, embedding: EmbeddingDict, limit: int) -> List[RequirementDict] | ErrorDict:
        ...


class EmbedderPort(Protocol):
    """埋め込み生成のポート"""
    def embed(self, text: str) -> EmbeddingDict | ErrorDict:
        ...


# バリデーション関数
def validate_embedding(embedding: EmbeddingDict) -> Optional[str]:
    """埋め込みの検証"""
    if len(embedding["vector"]) != embedding["dimension"]:
        return f"Vector dimension {len(embedding['vector'])} != {embedding['dimension']}"
    return None


def validate_relation_confidence(confidence: float) -> Optional[str]:
    """信頼度の検証"""
    if not 0.0 <= confidence <= 1.0:
        return f"Confidence must be between 0 and 1, got {confidence}"
    return None


def validate_requirement_id(requirement_id: str) -> Optional[str]:
    """要件IDの検証"""
    if not requirement_id or not isinstance(requirement_id, str):
        return "RequirementId must be a non-empty string"
    return None


# ヘルパー関数
def create_embedding(vector_values: List[float], model_name: str = "test") -> EmbeddingDict:
    """埋め込みを作成するヘルパー"""
    return {
        "vector": vector_values,
        "model_name": model_name,
        "dimension": len(vector_values)
    }


def create_requirement(text: str, embedding: Optional[EmbeddingDict] = None) -> RequirementDict:
    """要件を作成するヘルパー"""
    if embedding is None:
        embedding = create_embedding([0.1, 0.2, 0.3])
    
    now = datetime.now()
    return {
        "id": f"REQ-{now.timestamp()}",
        "text": text,
        "embedding": embedding,
        "created_at": now,
        "updated_at": now,
        "metadata": {}
    }


# ===== テストコード（規約: in-sourceテスト） =====

def test_requirement_dict_valid_creation_returns_dict():
    """要件作成_正常データ_成功"""
    req: RequirementDict = {
        "id": "REQ-001",
        "text": "ユーザー認証機能",
        "embedding": create_embedding([0.1, 0.2]),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "metadata": {}
    }
    assert req["id"] == "REQ-001"
    assert req["text"] == "ユーザー認証機能"
    assert req["embedding"]["dimension"] == 2


def test_embedding_dict_dimension_mismatch_returns_error():
    """埋め込み検証_次元不一致_エラー"""
    embedding: EmbeddingDict = {
        "vector": [0.1, 0.2, 0.3],
        "model_name": "test", 
        "dimension": 2  # 不一致
    }
    error = validate_embedding(embedding)
    assert error is not None
    assert "dimension" in error.lower()


def test_relation_confidence_valid_range_returns_none():
    """関係信頼度_0から1の範囲_成功"""
    assert validate_relation_confidence(0.0) is None
    assert validate_relation_confidence(1.0) is None
    assert validate_relation_confidence(0.5) is None


def test_relation_confidence_invalid_range_returns_error():
    """関係信頼度_範囲外_エラー"""
    error1 = validate_relation_confidence(1.5)
    error2 = validate_relation_confidence(-0.1)
    assert error1 is not None and "between 0 and 1" in error1
    assert error2 is not None and "between 0 and 1" in error2


def test_requirement_id_empty_string_returns_error():
    """要件ID検証_空文字_エラー"""
    assert "non-empty" in validate_requirement_id("")
    assert "non-empty" in validate_requirement_id(None)


def test_create_embedding_helper_returns_valid_dict():
    """埋め込み作成_ヘルパー使用_正常動作"""
    emb = create_embedding([1.0, 0.0, 0.0], "test-model")
    assert emb["dimension"] == 3
    assert emb["model_name"] == "test-model"
    assert emb["vector"] == [1.0, 0.0, 0.0]


def test_create_requirement_helper_auto_generates_id():
    """要件作成_ヘルパー使用_ID自動生成"""
    req = create_requirement("テスト要件")
    assert req["id"].startswith("REQ-")
    assert req["text"] == "テスト要件"
    assert req["embedding"] is not None