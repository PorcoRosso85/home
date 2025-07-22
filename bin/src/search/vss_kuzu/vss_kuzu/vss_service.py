#!/usr/bin/env python3
"""
VSS (Vector Similarity Search) Service - 規約準拠版

エラー処理規約に従い、フォールバックを排除し、
明示的なエラーハンドリングを実装
"""

import time
from typing import Dict, Any, List, Optional, Union, TypedDict
import numpy as np
import sys

# Constants
EMBEDDING_DIMENSION = 256
VECTOR_EXTENSION_NAME = 'VECTOR'
DEFAULT_MODEL_NAME = 'cl-nagoya/ruri-v3-30m'
IN_MEMORY_DB_PATH = ':memory:'
DOCUMENT_TABLE_NAME = 'Document'
DOCUMENT_EMBEDDING_INDEX_NAME = 'doc_embedding_index'


class VectorSearchError(TypedDict):
    """エラー情報を表す型"""
    ok: bool
    error: str
    details: Dict[str, Any]


class VectorSearchResult(TypedDict):
    """検索成功時の結果型"""
    ok: bool
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class VectorIndexResult(TypedDict):
    """インデックス操作の結果型"""
    ok: bool
    status: str
    indexed_count: int
    index_time_ms: float
    error: Optional[str]


class VSSService:
    """Vector Similarity Search service - 規約準拠版"""
    
    def __init__(self, db_path: str = "./kuzu_db", in_memory: bool = False):
        self.db_path = db_path
        self.in_memory = in_memory
        self.dimension = EMBEDDING_DIMENSION  # Default dimension for ruri-v3-30m
        
        # Database and connection - always create fresh instances
        self._db = None
        self._conn = None
        self._embedding_service = None
        self._vector_extension_available = None
        self._subprocess_wrapper = None
        
        # Check if we need subprocess wrapper (pytest environment)
        if 'pytest' in sys.modules:
            try:
                from .vector_subprocess_wrapper import VectorSubprocessWrapper
                self._subprocess_wrapper = VectorSubprocessWrapper(
                    IN_MEMORY_DB_PATH if in_memory else db_path
                )
            except ImportError:
                # Subprocess wrapper not available, continue without it
                pass
    
    def _get_connection(self):
        """Get or create database connection using persistence layer"""
        if self._conn is None:
            from kuzu_py import create_database, create_connection
            
            # For in-memory database, pass ":memory:" to kuzu
            db_path = IN_MEMORY_DB_PATH if self.in_memory else self.db_path
            
            # Create database and connection using kuzu_py helper functions
            db_result = create_database(db_path)
            # Check if it's an error (VectorSearchError has 'ok' attribute set to False)
            if hasattr(db_result, 'get') and db_result.get("ok") is False:
                error_msg = db_result.get("error", "Unknown error")
                raise RuntimeError(f"Failed to create database: {error_msg}")
            
            # db_result is the Database object itself
            self._db = db_result
            
            conn_result = create_connection(self._db)
            # Check if it's an error (VectorSearchError has 'ok' attribute set to False)
            if hasattr(conn_result, 'get') and conn_result.get("ok") is False:
                error_msg = conn_result.get("error", "Unknown error")
                raise RuntimeError(f"Failed to create connection: {error_msg}")
            
            # conn_result is the Connection object itself
            self._conn = conn_result
            
            # Initialize schema and check VECTOR extension
            self._initialize_schema()
        return self._conn
    
    def _initialize_schema(self):
        """Initialize database schema and check VECTOR extension availability"""
        conn = self._conn
        
        # Check VECTOR extension availability
        self._vector_extension_available = self._check_vector_extension(conn)
        
        # Create Document table if it doesn't exist
        try:
            conn.execute(f"""
                CREATE NODE TABLE IF NOT EXISTS {DOCUMENT_TABLE_NAME} (
                    id STRING,
                    content STRING,
                    embedding FLOAT[{self.dimension}],
                    PRIMARY KEY (id)
                )
            """)
        except Exception as e:
            # KuzuDB might not support IF NOT EXISTS, try without it
            try:
                conn.execute(f"""
                    CREATE NODE TABLE {DOCUMENT_TABLE_NAME} (
                        id STRING,
                        content STRING,
                        embedding FLOAT[{self.dimension}],
                        PRIMARY KEY (id)
                    )
                """)
            except Exception as inner_e:
                # Table already exists, which is fine
                if "already exists" not in str(inner_e):
                    raise
    
    def _check_vector_extension(self, conn) -> bool:
        """Check if VECTOR extension is available"""
        # First, try to load the extension (it might already be installed)
        try:
            conn.execute(f"LOAD EXTENSION {VECTOR_EXTENSION_NAME};")
            # Verify it works by checking if vector functions are available
            # Don't create test index here as table might not exist yet
            return True
        except Exception as load_error:
            # Extension not loaded, try to install it first
            try:
                conn.execute(f"INSTALL {VECTOR_EXTENSION_NAME};")
                # Now try to load the newly installed extension
                conn.execute(f"LOAD EXTENSION {VECTOR_EXTENSION_NAME};")
                return True
            except Exception as install_error:
                # Log detailed error for debugging
                import sys
                print(f"{VECTOR_EXTENSION_NAME} extension not available: {install_error}", file=sys.stderr)
                return False
    
    def _get_embedding_service(self):
        """Get or create embedding service"""
        if self._embedding_service is None:
            # Import sentence_transformers locally to avoid import errors during testing
            from sentence_transformers import SentenceTransformer
            
            # Simple mock for StandaloneEmbeddingService
            class StandaloneEmbeddingService:
                def __init__(self):
                    self.model_name = DEFAULT_MODEL_NAME
                    self.dimension = EMBEDDING_DIMENSION
                    self._model = None
                
                def _get_model(self):
                    if self._model is None:
                        self._model = SentenceTransformer(self.model_name)
                    return self._model
                
                def embed_documents(self, texts: List[str]):
                    model = self._get_model()
                    embeddings = model.encode(texts, normalize_embeddings=True)
                    results = []
                    for embedding in embeddings:
                        result = EmbeddingResult(
                            embeddings=embedding.tolist(),
                            model_name=self.model_name,
                            dimension=self.dimension
                        )
                        results.append(result)
                    return results
                
                def embed_query(self, text: str):
                    model = self._get_model()
                    embedding = model.encode([text], normalize_embeddings=True)[0]
                    return EmbeddingResult(
                        embeddings=embedding.tolist(),
                        model_name=self.model_name,
                        dimension=self.dimension
                    )
            
            self._embedding_service = StandaloneEmbeddingService()
            self.dimension = self._embedding_service.dimension
                
        return self._embedding_service
    
    def search(self, input_data: Dict[str, Any]) -> Union[VectorSearchResult, VectorSearchError]:
        """
        Perform vector similarity search
        
        規約準拠: VECTOR拡張が利用できない場合はエラーを返す
        """
        try:
            # Extract parameters
            query = input_data["query"]
            limit = input_data.get("limit", 10)
            model = input_data.get("model", DEFAULT_MODEL_NAME.split('/')[-1])
            threshold = input_data.get("threshold")
            query_vector = input_data.get("query_vector")
            
            # Start timing
            start_time = time.time()
            
            # Get services
            conn = self._get_connection()
            
            # Check VECTOR extension availability
            if not self._vector_extension_available:
                return VectorSearchError(
                    ok=False,
                    error=f"{VECTOR_EXTENSION_NAME} extension not available",
                    details={
                        "extension": VECTOR_EXTENSION_NAME,
                        "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}; LOAD EXTENSION {VECTOR_EXTENSION_NAME};",
                        "reason": "Required for vector similarity search"
                    }
                )
            
            embedding_service = self._get_embedding_service()
            
            # Get or compute query embedding
            if query_vector:
                # Use provided vector
                query_embedding = query_vector
                if len(query_embedding) != self.dimension:
                    return VectorSearchError(
                        ok=False,
                        error=f"Query vector dimension mismatch",
                        details={
                            "expected": self.dimension,
                            "got": len(query_embedding)
                        }
                    )
            else:
                # Compute embedding
                result = embedding_service.embed_query(query)
                query_embedding = result.embeddings
            
            # Ensure vector index exists
            self._ensure_vector_index(conn)
            
            # Execute vector search using VECTOR extension
            results = []
            result = conn.execute(
                f"CALL QUERY_VECTOR_INDEX('{DOCUMENT_TABLE_NAME}', '{DOCUMENT_EMBEDDING_INDEX_NAME}', $embedding, $k) RETURN *;",
                {"embedding": query_embedding, "k": limit}
            )
            
            while result.has_next():
                row = result.get_next()
                doc_data = row[0]  # Document node
                distance = row[1]  # Distance
                
                # Convert distance to similarity score
                score = 1.0 - distance
                
                # Apply threshold filter if specified
                if threshold is None or score >= threshold:
                    results.append({
                        "id": str(doc_data.get("id", "")),
                        "content": doc_data.get("content", ""),
                        "score": float(score),
                        "distance": float(distance)
                    })
            
            # Calculate query time
            query_time_ms = (time.time() - start_time) * 1000
            
            # Sort results by score in descending order to ensure consistency
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Build output
            return VectorSearchResult(
                ok=True,
                results=results,
                metadata={
                    "model": model,
                    "dimension": self.dimension,
                    "total_results": len(results),
                    "query_time_ms": round(query_time_ms, 2)
                }
            )
            
        except Exception as e:
            return VectorSearchError(
                ok=False,
                error=str(e),
                details={
                    "type": type(e).__name__,
                    "input": input_data
                }
            )
    
    def index_documents(self, documents: List[Dict[str, str]]) -> Union[VectorIndexResult, VectorSearchError]:
        """
        Index documents for vector search
        
        規約準拠: VECTOR拡張が利用できない場合はエラーを返す
        """
        try:
            start_time = time.time()
            
            # Get services
            conn = self._get_connection()
            
            # Check VECTOR extension availability
            if not self._vector_extension_available:
                return VectorSearchError(
                    ok=False,
                    error=f"{VECTOR_EXTENSION_NAME} extension not available",
                    details={
                        "extension": VECTOR_EXTENSION_NAME,
                        "install_command": f"INSTALL {VECTOR_EXTENSION_NAME}; LOAD EXTENSION {VECTOR_EXTENSION_NAME};",
                        "reason": "Required for vector indexing"
                    }
                )
            
            embedding_service = self._get_embedding_service()
            
            # Extract texts
            texts = [doc["content"] for doc in documents]
            
            # Generate embeddings
            embeddings = embedding_service.embed_documents(texts)
            
            # Insert documents
            indexed_count = 0
            for i, (doc, embedding_result) in enumerate(zip(documents, embeddings)):
                # Get next ID if not provided
                doc_id = doc.get("id")
                if doc_id is None:
                    # Generate a unique string ID based on timestamp
                    doc_id = f"doc_{int(time.time() * 1000)}_{i}"
                else:
                    # Keep doc_id as string
                    doc_id = str(doc_id)
                
                # Insert or update document
                conn.execute(f"""
                    MERGE (d:{DOCUMENT_TABLE_NAME} {{id: $id}})
                    SET d.content = $content, d.embedding = $embedding
                """, {
                    "id": doc_id,
                    "content": doc["content"],
                    "embedding": embedding_result.embeddings
                })
                indexed_count += 1
            
            # Ensure vector index exists
            self._ensure_vector_index(conn)
            
            index_time_ms = (time.time() - start_time) * 1000
            
            return VectorIndexResult(
                ok=True,
                status="success",
                indexed_count=indexed_count,
                index_time_ms=round(index_time_ms, 2),
                error=None
            )
            
        except Exception as e:
            return VectorSearchError(
                ok=False,
                error=str(e),
                details={
                    "type": type(e).__name__,
                    "documents_count": len(documents)
                }
            )
    
    def _ensure_vector_index(self, conn):
        """Ensure vector index exists on Document.embedding"""
        try:
            # Create vector index if it doesn't exist
            conn.execute(f"CALL CREATE_VECTOR_INDEX('{DOCUMENT_TABLE_NAME}', '{DOCUMENT_EMBEDDING_INDEX_NAME}', 'embedding')")
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" not in str(e):
                raise


# Simple data class for embedding results
class EmbeddingResult:
    def __init__(self, embeddings: List[float], model_name: str, dimension: int):
        self.embeddings = embeddings
        self.model_name = model_name
        self.dimension = dimension