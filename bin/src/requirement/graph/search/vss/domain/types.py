"""埋め込みモデルのドメイン型定義"""

from dataclasses import dataclass
from typing import List, Protocol, runtime_checkable
from enum import Enum


class EmbeddingType(Enum):
    """埋め込みタイプの列挙型"""
    QUERY = "query"
    DOCUMENT = "document"
    TOPIC = "topic"
    SEMANTIC = "semantic"


@dataclass
class EmbeddingRequest:
    """埋め込みリクエスト"""
    text: str
    embedding_type: EmbeddingType = EmbeddingType.DOCUMENT


@dataclass
class EmbeddingResult:
    """埋め込み結果"""
    embeddings: List[float]
    model_name: str
    dimension: int


@runtime_checkable
class EmbeddingModel(Protocol):
    """埋め込みモデルのプロトコル"""
    
    @property
    def model_name(self) -> str:
        """モデル名を返す"""
        ...
    
    @property
    def dimension(self) -> int:
        """埋め込みベクトルの次元数を返す"""
        ...
    
    def encode(self, request: EmbeddingRequest) -> EmbeddingResult:
        """テキストを埋め込みベクトルに変換"""
        ...
    
    def encode_batch(self, requests: List[EmbeddingRequest]) -> List[EmbeddingResult]:
        """複数のテキストを一括で埋め込みベクトルに変換"""
        ...