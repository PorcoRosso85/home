"""
KuzuDBを使用した検索サービスの実装
すべての実装詳細（サブプロセス、セグフォルト回避等）をここに隠蔽
"""

import os
from typing import List, Dict, Any, Optional
import tempfile

from poc.search.domain.interfaces import SearchService, SearchResult
from poc.search.hybrid.kuzu_extension_wrapper import KuzuExtensionSubprocess, is_pytest_running

# KuzuDB imports
import kuzu

# Embedding model
try:
    from sentence_transformers import SentenceTransformer
    import torch
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class KuzuSearchService(SearchService):
    """KuzuDBを使用した検索サービスの具体的実装"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: データベースパス。Noneの場合は一時ディレクトリを使用
        """
        if db_path is None:
            self._temp_dir = tempfile.mkdtemp()
            self._db_path = self._temp_dir
        else:
            self._temp_dir = None
            self._db_path = db_path
            
        self._setup_database()
        self._setup_embedding_model()
        
    def _setup_database(self):
        """データベースとテーブルのセットアップ"""
        self._db = kuzu.Database(self._db_path)
        self._conn = kuzu.Connection(self._db)
        
        # Create table
        self._conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS RequirementEntity (
                id STRING PRIMARY KEY,
                title STRING,
                content STRING,
                embedding DOUBLE[256]
            )
        """)
        
        # Store db_path for subprocess access
        self._conn.db_path = self._db_path
        self._conn.db_obj = self._db
        
    def _setup_embedding_model(self):
        """埋め込みモデルのセットアップ"""
        if EMBEDDINGS_AVAILABLE:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._embedder = SentenceTransformer("cl-nagoya/ruri-v3-30m", device=device)
            self._embedding_dim = 256
        else:
            self._embedder = None
            self._embedding_dim = 256
            
    def _generate_embedding(self, text: str) -> List[float]:
        """テキストから埋め込みベクトルを生成"""
        if self._embedder:
            embedding = self._embedder.encode(text)
            return embedding.tolist()
        else:
            # Fallback: deterministic mock embedding
            hash_value = hash(text)
            embedding = []
            for i in range(self._embedding_dim):
                seed = (hash_value + i) % 2147483647
                value = (seed % 1000) / 1000.0
                embedding.append(value)
            return embedding
    
    def add_requirement(self, id: str, title: str, content: str) -> None:
        """要件を追加"""
        full_text = f"{title} {content}"
        embedding = self._generate_embedding(full_text)
        
        # Format embedding for query
        embedding_str = "[" + ", ".join(str(v) for v in embedding) + "]"
        
        self._conn.execute(f"""
            CREATE (r:RequirementEntity {{
                id: '{id}',
                title: '{title}',
                content: '{content}',
                embedding: {embedding_str}
            }})
        """)
        
    def search_similar(self, query: str, k: int = 10) -> List[SearchResult]:
        """類似検索を実行"""
        query_embedding = self._generate_embedding(query)
        
        if is_pytest_running() and self._should_use_subprocess():
            return self._search_similar_subprocess(query_embedding, k)
        else:
            return self._search_similar_direct(query_embedding, k)
            
    def _should_use_subprocess(self) -> bool:
        """サブプロセスを使用すべきか判定"""
        # VSS拡張機能が必要な場合はTrue
        # 現在の実装では、拡張機能を使わないので常にFalse
        return False
        
    def _search_similar_subprocess(self, query_embedding: List[float], k: int) -> List[SearchResult]:
        """サブプロセス経由での類似検索（将来の拡張用）"""
        # TODO: KuzuExtensionSubprocessを使用した実装
        return []
        
    def _search_similar_direct(self, query_embedding: List[float], k: int) -> List[SearchResult]:
        """直接的な類似検索（簡易実装）"""
        # Get all requirements
        result = self._conn.execute("""
            MATCH (r:RequirementEntity)
            RETURN r.id, r.title, r.content, r.embedding
        """)
        
        requirements = []
        while result.has_next():
            row = result.get_next()
            requirements.append({
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "embedding": row[3]
            })
            
        # Calculate similarities
        similarities = []
        for req in requirements:
            # Simple cosine similarity
            similarity = self._cosine_similarity(query_embedding, req["embedding"])
            similarities.append({
                "requirement": req,
                "similarity": similarity
            })
            
        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Convert to SearchResult
        results = []
        for item in similarities[:k]:
            req = item["requirement"]
            results.append(SearchResult(
                id=req["id"],
                title=req["title"],
                content=req["content"],
                score=item["similarity"],
                source="vss"
            ))
            
        return results
        
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度を計算"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
        
    def search_keyword(self, query: str, k: int = 10) -> List[SearchResult]:
        """キーワード検索を実行"""
        # Simple keyword matching
        result = self._conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS $query OR r.content CONTAINS $query
            RETURN r.id, r.title, r.content
        """, {"query": query})
        
        results = []
        while result.has_next() and len(results) < k:
            row = result.get_next()
            # Simple scoring based on occurrence
            title_score = 1.0 if query in row[1] else 0.0
            content_score = 0.5 if query in row[2] else 0.0
            score = min(1.0, title_score + content_score)
            
            results.append(SearchResult(
                id=row[0],
                title=row[1],
                content=row[2],
                score=score,
                source="fts"
            ))
            
        return results
        
    def search_hybrid(self, query: str, k: int = 10) -> List[SearchResult]:
        """ハイブリッド検索を実行"""
        # Get results from both methods
        vss_results = self.search_similar(query, k)
        fts_results = self.search_keyword(query, k)
        
        # Merge results
        merged = {}
        
        # Add VSS results
        for result in vss_results:
            merged[result.id] = {
                "result": result,
                "vss_score": result.score,
                "fts_score": 0.0
            }
            
        # Add FTS results
        for result in fts_results:
            if result.id in merged:
                merged[result.id]["fts_score"] = result.score
            else:
                merged[result.id] = {
                    "result": result,
                    "vss_score": 0.0,
                    "fts_score": result.score
                }
                
        # Calculate combined scores
        final_results = []
        for item in merged.values():
            # Simple weighted average
            combined_score = (item["vss_score"] + item["fts_score"]) / 2
            
            result = item["result"]
            final_results.append(SearchResult(
                id=result.id,
                title=result.title,
                content=result.content,
                score=combined_score,
                source="hybrid"
            ))
            
        # Sort by score
        final_results.sort(key=lambda x: x.score, reverse=True)
        
        return final_results[:k]
        
    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, '_conn'):
            self._conn.close()
        if hasattr(self, '_temp_dir') and self._temp_dir:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)