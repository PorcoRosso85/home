"""テキスト埋め込みサービス"""

from typing import List, Tuple, Protocol, Any
from dataclasses import dataclass
import numpy as np
from ..domain.types import EmbeddingModel, EmbeddingRequest, EmbeddingType, EmbeddingResult


@dataclass
class Document:
    id: int
    content: str
    similarity_score: float = 0.0


@dataclass
class DocumentSearchResult:
    ok: bool
    documents: List[Document] = None
    error: str = ""


@dataclass
class IndexResult:
    ok: bool
    indexed_count: int = 0
    failed_count: int = 0
    error: str = ""


class VectorRepository(Protocol):
    """ベクトルリポジトリのプロトコル"""
    def query_index(self, index_name: str, query_vector: List[float], k: int) -> Any:
        ...
    
    def insert_documents(self, documents: List[Any]) -> Any:
        ...


class SearchSimilarDocumentsUseCase:
    """類似文書検索ユースケース"""
    
    def __init__(self, embedding_model: EmbeddingModel, vector_repository: VectorRepository):
        self.embedding_model = embedding_model
        self.vector_repository = vector_repository
    
    def execute(self, query: str, k: int) -> DocumentSearchResult:
        """類似文書を検索"""
        if not query:
            return DocumentSearchResult(
                ok=False,
                error="Empty query not allowed"
            )
        
        # クエリの埋め込みを生成
        request = EmbeddingRequest(text=query, embedding_type=EmbeddingType.QUERY)
        embedding_result = self.embedding_model.encode(request)
        
        # ベクトル検索を実行
        search_result = self.vector_repository.query_index(
            index_name="doc_embedding_index",
            query_vector=embedding_result.embeddings,
            k=k
        )
        
        if not search_result.ok:
            return DocumentSearchResult(
                ok=False,
                error=search_result.error
            )
        
        # 結果をDocumentオブジェクトに変換
        documents = []
        if search_result.results:
            for i, result in enumerate(search_result.results):
                # 距離をスコアに変換（小さいほど類似度が高い）
                score = 1.0 - result['distance']
                documents.append(Document(
                    id=result['id'],
                    content=result['content'],
                    similarity_score=score
                ))
        
        return DocumentSearchResult(
            ok=True,
            documents=documents
        )


class IndexDocumentsUseCase:
    """文書インデックス作成ユースケース"""
    
    def __init__(self, embedding_model: EmbeddingModel, vector_repository: VectorRepository):
        self.embedding_model = embedding_model
        self.vector_repository = vector_repository
    
    def execute(self, documents: List[Document]) -> IndexResult:
        """文書をインデックスに追加"""
        if not documents:
            return IndexResult(
                ok=False,
                error="No documents provided"
            )
        
        # 埋め込みを生成
        requests = [
            EmbeddingRequest(text=doc.content, embedding_type=EmbeddingType.DOCUMENT)
            for doc in documents
        ]
        embedding_results = self.embedding_model.encode_batch(requests)
        
        # リポジトリに保存
        docs_with_embeddings = []
        for doc, embedding_result in zip(documents, embedding_results):
            docs_with_embeddings.append({
                'id': doc.id,
                'content': doc.content,
                'embedding': embedding_result.embeddings
            })
        
        insert_result = self.vector_repository.insert_documents(docs_with_embeddings)
        
        if not insert_result.ok:
            return IndexResult(
                ok=False,
                error=insert_result.error
            )
        
        return IndexResult(
            ok=True,
            indexed_count=len(documents),
            failed_count=0
        )


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