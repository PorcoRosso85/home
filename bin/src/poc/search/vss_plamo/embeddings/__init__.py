"""埋め込みモデルパッケージの公開API"""

# ドメイン層
from .domain import (
    EmbeddingType,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingModel,
)

# アプリケーション層
from .application import TextEmbeddingService

# インフラストラクチャ層
from .infrastructure import (
    create_embedding_model,
    get_available_models,
)

__all__ = [
    # ドメイン型
    "EmbeddingType",
    "EmbeddingRequest", 
    "EmbeddingResult",
    "EmbeddingModel",
    # サービス
    "TextEmbeddingService",
    # ファクトリー
    "create_embedding_model",
    "get_available_models",
]