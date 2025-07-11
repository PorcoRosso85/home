"""埋め込みモデルパッケージの公開API"""

# ドメイン層
from .domain import (
    EmbeddingType,
    EmbeddingRequest,
    EmbeddingResult,
    EmbeddingModel,
)

# アプリケーション層
from .application import (
    TextEmbeddingService,
    SearchSimilarDocumentsUseCase,
    IndexDocumentsUseCase,
    DocumentSearchResult,
    Document,
)

# インフラストラクチャ層
from .infrastructure import (
    create_embedding_model,
    get_available_models,
)

# 統合システム
from .vector_search_system import VectorSearchSystem

__all__ = [
    # ドメイン型
    "EmbeddingType",
    "EmbeddingRequest", 
    "EmbeddingResult",
    "EmbeddingModel",
    # サービス
    "TextEmbeddingService",
    "SearchSimilarDocumentsUseCase",
    "IndexDocumentsUseCase",
    "DocumentSearchResult",
    "Document",
    # ファクトリー
    "create_embedding_model",
    "get_available_models",
    # システム
    "VectorSearchSystem",
]