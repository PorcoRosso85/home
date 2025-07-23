#!/usr/bin/env python3
"""
埋め込み生成モジュール

テキストから埋め込みベクトルを生成する機能を提供
"""

from typing import List, Callable, Optional, TypedDict


DEFAULT_MODEL_NAME = 'cl-nagoya/ruri-v3-30m'
EMBEDDING_DIMENSION = 256


class EmbeddingResult(TypedDict):
    """埋め込み結果を表す型定義"""
    embeddings: List[float]
    model_name: str
    dimension: int


def create_embedding_service(model_name: str = DEFAULT_MODEL_NAME) -> Callable[[str], List[float]]:
    """
    埋め込み生成サービスを作成する
    
    Args:
        model_name: 使用するモデル名
        
    Returns:
        埋め込み生成関数
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        
        embedding_dim = model.get_sentence_embedding_dimension()
        
        def generate_embedding_with_model(text: str) -> List[float]:
            """
            sentence-transformersを使用して埋め込みを生成
            """
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        
        generate_embedding_with_model.dimension = embedding_dim
        
        return generate_embedding_with_model
        
    except ImportError:
        def generate_embedding(text: str) -> List[float]:
            """
            テキストから埋め込みベクトルを生成する（フォールバック実装）
            
            sentence-transformersが利用できない場合のダミー実装
            """
            import hashlib
            import struct
            
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            embedding = []
            for i in range(0, min(len(hash_bytes), EMBEDDING_DIMENSION * 4), 4):
                if i + 4 <= len(hash_bytes):
                    value = struct.unpack('I', hash_bytes[i:i+4])[0]
                    normalized = (value / (2**32 - 1)) * 2 - 1
                    embedding.append(normalized)
            
            while len(embedding) < EMBEDDING_DIMENSION:
                embedding.append(0.0)
            
            return embedding[:EMBEDDING_DIMENSION]
        
        generate_embedding.dimension = EMBEDDING_DIMENSION
        
        return generate_embedding


def create_standalone_embedding_service(model_name: str = DEFAULT_MODEL_NAME):
    """
    スタンドアロン埋め込みサービスを作成する
    
    Args:
        model_name: 使用するモデル名
        
    Returns:
        埋め込みサービスオブジェクト
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        class StandaloneEmbeddingService:
            def __init__(self):
                self.model_name = model_name
                self.dimension = EMBEDDING_DIMENSION
                self._model = None
            
            def _get_model(self):
                if self._model is None:
                    self._model = SentenceTransformer(self.model_name)
                    self.dimension = self._model.get_sentence_embedding_dimension()
                return self._model
            
            def embed_documents(self, texts: List[str]) -> List[EmbeddingResult]:
                model = self._get_model()
                embeddings = model.encode(texts, normalize_embeddings=True)
                results = []
                for embedding in embeddings:
                    result: EmbeddingResult = {
                        'embeddings': embedding.tolist(),
                        'model_name': self.model_name,
                        'dimension': self.dimension
                    }
                    results.append(result)
                return results
            
            def embed_query(self, text: str) -> EmbeddingResult:
                model = self._get_model()
                embedding = model.encode([text], normalize_embeddings=True)[0]
                return {
                    'embeddings': embedding.tolist(),
                    'model_name': self.model_name,
                    'dimension': self.dimension
                }
        
        return StandaloneEmbeddingService()
        
    except ImportError:
        # Fallback implementation without sentence-transformers
        class FallbackEmbeddingService:
            def __init__(self):
                self.model_name = "fallback"
                self.dimension = EMBEDDING_DIMENSION
            
            def _generate_embedding(self, text: str) -> List[float]:
                import hashlib
                import struct
                
                hash_obj = hashlib.sha256(text.encode('utf-8'))
                hash_bytes = hash_obj.digest()
                
                embedding = []
                for i in range(0, min(len(hash_bytes), self.dimension * 4), 4):
                    if i + 4 <= len(hash_bytes):
                        value = struct.unpack('I', hash_bytes[i:i+4])[0]
                        normalized = (value / (2**32 - 1)) * 2 - 1
                        embedding.append(normalized)
                
                while len(embedding) < self.dimension:
                    embedding.append(0.0)
                
                return embedding[:self.dimension]
            
            def embed_documents(self, texts: List[str]) -> List[EmbeddingResult]:
                results = []
                for text in texts:
                    result: EmbeddingResult = {
                        'embeddings': self._generate_embedding(text),
                        'model_name': self.model_name,
                        'dimension': self.dimension
                    }
                    results.append(result)
                return results
            
            def embed_query(self, text: str) -> EmbeddingResult:
                return {
                    'embeddings': self._generate_embedding(text),
                    'model_name': self.model_name,
                    'dimension': self.dimension
                }
        
        return FallbackEmbeddingService()