"""インフラストラクチャ層の公開API"""

from .factory import create_embedding_model, get_available_models
from .ruri_model import RuriEmbeddingModel
# from .plamo_model import PlamoEmbeddingModel  # 将来的に有効化

__all__ = [
    "create_embedding_model",
    "get_available_models",
    "RuriEmbeddingModel",
    # "PlamoEmbeddingModel",  # 将来的に有効化
]