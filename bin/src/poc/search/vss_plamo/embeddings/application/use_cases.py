"""埋め込みモデルのユースケース"""

from typing import List, Tuple
import numpy as np
from ..domain.types import EmbeddingModel, EmbeddingRequest, EmbeddingType, EmbeddingResult


class TextEmbeddingService:
    """テキスト埋め込みサービス"""
    
    def __init__(self, model: EmbeddingModel):
        self.model = model
    
    def embed_query(self, query: str) -> EmbeddingResult:
        """検索クエリの埋め込み"""
        request = EmbeddingRequest(
            text=query,
            embedding_type=EmbeddingType.QUERY
        )
        return self.model.encode(request)
    
    def embed_documents(self, documents: List[str]) -> List[EmbeddingResult]:
        """ドキュメントの埋め込み"""
        requests = [
            EmbeddingRequest(text=doc, embedding_type=EmbeddingType.DOCUMENT)
            for doc in documents
        ]
        return self.model.encode_batch(requests)
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """コサイン類似度の計算"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def search_similar_documents(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[Tuple[int, str, float]]:
        """類似ドキュメントの検索"""
        # クエリの埋め込み
        query_result = self.embed_query(query)
        query_embedding = query_result.embeddings
        
        # ドキュメントの埋め込み
        doc_results = self.embed_documents(documents)
        
        # 類似度計算
        similarities = []
        for i, doc_result in enumerate(doc_results):
            similarity = self.compute_similarity(
                query_embedding, 
                doc_result.embeddings
            )
            similarities.append((i, documents[i], similarity))
        
        # 類似度でソート
        similarities.sort(key=lambda x: x[2], reverse=True)
        
        return similarities[:top_k]