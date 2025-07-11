"""埋め込みモデルのファクトリー"""

from typing import Literal
from ..domain.types import EmbeddingModel
from .ruri_model import RuriEmbeddingModel
# from .plamo_model import PlamoEmbeddingModel  # 将来的に有効化


ModelType = Literal["ruri-v3-30m", "plamo-embedding-1b"]


def create_embedding_model(
    model_type: ModelType = "ruri-v3-30m"
) -> EmbeddingModel:
    """指定されたタイプの埋め込みモデルを作成"""
    
    if model_type == "ruri-v3-30m":
        return RuriEmbeddingModel()
    
    # elif model_type == "plamo-embedding-1b":
    #     # メモリ要件: 8GB以上推奨
    #     return PlamoEmbeddingModel()
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def get_available_models() -> list[str]:
    """利用可能なモデルのリストを返す"""
    return [
        "ruri-v3-30m",       # 30M parameters, 256 dimensions
        # "plamo-embedding-1b",  # 1B parameters, 1536 dimensions (要高メモリ)
    ]