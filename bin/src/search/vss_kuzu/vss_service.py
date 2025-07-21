#!/usr/bin/env python3
"""
VSS (Vector Similarity Search) Service
"""

import time
from typing import Dict, Any, List, Optional
import numpy as np


class VSSService:
    """Vector Similarity Search service"""
    
    def __init__(self, db_path: str = "./kuzu_db", in_memory: bool = False):
        self.db_path = db_path
        self.in_memory = in_memory
        self.dimension = 256  # Default dimension for ruri-v3-30m
        
        # Database and connection
        self._db = None
        self._conn = None
        self._embedding_service = None
        self._vector_index_created = False
    
    def _get_connection(self):
        """Get or create database connection using persistence layer"""
        if self._conn is None:
            from kuzu_py import create_database, create_connection
            
            # For in-memory database, pass ":memory:" to kuzu
            db_path = ":memory:" if self.in_memory else self.db_path
            
            # Create database and connection using kuzu_py helper functions
            db_result = create_database(db_path)
            if not db_result.get("success", False):
                error_msg = db_result.get("error", {}).get("message", "Unknown error")
                raise RuntimeError(f"Failed to create database: {error_msg}")
            
            self._db = db_result["database"]
            
            conn_result = create_connection(self._db)
            if not conn_result.get("success", False):
                error_msg = conn_result.get("error", {}).get("message", "Unknown error")
                raise RuntimeError(f"Failed to create connection: {error_msg}")
            
            self._conn = conn_result["connection"]
            
            # Initialize schema
            self._initialize_schema()
        return self._conn
    
    def _initialize_schema(self):
        """Initialize database schema"""
        conn = self._conn
        
        # Check if Document table exists
        result = conn.execute("CALL show_tables() RETURN *;")
        tables = []
        while result.has_next():
            tables.append(result.get_next()[0])
        
        if "Document" not in tables:
            # Create Document table with id, content, and embedding
            conn.execute(f"""
                CREATE NODE TABLE Document (
                    id INT64,
                    content STRING,
                    embedding FLOAT[{self.dimension}],
                    PRIMARY KEY (id)
                )
            """)
    
    def _get_embedding_service(self):
        """Get or create embedding service"""
        if self._embedding_service is None:
            # Import sentence_transformers locally to avoid import errors during testing
            from sentence_transformers import SentenceTransformer
            
            # Simple mock for StandaloneEmbeddingService
            class StandaloneEmbeddingService:
                def __init__(self):
                    self.model_name = "cl-nagoya/ruri-v3-30m"
                    self.dimension = 256
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
                    result = EmbeddingResult(
                        embeddings=embedding.tolist(),
                        model_name=self.model_name,
                        dimension=self.dimension
                    )
                    return result
            
            self._embedding_service = StandaloneEmbeddingService()
            self.dimension = self._embedding_service.dimension
                
        return self._embedding_service
    
    def search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform vector similarity search
        
        Args:
            input_data: Dictionary with query parameters
            
        Returns:
            Dictionary with search results
        """
        # Extract parameters
        query = input_data["query"]
        limit = input_data.get("limit", 10)
        model = input_data.get("model", "ruri-v3-30m")
        threshold = input_data.get("threshold")
        query_vector = input_data.get("query_vector")
        
        # Start timing
        start_time = time.time()
        
        # Get services
        conn = self._get_connection()
        embedding_service = self._get_embedding_service()
        
        # Get or compute query embedding
        if query_vector:
            # Use provided vector
            query_embedding = query_vector
            if len(query_embedding) != self.dimension:
                raise ValueError(f"Query vector dimension mismatch. Expected {self.dimension}, got {len(query_embedding)}")
        else:
            # Compute embedding
            result = embedding_service.embed_query(query)
            query_embedding = result.embeddings
        
        # Ensure vector index exists
        self._ensure_vector_index(conn)
        
        # Execute vector search
        results = []
        try:
            # Use QUERY_VECTOR_INDEX for search
            result = conn.execute(
                "CALL QUERY_VECTOR_INDEX('Document', 'doc_embedding_index', $embedding, $k) RETURN *;",
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
        except Exception as e:
            # If vector index doesn't exist, return empty results
            if "does not exist" in str(e):
                results = []
            else:
                raise
        
        # Calculate query time
        query_time_ms = (time.time() - start_time) * 1000
        
        # Build output
        output = {
            "results": results,
            "metadata": {
                "model": model,
                "dimension": self.dimension,
                "total_results": len(results),
                "query_time_ms": round(query_time_ms, 2)
            }
        }
        
        return output
    
    def index_documents(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Index documents for vector search
        
        Args:
            documents: List of documents with 'id' and 'content'
            
        Returns:
            Status dictionary
        """
        start_time = time.time()
        
        # Get services
        conn = self._get_connection()
        embedding_service = self._get_embedding_service()
        
        # Extract texts
        texts = [doc["content"] for doc in documents]
        
        # Generate embeddings
        embeddings = embedding_service.embed_documents(texts)
        
        # Insert documents
        indexed_count = 0
        for doc, embedding_result in zip(documents, embeddings):
            # Get next ID if not provided
            doc_id = doc.get("id")
            if doc_id is None:
                # Get max ID and increment
                result = conn.execute("MATCH (d:Document) RETURN MAX(d.id) AS max_id;")
                max_id_row = result.get_next()
                max_id = max_id_row[0] if max_id_row[0] is not None else 0
                doc_id = max_id + 1
            else:
                doc_id = int(doc_id)
            
            # Insert or update document
            conn.execute("""
                MERGE (d:Document {id: $id})
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
        
        return {
            "status": "success",
            "indexed_count": indexed_count,
            "index_time_ms": round(index_time_ms, 2)
        }
    
    def _ensure_vector_index(self, conn):
        """Ensure vector index exists on Document.embedding"""
        if not self._vector_index_created:
            try:
                # Create vector index
                conn.execute("CALL CREATE_VECTOR_INDEX('Document', 'doc_embedding_index', 'embedding') RETURN *;")
                self._vector_index_created = True
            except Exception as e:
                # Index might already exist
                if "already exists" in str(e):
                    self._vector_index_created = True
                else:
                    # Try to drop and recreate
                    try:
                        conn.execute("CALL DROP_VECTOR_INDEX('Document', 'doc_embedding_index') RETURN *;")
                        conn.execute("CALL CREATE_VECTOR_INDEX('Document', 'doc_embedding_index', 'embedding') RETURN *;")
                        self._vector_index_created = True
                    except:
                        # Ignore if we can't create index
                        pass


# Simple data class for embedding results
class EmbeddingResult:
    def __init__(self, embeddings: List[float], model_name: str, dimension: int):
        self.embeddings = embeddings
        self.model_name = model_name
        self.dimension = dimension