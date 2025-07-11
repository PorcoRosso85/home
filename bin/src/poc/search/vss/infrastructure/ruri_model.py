"""Ruri v3 埋め込みモデルの実装"""

from typing import List
from sentence_transformers import SentenceTransformer
import torch
from ..domain.types import (
    EmbeddingModel, 
    EmbeddingRequest, 
    EmbeddingResult, 
    EmbeddingType
)


class RuriEmbeddingModel:
    """cl-nagoya/ruri-v3-30m の実装"""
    
    def __init__(self, model_name: str = "cl-nagoya/ruri-v3-30m"):
        self._model_name = model_name
        self._dimension = 256  # Ruri v3の次元数
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def _get_prefix(self, embedding_type: EmbeddingType) -> str:
        """埋め込みタイプに応じたプレフィックスを返す"""
        prefix_map = {
            EmbeddingType.SEMANTIC: "",  # 空文字列
            EmbeddingType.TOPIC: "トピック: ",
            EmbeddingType.QUERY: "検索クエリ: ",
            EmbeddingType.DOCUMENT: "検索文書: ",
        }
        return prefix_map.get(embedding_type, "")
    
    def encode(self, request: EmbeddingRequest) -> EmbeddingResult:
        """単一テキストの埋め込み"""
        prefix = self._get_prefix(request.embedding_type)
        text_with_prefix = f"{prefix}{request.text}"
        
        embeddings = self.model.encode(
            text_with_prefix, 
            convert_to_tensor=True
        )
        
        return EmbeddingResult(
            embeddings=embeddings.cpu().tolist(),
            model_name=self.model_name,
            dimension=self.dimension
        )
    
    def encode_batch(self, requests: List[EmbeddingRequest]) -> List[EmbeddingResult]:
        """バッチ埋め込み"""
        texts_with_prefix = [
            f"{self._get_prefix(req.embedding_type)}{req.text}"
            for req in requests
        ]
        
        embeddings = self.model.encode(
            texts_with_prefix,
            convert_to_tensor=True,
            batch_size=32
        )
        
        results = []
        for i, embedding in enumerate(embeddings):
            results.append(EmbeddingResult(
                embeddings=embedding.cpu().tolist(),
                model_name=self.model_name,
                dimension=self.dimension
            ))
        
        return results